import sys
import json
import re
import time
import hashlib
from pathlib import Path

# Fix relative import to reach scripts/common.py
sys.path.append(str(Path(__file__).parent.parent))
from common import load_env
from utils.safe_json import read_json_safe, write_json_safe

SCRIPTS_DIR = Path(__file__).parent.parent.absolute()
STATE_DIR   = SCRIPTS_DIR.parent / "state"
STATE_FILE  = STATE_DIR / "rate_limits.json"
RATE_LIMIT_FILE = STATE_FILE
BLOCKLIST_FILE = STATE_DIR / "blocklist.json"

_env_vars = load_env()
COOLDOWN_SECS     = int(_env_vars.get("GUARD_COOLDOWN_SECS", 300))
MAX_MSGS_PER_HOUR = int(_env_vars.get("GUARD_MAX_MSGS_PER_HOUR", 10))
MAX_CHARS_INPUT   = int(_env_vars.get("GUARD_MAX_CHARS_INPUT", 500))
CLEANUP_AFTER_H   = int(_env_vars.get("GUARD_CLEANUP_AFTER_H", 24))

DANGEROUS_PATTERNS = [
    r"(show|list|give|send|tell|dime|pásame|enseñame|muestra|envía|manda|dame|get|borra|elimina|copy|copia).{0,40}(file|folder|archivo|carpeta|\.env|config|password|contraseña|token|key|llave|secret|secreto|ssh)",
    r"\b(borra|elimina|delete|wipe|format|clean|vacía|rm|del).{0,50}(archivo|folder|fichero|carpeta|state|config|env|todo|all)",
    r"\bcat\s+[/\.~]",
    r"\b(ls|pwd|whoami|ifconfig|uname|ps aux|printenv|env|sudo|su )\b",
    r"\.\./",
    r"(/etc/|/root/|/var/|/proc/|/sys/)",
    r"\brm\s+-[rRf]{1,3}\s",
    r"\b(chmod|chown|mkfs|fdisk|dd\s+if|shred|wipefs)\b",
    r"\b(nc|ncat|netcat|nmap|tcpdump)\b",
    r"who (owns|runs|controls)|who is (the |your )?(owner|admin|boss)|quién es (tu |el )?(dueño|jefe|admin|propietario)",
    r"(tell|dime).{0,30}(name|email|phone|address|number|nombre|correo|teléfono|dirección).{0,30}(owner|admin|dueño|jefe)",
    r"(where|dónde).{0,30}(do you|are you|estás|vives)",
    r"(what is|cuál es).{0,30}(address|location|ip|server|dirección|ubicación|servidor)",
    r"(execute|run|exec|launch|bash|python|curl|wget|ejecuta|lanza)\s",
    r"`[^`]{1,200}`|\$\([^)]{1,200}\)",
    r"(ignore|forget|override|ignora|olvida|salta).{0,30}(instructions|rules|prompt|instrucciones|reglas)",
    r"system prompt|how are you configured|cómo estás programado|cuál es tu configuración",
    r"jailbreak|DAN mode|developer mode|no restrictions|no limits|god mode|modo dios|sin restricciones",
    r"act as|pretend (you are|to be)|you are now|from now on you are|actúa como|haz como si|ahora eres",
    r"(locate|track|find|where is|localiza|rastrea|dónde está).{0,30}(person|user|persona|usuario)",
    r"phone number of|address of|teléfono de|dirección de",
    r"\||\>|\>\>|\<|\&",
]

def clean_number(n):
    return re.sub(r"[^\d]", "", n)

from security.rbac import is_owner

def anon(number):
    return hashlib.sha256(number.encode('utf-8')).hexdigest()[:16]

def load_state():
    data = read_json_safe(STATE_FILE, default={})
    return data if isinstance(data, dict) else {}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    write_json_safe(STATE_FILE, state)

def prune_state(state):
    now = time.time()
    return {k: v for k, v in state.items() if now - v.get("last", 0) < CLEANUP_AFTER_H * 3600}

def check_rate(number, state):
    now  = time.time()
    h    = anon(number)
    d    = state.get(h, {})
    last = d.get("last", 0)
    cnt  = d.get("count_hour", 0)
    t0   = d.get("hour_start", now)

    if now - t0 > 3600:
        cnt = 0; t0 = now

    if now - last < COOLDOWN_SECS:
        return False, "cooldown", int(COOLDOWN_SECS - (now - last))

    if cnt >= MAX_MSGS_PER_HOUR:
        return False, "hourly_limit", 0

    return True, "", 0

def register_msg(number, state):
    now = time.time()
    h   = anon(number)
    d   = state.get(h, {})
    t0  = d.get("hour_start", now)
    cnt = d.get("count_hour", 0)
    if now - t0 > 3600:
        cnt = 0; t0 = now
    state[h] = {"last": now, "count_hour": cnt + 1, "hour_start": t0}
    return state


def _log_deny(reason: str, msg: str):
    import json
    from datetime import datetime
    log_dir = SCRIPTS_DIR.parent / "logs" / "security"
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / "deny_events.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(), "component": "input_guard", "reason": reason, "input_len": len(msg)}) + "\n")

def validate_input(number, message, msg_type="text"):
    """Validates an incoming message (Rate limiting, lengths, injections)"""
    env = load_env()
    state = prune_state(load_state())

    sender_is_owner = is_owner(number, env)
    
    if not sender_is_owner:
        if msg_type != "text":
            _log_deny("unsupported_type", message)
            return False, "unsupported_type", 0

        if len(message) > MAX_CHARS_INPUT:
            _log_deny("too_long", message)
            return False, "too_long", 0

        msg_l = message.lower()
        msg_norm = re.sub(r"[\s\.\-\_]", "", msg_l)
        
        for pat in DANGEROUS_PATTERNS:
            if re.search(pat, msg_l, re.IGNORECASE) or re.search(pat, msg_norm, re.IGNORECASE):
                _log_deny("dangerous", message)
                return False, "dangerous", 0

        ok, reason, secs = check_rate(number, state)
        if not ok:
            _log_deny(reason, message)
            return False, reason, secs

        state = register_msg(number, state)
        save_state(state)
        
    return True, "OK", 0
