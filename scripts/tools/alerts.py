#!/usr/bin/env python3
"""
🚨 Andoriña — Alerts & Forwarding Engine
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
STATE_DIR   = SCRIPTS_DIR.parent / "state"

sys.path.append(str(SCRIPTS_DIR))
from utils.jids import normalize_jid, resolve_sender_label, jid_match


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


def notify_target(target, source, keywords=None):
    """Send a privacy notification to the alert target informing them."""
    # Don't notify OWNER keyword — they know what they're doing
    if target == "OWNER":
        return

    source_label = resolve_sender_label(source, STATE_DIR)
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
    # V1.6: validar JIDs no vacíos antes de normalizar
    if not source or not str(source).strip():
        out({"status": "ERROR", "error_code": "INTERNAL_ERROR", "payload": {"error": "Source JID cannot be empty."}})
        return
    if not target or not str(target).strip():
        out({"status": "ERROR", "error_code": "INTERNAL_ERROR", "payload": {"error": "Target JID cannot be empty."}})
        return
    source = normalize_jid(source)
    # V1.6: Normalizar target también — permite números parciales y
    # asegura que la deduplicación por JID sea consistente.
    if target != "OWNER":
        target = normalize_jid(target)
    alerts = load_alerts()
    for a in alerts:
        # V1.6: usar jid_match en lugar de igualdad exacta —
        # tolera formatos distintos del mismo JID (con/sin código de país)
        if jid_match(a["source"], source) and jid_match(a["target"], target):
            a["keywords"] = keywords
            save_alerts(alerts)
            out({"status": "OK", "error_code": "NONE", "payload": {"message": "Rule updated."}})
            return
        elif jid_match(a["source"], source) and not jid_match(a["target"], target):
            a["target"] = target
            a["keywords"] = keywords
            save_alerts(alerts)
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
    # V1.6: validar JID no vacío y normalizar
    if not source or not str(source).strip():
        out({"status": "ERROR", "error_code": "INTERNAL_ERROR", "payload": {"error": "Source JID cannot be empty."}})
        return
    source = normalize_jid(source)
    alerts = load_alerts()
    new_alerts = [a for a in alerts if not jid_match(a["source"], source)]
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
