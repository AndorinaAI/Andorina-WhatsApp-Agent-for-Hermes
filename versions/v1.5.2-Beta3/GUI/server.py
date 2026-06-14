#!/usr/bin/env python3
"""
🕊️ Andoriña — GUI Backend Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Serves the web GUI and provides a REST API to manage the skill.
Uses only Python stdlib. Does NOT modify any existing script.

Usage: python3 GUI/server.py [--port 8888]
"""

import http.server
import json
import sys
import os
import subprocess
import urllib.parse
import urllib.request
import re
import time
import threading
import base64
import queue
import hashlib
import secrets
from pathlib import Path
from datetime import datetime

# Import setup_lib from parent directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    import setup_lib
except ImportError:
    setup_lib = None

# ── Activity Log & Install Log ─────────────────────────────────
INSTALL_LOG = queue.Queue()
LOG_BUFFER = []
LOG_MAX = 200

def log_event(level, msg, data=None):
    entry = {"ts": datetime.now().isoformat(), "level": level, "msg": msg}
    if data: entry["data"] = data
    LOG_BUFFER.append(entry)
    if len(LOG_BUFFER) > LOG_MAX: LOG_BUFFER.pop(0)
    print(f"[{entry['ts']}] [{level.upper()}] {msg}", flush=True)

PORT = 8888
GUI_DIR = Path(__file__).parent.absolute()
STATIC_DIR = GUI_DIR / "static"
SOURCE_DIR = GUI_DIR.parent

# Dynamically locate active skill installation
PROJECT_DIR = GUI_DIR.parent


SCRIPTS_DIR = PROJECT_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))  # Allow importing from scripts/utils
# Import canonical permissions list from rbac.py (single source of truth)
try:
    from security.rbac import AVAILABLE_PERMISSIONS as _RBAC_PERMISSIONS
except ImportError:
    _RBAC_PERMISSIONS = None
STATE_DIR = PROJECT_DIR / "state"
SOULS_DIR = STATE_DIR / "souls"
NOTES_DIR = STATE_DIR / "notes"
RECURRING_DIR = STATE_DIR / "recurring"
UPLOADS_DIR = STATE_DIR / "uploads"
WEBHOOKS_FILE = STATE_DIR / "webhooks.json"

def _run_soul_sync():
    """Re-sync Sub-Soul channel_prompts to Hermes config.yaml after any soul change."""
    try:
        sync_script = SCRIPTS_DIR / "security" / "soul_sync.py"
        if sync_script.exists():
            subprocess.run([sys.executable, str(sync_script)],
                          capture_output=True, timeout=10, env=os.environ.copy())
    except Exception:
        pass  # Non-fatal: sync will happen on next gateway restart

# ── Webhook Alerts helpers ────────────────────────────────────────────────────
def _load_webhooks():
    data = read_json(WEBHOOKS_FILE)
    return data if isinstance(data, list) else []

def _save_webhooks(hooks):
    WEBHOOKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = WEBHOOKS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(hooks, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(WEBHOOKS_FILE)

def _detect_public_url():
    """Return (url, source) for the public webhook base URL."""
    # 1. Env var set by user
    url = os.environ.get("ANDORINA_WEBHOOK_URL", "").strip().rstrip("/")
    if url:
        return url, "env"
    # 2. Named Cloudflare tunnel config
    try:
        import re as _re
        cf_cfg = Path.home() / ".cloudflared" / "config.yml"
        if cf_cfg.exists():
            text = cf_cfg.read_text(encoding="utf-8", errors="ignore")
            m = _re.search(r'hostname:\s*(\S+)', text)
            if m:
                return f"https://{m.group(1)}", "cloudflare-named"
    except Exception:
        pass
    # 3. Fallback to localhost (GUI server port)
    gui_port = os.environ.get("GUI_PORT", str(PORT))
    return f"http://localhost:{gui_port}", "local"

def _dispatch_webhook(hook, payload_dict):
    """Send WhatsApp messages to all targets of a webhook rule."""
    try:
        import re as _re
        template = hook.get("template") or "🔔 *{{_name}}*\n{{_summary}}"
        name = hook.get("name", "Webhook")
        # Build _summary from top-level string/number fields
        summary_parts = []
        for k, v in payload_dict.items():
            if isinstance(v, (str, int, float, bool)) and not k.startswith("_"):
                summary_parts.append(f"{k}: {v}")
        summary = "\n".join(summary_parts[:10])
        full_json = json.dumps(payload_dict, ensure_ascii=False, indent=2)[:1500]
        # Replace placeholders
        msg = template
        msg = msg.replace("{{_name}}", name)
        msg = msg.replace("{{_summary}}", summary)
        msg = msg.replace("{{_json}}", full_json)
        # Replace {{field}} → payload_dict.field
        def _replace_field(match):
            key = match.group(1).strip()
            parts = key.split(".")
            val = payload_dict
            for p in parts:
                if isinstance(val, dict):
                    val = val.get(p, "")
                else:
                    val = ""
            return str(val)
        msg = _re.sub(r"\{\{([^{}]+)\}\}", _replace_field, msg)
        # Send to each target
        send_script = SCRIPTS_DIR / "transport" / "send.py"
        for target in hook.get("targets", []):
            if target and send_script.exists():
                subprocess.Popen(
                    [sys.executable, str(send_script), "message", target, msg],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
    except Exception:
        pass

# Create required dirs
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
SOULS_DIR.mkdir(parents=True, exist_ok=True)

# ── Auth & Sessions ───────────────────────────────────────────
SESSION_FILE = STATE_DIR / "sessions.json"
SESSIONS = {}
FAILED_ATTEMPTS = {}
try:
    if SESSION_FILE.exists():
        SESSIONS = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
except Exception:
    pass

def save_sessions():
    try:
        # Cleanup expired sessions before saving
        now = time.time()
        active_sessions = {k: v for k, v in SESSIONS.items() if v["expires"] > now}
        SESSION_FILE.write_text(json.dumps(active_sessions), encoding="utf-8")
    except Exception as e:
        log_event("error", "Failed to save sessions", str(e))

SESSION_EXPIRY = 24 * 3600

def hash_password(jid, password):
    return hashlib.sha256(f"{jid}:{password}:andorina".encode('utf-8')).hexdigest()

def check_auth(headers, required_perm=None):
    """Verifica si la petición tiene un token válido y los permisos necesarios. Retorna (bool, dict)."""
    # Si estamos en localhost y no hay auth configurada aún, podríamos relajarlo, pero forzaremos auth.
    auth_header = headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False, None
    token = auth_header.split(' ')[1]
    
    session = SESSIONS.get(token)
    if not session: return False, None
    if time.time() > session['expires']:
        del SESSIONS[token]
        save_sessions()
        return False, None
        
    # Renovar sesión
    session['expires'] = time.time() + SESSION_EXPIRY
    
    # Refresh permissions dynamically
    try:
        rules = read_json(STATE_DIR / "guard_rules.json") or {}
        if "roles" not in rules:
            rules["roles"] = {
                "owner": {"permissions": ["all"]},
                "manager": {"permissions": ["send_text","send_file","send_voice","read_inbox","search_history","search_contacts","list_groups","schedule_msg","list_agenda","remove_agenda","add_alert","get_role", "panel:send", "panel:contacts", "panel:inbox", "panel:agenda", "panel:alerts"]},
                "chatbot": {"permissions": []},
                "blocked": {"permissions": []}
            }
        
        jid_clean = session["jid"]
        entry = rules.get("jids", {}).get(jid_clean, {})
        
        env_vars, _ = read_env_file()
        owner_jids = []
        admin_phone = env_vars.get("ADMIN_PHONE", "").strip()
        if admin_phone:
            owner_jids.append(admin_phone)
        is_owner = any(jid_clean.endswith(re.sub(r"[^\d]", "", j)) for j in owner_jids if j)
        
        if is_owner:
            role = "owner"
            perms = ["all"]
        else:
            role = entry.get("role", rules.get("global_default_role", "chatbot"))
            perms = rules.get("roles", {}).get(role, {}).get("permissions", [])
        
        session["role"] = role
        session["permissions"] = perms
    except Exception:
        pass

    save_sessions()
    
    if required_perm:
        perms = session.get('permissions', [])
        if "all" not in perms and required_perm not in perms:
            return False, session
            
    return True, session

# ── Helpers ───────────────────────────────────────────────────

from utils.safe_json import read_json_safe, write_json_safe

def read_json(path):
    return read_json_safe(path)

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    return write_json_safe(path, data)

def run_script(script, *args, timeout=30):
    """Run a script and return (stdout, stderr, returncode)."""
    cmd = [sys.executable, str(SCRIPTS_DIR / script)] + list(args)
    log_event("info", f"run: {script} {' '.join(args[:3])}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=str(PROJECT_DIR))
        if r.returncode != 0:
            log_event("error", f"{script} failed (rc={r.returncode})", r.stderr[:300])
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        log_event("error", f"{script} timeout")
        return "", "Timeout", 1
    except Exception as e:
        log_event("error", f"{script} exception", str(e))
        return "", str(e), 1

def read_env_file():
    """Read .env as dict. Tries skill-local, then HERMES_HOME."""
    paths = []
    hh = os.environ.get("HERMES_HOME")
    if hh:
        paths.append(Path(hh) / "skills" / "andorina" / ".env")
    # Fallback: look relative to project
    paths.append(PROJECT_DIR / ".env")
    for p in paths:
        if p.exists():
            env = {}
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
            return env, p
    return {}, None

def parse_json_body(handler):
    try:
        length = int(handler.headers.get("Content-Length", 0))
        body = handler.rfile.read(length).decode("utf-8")
        return json.loads(body) if body else {}
    except Exception:
        return {}

# ── MIME types ────────────────────────────────────────────────
MIME = {
    ".html": "text/html", ".css": "text/css", ".js": "application/javascript",
    ".json": "application/json", ".png": "image/png", ".svg": "image/svg+xml",
    ".ico": "image/x-icon", ".woff2": "font/woff2", ".woff": "font/woff",
}

# ── Request Handler ───────────────────────────────────────────

class APIHandler(http.server.BaseHTTPRequestHandler):

    def send_json(self, data, code=200):
        # V3.6 GUI Adapter
        if isinstance(data, dict):
            if "payload" in data and isinstance(data["payload"], dict):
                data.update(data.pop("payload"))
            if data.get("status") == "OK":
                data["ok"] = True
            elif data.get("status") in ("ERROR", "DENY"):
                data["ok"] = False
                
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, code, msg):
        self.send_json({"ok": False, "error": msg}, code)

    def serve_static(self, rel_path):
        if not rel_path or rel_path == "/":
            rel_path = "/index.html"
        file_path = STATIC_DIR / rel_path.lstrip("/")
        if not file_path.resolve().is_relative_to(STATIC_DIR.resolve()):
            self.send_error(403); return
        if not file_path.exists():
            self.send_error(404); return
        ext = file_path.suffix.lower()
        mime = MIME.get(ext, "application/octet-stream")
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(data)

    # ── GET routes ────────────────────────────────────────────

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = dict(urllib.parse.parse_qsl(parsed.query))

        if not path.startswith("/api/"):
            self.serve_static(path); return

        public_routes = ["/api/install/status", "/api/install/detect", "/api/install/stream"]
        if path not in public_routes and not path.startswith("/api/public"):
            is_auth, session = check_auth(self.headers)
            if not is_auth:
                # Bypass if coming from localhost? No, plan says enforce auth always.
                self.send_error_json(401, "Unauthorized")
                return

        if path == "/api/public/banner":
            lang = qs.get("lang", "es").lower()
            if lang == "en":
                url = "https://lostregofestival.com/lostrego/banner_andorina_en.txt"
            else:
                url = "https://lostregofestival.com/lostrego/banner_andorina.txt"
            try:
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    text = response.read().decode('utf-8', errors='ignore')
                self.send_json({"ok": True, "text": text.strip()})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
            return

        if path == "/api/auth/status":
            if not session:
                return self.send_error_json(401, "Unauthorized")
            return self.send_json({"ok": True, "role": session.get("role", "chatbot"), "permissions": session.get("permissions", [])})

        # ── Installation / Setup ──
        if path == "/api/install/status":
            try:
                _, env_path = read_env_file()
                # In install mode, the .env might be in PROJECT_DIR or installed agent path
                local_env = PROJECT_DIR / ".env"
                
                hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))

                skill_dir = hermes_home / "skills" / "andorina"
                # Require guard_rules.json to exist — a folder alone means incomplete/stale install
                installed = skill_dir.exists() and (skill_dir / "state" / "guard_rules.json").exists()
                
                # Resolve .env: prefer installed Hermes path (panel shortcut scenario),
                # then fall back to local PROJECT_DIR (first-time wizard scenario).
                hermes_env = hermes_home / "skills" / "andorina" / ".env"

                if hermes_env.exists():
                    active_env_path = hermes_env
                    env_configured = True
                elif local_env.exists():
                    active_env_path = local_env
                    env_configured = True
                else:
                    active_env_path = None
                    env_configured = False

                google_linked = False
                if active_env_path:
                    google_linked = "GOOGLE_CONTACTS_REFRESH_TOKEN=" in active_env_path.read_text(errors="ignore")

                saved_admin = ""
                saved_cc = "34"
                if active_env_path:
                    try:
                        for line in active_env_path.read_text(errors="ignore").splitlines():
                            if line.startswith("ADMIN_PHONE="): saved_admin = line.split("=", 1)[1].strip()
                            elif line.startswith("DEFAULT_COUNTRY_CODE="): saved_cc = line.split("=", 1)[1].strip()
                    except Exception:
                        pass

                _cfg_yaml_text = (hermes_home / "config.yaml").read_text(errors="ignore") if (hermes_home / "config.yaml").exists() else ""
                hooks_registered = bool(_cfg_yaml_text) and (
                    "orchestrator_hook.py" in _cfg_yaml_text  # current version
                    or "webhook.py" in _cfg_yaml_text          # legacy
                )
                hermes_cmd = os.environ.get("HERMES_CMD", "hermes")
                autostart_enabled = (Path.home() / ".config" / "autostart" / f"{hermes_cmd}-agent.desktop").exists()
                bridge_patched = (hermes_home / "hermes-agent" / "scripts" / "whatsapp-bridge" / "bridge.js").exists() and "/groups" in (hermes_home / "hermes-agent" / "scripts" / "whatsapp-bridge" / "bridge.js").read_text(errors="ignore")
                soul_patched = (hermes_home / "SOUL.md").exists() and "WHATSAPP AGENT EXTENSION" in (hermes_home / "SOUL.md").read_text(errors="ignore")
                panel_shortcut_installed = (Path.home() / ".local" / "share" / "applications" / "andorina-panel.desktop").exists()
                
                deps_installed = not setup_lib.check_deps() if setup_lib else False

                try:
                    agents = setup_lib.detect_agents() if setup_lib else []
                except Exception:
                    agents = []

                self.send_json({
                    "ok": True,
                    "installed": installed,
                    "skill_path": str(PROJECT_DIR),
                    "env_configured": env_configured,
                    "saved_admin": saved_admin,
                    "saved_cc": saved_cc,
                    "hooks_registered": hooks_registered,
                    "google_linked": google_linked,
                    "autostart_enabled": autostart_enabled,
                    "bridge_patched": bridge_patched,
                    "soul_patched": soul_patched,
                    "deps_installed": deps_installed,
                    "panel_shortcut_installed": panel_shortcut_installed,
                    "agents": agents,
                    "display_server": setup_lib.detect_display_server() if setup_lib else "headless",
                    "python_env": setup_lib.detect_python_env() if setup_lib else {}
                })
            except Exception as e:
                log_event("error", f"install/status failed: {e}")
                self.send_json({"ok": True, "installed": False, "env_configured": False,
                                "hooks_registered": False, "agents": [], "error": str(e)})
            return

        elif path == "/api/install/detect":
            self.send_json({"ok": True, "agents": setup_lib.detect_agents() if setup_lib else []})
            return

        elif path == "/api/install/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                while True:
                    line = INSTALL_LOG.get()
                    self.wfile.write(f"data: {json.dumps(line)}\n\n".encode())
                    self.wfile.flush()
            except BaseException:
                pass
            return

        # ── Status / Dashboard ──
        if path == "/api/tunnel/status":
            is_auth, session = check_auth(self.headers)
            if not is_auth: return self.send_error_json(403, "No permission")
            sys.path.insert(0, str(SCRIPTS_DIR))
            from utils import tunnel
            status = tunnel.get_status()
            self.send_json({"ok": True, **status})
            return
        elif path == "/api/system/config-limits":
            # Leer config.yaml de hermes y extraer limites
            hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
            cfg_path = hermes_home / "config.yaml"
            u_limit = 1375
            m_limit = 2200
            if cfg_path.exists():
                text = cfg_path.read_text(encoding="utf-8")
                try:
                    for l in text.splitlines():
                        if l.strip().startswith("user_char_limit:"):
                            u_limit = int(l.split(":")[1].strip())
                        elif l.strip().startswith("memory_char_limit:"):
                            m_limit = int(l.split(":")[1].strip())
                except: pass
            self.send_json({"ok": True, "user_char_limit": u_limit, "memory_char_limit": m_limit})
            return
            
        elif path == "/api/status":
            out, err, _ = run_script("utils/diag.py", timeout=10)
            lines = out.splitlines()
            def line_ok(*keywords):
                """True if any line has ✅ AND contains at least one of the keywords (ES or EN)."""
                return any("✅" in l and any(kw in l for kw in keywords) for l in lines)

            bridge_ok = line_ok("Bridge")
            wa_ok     = line_ok("Connection", "Conexi")   # "Conexión de WhatsApp" or "Connection"
            google_ok = line_ok("Google")
            memory_ok = line_ok("Memory", "Memoria")      # "Motor de Memoria" or "Memory Engine"

            # Extract memory provider — handles both "Motor de Memoria (x)" and "Memory Provider (x)"
            memory_provider = "Unknown"
            for l in lines:
                for marker in ("Motor de Memoria (", "Memory Engine (", "Memory Provider ("):
                    if marker in l:
                        try:
                            memory_provider = l.split(marker)[1].split(")")[0].strip()
                        except Exception:
                            pass
                        break

            chatbot = read_json(STATE_DIR / "chatbot.json") or {"enabled": True, "muted_jids": []}
            away = read_json(STATE_DIR / "away.json") or {"enabled": False, "message": ""}
            rules = read_json(STATE_DIR / "guard_rules.json") or {}
            inbox = read_json(STATE_DIR / "inbox.json") or []
            agenda = read_json(STATE_DIR / "agenda.json") or {}
            alerts = read_json(STATE_DIR / "alerts.json") or []
            
            # Adapt real states based on bridge
            if not bridge_ok:
                memory_ok = False
                chatbot["enabled"] = False
                away["enabled"] = False
                
            # Unread tracking: messages without read field are treated as read (retrocompat)
            unread_msgs = sum(1 for m in inbox if m.get("read") is False)
            unread_chats = len(set(m["chatId"] for m in inbox if m.get("read") is False))

            # Hindsight (PostgreSQL) health check
            _pg_ctl_path = Path.home() / ".pg0" / "installation" / "18.1.0" / "bin" / "pg_ctl"
            _pg_data_path = Path.home() / ".pg0" / "instances" / "default" / "data"
            hindsight_installed = _pg_ctl_path.exists()
            hindsight_running = False
            if hindsight_installed:
                try:
                    _pg_r = subprocess.run(
                        [str(_pg_ctl_path), "status", "-D", str(_pg_data_path)],
                        capture_output=True, text=True, timeout=5
                    )
                    hindsight_running = _pg_r.returncode == 0
                except Exception:
                    pass

            self.send_json({
                "ok": True,
                "bridge": bridge_ok, "memory": memory_ok, "memory_provider": memory_provider,
                "whatsapp": wa_ok, "google": google_ok,
                "chatbot": chatbot, "away": away,
                "hindsight_installed": hindsight_installed,
                "hindsight_running": hindsight_running,
                "total_messages": len(inbox),
                "unread_messages": unread_msgs,
                "unread_chats": unread_chats,
                "total_scheduled": len(agenda),
                "total_alerts": len(alerts),
                "total_jids": len(rules.get("jids", {})),
                "total_role_assignments": sum(
                    1 for cfg in rules.get("jids", {}).values()
                    if (cfg.get("role") and cfg["role"] != "chatbot")
                    or cfg.get("custom_soul")
                    or cfg.get("allowed_folders")
                    or cfg.get("allowed_chats")
                    or cfg.get("allowed_contact_tags")
                ),
                "raw_diag": out
            })

        # ── Hindsight memory ──
        elif path == "/api/hindsight/start":
            _pg_ctl = Path.home() / ".pg0" / "installation" / "18.1.0" / "bin" / "pg_ctl"
            _pg_data = Path.home() / ".pg0" / "instances" / "default" / "data"
            _pg_log  = _pg_data / "log" / "postgresql.log"
            if not _pg_ctl.exists():
                self.send_error_json(404, "pg0 not installed — run: hermes memory setup"); return
            try:
                _pg_log.parent.mkdir(parents=True, exist_ok=True)
                _pg_env = os.environ.copy()
                _pg_env["LD_LIBRARY_PATH"] = "/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu"
                r = subprocess.run(
                    [str(_pg_ctl), "start", "-D", str(_pg_data), "-l", str(_pg_log)],
                    capture_output=True, text=True, timeout=15, env=_pg_env
                )
                self.send_json({"ok": r.returncode == 0, "output": (r.stdout + r.stderr).strip()})
            except Exception as e:
                self.send_error_json(500, str(e))

        # ── Contacts ──
        elif path == "/api/contacts/search":
            q = qs.get("q", "")
            if not q:
                self.send_error_json(400, "Missing query"); return
            out, _, _ = run_script("tools/contacts.py", "search", q)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": False, "raw": out})

        elif path == "/api/contacts/groups":
            out, _, _ = run_script("tools/contacts.py", "groups")
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": False, "raw": out})

        elif path == "/api/contacts/cache":
            data = read_json(STATE_DIR / "contacts_cache.json") or {"ts": 0, "contacts": []}
            self.send_json({"ok": True, "data": data})

        elif path == "/api/contacts/avatar":
            jid = qs.get("jid", "")
            if not jid:
                self.send_error_json(400, "Missing jid"); return
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:3000/profile-pic/{jid}", timeout=3) as r:
                    data = json.loads(r.read().decode())
                    self.send_json(data)
            except Exception:
                self.send_json({"url": ""})

        elif path == "/api/contacts/all":
            # Merge contacts from cache + guard JIDs + inbox chats
            cache = read_json(STATE_DIR / "contacts_cache.json") or {}
            rules = read_json(STATE_DIR / "guard_rules.json") or {}
            inbox = read_json(STATE_DIR / "inbox.json")
            if not isinstance(inbox, list): inbox = []
            merged = {}
            # From cache
            for c in cache.get("contacts", []):
                jid = c.get("chatId") or c.get("jid", "")
                if jid:
                    merged[jid] = {"jid": jid, "name": c.get("name", ""), "type": c.get("type", "contact")}
            # Pre-scan inbox for real domains
            real_domains = {}
            for msg in inbox:
                cid = msg.get("chatId", "")
                if "@" in cid:
                    real_domains[cid.split("@")[0]] = cid
            
            # From guard JIDs
            for num, cfg in rules.get("jids", {}).items():
                if num in real_domains:
                    jid = real_domains[num]
                else:
                    jid = f"{num}@g.us" if "-" in num else f"{num}@s.whatsapp.net" if "@" not in num else num
                
                if jid not in merged:
                    merged[jid] = {"jid": jid, "name": num, "type": "group" if "@g.us" in jid else "contact"}
                merged[jid]["role"] = cfg.get("role", "")
                merged[jid]["soul"] = cfg.get("custom_soul", "")
            # From inbox
            for msg in inbox[-500:]:
                cid = msg.get("chatId", "")
                if cid:
                    if cid not in merged:
                        merged[cid] = {"jid": cid, "name": cid.split("@")[0], "type": "group" if "@g.us" in cid else "contact"}
                    
                    # Update with real names if they were missing or raw
                    if merged[cid]["name"] == cid.split("@")[0]:
                        if "@g.us" in cid and msg.get("chatName"):
                            merged[cid]["name"] = msg.get("chatName")
                        elif "@g.us" not in cid and msg.get("senderName"):
                            merged[cid]["name"] = msg.get("senderName")
                            
            result = sorted(merged.values(), key=lambda x: x.get("name", "").lower())
            self.send_json({"ok": True, "contacts": result})

        elif path.startswith("/api/notes/"):
            jid = path.split("/api/notes/")[1]
            if not jid:
                self.send_error_json(400, "Missing JID"); return
            try:
                out, _, _ = run_script("tools/contacts.py", "note-read", jid)
                self.send_json(json.loads(out))
            except Exception as e:
                self.send_json({"ok": True, "notes": ""})
                
        elif path.startswith("/api/tags/get/"):
            jid = path.split("/api/tags/get/")[1]
            if not jid:
                self.send_error_json(400, "Missing JID"); return
            tags_data = read_json(STATE_DIR / "tags.json") or {}
            num = jid.split("@")[0]
            self.send_json({"ok": True, "tags": tags_data.get(num, [])})

        elif path == "/api/tags/all":
            tags_data = read_json(STATE_DIR / "tags.json") or {}
            self.send_json({"ok": True, "tags": tags_data})

        # ── Inbox ──
        elif path == "/api/inbox/list":
            inbox_data = read_json(STATE_DIR / "inbox.json") or []
            
            # Build a canonical map: numeric part → real @s.whatsapp.net JID
            # Covers both @lid entries and number-format mismatches (e.g. CC prefix)
            cache = read_json(STATE_DIR / "contacts_cache.json") or {}
            num_to_canonical = {}  # "68204198105199" -> "34612345678@s.whatsapp.net"
            for c in cache.get("contacts", []):
                c_id = c.get("id", "") or c.get("chatId", "")
                c_lid = c.get("lid", "")
                r_jid = c_id if "@s.whatsapp.net" in c_id else None
                if r_jid:
                    num_to_canonical[r_jid.split("@")[0]] = r_jid
                    if c_lid and "@lid" in c_lid:
                        num_to_canonical[c_lid.split("@")[0]] = r_jid
                    if "@lid" in c_id:
                        num_to_canonical[c_id.split("@")[0]] = r_jid

            # Also scan lid-mapping-*_reverse.json files from the bridge session dir.
            # These cover @lid addresses not yet synced in contacts_cache (e.g. bot's
            # own outgoing messages that WhatsApp echoes back with the recipient's LID).
            try:
                hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
                session_dir = hermes_home / "whatsapp" / "session"
                if session_dir.is_dir():
                    for mapping_file in session_dir.glob("lid-mapping-*_reverse.json"):
                        lid_num = mapping_file.name.replace("lid-mapping-", "").replace("_reverse.json", "")
                        if lid_num not in num_to_canonical:
                            try:
                                phone = json.loads(mapping_file.read_text(encoding="utf-8"))
                                if isinstance(phone, str) and phone:
                                    canonical = phone if "@" in phone else f"{phone}@s.whatsapp.net"
                                    num_to_canonical[lid_num] = canonical
                                    # Also map the phone number itself
                                    phone_num = canonical.split("@")[0]
                                    if phone_num not in num_to_canonical:
                                        num_to_canonical[phone_num] = canonical
                            except Exception:
                                pass
            except Exception:
                pass

            def canonical_chat_id(cid):
                """Return the canonical JID for a chatId, resolving @lid and bare numbers."""
                if not cid:
                    return cid
                num = cid.split("@")[0]
                if "@g.us" in cid:
                    return cid  # groups stay as-is
                if num in num_to_canonical:
                    return num_to_canonical[num]
                return cid

            # Build per-chat summary with unread counts, using canonical IDs
            chats = {}
            for m in inbox_data:
                raw_cid = m.get("chatId", "")
                if not raw_cid:
                    continue
                cid = canonical_chat_id(raw_cid)

                is_empty_outgoing = (m.get("senderName") == "Me" and not m.get("body", "").strip())

                if cid not in chats:
                    chats[cid] = {"last": m, "unread": 0, "canonical_id": cid}
                else:
                    m_date = m.get("date", "")
                    last_date = chats[cid]["last"].get("date", "")
                    last_is_empty = (chats[cid]["last"].get("senderName") == "Me"
                                    and not chats[cid]["last"].get("body", "").strip())
                    # Prefer non-empty messages for the preview; only replace with empty if strictly newer
                    if not is_empty_outgoing and m_date >= last_date:
                        chats[cid]["last"] = m
                    elif is_empty_outgoing and last_is_empty and m_date >= last_date:
                        chats[cid]["last"] = m
                    # else: keep existing (has real content or is newer)
                if m.get("read") is False:
                    chats[cid]["unread"] += 1

            recent = sorted(chats.values(), key=lambda x: x["last"].get("date", ""), reverse=True)
            # Ensure the chatId in the response always uses the canonical form
            recent_chats = []
            for c in recent:
                entry = {**c["last"], "unread_count": c["unread"]}
                entry["chatId"] = c["canonical_id"]
                recent_chats.append(entry)
            self.send_json({"ok": True, "total_chats": len(recent_chats), "recent_chats": recent_chats})

        elif path == "/api/inbox/read":
            chat_id = qs.get("chatId", "")
            limit = qs.get("limit", "50")
            if not chat_id:
                self.send_error_json(400, "Missing chatId"); return
            out, _, _ = run_script("tools/inbox.py", "read", chat_id, limit)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": False, "raw": out})



        elif path == "/api/inbox/search":
            q = qs.get("q", "")
            if not q:
                self.send_error_json(400, "Missing query"); return
            args = ["search", q]
            days = qs.get("days")
            if days: args += ["--days", days]
            out, _, _ = run_script("tools/inbox.py", *args)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": False, "raw": out})

        # ── Agenda ──
        elif path == "/api/agenda/list":
            out, _, _ = run_script("tools/agenda.py", "list")
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": False, "raw": out})

        elif path == "/api/agenda/recurring":
            out, _, _ = run_script("tools/agenda.py", "recurring", "list")
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": False, "raw": out})

        # ── Alerts ──
        elif path == "/api/alerts/list":
            data = read_json(STATE_DIR / "alerts.json") or []
            self.send_json({"ok": True, "alerts": data})

        elif path == "/api/webhooks/list":
            self.send_json({"ok": True, "webhooks": _load_webhooks()})

        elif path == "/api/webhooks/url":
            url, source = _detect_public_url()
            self.send_json({"ok": True, "url": url, "source": source})

        # ── Guard / RBAC ──
        elif path == "/api/guard/rules":
            data = read_json(STATE_DIR / "guard_rules.json") or {}
            
            if "roles" not in data:
                data["roles"] = {}
                
            # Guarantee owner role is always visible and correct in UI
            if "owner" not in data["roles"]:
                data["roles"]["owner"] = {"permissions": ["all"]}
            else:
                if "all" not in data["roles"]["owner"].get("permissions", []):
                    data["roles"]["owner"]["permissions"] = ["all"]
                    
            if "global_default_role" not in data:
                data["global_default_role"] = "chatbot"
            if "jids" not in data:
                data["jids"] = {}
                
            # Use canonical list from rbac.py (single source of truth)
            data["_available_permissions"] = _RBAC_PERMISSIONS if _RBAC_PERMISSIONS else [
                "all","send_text","send_file","send_voice","broadcast",
                "read_inbox","search_history","search_contacts","list_groups","refresh_contacts","add_note",
                "schedule_msg","list_agenda","remove_agenda","recurring_add","recurring_list","recurring_remove",
                "add_alert","run_diag","run_repair","wipe_logs",
                "guard_status","guard_reset","set_role","get_role","remove_role","list_roles",
                "set_soul","get_soul","chatbot_mute","chatbot_toggle","away_toggle",
                "panel:send", "panel:contacts", "panel:inbox", "panel:agenda", "panel:alerts",
                "panel:send:direct", "panel:send:broadcast", "panel:send:file", "panel:contacts:notes", "panel:contacts:refresh",
                "panel:inbox:delete", "panel:agenda:schedule", "panel:agenda:delete", "panel:alerts:manage",
                "admin:dashboard", "admin:status", "admin:rbac", "admin:souls", "admin:chatbot",
                "admin:away", "admin:env", "admin:logs", "admin:system", "admin:system:engine"
            ]
            self.send_json({"ok": True, "rules": data})

        elif path == "/api/guard/status":
            out, _, _ = run_script("security/orchestrator.py", "status")
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": True, "raw": out})

        # ── Chatbot ──
        elif path == "/api/chatbot/status":
            data = read_json(STATE_DIR / "chatbot.json") or {"enabled": True, "muted_jids": []}
            self.send_json({"ok": True, **data})

        # ── Away ──
        elif path == "/api/away/status":
            data = read_json(STATE_DIR / "away.json") or {"enabled": False, "message": "", "cooldown": {}}
            self.send_json({"ok": True, **data})

        # ── Souls ──
        elif path == "/api/souls/list":
            souls = []
            if SOULS_DIR.exists():
                for f in sorted(SOULS_DIR.rglob("*.md")):
                    rel_path = f.relative_to(SOULS_DIR)
                    parts    = rel_path.parts   # e.g. ("Categoria", "Nombre", "prompt.md")
                    depth    = len(parts)        # 1=root .md, 2=categoria/soul.md, 3=cat/name/prompt.md

                    if f.name == "prompt.md":
                        # Sandbox soul: Categoria/Nombre/prompt.md (depth 2 or 3)
                        soul_name = str(rel_path.parent).replace("\\", "/")
                        if soul_name == ".":
                            continue  # prompt.md at root — not a valid soul
                        d = f.parent
                        try:
                            content = f.read_text(encoding="utf-8")
                            knowledge_dir = d / "knowledge"
                            knowledge_files = []
                            if knowledge_dir.exists():
                                knowledge_files = [
                                    {"name": str(kf.relative_to(knowledge_dir)).replace("\\", "/"),
                                     "size": kf.stat().st_size}
                                    for kf in sorted(knowledge_dir.rglob("*"))
                                    if kf.is_file()
                                ]
                            souls.append({"name": soul_name, "file": str(rel_path).replace("\\", "/"),
                                          "content": content, "size": len(content),
                                          "is_sandbox": True, "knowledge_files": knowledge_files})
                        except: pass

                    else:
                        # Classic soul: Soul.md (depth 1) or Categoria/Soul.md (depth 2)
                        # Depth >= 3 → always inside a sandbox subfolder (knowledge, recursos, etc.) → skip
                        if depth >= 3:
                            continue
                        # Depth 2: skip if parent folder is itself a sandbox (has prompt.md sibling)
                        if depth == 2 and (f.parent / "prompt.md").exists():
                            continue
                        soul_name = str(rel_path.with_suffix("")).replace("\\", "/")
                        try:
                            content = f.read_text(encoding="utf-8")
                            souls.append({"name": soul_name, "file": str(rel_path).replace("\\", "/"),
                                          "content": content, "size": len(content),
                                          "is_sandbox": False, "knowledge_files": []})
                        except: pass

            self.send_json({"ok": True, "souls": souls})

        elif path.startswith("/api/souls/get/"):
            name = urllib.parse.unquote(path.split("/api/souls/get/")[1])
            soul_file = (SOULS_DIR / f"{name}.md").resolve()
            # Also check sandbox prompt.md
            sandbox_prompt = (SOULS_DIR / name / "prompt.md").resolve()
            if sandbox_prompt.exists() and sandbox_prompt.is_relative_to(SOULS_DIR.resolve()):
                self.send_json({"ok": True, "name": name, "content": sandbox_prompt.read_text(encoding="utf-8"), "is_sandbox": True})
            elif soul_file.exists() and soul_file.is_relative_to(SOULS_DIR.resolve()):
                self.send_json({"ok": True, "name": name, "content": soul_file.read_text(encoding="utf-8"), "is_sandbox": False})
            else:
                self.send_error_json(404, "Soul not found")

        elif path.startswith("/api/souls/knowledge/list/"):
            soul_name = urllib.parse.unquote(path.split("/api/souls/knowledge/list/")[1])
            knowledge_dir = (SOULS_DIR / soul_name / "knowledge").resolve()
            if not knowledge_dir.is_relative_to(SOULS_DIR.resolve()):
                self.send_error_json(403, "Invalid name"); return
            knowledge_dir.mkdir(parents=True, exist_ok=True)
            files = [{"name": f.name, "size": f.stat().st_size} for f in sorted(knowledge_dir.iterdir()) if f.is_file()]
            self.send_json({"ok": True, "files": files})

        elif path.startswith("/api/souls/knowledge/get/"):
            rest = urllib.parse.unquote(path.split("/api/souls/knowledge/get/")[1]).rsplit("/", 1)
            if len(rest) != 2:
                self.send_error_json(400, "Missing soul/filename"); return
            soul_name, filename = rest
            target = (SOULS_DIR / soul_name / "knowledge" / filename).resolve()
            if not target.is_relative_to(SOULS_DIR.resolve()):
                self.send_error_json(403, "Invalid path"); return
            if not target.exists():
                self.send_error_json(404, "File not found"); return
            TEXT_EXTS = {".txt", ".md", ".csv", ".json"}
            if target.suffix.lower() not in TEXT_EXTS:
                self.send_error_json(400, "Only text files can be edited"); return
            self.send_json({"ok": True, "content": target.read_text(encoding="utf-8", errors="replace")})


        elif path == "/api/docs":
            docs_path = PROJECT_DIR / "docs" / "developer_guide.md"
            if docs_path.exists():
                content = docs_path.read_text(encoding="utf-8")
                self.send_json({"ok": True, "content": content})
            else:
                self.send_error_json(404, "Developer guide not found")

        # ── Logs ──
        elif path == "/api/logs":
            def tail(file_path, lines=50):
                if not file_path.exists(): return []
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines_list = f.read().splitlines()
                        return lines_list[-lines:]
                except Exception: return []

            hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
            server_log = tail(GUI_DIR / ".server.log", 30)
            bridge_log = tail(hermes_home / "whatsapp" / "bridge.log", 30)
            gateway_log = tail(hermes_home / "logs" / "gateway.log", 30)
            agent_log = tail(hermes_home / "logs" / "agent.log", 30)

            self.send_json({
                "ok": True, 
                "api_logs": LOG_BUFFER[-30:],
                "files": {
                    "server": server_log,
                    "bridge": bridge_log,
                    "gateway": gateway_log,
                    "agent": agent_log
                }
            })

        # ── Environment ──
        elif path == "/api/env":
            env, env_path = read_env_file()
            schema = [
                {"key": "HERMES_AGENT_PATH", "desc": "Ruta absoluta a la instalación de Hermes (ej: /home/usuario/.hermes/hermes-agent)"},
                {"key": "ANDORINA_ROOT", "desc": "Ruta absoluta a la carpeta de este panel Andoriña"},
                {"key": "WHATSAPP_NUMBER", "desc": "Tu número de teléfono con la skill conectada a WhatsApp (ej: 34600111222)"},
                {"key": "ADMIN_PHONE", "desc": "Número personal del dueño (para panel y recuperación)"},
                {"key": "PANEL_PASSWORD", "desc": "Contraseña de acceso inicial al panel web"},
                {"key": "GOOGLE_CONTACTS_CLIENT_ID", "desc": "Credenciales OAuth2 para sincronizar contactos de Google"},
                {"key": "GOOGLE_CONTACTS_CLIENT_SECRET", "desc": "Secreto OAuth2 de la app de Google Contacts"},
                {"key": "GOOGLE_CONTACTS_REFRESH_TOKEN", "desc": "Token guardado automáticamente tras vincular cuenta de Google (No editar a mano)"},
                {"key": "GUARD_COOLDOWN_SECS", "desc": "Segundos de espera obligatorios entre respuestas a grupos para evitar spam (ej: 60)"},
                {"key": "MAX_MSG_LEN", "desc": "Límite máximo de caracteres por respuesta individual (ej: 2000)"},
                {"key": "TUNNEL_NOTIFY_MODE", "desc": "Quién recibe el aviso por WhatsApp al iniciar el túnel temporal (Elige SOLO UNA opción)", "options": ["all_panel_users", "owner_only", "off"]}
            ]
            self.send_json({"ok": True, "env": env, "path": str(env_path) if env_path else None, "schema": schema})

        # ── Recurring files ──
        elif path == "/api/recurring/list":
            recs = []
            if RECURRING_DIR.exists():
                for f in sorted(RECURRING_DIR.glob("*.json")):
                    try: recs.append(json.loads(f.read_text(encoding="utf-8")))
                    except: pass
            self.send_json({"ok": True, "recurring": recs})

        # ── Panel Shortcut Status ──
        elif path == "/api/system/panel-shortcut-status":
            launcher_path = PROJECT_DIR / "Andorina-Panel.sh"
            app_menu_desktop = Path.home() / ".local" / "share" / "applications" / "andorina-panel.desktop"
            desktop_candidates = [Path.home() / "Desktop" / "Andorina-Panel.desktop",
                                  Path.home() / "Escritorio" / "Andorina-Panel.desktop"]
            desktop_path = next((str(p) for p in desktop_candidates if p.exists()), None)
            icon_path = GUI_DIR / "static" / "logo.png"
            self.send_json({
                "ok": True,
                "app_menu_installed": app_menu_desktop.exists(),
                "desktop_installed": desktop_path is not None,
                "launcher_path": str(launcher_path),
                "launcher_exists": launcher_path.exists(),
                "desktop_path": str(app_menu_desktop),
                "desktop_icon_path": str(icon_path) if icon_path.exists() else None
            })

        # ── Patch Guard ──
        elif path == "/api/patches/status":
            try:
                env = os.environ.copy()
                if "HERMES_HOME" not in env:
                    env["HERMES_HOME"] = str(Path.home() / ".hermes")
                r = subprocess.run(
                    [sys.executable, str(SOURCE_DIR / "check_patches.py"), "--json"],
                    capture_output=True, text=True, timeout=15, env=env
                )
                raw = json.loads(r.stdout)

                # Transform raw marker dicts into the flat list the frontend renders:
                # [{name, ok, reason}]  +  ok  +  missing_count
                MARKER_LABELS = {
                    "health_endpoint":  "bridge.js — /health endpoint",
                    "groups_endpoint":  "bridge.js — /groups endpoint",
                    "sender_id_fix":    "bridge.js — sender ID fix",
                    "mime_expansion":   "bridge.js — MIME type expansion",
                    "fromMe_inbox_fix": "bridge.js — fromMe inbox filter",
                    "inbox_writer":     "whatsapp.py — inbox writer",
                    "webhook_dispatch": "whatsapp.py — webhook dispatch",
                    "hermes_home_env":  "whatsapp.py — HERMES_HOME env",
                }
                patches = []
                missing_count = 0

                # Bridge file presence
                bridge_ok = raw.get("bridge", {}).get("exists", False)
                patches.append({
                    "name": f"bridge.js — {raw.get('bridge', {}).get('file', 'not found')}",
                    "ok": bridge_ok,
                    "reason": None if bridge_ok else "bridge.js not found"
                })
                for key, present in raw.get("bridge", {}).get("markers", {}).items():
                    if not present:
                        missing_count += 1
                    patches.append({
                        "name": MARKER_LABELS.get(key, f"bridge.js — {key}"),
                        "ok": present,
                        "reason": None if present else "Missing from bridge.js"
                    })

                # whatsapp.py
                wa_ok = raw.get("whatsapp", {}).get("exists", False)
                patches.append({
                    "name": "whatsapp.py — adapter file",
                    "ok": wa_ok,
                    "reason": None if wa_ok else "whatsapp.py not found"
                })
                for key, present in raw.get("whatsapp", {}).get("markers", {}).items():
                    if not present:
                        missing_count += 1
                    patches.append({
                        "name": MARKER_LABELS.get(key, f"whatsapp.py — {key}"),
                        "ok": present,
                        "reason": None if present else "Missing from whatsapp.py"
                    })

                self.send_json({
                    "ok": missing_count == 0,
                    "patches": patches,
                    "missing_count": missing_count
                })
            except Exception as e:
                self.send_error_json(500, str(e))

        # ── Andoriña Update ──
        elif path == "/api/update/check":
            try:
                r = subprocess.run(
                    [sys.executable, str(SOURCE_DIR / "andorina_updater.py"), "--json"],
                    capture_output=True, text=True, timeout=15
                )
                self.send_json(json.loads(r.stdout))
            except Exception as e:
                self.send_error_json(500, str(e))

        else:
            self.send_error_json(404, "Unknown endpoint")


    # ── POST routes ───────────────────────────────────────────

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        body = parse_json_body(self)

        public_routes = [
            "/api/login", 
            "/api/install/step/env", 
            "/api/install/step/google", 
            "/api/install/step/deploy",
            "/api/install/step/patch",
            "/api/install/step/autostart",
            "/api/install/step/soul",
            "/api/install/step/deps",
            "/api/install/step/finalize",
            "/api/system/install-panel",    # needed during install wizard (no token yet)
            "/api/system/uninstall-panel",
        ]
        
        if path not in public_routes and not path.startswith("/webhook/"):
            is_auth, session = check_auth(self.headers)
            if not is_auth:
                self.send_error_json(401, "Unauthorized")
                return

        # ── Public webhook receiver (no auth — called by external services) ──
        if path.startswith("/webhook/"):
            wh_id = path.split("/webhook/", 1)[1].strip("/")
            if not wh_id:
                self.send_json({"ok": False, "error": "Missing webhook id"}, 400); return
            hooks = _load_webhooks()
            hook = next((h for h in hooks if h.get("id") == wh_id), None)
            if not hook:
                self.send_json({"ok": False, "error": "Not found"}, 404); return
            if not hook.get("enabled", True):
                self.send_json({"ok": True, "message": "Webhook disabled"}); return
            # Check optional secret header
            secret = hook.get("secret", "")
            if secret:
                sig = self.headers.get("X-Webhook-Secret", "") or self.headers.get("X-WC-Webhook-Signature", "")
                if sig != secret:
                    self.send_json({"ok": False, "error": "Invalid secret"}, 403); return
            # Parse body
            payload = body if isinstance(body, dict) else {"_raw": str(body)}
            # Dispatch
            _dispatch_webhook(hook, payload)
            # Update stats
            import time as _time
            hook["last_triggered"] = _time.strftime("%Y-%m-%dT%H:%M:%S")
            hook["trigger_count"] = hook.get("trigger_count", 0) + 1
            _save_webhooks(hooks)
            self.send_json({"ok": True, "dispatched": len(hook.get("targets", []))})
            return

        if path == "/api/login":
            client_ip = self.client_address[0]
            now = time.time()
            if client_ip in FAILED_ATTEMPTS:
                attempts, last_time = FAILED_ATTEMPTS[client_ip]
                if attempts >= 5 and now - last_time < 300: # 5 mins block
                    return self.send_error_json(429, "Too many failed attempts. Try again in 5 minutes.")
                if now - last_time >= 300:
                    del FAILED_ATTEMPTS[client_ip]

            jid = body.get("jid")
            password = body.get("password")
            if not jid: return self.send_error_json(400, "Missing JID")
            
            env_vars, _ = read_env_file()
            owner_jids = []
            admin_phone = env_vars.get("ADMIN_PHONE", "").strip()
            if admin_phone:
                owner_jids.append(admin_phone)
                
            rules = read_json(STATE_DIR / "guard_rules.json") or {}
            
            # Also collect owners from guard_rules.json (role == owner)
            for k, v in rules.get("jids", {}).items():
                if v.get("role") == "owner" and k not in owner_jids:
                    owner_jids.append(k)
            
            # Limpiar número (strip +, spaces, dashes)
            jid_clean = re.sub(r"[^\d]", "", jid)
            is_owner = any(
                jid_clean.endswith(re.sub(r"[^\d]", "", j)) or
                re.sub(r"[^\d]", "", j).endswith(jid_clean)
                for j in owner_jids if j
            )
            
            # Check existing rule entry
            entry = rules.get("jids", {}).get(jid_clean, {})
            # If not found, try suffix matching (different country code format)
            if not entry:
                for k, v in rules.get("jids", {}).items():
                    if k.endswith(jid_clean) or jid_clean.endswith(k):
                        entry = v
                        jid_clean = k
                        break
            
            saved_hash = entry.get("password_hash")
            
            # Si es el dueño y no tiene contraseña, le dejamos pasar pero obligamos a cambiarla?
            # O mejor, si no hay hash y es owner, el password de login se convierte en el nuevo hash
            if not saved_hash:
                if is_owner:
                    if not password:
                        return self.send_json({"ok": False, "require_setup": True})
                    # Set initial password
                    entry["password_hash"] = hash_password(jid_clean, password)
                    entry["role"] = "owner"
                    if "jids" not in rules: rules["jids"] = {}
                    rules["jids"][jid_clean] = entry
                    write_json(STATE_DIR / "guard_rules.json", rules)
                else:
                    if client_ip not in FAILED_ATTEMPTS: FAILED_ATTEMPTS[client_ip] = [0, now]
                    FAILED_ATTEMPTS[client_ip][0] += 1
                    FAILED_ATTEMPTS[client_ip][1] = now
                    return self.send_error_json(401, "Invalid credentials")
            else:
                if hash_password(jid_clean, password) != saved_hash:
                    if client_ip not in FAILED_ATTEMPTS: FAILED_ATTEMPTS[client_ip] = [0, now]
                    FAILED_ATTEMPTS[client_ip][0] += 1
                    FAILED_ATTEMPTS[client_ip][1] = now
                    return self.send_error_json(401, "Invalid credentials")
                    
            if client_ip in FAILED_ATTEMPTS: del FAILED_ATTEMPTS[client_ip]
                    
            # Issue token
            token = secrets.token_hex(32)
            
            # Resolve role & perms (mocking guard.py's resolve_role)
            role = "owner" if is_owner else entry.get("role", rules.get("global_default_role", "chatbot"))
            perms = rules.get("roles", {}).get(role, {}).get("permissions", [])
            
            SESSIONS[token] = {
                "jid": jid_clean,
                "role": role,
                "permissions": perms,
                "expires": time.time() + SESSION_EXPIRY
            }
            save_sessions()
            
            return self.send_json({"ok": True, "token": token, "role": role, "permissions": perms})


        elif path == "/api/auth/change-password":
            new_pass = body.get("password")
            if not new_pass: return self.send_error_json(400, "Missing password")
            # session is already verified by the global auth check at the top of do_POST
            is_auth, session = check_auth(self.headers)
            if not is_auth or not session:
                return self.send_error_json(401, "Unauthorized")
            jid_clean = session["jid"]
            rules = read_json(STATE_DIR / "guard_rules.json") or {}
            if "jids" not in rules: rules["jids"] = {}
            if jid_clean not in rules["jids"]: rules["jids"][jid_clean] = {}
            rules["jids"][jid_clean]["password_hash"] = hash_password(jid_clean, new_pass)
            write_json(STATE_DIR / "guard_rules.json", rules)
            return self.send_json({"ok": True})

        elif path == "/api/tags/set":
            jid = body.get("jid")
            tags = body.get("tags")
            if not jid or tags is None:
                return self.send_error_json(400, "Missing JID or tags")
            tags_file = STATE_DIR / "tags.json"
            tags_data = read_json(tags_file) or {}
            num = jid.split("@")[0]
            if not tags:
                if num in tags_data:
                    del tags_data[num]
            else:
                tags_data[num] = tags
            write_json(tags_file, tags_data)
            return self.send_json({"ok": True})

        elif path == "/api/inbox/delete":
            try:
                chat_id = body.get("chatId")
                if not chat_id:
                    self.send_error_json(400, "Missing chatId"); return
                out, _, _ = run_script("tools/inbox.py", "delete", chat_id)
                r = json.loads(out)
                self.send_json({"ok": r.get("status") == "OK", "error": r.get("payload", {}).get("error")})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)})

        elif path == "/api/inbox/message/delete":
            try:
                chat_id = body.get("chatId")
                msg_index = body.get("msgIndex")
                if chat_id is None or msg_index is None:
                    self.send_error_json(400, "Missing chatId or msgIndex"); return
                inbox_file = STATE_DIR / "inbox.json"
                inbox = read_json(inbox_file)
                if inbox is None:
                    self.send_error_json(404, "inbox.json not found"); return
                # Get messages for this chat in order
                chat_msgs = [(i, m) for i, m in enumerate(inbox) if m.get("chatId") == chat_id]
                if msg_index >= len(chat_msgs):
                    self.send_error_json(404, "Message not found"); return
                real_idx = chat_msgs[msg_index][0]
                inbox.pop(real_idx)
                write_json(inbox_file, inbox)
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)})

        elif path == "/api/inbox/message/edit":
            try:
                chat_id = body.get("chatId")
                msg_index = body.get("msgIndex")
                new_text = body.get("text", "")
                if chat_id is None or msg_index is None:
                    self.send_error_json(400, "Missing chatId or msgIndex"); return
                inbox_file = STATE_DIR / "inbox.json"
                inbox = read_json(inbox_file)
                if inbox is None:
                    self.send_error_json(404, "inbox.json not found"); return
                chat_msgs = [(i, m) for i, m in enumerate(inbox) if m.get("chatId") == chat_id]
                if msg_index >= len(chat_msgs):
                    self.send_error_json(404, "Message not found"); return
                real_idx = chat_msgs[msg_index][0]
                inbox[real_idx]["text"] = new_text
                write_json(inbox_file, inbox)
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)})

        # ── Installation / Setup ──
        if path == "/api/install/step/env":
            try:
                # Determine hermes agent path to calculate right script directory
                agent_path = Path(body.get("agent_path", str(Path.home() / ".hermes")))
                env_content = f"""# Andoriña Configuration
HERMES_AGENT_PATH={agent_path}
DEFAULT_COUNTRY_CODE={body.get("country_code", "34")}
WHATSAPP_ALLOWED_USERS=*
ADMIN_PHONE={body.get("admin_phone", "")}
CTX_MAX_TOKENS={body.get("ctx_tokens", "2000")}
USER_MEMORY_ENABLED={body.get("user_mem", "true")}
SYSTEM_MEMORY_ENABLED={body.get("sys_mem", "true")}
WHATSAPP_BRIDGE_URL=http://localhost:3000
# Andorina core will use this logic if we configure absolute path correctly
ANDORINA_ROOT={agent_path / "skills" / "andorina"}
"""
                (PROJECT_DIR / ".env").write_text(env_content)
                
                # If the skill is already installed, update it directly there too!
                target_skill_dir = agent_path / "skills" / "andorina"
                if target_skill_dir.exists():
                    (target_skill_dir / ".env").write_text(env_content)
                    # Also update guard_rules.json with the new owner
                    if setup_lib:
                        setup_lib.init_rbac(str(agent_path), body.get("admin_phone", ""))

                # Patch the Hermes root .env so the bridge accepts all users.
                # The bridge reads WHATSAPP_ALLOWED_USERS from ~/.hermes/.env,
                # NOT from the skill .env. Without this, all incoming messages
                # are silently dropped at the bridge level.
                hermes_root_env = agent_path / ".env"
                try:
                    root_env_text = hermes_root_env.read_text(encoding="utf-8") if hermes_root_env.exists() else ""
                    if "WHATSAPP_ALLOWED_USERS=" in root_env_text:
                        import re as _re
                        root_env_text = _re.sub(r"^WHATSAPP_ALLOWED_USERS=.*", "WHATSAPP_ALLOWED_USERS=*", root_env_text, flags=_re.MULTILINE)
                    else:
                        root_env_text += "\nWHATSAPP_ALLOWED_USERS=*\n"
                    hermes_root_env.write_text(root_env_text, encoding="utf-8")
                except Exception:
                    pass  # Non-fatal: bridge will start with no allowlist warning

                self.send_json({"ok": True})
            except Exception as e:
                self.send_error_json(500, str(e))
            return

        elif path == "/api/install/step/google":
            def run_auth():
                INSTALL_LOG.put({"level": "info", "msg": "Lanzando autenticación con Google..."})

                # Resolve target_skill_dir from the request body (multi-profile support)
                _agent_path = Path(body.get("agent_path", str(Path.home() / ".hermes")))
                target_skill_dir = _agent_path / "skills" / "andorina"

                # Use SOURCE_DIR instead of PROJECT_DIR and make sure HERMES_HOME is passed
                env_dict = os.environ.copy()
                env_dict["HERMES_HOME"] = str(_agent_path)

                p = subprocess.Popen([sys.executable, str(SOURCE_DIR / "scripts" / "utils" / "auth.py")],
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(SOURCE_DIR), env=env_dict)
                for line in iter(p.stdout.readline, ''):
                    line = line.strip()
                    if line: INSTALL_LOG.put({"level": "info", "msg": line})
                p.wait()

                # Sync Google tokens to the live environment if already installed.
                # auth.py writes into SOURCE_DIR/.env (Beta1), so we read tokens from there
                # and merge them into the live .env via key-by-key update.
                source_env_path = SOURCE_DIR / ".env"
                target_env_path = target_skill_dir / ".env"
                if target_skill_dir.exists() and source_env_path.exists():
                    import re as _re
                    src_text = source_env_path.read_text(encoding="utf-8", errors="ignore")
                    token_keys = [
                        "GOOGLE_CONTACTS_ACCESS_TOKEN",
                        "GOOGLE_CONTACTS_REFRESH_TOKEN",
                        "GOOGLE_CONTACTS_CLIENT_ID",
                        "GOOGLE_CONTACTS_CLIENT_SECRET",
                    ]
                    tokens = {}
                    for line in src_text.splitlines():
                        for k in token_keys:
                            if line.startswith(f"{k}="):
                                tokens[k] = line.split("=", 1)[1].strip()
                    if tokens:
                        dst_text = target_env_path.read_text(encoding="utf-8", errors="ignore") if target_env_path.exists() else ""
                        for k, v in tokens.items():
                            pat = _re.compile(rf"^{k}=.*", _re.MULTILINE)
                            if pat.search(dst_text):
                                dst_text = pat.sub(f"{k}={v}", dst_text)
                            else:
                                if dst_text and not dst_text.endswith("\n"): dst_text += "\n"
                                dst_text += f"{k}={v}\n"
                        target_env_path.write_text(dst_text, encoding="utf-8")
                        INSTALL_LOG.put({"level": "info", "msg": f"Tokens sincronizados con el entorno activo ({target_env_path})."})
                INSTALL_LOG.put({"level": "info", "msg": "Autenticación completada."})
            threading.Thread(target=run_auth, daemon=True).start()
            self.send_json({"ok": True})
            return

        elif path == "/api/install/step/deploy":
            agent_path_str = body.get("agent_path")
            admin_phone = body.get("admin_phone", "")
            if not agent_path_str:
                self.send_error_json(400, "Falta agent_path")
                return
            def run_deploy():
                if setup_lib:
                    INSTALL_LOG.put({"level": "info", "msg": "Iniciando despliegue de archivos..."})
                    # Deploy files, register hooks, and init RBAC with admin_phone
                    if setup_lib.deploy_files(agent_path_str, str(SOURCE_DIR), INSTALL_LOG):
                        setup_lib.register_hooks(agent_path_str, INSTALL_LOG)
                        setup_lib.init_rbac(agent_path_str, admin_phone, INSTALL_LOG)
                    # Also init local state (download folder) so this running server can log in immediately
                    setup_lib.init_rbac(str(SOURCE_DIR), admin_phone, INSTALL_LOG, local_dir_str=str(SOURCE_DIR))
                    INSTALL_LOG.put({"level": "info", "msg": "Despliegue finalizado con éxito."})
                else:
                    INSTALL_LOG.put({"level": "error", "msg": "Error: setup_lib no encontrado."})
            threading.Thread(target=run_deploy, daemon=True).start()
            self.send_json({"ok": True})
            return

        elif path == "/api/install/step/finalize":
            agent_path_str = body.get("agent_path", "")
            admin_phone = body.get("admin_phone", "")
            def run_finalize():
                if setup_lib and admin_phone:
                    INSTALL_LOG.put({"level": "info", "msg": "Finalizando configuración RBAC..."})
                    # Ensure guard_rules.json has the owner in both locations
                    if agent_path_str:
                        setup_lib.init_rbac(agent_path_str, admin_phone, INSTALL_LOG)
                    setup_lib.init_rbac(str(SOURCE_DIR), admin_phone, INSTALL_LOG)
                INSTALL_LOG.put({"level": "ok", "msg": "✓ Instalación completa. Ya puedes iniciar sesión."})
            threading.Thread(target=run_finalize, daemon=True).start()
            self.send_json({"ok": True})
            return

        elif path == "/api/install/step/patch":
            def run_patch():
                INSTALL_LOG.put({"level": "info", "msg": "Parcheando bridge.js..."})
                env_dict = os.environ.copy()
                env_dict["HERMES_HOME"] = body.get("agent_path", str(Path.home() / ".hermes"))
                p = subprocess.Popen([sys.executable, str(SOURCE_DIR / "patch_bridge.py")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(SOURCE_DIR), env=env_dict)
                for line in iter(p.stdout.readline, ''):
                    line = line.strip()
                    if line: INSTALL_LOG.put({"level": "info", "msg": line})
                p.wait()
                
                INSTALL_LOG.put({"level": "info", "msg": "Parcheando whatsapp.py (Sub-Soul)..."})
                p2 = subprocess.Popen([sys.executable, str(SOURCE_DIR / "patch_whatsapp.py")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(SOURCE_DIR), env=env_dict)
                for line in iter(p2.stdout.readline, ''):
                    line = line.strip()
                    if line: INSTALL_LOG.put({"level": "info", "msg": line})
                p2.wait()
                
                INSTALL_LOG.put({"level": "info", "msg": "Parcheado completado."})
            threading.Thread(target=run_patch, daemon=True).start()
            self.send_json({"ok": True})
            return

        elif path == "/api/install/step/autostart":
            enable = body.get("enable", False)
            def run_autostart():
                if setup_lib:
                    INSTALL_LOG.put({"level": "info", "msg": ("Habilitando" if enable else "Deshabilitando") + " autostart..."})
                    autostart_setup = SCRIPTS_DIR / "utils" / "setup_autostart.py"
                    if autostart_setup.exists():
                        args = [sys.executable, str(autostart_setup)]
                        if not enable: args.append("--disable")
                        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                        for line in iter(p.stdout.readline, ''):
                            if line.strip(): INSTALL_LOG.put({"level": "info", "msg": line.strip()})
                        p.wait()
                    else:
                        INSTALL_LOG.put({"level": "error", "msg": "setup_autostart.py no encontrado."})
            threading.Thread(target=run_autostart, daemon=True).start()
            self.send_json({"ok": True})
            return

        elif path == "/api/install/step/soul":
            agent_path_str = body.get("agent_path")
            owner_num = body.get("owner_num", "")
            if not agent_path_str:
                self.send_error_json(400, "Falta agent_path"); return
            def run_soul():
                if setup_lib:
                    INSTALL_LOG.put({"level": "info", "msg": "Optimizando SOUL.md..."})
                    setup_lib.optimize_soul(agent_path_str, owner_num, INSTALL_LOG)
            threading.Thread(target=run_soul, daemon=True).start()
            self.send_json({"ok": True})
            return
            
        elif path == "/api/install/step/deps":
            def _install_nodejs_cascade(log):
                """Try 3 strategies in order: system pkg manager → nvm → pre-built binary."""
                import shutil as _sh, urllib.request as _ur, tarfile as _tf, platform as _pl

                def node_ok():
                    return bool(_sh.which("node") or _sh.which("nodejs"))

                # ── Strategy 1: system package manager (needs sudo) ──────────────
                log({"level": "info", "msg": "🔍 Buscando gestor de paquetes del sistema..."})
                pkg_cmds = []
                if _sh.which("pacman"):   pkg_cmds = ["sudo", "pacman", "-S", "--noconfirm", "nodejs", "npm"]
                elif _sh.which("apt-get"): pkg_cmds = ["sudo", "apt-get", "install", "-y", "nodejs", "npm"]
                elif _sh.which("dnf"):     pkg_cmds = ["sudo", "dnf", "install", "-y", "nodejs", "npm"]
                elif _sh.which("zypper"):  pkg_cmds = ["sudo", "zypper", "install", "-y", "nodejs", "npm"]
                elif _sh.which("apk"):     pkg_cmds = ["sudo", "apk", "add", "nodejs", "npm"]

                if pkg_cmds:
                    mgr = pkg_cmds[1]
                    log({"level": "info", "msg": f"📦 Instalando Node.js via {mgr}..."})
                    r = subprocess.run(pkg_cmds, capture_output=True, text=True, timeout=120)
                    if r.returncode == 0 and node_ok():
                        v = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
                        log({"level": "ok", "msg": f"✅ Node.js instalado via {mgr}: {v}"})
                        return True
                    log({"level": "info", "msg": f"⚠️ {mgr} falló (¿sin sudo?). Probando nvm..."})

                # ── Strategy 2: nvm (no sudo required) ───────────────────────────
                nvm_dir = Path.home() / ".nvm"
                try:
                    log({"level": "info", "msg": "⬇️ Descargando nvm..."})
                    nvm_script = Path("/tmp/nvm_install.sh")
                    _ur.urlretrieve("https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh", nvm_script)
                    r = subprocess.run(["bash", str(nvm_script)],
                                       capture_output=True, text=True, timeout=120,
                                       env={**os.environ, "NVM_DIR": str(nvm_dir)})
                    if r.returncode == 0:
                        log({"level": "info", "msg": "nvm instalado. Descargando Node.js LTS (puede tardar 1-2 min)..."})
                        node_cmd = (f'export NVM_DIR="{nvm_dir}" && '
                                    f'[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
                                    f'nvm install --lts && nvm use --lts')
                        r2 = subprocess.run(["bash", "-c", node_cmd],
                                            capture_output=True, text=True, timeout=300)
                        if r2.returncode == 0:
                            log({"level": "ok", "msg": "✅ Node.js LTS instalado via nvm."})
                            return True
                        log({"level": "info", "msg": f"⚠️ nvm install falló: {r2.stderr[:150]}. Probando binario directo..."})
                    else:
                        log({"level": "info", "msg": f"⚠️ nvm no pudo instalarse: {r.stderr[:150]}. Probando binario directo..."})
                except Exception as e:
                    log({"level": "info", "msg": f"⚠️ nvm no disponible ({e}). Probando binario directo..."})

                # ── Strategy 3: pre-built official binary from nodejs.org ─────────
                try:
                    log({"level": "info", "msg": "⬇️ Descargando binario oficial de Node.js LTS..."})
                    arch = _pl.machine()  # x86_64 / aarch64 / armv7l
                    arch_map = {"x86_64": "x64", "aarch64": "arm64", "armv7l": "armv7l"}
                    node_arch = arch_map.get(arch, "x64")
                    # Use a pinned LTS version
                    node_ver = "v20.14.0"
                    fname = f"node-{node_ver}-linux-{node_arch}.tar.xz"
                    url = f"https://nodejs.org/dist/{node_ver}/{fname}"
                    dest_tar = Path(f"/tmp/{fname}")
                    _ur.urlretrieve(url, dest_tar)
                    log({"level": "info", "msg": "Extrayendo Node.js..."})
                    local_dir = Path.home() / ".local"
                    (local_dir / "bin").mkdir(parents=True, exist_ok=True)
                    with _tf.open(dest_tar) as t:
                        t.extractall(local_dir / "node")
                    node_bin = local_dir / "node" / f"node-{node_ver}-linux-{node_arch}" / "bin"
                    # Symlink into ~/.local/bin
                    for binary in ["node", "npm", "npx"]:
                        src = node_bin / binary
                        dst = local_dir / "bin" / binary
                        if src.exists():
                            if dst.exists() or dst.is_symlink(): dst.unlink()
                            dst.symlink_to(src)
                    log({"level": "ok", "msg": f"✅ Node.js {node_ver} instalado en ~/.local/bin/node"})
                    log({"level": "info", "msg": "ℹ️ Añade ~/.local/bin a tu PATH si el bridge no lo detecta automáticamente."})
                    return True
                except Exception as e:
                    log({"level": "error", "msg": f"❌ Todos los métodos fallaron: {e}. Instala Node.js manualmente: https://nodejs.org"})
                    return False

            def run_deps():
                if setup_lib:
                    INSTALL_LOG.put({"level": "info", "msg": "Instalando dependencias Python..."})
                    setup_lib.install_deps(INSTALL_LOG)
                    import shutil as _sh
                    if not _sh.which("node") and not _sh.which("nodejs"):
                        _install_nodejs_cascade(INSTALL_LOG.put)
                    else:
                        v = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
                        INSTALL_LOG.put({"level": "ok", "msg": f"✅ Node.js ya instalado: {v}"})
                    INSTALL_LOG.put({"level": "ok", "msg": "Verificación de dependencias completada."})
            threading.Thread(target=run_deps, daemon=True).start()
            self.send_json({"ok": True})
            return

        elif path == "/api/install/uninstall-all":
            agent_path_str = body.get("agent_path")
            if not agent_path_str:
                self.send_error_json(400, "Falta agent_path"); return
            def run_uninstall():
                INSTALL_LOG.put({"level": "info", "msg": "Iniciando desinstalación..."})
                agent_path = Path(agent_path_str)
                hermes_base = agent_path / "skills" / "andorina"
                import shutil
                try:
                    if (hermes_base / "scripts").exists(): shutil.rmtree(hermes_base / "scripts")
                    if (hermes_base / "GUI").exists(): shutil.rmtree(hermes_base / "GUI")
                    if (hermes_base / "Andorina-Panel.sh").exists(): (hermes_base / "Andorina-Panel.sh").unlink()
                    if (hermes_base / "SKILL.md").exists(): (hermes_base / "SKILL.md").unlink()
                    INSTALL_LOG.put({"level": "info", "msg": "Código base eliminado."})
                    
                    if body.get("un_env") and (hermes_base / ".env").exists():
                        (hermes_base / ".env").unlink()
                        INSTALL_LOG.put({"level": "info", "msg": "Configuración (.env) eliminada."})
                        
                    if body.get("un_rbac") and (hermes_base / "state" / "guard_rules.json").exists():
                        (hermes_base / "state" / "guard_rules.json").unlink()
                        INSTALL_LOG.put({"level": "info", "msg": "Reglas RBAC eliminadas."})
                        
                    if body.get("un_mem"):
                        if (hermes_base / "state" / "memoria.json").exists(): (hermes_base / "state" / "memoria.json").unlink()
                        if (hermes_base / "state" / "inbox.json").exists(): (hermes_base / "state" / "inbox.json").unlink()
                        INSTALL_LOG.put({"level": "info", "msg": "Memoria e Inbox eliminados."})
                        
                    if body.get("un_notes"):
                        if (hermes_base / "state" / "notes").exists(): shutil.rmtree(hermes_base / "state" / "notes")
                        if (hermes_base / "state" / "alerts.json").exists(): (hermes_base / "state" / "alerts.json").unlink()
                        INSTALL_LOG.put({"level": "info", "msg": "Notas y Alertas eliminadas."})
                        
                    if body.get("un_souls") and (hermes_base / "state" / "souls").exists():
                        shutil.rmtree(hermes_base / "state" / "souls")
                        INSTALL_LOG.put({"level": "info", "msg": "Personalidades eliminadas."})
                        # Clean channel_prompts from Hermes config.yaml
                        try:
                            cfg_path = agent_path / "config.yaml"
                            if cfg_path.exists():
                                cfg_text = cfg_path.read_text(encoding="utf-8")
                                # Remove channel_prompts block under whatsapp:
                                cfg_text = re.sub(r"(whatsapp:\s*\n)(\s+channel_prompts:.*?)(\n\w)", r"\1\3", cfg_text, flags=re.DOTALL)
                                cfg_path.write_text(cfg_text, encoding="utf-8")
                                INSTALL_LOG.put({"level": "info", "msg": "channel_prompts limpiados de config.yaml."})
                        except Exception:
                            pass  # Non-fatal
                    
                    config_file = agent_path / "config.yaml"
                    if config_file.exists():
                        content = config_file.read_text(encoding="utf-8")
                        content = re.sub(r"\s*-\s*event:\s*message_received\n\s*command:.*hook_inbox\.py.*", "", content)
                        content = re.sub(r"\s*-\s*event:\s*whatsapp:message\n\s*command:.*hook_inbox\.py.*", "", content)
                        content = re.sub(r"\s*-\s*event:\s*message_received\n\s*command:.*webhook\.py.*", "", content)
                        content = re.sub(r"\s*-\s*event:\s*whatsapp:message\n\s*command:.*webhook\.py.*", "", content)
                        content = re.sub(r"\s*-\s*event:\s*pre_llm_call\n\s*command:.*guard\.py.*", "", content)
                        content = re.sub(r"\s*-\s*event:\s*pre_tool_call\n\s*command:.*guard\.py.*", "", content)
                        content = re.sub(r"\s*-\s*event:\s*pre_llm_call\n\s*command:.*orchestrator\.py.*", "", content)
                        content = re.sub(r"\s*-\s*event:\s*pre_tool_call\n\s*command:.*orchestrator\.py.*", "", content)
                        config_file.write_text(content, encoding="utf-8")
                        INSTALL_LOG.put({"level": "info", "msg": "Hooks eliminados."})
                        
                    soul_file = agent_path / "SOUL.md"
                    if soul_file.exists():
                        content = soul_file.read_text(encoding="utf-8")
                        content = re.sub(r"# --- WHATSAPP AGENT EXTENSION BEGIN ---.*?# --- WHATSAPP AGENT EXTENSION END ---", "", content, flags=re.DOTALL).strip()
                        soul_file.write_text(content + "\n", encoding="utf-8")
                        INSTALL_LOG.put({"level": "info", "msg": "SOUL.md restaurado."})
                        
                    hermes_cmd = os.environ.get("HERMES_CMD", "hermes")
                    desktop_file = Path.home() / ".config" / "autostart" / f"{hermes_cmd}-agent.desktop"
                    if desktop_file.exists():
                        desktop_file.unlink()
                        INSTALL_LOG.put({"level": "info", "msg": "Autostart eliminado."})
                    
                    INSTALL_LOG.put({"level": "ok", "msg": "Desinstalación completada con éxito."})
                except Exception as e:
                    INSTALL_LOG.put({"level": "error", "msg": f"Error: {e}"})
            threading.Thread(target=run_uninstall, daemon=True).start()
            self.send_json({"ok": True})
            return

        # ── Contacts ──
        if path == "/api/contacts/auth":
            threading.Thread(target=run_script, args=("utils/auth.py",), daemon=True).start()
            self.send_json({"ok": True})
            return

        elif path == "/api/contacts/refresh":
            out, _, _ = run_script("tools/contacts.py", "refresh", timeout=60)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": True, "raw": out})

        # ── Notes ──
        elif path == "/api/notes/set":
            jid = body.get("jid")
            text = body.get("text", "")
            if not jid:
                self.send_error_json(400, "Missing jid"); return
            out, _, _ = run_script("tools/contacts.py", "note-set", jid, text)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": True})
            
        elif path == "/api/notes/section-set":
            jid = body.get("jid")
            section = body.get("section")
            text = body.get("text", "")
            if not jid or not section:
                self.send_error_json(400, "Missing jid or section"); return
            out, _, _ = run_script("tools/contacts.py", "note-section-set", jid, section, text)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": True})
            
        elif path.startswith("/api/notes/"):
            jid = path.split("/api/notes/")[1]
            text = body.get("text", "")
            if not text:
                self.send_error_json(400, "Missing text"); return
            out, _, _ = run_script("tools/contacts.py", "note-add", jid, text)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": True})
        # ── Uploads ──
        elif path == "/api/upload":
            filename = body.get("filename", "")
            b64_data = body.get("data", "")
            if not filename or not b64_data:
                self.send_error_json(400, "Missing filename or data")
                return
            try:
                if "," in b64_data:
                    b64_data = b64_data.split(",", 1)[1]
                raw_data = base64.b64decode(b64_data)
                filepath = UPLOADS_DIR / f"{int(time.time())}_{filename}"
                filepath.write_bytes(raw_data)
                self.send_json({"ok": True, "path": str(filepath.absolute())})
            except Exception as e:
                self.send_error_json(500, f"Upload failed: {e}")

        # ── Inbox ──
        elif path == "/api/inbox/mark-read":
            chat_id = body.get("chatId") # Can be None to mark all
            inbox_data = read_json(STATE_DIR / "inbox.json") or []
            marked = 0
            for m in inbox_data:
                if chat_id is None or m.get("chatId") == chat_id:
                    if m.get("read") is False:
                        m["read"] = True
                        marked += 1
            if marked > 0:
                write_json(STATE_DIR / "inbox.json", inbox_data)
            self.send_json({"ok": True, "marked": marked})

        # ── Send ──
        elif path == "/api/send/message":
            chat_id = body.get("chatId", "")
            text = body.get("text", "")
            filepath = body.get("file", "")
            if not chat_id or (not text and not filepath):
                self.send_error_json(400, "Missing chatId or text/file"); return
            args = ["message", chat_id, text]
            if filepath:
                args += ["--file", filepath]
            out, err, rc = run_script("transport/send.py", *args, timeout=30)
            if rc != 0:
                print(f"[DEBUG] send.py failed! out={out!r} err={err!r}", flush=True)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out, "error": err})

        elif path == "/api/send/broadcast":
            text = body.get("text", "")
            jids = body.get("jids", "")
            filepath = body.get("file", "")
            if not jids or (not text and not filepath):
                self.send_error_json(400, "Missing jids or text/file"); return
            args = ["broadcast", text, jids]
            if filepath:
                args += ["--file", filepath]
            out, err, rc = run_script("transport/send.py", *args, timeout=120)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        # ── Agenda ──
        elif path == "/api/agenda/schedule":
            chat_id = body.get("chatId", "")
            time_str = body.get("time", "")
            message = body.get("message", "")
            filepath = body.get("file", "")
            if not chat_id or not time_str or (not message and not filepath):
                self.send_error_json(400, "Missing fields"); return

            results = []
            for cid in chat_id.split(','):
                cid = cid.strip()
                if not cid: continue
                # agenda.py expects: auto-schedule <jid> <datetime> [filepath] [message]
                # It detects filepath by checking if args[0] exists as a file on disk
                args = ["auto-schedule", cid, time_str]
                if filepath:
                    args.append(filepath)  # positional: checked with Path.exists()
                args.append(message)
                out, err, rc = run_script("tools/agenda.py", *args)
                try:
                    res_dict = json.loads(out)
                    if isinstance(res_dict, dict):
                        if "payload" in res_dict and isinstance(res_dict["payload"], dict):
                            res_dict.update(res_dict.pop("payload"))
                        if res_dict.get("status") == "OK":
                            res_dict["ok"] = True
                        elif res_dict.get("status") in ("ERROR", "DENY"):
                            res_dict["ok"] = False
                    results.append(res_dict)
                except:
                    results.append({"jid": cid, "ok": rc == 0, "raw": out, "error": err})

            self.send_json({"ok": True, "results": results})

        elif path == "/api/agenda/recurring/add":
            chat_id = body.get("chatId", "")
            cron = body.get("cron", "")
            message = body.get("message", "")
            filepath = body.get("file", "")
            if not chat_id or not cron or (not message and not filepath):
                self.send_error_json(400, "Missing fields"); return

            results = []
            for cid in chat_id.split(','):
                cid = cid.strip()
                if not cid: continue
                args = ["recurring", "add", cid, cron]
                if filepath:
                    args.append(filepath)
                args.append(message)
                out, err, rc = run_script("tools/agenda.py", *args)
                try:
                    res_dict = json.loads(out)
                    if isinstance(res_dict, dict):
                        if "payload" in res_dict and isinstance(res_dict["payload"], dict):
                            res_dict.update(res_dict.pop("payload"))
                        if res_dict.get("status") == "OK":
                            res_dict["ok"] = True
                        elif res_dict.get("status") in ("ERROR", "DENY"):
                            res_dict["ok"] = False
                    results.append(res_dict)
                except:
                    results.append({"jid": cid, "ok": rc == 0, "raw": out, "error": err})

            self.send_json({"ok": True, "results": results})

        # ── Alerts ──
        elif path == "/api/alerts/add":
            source = body.get("source", "")
            target = body.get("target", "")
            keywords = body.get("keywords")
            if not source or not target:
                self.send_error_json(400, "Missing source or target"); return
            args = ["add", source, target]
            if keywords: args += ["--keywords", keywords]
            out, _, rc = run_script("tools/alerts.py", *args)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        elif path == "/api/webhooks/add":
            import uuid as _uuid, time as _wtime
            name = body.get("name", "").strip()
            targets = body.get("targets", [])
            template = body.get("template", "🔔 *{{_name}}*\n{{_summary}}").strip()
            secret = body.get("secret", "").strip()
            wh_id = body.get("id") or _uuid.uuid4().hex[:12]
            if not name or not targets:
                self.send_error_json(400, "name and targets required"); return
            hooks = _load_webhooks()
            # Update existing if same id
            existing = next((h for h in hooks if h.get("id") == wh_id), None)
            if existing:
                existing.update({"name": name, "targets": targets, "template": template, "secret": secret})
            else:
                hooks.append({"id": wh_id, "name": name, "enabled": True,
                              "targets": targets, "template": template, "secret": secret,
                              "created_at": _wtime.strftime("%Y-%m-%dT%H:%M:%S"),
                              "last_triggered": None, "trigger_count": 0})
            _save_webhooks(hooks)
            self.send_json({"ok": True, "id": wh_id})

        elif path.startswith("/api/webhooks/toggle/"):
            wh_id = path.split("/api/webhooks/toggle/")[1]
            hooks = _load_webhooks()
            hook = next((h for h in hooks if h.get("id") == wh_id), None)
            if not hook:
                self.send_error_json(404, "Not found"); return
            hook["enabled"] = not hook.get("enabled", True)
            _save_webhooks(hooks)
            self.send_json({"ok": True, "enabled": hook["enabled"]})

        elif path.startswith("/api/webhooks/test/"):
            wh_id = path.split("/api/webhooks/test/")[1]
            hooks = _load_webhooks()
            hook = next((h for h in hooks if h.get("id") == wh_id), None)
            if not hook:
                self.send_error_json(404, "Not found"); return
            test_payload = {"_test": True, "source": "Andoriña Panel",
                            "event": "test", "message": "Webhook de prueba ✅"}
            _dispatch_webhook(hook, test_payload)
            self.send_json({"ok": True, "message": "Test enviado"})

        # ── Guard / RBAC ──
        elif path == "/api/guard/rules":
            rules = body.get("rules")
            if not rules:
                self.send_error_json(400, "Missing rules"); return
            if "_available_permissions" in rules:
                del rules["_available_permissions"]
            write_json(STATE_DIR / "guard_rules.json", rules)
            # Propagate soul/role/embed model changes to Hermes config + SOUL.md
            if any(k in rules for k in ("global_default_soul", "global_default_role", "knowledge_embed_model")):
                _run_soul_sync()
            self.send_json({"ok": True, "message": "Rules saved"})

        elif path == "/api/guard/set-role":
            jid = body.get("jid", "")
            role = body.get("role", "")
            if not jid or not role:
                self.send_error_json(400, "Missing jid or role"); return
            out, _, rc = run_script("utils/admin_cli.py", "role", "set", jid, role)
            soul = body.get("soul")
            if soul: run_script("utils/admin_cli.py", "soul", "set", jid, soul)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})
            
        elif path == "/api/guard/soul/set":
            jid = body.get("jid", "")
            soul = body.get("soul", "")
            if not jid:
                self.send_error_json(400, "Missing jid"); return
            out, _, rc = run_script("utils/admin_cli.py", "soul", "set", jid, soul)
            _run_soul_sync()  # Update channel_prompts in Hermes config.yaml
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        elif path == "/api/guard/reset":
            jid = body.get("jid", "")
            if not jid:
                self.send_error_json(400, "Missing jid"); return
            out, _, rc = run_script("security/orchestrator.py", "reset", jid)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        # ── Chatbot ──
        elif path == "/api/chatbot/toggle":
            action = body.get("action", "on")
            out, _, rc = run_script("utils/admin_cli.py", "chatbot", action)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        elif path == "/api/chatbot/mute":
            jid = body.get("jid", "")
            action = body.get("action", "mute")
            if not jid:
                self.send_error_json(400, "Missing jid"); return
            out, _, rc = run_script("utils/admin_cli.py", "chatbot", action, jid)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        # ── Away ──
        elif path == "/api/away/set":
            message = body.get("message", "")
            if not message:
                self.send_error_json(400, "Missing message"); return
            out, _, rc = run_script("utils/admin_cli.py", "away", message)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        elif path == "/api/away/off":
            out, _, rc = run_script("utils/admin_cli.py", "away", "off")
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        # ── Souls ──
        elif path == "/api/souls/save":
            name = body.get("name", "")
            content = body.get("content", "")
            is_sandbox = body.get("is_sandbox", False)
            if not name:
                self.send_error_json(400, "Missing name"); return
            SOULS_DIR.mkdir(parents=True, exist_ok=True)
            if is_sandbox:
                # Save to sandbox prompt.md
                sandbox_dir = SOULS_DIR / name
                soul_file = (sandbox_dir / "prompt.md").resolve()
                if not soul_file.is_relative_to(SOULS_DIR.resolve()):
                    self.send_error_json(403, "Invalid name"); return
                sandbox_dir.mkdir(parents=True, exist_ok=True)
            else:
                soul_file = (SOULS_DIR / f"{name}.md").resolve()
                if not soul_file.is_relative_to(SOULS_DIR.resolve()):
                    self.send_error_json(403, "Invalid name"); return
            
            # Ensure parent directories exist for folder structure
            soul_file.parent.mkdir(parents=True, exist_ok=True)
            
            soul_file.write_text(content, encoding="utf-8")
            _run_soul_sync()
            self.send_json({"ok": True, "message": f"Soul '{name}' saved"})

        elif path == "/api/souls/rename":
            old_name = body.get("old_name")
            new_name = body.get("new_name")
            if not old_name or not new_name:
                self.send_error_json(400, "Missing names"); return
            
            # Resolve paths
            old_md = (SOULS_DIR / f"{old_name}.md").resolve()
            old_dir = (SOULS_DIR / old_name).resolve()
            new_md = (SOULS_DIR / f"{new_name}.md").resolve()
            new_dir = (SOULS_DIR / new_name).resolve()
            
            # Security checks
            if not old_md.is_relative_to(SOULS_DIR.resolve()) or not new_md.is_relative_to(SOULS_DIR.resolve()):
                self.send_error_json(403, "Invalid name"); return
                
            if not old_md.exists() and not old_dir.exists():
                self.send_error_json(404, "Old soul not found"); return
                
            if new_md.exists() or (new_dir.exists() and any(new_dir.iterdir())):
                self.send_error_json(409, "Target name already exists"); return
                
            import shutil
            # Ensure target parent exists
            new_md.parent.mkdir(parents=True, exist_ok=True)
            
            # Rename .md file if it exists
            if old_md.exists():
                old_md.rename(new_md)
                
            # Rename knowledge/sandbox dir if it exists
            if old_dir.exists():
                new_dir.parent.mkdir(parents=True, exist_ok=True)
                old_dir.rename(new_dir)
                
            # Update assigned JIDs
            rules = read_json(STATE_DIR / "guard_rules.json") or {}
            modified = False
            for jid, entry in rules.get("jids", {}).items():
                if entry.get("custom_soul") == old_name:
                    entry["custom_soul"] = new_name
                    modified = True
            if modified:
                write_json(STATE_DIR / "guard_rules.json", rules)
                
            _run_soul_sync()
            self.send_json({"ok": True})

        elif path == "/api/souls/rename_category":
            old_cat = body.get("old_cat", "")
            new_cat = body.get("new_cat", "")
            if not new_cat or "/" in old_cat or "/" in new_cat:
                self.send_error_json(400, "Invalid category name"); return
            
            new_dir = (SOULS_DIR / new_cat).resolve()
            if new_dir.exists():
                self.send_error_json(409, "Target category already exists"); return
            
            new_dir.mkdir(parents=True, exist_ok=True)
            
            if old_cat == "":
                # Move all root .md files into new_cat
                for f in SOULS_DIR.iterdir():
                    if f.is_file() and f.name.endswith(".md"):
                        base_name = f.name[:-3]
                        f.rename(new_dir / f.name)
                        # Also move its knowledge folder if it exists
                        k_dir = SOULS_DIR / base_name
                        if k_dir.is_dir():
                            k_dir.rename(new_dir / base_name)
            else:
                old_dir = (SOULS_DIR / old_cat).resolve()
                if not old_dir.is_relative_to(SOULS_DIR.resolve()):
                    self.send_error_json(403, "Invalid path"); return
                if not old_dir.exists():
                    self.send_error_json(404, "Category not found"); return
                old_dir.rename(new_dir)
            
            # Update assigned JIDs in guard_rules.json
            rules = read_json(STATE_DIR / "guard_rules.json") or {}
            modified = False
            for jid, entry in rules.get("jids", {}).items():
                cs = entry.get("custom_soul", "")
                if old_cat == "":
                    if cs and "/" not in cs:
                        entry["custom_soul"] = f"{new_cat}/{cs}"
                        modified = True
                else:
                    if cs.startswith(f"{old_cat}/"):
                        entry["custom_soul"] = f"{new_cat}/" + cs[len(old_cat)+1:]
                        modified = True
            if modified:
                write_json(STATE_DIR / "guard_rules.json", rules)
                
            _run_soul_sync()
            self.send_json({"ok": True})

        elif path == "/api/souls/knowledge/upload":
            soul_name = body.get("soul_name", "")
            filename = body.get("filename", "")
            file_b64 = body.get("content_b64", "")
            if not soul_name or not filename or not file_b64:
                self.send_error_json(400, "Missing soul_name, filename or content_b64"); return
            # Security: sanitize filename
            filename = Path(filename).name
            knowledge_dir = (SOULS_DIR / soul_name / "knowledge").resolve()
            if not knowledge_dir.is_relative_to(SOULS_DIR.resolve()):
                self.send_error_json(403, "Invalid path"); return
            knowledge_dir.mkdir(parents=True, exist_ok=True)
            target = knowledge_dir / filename
            try:
                target.write_bytes(base64.b64decode(file_b64))
                self.send_json({"ok": True, "message": f"Uploaded {filename} to {soul_name}/knowledge/"})
            except Exception as e:
                self.send_error_json(500, str(e))

        elif path == "/api/souls/knowledge/save":
            soul_name = body.get("soul_name", "")
            filename = body.get("filename", "")
            content = body.get("content", "")
            if not soul_name or not filename:
                self.send_error_json(400, "Missing soul_name or filename"); return
            filename = Path(filename).name
            target = (SOULS_DIR / soul_name / "knowledge" / filename).resolve()
            if not target.is_relative_to(SOULS_DIR.resolve()):
                self.send_error_json(403, "Invalid path"); return
            TEXT_EXTS = {".txt", ".md", ".csv", ".json"}
            if target.suffix.lower() not in TEXT_EXTS:
                self.send_error_json(400, "Only text files can be edited"); return
            try:
                target.write_text(content, encoding="utf-8")
                self.send_json({"ok": True})
            except Exception as e:
                self.send_error_json(500, str(e))



        elif path == "/api/plugins/list":
            plugins = []
            if SOULS_DIR.exists():
                for p_dir in SOULS_DIR.iterdir():
                    if p_dir.is_dir() and (p_dir / "plugin.json").exists():
                        try:
                            config = json.loads((p_dir / "plugin.json").read_text(encoding="utf-8"))
                        except:
                            config = {}
                        has_code = (p_dir / "tools.py").exists()
                        has_prompt = (p_dir / "prompt.md").exists()
                        plugins.append({
                            "name": p_dir.name,
                            "config": config,
                            "has_code": has_code,
                            "has_prompt": has_prompt
                        })
            self.send_json({"ok": True, "plugins": plugins})

        elif path == "/api/plugins/load":
            plugin_name = body.get("plugin_name", "").strip()
            if not plugin_name:
                self.send_error_json(400, "Missing plugin_name"); return
            p_dir = (SOULS_DIR / plugin_name).resolve()
            if not p_dir.is_relative_to(SOULS_DIR.resolve()):
                self.send_error_json(403, "Invalid path"); return
                
            try:
                config_str = (p_dir / "plugin.json").read_text(encoding="utf-8") if (p_dir / "plugin.json").exists() else "{}"
                prompt_str = (p_dir / "prompt.md").read_text(encoding="utf-8") if (p_dir / "prompt.md").exists() else ""
                code_str = (p_dir / "tools.py").read_text(encoding="utf-8") if (p_dir / "tools.py").exists() else ""
                log_str = (p_dir / "plugin.log").read_text(encoding="utf-8") if (p_dir / "plugin.log").exists() else ""
                self.send_json({
                    "ok": True,
                    "config": config_str,
                    "prompt": prompt_str,
                    "code": code_str,
                    "logs": log_str
                })
            except Exception as e:
                self.send_error_json(500, str(e))

        elif path == "/api/plugins/save":
            plugin_name = body.get("plugin_name", "").strip()
            filename = body.get("filename", "").strip()
            content = body.get("content", "")
            if not plugin_name or not filename:
                self.send_error_json(400, "Missing plugin_name or filename"); return
            
            # Sanitizar nombre
            plugin_name = re.sub(r'[^a-zA-Z0-9_\-]', '', plugin_name)
            if filename not in ["plugin.json", "prompt.md", "tools.py"]:
                self.send_error_json(400, "Invalid filename for plugin"); return
                
            p_dir = (SOULS_DIR / plugin_name).resolve()
            if not p_dir.is_relative_to(SOULS_DIR.resolve()):
                self.send_error_json(403, "Invalid path"); return
                
            p_dir.mkdir(parents=True, exist_ok=True)
            target_file = p_dir / filename
            
            # Si es tools.py, nos aseguramos que existe __init__.py en souls y en plugin
            if not (SOULS_DIR / "__init__.py").exists():
                (SOULS_DIR / "__init__.py").write_text("")
            if not (p_dir / "__init__.py").exists():
                (p_dir / "__init__.py").write_text("")
                
            try:
                target_file.write_text(content, encoding="utf-8")
                self.send_json({"ok": True})
            except Exception as e:
                self.send_error_json(500, str(e))

        elif path == "/api/plugins/delete":
            plugin_name = body.get("plugin_name", "").strip()
            if not plugin_name:
                self.send_error_json(400, "Missing plugin_name"); return
            
            p_dir = (SOULS_DIR / plugin_name).resolve()
            if not p_dir.is_relative_to(SOULS_DIR.resolve()) or p_dir == SOULS_DIR.resolve():
                self.send_error_json(403, "Invalid path"); return
                
            if p_dir.exists() and p_dir.is_dir():
                import shutil
                shutil.rmtree(p_dir)
                self.send_json({"ok": True})
            else:
                self.send_error_json(404, "Plugin not found")

        elif path == "/api/jid/update":
            raw_jid = body.get("jid", "")
            if not raw_jid:
                self.send_error_json(400, "Missing jid"); return
            jid = raw_jid.split("@")[0].replace("+", "").replace(" ", "")
            rules = read_json(STATE_DIR / "guard_rules.json") or {}
            jids = rules.setdefault("jids", {})
            entry = jids.setdefault(jid, {})
            for key in ["role", "custom_soul", "wake_word", "wake_word_mode", "allowed_folders", "allowed_contact_tags", "allowed_chats"]:
                if key in body:
                    val = body[key]
                    if val == "" or val == []:
                        if key in entry:
                            del entry[key]
                    else:
                        entry[key] = val
            
            if body.get("password"):
                if body.get("password") == "__REMOVE__":
                    if "password_hash" in entry:
                        del entry["password_hash"]
                else:
                    entry["password_hash"] = hash_password(jid, body.get("password"))
                    
            # Phase 4: Intercept game assignment to DM
            assigned_soul = body.get("custom_soul")
            welcome_msg = None
            if assigned_soul and "@" not in raw_jid: # If it's a DM
                plugin_json_path = SOULS_DIR / assigned_soul / "plugin.json"
                if plugin_json_path.exists():
                    try:
                        p_config = read_json(plugin_json_path)
                        if p_config and p_config.get("type") == "game":
                            # Move custom_soul to dm_game
                            entry["dm_game"] = assigned_soul
                            entry["dm_mode"] = "game"
                            # Revert custom_soul to its previous value (or delete if it didn't exist)
                            if "custom_soul" in entry and entry["custom_soul"] == assigned_soul:
                                del entry["custom_soul"]
                            # Restore old custom_soul if it existed in the body but we overwrote it?
                            # Actually if body has custom_soul, it overwrote the old entry["custom_soul"] above.
                            # We can't recover the old one easily without reading it before.
                            # So we just delete it so it falls back to default, or if the GUI sent it, it's fine.
                            
                            welcome_msg = f"🎮 Tienes el juego *{p_config.get('name', assigned_soul)}* disponible. Di `/play` para activarlo. Di `/bot` para volver al asistente normal."
                    except Exception as e:
                        print(f"[API] Error checking game type: {e}")

            if not entry:
                del jids[jid]

            write_json(STATE_DIR / "guard_rules.json", rules)
            _run_soul_sync()  # Update channel_prompts in Hermes config.yaml
            
            if welcome_msg:
                try:
                    run_script("transport/send.py", "message", raw_jid, welcome_msg)
                except Exception as e:
                    print(f"[API] Error sending game welcome message: {e}")
            

            
            self.send_json({"ok": True, "message": f"JID {jid} updated"})

        # ── System ──
        elif path == "/api/tunnel/start":
            # Only owner or admin:system should start/stop tunnels
            is_auth, session = check_auth(self.headers, "admin:system")
            if not is_auth: return self.send_error_json(403, "No permission")
            
            t_type = body.get("type", "quick")
            token = body.get("token")
            
            sys.path.insert(0, str(SCRIPTS_DIR))
            from utils import tunnel
            ok, msg = tunnel.start_tunnel(port=PORT, token=token if t_type == "custom" else None)
            if ok:
                self.send_json({"ok": True, "url": msg})
            else:
                self.send_error_json(500, msg)
                
        elif path == "/api/tunnel/stop":
            is_auth, session = check_auth(self.headers, "admin:system")
            if not is_auth: return self.send_error_json(403, "No permission")
            sys.path.insert(0, str(SCRIPTS_DIR))
            from utils import tunnel
            tunnel.stop_tunnel()
            self.send_json({"ok": True})
        elif path == "/api/system/config-limits":
            is_auth, session = check_auth(self.headers, "admin:system")
            if not is_auth: return self.send_error_json(403, "No permission")
            u_limit = body.get("user_char_limit")
            m_limit = body.get("memory_char_limit")
            
            try:
                hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
                cfg_path = hermes_home / "config.yaml"
                if cfg_path.exists():
                    content = cfg_path.read_text(encoding="utf-8")
                    
                    # Replace values using regex to preserve YAML formatting
                    if u_limit is not None:
                        if re.search(r"^\s*user_char_limit:.*", content, flags=re.MULTILINE):
                            content = re.sub(r"^\s*user_char_limit:.*", f"  user_char_limit: {u_limit}", content, flags=re.MULTILINE)
                        else:
                            content += f"\n  user_char_limit: {u_limit}\n"
                            
                    if m_limit is not None:
                        if re.search(r"^\s*memory_char_limit:.*", content, flags=re.MULTILINE):
                            content = re.sub(r"^\s*memory_char_limit:.*", f"  memory_char_limit: {m_limit}", content, flags=re.MULTILINE)
                        else:
                            content += f"\n  memory_char_limit: {m_limit}\n"
                            
                    cfg_path.write_text(content, encoding="utf-8")
                    
                self.send_json({"ok": True})
            except Exception as e:
                self.send_error_json(500, f"Error saving limits: {e}")
            
        elif path == "/api/system/repair":
            out, err, rc = run_script("utils/bridge_health.py", timeout=30)
            self.send_json({"ok": rc == 0, "output": out + err})

        elif path == "/api/patches/repair":
            try:
                env = os.environ.copy()
                if "HERMES_HOME" not in env:
                    env["HERMES_HOME"] = str(Path.home() / ".hermes")
                r = subprocess.run(
                    [sys.executable, str(SOURCE_DIR / "check_patches.py"), "--repair"],
                    capture_output=True, text=True, timeout=60, env=env
                )
                self.send_json({
                    "ok": r.returncode == 0,
                    "output": (r.stdout + r.stderr).strip()
                })
            except Exception as e:
                self.send_error_json(500, str(e))

        elif path == "/api/update/run":
            def run_update():
                INSTALL_LOG.put({"level": "info", "msg": "🔄 Iniciando actualización de Andoriña..."})
                updater = SOURCE_DIR / "andorina_updater.py"
                if not updater.exists():
                    INSTALL_LOG.put({"level": "error", "msg": "❌ andorina_updater.py no encontrado"})
                    return
                p = subprocess.Popen(
                    [sys.executable, str(updater), "--update"],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
                )
                for line in iter(p.stdout.readline, ""):
                    line = line.rstrip()
                    if line:
                        INSTALL_LOG.put({"level": "info", "msg": line})
                p.wait()
                level = "ok" if p.returncode == 0 else "error"
                INSTALL_LOG.put({"level": level, "msg": "✅ Actualización completada." if p.returncode == 0 else "❌ Error en la actualización."})
            threading.Thread(target=run_update, daemon=True).start()
            self.send_json({"ok": True, "msg": "Actualización iniciada. Sigue el progreso en la consola."})

        elif path == "/api/system/wipe-logs":
            out, err, rc = run_script("utils/wipe_logs.py", timeout=10)
            self.send_json({"ok": rc == 0, "output": out + err})

        elif path == "/api/system/restart":
            self.send_json({"ok": True, "msg": "Reiniciando servidor y bridge..."})
            def restart_all():
                time.sleep(1)
                cmd = os.environ.get("HERMES_CMD", "hermes")
                subprocess.run(["bash", "-c", f"{cmd} gateway stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.Popen(["bash", "-c", f"{cmd} gateway start"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.execv(sys.executable, [sys.executable] + sys.argv)
            threading.Thread(target=restart_all, daemon=True).start()
            return

        elif path == "/api/system/restart-server":
            self.send_json({"ok": True, "msg": "Reiniciando servidor del panel..."})
            def restart_server_only():
                time.sleep(1)
                os.execv(sys.executable, [sys.executable] + sys.argv)
            threading.Thread(target=restart_server_only, daemon=True).start()
            return


        elif path == "/api/system/install-panel":
            desktop_path = Path.home() / ".local" / "share" / "applications" / "andorina-panel.desktop"
            
            hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
            target_installed = hermes_home / "skills" / "andorina"
            if target_installed.exists() and (target_installed / "Andorina-Panel.sh").exists():
                launcher_sh = target_installed / "Andorina-Panel.sh"
                icon_path = target_installed / "GUI" / "static" / "logo.png"
            else:
                launcher_sh = PROJECT_DIR / "Andorina-Panel.sh"
                icon_path = PROJECT_DIR / "GUI" / "static" / "logo.png"
                
            icon_str = str(icon_path.absolute()) if icon_path.exists() else "utilities-terminal"
            
            warning = None
            if desktop_path.exists():
                existing = desktop_path.read_text(encoding="utf-8")
                if "X-Andorina-Source=" in existing:
                    old_path = existing.split("X-Andorina-Source=")[1].split("\n")[0].strip()
                    if old_path != str(launcher_sh.absolute()):
                        warning = "Ya existe un acceso directo apuntando a otra ruta. Se ha actualizado."
            
            content = f"""[Desktop Entry]
Name=Andoriña Panel
Comment=Panel de Control de Andoriña
Exec=bash "{launcher_sh.absolute()}"
Icon={icon_str}
Terminal=false
Type=Application
Categories=Utility;
X-Andorina-Source={launcher_sh.absolute()}
"""
            desktop_path.parent.mkdir(parents=True, exist_ok=True)
            desktop_path.write_text(content)
            
            user_desktop = Path.home() / "Desktop" / "Andorina-Panel.desktop"
            if Path.home().joinpath("Escritorio").exists():
                user_desktop = Path.home() / "Escritorio" / "Andorina-Panel.desktop"
            if user_desktop.parent.exists():
                user_desktop.write_text(content)
                user_desktop.chmod(0o755)
            
            resp = {"ok": True, "output": "Acceso directo instalado."}
            if warning: resp["warning"] = warning
            self.send_json(resp)
            # Refresh desktop menu (GNOME/KDE)
            try:
                subprocess.run(
                    ["update-desktop-database",
                     str(Path.home() / ".local" / "share" / "applications")],
                    capture_output=True, timeout=5
                )
            except Exception:
                pass


        elif path == "/api/system/uninstall-panel":
            Path(Path.home() / ".local" / "share" / "applications" / "andorina-panel.desktop").unlink(missing_ok=True)
            Path(Path.home() / "Desktop" / "Andorina-Panel.desktop").unlink(missing_ok=True)
            Path(Path.home() / "Escritorio" / "Andorina-Panel.desktop").unlink(missing_ok=True)
            # Refresh desktop menu so the entry disappears immediately
            try:
                subprocess.run(
                    ["update-desktop-database",
                     str(Path.home() / ".local" / "share" / "applications")],
                    capture_output=True, timeout=5
                )
            except Exception:
                pass
            self.send_json({"ok": True, "output": "Acceso directo eliminado."})


        elif path == "/api/system/start-service":
            target = body.get("target")
            try:
                cmd = os.environ.get("HERMES_CMD", "hermes")
                if target == "bridge":
                    subprocess.Popen(["bash", "-c", f"{cmd} gateway start"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.send_json({"ok": True, "output": f"Iniciando {target}..."})
            except Exception as e:
                self.send_error_json(500, str(e))

        elif path == "/api/system/stop-service":
            target = body.get("target")
            try:
                cmd = os.environ.get("HERMES_CMD", "hermes")
                if target == "bridge":
                    subprocess.Popen(["bash", "-c", f"{cmd} gateway stop"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.send_json({"ok": True, "output": f"Deteniendo {target}..."})
            except Exception as e:
                self.send_error_json(500, str(e))

        # ── Per-user Away ──
        elif path == "/api/away/set-custom":
            jid = body.get("jid", "")
            message = body.get("message", "")
            if not jid or not message:
                self.send_error_json(400, "Missing jid or message"); return
            away_file = STATE_DIR / "away.json"
            data = read_json(away_file) or {}
            if "custom" not in data: data["custom"] = {}
            data["custom"][jid] = message
            write_json(away_file, data)
            self.send_json({"ok": True})

        elif path == "/api/away/clear-custom":
            jid = body.get("jid", "")
            if not jid: self.send_error_json(400, "Missing jid"); return
            away_file = STATE_DIR / "away.json"
            data = read_json(away_file) or {}
            if "custom" in data:
                data["custom"].pop(jid, None)
                # Also remove by stripped number in case of format mismatch
                num = jid.split("@")[0] if "@" in jid else jid
                data["custom"].pop(num, None)
            write_json(away_file, data)
            self.send_json({"ok": True})

        # ── Environment save ──
        elif path == "/api/env":
            updates = body.get("updates", {})
            _, env_path = read_env_file()
            if not env_path:
                self.send_error_json(404, "No .env found"); return
            text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
            for k, v in updates.items():
                pat = rf"^{re.escape(k)}=.*"
                repl = f"{k}={v}"
                if re.search(pat, text, flags=re.MULTILINE):
                    text = re.sub(pat, repl, text, flags=re.MULTILINE)
                else:
                    if text and not text.endswith("\n"): text += "\n"
                    text += f"{repl}\n"
            
            deletes = body.get("deletes", [])
            for k in deletes:
                pat = rf"^{re.escape(k)}=.*\n?"
                text = re.sub(pat, "", text, flags=re.MULTILINE)
                
            env_path.write_text(text, encoding="utf-8")
            log_event("info", f"env updated: {list(updates.keys())}, deleted: {deletes}")
            self.send_json({"ok": True, "message": "Environment updated"})

        # ── File System Browser ──
        elif path == "/api/fs/list":
            req_dir = body.get("dir", str(Path.home()))
            try:
                p = Path(req_dir).resolve()
                if not p.exists() or not p.is_dir():
                    self.send_error_json(404, "Directory not found")
                    return
                
                dirs = []
                for child in p.iterdir():
                    try:
                        if child.is_dir() and not child.name.startswith("."):
                            dirs.append({"name": child.name, "path": str(child.absolute())})
                    except PermissionError:
                        pass
                
                dirs.sort(key=lambda x: x["name"].lower())
                parent = str(p.parent.absolute()) if p != p.parent else None
                self.send_json({"ok": True, "current": str(p), "parent": parent, "dirs": dirs})
            except Exception as e:
                self.send_error_json(500, str(e))

        # ── Install ──
        elif path == "/api/install/run":
            setup = PROJECT_DIR / "setup.py"
            if not setup.exists():
                self.send_error_json(404, "setup.py not found"); return
            log_event("info", "Installation started")
            self.send_json({"ok": True, "message": "Use terminal: python3 setup.py", "path": str(setup)})

        # ── Alerts update ──
        elif path == "/api/alerts/update":
            alerts = body.get("alerts")
            if alerts is None:
                self.send_error_json(400, "Missing alerts"); return
            write_json(STATE_DIR / "alerts.json", alerts)
            log_event("info", f"Alerts updated ({len(alerts)} rules)")
            self.send_json({"ok": True, "message": "Alerts saved"})

        else:
            self.send_error_json(404, "Unknown endpoint")

    # ── DELETE routes ─────────────────────────────────────────

    def do_DELETE(self):
        path = urllib.parse.urlparse(self.path).path

        if path.startswith("/api/agenda/remove/"):
            msg_id = path.split("/api/agenda/remove/")[1]
            out, _, rc = run_script("tools/agenda.py", "remove", msg_id)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        elif path.startswith("/api/souls/knowledge/delete/"):
            parts = urllib.parse.unquote(path.split("/api/souls/knowledge/delete/")[1]).rsplit("/", 1)
            if len(parts) != 2:
                self.send_error_json(400, "Missing soul/filename"); return
            soul_name, filename = parts
            target = (SOULS_DIR / soul_name / "knowledge" / filename).resolve()
            if not target.is_relative_to(SOULS_DIR.resolve()):
                self.send_error_json(403, "Invalid path"); return
            if target.exists():
                target.unlink()
                self.send_json({"ok": True})
            else:
                self.send_error_json(404, "File not found")

        elif path.startswith("/api/agenda/recurring/"):
            rec_id = path.split("/api/agenda/recurring/")[1]
            out, _, rc = run_script("tools/agenda.py", "recurring", "remove", rec_id)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        elif path.startswith("/api/alerts/remove/"):
            source = urllib.parse.unquote(path.split("/api/alerts/remove/")[1])
            out, _, rc = run_script("tools/alerts.py", "remove", source)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        elif path.startswith("/api/webhooks/remove/"):
            wh_id = urllib.parse.unquote(path.split("/api/webhooks/remove/")[1])
            hooks = _load_webhooks()
            new_hooks = [h for h in hooks if h.get("id") != wh_id]
            _save_webhooks(new_hooks)
            self.send_json({"ok": True})

        elif path.startswith("/api/guard/remove-role/"):
            jid = path.split("/api/guard/remove-role/")[1]
            out, _, rc = run_script("utils/admin_cli.py", "role", "remove", jid)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        elif path.startswith("/api/notes/"):
            jid = path.split("/api/notes/")[1]
            out, _, rc = run_script("tools/contacts.py", "note-clear", jid)
            try: self.send_json(json.loads(out))
            except: self.send_json({"ok": rc == 0, "raw": out})

        elif path.startswith("/api/souls/delete/"):
            name = urllib.parse.unquote(path.split("/api/souls/delete/")[1])
            soul_md = (SOULS_DIR / f"{name}.md").resolve()
            soul_dir = (SOULS_DIR / name).resolve()
            
            if not soul_md.is_relative_to(SOULS_DIR.resolve()) or not soul_dir.is_relative_to(SOULS_DIR.resolve()):
                self.send_error_json(403, "Invalid name"); return
                
            deleted = False
            import shutil
            if soul_md.exists():
                soul_md.unlink()
                deleted = True
            if soul_dir.exists() and soul_dir.is_dir():
                shutil.rmtree(soul_dir)
                deleted = True
                
            if deleted:
                # Clean up assignments
                rules = read_json(STATE_DIR / "guard_rules.json") or {}
                modified = False
                for jid, entry in rules.get("jids", {}).items():
                    if entry.get("custom_soul") == name:
                        entry["custom_soul"] = ""
                        modified = True
                if modified:
                    write_json(STATE_DIR / "guard_rules.json", rules)
                _run_soul_sync()  # Update channel_prompts in Hermes config.yaml
                self.send_json({"ok": True, "message": f"Soul '{name}' deleted"})
            else:
                self.send_error_json(404, "Soul not found")

        else:
            self.send_error_json(404, "Unknown endpoint")

    def log_message(self, fmt, *args):
        # Quieter logging
        arg_str = str(args[0]) if args else ""
        if "/api/" in arg_str:
            return
        super().log_message(fmt, *args)


# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    port = PORT
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])
            
    bind_ip = "127.0.0.1"
    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        if idx + 1 < len(sys.argv):
            bind_ip = sys.argv[idx + 1]

    print(f"🕊️  Andoriña GUI — http://{bind_ip}:{port}")
    print(f"   Proyecto: {PROJECT_DIR}")
    print(f"   Scripts:  {SCRIPTS_DIR}")
    print(f"   Estado:   {STATE_DIR}")
    print(f"   Estáticos: {STATIC_DIR}")
    print(f"   Ctrl+C para detener\n")

    server = http.server.ThreadingHTTPServer((bind_ip, port), APIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido.")
        server.server_close()
