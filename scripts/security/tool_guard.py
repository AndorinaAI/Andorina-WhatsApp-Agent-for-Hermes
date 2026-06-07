import shlex
import sys
from pathlib import Path

# Fix relative import
sys.path.append(str(Path(__file__).parent.parent))
from security.sec_types import ToolContract


def _log_deny(reason: str, cmd: str):
    import json
    from datetime import datetime
    log_dir = Path(__file__).parent.parent.parent / "logs" / "security"
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / "deny_events.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(), "component": "tool_guard", "reason": reason, "cmd": cmd}) + "\n")

def _log_audit_owner(cmd: str, jid: str):
    import json
    from datetime import datetime
    log_dir = Path(__file__).parent.parent.parent / "logs" / "security"
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / "owner_audit.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(), "jid": jid, "cmd": cmd}) + "\n")

def validate_tool_call(command_line: str, role_config: dict = None, user_jid: str = None, execution_source: str = "user_request") -> ToolContract:
    """
    Validates a tool command line before execution.
    Checks syntax, permissions, path traversal, and allowed chats.
    """
    if role_config is None:
        role_config = {}
    
    allowed_folders = role_config.get("allowed_folders", [])
    perms = role_config.get("permissions", [])
    is_owner = "all" in perms

    try:
        parts = shlex.split(command_line)
    except Exception:
        _log_deny("syntax", command_line)
        return {"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "syntax"}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}

    if not parts:
        _log_deny("empty", command_line)
        return {"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "empty"}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}
        
    script_name = ""
    subcmd = ""
    for i, p in enumerate(parts):
        if p.endswith(".py"):
            script_name = Path(p).name
            if i + 1 < len(parts) and not parts[i+1].startswith("-"):
                subcmd = parts[i+1]
            break
            
    if not script_name:
        # Permite acceso al OS crudo si es Owner, si tiene permiso os:execute o si es la soul de _hermes_
        if is_owner:
            _log_audit_owner(command_line, user_jid)
            return {"status": "OK", "error_code": "NONE", "payload": {"command": command_line}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}

        if role_config.get("custom_soul") == "_hermes_" or "os:execute" in perms:
            return {"status": "OK", "error_code": "NONE", "payload": {"command": command_line}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}

        # Validate granular OS permissions
        os_cmd = parts[0].lower()
        required_os_perm = None
        
        # Mapping OS commands to permissions
        os_perm_map = {
            "os:ls": ["ls", "dir", "find", "tree"],
            "os:read": ["cat", "head", "tail", "grep", "less", "wc", "stat", "file"],
            "os:write": ["echo", "tee", "cp", "mv", "touch"],
            "os:mkdir": ["mkdir"],
            "os:delete": ["rm", "rmdir", "unlink"],
            "os:net": ["curl", "wget", "ping", "nslookup", "ssh"],
            "os:env": ["env", "export", "printenv"],
            "os:proc": ["ps", "top", "kill", "pkill", "pgrep"],
            "os:archive": ["tar", "zip", "unzip", "gzip"],
            "os:python": ["python", "python3"]
        }
        
        for perm, cmds in os_perm_map.items():
            if os_cmd in cmds:
                required_os_perm = perm
                break
                
        if not required_os_perm:
            required_os_perm = "os:exec" # Default for unknown binaries
            
        if required_os_perm not in perms:
            _log_deny(f"forbidden_system_command_missing_{required_os_perm}", command_line)
            return {"status": "DENY", "error_code": "PERMISSION_DENIED", "payload": {"error": f"Lacks required permission: {required_os_perm}"}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}
            
        # Path restriction check for OS commands
        allowed_os_paths = role_config.get("allowed_os_paths", [])
        
        # We must check all arguments that are not flags.
        # If allowed_os_paths is empty but they try to pass ANY non-flag argument to an OS command, deny it.
        for arg in parts[1:]:
            if arg.startswith("-") or arg.startswith(">") or arg.startswith("<") or "=" in arg: 
                continue
                
            abs_arg = str(Path(arg).absolute())
            
            if not allowed_os_paths:
                _log_deny("os_path_not_allowed_empty_whitelist", command_line)
                return {"status": "DENY", "error_code": "PERMISSION_DENIED", "payload": {"error": f"No OS paths allowed for this role. Denied access to: {arg}"}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}
                
            allowed = any(abs_arg.startswith(str(Path(ap).absolute())) for ap in allowed_os_paths)
            if not allowed:
                _log_deny("os_path_not_allowed", command_line)
                return {"status": "DENY", "error_code": "PERMISSION_DENIED", "payload": {"error": f"Path not allowed: {arg}"}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}
                        
        # -- command_rules validation (granular argument restrictions) --
        # JID-level command_rules override role-level command_rules
        role_cmd_rules = role_config.get("command_rules", {})
        jid_cmd_rules  = role_config.get("jid_command_rules", {})
        merged_cmd_rules = {**role_cmd_rules, **jid_cmd_rules}
        cmd_rule = merged_cmd_rules.get(os_cmd, {})
        if cmd_rule and not is_owner:
            denied_args = cmd_rule.get("denied_args", [])
            for arg in parts[1:]:
                if arg in denied_args:
                    _log_deny(f"command_rules_denied_arg_{os_cmd}_{arg}", command_line)
                    return {"status": "DENY", "error_code": "PERMISSION_DENIED",
                            "payload": {"error": f"Argument '{arg}' not allowed for command '{os_cmd}'"},
                            "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}

        return {"status": "OK", "error_code": "NONE", "payload": {"command": command_line}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}

    req_perm = None
    if script_name == "send.py":
        if subcmd == "broadcast": req_perm = "broadcast"
        else: req_perm = "send_text"
    elif script_name == "files.py":
        if "--voice" in parts: req_perm = "send_voice"
        else: req_perm = "send_file"
    elif script_name == "inbox.py":
        if subcmd == "search": req_perm = "search_history"
        else: req_perm = "read_inbox"
    elif script_name == "contacts.py":
        if subcmd == "search": req_perm = "search_contacts"
        elif subcmd == "groups": req_perm = "list_groups"
        elif subcmd == "refresh": req_perm = "refresh_contacts"
        elif subcmd.startswith("note-"): req_perm = "add_note"
    elif script_name == "agenda.py":
        if subcmd == "auto-schedule": req_perm = "schedule_msg"
        elif subcmd == "list": req_perm = "list_agenda"
        elif subcmd == "remove": req_perm = "remove_agenda"
        elif subcmd == "recurring":
            r_sub = parts[parts.index("recurring")+1] if "recurring" in parts and parts.index("recurring")+1 < len(parts) else ""
            if r_sub == "add": req_perm = "recurring_add"
            elif r_sub == "list": req_perm = "recurring_list"
            elif r_sub == "remove": req_perm = "recurring_remove"
    elif script_name == "alerts.py": req_perm = "add_alert"
    elif script_name == "diag.py": req_perm = "run_diag"
    elif script_name == "bridge_health.py": req_perm = "run_repair"
    elif script_name == "wipe_logs.py": req_perm = "wipe_logs"
    elif script_name == "orchestrator.py":
        if subcmd == "status": req_perm = "guard_status"
        elif subcmd == "reset": req_perm = "guard_reset"
    elif script_name == "admin_cli.py":
        if subcmd == "role":
            r_sub = parts[parts.index("role")+1] if "role" in parts and parts.index("role")+1 < len(parts) else ""
            if r_sub == "set": req_perm = "set_role"
            elif r_sub in ["get", "list"]: req_perm = "get_role"
            elif r_sub == "remove": req_perm = "remove_role"
        elif subcmd == "chatbot": req_perm = "chatbot_toggle"
        elif subcmd == "away": req_perm = "away_toggle"
        elif subcmd == "soul":
            s_sub = parts[parts.index("soul")+1] if "soul" in parts and parts.index("soul")+1 < len(parts) else ""
            if s_sub == "set": req_perm = "set_soul"
            elif s_sub == "get": req_perm = "get_soul"

    if not is_owner and req_perm and req_perm not in perms:
        _log_deny(f"missing_permission_{req_perm}", command_line)
        return {"status": "DENY", "error_code": "PERMISSION_DENIED", "payload": {"error": f"Lacks required permission: {req_perm}"}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}

    # Unknown .py scripts not in the whitelist above → require explicit 'run_script' permission
    if not is_owner and req_perm is None and script_name and script_name.endswith(".py"):
        if "run_script" not in perms:
            _log_deny("unknown_script_no_run_script_perm", command_line)
            return {"status": "DENY", "error_code": "PERMISSION_DENIED", "payload": {"error": f"Unknown script '{script_name}'. Requires 'run_script' permission."}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}

    # If it's files.py, enforce allowed_folders
    if script_name == "files.py" and not is_owner:
        file_path = None
        for i, p in enumerate(parts):
            if p.endswith("files.py") and i + 1 < len(parts):
                file_path = parts[i + 1]
                break
        
        if file_path:
            abs_path = str(Path(file_path).absolute())
            soul_knowledge_dir = role_config.get("soul_knowledge_dir")
            allowed_by_folder = allowed_folders and any(abs_path.startswith(str(Path(f).absolute())) for f in allowed_folders)
            allowed_by_soul = bool(soul_knowledge_dir and abs_path.startswith(soul_knowledge_dir))
            
            if not allowed_by_folder and not allowed_by_soul:
                _log_deny("folder_not_allowed", command_line)
                return {"status": "DENY", "error_code": "PERMISSION_DENIED", "payload": {"error": "folder_not_allowed"}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}

    # Enforce allowed_chats
    allowed_chats = role_config.get("allowed_chats", [])
    if allowed_chats and not is_owner:
        target_chats = []
        script_idx = -1
        for i, p in enumerate(parts):
            if p.endswith(".py"):
                script_idx = i
                break
                
        if script_idx != -1:
            if script_name == "send.py":
                if subcmd == "message" and script_idx + 2 < len(parts):
                    target_chats = [parts[script_idx + 2]]
                elif subcmd == "broadcast" and script_idx + 2 < len(parts):
                    # For broadcast, the syntax is send.py broadcast "msg" "id1,id2"
                    # But if msg is not quoted it can be multiple parts. So we should search for a comma?
                    # Or maybe it's just the last argument.
                    # In send.py: cmd_broadcast(args[0], args[1].split(","), file_path) where args = sys.argv[2:] (so parts[2] is broadcast, parts[3] is msg, parts[4] is chat_id)
                    # wait, args = sys.argv[2:]. So args[0] is sys.argv[2] which is the first word after broadcast.
                    # It's safer to just check ALL parts for something resembling a chat id.
                    pass # We will do a generic scan instead below
            elif script_name == "files.py" and script_idx + 2 < len(parts):
                target_chats = [parts[script_idx + 2]]
            elif script_name == "inbox.py" and subcmd == "read" and script_idx + 2 < len(parts):
                target_chats = [parts[script_idx + 2]]
            elif script_name == "agenda.py":
                if subcmd == "auto-schedule" and script_idx + 2 < len(parts):
                    target_chats = [parts[script_idx + 2]]
                elif subcmd == "recurring" and "add" in parts:
                    idx = parts.index("add")
                    if idx + 1 < len(parts):
                        target_chats = [parts[idx + 1]]
                        
        # Fallback generic scanner to find ANY chat ID in the arguments to be safe
        for p in parts:
            if "@s.whatsapp.net" in p or "@g.us" in p:
                for c in p.split(","):
                    c_clean = c.strip()
                    if c_clean and (c_clean.endswith("@s.whatsapp.net") or c_clean.endswith("@g.us")):
                        if c_clean not in target_chats:
                            target_chats.append(c_clean)
                    
        for tc in target_chats:
            tc_clean = tc.split("@")[0]
            is_allowed = False
            for ac in allowed_chats:
                ac_clean = ac.split("@")[0]
                if ac_clean == "self" and user_jid:
                    if tc_clean == user_jid.split("@")[0]:
                        is_allowed = True
                        break
                elif ac_clean == tc_clean:
                    is_allowed = True
                    break
            
            if not is_allowed:
                _log_deny("chat_not_allowed", command_line)
                return {"status": "DENY", "error_code": "PERMISSION_DENIED", "payload": {"error": f"Not allowed to interact with chat: {tc}"}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}

    return {"status": "OK", "error_code": "NONE", "payload": {"command": command_line}, "trace_id": "", "tool_call_id": "", "tool_chain_id": "", "parent_trace_id": None}
