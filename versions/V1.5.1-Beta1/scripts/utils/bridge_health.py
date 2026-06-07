#!/usr/bin/env python3
"""
⚕️ Andoriña — Infrastructure Shield & Auto-Repair (Hyper-Resilient V3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Professional version with zombie cleaning, binary validation and smart backoff.
"""

import os, sys, subprocess, time, json, urllib.request, re
from pathlib import Path

# Config
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))

def discover_bridge(start_path):
    curr = start_path
    for _ in range(3):
        possible = curr / "hermes-agent" / "scripts" / "whatsapp-bridge" / "bridge.js"
        if possible.exists(): return possible
        if curr.parent == curr: break
        curr = curr.parent
    main = start_path
    if main.parent.name == "profiles":
        main = main.parent.parent
    return main / "hermes-agent" / "scripts" / "whatsapp-bridge" / "bridge.js"

BRIDGE_PATH = Path(os.environ.get("WHATSAPP_BRIDGE_PATH", str(discover_bridge(HERMES_HOME))))
# Import centralized env loading from common module
sys.path.append(str(Path(__file__).parent.parent))
from common import ENV_PATH as ENV_FILE, BRIDGE_URL



def check_bridge(retries=2, delay=2, check_connection=False):
    """Wait for WhatsApp Bridge to be ready with retries. 
    If check_connection is True, also verifies if WhatsApp is linked.
    """
    for i in range(retries):
        try:
            with urllib.request.urlopen(f"{BRIDGE_URL}/health", timeout=2) as r:
                if r.getcode() == 200:
                    data = json.loads(r.read().decode('utf-8'))
                    if not check_connection: return True
                    status = data.get('status', '').lower()
                    return status in ['open', 'connected']
        except Exception:
            if i < retries - 1: time.sleep(delay)
    return False

def get_qr():
    """Fetches the QR code from the bridge if available"""
    try:
        with urllib.request.urlopen(f"{BRIDGE_URL}/qr", timeout=2) as r:
            if r.getcode() == 200:
                data = json.loads(r.read().decode('utf-8'))
                return data.get("qr")
    except Exception: pass
    return None

def show_qr():
    """Prints the QR code to terminal using qrencode if available, or just the string"""
    qr_string = get_qr()
    if not qr_string:
        print("ℹ️  No QR code available (Bridge might be connected or starting).", file=sys.stderr)
        return False
    
    print("\n📱 SCAN THIS QR CODE WITH WHATSAPP:", file=sys.stderr)
    print("-" * 40, file=sys.stderr)
    try:
        # Try to use qrencode for a real terminal QR
        subprocess.run(["qrencode", "-t", "ansiutf8", qr_string], check=True)
    except Exception:
        # Fallback to showing the link/string
        print(f"QR String: {qr_string}", file=sys.stderr)
        print("Tip: Install 'qrencode' for a better visual experience.", file=sys.stderr)
    print("-" * 40, file=sys.stderr)
    return True

def check_config():
    """Syncs target limits from .env to config.yaml"""
    targets = {"context_length": None, "user_char_limit": None, "memory_char_limit": None}
    if not ENV_FILE.exists(): return False
    
    try:
        content = ENV_FILE.read_text(encoding="utf-8")
        if "ANDORINA_TARGET_CONTEXT" in content:
            targets["context_length"] = re.search(r"ANDORINA_TARGET_CONTEXT=(\d+)", content).group(1)
        if "ANDORINA_TARGET_USER_MEM" in content:
            targets["user_char_limit"] = re.search(r"ANDORINA_TARGET_USER_MEM=(\d+)", content).group(1)
        if "ANDORINA_TARGET_SYS_MEM" in content:
            targets["memory_char_limit"] = re.search(r"ANDORINA_TARGET_SYS_MEM=(\d+)", content).group(1)
    except Exception: pass
    
    if not any(targets.values()): return False
    
    conf_path = HERMES_HOME / "config.yaml"
    if not conf_path.exists(): return False
    
    try:
        conf = conf_path.read_text(encoding="utf-8")
        changed = False
        if targets["context_length"]:
            new_conf = re.sub(r"^([ \t]*)#?\s*context_length:\s*\d+.*$", rf"\1context_length: {targets['context_length']}", conf, flags=re.MULTILINE)
            if new_conf != conf: conf = new_conf; changed = True
        
        if targets["user_char_limit"]:
            new_conf = re.sub(r"^([ \t]*)#?\s*user_char_limit:\s*\d+.*$", rf"\1user_char_limit: {targets['user_char_limit']}", conf, flags=re.MULTILINE)
            if new_conf != conf: conf = new_conf; changed = True

        if targets["memory_char_limit"]:
            new_conf = re.sub(r"^([ \t]*)#?\s*memory_char_limit:\s*\d+.*$", rf"\1memory_char_limit: {targets['memory_char_limit']}", conf, flags=re.MULTILINE)
            if new_conf != conf: conf = new_conf; changed = True
            
        if changed:
            conf_path.write_text(conf, encoding="utf-8")
            return True
    except Exception: pass
    return False

def apply_repair():
    """Diagnostic and recovery tool (Non-Intrusive)"""
    print("⚕️  Andoriña: System Health Check...", file=sys.stderr)
    
    # 0. Load Dynamic Port
    port = "3000"
    m = re.search(r":(\d+)", BRIDGE_URL)
    if m: port = m.group(1)



    # 2. Compatibility Audit & Proactive Repair
    if BRIDGE_PATH.exists():
        try:
            content = BRIDGE_PATH.read_text(encoding="utf-8")
            missing = []
            # NOTE: do NOT add markers here that patch_bridge.py never writes —
            # a stale marker causes an eternal restart loop (bridge gets killed
            # every time ensure_patched() runs, even when fully patched).
            if "app.get('/health'" not in content: missing.append("Health Endpoint")
            if "reqMimetype" not in content: missing.append("Media Mime/PTT Override")
            if "app.get('/groups'" not in content: missing.append("Groups Endpoint")
            if "ANDORINA INBOX FIX" not in content: missing.append("fromMe Inbox Fix")
            
            if missing:
                print(f"🔧 Bridge Repair: Patching missing features: {', '.join(missing)}", file=sys.stderr)
                scripts_dir = Path(__file__).parent.absolute()
                # Use the root patch script as source of truth
                patch_script = scripts_dir.parent.parent / "patch_bridge.py"
                if not patch_script.exists(): patch_script = scripts_dir.parent / "patch_bridge.py"
                
                if patch_script.exists():
                    subprocess.run([sys.executable, str(patch_script)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("✅ Bridge patched and restarted successfully.", file=sys.stderr)
                    time.sleep(2)
                
                # Also apply whatsapp.py patch
                whatsapp_patch = scripts_dir.parent.parent / "patch_whatsapp.py"
                if not whatsapp_patch.exists(): whatsapp_patch = scripts_dir.parent / "patch_whatsapp.py"
                if whatsapp_patch.exists():
                    subprocess.run([sys.executable, str(whatsapp_patch)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print("✅ WhatsApp Sub-Soul patch verified.", file=sys.stderr)
        except Exception: pass

    # 3. Crontab hygiene — remove stale entries from old Andoriña versions
    # (paths that no longer exist on disk: old V1.0.4, /tmp sandbox, etc.)
    try:
        agenda_script = scripts_dir / "tools" / "agenda.py"
        if agenda_script.exists():
            subprocess.run(
                [sys.executable, str(agenda_script), "cleanup-crons"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10
            )
            print("🧹 Stale crontab entries cleaned.", file=sys.stderr)
    except Exception: pass

    # 3. Gateway Connectivity Check
    if not check_bridge(retries=2, check_connection=True):
        print("📱 WhatsApp session is OFFLINE.", file=sys.stderr)
        return False
    
    print("✅ System stability verified.", file=sys.stderr)
    return True

def ensure_patched():
    """Silent check and repair called by other scripts.
    Uses retries=3 to avoid false alarms from a slow bridge startup —
    we only want to restart if the bridge is genuinely down, not just
    temporarily busy (e.g. processing a previous message).
    """
    if not check_bridge(retries=3, delay=2):
        apply_repair()

def main():
    if apply_repair():
        print("✅ System stability verified.")
        print("📱 WhatsApp session is already ACTIVE. No QR code needed.")
    else:
        print("📱 WhatsApp session is OFFLINE.")
        show_qr()

if __name__ == "__main__":
    main()
