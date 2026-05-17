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
except Exception: pass

from common import BRIDGE_URL, log_outgoing, post_json, out

def simulate_presence(chat_id, presence_type="composing"):
    """Simulates activity (Base Bridge only supports 'composing')"""
    try:
        # Base Hermes Bridge ignores 'presence' and always shows 'composing'
        post_json("/typing", {"chatId": chat_id}, silent_pacing=True)
        time.sleep(3.0)
    except Exception: pass

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

    import mimetypes
    mime_type, _ = mimetypes.guess_type(path)
    if not mime_type:
        ext = path.lower().split('.')[-1] if '.' in path else ''
        if ext == 'xcf': mime_type = 'image/x-xcf'
        elif ext == 'psd': mime_type = 'image/vnd.adobe.photoshop'
        else: mime_type = 'application/octet-stream'

    payload = {
        "chatId": chat_id,
        "filePath": str(Path(path).absolute()),
        "fileName": os.path.basename(path),
        "mimetype": mime_type,
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
