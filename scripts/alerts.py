#!/usr/bin/env python3
"""
🚨 Andoriña — Alerts & Forwarding Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Manages permanent listening rules for incoming messages.
"""

import sys, json
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.absolute()
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

def cmd_add(source, target, keywords=None):
    alerts = load_alerts()
    for a in alerts:
        if a["source"] == source and a["target"] == target:
            # Update existing rule (same source+target): just refresh keywords
            a["keywords"] = keywords
            save_alerts(alerts)
            out({"ok": True, "message": "Rule updated."})
            return
        elif a["source"] == source and a["target"] != target:
            # Same source but different target: update everything
            a["target"] = target
            a["keywords"] = keywords
            save_alerts(alerts)
            out({"ok": True, "message": f"Rule updated: now forwarding to {target}."})
            return

    alerts.append({"source": source, "target": target, "keywords": keywords})
    save_alerts(alerts)
    msg = f"Alert added: Messages from {source} will be forwarded to {target}"
    if keywords:
        msg += f" (filtered by keywords: {keywords})"
    out({"ok": True, "message": msg})

def cmd_remove(source):
    alerts = load_alerts()
    new_alerts = [a for a in alerts if a["source"] != source]
    if len(new_alerts) == len(alerts):
        out({"ok": False, "error": "Rule not found."})
        return
    save_alerts(new_alerts)
    out({"ok": True, "message": f"Alert(s) removed for source {source}"})

def cmd_list():
    out({"ok": True, "alerts": load_alerts()})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: alerts.py [add <source> <target> | remove <source> | list]")
        sys.exit(1)
        
    cmd = sys.argv[1].lower()
    
    if cmd == "add":
        if len(sys.argv) < 4:
            out({"ok": False, "error": "Missing source or target."})
            sys.exit(1)
            
        keywords = None
        if "--keywords" in sys.argv:
            idx = sys.argv.index("--keywords")
            if idx + 1 < len(sys.argv):
                keywords = sys.argv[idx + 1]
                
        cmd_add(sys.argv[2], sys.argv[3], keywords)
    elif cmd == "remove":
        if len(sys.argv) < 3:
            out({"ok": False, "error": "Missing source."})
            sys.exit(1)
        cmd_remove(sys.argv[2])
    elif cmd == "list":
        cmd_list()
    else:
        out({"ok": False, "error": "UNKNOWN_COMMAND"})
        sys.exit(1)
