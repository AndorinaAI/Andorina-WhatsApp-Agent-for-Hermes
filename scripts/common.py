import os
import json
import time
import urllib.request
import urllib.error
import fcntl
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.absolute()
STATE_DIR   = SCRIPTS_DIR.parent / "state"

# Helper to locate the appropriate .env file
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))

def get_env_path(profile_path):
    # FIRST priority: local .env next to the skill folder (always wins)
    local_env = SCRIPTS_DIR.parent / ".env"
    if local_env.exists():
        return local_env

    # Secondary: flat skills/andorina hierarchy (Hermes >= 2025)
    skill_env = profile_path / "skills" / "andorina" / ".env"
    if skill_env.exists():
        return skill_env

    # Last resort: global Hermes .env
    return profile_path / ".env"

ENV_PATH = get_env_path(HERMES_HOME)

def load_env(env_path=None):
    """Load .env file into a dict, filtering comments and empty lines."""
    path = env_path or ENV_PATH
    env = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return env

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

