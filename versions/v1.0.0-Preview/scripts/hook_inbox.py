#!/usr/bin/env python3
import sys
import json
import time
import re
from pathlib import Path

# Use binary stdin for absolute robustness with high-unicode characters
def get_input():
    try:
        raw = sys.stdin.buffer.read()
        return raw.decode('utf-8')
    except:
        return ""

INBOX_FILE = Path.home() / ".hermes" / "skills" / "messaging" / "andorina" / "state" / "inbox.json"
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

        entry = {
            "chatId": payload.get("chatId"),
            "from":   payload.get("from"),
            "text":   payload.get("text", ""),
            "date":   payload.get("date", time.strftime("%Y-%m-%dT%H:%M:%S")),
            "type":   payload.get("type", "text")
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
