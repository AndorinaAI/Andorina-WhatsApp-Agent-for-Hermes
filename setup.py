#!/usr/bin/env python3
"""
🚀 Andoriña Setup Assistant v1.0.1 (Bugfix-1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys, os, re, subprocess, json
from pathlib import Path

ENV_FILE = Path.home() / ".hermes" / ".env"
SOUL_FILE = Path.home() / ".hermes" / "SOUL.md"
SOURCE_DIR = Path(__file__).parent
AUTH_SCRIPT = SOURCE_DIR / "scripts" / "auth.py"

def check_deps():
    print("\n📦 Checking dependencies...")
    try:
        import requests
        print("✅ Requests found.")
    except ImportError:
        print("📥 Installing requests...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)

def read_env():
    if not ENV_FILE.exists(): return {}
    env = {}
    try:
        # Explicit UTF-8
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    except: pass
    return env

def write_env(updates):
    text = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""
    for k, v in updates.items():
        pat = rf"^{k}=.*"
        repl = f"{k}={v}"
        if re.search(pat, text, flags=re.MULTILINE):
            text = re.sub(pat, repl, text, flags=re.MULTILINE)
        else:
            if text and not text.endswith("\n"): text += "\n"
            text += f"{repl}\n"
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Explicit UTF-8
    ENV_FILE.write_text(text, encoding="utf-8")

def optimize_soul():
    print("\n🧠 7. Soul Optimization")
    if input("👉 Optimize SOUL.md? [Y/n]: ").strip().lower() in ["", "y", "yes"]:
        anchoring = """
## 🕊️ Andoriña Identity Anchoring (MANDATORY)
- **WhatsApp = Andoriña:** You ONLY interact with WhatsApp through the `andorina` skill.
- **Search-First:** Always run `contacts.py search` before any send or schedule command.
- **No Native Tools:** Never use the native `cronjob` tools. Use the python scripts.
- **Smart Dates:** When scheduling, use `HH:MM`, `DD/MM HH:MM` or `DD HH:MM` (24h format).
"""
        try:
            content = SOUL_FILE.read_text(encoding="utf-8") if SOUL_FILE.exists() else "# HERMES SOUL\n"
            if "Andoriña Identity Anchoring" not in content:
                SOUL_FILE.write_text(content + anchoring, encoding="utf-8")
                print("✅ SOUL.md updated.")
        except: print("⚠️ Warning: Could not update SOUL.md")

def main():
    print("🚀 Andoriña Setup v1.0.1 (Bugfix-1)\n")
    check_deps()
    env = read_env()
    updates = {}

    print("\n🌍 1. Country Code")
    cc = input(f"👉 Country prefix (e.g. 34) [{env.get('DEFAULT_COUNTRY_CODE', '34')}]: ").strip() or env.get('DEFAULT_COUNTRY_CODE', '34')
    updates["DEFAULT_COUNTRY_CODE"] = cc.replace("+", "").lstrip("0")

    print("\n🛡️  2. Security")
    admin = input(f"👉 Admin phone (e.g. 34600112233) [{env.get('WHATSAPP_ALLOWED_USERS', '')}]: ").strip() or env.get('WHATSAPP_ALLOWED_USERS', '')
    if admin: updates["WHATSAPP_ALLOWED_USERS"] = admin.replace("+", "").replace(" ", "")

    print("\n📒 3. Google API (Optional)")
    cid = input(f"👉 CLIENT_ID [{env.get('GOOGLE_CONTACTS_CLIENT_ID', '')}]: ").strip() or env.get('GOOGLE_CONTACTS_CLIENT_ID', '')
    sec = input(f"👉 CLIENT_SECRET [{env.get('GOOGLE_CONTACTS_CLIENT_SECRET', '')}]: ").strip() or env.get('GOOGLE_CONTACTS_CLIENT_SECRET', '')
    if cid: updates["GOOGLE_CONTACTS_CLIENT_ID"] = cid
    if sec: updates["GOOGLE_CONTACTS_CLIENT_SECRET"] = sec

    write_env(updates)
    if cid and sec:
        print("\n🔑 4. Google Auth"); subprocess.run([sys.executable, str(SOURCE_DIR / "scripts" / "auth.py")])

    print("\n🔧 5. Patch Bridge"); subprocess.run([sys.executable, str(SOURCE_DIR / "scripts" / "bridge_health.py")])

    print("\n🔗 6. Deploying Skills & Permissions")
    hermes_base = Path.home() / ".hermes" / "skills" / "messaging" / "andorina"
    scripts_dir = hermes_base / "scripts"
    
    try:
        # Create directory structure
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy SKILL.md
        import shutil
        shutil.copy2(SOURCE_DIR / "SKILL.md", hermes_base / "SKILL.md")
        
        # Copy all scripts
        for script in (SOURCE_DIR / "scripts").glob("*.py"):
            shutil.copy2(script, scripts_dir / script.name)
            (scripts_dir / script.name).chmod(0o755) # Ensure executable
            
        # Register Hook
        hook = scripts_dir / "hook_inbox.py"
        subprocess.run(["hermes", "hooks", "add", "wa_inbox", "--command", f"python3 {hook}", "--event", "message_received"], capture_output=True)
        print("✅ Skills deployed and inbox hook registered.")
    except Exception as e:
        print(f"⚠️ Warning: Deployment failed: {e}")

    optimize_soul()
    print("\n🎉 Setup complete! 🕊️\n")

if __name__ == "__main__":
    main()
