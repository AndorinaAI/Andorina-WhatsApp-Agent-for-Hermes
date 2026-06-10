#!/usr/bin/env python3
"""
🚀 Andoriña — Contact & Group Discovery Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Universal search for Google Contacts and WhatsApp Groups.
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import re
import time
import unicodedata
from pathlib import Path

# Config
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))

# Import centralized env loading from common module
sys.path.append(str(Path(__file__).parent.parent))
import common
from common import ENV_PATH, load_env as _base_load_env

SCRIPTS_DIR = Path(__file__).parent.parent.absolute()
CACHE_FILE = SCRIPTS_DIR.parent / "state" / "contacts_cache.json"
NOTES_DIR = SCRIPTS_DIR.parent / "state" / "notes"
CACHE_TTL = 3600 * 24 # 24 hours

# contacts.py needs env-var overrides on top of .env
def load_env():
    env = _base_load_env()
    # Overlay with actual OS environment variables (for runtime overrides)
    for k, v in os.environ.items():
        if v: env[k] = v
    common.BRIDGE_URL = env.get("WHATSAPP_BRIDGE_URL", common.BRIDGE_URL)
    return env

def save_token(token):
    if not ENV_PATH.exists(): return
    try:
        content = ENV_PATH.read_text(encoding="utf-8")
        if "GOOGLE_CONTACTS_ACCESS_TOKEN=" in content:
            content = re.sub(r"GOOGLE_CONTACTS_ACCESS_TOKEN=.*", f"GOOGLE_CONTACTS_ACCESS_TOKEN={token}", content)
        else:
            if not content.endswith("\n"): content += "\n"
            content += f"GOOGLE_CONTACTS_ACCESS_TOKEN={token}\n"
        ENV_PATH.write_text(content, encoding="utf-8")
    except Exception: pass

def refresh_token(env):
    rt = env.get("GOOGLE_CONTACTS_REFRESH_TOKEN", "")
    if not rt:
        print('⚠️  No refresh token found. Run: python3 scripts/utils/auth.py to link Google Contacts', file=sys.stderr, flush=True)
        return ""
    data = urllib.parse.urlencode({
        "client_id":     env.get("GOOGLE_CONTACTS_CLIENT_ID", "234411781437-33o7f79beii28ehqqo7qrdl1tos7a9v3.apps.googleusercontent.com"),
        "client_secret": env.get("GOOGLE_CONTACTS_CLIENT_SECRET", "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"),
        "refresh_token": rt,
        "grant_type":    "refresh_token",
    }).encode()
    try:
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read().decode('utf-8'))
        token = result.get("access_token", "")
        if token: save_token(token)
        return token
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode('utf-8'))
            err_desc = err_body.get("error_description", err_body.get("error", str(e)))
        except Exception: err_desc = str(e)
        print(f'⚠️  Token refresh failed: {err_desc}. Run: python3 scripts/utils/auth.py to re-authenticate', file=sys.stderr, flush=True)
        return ""
    except Exception as e:
        print(f'⚠️  Token refresh failed: {e}. Run: python3 scripts/utils/auth.py to re-authenticate', file=sys.stderr, flush=True)
        return ""

def google_get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode('utf-8')), False, None
    except urllib.error.HTTPError as e:
        if e.code == 401: return None, True, None
        try:
            err_body = json.loads(e.read().decode('utf-8'))
            err_msg = err_body.get("error", {}).get("message", str(e))
        except Exception:
            err_msg = str(e)
        return None, False, err_msg
    except Exception as e:
        return None, False, str(e)

def fetch_all(token, env):
    base   = "https://people.googleapis.com/v1/people/me/connections"
    params = "personFields=names,phoneNumbers,photos&pageSize=1000"
    all_c  = []
    page   = None
    while True:
        url  = f"{base}?{params}" + (f"&pageToken={urllib.parse.quote(page)}" if page else "")
        data, expired, err = google_get(url, token)
        if expired:
            token = refresh_token(env)
            data, expired, err = google_get(url, token)
            if err: return None, err
            if not data: break
        if err: return None, err
        if not data: break
        all_c.extend(data.get("connections", []))
        page = data.get("nextPageToken")
        if not page: break
    return all_c, None

def norm(text):
    text = str(text).lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")

def clean_phone(raw, env):
    digits = re.sub(r"[^\d]", "", str(raw)).lstrip("0") or ""
    cc = env.get("DEFAULT_COUNTRY_CODE", "34")
    if 8 <= len(digits) <= 10: digits = cc + digits
    return digits

def build_contacts(raw_list, env):
    result = []
    for c in raw_list:
        names  = c.get("names", [])
        phones = c.get("phoneNumbers", [])
        photos = c.get("photos", [])
        if not names or not phones: continue
        name = names[0].get("displayName", "").strip()
        if not name: continue
        
        avatar_url = ""
        if photos:
            for p in photos:
                if not p.get("default") and p.get("metadata", {}).get("source", {}).get("type") == "CONTACT":
                    avatar_url = p.get("url", "")
                    break

        entries = []
        for p in phones:
            clean = clean_phone(p.get("value", ""), env)
            if clean:
                entries.append({"number": clean, "chatId": f"{clean}@s.whatsapp.net"})
        if entries:
            result.append({"name": name, "chatId": entries[0]["chatId"], "number": entries[0]["number"], "avatarUrl": avatar_url})
    return sorted(result, key=lambda x: norm(x["name"]))

def load_cache():
    try:
        if CACHE_FILE.exists():
            d = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if isinstance(d, dict) and time.time() - d.get("ts", 0) < CACHE_TTL:
                return d.get("contacts", [])
    except Exception: pass
    return None

def save_cache(contacts):
    try:
        state_dir = SCRIPTS_DIR.parent / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        tmp = CACHE_FILE.with_suffix('.tmp')
        tmp.write_text(json.dumps({"ts": time.time(), "contacts": contacts}, ensure_ascii=False), encoding="utf-8")
        tmp.replace(CACHE_FILE)
    except Exception: pass

def out(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))

def cmd_buscar(contacts, query, retry=True, filter_tags=None):
    q = norm(query)
    found = []
    
    for c in contacts:
        name_n = norm(c["name"])
        num_n = norm(c.get("number", ""))
        if q in name_n or name_n in q or q in num_n:
            found.append({**c, "type": "Contact"})
    
    # 2. Search Groups
    groups = obtener_grupos()
    for g in groups:
        gn = norm(g["name"])
        if q in gn or gn in q:
            if not any(f["chatId"] == g["chatId"] for f in found):
                found.append({**g, "type": "Group"})

    if not found and retry:
        env = load_env()
        token = env.get("GOOGLE_CONTACTS_ACCESS_TOKEN") or refresh_token(env)
        if token:
            raw, err = fetch_all(token, env)
            if not err and raw:
                new_contacts = build_contacts(raw, env)
                if new_contacts:
                    save_cache(new_contacts)
                    return cmd_buscar(new_contacts, query, retry=False, filter_tags=filter_tags)

    if filter_tags:
        filtered = []
        try:
            tags_file = SCRIPTS_DIR.parent / "state" / "tags.json"
            if tags_file.exists():
                all_tags = json.loads(tags_file.read_text(encoding="utf-8"))
            else:
                all_tags = {}
        except Exception:
            all_tags = {}

        for c in found:
            num = extract_number(c["chatId"])
            contact_tags = [t.lower() for t in all_tags.get(num, [])]
            if any(t in contact_tags for t in filter_tags):
                filtered.append(c)
                
        found = filtered

    if not found:
        out({"status": "OK", "error_code": "NONE", "payload": {"message": f"No results found for '{query}'"}})
    else:
        out({"status": "OK", "error_code": "NONE", "payload": {"total": len(found), "results": found[:30]}})

def obtener_grupos():
    # 1. Try Bridge Endpoint (only works on patched version)
    try:
        with urllib.request.urlopen(f"{common.BRIDGE_URL}/groups", timeout=3) as r:
            if r.getcode() == 200:
                data = json.loads(r.read().decode('utf-8'))
                # The Bridge can return a list of objects or a dict
                if isinstance(data, list):
                    # We accept both 'name' and 'subject' (Baileys uses subject)
                    return [{"name": g.get("name") or g.get("subject") or g.get("id"), "chatId": g.get("id")} for g in data]
                elif isinstance(data, dict):
                    return [{"name": v.get("name") or v.get("subject") or k, "chatId": k} for k, v in data.items()]
    except Exception as e:
        pass

    # 2. Fallback: Local channel directory (standard Hermes behavior)
    f = HERMES_HOME / 'channel_directory.json'
    if f.exists():
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            # Hermes stores groups in platforms.whatsapp
            groups = [c for c in d.get('platforms', {}).get('whatsapp', []) if '@g.us' in str(c.get('id', ''))]
            if groups:
                return [{"name": g.get("name") or g.get("id"), "chatId": g.get("id")} for g in groups]
        except Exception: pass
    
    # 3. Last Resort: Check state/inbox.json for active groups
    try:
        inbox_file = SCRIPTS_DIR.parent / "state" / "inbox.json"
        if inbox_file.exists():
            inbox = json.loads(inbox_file.read_text(encoding="utf-8"))
            active_groups = {}
            for m in inbox:
                cid = m.get("chatId", "")
                if "@g.us" in cid:
                    active_groups[cid] = cid # We don't have the name here easily
            if active_groups:
                return [{"name": cid.split("@")[0], "chatId": cid} for cid in active_groups.keys()]
    except Exception: pass

    return []

# ── Notes Management ──────────────────────────────────────────────────────────

def get_jid(raw):
    raw = raw.strip()
    if not "@" in raw:
        if "-" in raw: raw += "@g.us"
        else: raw += "@s.whatsapp.net"
    return raw

def extract_number(jid):
    return jid.split("@")[0] if "@" in jid else jid

def cmd_note_set(jid, text):
    num = extract_number(get_jid(jid))
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    note_file = NOTES_DIR / f"{num}.md"
    note_file.write_text(text, encoding="utf-8")
    out({"status": "OK", "error_code": "NONE", "payload": {"jid": num, "message": "Notes updated."}})

def cmd_note_section_set(jid, section, text):
    num = extract_number(get_jid(jid))
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    note_file = NOTES_DIR / f"{num}.md"
    
    if not note_file.exists():
        note_file.write_text(f"# {section}\n{text}\n", encoding="utf-8")
        out({"status": "OK", "error_code": "NONE", "payload": {"jid": num, "message": f"Section '{section}' created."}})
        return
        
    lines = note_file.read_text(encoding="utf-8").splitlines()
    new_lines = []
    in_target_section = False
    section_found = False
    
    header_pattern = re.compile(rf"^#+\s+{re.escape(section)}$", re.IGNORECASE)
    
    for line in lines:
        if header_pattern.match(line.strip()):
            in_target_section = True
            section_found = True
            new_lines.append(line)
            new_lines.append(text)
            continue
            
        if in_target_section:
            if re.match(r"^#+\s+", line.strip()):
                in_target_section = False
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    if not section_found:
        if new_lines and new_lines[-1].strip() != "":
            new_lines.append("")
        new_lines.append(f"# {section}")
        new_lines.append(text)
        
    note_file.write_text("\n".join(new_lines).strip() + "\n", encoding="utf-8")
    out({"status": "OK", "error_code": "NONE", "payload": {"jid": num, "message": f"Section '{section}' updated."}})

def cmd_note_add(jid, text):
    num = jid.split("@")[0]
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    note_file = NOTES_DIR / f"{num}.md"
    
    if note_file.exists():
        try:
            existing = note_file.read_text(encoding="utf-8").strip()
            # If the user sends the same note, remove it
            if text in existing:
                new_text = existing.replace(text, "").strip()
            else:
                new_text = existing + "\n\n" + text
        except Exception:
            new_text = text
    else:
        new_text = text
        
    note_file.write_text(new_text, encoding="utf-8")
    out({"status": "OK", "error_code": "NONE", "payload": {"jid": num, "message": "Note added."}})

def cmd_note_read(jid):
    num = extract_number(get_jid(jid))
    note_file = NOTES_DIR / f"{num}.md"
    if note_file.exists():
        try:
            text = note_file.read_text(encoding="utf-8").strip()
            out({"status": "OK", "error_code": "NONE", "payload": {"jid": num, "notes": text}})
            return
        except Exception:
            pass
    out({"status": "OK", "error_code": "NONE", "payload": {"jid": num, "notes": ""}})

def cmd_note_clear(jid):
    num = extract_number(get_jid(jid))
    note_file = NOTES_DIR / f"{num}.md"
    if note_file.exists():
        try:
            note_file.unlink()
            out({"status": "OK", "error_code": "NONE", "payload": {"jid": num, "message": "Notes cleared."}})
            return
        except Exception as e:
            out({"status": "ERROR", "error_code": "INTERNAL_ERROR", "payload": {"error": str(e)}})
            return
    out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "No notes found to clear."}})


def main():
    load_env()
    if len(sys.argv) < 2:
        out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "MISSING_ARGUMENTS", "usage": "contacts.py [search|groups|refresh]"}})
        sys.exit(0)
    cmd = sys.argv[1].lower()
    arg = " ".join(sys.argv[2:]).strip()

    if cmd == "search":
        filter_tags = None
        if "--filter-tags" in sys.argv:
            idx = sys.argv.index("--filter-tags")
            if idx + 1 < len(sys.argv):
                filter_tags = [t.strip().lower() for t in sys.argv[idx+1].split(",")]
                arg_parts = sys.argv[2:idx] + sys.argv[idx+2:]
                arg = " ".join(arg_parts).strip()
        
        contacts = load_cache() or []
        cmd_buscar(contacts, arg, filter_tags=filter_tags)
    elif cmd == "groups":
        out({"status": "OK", "error_code": "NONE", "payload": {"results": obtener_grupos()}})
    elif cmd == "refresh":
        env = load_env()
        token = refresh_token(env)
        if token:
            raw, err = fetch_all(token, env)
            if err:
                out({"status": "ERROR", "error_code": "INTERNAL_ERROR", "payload": {"error": err}})
            else:
                new_contacts = build_contacts(raw, env)
                groups = obtener_grupos()
                for g in groups:
                    new_contacts.append({**g, "type": "Group"})
                save_cache(new_contacts)
                out({"status": "OK", "error_code": "NONE", "payload": {"message": f"Synced {len(new_contacts)} contacts (including groups)."}})
        else:
            out({"status": "ERROR", "error_code": "PERMISSION_DENIED", "payload": {"error": "AUTH_FAILED", "message": "Could not connect to Google Contacts. The authentication tokens may be expired or invalid.", "action": "Run: python3 scripts/utils/auth.py to re-authenticate with Google."}})
    elif cmd == "note-add":
        if len(sys.argv) < 4:
            out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "MISSING_ARGUMENTS", "usage": "contacts.py note-add <JID> <text>"}})
            sys.exit(0)
        text = " ".join(sys.argv[3:])
        cmd_note_add(sys.argv[2], text)
    elif cmd == "note-set":
        if len(sys.argv) < 4:
            out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "MISSING_ARGUMENTS", "usage": "contacts.py note-set <JID> <text>"}})
            sys.exit(0)
        text = " ".join(sys.argv[3:])
        cmd_note_set(sys.argv[2], text)
    elif cmd == "note-section-set":
        if len(sys.argv) < 5:
            out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "MISSING_ARGUMENTS", "usage": "contacts.py note-section-set <JID> <Section> <text>"}})
            sys.exit(0)
        section = sys.argv[3]
        text = " ".join(sys.argv[4:])
        cmd_note_section_set(sys.argv[2], section, text)
    elif cmd == "note-read":
        if len(sys.argv) < 3:
            out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "MISSING_ARGUMENTS", "usage": "contacts.py note-read <JID>"}})
            sys.exit(0)
        cmd_note_read(sys.argv[2])
    elif cmd == "note-clear":
        if len(sys.argv) < 3:
            out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "MISSING_ARGUMENTS", "usage": "contacts.py note-clear <JID>"}})
            sys.exit(0)
        cmd_note_clear(sys.argv[2])
    else:
        out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "UNKNOWN_COMMAND", "detail": f"Command '{cmd}' not found in contacts.py."}})
        sys.exit(0)

if __name__ == "__main__":
    main()
