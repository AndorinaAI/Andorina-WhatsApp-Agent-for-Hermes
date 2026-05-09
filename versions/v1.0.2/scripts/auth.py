#!/usr/bin/env python3
"""
🔑 Google Contacts OAuth Authentication for Andoriña
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generates the authorization URL, receives the code, and exchanges it for tokens,
saving them directly to the agent's .env
"""

import sys, json, re, urllib.request, urllib.parse, urllib.error
from pathlib import Path

import os
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
ENV_FILE = HERMES_HOME / ".env"

def load_env():
    env = {}
    try:
        # Explicit UTF-8 encoding
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return env

def save_tokens(access_token, refresh_token):
    try:
        # Explicit UTF-8 encoding
        text = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""

        pat_access = r"^GOOGLE_CONTACTS_ACCESS_TOKEN=.*"
        repl_access = f"GOOGLE_CONTACTS_ACCESS_TOKEN={access_token}"
        if re.search(pat_access, text, flags=re.MULTILINE):
            text = re.sub(pat_access, repl_access, text, flags=re.MULTILINE)
        else:
            if text and not text.endswith("\n"): text += "\n"
            text += f"{repl_access}\n"

        if refresh_token:
            pat_refresh = r"^GOOGLE_CONTACTS_REFRESH_TOKEN=.*"
            repl_refresh = f"GOOGLE_CONTACTS_REFRESH_TOKEN={refresh_token}"
            if re.search(pat_refresh, text, flags=re.MULTILINE):
                text = re.sub(pat_refresh, repl_refresh, text, flags=re.MULTILINE)
            else:
                if text and not text.endswith("\n"): text += "\n"
                text += f"{repl_refresh}\n"

        ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Explicit UTF-8 encoding
        ENV_FILE.write_text(text, encoding="utf-8")
        print(f"\n✅ Tokens saved successfully to {ENV_FILE}")
    except Exception as e:
        print(f"\n❌ Error saving tokens: {e}")

def main():
    print("🔑 Google Contacts API Setup")
    print("==============================\n")

    env = load_env()
    client_id = env.get("GOOGLE_CONTACTS_CLIENT_ID")
    client_secret = env.get("GOOGLE_CONTACTS_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(f"❌ Missing GOOGLE_CONTACTS_CLIENT_ID and/or GOOGLE_CONTACTS_CLIENT_SECRET in {ENV_FILE}")
        print("Please create them in Google Cloud Console and add them to the file.")
        sys.exit(1)

    redirect_uri = "http://localhost"
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

    print("1. Open this link in your browser:")
    print(f"\n{auth_url}\n")
    print("2. Sign in with your Google account.")
    print("3. If you see a security warning, click 'Advanced' and 'Go to (unsafe)'.")
    print("4. After accepting, the browser will fail to load (Page not found). THAT IS NORMAL!")
    print("5. Copy the text from the browser address bar AFTER '?code='")

    code = input("\n👉 Paste the authorization code here: ").strip()

    if not code:
        print("Operation cancelled.")
        sys.exit(0)

    print("\n⏳ Exchanging code for tokens...")

    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }).encode()

    try:
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read().decode('utf-8'))

        access_token = result.get("access_token")
        refresh_token = result.get("refresh_token")

        if not access_token:
            print("❌ Google did not return an access_token. Please try again.")
            sys.exit(1)

        if not refresh_token:
            print("⚠️ Note: Google did not return a refresh_token.")

        save_tokens(access_token, refresh_token)
        print("\n🎉 Setup complete. You can now search contacts with contacts.py!")

    except urllib.error.HTTPError as e:
        print(f"\n❌ Google API error ({e.code}):\n{e.read().decode('utf-8')}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
