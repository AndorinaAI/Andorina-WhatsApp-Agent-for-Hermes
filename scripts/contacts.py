#!/usr/bin/env python3
"""
📒 Google Contacts for Andoriña
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys, os, json, re, unicodedata, urllib.request, urllib.parse, urllib.error, time
from pathlib import Path

ENV_FILE   = Path.home() / ".hermes" / ".env"
CACHE_FILE = Path.home() / ".hermes" / "skills" / "messaging" / "andorina" / "state" / "contacts_cache.json"
CACHE_TTL  = 3600
BRIDGE     = "http://localhost:3000"

def load_env():
    env = {}
    try:
        # Explicit UTF-8
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return env

def save_token(token):
    try:
        # Explicit UTF-8
        text = ENV_FILE.read_text(encoding="utf-8")
        pat  = r"GOOGLE_CONTACTS_ACCESS_TOKEN=.*"
        repl = f"GOOGLE_CONTACTS_ACCESS_TOKEN={token}"
        ENV_FILE.write_text(re.sub(pat, repl, text) if re.search(pat, text) else text + f"\n{repl}\n", encoding="utf-8")
    except Exception as e:
        print(f"[warning] Could not save token: {e}", file=sys.stderr)

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
    except Exception as e:
        print(f"Error refreshing token: {e}", file=sys.stderr)
        return ""

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
            # Explicit UTF-8
            d = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if time.time() - d.get("ts", 0) < CACHE_TTL:
                return d["contacts"]
    except: pass
    return None

def save_cache(contacts):
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Explicit UTF-8
        CACHE_FILE.write_text(json.dumps({"ts": time.time(), "contacts": contacts}, ensure_ascii=False), encoding="utf-8")
    except: pass

def out(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))

def cmd_buscar(contacts, query):
    q = norm(query)
    found = []
    for c in contacts:
        if q in norm(c["name"]): found.append(c)
    if not found:
        out({"ok": False, "message": "No results.", "hint": "Try fewer letters or omit accents. / Prueba con menos letras o quita las tildes."})
    else:
        out({"ok": True, "total": len(found), "results": found[:30]})

def obtener_grupos():
    try:
        # Check bridge status
        with urllib.request.urlopen(f"{BRIDGE}/status", timeout=1) as r: pass
    except: return []

    f = Path.home() / '.hermes/channel_directory.json'
    if not f.exists(): return []
    try:
        # Explicit UTF-8
        d = json.loads(f.read_text(encoding="utf-8"))
        groups = [c for c in d.get('platforms', {}).get('whatsapp', []) if '@g.us' in c.get('id', '')]
        return [{"name": g.get("name", g.get("id")), "chatId": g.get("id")} for g in groups]
    except: return []

def main():
    if len(sys.argv) < 2: sys.exit(0)
    cmd = sys.argv[1].lower()
    arg = " ".join(sys.argv[2:]).strip()

    if cmd == "refresh":
        CACHE_FILE.unlink(missing_ok=True); out({"ok": True}); return

    contacts = load_cache()
    if contacts is None:
        env = load_env()
        token = env.get("GOOGLE_CONTACTS_ACCESS_TOKEN", "")
        if not token: out({"ok": False, "error": "No token"}); sys.exit(1)
        raw = fetch_all(token, env)
        contacts = build_contacts(raw, env)
        save_cache(contacts)

    if cmd in ("search", "buscar"): cmd_buscar(contacts, arg)
    elif cmd in ("groups", "grupos"): out({"ok": True, "groups": obtener_grupos()})
    elif cmd == "all": out({"ok": True, "total": len(contacts), "contacts": contacts})
    elif cmd == "count": out({"ok": True, "total": len(contacts)})

if __name__ == "__main__":
    main()
