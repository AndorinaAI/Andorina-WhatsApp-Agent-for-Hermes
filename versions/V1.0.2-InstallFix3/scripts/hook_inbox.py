#!/usr/bin/env python3
import sys
import json
import time
import re
from pathlib import Path

# Use binary stdin for absolute robustness with high-unicode characters
import os

def get_input():
    try:
        raw = sys.stdin.buffer.read()
        return raw.decode('utf-8')
    except:
        return ""

SCRIPTS_DIR = Path(__file__).parent.absolute()
# Load .env to get the bot phone for filtering
BOT_PHONE = ""
try:
    env_file = SCRIPTS_DIR.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("ANDORINA_BOT_PHONE="):
                BOT_PHONE = line.split("=", 1)[1].strip().replace("+", "")
except: pass

INBOX_FILE = SCRIPTS_DIR.parent / "state" / "inbox.json"
MAX_HISTORY = 500

def main():
    raw_data = get_input()
    if not raw_data:
        return
    
    try:
        event = json.loads(raw_data)
        if event.get("event") != "message_received":
            return

        payload = event.get("payload", {})
        if not payload:
            return

        # Handle both standard Hermes fields and legacy patched fields
        sender = (payload.get("from") or payload.get("senderId") or "").replace("+", "")
        if BOT_PHONE and sender == BOT_PHONE:
            return

        entry = {
            "chatId": payload.get("chatId"),
            "from":   sender,
            "text":   payload.get("text") or payload.get("body") or "",
            "date":   payload.get("date") or payload.get("timestamp") or time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type":   payload.get("type") or payload.get("mediaType") or "text"
        }

        inbox = []
        if INBOX_FILE.exists():
            try:
                # Explicit UTF-8 encoding
                inbox = json.loads(INBOX_FILE.read_text(encoding="utf-8"))
            except:
                inbox = []

        inbox.append(entry)
        if len(inbox) > MAX_HISTORY:
            inbox = inbox[-MAX_HISTORY:]

        INBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Explicit UTF-8 encoding
        INBOX_FILE.write_text(json.dumps(inbox, ensure_ascii=False, indent=2), encoding="utf-8")

    except Exception:
        pass

if __name__ == "__main__":
    main()
