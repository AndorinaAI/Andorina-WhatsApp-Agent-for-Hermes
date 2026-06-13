#!/usr/bin/env python3
import sys, os, platform, urllib.request, subprocess, threading, re, time
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
BIN_DIR = SCRIPT_DIR.parent / "bin"
CLOUDFLARED = BIN_DIR / ("cloudflared.exe" if platform.system() == "Windows" else "cloudflared")
LOG_FILE = PROJECT_DIR / "state" / "tunnel.log"

BIN_DIR.mkdir(parents=True, exist_ok=True)
(PROJECT_DIR / "state").mkdir(parents=True, exist_ok=True)

# Process tracking
active_process = None
active_url = None
monitor_thread = None

def download_cloudflared():
    if CLOUDFLARED.exists(): return True
    
    print("Descargando cloudflared...")
    sys_name = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map to cloudflared arch
    arch = "amd64"
    if "arm" in machine or "aarch" in machine:
        if "64" in machine: arch = "arm64"
        else: arch = "arm"
    
    if sys_name == "linux":
        url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-{arch}"
    elif sys_name == "darwin":
        url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-{arch}"
    elif sys_name == "windows":
        url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-{arch}.exe"
    else:
        print(f"Sistema no soportado: {sys_name}")
        return False
        
    try:
        urllib.request.urlretrieve(url, CLOUDFLARED)
        if sys_name != "windows":
            os.chmod(CLOUDFLARED, 0o755)
        return True
    except Exception as e:
        print(f"Error descargando cloudflared: {e}")
        return False

def _notify_users(msg_body):
    try:
        import json
        users = set()
        
        # Owner & Mode
        env_path = PROJECT_DIR / ".env"
        mode = "all_panel_users"
        owner = None
        if env_path.exists():
            text = env_path.read_text(errors="ignore")
            
            # Extract country code just in case
            cc = "34"
            match_cc = re.search(r"^DEFAULT_COUNTRY_CODE=(.+)$", text, re.MULTILINE)
            if match_cc: cc = match_cc.group(1).strip().replace("+", "")
            
            match_owner = re.search(r"^(?:OWNER_NUMBER|ADMIN_PHONE)=(.+)$", text, re.MULTILINE)
            if match_owner:
                owner = match_owner.group(1).strip().replace("+", "")
                if not owner.startswith(cc) and len(owner) < 11:
                    owner = cc + owner
                if not owner.endswith("@s.whatsapp.net"): owner += "@s.whatsapp.net"
            
            match_mode = re.search(r"^TUNNEL_NOTIFY_MODE=(.+)$", text, re.MULTILINE)
            if match_mode:
                mode = match_mode.group(1).strip().lower()
                
        if mode == "off": return
        if owner: users.add(owner)
                
        # Users with panel access
        if mode == "all_panel_users":
            rules_path = PROJECT_DIR / "state" / "guard_rules.json"
            if rules_path.exists():
                rules = json.loads(rules_path.read_text(encoding="utf-8"))
                for jid, data in rules.get("jids", {}).items():
                    role = data.get("role", "")
                    has_access = "password_hash" in data or role in ["owner", "manager", "admin"]
                    if has_access:
                        clean_jid = jid.strip()
                        if clean_jid:
                            if not clean_jid.endswith("@s.whatsapp.net") and not clean_jid.endswith("@g.us"):
                                clean_jid += "@s.whatsapp.net"
                            users.add(clean_jid)
                        
        msg = f"🌐 *Panel Andoriña*\n{msg_body}"
        for jid in users:
            subprocess.Popen([sys.executable, str(PROJECT_DIR / "scripts" / "transport" / "send.py"), "message", jid, msg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
    except Exception as e:
        print(f"NOTIFY ERROR: {e}", file=sys.stderr)

def _notify_users_url(url):
    _notify_users(f"🇪🇸 La URL del panel temporal ha cambiado. Nuevo acceso:\n🇬🇧 The temporary panel URL has changed. New access:\n\n🔗 {url}")

def _notify_stop():
    _notify_users("🇪🇸 El acceso web ha sido *detenido* manualmente.\n🇬🇧 Web access has been manually *stopped*.")

def _monitor_output(proc, is_quick):
    global active_url
    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
    
    with open(LOG_FILE, "w") as f:
        for line in iter(proc.stdout.readline, ''):
            print(line, end='', file=f)
            f.flush()
            if is_quick and not active_url:
                match = url_pattern.search(line)
                if match:
                    active_url = match.group(0)

def start_tunnel(port=8888, token=None):
    global active_url, monitor_thread
    
    if active_process and active_process.poll() is None:
        return True, "El túnel ya está corriendo"
        
    if not download_cloudflared():
        return False, "No se pudo descargar cloudflared"
        
    active_url = None
    cmd = []
    is_quick = False
    
    if token:
        cmd = [str(CLOUDFLARED), "tunnel", "run", "--token", token]
    else:
        cmd = [str(CLOUDFLARED), "tunnel", "--url", f"http://localhost:{port}"]
        is_quick = True
        
    try:
        def run_forever():
            global active_process, active_url
            while True:
                active_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                
                # Start reading stdout to find the URL
                url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
                with open(LOG_FILE, "a") as f:
                    f.write("\n--- Starting Tunnel ---\n")
                    for line in iter(active_process.stdout.readline, ''):
                        print(line, end='', file=f)
                        f.flush()
                        if is_quick and not active_url:
                            match = url_pattern.search(line)
                            if match:
                                active_url = match.group(0)
                                _notify_users_url(active_url)
                
                active_process.wait()
                if active_process is None: # Means stop_tunnel was called
                    break
                # If we get here, it crashed or closed. Wait and restart.
                time.sleep(2)
                active_url = None # Reset URL so it can be captured again if quick tunnel
                
        monitor_thread = threading.Thread(target=run_forever, daemon=True)
        monitor_thread.start()
        
        # Wait a bit to catch the URL if quick
        if is_quick:
            for _ in range(20):
                if active_url: break
                time.sleep(0.5)
            if not active_url:
                return True, "Iniciando (esperando URL)..."
                
        return True, active_url or "Custom Tunnel Started"
        
    except Exception as e:
        return False, str(e)

def stop_tunnel():
    global active_process, active_url
    proc = active_process
    active_process = None # Signal loop to break
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except:
            proc.kill()
    if active_url is not None:
        _notify_stop()
    active_url = None
    return True

def get_status():
    if active_process and active_process.poll() is None:
        return {"active": True, "url": active_url}
    return {"active": False, "url": None}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["start", "stop", "status"])
    parser.add_argument("--token", help="Tunnel token")
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()
    
    if args.cmd == "start":
        ok, msg = start_tunnel(args.port, args.token)
        print(f"OK: {ok} - {msg}")
        if ok:
            try:
                while active_process and active_process.poll() is None:
                    time.sleep(1)
            except KeyboardInterrupt:
                stop_tunnel()
    elif args.cmd == "stop":
        stop_tunnel()
        print("Detenido")
    elif args.cmd == "status":
        print(get_status())
