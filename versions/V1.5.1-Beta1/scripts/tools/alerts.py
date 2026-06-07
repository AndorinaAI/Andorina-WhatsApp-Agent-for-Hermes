#!/usr/bin/env python3
"""
🚨 Andoriña — Alerts & Forwarding Engine (v1.5.1-Beta1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Manages permanent listening rules for incoming messages.
Now with automatic notification to the alert target.
"""

import sys
import json
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.absolute()
ALERTS_FILE = SCRIPTS_DIR.parent / "state" / "alerts.json"

def out(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))

def load_alerts():
    if not ALERTS_FILE.exists(): return []
    try: 
        data = json.loads(ALERTS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception: return []

def save_alerts(alerts):
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = ALERTS_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(alerts, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ALERTS_FILE)

def _resolve_label(source: str) -> str:
    """Resolve a JID/phone to a human-readable name.
    Priority: Google Contacts (contacts_cache) → bridge /groups → raw number."""
    raw = source.split("@")[0] if "@" in source else source
    _bare = raw.lstrip("+").lstrip("0")
    state_dir = SCRIPTS_DIR.parent / "state"

    # 1. Google Contacts cache (contacts_cache.json) — highest priority
    cache_file = state_dir / "contacts_cache.json"
    if cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text(encoding="utf-8"))
            for c in cache.get("contacts", []):
                c_id = (c.get("id") or c.get("chatId") or "").split("@")[0].lstrip("+").lstrip("0")
                if _bare and (_bare in c_id or c_id in _bare) and c.get("name"):
                    return c["name"]
        except Exception:
            pass

    # 2. Bridge /groups (for group JIDs)
    if "@g.us" in source or (len(raw) > 13 and raw.isdigit()):
        try:
            import urllib.request, os
            burl = os.environ.get("WHATSAPP_BRIDGE_URL", "http://localhost:3000")
            with urllib.request.urlopen(f"{burl}/groups", timeout=2) as resp:
                glist = json.loads(resp.read())
                giter = glist if isinstance(glist, list) else glist.get("groups", [])
                for g in giter:
                    g_id = (g.get("id") or g.get("chatId") or "").split("@")[0]
                    if raw and raw == g_id:
                        return g.get("name") or g.get("subject") or raw
        except Exception:
            pass

    return raw


def notify_target(target, source, keywords=None):
    """Send a privacy notification to the alert target informing them."""
    # Don't notify OWNER keyword — they know what they're doing
    if target == "OWNER":
        return

    source_label = _resolve_label(source)
    msg = f"🔔 Se ha configurado una alerta. Recibirás en este chat los mensajes de {source_label}"
    if keywords:
        msg += f" que contengan las palabras clave: {keywords}"
    msg += "."

    try:
        subprocess.Popen([
            sys.executable,
            str(SCRIPTS_DIR / "transport" / "send.py"),
            "message", target, msg
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def cmd_add(source, target, keywords=None):
    alerts = load_alerts()
    for a in alerts:
        if a["source"] == source and a["target"] == target:
            # Update existing rule (same source+target): just refresh keywords
            a["keywords"] = keywords
            save_alerts(alerts)
            out({"status": "OK", "error_code": "NONE", "payload": {"message": "Rule updated."}})
            return
        elif a["source"] == source and a["target"] != target:
            # Same source but different target: update everything
            a["target"] = target
            a["keywords"] = keywords
            save_alerts(alerts)
            # Notify the new target
            notify_target(target, source, keywords)
            out({"status": "OK", "error_code": "NONE", "payload": {"message": f"Rule updated: now forwarding to {target}."}})
            return

    alerts.append({"source": source, "target": target, "keywords": keywords})
    save_alerts(alerts)

    # Notify the target about the new alert
    notify_target(target, source, keywords)

    msg = f"Alert added: Messages from {source} will be forwarded to {target}"
    if keywords:
        msg += f" (filtered by keywords: {keywords})"
    out({"status": "OK", "error_code": "NONE", "payload": {"message": msg}})

def cmd_remove(source):
    alerts = load_alerts()
    new_alerts = [a for a in alerts if a["source"] != source]
    if len(new_alerts) == len(alerts):
        out({"status": "ERROR", "error_code": "INTERNAL_ERROR", "payload": {"error": "Rule not found."}})
        return
    save_alerts(new_alerts)
    out({"status": "OK", "error_code": "NONE", "payload": {"message": f"Alert(s) removed for source {source}"}})

def cmd_list():
    out({"status": "OK", "error_code": "NONE", "payload": {"alerts": load_alerts()}})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: alerts.py [add <source> <target> | remove <source> | list]")
        sys.exit(1)
        
    cmd = sys.argv[1].lower()
    
    if cmd == "add":
        if len(sys.argv) < 4:
            out({"status": "ERROR", "error_code": "INTERNAL_ERROR", "payload": {"error": "Missing source or target."}})
            sys.exit(1)
            
        keywords = None
        if "--keywords" in sys.argv:
            idx = sys.argv.index("--keywords")
            if idx + 1 < len(sys.argv):
                keywords = sys.argv[idx + 1]
                
        cmd_add(sys.argv[2], sys.argv[3], keywords)
    elif cmd == "remove":
        if len(sys.argv) < 3:
            out({"status": "ERROR", "error_code": "INTERNAL_ERROR", "payload": {"error": "Missing source."}})
            sys.exit(1)
        cmd_remove(sys.argv[2])
    elif cmd == "list":
        cmd_list()
    else:
        out({"status": "ERROR", "error_code": "INTERNAL_ERROR", "payload": {"error": "UNKNOWN_COMMAND"}})
        sys.exit(1)
