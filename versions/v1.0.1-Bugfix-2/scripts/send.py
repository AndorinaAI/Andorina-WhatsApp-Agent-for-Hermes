#!/usr/bin/env python3
"""
🚀 Andoriña — Messaging Engine (Hardened Edition)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sends immediate text messages with request pacing and self-healing.
"""

import sys, json, time, urllib.request, urllib.error
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
    
    # 🕊️ Request Pacing: Breathe before sending to avoid bridge saturation
    time.sleep(0.5)
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode('utf-8'))
            if not res.get("success") and attempt < max_attempts:
                import bridge_health
                if bridge_health.ensure_patched():
                    time.sleep(2)
                    return post_json(endpoint, data, attempt=attempt + 1)
            return res, None
    except Exception as e:
        if attempt < max_attempts:
            import bridge_health
            if bridge_health.ensure_patched():
                time.sleep(2)
                return post_json(endpoint, data, attempt=attempt + 1)
        return None, str(e)

def cmd_mensaje(chat_id_raw, message):
    if not (chat_id_raw.endswith("@s.whatsapp.net") or chat_id_raw.endswith("@g.us")):
        out({"ok": False, "error": "INVALID_CHAT_ID"})
        sys.exit(1)

    if not message.strip():
        out({"ok": False, "error": "EMPTY_MESSAGE"})
        sys.exit(1)

    chat_id = chat_id_raw.strip()
    res, err = post_json("/send", {"chatId": chat_id, "message": message})

    if err:
        out({"ok": False, "error": "NETWORK_ERROR", "detail": err})
        sys.exit(1)
    elif res and res.get("success"):
        out({"ok": True, "chatId": chat_id})
    else:
        out({"ok": False, "error": "SEND_FAILED", "detail": res.get("error", "Unknown") if res else "No response"})
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "message":
        if len(sys.argv) < 4: sys.exit(1)
        chat_id = sys.argv[2]
        text = " ".join(sys.argv[3:])
        cmd_mensaje(chat_id, text)
    elif cmd == "status":
        try:
            with urllib.request.urlopen(f"{BRIDGE_URL}/health", timeout=2) as r:
                out({"ok": r.status == 200, "status": json.loads(r.read().decode())})
        except: out({"ok": False})
