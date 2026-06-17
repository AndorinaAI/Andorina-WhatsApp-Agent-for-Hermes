import sys
import uuid
import json
import argparse
from pathlib import Path

# Fix relative import to reach scripts/common.py
sys.path.append(str(Path(__file__).parent.parent))
from common import load_env
from utils.safe_json import read_json_safe, write_json_safe
from security.input_guard import validate_input
from security.rbac import load_rules, resolve_role, get_role_config, is_owner

STATE_DIR = Path(__file__).parent.parent.parent / "state"

def build_snapshot(number, env):
    rules = load_rules()
    role = resolve_role(number, rules, env)
    role_config = get_role_config(role, rules)
    is_admin = is_owner(number, env) or resolve_role(number, rules, env) == "owner"
    mode = "full" if is_admin else ("manager" if role == "manager" else "chatbot")

    # Merge JID-level overrides (allowed_folders, allowed_chats) from guard_rules.json
    num = number.split("@")[0]
    jid_entry = rules.get("jids", {}).get(num, {})
    if jid_entry.get("allowed_folders"):
        merged_folders = list(set(role_config.get("allowed_folders", [])) | set(jid_entry["allowed_folders"]))
        role_config = dict(role_config)
        role_config["allowed_folders"] = merged_folders
    if jid_entry.get("allowed_chats"):
        merged_chats = list(set(role_config.get("allowed_chats", [])) | set(jid_entry["allowed_chats"]))
        role_config = dict(role_config)
        role_config["allowed_chats"] = merged_chats
    
    # Note: Personality (sub-soul) is no longer loaded here.
    # Soul/identity goes via soul_sync.py → channel_prompts → real system prompt.
    
    # ── Auxiliary context (injected via pre_llm_call hook, NOT the soul) ──
    context_parts = []
    num = number.split("@")[0]

    # Notes
    notes_file = STATE_DIR / "notes" / f"{num}.md"
    if notes_file.exists():
        context_parts.append(f"### NOTES FOR {number}:\n" + notes_file.read_text(encoding="utf-8"))

    # If chatbot role but has allowed_folders → promote effective permissions
    folders = role_config.get("allowed_folders", [])
    effective_perms = list(role_config.get("permissions", []))
    if folders and not is_admin and role != "manager":
        if "os:read" not in effective_perms:
            effective_perms.append("os:read")
        if "os:ls" not in effective_perms:
            effective_perms.append("os:ls")

    # Inject permissions
    _perms_str = f"### YOUR PERMISSIONS FOR THIS USER:\n{', '.join(effective_perms) if effective_perms else 'NONE'}"
    context_parts.append(_perms_str)
    
    # Inject allowed folders
    if folders:
        _folders_str = f"### ALLOWED FOLDERS:\n{chr(10).join(f'  - {f}' for f in folders)}"
        context_parts.append(_folders_str)

    # Inject allowed chats
    chats = role_config.get("allowed_chats", [])
    if chats:
        _chats_str = f"### ALLOWED CHATS:\n{', '.join(chats)}"
        context_parts.append(_chats_str)
        
    # Inject mode context
    if is_admin:
        _mode_str = "### OPERATION MODE: full\nYou are talking to the OWNER. All tools and features are enabled."
    elif role == "manager":
        _mode_str = (
            "### OPERATION MODE: manager\n"
            "⚠️ CRITICAL — You are talking to a MANAGER. They have limited tool permissions.\n"
            "1. You MAY use tools if they have the explicit permission granted.\n"
            "2. DO NOT mention internal scripts or paths to them.\n"
            "3. DO NOT share private data unless it is explicitly within their allowed_folders or allowed_chats."
        )
    elif folders:
        # Chatbot with allowed_folders → restricted file access mode
        folders_list = "\n".join(f"  - {f}" for f in folders)
        _mode_str = (
            "### OPERATION MODE: restricted_access\n"
            "⚠️ RULES — You are talking to a THIRD PARTY with limited file access.\n"
            "You have these authorizations with ZERO exceptions:\n"
            f"1. You MAY use terminal or read_file tools ONLY to read/list files in these folders:\n{folders_list}\n"
            "2. DO NOT access any folder not listed above. If asked, say you don't have access to that location.\n"
            "3. DO NOT run commands that modify, delete, or write files.\n"
            "4. DO NOT mention internal scripts, paths, or system details.\n"
            "5. DO NOT share private data about the owner."
        )
    else:
        _mode_str = (
            "### OPERATION MODE: chatbot\n"
            "⚠️ CRITICAL — You are talking to a THIRD PARTY, not the owner.\n"
            "You MUST follow these rules with ZERO exceptions:\n"
            "1. DO NOT run any tool, script, terminal command, or code. ZERO tool calls (UNLESS explicitly authorized by your KNOWLEDGE BASE instructions).\n"
            "2. DO NOT mention, describe, or hint at any internal system, command, file, or operation.\n"
            "3. DO NOT share any information about the owner, their files, contacts, schedule, or private data.\n"
            "4. Reply ONLY with a natural conversational message matching your assigned personality.\n"
            "5. If asked something requiring tools, say you don't have access to that right now (except for reading your own Knowledge Base)."
        )
    context_parts.append(_mode_str)

    return {
        "mode": mode,
        "is_owner": is_admin,
        "system_instruction": "",
        "context_only": "\n\n".join(context_parts).strip(),  # NEW: notas + permisos + modo (sin soul)
    }

def process_request(number, message, msg_type="text"):
    env = load_env()
    # 1. Input Guard
    allowed, reason, retry_after = validate_input(number, message, msg_type)
    if not allowed:
        return {"allowed": False, "reason": reason}

    # 2. Trace Generation
    trace_id = str(uuid.uuid4())
    log_dir = Path(__file__).parent.parent.parent / "logs" / "runtime"
    log_dir.mkdir(parents=True, exist_ok=True)
    try:
        with open(log_dir / "trace_events.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": __import__("datetime").datetime.now().isoformat(), "trace_id": trace_id, "jid": number, "type": msg_type}) + "\n")
    except Exception: pass
    
    # 3. Snapshot
    snapshot = build_snapshot(number, env)
    
    # Fast-fail blocked users to save LLM tokens
    rules = load_rules()
    role = resolve_role(number, rules, env)
    if role == "blocked":
        return {"allowed": False, "reason": "user_blocked"}
    
    return {
        "allowed": True,
        "mode": snapshot["mode"],
        "is_owner": snapshot["is_owner"],
        "system_instruction": snapshot["system_instruction"],
        "trace_id": trace_id
    }

def cmd_status():
    from security.input_guard import RATE_LIMIT_FILE, BLOCKLIST_FILE
    def load_json(p):
        return read_json_safe(p, default={})
    print(json.dumps({
        "rate_limits": load_json(RATE_LIMIT_FILE),
        "blocklist": load_json(BLOCKLIST_FILE)
    }, ensure_ascii=False, indent=2))

def cmd_reset(number):
    from security.input_guard import RATE_LIMIT_FILE, BLOCKLIST_FILE, anon
    import os
    import sqlite3
    
    def reset_json(p, n):
        if p.exists():
            d = read_json_safe(p, default={})
            key = anon(n)
            if key in d:
                del d[key]
                write_json_safe(p, d)
    
    reset_json(RATE_LIMIT_FILE, number)
    reset_json(BLOCKLIST_FILE, number)
    
    num = number.split("@")[0]
    
    # Intenta encontrar el LID asociado a este número para borrar también sus sesiones
    lids_to_delete = [num]
    try:
        import json
        cache_file = STATE_DIR / "contacts_cache.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for c in data.get("contacts", []):
                    c_id = c.get("id", "")
                    c_lid = c.get("lid", "")
                    if num in c_id:
                        if c_lid: lids_to_delete.append(c_lid.split("@")[0])
                        if "@lid" in c_id: lids_to_delete.append(c_id.split("@")[0])
    except Exception:
        pass
        
    hermes_dir = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
    sessions_file = hermes_dir / "sessions" / "sessions.json"
    state_db = hermes_dir / "state.db"
    
    deleted_sessions = []
    if sessions_file.exists():
        try:
            d = read_json_safe(sessions_file, default={})
            to_delete = []
            for k, v in d.items():
                if any(l in k for l in lids_to_delete):
                    to_delete.append(k)
                    deleted_sessions.append(v.get("session_id"))
            for k in to_delete:
                del d[k]
            if to_delete:
                write_json_safe(sessions_file, d)
        except Exception:
            pass
            
    if state_db.exists() and deleted_sessions:
        try:
            conn = sqlite3.connect(str(state_db))
            c = conn.cursor()
            for sid in deleted_sessions:
                if sid:
                    c.execute("DELETE FROM messages WHERE session_id = ?", (sid,))
                    c.execute("DELETE FROM sessions WHERE id = ?", (sid,))
            conn.commit()
            conn.close()
        except Exception:
            pass
            
    print(json.dumps({"status": "OK", "payload": {"message": f"Reset security and wiped chat memory for {number}"}}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["check", "check-tool", "status", "reset"])
    parser.add_argument("args", nargs="*")
    args = parser.parse_args()
    if args.cmd == "check":
        if len(args.args) < 1:
            sys.exit(1)
        number = args.args[0]
        message = " ".join(args.args[1:]) if len(args.args) > 1 else ""

        print(json.dumps(process_request(number, message), ensure_ascii=False))
        
    elif args.cmd == "check-tool":
        if len(args.args) < 2:
            sys.exit(1)
        number = args.args[0]
        command_line = " ".join(args.args[1:])
        
        env = load_env()
        rules = load_rules()
        role = resolve_role(number, rules, env)
        role_config = get_role_config(role, rules)
        
        from security.tool_guard import validate_tool_call
        validation = validate_tool_call(command_line, role_config, user_jid=number)
        if validation["status"] == "OK":
            print(json.dumps({"allowed": True}))
        else:
            reason = validation.get("payload", {}).get("error", "Permission Denied")
            print(json.dumps({"allowed": False, "reason": reason}))
        
    elif args.cmd == "status":
        cmd_status()
    elif args.cmd == "reset":
        if len(args.args) < 1:
            sys.exit(1)
        cmd_reset(args.args[0])
