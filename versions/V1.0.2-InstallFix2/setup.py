#!/usr/bin/env python3
"""
      @@@@@@@@@@@@@@@@@@@@@@@ @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@ @%@@@@@@@@@@@@@@@@@@@@@@@@@@@@%+#@@@@@
      @@@@@@@@@@@@@@@@@@@@ #@=%@@@@@@@@@@@@@@@@@@@@@@@%+ +-@@@@@@@
      @@@@@@@@@@@@@@@@@@@  @ @#@@@@@@@@@@@@@@@@@@@%+  +@@-@@@@@@@@
      @@@@@@@@@@@@@@@@@@  @ +@*@@@@@@@@@@@@@@@%-   +@@@+:@@@@@@@@@
      @@@@@@@@@@@@@@@@@  #  @ @@@@@@@@@@@@#-   :#@@%-- @@@@@@@@@@@
      @@@@@@@@@@@@@@@%     =-=@@@@@@@@#-    :#@%- :@%+@@@@@@@@@@@@
      @@@@@@@@@@@@@@-     = @@@@@%      :#%+  :#@@-@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@+       @@@@:    :*+    +@%+:@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@#       :@+          +@+  *@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@      +@         :%-  +@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@%+=   :=*@%*@-             %@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@:                         -@@@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@+  +@@@+-@+          :@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@%= =@@ @@@@+       *@@@@@@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@%-:@:@@@@@@+      %@@@@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@%:+#@@@@@@@*    :*@@@@@@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@#+--+#@@@*     :=#@@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%* -=        -#@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%-    **=-    :*@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+   +@@@@@@@@@%#%@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%  :@@@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%: *@@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@+:@@@@@@@@@@@@@@@
      @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@*@@@@@@@@@@@@@@

🚀 Andoriña — Setup Assistant (v1.0.2-hotfix2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys, os, re, subprocess, json
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
ENV_FILE = HERMES_HOME / ".env"
SOUL_FILE = HERMES_HOME / "SOUL.md"
SOURCE_DIR = Path(__file__).parent

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

def setup_memory_limits(env):
    print("\n⚙️  4. Performance & Stability")
    ctx = input(f"👉 Context limit [{env.get('ANDORINA_TARGET_CONTEXT', '75000')}]: ").strip() or env.get('ANDORINA_TARGET_CONTEXT', '75000')
    umem = input(f"👉 User memory limit [{env.get('ANDORINA_TARGET_USER_MEM', '5000')}]: ").strip() or env.get('ANDORINA_TARGET_USER_MEM', '5000')
    smem = input(f"👉 System memory limit [{env.get('ANDORINA_TARGET_SYS_MEM', '5000')}]: ").strip() or env.get('ANDORINA_TARGET_SYS_MEM', '5000')
    
    updates = {
        "ANDORINA_TARGET_CONTEXT": ctx,
        "ANDORINA_TARGET_USER_MEM": umem,
        "ANDORINA_TARGET_SYS_MEM": smem
    }
    write_env(updates)
    print("✅ Limits applied.")

def main():
    print("🚀 Andoriña Setup v1.0.2-hotfix2\n")
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
    
    # Ensure bridge URL is explicitly set
    updates["WHATSAPP_BRIDGE_URL"] = "http://localhost:3000"

    write_env(updates)
    
    setup_memory_limits(env)

    print("\n🔗 5. Deploying Skills & Permissions")
    # Dynamic category detection for maximum compatibility
    skills_root = HERMES_HOME / "skills"
    category = "messaging"
    if (skills_root / "message").exists() and not (skills_root / "messaging").exists():
        category = "message"
    
    hermes_base = skills_root / category / "andorina"
    scripts_dir = hermes_base / "scripts"
    
    try:
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (hermes_base / "state").mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(SOURCE_DIR / "SKILL.md", hermes_base / "SKILL.md")
        
        for script in (SOURCE_DIR / "scripts").glob("*.py"):
            shutil.copy2(script, scripts_dir / script.name)
            (scripts_dir / script.name).chmod(0o755)
            
        hook = scripts_dir / "hook_inbox.py"
        # Ensure HERMES_HOME and HERMES_CMD are available for sub-modules
        os.environ["HERMES_HOME"] = str(HERMES_HOME)
        hermes_cmd = os.environ.get("HERMES_CMD", HERMES_HOME.name.lstrip(".") or "hermes")
        os.environ["HERMES_CMD"] = hermes_cmd
        
        # Safe Hook Injection instead of unstable CLI command
        def inject_hooks_safely(profile_path, hook_script):
            config_file = profile_path / "config.yaml"
            if not config_file.exists(): return False
            try:
                content = config_file.read_text(encoding="utf-8")
                hook_cmd = f"python3 '{hook_script}'"
                if hook_cmd in content: return True
                
                lines = content.splitlines()
                hooks_idx = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith("hooks:"):
                        hooks_idx = i
                        break
                
                new_hook = [
                    f"  - event: message_received",
                    f'    command: "{hook_cmd}"',
                    f"  - event: whatsapp:message",
                    f'    command: "{hook_cmd}"'
                ]
                
                if hooks_idx == -1:
                    if lines and lines[-1].strip(): lines.append("")
                    lines.append("hooks:")
                    lines.extend(new_hook)
                else:
                    if "[]" in lines[hooks_idx]: lines[hooks_idx] = "hooks:"
                    for j, h_line in enumerate(new_hook):
                        lines.insert(hooks_idx + 1 + j, h_line)
                
                config_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return True
            except: return False

        if inject_hooks_safely(HERMES_HOME, hook):
            print("✅ Skills deployed and inbox hooks registered (Safe Inject).")
        else:
            print("⚠️ Warning: Skills deployed but hooks could not be registered automatically.")
    except Exception as e:
        print(f"⚠️ Warning: Deployment failed: {e}")

    # Now that scripts are deployed, run the portable components
    try:
        print("\n🧠 6. Memory Engine (Qdrant)")
        do_qdrant = input("👉 Do you want to setup/check the Qdrant memory engine? (y/n) [y]: ").lower().strip() or "y"
        if do_qdrant in ("y", "s"):
            qdrant_setup = scripts_dir / "setup_portable.py"
            if qdrant_setup.exists():
                subprocess.run([sys.executable, str(qdrant_setup)])
    except Exception as e:
        print(f"⚠️  Note: Qdrant setup skipped or failed: {e}")

    try:
        print("\n🖥️  7. Autostart Engine")
        do_auto = input("👉 Do you want to enable automatic startup for Hermes on login? (y/n) [y]: ").lower().strip() or "y"
        if do_auto in ("y", "s"):
            autostart_setup = scripts_dir / "setup_autostart.py"
            if autostart_setup.exists():
                subprocess.run([sys.executable, str(autostart_setup)])
    except Exception as e:
        print(f"⚠️  Note: Autostart setup skipped or failed: {e}")

    try:
        print("\n🔧 8. Patch Bridge")
        do_patch = input("👉 Do you want to apply the compatibility patch and restart the bridge now? (y/n) [y]: ").lower().strip() or "y"
        if do_patch in ("y", "s"):
            health_script = scripts_dir / "bridge_health.py"
            if health_script.exists():
                subprocess.run([sys.executable, str(health_script)])
    except Exception as e:
        print(f"⚠️  Note: Bridge patching skipped or failed: {e}")

    try:
        optimize_soul()
    except: pass
    
    print("\n" + "━"*50)
    print("🎉 ANDORIÑA SETUP COMPLETE! 🕊️")
    print("   Your assistant is ready to fly.")
    print("━"*50 + "\n")

if __name__ == "__main__":
    main()
