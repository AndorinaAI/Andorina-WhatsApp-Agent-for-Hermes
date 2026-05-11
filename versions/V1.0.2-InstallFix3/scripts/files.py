#!/usr/bin/env python3
"""
🚀 Andoriña — Multimedia Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sends images, videos, and documents with request pacing.
"""

import sys, json, time, os, urllib.request, urllib.error
from pathlib import Path

# Self-healing: Ensure bridge is patched
try:
    import bridge_health
    bridge_health.ensure_patched()
except: pass

import os
SCRIPTS_DIR = Path(__file__).parent.absolute()

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
ENV_PATH = HERMES_HOME / ".env"
BRIDGE_URL = "http://localhost:3000"

if ENV_PATH.exists():
    try:
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "WHATSAPP_BRIDGE_URL" in line and "=" in line:
                BRIDGE_URL = line.partition("=")[2].strip()
    except Exception: pass

BRIDGE_URL = os.environ.get("WHATSAPP_BRIDGE_URL", BRIDGE_URL)
INBOX_FILE = SCRIPTS_DIR.parent / "state" / "inbox.json"

def log_outgoing(chat_id, text, msg_type="text"):
    """Saves outgoing messages to the local inbox for self-visibility"""
    try:
        entry = {
            "chatId": chat_id,
            "from": "Me",
            "text": text,
            "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": msg_type
        }
        inbox = []
        if INBOX_FILE.exists():
            inbox = json.loads(INBOX_FILE.read_text(encoding="utf-8"))
        inbox.append(entry)
        if len(inbox) > 500: inbox = inbox[-500:]
        INBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
        INBOX_FILE.write_text(json.dumps(inbox, ensure_ascii=False, indent=2), encoding="utf-8")
    except: pass

def out(data):
    print(json.dumps(data, ensure_ascii=False))

def post_json(endpoint, data, attempt=0, silent_pacing=False):
    """Standardized POST with pacing"""
    url = f"{BRIDGE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if not silent_pacing:
        time.sleep(1.0)
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=120) as r:
            res = json.loads(r.read().decode('utf-8'))
            return res, None
    except Exception as e:
        return None, str(e)

def simulate_presence(chat_id, presence_type="composing"):
    """Simulates activity (Base Bridge only supports 'composing')"""
    try:
        # Base Hermes Bridge ignores 'presence' and always shows 'composing'
        post_json("/typing", {"chatId": chat_id}, silent_pacing=True)
        time.sleep(3.0)
    except: pass

def cmd_enviar(path, chat_id, is_voice=False):
    if not os.path.exists(path):
        out({"ok": False, "error": "FILE_NOT_FOUND", "path": path})
        sys.exit(1)

    if not os.access(path, os.R_OK):
        out({"ok": False, "error": "PERMISSION_DENIED", "path": path})
        sys.exit(1)

    # ✍️ Human Simulation: Show status before uploading
    presence = "recording" if is_voice else "composing"
    simulate_presence(chat_id, presence)

    payload = {
        "chatId": chat_id,
        "filePath": str(Path(path).absolute()),
        "caption": ""
    }
    
    if is_voice:
        payload["mediaType"] = "audio"
        payload["ptt"] = True

    res, err = post_json("/send-media", payload)

    if err:
        out({"ok": False, "error": "NETWORK_ERROR", "detail": err})
        sys.exit(1)
    elif res and res.get("success"):
        desc = "[Voice Note]" if is_voice else f"[File: {os.path.basename(path)}]"
        log_outgoing(chat_id, desc, msg_type="voice" if is_voice else "document")
        out({"ok": True, "chatId": chat_id, "file": os.path.basename(path)})
    else:
        out({"ok": False, "error": "SEND_FAILED", "detail": res.get("error", "Unknown") if res else "No response"})
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(1)
    file_path = sys.argv[1]
    target_id = sys.argv[2]
    voice_mode = "--voice" in sys.argv
    cmd_enviar(file_path, target_id, voice_mode)
