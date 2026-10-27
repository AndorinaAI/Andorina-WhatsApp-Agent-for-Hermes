import os
import json
import time
import urllib.request
import urllib.error
try:
    from filelock import FileLock
    _HAS_FILELOCK = True
except ImportError:
    import fcntl
    _HAS_FILELOCK = False
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.absolute()

def _get_state_dir():
    """Resolve state directory — uses plugin-data to separate user data from plugin install tree."""
    data_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
    state = data_home / "plugin-data" / "andorina"
    return state

STATE_DIR = _get_state_dir()

# Helper to locate the appropriate .env file
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))

def get_env_path(profile_path):
    # FIRST priority: local .env next to the plugin/skill folder (always wins)
    local_env = SCRIPTS_DIR.parent / ".env"
    if local_env.exists():
        return local_env

    # Secondary: flat skills/andorina or plugins/andorina hierarchy
    # V2.0: Check plugin layout first, then skill layout
    plugin_env = profile_path / "plugins" / "andorina" / ".env"
    if plugin_env.exists():
        return plugin_env
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
INBOX_FILE = _get_state_dir() / "inbox.json"

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
        
        lock_path = INBOX_FILE.with_suffix(".lock")
        if _HAS_FILELOCK:
            from filelock import FileLock
            with FileLock(str(lock_path), timeout=5):
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
    except Exception: pass



# ── Per-chat send cooldown (anti-spam) ────────────────────────────────────
import json as _json
from pathlib import Path as _Path

SEND_COOLDOWN_FILE = STATE_DIR / "send_cooldown.json"
SEND_COOLDOWN_SECS = int(os.environ.get("ANDORINA_SEND_COOLDOWN_SECS", 15))

def check_send_cooldown(chat_id: str) -> bool:
    """Check if enough time has passed since the last send to this chat.
    Returns True if allowed, False if cooldown still active."""
    try:
        SEND_COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if SEND_COOLDOWN_FILE.exists():
            data = _json.loads(SEND_COOLDOWN_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
        now = time.time()
        last = data.get(chat_id, 0)
        if now - last < SEND_COOLDOWN_SECS:
            remaining = int(SEND_COOLDOWN_SECS - (now - last))
            return False
        return True
    except Exception:
        return True  # fail open — don't block sends on cooldown errors

def record_send_cooldown(chat_id: str) -> None:
    """Record a send to this chat for cooldown tracking."""
    try:
        SEND_COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if SEND_COOLDOWN_FILE.exists():
            data = _json.loads(SEND_COOLDOWN_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
        data[chat_id] = time.time()
        tmp = SEND_COOLDOWN_FILE.with_suffix(".tmp")
        tmp.write_text(_json.dumps(data), encoding="utf-8")
        tmp.replace(SEND_COOLDOWN_FILE)
    except Exception:
        pass  # fail open

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

