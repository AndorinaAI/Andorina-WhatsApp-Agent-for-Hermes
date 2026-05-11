#!/usr/bin/env python3
"""
🚀 Andoriña — Contact & Group Discovery Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Universal search for Google Contacts and WhatsApp Groups.
"""

import sys, os, json, urllib.request, urllib.parse, re, time, hashlib, unicodedata
from pathlib import Path

# Config
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
def get_env_path(profile_path):
    skills_root = profile_path / "skills"
    category = "messaging"
    if (skills_root / "message").exists() and not (skills_root / "messaging").exists():
        category = "message"
    return skills_root / category / "andorina" / ".env"

ENV_FILE = get_env_path(HERMES_HOME)
SCRIPTS_DIR = Path(__file__).parent.absolute()
CACHE_FILE = SCRIPTS_DIR.parent / "state" / "contacts_cache.json"
CACHE_TTL = 3600 * 24 # 24 hours
BRIDGE_URL = "http://localhost:3000"

# Load dynamic configuration
def load_env():
    env = {}
    if ENV_FILE.exists():
        try:
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
        except: pass
    
    for k, v in os.environ.items():
        if v: env[k] = v
        
    global BRIDGE_URL
    BRIDGE_URL = env.get("WHATSAPP_BRIDGE_URL", BRIDGE_URL)
    return env

def save_token(token):
    if not ENV_FILE.exists(): return
    try:
        content = ENV_FILE.read_text(encoding="utf-8")
        if "GOOGLE_CONTACTS_ACCESS_TOKEN=" in content:
            content = re.sub(r"GOOGLE_CONTACTS_ACCESS_TOKEN=.*", f"GOOGLE_CONTACTS_ACCESS_TOKEN={token}", content)
        else:
            if not content.endswith("\n"): content += "\n"
            content += f"GOOGLE_CONTACTS_ACCESS_TOKEN={token}\n"
        ENV_FILE.write_text(content, encoding="utf-8")
    except: pass

def refresh_token(env):
    data = urllib.parse.urlencode({
        "client_id":     env.get("GOOGLE_CONTACTS_CLIENT_ID", ""),
        "client_secret": env.get("GOOGLE_CONTACTS_CLIENT_SECRET", ""),
        "refresh_token": env.get("GOOGLE_CONTACTS_REFRESH_TOKEN", ""),
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
    except: return ""

def google_get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode('utf-8')), False
    except urllib.error.HTTPError as e:
        if e.code == 401: return None, True
        return None, False
    except: return None, False

def fetch_all(token, env):
    base   = "https://people.googleapis.com/v1/people/me/connections"
    params = "personFields=names,phoneNumbers&pageSize=1000"
    all_c  = []
    page   = None
    while True:
        url  = f"{base}?{params}" + (f"&pageToken={urllib.parse.quote(page)}" if page else "")
        data, expired = google_get(url, token)
        if expired:
            token = refresh_token(env)
            data, expired = google_get(url, token)
            if not data: break
        if not data: break
        all_c.extend(data.get("connections", []))
        page = data.get("nextPageToken")
        if not page: break
    return all_c

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
        if not names or not phones: continue
        name = names[0].get("displayName", "").strip()
        if not name: continue
        entries = []
        for p in phones:
            clean = clean_phone(p.get("value", ""), env)
            if clean:
                entries.append({"number": clean, "chatId": f"{clean}@s.whatsapp.net"})
        if entries:
            result.append({"name": name, "chatId": entries[0]["chatId"], "number": entries[0]["number"]})
    return sorted(result, key=lambda x: norm(x["name"]))

def load_cache():
    try:
        if CACHE_FILE.exists():
            d = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if time.time() - d.get("ts", 0) < CACHE_TTL:
                return d["contacts"]
    except: pass
    return None

def save_cache(contacts):
    try:
        state_dir = SCRIPTS_DIR.parent / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({"ts": time.time(), "contacts": contacts}, ensure_ascii=False), encoding="utf-8")
    except: pass

def out(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))

def cmd_buscar(contacts, query, retry=True):
    q = norm(query)
    found = []
    
    for c in contacts:
        name_n = norm(c["name"])
        num_n = norm(c.get("number", ""))
        if q in name_n or name_n in q or q in num_n:
            c["type"] = "Contact"
            found.append(c)
    
    # 2. Search Groups
    groups = obtener_grupos()
    for g in groups:
        gn = norm(g["name"])
        if q in gn or gn in q:
            g["type"] = "Group"
            if not any(f["chatId"] == g["chatId"] for f in found):
                found.append(g)

    if not found and retry:
        env = load_env()
        token = env.get("GOOGLE_CONTACTS_ACCESS_TOKEN") or refresh_token(env)
        if token:
            raw = fetch_all(token, env)
            new_contacts = build_contacts(raw, env)
            if new_contacts:
                save_cache(new_contacts)
                return cmd_buscar(new_contacts, query, retry=False)

    if not found:
        out({"ok": False, "message": f"No results found for '{query}'"})
    else:
        out({"ok": True, "total": len(found), "results": found[:30]})

def obtener_grupos():
    # 1. Try Bridge Endpoint (only works on patched version)
    try:
        with urllib.request.urlopen(f"{BRIDGE_URL}/groups", timeout=3) as r:
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
        except: pass
    
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
    except: pass

    return []

def main():
    load_env()
    if len(sys.argv) < 2: sys.exit(0)
    cmd = sys.argv[1].lower()
    arg = " ".join(sys.argv[2:]).strip()

    if cmd == "search":
        contacts = load_cache() or []
        cmd_buscar(contacts, arg)
    elif cmd == "groups":
        out({"ok": True, "results": obtener_grupos()})
    elif cmd == "refresh":
        env = load_env()
        token = refresh_token(env)
        if token:
            raw = fetch_all(token, env)
            new_contacts = build_contacts(raw, env)
            save_cache(new_contacts)
            out({"ok": True, "message": f"Synced {len(new_contacts)} contacts."})
        else:
            out({"ok": False, "message": "Failed to refresh token."})

if __name__ == "__main__":
    main()
