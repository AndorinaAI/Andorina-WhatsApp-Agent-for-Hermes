import os, sys, json, time, urllib.request, urllib.error, fcntl
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.absolute()

# The user requested to review the .env path logic.
# I will use the same logic as auth.py and contacts.py to unify it,
# but fallback to HERMES_HOME/.env just in case.
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))

def get_env_path(profile_path):
    skills_root = profile_path / "skills"
    category = "messaging"
    if (skills_root / "message").exists() and not (skills_root / "messaging").exists():
        category = "message"
    skill_env = skills_root / category / "andorina" / ".env"
    
    if skill_env.exists():
        return skill_env
    return profile_path / ".env"

ENV_PATH = get_env_path(HERMES_HOME)

BRIDGE_URL = "http://localhost:3000"

if ENV_PATH.exists():
    try:
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "WHATSAPP_BRIDGE_URL" in line and "=" in line:
                BRIDGE_URL = line.partition("=")[2].strip()
    except Exception: pass

BRIDGE_URL = os.environ.get("WHATSAPP_BRIDGE_URL", BRIDGE_URL)
INBOX_FILE = SCRIPTS_DIR.parent / "state" / "inbox.json"

def log_outgoing(chat_id, text, msg_type="text"):
    """Saves outgoing messages to the local inbox for self-visibility"""
    try:
        entry = {
            "chatId": chat_id,
            "from": "Me",
            "text": text,
            "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "type": msg_type
        }
        INBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
        lock_file = INBOX_FILE.with_suffix(".lock")
        
        with open(lock_file, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            try:
                inbox = []
                if INBOX_FILE.exists():
                    try:
                        data = json.loads(INBOX_FILE.read_text(encoding="utf-8"))
                        inbox = data if isinstance(data, list) else []
                    except Exception: pass
                inbox.append(entry)
                # Keep same history limit as hook_inbox (500)
                if len(inbox) > 500: inbox = inbox[-500:]
                
                tmp_file = INBOX_FILE.with_suffix(".tmp")
                tmp_file.write_text(json.dumps(inbox, ensure_ascii=False, indent=2), encoding="utf-8")
                tmp_file.replace(INBOX_FILE)
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN)
    except Exception: pass

def post_json(endpoint, data, attempt=0, silent_pacing=False):
    """Standardized POST with pacing"""
    url = f"{BRIDGE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if not silent_pacing:
        time.sleep(1.0)
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req, timeout=120) as r:
            res = json.loads(r.read().decode('utf-8'))
            return res, None
    except Exception as e:
        return None, str(e)

def out(data):
    print(json.dumps(data, ensure_ascii=False))

