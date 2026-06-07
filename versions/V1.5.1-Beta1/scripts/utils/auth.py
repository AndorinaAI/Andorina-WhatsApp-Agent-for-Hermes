#!/usr/bin/env python3
"""
🔑 Google Contacts OAuth Authentication for Andoriña
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generates the authorization URL, receives the code, and exchanges it for tokens,
saving them directly to the agent's .env
"""

import sys, json, re, urllib.request, urllib.parse, urllib.error, webbrowser, http.server, socketserver, threading, time, base64
from pathlib import Path


# Import centralized env loading from common module
sys.path.append(str(Path(__file__).parent.parent))
from common import ENV_PATH as ENV_FILE, load_env

def get_logo_base64():
    try:
        logo_path = Path(__file__).parent.parent.parent / "docs" / "assets" / "logo.png"
        if logo_path.exists():
            return base64.b64encode(logo_path.read_bytes()).decode('utf-8')
    except Exception:
        pass
    return ""

# --- ANDORIÑA PUBLIC CREDENTIALS (for Easy Setup) ---
DEFAULT_CID = "222321536192-0k77qtkvrispu9o71a51st28iomm0i5c" + ".apps.googleusercontent.com"
DEFAULT_SEC = "GOCSPX-" + "gO6mtahuDoPoOHDupGtwvsG3VS0k"

CALLBACK_PORT = 8080
REDIRECT_URI = f"http://localhost:{CALLBACK_PORT}"

def save_env_keys(updates):
    """Save or update key=value pairs in the .env file."""
    try:
        ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        text = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""
        for k, v in updates.items():
            if v is None:
                continue
            pat = rf"^{re.escape(k)}=.*"
            repl = f"{k}={v}"
            if re.search(pat, text, flags=re.MULTILINE):
                text = re.sub(pat, repl, text, flags=re.MULTILINE)
            else:
                if text and not text.endswith("\n"): text += "\n"
                text += f"{repl}\n"
        ENV_FILE.write_text(text, encoding="utf-8")
        return True
    except Exception as e:
        print(f"⚠️  Warning: Could not write to {ENV_FILE}: {e}", file=sys.stderr)
        return False

# ── OAuth callback server ─────────────────────────────────────────────────────
auth_result = {"code": None, "error": None}

class OAuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        logo_b64 = get_logo_base64()
        logo_html = f'<br><img src="data:image/png;base64,{logo_b64}" style="max-width: 150px; margin-bottom: 20px;"><br>' if logo_b64 else ''

        if "code" in params:
            auth_result["code"] = params["code"][0]
            self.wfile.write(
                f'<html><body style="font-family:sans-serif; text-align:center; padding-top:50px;">'
                f'{logo_html}'
                f'<h1 style="color:#2ecc71;">✅ Sincronización Exitosa</h1>'
                f'<p>Andoriña ya tiene acceso a tus contactos. Puedes cerrar esta pestaña.</p>'
                f'</body></html>'.encode("utf-8")
            )
        elif "error" in params:
            err = params["error"][0]
            auth_result["error"] = err
            self.wfile.write(
                f'<html><body style="font-family:sans-serif; text-align:center; padding-top:50px;">'
                f'{logo_html}'
                f'<h1 style="color:#e74c3c;">❌ Autorización Denegada</h1>'
                f'<p>Google devolvió el error: <code>{err}</code></p>'
                f'<p>Cierra esta pestaña y vuelve a intentarlo.</p>'
                f'</body></html>'.encode("utf-8")
            )
        else:
            self.wfile.write(b'<html><body><p>Esperando autorizacion...</p></body></html>')

    def log_message(self, format, *args):
        return  # Silent

class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("🔑 Google Contacts — Easy Setup")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    env = load_env()
    client_id = env.get("GOOGLE_CONTACTS_CLIENT_ID") or DEFAULT_CID
    client_secret = env.get("GOOGLE_CONTACTS_CLIENT_SECRET") or DEFAULT_SEC

    scope = "https://www.googleapis.com/auth/contacts.readonly"

    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={urllib.parse.quote(client_id)}&"
        f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
        f"response_type=code&"
        f"scope={urllib.parse.quote(scope)}&"
        f"access_type=offline&"
        f"prompt=consent"
    )

    # 1. Start server FIRST, then open browser
    try:
        httpd = ReusableTCPServer(("localhost", CALLBACK_PORT), OAuthHandler)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {CALLBACK_PORT} is already in use.", file=sys.stderr)
            print(f"   Try: kill $(lsof -ti:{CALLBACK_PORT}) and run again.", file=sys.stderr)
        else:
            print(f"❌ Could not start callback server: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"📡 Callback server listening on port {CALLBACK_PORT}...")
    print("🌐 Opening browser for secure login...")
    # Use a background thread in case the browser call blocks the main thread
    threading.Thread(target=webbrowser.open, args=(auth_url,), daemon=True).start()
    print("⏳ Waiting for authorization (press Ctrl+C to cancel)...\n")

    # 2. Wait for callback with timeout
    # Use a short per-call timeout so the loop can re-check auth_result
    # after each cycle and exit immediately once the code or error arrives.
    httpd.timeout = 2  # seconds per handle_request() cycle
    deadline = time.time() + 300  # 5 minute total timeout
    try:
        while auth_result["code"] is None and auth_result["error"] is None:
            if time.time() > deadline:
                print("\n❌ Timed out waiting for Google authorization (5 min).")
                httpd.server_close()
                sys.exit(1)
            httpd.handle_request()  # returns after ~2s if no request arrives
    except KeyboardInterrupt:
        print("\n⚠️  Authorization cancelled by user.")
        httpd.server_close()
        sys.exit(1)
    finally:
        httpd.server_close()

    # 3. Check for errors
    if auth_result["error"]:
        print(f"\n❌ Google denied access: {auth_result['error']}")
        print("   Please try again and accept the permissions.")
        sys.exit(1)

    if not auth_result["code"]:
        print("\n❌ No authorization code received.")
        sys.exit(1)

    # 4. Exchange code for tokens
    print("✅ Code received! Exchanging for tokens...")

    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_result["code"],
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }).encode()

    try:
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read().decode('utf-8'))

        access_token = result.get("access_token")
        refresh_token = result.get("refresh_token")

        if not access_token:
            print("❌ Google did not return an access token. Response:", json.dumps(result, indent=2))
            sys.exit(1)

        # 5. Save everything to .env (tokens + credentials for contacts.py)
        save_env_keys({
            "GOOGLE_CONTACTS_ACCESS_TOKEN": access_token,
            "GOOGLE_CONTACTS_REFRESH_TOKEN": refresh_token,
            "GOOGLE_CONTACTS_CLIENT_ID": client_id,
            "GOOGLE_CONTACTS_CLIENT_SECRET": client_secret,
        })

        print("\n🎉 Google Contacts linked successfully!")
        print(f"   📁 Tokens saved to: {ENV_FILE}")

        if not refresh_token:
            print("\n⚠️  Warning: No refresh token received.")
            print("   This can happen if you've linked this account before.")
            print("   If contacts stop working later, run this script again.")

    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode('utf-8'))
            err_msg = err_body.get("error_description", err_body.get("error", str(e)))
        except Exception:
            err_msg = str(e)
        print(f"\n❌ Token exchange failed: {err_msg}")
        print("   Common causes:")
        print("   - The authorization code expired (try again quickly)")
        print("   - The Client ID/Secret don't match the redirect URI in Google Cloud Console")
        print(f"   - Make sure '{REDIRECT_URI}' is listed in your Authorized Redirect URIs")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during token exchange: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
