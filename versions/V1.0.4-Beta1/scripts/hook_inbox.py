#!/usr/bin/env python3
import sys
import json
import time
import re
import os
import subprocess
from pathlib import Path

def get_input():
    try:
        raw = sys.stdin.buffer.read()
        return raw.decode('utf-8')
    except Exception:
        return ""

SCRIPTS_DIR = Path(__file__).parent.absolute()
# Load .env to get the bot phone for filtering and admin for alerts
BOT_PHONE = ""
ADMIN_PHONE = ""
try:
    env_file = SCRIPTS_DIR.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("ANDORINA_BOT_PHONE="):
                BOT_PHONE = line.split("=", 1)[1].strip().replace("+", "")
            elif line.startswith("WHATSAPP_ALLOWED_USERS="):
                ADMIN_PHONE = line.split("=", 1)[1].split(",")[0].strip().replace("+", "")
except Exception: pass

INBOX_FILE = SCRIPTS_DIR.parent / "state" / "inbox.json"
MAX_HISTORY = 500

def main():
    raw_data = get_input()
    if not raw_data:
        return
    
    try:
        event = json.loads(raw_data)
        if event.get("event") not in ("message_received", "whatsapp:message"):
            return

        payload = event.get("payload", {})
        if not payload:
            return

        # Handle both standard Hermes fields and legacy patched fields
        sender = (payload.get("from") or payload.get("senderId") or "").replace("+", "")
        if BOT_PHONE and sender == BOT_PHONE:
            return

        chat_id = payload.get("chatId")
        if not chat_id:
            return  # Cannot process message without a chatId

        entry = {
            "chatId": chat_id,
            "from":   sender,
            "text":   payload.get("text") or payload.get("body") or "",
            "date":   payload.get("date") or payload.get("timestamp") or time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type":   payload.get("type") or payload.get("mediaType") or "text"
        }

        import fcntl
        INBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
        lock_file = INBOX_FILE.with_suffix(".lock")
        
        with open(lock_file, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            try:
                inbox = []
                if INBOX_FILE.exists():
                    try:
                        # Explicit UTF-8 encoding
                        data = json.loads(INBOX_FILE.read_text(encoding="utf-8"))
                        inbox = data if isinstance(data, list) else []
                    except Exception:
                        inbox = []

                inbox.append(entry)
                if len(inbox) > MAX_HISTORY:
                    inbox = inbox[-MAX_HISTORY:]

                # Atomic write to prevent partial JSON files if interrupted
                tmp_file = INBOX_FILE.with_suffix(".tmp")
                tmp_file.write_text(json.dumps(inbox, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp_file.replace(INBOX_FILE)
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN)

        # --- ALERTS LOGIC ---
        alerts_file = SCRIPTS_DIR.parent / "state" / "alerts.json"
        if alerts_file.exists():
            try:
                alerts = json.loads(alerts_file.read_text(encoding="utf-8"))
                for rule in alerts:
                    source = rule.get("source", "")
                    chat_id_str = entry.get("chatId") or ""
                    if source and source in chat_id_str:
                        target = rule.get("target", "")
                        keywords = rule.get("keywords")
                        
                        if keywords:
                            msg_text_raw = entry.get("text", "").strip().lower()
                            k_list = [k.strip().lower() for k in keywords.split(",")]
                            if not any(k in msg_text_raw for k in k_list):
                                continue
                                
                        if target == "OWNER" and ADMIN_PHONE:
                            target = ADMIN_PHONE + "@s.whatsapp.net"
                        
                        if target:
                            msg_text = entry.get("text", "").strip()
                            if not msg_text:
                                msg_text = "[Multimedia recibido, no se puede reenviar]"
                            
                            sender_label = entry.get("from") or source
                            # Shorten long IDs for readability
                            if "@" in sender_label:
                                sender_label = sender_label.split("@")[0]
                            alert_text = f"🚨 Alerta de {sender_label}:\n\"{msg_text}\""
                            
                            subprocess.Popen([sys.executable, str(SCRIPTS_DIR / "send.py"), "message", target, alert_text])
            except Exception:
                pass

    except Exception:
        pass

if __name__ == "__main__":
    main()
