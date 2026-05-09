#!/usr/bin/env python3
"""
🚀 Andoriña — Smart Scheduling Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Manages scheduled messages and integrates with system cron.
Supports formats: HH:MM, DD/MM HH:MM, DD HH:MM (24h format).
"""

import sys
import json
import re
from datetime import datetime
from pathlib import Path
import subprocess

# Ensure we can import from the same directory
sys.path.append(str(Path(__file__).parent))

from send import post_json

AGENDA_FILE = Path.home() / ".hermes" / "skills" / "messaging" / "andorina" / "state" / "agenda.json"

def out(data):
    """Outputs JSON to stdout for AI consumption"""
    print(json.dumps(data, ensure_ascii=False))

def load_agenda():
    if not AGENDA_FILE.exists():
        try:
            AGENDA_FILE.parent.mkdir(parents=True, exist_ok=True)
        except Exception: pass
        return {}
    try:
        # Explicit UTF-8 for portability
        return json.loads(AGENDA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_agenda(agenda):
    try:
        # Explicit UTF-8 and robust error handling for disk writes
        AGENDA_FILE.write_text(json.dumps(agenda, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception as e:
        print(f"❌ Critical Error: Could not write to agenda file: {e}", file=sys.stderr)
        return False

def cmd_list():
    agenda = load_agenda()
    items = []
    for mid, data in agenda.items():
        items.append({
            "id": mid,
            "to": data.get("name"),
            "time": data.get("time"),
            "message": data.get("message")
        })
    out({"ok": True, "agenda": items})

def cmd_send_pending(msg_id):
    """Triggered by cron to deliver a message"""
    agenda = load_agenda()
    if msg_id not in agenda:
        sys.exit(1)
    
    data = agenda[msg_id]
    res, err = post_json("/send", {"chatId": data["chatId"], "message": data["message"]})
    
    if res and res.get("success"):
        del agenda[msg_id]
        save_agenda(agenda)
        out({"ok": True, "message_sent": True, "id": msg_id})
    else:
        sys.exit(1)

def cmd_remove(msg_id):
    agenda = load_agenda()
    if msg_id in agenda:
        del agenda[msg_id]
        if save_agenda(agenda):
            out({"ok": True, "message": f"Message {msg_id} cancelled."})
        else:
            out({"ok": False, "error": "DISK_ERROR"})
    else:
        out({"ok": False, "error": "ID_NOT_FOUND"})

def parse_cron_schedule(time_str):
    time_str = time_str.strip()
    # DD/MM HH:MM or DD-MM HH:MM
    m = re.match(r"(\d{1,2})[/-](\d{1,2})\s+(\d{1,2}):(\d{1,2})", time_str)
    if m:
        day, mon, h, minute = m.groups()
        return f"{int(minute)} {int(h)} {int(day)} {int(mon)} *"
    # DD HH:MM
    m = re.match(r"(\d{1,2})\s+(\d{1,2}):(\d{1,2})", time_str)
    if m:
        day, h, minute = m.groups()
        return f"{int(minute)} {int(h)} {int(day)} * *"
    # HH:MM
    m = re.match(r"(\d{1,2}):(\d{1,2})", time_str)
    if m:
        h, minute = m.groups()
        return f"{int(minute)} {int(h)} * * *"
    return "* * * * *"

def cmd_auto_schedule(chat_id, time_str, message):
    if not (chat_id.endswith("@s.whatsapp.net") or chat_id.endswith("@g.us")):
        out({"ok": False, "error": "INVALID_CHAT_ID", "message": "❌ ERROR: Use a numeric ID."})
        sys.exit(1)
    
    # Millisecond precision to avoid collisions in high-frequency scheduling
    msg_id = f"msg_{datetime.now().strftime('%H%M%S%f')[:-3]}"
    agenda = load_agenda()
    agenda[msg_id] = {
        "chatId": chat_id,
        "name": chat_id.split("@")[0],
        "time": time_str,
        "message": message
    }
    
    if not save_agenda(agenda):
        out({"ok": False, "error": "STORAGE_FAILED"})
        sys.exit(1)
    
    cron_expr = parse_cron_schedule(time_str)
    scripts_path = Path(__file__).parent.absolute()

    # Wrap command in quotes to handle paths with spaces
    full_cmd = f'python3 "{scripts_path}/agenda.py" send {msg_id}'
    cmd = [
        "hermes", "cron", "create",
        "--name", f"WhatsApp_{msg_id}",
        "--schedule", cron_expr,
        "--repeat", "1",
        "--command", full_cmd
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        out({"ok": True, "id": msg_id, "time": time_str})
    except Exception:
        out({"ok": False, "error": "CRON_CREATION_FAILED"})
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: agenda.py [list|send|remove|auto-schedule]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "list":
        cmd_list()
    elif cmd == "send" and len(sys.argv) > 2:
        cmd_send_pending(sys.argv[2])
    elif cmd == "remove" and len(sys.argv) > 2:
        cmd_remove(sys.argv[2])
    elif cmd == "auto-schedule" and len(sys.argv) > 4:
        cmd_auto_schedule(sys.argv[2], sys.argv[3], " ".join(sys.argv[4:]))
    else:
        print("Invalid command or missing arguments.")
        sys.exit(1)
