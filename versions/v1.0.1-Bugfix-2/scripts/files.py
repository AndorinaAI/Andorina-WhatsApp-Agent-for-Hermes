#!/usr/bin/env python3
"""
🚀 Andoriña — Multimedia Engine (Hardened Edition)
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

ENV_PATH = Path.home() / ".hermes" / ".env"
BRIDGE_URL = "http://localhost:3000"

if ENV_PATH.exists():
    try:
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "WHATSAPP_BRIDGE_URL" in line and "=" in line:
                BRIDGE_URL = line.partition("=")[2].strip()
    except Exception: pass

def out(data):
    print(json.dumps(data, ensure_ascii=False))

def post_json(endpoint, data, attempt=0):
    """Standardized POST with pacing and finite retries"""
    max_attempts = 3
    url = f"{BRIDGE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    # 🕊️ Request Pacing: Essential for heavy media uploads
    time.sleep(0.5)
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=120) as r:
            res = json.loads(r.read().decode('utf-8'))
            if not res.get("success") and attempt < max_attempts:
                import bridge_health
                if bridge_health.ensure_patched():
                    time.sleep(3)
                    return post_json(endpoint, data, attempt=attempt + 1)
            return res, None
    except Exception as e:
        if attempt < max_attempts:
            import bridge_health
            if bridge_health.ensure_patched():
                time.sleep(3)
                return post_json(endpoint, data, attempt=attempt + 1)
        return None, str(e)

def cmd_enviar(path, chat_id, is_voice=False):
    if not os.path.exists(path):
        out({"ok": False, "error": "FILE_NOT_FOUND", "path": path})
        sys.exit(1)

    if not os.access(path, os.R_OK):
        out({"ok": False, "error": "PERMISSION_DENIED", "path": path})
        sys.exit(1)

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
