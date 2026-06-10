#!/usr/bin/env python3
"""
🚀 Andoriña — Messaging Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sends immediate text messages with request pacing and self-healing.
"""

import sys, json, time, urllib.request, urllib.error
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

# Self-healing: Ensure bridge is patched
try:
    import utils.bridge_health as bridge_health
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

def cmd_mensaje(chat_id_raw, message, file_path=None):
    if not (chat_id_raw.endswith("@s.whatsapp.net") or chat_id_raw.endswith("@g.us")):
        out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "INVALID_CHAT_ID"}})
        sys.exit(1)

    if not message.strip() and not file_path:
        out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "EMPTY_MESSAGE"}})
        sys.exit(1)

    chat_id = chat_id_raw.strip()
    simulate_typing(chat_id, len(message) if message else 0)
    
    if file_path:
        import mimetypes, os
        target_path = Path(file_path).resolve()
        str_path = str(target_path)
        mime_type, _ = mimetypes.guess_type(str_path)
        if not mime_type:
            ext = str_path.lower().split('.')[-1] if '.' in str_path else ''
            if ext == 'xcf': mime_type = 'image/x-xcf'
            elif ext == 'psd': mime_type = 'image/vnd.adobe.photoshop'
            else: mime_type = 'application/octet-stream'

        payload = {
            "chatId": chat_id,
            "filePath": str_path,
            "fileName": os.path.basename(str_path),
            "mimetype": mime_type,
            "caption": message
        }
        res, err = post_json("/send-media", payload)
    else:
        payload = {"chatId": chat_id, "message": message}
        res, err = post_json("/send", payload)

    if err:
        out({"status": "ERROR", "error_code": "FATAL", "payload": {"error": "NETWORK_ERROR", "detail": err}})
        sys.exit(0)
    elif res and res.get("success"):
        log_outgoing(chat_id, message)
        out({"status": "OK", "error_code": "NONE", "payload": {"chatId": chat_id}})
    else:
        out({"status": "ERROR", "error_code": "FATAL", "payload": {"error": "SEND_FAILED", "detail": res.get("error", "Unknown") if res else "No response"}})
        sys.exit(0)

def cmd_broadcast(message, chat_ids, file_path=None):
    import random
    results = []
    for cid in chat_ids:
        cid = cid.strip()
        if not (cid.endswith("@s.whatsapp.net") or cid.endswith("@g.us")):
            continue
        simulate_typing(cid, len(message) if message else 0)
        
        if file_path:
            import mimetypes, os
            target_path = Path(file_path).resolve()
            str_path = str(target_path)
            mime_type, _ = mimetypes.guess_type(str_path)
            if not mime_type:
                ext = str_path.lower().split('.')[-1] if '.' in str_path else ''
                if ext == 'xcf': mime_type = 'image/x-xcf'
                elif ext == 'psd': mime_type = 'image/vnd.adobe.photoshop'
                else: mime_type = 'application/octet-stream'

            payload = {
                "chatId": cid,
                "filePath": str_path,
                "fileName": os.path.basename(str_path),
                "mimetype": mime_type,
                "caption": message
            }
            res, err = post_json("/send-media", payload, silent_pacing=True)
        else:
            payload = {"chatId": cid, "message": message}
            res, err = post_json("/send", payload, silent_pacing=True)
        
        if err or not (res and res.get("success")):
            results.append({"chatId": cid, "status": "failed", "error": err or (res.get("error", "Unknown") if res else "Unknown")})
        else:
            log_outgoing(cid, message)
            results.append({"chatId": cid, "status": "sent"})
        
        time.sleep(random.uniform(2.0, 5.0))
        
    out({"status": "OK", "error_code": "NONE", "payload": {"results": results}})

def parse_args():
    if len(sys.argv) < 2: sys.exit(0)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    file_path = None
    if "--file" in args:
        idx = args.index("--file")
        if idx + 1 < len(args):
            file_path = args[idx+1]
        args = args[:idx] + args[idx+2:]
    return cmd, args, file_path

if __name__ == "__main__":
    cmd, args, file_path = parse_args()
    if cmd == "message":
        if len(args) < 2: sys.exit(1)
        cmd_mensaje(args[0], " ".join(args[1:]), file_path)
    elif cmd == "broadcast":
        if len(args) < 2: sys.exit(1)
        cmd_broadcast(args[0], args[1].split(","), file_path)
    elif cmd == "status":
        try:
            with urllib.request.urlopen(f"{BRIDGE_URL}/health", timeout=2) as r:
                out({"status": "OK" if r.status == 200 else "ERROR", "error_code": "NONE" if r.status == 200 else "BRIDGE_ERROR", "payload": {"status": json.loads(r.read().decode('utf-8'))}})
        except Exception as e: out({"status": "ERROR", "error_code": "NETWORK_ERROR", "payload": {"error": str(e)}})
    else:
        out({"status": "ERROR", "error_code": "FATAL", "payload": {"error": "UNKNOWN_COMMAND", "detail": f"Command '{cmd}' not found in send.py. Did you mean to use files.py for sending files?"}})
        sys.exit(0)
