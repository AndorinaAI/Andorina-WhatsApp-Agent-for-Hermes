#!/usr/bin/env python3
"""
🚀 Andoriña — Messaging Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sends immediate text messages with request pacing and self-healing.
"""

import sys, json, time, urllib.request, urllib.error
from pathlib import Path

# Self-healing: Ensure bridge is patched
try:
    import bridge_health
    bridge_health.ensure_patched()
except Exception: pass

from common import BRIDGE_URL, log_outgoing, post_json, out

def simulate_typing(chat_id, text_length):
    """Simulates natural typing delay (Base Bridge only supports 'composing')"""
    try:
        # Base Hermes Bridge ignores 'presence' field and uses 'composing' by default
        post_json("/typing", {"chatId": chat_id}, silent_pacing=True)
        delay = min(max(1.5, text_length / 15), 5.0)
        time.sleep(delay)
    except Exception: pass

def cmd_mensaje(chat_id_raw, message):
    if not (chat_id_raw.endswith("@s.whatsapp.net") or chat_id_raw.endswith("@g.us")):
        out({"ok": False, "error": "INVALID_CHAT_ID"})
        sys.exit(1)

    if not message.strip():
        out({"ok": False, "error": "EMPTY_MESSAGE"})
        sys.exit(1)

    chat_id = chat_id_raw.strip()
    
    # ✍️ Human Simulation: Show 'typing...' before sending
    simulate_typing(chat_id, len(message))
    
    res, err = post_json("/send", {"chatId": chat_id, "message": message})

    if err:
        out({"ok": False, "error": "NETWORK_ERROR", "detail": err})
        sys.exit(1)
    elif res and res.get("success"):
        log_outgoing(chat_id, message)
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
                out({"ok": r.status == 200, "status": json.loads(r.read().decode('utf-8'))})
        except Exception: out({"ok": False})
    else:
        out({"ok": False, "error": "UNKNOWN_COMMAND", "detail": f"Command '{cmd}' not found in send.py. Did you mean to use files.py for sending files?"})
        sys.exit(1)
