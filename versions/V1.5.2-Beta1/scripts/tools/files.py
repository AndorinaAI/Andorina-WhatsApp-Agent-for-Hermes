#!/usr/bin/env python3
"""
🚀 Andoriña — Multimedia Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sends images, videos, and documents with request pacing.
"""

import sys
import time
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

# Self-healing: Ensure bridge is patched
try:
    import utils.bridge_health as bridge_health
    bridge_health.ensure_patched()
except Exception: pass

from common import log_outgoing, post_json, out

def simulate_presence(chat_id, presence_type="composing"):
    """Simulates activity (Base Bridge only supports 'composing')"""
    try:
        # Base Hermes Bridge ignores 'presence' and always shows 'composing'
        post_json("/typing", {"chatId": chat_id}, silent_pacing=True)
        time.sleep(3.0)
    except Exception: pass

def cmd_enviar(path, chat_id, is_voice=False, caption=""):
    # --- PATH TRAVERSAL PROTECTION ---
    try:
        target_path = Path(path).resolve()
        str_path = str(target_path)
    except Exception:
        out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "INVALID_PATH", "path": str(path)}})
        sys.exit(0)

    # 1. Block access to critical system directories
    blocked_prefixes = ["/etc/", "/var/", "/proc/", "/sys/", "/dev/", "/root/", "/boot/"]
    if any(str_path.startswith(b) for b in blocked_prefixes):
        out({"status": "DENY", "error_code": "PERMISSION_DENIED", "payload": {"reason": "system_directory_blocked"}})
        sys.exit(0)

    # 2. Check existence using resolved path
    if not target_path.exists():
        out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "FILE_NOT_FOUND", "path": str_path}})
        sys.exit(0)

    # 3. Check readability
    if not os.access(target_path, os.R_OK):
        out({"status": "DENY", "error_code": "PERMISSION_DENIED", "payload": {"reason": "file_not_readable"}})
        sys.exit(0)

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
        "filePath": str_path,
        "fileName": os.path.basename(path),
        "mimetype": mime_type,
        "caption": caption
    }
    
    if is_voice:
        payload["mediaType"] = "audio"
        payload["ptt"] = True

    res, err = post_json("/send-media", payload)

    if err:
        out({"status": "ERROR", "error_code": "INTERNAL_ERROR", "payload": {"error": "NETWORK_ERROR", "detail": err}})
        sys.exit(0)
    elif res and res.get("success"):
        desc = "[Voice Note]" if is_voice else f"[File: {os.path.basename(path)}]"
        log_outgoing(chat_id, desc, msg_type="voice" if is_voice else "document")
        out({"status": "OK", "error_code": "NONE", "payload": {"chatId": chat_id, "file": os.path.basename(path)}})
    else:
        out({"status": "ERROR", "error_code": "FATAL", "payload": {"error": "SEND_FAILED", "detail": res.get("error", "Unknown") if res else "No response"}})
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(1)
    file_path = sys.argv[1]
    target_id = sys.argv[2]
    voice_mode = "--voice" in sys.argv
    args = [a for a in sys.argv[3:] if a != "--voice"]
    caption = " ".join(args) if args else ""
    cmd_enviar(file_path, target_id, voice_mode, caption)
