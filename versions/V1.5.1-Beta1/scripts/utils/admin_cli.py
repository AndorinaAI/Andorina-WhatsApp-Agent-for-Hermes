#!/usr/bin/env python3
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))
# Add scripts dir to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from common import out, load_env
from security.rbac import RULES_FILE, resolve_role, clean_number

STATE_DIR = Path(__file__).parent.parent.parent / "state"
CHATBOT_FILE = STATE_DIR / "chatbot.json"
AWAY_FILE = STATE_DIR / "away.json"

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception: return {}

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)

def extract_number(jid):
    return clean_number(jid)

# -- Role commands --
def cmd_role_set(jid, role):
    rules = read_json(RULES_FILE)
    if "roles" not in rules: rules["roles"] = {}
    if role not in rules["roles"]:
        return out({"status": "ERROR", "error_code": "INVALID_ARGS", "payload": {"error": f"Role '{role}' does not exist"}})
    
    num = extract_number(jid)
    if "jids" not in rules: rules["jids"] = {}
    if num not in rules["jids"]: rules["jids"][num] = {}
    
    rules["jids"][num]["role"] = role
    write_json(RULES_FILE, rules)
    out({"status": "OK", "error_code": "NONE", "payload": {"message": f"Assigned role '{role}' to {jid}"}})

def cmd_role_get(jid):
    rules = read_json(RULES_FILE)
    env = load_env()
    role = resolve_role(jid, rules, env)
    out({"status": "OK", "error_code": "NONE", "payload": {"jid": jid, "role": role}})

def cmd_role_remove(jid):
    rules = read_json(RULES_FILE)
    num = extract_number(jid)
    if "jids" in rules and num in rules["jids"]:
        if "role" in rules["jids"][num]:
            del rules["jids"][num]["role"]
            write_json(RULES_FILE, rules)
    out({"status": "OK", "error_code": "NONE", "payload": {"message": f"Removed role from {jid}"}})

def cmd_role_list():
    rules = read_json(RULES_FILE)
    env = load_env()
    assigned = {}
    
    # 1. Add explicitly assigned JSON roles
    for num, data in rules.get("jids", {}).items():
        if data.get("role"):
            assigned[num] = data["role"]
            
    # 2. Add owner from .env (overrides JSON)
    for n in env.get("WHATSAPP_ALLOWED_USERS", "").split(","):
        clean_n = clean_number(n)
        if clean_n:
            assigned[clean_n] = "owner"
            
    out({"status": "OK", "error_code": "NONE", "payload": {"assigned_roles": assigned}})

# -- Soul commands --
def cmd_soul_set(jid, text):
    rules = read_json(RULES_FILE)
    num = extract_number(jid)
    if "jids" not in rules: rules["jids"] = {}
    if num not in rules["jids"]: rules["jids"][num] = {}
    
    rules["jids"][num]["custom_soul"] = text
    write_json(RULES_FILE, rules)
    out({"status": "OK", "error_code": "NONE", "payload": {"message": f"Set personality for {jid}"}})

def cmd_soul_get(jid):
    rules = read_json(RULES_FILE)
    num = extract_number(jid)
    entry = rules.get("jids", {}).get(num, {})
    soul = entry.get("custom_soul", "")
    out({"status": "OK", "error_code": "NONE", "payload": {"jid": jid, "soul": soul}})

# -- Chatbot commands --
def cmd_chatbot_on():
    data = read_json(CHATBOT_FILE)
    data["enabled"] = True
    write_json(CHATBOT_FILE, data)
    out({"status": "OK", "error_code": "NONE", "payload": {"message": "Chatbot globally ENABLED"}})

def cmd_chatbot_off():
    data = read_json(CHATBOT_FILE)
    data["enabled"] = False
    write_json(CHATBOT_FILE, data)
    out({"status": "OK", "error_code": "NONE", "payload": {"message": "Chatbot globally DISABLED"}})

def cmd_chatbot_mute(jid):
    data = read_json(CHATBOT_FILE)
    if "muted_jids" not in data: data["muted_jids"] = []
    num = extract_number(jid)
    if num not in data["muted_jids"]:
        data["muted_jids"].append(num)
        write_json(CHATBOT_FILE, data)
    out({"status": "OK", "error_code": "NONE", "payload": {"message": f"Muted chatbot for {jid}"}})

def cmd_chatbot_unmute(jid):
    data = read_json(CHATBOT_FILE)
    if "muted_jids" not in data: data["muted_jids"] = []
    num = extract_number(jid)
    if num in data["muted_jids"]:
        data["muted_jids"].remove(num)
        write_json(CHATBOT_FILE, data)
    out({"status": "OK", "error_code": "NONE", "payload": {"message": f"Unmuted chatbot for {jid}"}})

def cmd_chatbot_status():
    data = read_json(CHATBOT_FILE)
    out({"status": "OK", "error_code": "NONE", "payload": data})

# -- Away commands --
def cmd_away_set(text):
    if text.lower() == "off":
        data = read_json(AWAY_FILE)
        data["enabled"] = False
        write_json(AWAY_FILE, data)
        out({"status": "OK", "error_code": "NONE", "payload": {"message": "Away auto-reply DISABLED"}})
    else:
        data = read_json(AWAY_FILE)
        data["enabled"] = True
        data["message"] = text
        if "cooldown" not in data: data["cooldown"] = {}
        write_json(AWAY_FILE, data)
        out({"status": "OK", "error_code": "NONE", "payload": {"message": "Away auto-reply ENABLED"}})

def cmd_away_status():
    data = read_json(AWAY_FILE)
    out({"status": "OK", "error_code": "NONE", "payload": {"enabled": data.get("enabled", False), "message": data.get("message", "")}})


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
        
    cmd = sys.argv[1]
    
    if cmd == "role":
        if len(sys.argv) < 3: sys.exit(1)
        sub = sys.argv[2]
        if sub == "set" and len(sys.argv) == 5:
            cmd_role_set(sys.argv[3], sys.argv[4])
        elif sub == "get" and len(sys.argv) == 4:
            cmd_role_get(sys.argv[3])
        elif sub == "remove" and len(sys.argv) == 4:
            cmd_role_remove(sys.argv[3])
        elif sub == "list":
            cmd_role_list()
        else:
            sys.exit(1)
            
    elif cmd == "soul":
        if len(sys.argv) < 3: sys.exit(1)
        sub = sys.argv[2]
        if sub == "set" and len(sys.argv) == 5:
            cmd_soul_set(sys.argv[3], sys.argv[4])
        elif sub == "get" and len(sys.argv) == 4:
            cmd_soul_get(sys.argv[3])
        else:
            sys.exit(1)
            
    elif cmd == "chatbot":
        if len(sys.argv) < 3: sys.exit(1)
        sub = sys.argv[2]
        if sub == "on": cmd_chatbot_on()
        elif sub == "off": cmd_chatbot_off()
        elif sub == "mute" and len(sys.argv) == 4: cmd_chatbot_mute(sys.argv[3])
        elif sub == "unmute" and len(sys.argv) == 4: cmd_chatbot_unmute(sys.argv[3])
        elif sub == "status": cmd_chatbot_status()
        else: sys.exit(1)
        
    elif cmd == "away":
        if len(sys.argv) < 3: sys.exit(1)
        sub = sys.argv[2]
        if sub == "status":
            cmd_away_status()
        elif sub == "off":
            cmd_away_set("off")
        else:
            cmd_away_set(sys.argv[2])
            
    else:
        out({"status": "ERROR", "error_code": "UNKNOWN_COMMAND", "payload": {"error": f"Unknown command {cmd}"}})
