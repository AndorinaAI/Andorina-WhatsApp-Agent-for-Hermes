#!/usr/bin/env python3
"""
🚀 Andoriña — Inbox Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━
Reads and lists incoming WhatsApp messages from the local log.
"""

import sys, json
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.absolute()
sys.path.append(str(SCRIPTS_DIR))
from utils.safe_json import read_json_safe, write_json_safe

INBOX_FILE = SCRIPTS_DIR.parent / 'state' / 'inbox.json'

def load_canonical_map():
    """Builds {numeric_part -> canonical_JID} map from lid-mapping-*_reverse.json files.
    Allows resolving @lid chatIds to their @s.whatsapp.net equivalents and vice-versa.
    """
    import os
    num_to_canonical = {}
    try:
        hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
        session_dir = hermes_home / "whatsapp" / "session"
        if session_dir.is_dir():
            for f in session_dir.glob("lid-mapping-*_reverse.json"):
                lid_num = f.name.replace("lid-mapping-", "").replace("_reverse.json", "")
                try:
                    phone = json.loads(f.read_text(encoding="utf-8"))
                    if isinstance(phone, str) and phone:
                        phone_clean = phone.split("@")[0]
                        canonical = f"{phone_clean}@s.whatsapp.net"
                        num_to_canonical[lid_num] = canonical    # LID num  → canonical JID
                        num_to_canonical[phone_clean] = canonical  # phone num → canonical JID
                except Exception:
                    pass
    except Exception:
        pass
    return num_to_canonical

def out(data):
    """Outputs JSON to stdout for AI consumption"""
    print(json.dumps(data, ensure_ascii=False, indent=2))

def load_inbox():
    data = read_json_safe(INBOX_FILE, default=[])
    return data if isinstance(data, list) else []

def cmd_listar(filter_chats=None):
    inbox = load_inbox()
    cmap = load_canonical_map()
    def _to_canon(cid):
        if not cid: return cid
        return cmap.get(cid.split("@")[0], cid)

    chats = {}  # canonical_chatId → most recent msg
    for msg in inbox:
        chat_id = msg.get('chatId')
        if not chat_id:
            continue
        canon = _to_canon(chat_id)
        if filter_chats and canon not in filter_chats and chat_id not in filter_chats:
            continue
        # Keep the most recent message per canonical chat
        existing = chats.get(canon)
        if not existing or str(msg.get('date', '')) > str(existing.get('date', '')):
            chats[canon] = {**msg, 'chatId': canon}  # normalize chatId to canonical form

    sorted_chats = sorted(chats.values(), key=lambda x: str(x.get('date', '')), reverse=True)
    out({"status": "OK", "error_code": "NONE", "payload": {"total_chats": len(sorted_chats), "recent_chats": sorted_chats}})

def cmd_leer(chat_id, limit=50, filter_chats=None):
    inbox = load_inbox()
    
    chat_id = chat_id.strip()
    if "@" not in chat_id:
        if "-" in chat_id: chat_id += "@g.us"
        else: chat_id += "@s.whatsapp.net"
        
    if filter_chats and chat_id not in filter_chats:
        out({"status": "DENY", "error_code": "PERMISSION_DENIED", "payload": {"error": "You are not authorized to read this chat."}})
        sys.exit(1)
        
    cmap = load_canonical_map()
    def _to_canon(cid):
        if not cid: return cid
        return cmap.get(cid.split("@")[0], cid)
    target = _to_canon(chat_id)
    messages = [m for m in inbox if _to_canon(m.get('chatId', '')) == target]
    
    if str(limit).lower() != "all":
        try:
            limit_int = int(limit)
            if limit_int <= 0: messages = []
            else: messages = messages[-limit_int:]
        except ValueError:
            messages = messages[-50:]
            
    out({"status": "OK", "error_code": "NONE", "payload": {"chat_id": chat_id, "total_messages": len(messages), "messages": messages}})

def cmd_buscar_historial(keyword, filter_chats=None, max_days=None):
    inbox = load_inbox()
    kw = str(keyword).lower().strip()
    results = []
    
    cutoff = None
    if max_days:
        try:
            import datetime
            cutoff = (datetime.datetime.now() - datetime.timedelta(days=int(max_days))).isoformat()
        except Exception:
            pass

    for m in inbox:
        chat_id = m.get('chatId')
        if filter_chats and chat_id not in filter_chats:
            continue
            
        if cutoff and m.get('date') and m.get('date') < cutoff:
            continue
            
        text = str(m.get('text', '')).lower()
        if kw in text:
            results.append({
                "chatId": chat_id,
                "from": m.get('from'),
                "date": m.get('date'),
                "text": m.get('text')
            })
    
    sorted_results = sorted(results, key=lambda x: x.get('date', ''), reverse=True)[:50]
    out({"status": "OK", "error_code": "NONE", "payload": {"keyword": keyword, "total_matches": len(results), "matches": sorted_results}})

def cmd_delete(chat_id):
    inbox = load_inbox()
    chat_id = chat_id.strip()
    if "@" not in chat_id:
        if "-" in chat_id: chat_id += "@g.us"
        else: chat_id += "@s.whatsapp.net"
    
    original_len = len(inbox)
    cmap = load_canonical_map()
    def _to_canon(cid):
        if not cid: return cid
        return cmap.get(cid.split("@")[0], cid)
    target = _to_canon(chat_id)
    inbox = [m for m in inbox if _to_canon(m.get('chatId', '')) != target]
    
    if len(inbox) < original_len:
        if write_json_safe(INBOX_FILE, inbox):
            out({"status": "OK", "error_code": "NONE", "payload": {"message": f"Chat {chat_id} deleted from inbox."}})
        else:
            out({"status": "ERROR", "error_code": "WRITE_ERROR", "payload": {"error": "Failed to write inbox."}})
    else:
        out({"status": "ERROR", "error_code": "NOT_FOUND", "payload": {"error": "Chat not found in inbox."}})

def parse_filter_chats():
    if "--filter-chats" in sys.argv:
        idx = sys.argv.index("--filter-chats")
        if idx + 1 < len(sys.argv):
            chats = [c.strip() for c in sys.argv[idx+1].split(",")]
            # Remove from argv
            sys.argv = sys.argv[:idx] + sys.argv[idx+2:]
            return chats
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: inbox.py [list|read <chatId>|search <keyword>|delete <chatId>]")
        sys.exit(1)
    
    filter_chats = parse_filter_chats()
    cmd = sys.argv[1]
    
    if cmd in ("listar", "list"):
        cmd_listar(filter_chats=filter_chats)
    elif cmd in ("leer", "read") and len(sys.argv) >= 3:
        limit = 50
        if len(sys.argv) >= 4:
            limit = sys.argv[3]
        cmd_leer(sys.argv[2], limit, filter_chats=filter_chats)
    elif cmd in ("buscar", "search") and len(sys.argv) >= 3:
        max_days = None
        if "--days" in sys.argv:
            idx = sys.argv.index("--days")
            if idx + 1 < len(sys.argv):
                max_days = sys.argv[idx + 1]
                sys.argv = sys.argv[:idx] + sys.argv[idx+2:]
                
        keyword = " ".join(sys.argv[2:])
        cmd_buscar_historial(keyword, filter_chats=filter_chats, max_days=max_days)
    elif cmd in ("borrar", "delete") and len(sys.argv) >= 3:
        cmd_delete(sys.argv[2])
    else:
        out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "INVALID_COMMAND"}})
        sys.exit(0)
