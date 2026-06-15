#!/usr/bin/env python3
import sys
import json
import time
import re
import subprocess
import unicodedata
from pathlib import Path

def get_input():
    try:
        raw = sys.stdin.buffer.read()
        return raw.decode('utf-8')
    except Exception:
        return ""

SCRIPTS_DIR = Path(__file__).parent.parent.absolute()
STATE_DIR   = SCRIPTS_DIR.parent / "state"

# Import centralized env loading from common module
sys.path.append(str(Path(__file__).parent.parent))
from common import load_env
from security.output_pipeline.pipeline import run_pipeline

# Load .env to get the bot phone for filtering and admin for alerts
_env = load_env()
BOT_PHONE = _env.get("ANDORINA_BOT_PHONE", "").replace("+", "")
ADMIN_PHONE = _env.get("ADMIN_PHONE", "").replace("+", "")

INBOX_FILE = STATE_DIR / "inbox.json"
AWAY_FILE  = STATE_DIR / "away.json"
MAX_HISTORY = 500

# ── Away Auto-Responder ───────────────────────────────────────────────────────

def load_away():
    """Load away.json state. Returns dict with enabled, message, cooldown."""
    try:
        if AWAY_FILE.exists():
            data = json.loads(AWAY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {"enabled": False, "message": "", "cooldown": {}}

def save_away(away):
    """Atomic write of away.json."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = AWAY_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(away, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(AWAY_FILE)

def check_away_and_reply(chat_id, sender):
    """If Away mode is active and cooldown is OK, send the static reply.
    Returns True if a reply was sent (caller may want to continue processing)."""
    away = load_away()
    jid_key = chat_id.split("@")[0] if "@" in chat_id else chat_id
    
    # Check for custom message first (GUI stores full JID, CLI may store number-only)
    custom_map = away.get("custom", {})
    custom_msg = custom_map.get(chat_id) or custom_map.get(jid_key)
    
    if custom_msg:
        reply_msg = custom_msg
    else:
        # Fallback to global away
        if not away.get("enabled") or not away.get("message"):
            return False
        reply_msg = away["message"]

    # Don't auto-reply to ourselves or to the bot
    sender_clean = re.sub(r"[^\d]", "", sender)
    if sender_clean == BOT_PHONE:
        return False

    # Don't auto-reply to the owner
    # Suffix match: handles missing/different country prefix (same logic as rbac.is_owner)
    if ADMIN_PHONE and (
        sender_clean == ADMIN_PHONE
        or sender_clean.endswith(ADMIN_PHONE)
        or ADMIN_PHONE.endswith(sender_clean)
    ):
        return False

    # Cooldown configurable via .env (default 1h)
    cooldown_secs = int(_env.get("AWAY_COOLDOWN_SECS", 3600))
    now = time.time()
    cooldown = away.get("cooldown", {})
    last_reply = cooldown.get(jid_key, 0)
    if now - last_reply < cooldown_secs:
        return False  # Already replied recently

    # Send the away message
    try:
        res = run_pipeline(reply_msg, bypass_truncation=True)
        if res.get("status") == "OK":
            for chunk in res.get("chunks", []):
                subprocess.Popen([
                    sys.executable,
                    str(SCRIPTS_DIR / "transport" / "send.py"),
                    "message", chat_id, chunk
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return False

    # Update cooldown
    cooldown[jid_key] = now
    away["cooldown"] = cooldown
    save_away(away)
    return True


# ── JID matching helper ─────────────────────────────────────────────────────

def _jid_match(stored: str, incoming: str) -> bool:
    """Compare a stored source/target against an incoming chat_id.
    Strips all non-digits and uses suffix match to tolerate:
    - Different country prefix (34612345678 vs 612345678)
    - JID domain differences (@s.whatsapp.net vs @lid)
    Mirrors the logic in rbac.is_owner."""
    s = re.sub(r"[^\d]", "", stored)
    c = re.sub(r"[^\d]", "", incoming)
    if not s or not c:
        return False
    return s == c or c.endswith(s) or s.endswith(c)


# ── Fuzzy Alert Matching ──────────────────────────────────────────────────────

def normalize_text(text):
    """Normalize text for fuzzy matching: lowercase, strip accents/diacritics."""
    text = str(text).lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text

def strip_suffix(word):
    """Basic Spanish/English stemming: remove common plural/verb suffixes.
    'reuniones' -> 'reunion', 'exámenes' -> 'examen', 'trabajos' -> 'trabajo'"""
    w = word
    # Spanish plurals
    if w.endswith("iones"):  return w[:-2]   # reuniones -> reunion (after accent strip: reunion)
    if w.endswith("enes"):   return w[:-2]    # examenes -> examen
    if w.endswith("es") and len(w) > 4:  return w[:-2]   # clases -> clas
    if w.endswith("s") and len(w) > 3:   return w[:-1]   # trabajos -> trabajo
    return w

def fuzzy_keyword_match(message_text, keywords_csv):
    """Check if any keyword matches the message using fuzzy logic:
    1. Normalize accents (reunión == reunion)
    2. Strip common suffixes (reuniones matches reunion)
    3. Substring match (examen matches exámenes)
    Returns True if any keyword matches."""
    msg_norm = normalize_text(message_text)
    msg_words = re.split(r'\s+', msg_norm)
    msg_stems = [strip_suffix(w) for w in msg_words if len(w) > 2]

    keywords = [k.strip() for k in keywords_csv.split(",") if k.strip()]

    for kw in keywords:
        kw_norm = normalize_text(kw)
        kw_stem = strip_suffix(kw_norm)

        # 1. Direct substring match (normalized)
        if kw_norm in msg_norm:
            return True

        # 2. Stem match: keyword stem matches any word stem
        if kw_stem and any(kw_stem == s or s.startswith(kw_stem) or kw_stem.startswith(s)
                          for s in msg_stems if len(s) > 2):
            return True

        # 3. Word-level substring: any message word contains the keyword or vice versa
        if any(kw_norm in w or w in kw_norm for w in msg_words if len(w) > 2 and len(kw_norm) > 2):
            return True

    return False


def resolve_lid(lid_str, retries=4):
    """Attempts to resolve a LID to a phone number using Baileys reverse mapping files."""
    if not lid_str: return None
    lid_num = lid_str.split("@")[0]
    
    # Check if it's already a standard phone number length/start, but skip the naive starts-with check
    # since LIDs can start with any digit and be 14-16 digits long.
    if len(lid_num) <= 13:
        # Standard international numbers are usually max 13-14 digits. LIDs are often 15+.
        pass
        
    try:
        import os, time
        hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
        session_dir = hermes_home / "whatsapp" / "session"
        reverse_file = session_dir / f"lid-mapping-{lid_num}_reverse.json"
        
        for _ in range(retries):
            if reverse_file.exists():
                with open(reverse_file, "r", encoding="utf-8") as f:
                    val = json.load(f)
                    if isinstance(val, str):
                        return val
            time.sleep(0.5)
            
        # Fallback to contacts_cache.json
        cache_file = STATE_DIR / "contacts_cache.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for c in data.get("contacts", []):
                    c_id = c.get("id", "")
                    c_lid = c.get("lid", "")
                    if (c_lid and lid_num in c_lid) or (lid_num in c_id and "@lid" in c_id):
                        if "@s.whatsapp.net" in c_id:
                            return c_id.split("@")[0]
    except Exception:
        pass
    return None


# ── Core processing (also called directly from orchestrator_hook.py) ─────────────

def process_incoming_message(chat_id: str, sender: str, text: str,
                             is_bot: bool = False,
                             sender_name: str = "",
                             chat_name: str = "",
                             write_inbox: bool = True) -> None:
    """
    Write message to inbox, fire away auto-reply, and check alert rules.
    Pass write_inbox=False to skip the inbox write (e.g. from orchestrator_hook
    when whatsapp.py has already written it) and only run away/alert logic.
    """
    try:
        import fcntl as _fcntl
        from datetime import datetime as _dt

        date_str = time.strftime("%Y-%m-%dT%H:%M:%S")

        def _norm(jid):
            if not jid:
                return jid
            parts = jid.split("@")
            num = parts[0]
            cc = _env.get("DEFAULT_COUNTRY_CODE", "34")
            if len(num) >= 8 and len(num) <= 10 and num.isdigit():
                parts[0] = f"{cc}{num}"
                return "@".join(parts)
            return jid

        chat_id = _norm(chat_id) or chat_id
        sender  = _norm(sender)  or sender

        entry = {
            "chatId":     chat_id,
            "chatName":   chat_name,
            "from":       "Me" if is_bot else sender,
            "senderName": "Bot (Hermes)" if is_bot else sender_name,
            "text":       text or "",
            "date":       date_str,
            "type":       "text",
            "read":       is_bot,
        }

        if write_inbox:
            INBOX_FILE.parent.mkdir(parents=True, exist_ok=True)
            lock_file = INBOX_FILE.with_suffix(".lock")

            with open(lock_file, "w") as lf:
                _fcntl.flock(lf, _fcntl.LOCK_EX)
                try:
                    inbox = []
                    if INBOX_FILE.exists():
                        try:
                            data = json.loads(INBOX_FILE.read_text(encoding="utf-8"))
                            inbox = data if isinstance(data, list) else []
                        except Exception:
                            inbox = []

                    merged = False
                    if inbox and entry["type"] == "text":
                        try:
                            curr_dt = _dt.strptime(entry["date"], "%Y-%m-%dT%H:%M:%S")
                            for i in range(len(inbox) - 1, max(len(inbox) - 21, -1), -1):
                                prev = inbox[i]
                                if (prev.get("chatId") == entry["chatId"]
                                        and prev.get("from") == entry["from"]
                                        and prev.get("type") == "text"):
                                    prev_dt = _dt.strptime(prev["date"], "%Y-%m-%dT%H:%M:%S")
                                    if (_dt.strptime(entry["date"], "%Y-%m-%dT%H:%M:%S") - prev_dt).total_seconds() < 300:
                                        prev["text"] += "\n" + entry["text"]
                                        prev["date"]  = entry["date"]
                                        prev["read"]  = False
                                        merged = True
                                    break
                        except Exception:
                            pass

                    if not merged:
                        inbox.append(entry)
                    if len(inbox) > MAX_HISTORY:
                        inbox = inbox[-MAX_HISTORY:]

                    tmp = INBOX_FILE.with_suffix(".tmp")
                    tmp.write_text(json.dumps(inbox, ensure_ascii=False, indent=2), encoding="utf-8")
                    tmp.replace(INBOX_FILE)
                finally:
                    _fcntl.flock(lf, _fcntl.LOCK_UN)

        if is_bot:
            return

        # Away auto-responder
        check_away_and_reply(chat_id, sender)

        # Alert rules
        alerts_file = STATE_DIR / "alerts.json"
        if alerts_file.exists():
            try:
                alerts = json.loads(alerts_file.read_text(encoding="utf-8"))
                for rule in alerts:
                    source = rule.get("source", "")
                    if source and _jid_match(source, chat_id or ""):
                        target   = rule.get("target", "")
                        keywords = rule.get("keywords")
                        if keywords and not fuzzy_keyword_match(text or "", keywords):
                            continue
                        if target == "OWNER" and ADMIN_PHONE:
                            target = ADMIN_PHONE + "@s.whatsapp.net"
                        if target:
                            msg_text = (text or "").strip() or "[Multimedia recibido]"

                            # Human-readable label:
                            # groups → use chat_name (or look it up in inbox)
                            # individual → use sender number
                            if "@g.us" in (chat_id or ""):
                                label = chat_name or ""
                                if not label and INBOX_FILE.exists():
                                    try:
                                        for _m in reversed(
                                            json.loads(INBOX_FILE.read_text(encoding="utf-8"))
                                        ):
                                            if _m.get("chatId") == chat_id and _m.get("chatName"):
                                                label = _m["chatName"]
                                                break
                                    except Exception:
                                        pass
                                if not label:
                                    try:
                                        import urllib.request as _urlreq, os as _os2
                                        _burl = _os2.environ.get("WHATSAPP_BRIDGE_URL", "http://localhost:3000")
                                        with _urlreq.urlopen(f"{_burl}/groups", timeout=2) as _gr:
                                            _glist = json.loads(_gr.read())
                                            _gid = chat_id.split("@")[0]
                                            if isinstance(_glist, list):
                                                _giter = _glist
                                            else:
                                                _giter = _glist.get("groups", [])
                                            for _g in _giter:
                                                _gkey = (_g.get("id") or _g.get("chatId") or "").split("@")[0]
                                                if _gid and _gid == _gkey:
                                                    label = _g.get("name") or _g.get("subject") or ""
                                                    break
                                    except Exception:
                                        pass
                                if not label:
                                    gnum = chat_id.split("@")[0]
                                    label = f"Grupo {gnum[-6:]}"
                                sender_label = label
                            else:
                                # Individual: Google Contacts → inbox → WhatsApp pushName
                                sender_num = sender.split("@")[0] if "@" in sender else sender
                                _sbare = sender_num.lstrip("+").lstrip("0")
                                contact_name = ""
                                # 1. Google Contacts (contacts_cache.json) — highest priority
                                cache_file = STATE_DIR / "contacts_cache.json"
                                if cache_file.exists():
                                    try:
                                        cache = json.loads(cache_file.read_text(encoding="utf-8"))
                                        for c in cache.get("contacts", []):
                                            c_id = (c.get("id") or c.get("chatId") or "").split("@")[0].lstrip("+").lstrip("0")
                                            if _sbare and (_sbare in c_id or c_id in _sbare) and c.get("name"):
                                                contact_name = c["name"]
                                                break
                                    except Exception:
                                        pass
                                # 2. Inbox senderName (in case not in contacts)
                                if not contact_name and INBOX_FILE.exists():
                                    try:
                                        for _m in reversed(
                                            json.loads(INBOX_FILE.read_text(encoding="utf-8"))
                                        ):
                                            _mfrom = (_m.get("from") or "").split("@")[0].lstrip("+").lstrip("0")
                                            if _sbare and (_sbare in _mfrom or _mfrom in _sbare):
                                                if _m.get("senderName") and _m["senderName"] not in ("Me", "Bot (Hermes)"):
                                                    contact_name = _m["senderName"]
                                                    break
                                    except Exception:
                                        pass
                                # 3. WhatsApp pushName (fallback only)
                                if not contact_name:
                                    contact_name = sender_name or ""
                                sender_label = contact_name or sender_num

                            alert_text = f"🚨 Alerta de {sender_label}:\n\"{msg_text}\""
                            try:
                                subprocess.Popen([
                                    sys.executable,
                                    str(SCRIPTS_DIR / "transport" / "send.py"),
                                    "message", target, alert_text
                                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            except Exception:
                                pass
            except Exception:
                pass
    except Exception:
        pass


# ── Main (shell hook entry point) ───────────────────────────────────────────────────

def main():
    raw_data = get_input()
    if not raw_data:
        return

    try:
        event = json.loads(raw_data)
    except Exception:
        return

    # — Legacy format: {"event": "message_received", "payload": {...}}
    payload = None
    event_name = event.get("event", "")
    if event_name in ("message_received", "whatsapp:message"):
        payload = event.get("payload", {})

    # — Hermes pre_llm_call format: {"hook_event_name": "pre_llm_call", "extra": {...}}
    elif event.get("hook_event_name") == "pre_llm_call":
        extra  = event.get("extra", {})
        # Build a minimal payload from pre_llm_call fields
        sender = (extra.get("user") or event.get("session_key", "")).replace("+", "")
        if "whatsapp:dm:" in sender:
            sender = sender.split("whatsapp:dm:")[1]
        text = extra.get("user_message", "")
        if sender:
            process_incoming_message(
                chat_id=sender + ("" if "@" in sender else "@s.whatsapp.net"),
                sender=sender + ("" if "@" in sender else "@s.whatsapp.net"),
                text=text,
                is_bot=False,
            )
        return
    else:
        return

    if not payload:
        return

    sender   = (payload.get("from") or payload.get("senderId") or payload.get("user") or "").replace("+", "")
    chat_id  = payload.get("chatId") or payload.get("chat")

    # Resolve LIDs
    resolved_sender = resolve_lid(sender)
    if resolved_sender:
        sender = resolved_sender if "@" not in sender else f"{resolved_sender}@{sender.split('@')[1]}"
    if chat_id:
        resolved_chat = resolve_lid(chat_id)
        if resolved_chat:
            chat_id = (
                f"{resolved_chat}@s.whatsapp.net" if "@lid" in chat_id
                else f"{resolved_chat}@{chat_id.split('@')[1]}"
            )

    if not chat_id:
        return

    from_me_flag = payload.get("fromMe", False)
    if isinstance(from_me_flag, str):
        from_me_flag = from_me_flag.lower() == "true"

    # Caller can set write_inbox=false at event level to skip the inbox write
    # (used by whatsapp.py Alert Dispatcher which already wrote inbox directly)
    _write_inbox = event.get("write_inbox", True)

    process_incoming_message(
        chat_id=chat_id,
        sender=sender,
        text=payload.get("text") or payload.get("body") or payload.get("message") or "",
        is_bot=bool(from_me_flag),
        sender_name=payload.get("pushName") or payload.get("senderName") or "",
        chat_name=payload.get("chatName") or payload.get("groupName") or "",
        write_inbox=_write_inbox,
    )


if __name__ == "__main__":
    main()
