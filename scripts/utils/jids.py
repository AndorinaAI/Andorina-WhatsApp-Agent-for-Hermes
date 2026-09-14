"""
utils/jids.py — Utilidades centralizadas de normalización de JIDs y números de teléfono.

FASE 1 del refactor V1.6: consolida implementaciones duplicadas de:
  - clean_number:     rbac.py, input_guard.py, admin_cli.py, GUI/server.py
  - extract_number:   rbac.py, contacts.py, admin_cli.py
  - jid_match:        webhook.py, rbac.py (resolve_role suffix loop), GUI/server.py
  - normalize_text:   contacts.py, webhook.py, knowledge_retrieval.py
  - normalize_jid:    alerts.py, webhook.py (_norm local)
  - resolve_sender_label:  alerts.py, webhook.py
"""
import re
import os
import sys
import unicodedata
from pathlib import Path


def _get_default_country_code() -> str:
    """Lee DEFAULT_COUNTRY_CODE del .env de la skill, con fallback a '34'."""
    try:
        hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
        env_file = hermes_home / "skills" / "andorina" / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("DEFAULT_COUNTRY_CODE="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return "34"


def clean_number(jid: str) -> str:
    """Devuelve solo los dígitos del JID (quita @s.whatsapp.net, @g.us, +, espacios, etc.)."""
    if not isinstance(jid, str): return ""
    bare = jid.split("@")[0] if "@" in jid else jid
    return re.sub(r"[^\d]", "", bare)


def extract_number(jid: str) -> str:
    """Extrae la parte bare de un JID (sin sufijo de dominio). Sin limpiar dígitos."""
    if not isinstance(jid, str): return ""
    return jid.split("@")[0] if "@" in jid else jid


def jid_match(stored: str, incoming: str) -> bool:
    """Compara dos JIDs por sufijo numérico. Tolera prefijos de país distintos."""
    s = clean_number(stored)
    c = clean_number(incoming)
    if not s or not c:
        return False
    return s == c or c.endswith(s) or s.endswith(c)


def normalize_text(text: str) -> str:
    """Lowercase + strip acentos. Unifica contacts.norm() y webhook.normalize_text()."""
    t = str(text).lower().strip()
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def normalize_jid(val: str, country_code: str | None = None) -> str:
    """Normaliza un número/JID parcial a JID completo.
    Unifica alerts._norm_jid() y webhook._norm().

    Si country_code es None, se lee DEFAULT_COUNTRY_CODE del .env (fallback '34').
    """
    if country_code is None:
        country_code = _get_default_country_code()
    if not val:
        return val if isinstance(val, str) else ""
    if "@" in val:
        return val
    num = re.sub(r"[^\d]", "", val).lstrip("0")
    if not num:
        return val
    if 8 <= len(num) <= 10:
        num = country_code + num
    if len(num) > 13 or "-" in val:
        return f"{num}@g.us"
    return f"{num}@s.whatsapp.net"


def resolve_lid_to_phone(lid_str: str, hermes_dir: str | None = None, contacts_cache_file: str | None = None) -> str | None:
    """Resuelve un LID de WhatsApp a un número de teléfono canónico.

    Usa la cadena de resolución:
      1. lid-mapping-{lid}_reverse.json en la sesión de WhatsApp
      2. contacts_cache.json (campo 'lid' o chatId)

    Args:
        lid_str: JID con sufijo @lid (ej. '212725569433687@lid') o solo el número LID.
        hermes_dir: Ruta al directorio Hermes (por defecto $HERMES_HOME o ~/.hermes).
        contacts_cache_file: Ruta al contacts_cache.json (por defecto state/contacts_cache.json).

    Returns:
        Número de teléfono limpio (sin @) o None si no se pudo resolver.
    """
    if not lid_str:
        return None
    lid_num = lid_str.split("@")[0] if "@" in lid_str else lid_str

    import json as _json
    import time as _time
    from pathlib import Path as _Path

    if hermes_dir is None:
        hermes_dir = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    hermes_path = _Path(hermes_dir)

    # 1. lid-mapping-*_reverse.json (fast path, hasta 4 reintentos)
    session_dir = hermes_path / "whatsapp" / "session"
    reverse_file = session_dir / f"lid-mapping-{lid_num}_reverse.json"
    for _ in range(4):
        if reverse_file.exists():
            try:
                val = _json.loads(reverse_file.read_text(encoding="utf-8"))
                if isinstance(val, str) and val:
                    return val.strip()
            except Exception:
                pass
        _time.sleep(0.5)

    # 2. contacts_cache.json — match by 'lid' field OR by chatId digits
    if contacts_cache_file is None:
        contacts_cache_file = str(hermes_path / "skills" / "andorina" / "state" / "contacts_cache.json")
    cache_path = _Path(contacts_cache_file)
    if cache_path.exists():
        try:
            data_cache = _json.loads(cache_path.read_text(encoding="utf-8"))
            for contact in data_cache.get("contacts", []):
                # Primary: explicit 'lid' field on the contact
                c_lid = str(contact.get("lid", "")).split("@")[0]
                if c_lid and c_lid == lid_num:
                    resolved = contact.get("chatId") or contact.get("id", "")
                    if resolved and "@s.whatsapp.net" in resolved:
                        return resolved.split("@")[0]
                # Secondary: chatId digits match the LID number
                c_id = contact.get("chatId", "") or contact.get("id", "")
                if "@s.whatsapp.net" in c_id and c_id.split("@")[0] == lid_num:
                    return c_id.split("@")[0]
        except Exception:
            pass

    return None


def resolve_sender_label(
    jid: str,
    state_dir,
    *,
    sender_name: str = "",
    inbox_file=None,
    bridge_url: str = "http://localhost:3000",
) -> str:
    """Resuelve un JID a un nombre legible para el usuario.
    Unifica alerts._resolve_label() y el bloque inline de webhook.py.

    Prioridades para grupos (@g.us):
      1. chat_name / senderName del inbox
      2. Bridge /groups
      3. Fallback: "Grupo {últimos 6 dígitos}"

    Prioridades para individuos:
      1. contacts_cache.json (Google Contacts)
      2. senderName del inbox (historial)
      3. pushName (sender_name arg)
      4. Fallback: número limpio

    Args:
        jid: JID completo del remitente/chat.
        state_dir: Path al directorio state/.
        sender_name: Nombre de WhatsApp (pushName), usado como último recurso.
        inbox_file: Path al inbox.json (opcional, para resolución por historial).
        bridge_url: URL del bridge WhatsApp (para consulta /groups).
    """
    import json as _json
    from pathlib import Path as _Path

    state_dir = _Path(state_dir)
    jid = jid or ""

    if "@g.us" in jid:
        # ── Grupos ────────────────────────────────────────────────────────────
        label = sender_name or ""

        # 1. Inbox chatName
        if not label and inbox_file and _Path(inbox_file).exists():
            try:
                for _m in reversed(_json.loads(_Path(inbox_file).read_text(encoding="utf-8"))):
                    if _m.get("chatId") == jid and _m.get("chatName"):
                        label = _m["chatName"]
                        break
            except Exception:
                pass

        # 2. Bridge /groups
        if not label:
            try:
                import urllib.request as _ur
                with _ur.urlopen(f"{bridge_url}/groups", timeout=2) as _gr:
                    _glist = _json.loads(_gr.read())
                    _giter = _glist if isinstance(_glist, list) else _glist.get("groups", [])
                    _gid = jid.split("@")[0]
                    for _g in _giter:
                        if (_g.get("id") or _g.get("chatId") or "").split("@")[0] == _gid:
                            label = _g.get("name") or _g.get("subject") or ""
                            break
            except Exception:
                pass

        # 3. Fallback
        return label or f"Grupo {jid.split('@')[0][-6:]}"

    else:
        # ── Individuos ────────────────────────────────────────────────────────
        bare = (jid.split("@")[0] if "@" in jid else jid).lstrip("+").lstrip("0")

        # 1. Google Contacts cache
        cache_file = state_dir / "contacts_cache.json"
        if cache_file.exists():
            try:
                cache = _json.loads(cache_file.read_text(encoding="utf-8"))
                for c in cache.get("contacts", []):
                    c_id = (c.get("id") or c.get("chatId") or "").split("@")[0].lstrip("+").lstrip("0")
                    if jid_match(bare, c_id) and c.get("name"):
                        return c["name"]
            except Exception:
                pass

        # 2. Inbox senderName
        if inbox_file and _Path(inbox_file).exists():
            try:
                for _m in reversed(_json.loads(_Path(inbox_file).read_text(encoding="utf-8"))):
                    _mfrom = (_m.get("from") or "").split("@")[0].lstrip("+").lstrip("0")
                    if jid_match(bare, _mfrom):
                        if _m.get("senderName") and _m["senderName"] not in ("Me", "Bot (Hermes)"):
                            return _m["senderName"]
            except Exception:
                pass

        # 3. pushName / fallback
        return sender_name or bare or jid


# ── Identity resolution (session & JID) ────────────────────────────────────

def resolve_hook_jid(data: dict) -> str:
    """Resolve sender identity to a canonical JID from all available sources.

    Centraliza la lógica antes dispersa en knowledge_retrieval._resolve_jid()
    y orchestrator_hook. Usa la cadena completa de fallbacks:
      session_key → extra.user → session_id → task_id DB → sender_id → LID→phone.

    Args:
        data: Diccionario completo del hook payload de Hermes.

    Returns:
        JID canónico resuelto (ej. 34600000000@s.whatsapp.net) o string vacío.
    """
    import json as _json
    import os as _os
    import sqlite3 as _sqlite3
    from pathlib import Path as _Path

    session_key = data.get("session_key", "")
    session_id  = data.get("session_id", "")
    extra       = data.get("extra", {})
    jid = ""

    # 1. session_key
    if session_key and "whatsapp:dm:" in session_key:
        jid = session_key.split("whatsapp:dm:")[1]
    elif session_key and "whatsapp:group:" in session_key:
        # V1.6-Beta1: Extraer el SENDER individual, no el grupo.
        # Formato: whatsapp:group:<GROUP_JID>:<SENDER_NUMBER>
        raw = session_key.split("whatsapp:group:")[1]
        parts = raw.split(":")
        if len(parts) > 1:
            jid = parts[1]  # sender number (último segmento)
        else:
            jid = parts[0]  # fallback: sin sender explícito
    # 2. extra.user
    elif extra.get("user"):
        jid = extra["user"]
        if "@" not in jid:
            jid += "@s.whatsapp.net"
    # 3. session_id (only if it looks like a real JID/phone, not a UUID timestamp)
    elif "whatsapp:dm:" in session_id:
        jid = session_id.split("whatsapp:dm:")[1]
    elif "whatsapp:group:" in session_id:
        jid = session_id.split("whatsapp:group:")[1]
    elif session_id and ("@" in session_id or session_id.replace("+", "").isdigit()):
        jid = session_id

    # 4. task_id DB lookup
    if not jid and extra.get("task_id"):
        try:
            hermes_dir = _Path(_os.environ.get("HERMES_HOME", str(_Path.home() / ".hermes")))
            state_db = hermes_dir / "state.db"
            if state_db.exists():
                conn = _sqlite3.connect(str(state_db))
                cur = conn.cursor()
                cur.execute("SELECT user_id FROM sessions WHERE id = ?", (extra["task_id"],))
                row = cur.fetchone()
                if row and row[0]:
                    jid = row[0]
                conn.close()
        except Exception:
            pass

    # 5. sender_id (primary path for real WhatsApp messages via LID/V2 hooks)
    if not jid and extra.get("sender_id"):
        jid = extra["sender_id"]
    if not jid and data.get("sender_id"):
        jid = data["sender_id"]

    # 6. Resolve LID → canonical JID
    if jid and "@lid" in jid:
        phone = resolve_lid_to_phone(jid)
        if phone:
            jid = f"{phone}@s.whatsapp.net"
        else:
            print(f"[jids] ⚠️  Unresolved LID: {jid} — no mapping found",
                  file=sys.stderr)

    return jid


def is_whatsapp_session(data: dict) -> bool:
    """True only if the hook event comes from a WhatsApp session.

    Args:
        data: Diccionario completo del hook payload de Hermes.

    Returns:
        True si es una sesión de WhatsApp, False para TUI/CLI local.
    """
    extra = data.get("extra", {})
    if "whatsapp:" in data.get("session_key", ""):
        return True
    if "whatsapp:" in data.get("session_id", ""):
        return True
    if extra.get("platform") == "whatsapp" or data.get("platform") == "whatsapp":
        return True
    sid = extra.get("sender_id", "") or data.get("sender_id", "")
    if sid and ("@s.whatsapp.net" in sid or "@lid" in sid or "@g.us" in sid):
        return True
    return False



def resolve_chat_id(data: dict) -> str:
    """Extrae el chat_id efectivo del payload del hook.
    
    Para grupos retorna el JID del grupo (@g.us).
    Para DMs retorna el JID del individuo (@s.whatsapp.net).
    Útil para separar contexto de notas (grupo vs DM).
    
    Args:
        data: Diccionario completo del hook payload de Hermes.
    
    Returns:
        JID del chat efectivo (grupo o individuo) o string vacío.
    """
    session_key = data.get("session_key", "")

    if "whatsapp:group:" in session_key:
        # Formato: whatsapp:group:<GROUP_JID>:<SENDER>
        raw = session_key.split("whatsapp:group:")[1]
        group_jid = raw.split(":")[0]  # primer segmento = grupo
        return normalize_jid(group_jid) if group_jid else ""

    # DM: el sender JID es el chat_id
    jid = resolve_hook_jid(data)
    return normalize_jid(jid) if jid else ""
