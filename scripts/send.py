#!/usr/bin/env python3
"""
🚀 Andoriña — Messaging Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sends immediate text messages via the WhatsApp bridge.
"""

import sys
import json
import requests
from pathlib import Path

ENV_PATH = Path.home() / ".hermes" / ".env"
BRIDGE_URL = "http://localhost:3000"

if ENV_PATH.exists():
    try:
        # Explicit UTF-8 for portability
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "WHATSAPP_BRIDGE_URL" in line:
                BRIDGE_URL = line.split("=")[1].strip()
    except Exception:
        pass

def out(data):
    """Outputs JSON to stdout for AI consumption"""
    print(json.dumps(data, ensure_ascii=False))

def post_json(endpoint, data):
    try:
        # 15s timeout for message delivery
        r = requests.post(f"{BRIDGE_URL}{endpoint}", json=data, timeout=15)
        return r.json(), None
    except Exception as e:
        return None, str(e)

def bridge_ok():
    try:
        # Quick 2s health check
        r = requests.get(f"{BRIDGE_URL}/status", timeout=2)
        return r.status_code == 200, r.json()
    except Exception:
        return False, None

def normalize_number(num):
    num = str(num).strip().replace(" ", "").replace("+", "")
    if "@" not in num:
        if "-" in num: return f"{num}@g.us"
        return f"{num}@s.whatsapp.net"
    return num

def cmd_mensaje(chat_id_raw, message):
    if not (chat_id_raw.endswith("@s.whatsapp.net") or chat_id_raw.endswith("@g.us")):
        out({"ok": False, "error": "INVALID_CHAT_ID", "message": "❌ ERROR: Use a numeric ID. Run 'contacts.py search' first."})
        sys.exit(1)

    if not message.strip():
        out({"ok": False, "error": "EMPTY_MESSAGE"})
        sys.exit(1)

    chat_id = normalize_number(chat_id_raw)
    ok, _ = bridge_ok()
    if not ok:
        out({"ok": False, "error": "BRIDGE_OFFLINE", "message": "❌ WhatsApp is not connected."})
        sys.exit(1)

    res, err = post_json("/send", {"chatId": chat_id, "message": message})
    if err:
        out({"ok": False, "error": "NETWORK_ERROR", "detail": err})
    elif res and res.get("success"):
        out({"ok": True, "chatId": chat_id})
    else:
        out({"ok": False, "error": "SEND_FAILED", "detail": res.get("error", "Unknown") if res else "No response"})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: send.py [message|status]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "message":
        if len(sys.argv) < 4:
            print("Usage: send.py message <chatId> <text>")
            sys.exit(1)
        chat_id = sys.argv[2]
        text = " ".join(sys.argv[3:])
        cmd_mensaje(chat_id, text)
    elif cmd == "status":
        ok, data = bridge_ok()
        out({"ok": ok, "status": data})
