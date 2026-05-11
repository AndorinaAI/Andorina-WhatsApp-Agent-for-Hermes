#!/usr/bin/env python3
"""
🔑 Google Contacts OAuth Authentication for Andoriña
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generates the authorization URL, receives the code, and exchanges it for tokens,
saving them directly to the agent's .env
"""

import sys, json, re, urllib.request, urllib.parse, urllib.error, webbrowser, http.server, socketserver, threading
from pathlib import Path

import os
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))

def get_env_path(profile_path):
    skills_root = profile_path / "skills"
    category = "messaging"
    if (skills_root / "message").exists() and not (skills_root / "messaging").exists():
        category = "message"
    return skills_root / category / "andorina" / ".env"

ENV_FILE = get_env_path(HERMES_HOME)

# --- ANDORIÑA PUBLIC CREDENTIALS (for Easy Setup) ---
DEFAULT_CID = "945115201402-b06it94lslqdqsh0e6761v75v6iun547.apps.googleusercontent.com"
DEFAULT_SEC = "GOCSPX-uLqO8Y_X_F79u_qRjE9_j_w_X_q" # Placeholder for demo, normally would be the project's secret

def load_env():
    env = {}
    try:
        if ENV_FILE.exists():
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
    except: pass
    return env

def save_tokens(access_token, refresh_token):
    try:
        text = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""
        updates = {
            "GOOGLE_CONTACTS_ACCESS_TOKEN": access_token,
            "GOOGLE_CONTACTS_REFRESH_TOKEN": refresh_token
        }
        for k, v in updates.items():
            if v:
                pat = rf"^{k}=.*"
                repl = f"{k}={v}"
                if re.search(pat, text, flags=re.MULTILINE):
                    text = re.sub(pat, repl, text, flags=re.MULTILINE)
                else:
                    if text and not text.endswith("\n"): text += "\n"
                    text += f"{repl}\n"
        
        ENV_FILE.write_text(text, encoding="utf-8")
        return True
    except: return False

# Temporary server to catch the code
auth_code = None
class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        if "code" in params:
            auth_code = params["code"][0]
            self.wfile.write(b"<html><body style='font-family:sans-serif; text-align:center; padding-top:50px;'>")
            self.wfile.write(b"<h1 style='color:#2ecc71;'>\xe2\x9c\x85 Sincronizaci\xc3\xb3n Exitosa</h1>")
            self.wfile.write(b"<p>Andori\xc3\xb1a ya tiene acceso. Puedes cerrar esta pesta\xc3\xb1a y volver a la terminal.</p>")
            self.wfile.write(b"</body></html>")
        else:
            self.wfile.write(b"Error: No code found")
    def log_message(self, format, *args): return # Silent

def main():
    print("🔑 Google Contacts — Easy Setup")
    print("==============================\n")

    env = load_env()
    client_id = env.get("GOOGLE_CONTACTS_CLIENT_ID") or DEFAULT_CID
    client_secret = env.get("GOOGLE_CONTACTS_CLIENT_SECRET") or DEFAULT_SEC

    redirect_uri = "http://localhost:8080"
    scope = "https://www.googleapis.com/auth/contacts.readonly"

    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"access_type=offline&"
        f"prompt=consent"
    )

    print("🌐 Opening browser for secure login...")
    webbrowser.open(auth_url)

    print("⏳ Waiting for authorization...")
    with socketserver.TCPServer(("", 8080), OAuthHandler) as httpd:
        while auth_code is None:
            httpd.handle_request()

    print("\n✅ Code received! Exchanging for tokens...")
    
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }).encode()

    try:
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read().decode('utf-8'))

        save_tokens(result.get("access_token"), result.get("refresh_token"))
        print("\n🎉 Google Contacts linked successfully!")

    except Exception as e:
        print(f"\n❌ Error during token exchange: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
