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
ENV_FILE = HERMES_HOME / ".env"
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
                if "=" in line:
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
            content += f"\nGOOGLE_CONTACTS_ACCESS_TOKEN={token}\n"
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
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")

def clean_phone(raw, env):
    digits = re.sub(r"[^\d]", "", raw).lstrip("0") or ""
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
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({"ts": time.time(), "contacts": contacts}, ensure_ascii=False), encoding="utf-8")
    except: pass

def out(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))

def cmd_buscar(contacts, query, retry=True):
    q = norm(query)
    found = []
    for c in contacts:
        # Search in Name, Number or ChatId
        if q in norm(c["name"]) or q in norm(c.get("number", "")) or q in norm(c.get("chatId", "")):
            c["type"] = "Contact"
            found.append(c)
    
    groups = obtener_grupos()
    for g in groups:
        # Search in Group Name or Group Id
        if q in norm(g["name"]) or q in norm(g.get("chatId", "")):
            g["type"] = "Group"
            if not any(f["chatId"] == g["chatId"] for f in found):
                found.append(g)

    if not found and retry:
        CACHE_FILE.unlink(missing_ok=True)
        env = load_env()
        token = env.get("GOOGLE_CONTACTS_ACCESS_TOKEN", "")
        if token:
            raw = fetch_all(token, env)
            new_contacts = build_contacts(raw, env)
            save_cache(new_contacts)
            return cmd_buscar(new_contacts, query, retry=False)

    if not found:
        out({"ok": False, "message": f"No results found for '{query}'"})
    else:
        out({"ok": True, "total": len(found), "results": found[:30]})

def obtener_grupos():
    """Fetches groups from Bridge or Local Cache"""
    try:
        with urllib.request.urlopen(f"{BRIDGE_URL}/groups", timeout=3) as r:
            data = json.loads(r.read().decode('utf-8'))
            if isinstance(data, list):
                return [{"name": g.get("name", g.get("id")), "chatId": g.get("id")} for g in data]
            elif isinstance(data, dict):
                return [{"name": v.get("name", k), "chatId": k} for k, v in data.items()]
    except Exception:
        # If bridge fails, try self-healing or local fallback
        pass

    # 2. Try Local Hermes Cache (Fallback)
    f = HERMES_HOME / 'channel_directory.json'
    if not f.exists(): return []
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        groups = [c for c in d.get('platforms', {}).get('whatsapp', []) if '@g.us' in c.get('id', '')]
        return [{"name": g.get("name", g.get("id")), "chatId": g.get("id")} for g in groups]
    except: return []

def main():
    load_env() # Ensure BRIDGE is loaded
    if len(sys.argv) < 2: sys.exit(0)
    cmd = sys.argv[1].lower()
    arg = " ".join(sys.argv[2:]).strip()

    if cmd == "refresh":
        CACHE_FILE.unlink(missing_ok=True); out({"ok": True}); return

    contacts = load_cache()
    if contacts is None:
        env = load_env()
        token = env.get("GOOGLE_CONTACTS_ACCESS_TOKEN", "")
        if not token: 
            # If no Google Contacts, we still want to see groups
            if cmd in ("search", "buscar", "groups", "grupos"):
                contacts = []
            else:
                out({"ok": False, "error": "No token"}); sys.exit(1)
        else:
            raw = fetch_all(token, env)
            contacts = build_contacts(raw, env)
            save_cache(contacts)

    if cmd in ("search", "buscar"): cmd_buscar(contacts, arg)
    elif cmd in ("groups", "grupos"): out({"ok": True, "groups": obtener_grupos()})
    elif cmd == "all": out({"ok": True, "total": len(contacts), "contacts": contacts})

if __name__ == "__main__":
    main()
