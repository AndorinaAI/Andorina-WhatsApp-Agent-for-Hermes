#!/usr/bin/env python3
"""
🚀 Andoriña — Multimedia Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sends files (images, PDFs, videos) and voice notes.
"""

import sys
import json
import os
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

def cmd_send(file_path, chat_id, as_voice=False):
    if not (chat_id.endswith("@s.whatsapp.net") or chat_id.endswith("@g.us")):
        out({"ok": False, "error": "INVALID_CHAT_ID", "message": "❌ ERROR: Use a numeric ID."})
        sys.exit(1)

    abs_path = os.path.abspath(os.path.expanduser(file_path))
    if not os.path.exists(abs_path):
        out({"ok": False, "error": "FILE_NOT_FOUND", "path": abs_path})
        sys.exit(1)

    payload = {"chatId": chat_id, "path": abs_path}
    endpoint = "/send-voice" if as_voice else "/send-file"

    try:
        # 120s timeout for large multimedia uploads
        r = requests.post(f"{BRIDGE_URL}{endpoint}", json=payload, timeout=120)
        res = r.json()
        if res.get("success"):
            out({"ok": True, "file": os.path.basename(abs_path), "chatId": chat_id})
        else:
            out({"ok": False, "error": "BRIDGE_ERROR", "detail": res.get("error", "Unknown error")})
    except Exception as e:
        out({"ok": False, "error": "NETWORK_ERROR", "detail": str(e)})

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: files.py send <path> <chatId> [--voice]")
        sys.exit(1)
    
    action = sys.argv[1]
    if action == "send":
        path = sys.argv[2]
        target = sys.argv[3]
        is_voice = "--voice" in sys.argv
        cmd_send(path, target, is_voice)
    else:
        print(f"Unknown command: {action}")
        sys.exit(1)
