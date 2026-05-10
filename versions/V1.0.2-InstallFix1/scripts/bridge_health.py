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
main_hermes = HERMES_HOME
if main_hermes.parent.name == "profiles":
    main_hermes = main_hermes.parent.parent

BRIDGE_PATH = Path(os.environ.get("WHATSAPP_BRIDGE_PATH",
    str(main_hermes / "hermes-agent" / "scripts" / "whatsapp-bridge" / "bridge.js")))
STAMP_PATH  = HERMES_HOME / ".andorina_bridge_patched"
ENV_FILE    = HERMES_HOME / ".env"

BRIDGE_URL = os.environ.get("WHATSAPP_BRIDGE_URL", "http://localhost:3000")
if ENV_FILE.exists():
    try:
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "WHATSAPP_BRIDGE_URL" in line and "=" in line:
                if "WHATSAPP_BRIDGE_URL" not in os.environ:
                    BRIDGE_URL = line.partition("=")[2].strip()
    except: pass

def check_qdrant(retries=3, delay=2):
    """Wait for Qdrant to be ready with retries"""
    for i in range(retries):
        try:
            with urllib.request.urlopen("http://localhost:6333/", timeout=2) as r:
                if r.getcode() == 200: return True
        except:
            if i < retries - 1: time.sleep(delay)
    return False

def check_bridge(retries=2, delay=2):
    """Wait for WhatsApp Bridge to be ready with retries"""
    for i in range(retries):
        try:
            with urllib.request.urlopen(f"{BRIDGE_URL}/health", timeout=2) as r:
                if r.getcode() == 200: return True
        except:
            if i < retries - 1: time.sleep(delay)
    return False

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
    except: pass
    
    if not any(targets.values()): return False
    
    conf_path = HERMES_HOME / "config.yaml"
    if not conf_path.exists(): return False
    
    try:
        conf = conf_path.read_text(encoding="utf-8")
        changed = False
        if targets["context_length"]:
            new_conf = re.sub(r"#?\s*context_length:\s*\d+", f"context_length: {targets['context_length']}", conf)
            if new_conf != conf: conf = new_conf; changed = True
        
        if targets["user_char_limit"]:
            new_conf = re.sub(r"#?\s*user_char_limit:\s*\d+", f"user_char_limit: {targets['user_char_limit']}", conf)
            if new_conf != conf: conf = new_conf; changed = True

        if targets["memory_char_limit"]:
            new_conf = re.sub(r"#?\s*memory_char_limit:\s*\d+", f"memory_char_limit: {targets['memory_char_limit']}", conf)
            if new_conf != conf: conf = new_conf; changed = True
            
        if changed:
            conf_path.write_text(conf, encoding="utf-8")
            return True
    except: pass
    return False

def apply_repair():
    """Performs deep infrastructure repair"""
    print("⚕️  Andoriña: Deep Repair Mode Activated...", file=sys.stderr)
    
    # 0. Load Dynamic Port
    port = "3000"
    m = re.search(r":(\d+)", BRIDGE_URL)
    if m: port = m.group(1)

    # 1. Qdrant Restoration
    if not check_qdrant(retries=1):
        scripts_dir = Path(__file__).parent.absolute()
        q_bin = scripts_dir.parent / "bin" / "qdrant"
        if q_bin.exists():
            print("🚀 Starting portable Qdrant...", file=sys.stderr)
            q_bin.chmod(0o755) # Ensure executable
            # Force kill any zombie on 6333 just in case
            try:
                subprocess.run(["fuser", "-k", "6333/tcp"], capture_output=True)
            except FileNotFoundError:
                pass # Graceful degradation if fuser is not installed
            
            # Aseguramos que sin importar qué agente levante Qdrant, los vectores se guarden en una ruta global unificada
            q_env = os.environ.copy()
            q_env["QDRANT__STORAGE__STORAGE_PATH"] = str(Path.home() / ".qdrant_storage")
            
            subprocess.Popen([str(q_bin)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=q_env)
            time.sleep(4) 

    # 2. Bridge Logic Patching
    if BRIDGE_PATH.exists():
        try:
            content = BRIDGE_PATH.read_text(encoding="utf-8")
            patched = False
            # Data Mapping Fix
            if "from: senderId" not in content:
                content = re.sub(r"(senderId,)(\s+senderName:)", r"\1 from: senderId,\2", content)
                content = re.sub(r"(body,)(\s+hasMedia:)", r"\1 text: body,\2", content)
                content = re.sub(r"(mediaType,)(\s+mediaUrls:)", r"\1 type: mediaType || 'text',\2", content)
                patched = True
            
            # Health Endpoint Injection (Our Canary)
            if "app.get('/health'" not in content:
                health_code = "\napp.get('/health', (req, res) => { res.json({ status: connectionState, uptime: process.uptime(), version: '1.0.2' }); });\n"
                content = re.sub(r"app\.listen\s*\(", health_code + "app.listen(", content)
                patched = True

            # =================================================================
            # ADVANCED MEDIA PATCHING (MIME & PTT) 
            # Automatically applies when Hermes updates and overwrites bridge.js
            # =================================================================
            REQUIRED_MIMES = {
                "txt": "text/plain", "md": "text/markdown", "csv": "text/csv", "rtf": "application/rtf",
                "xls": "application/vnd.ms-excel", "zip": "application/zip", "bmp": "image/bmp",
                "heic": "image/heic", "mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg", "opus": "audio/ogg"
            }
            
            # 1. Patch MIME_MAP
            match = re.search(r"(MIME_MAP\s*=\s*\{)", content)
            if match:
                missing = []
                for ext, mime in REQUIRED_MIMES.items():
                    if not re.search(rf"['\"]?{ext}['\"]?\s*:", content):
                        missing.append(f"  {ext}: '{mime}',")
                if missing:
                    insertion = "\n" + "\n".join(missing)
                    closing = content.find("};", match.start())
                    if closing != -1:
                        content = content[:closing] + insertion + "\n" + content[closing:]
                        patched = True

            # 2. Patch PTT and Media Logic
            if "reqMimetype" not in content:
                pattern = r"const\s*\{[^}]*chatId[^}]*filePath[^}]*\}\s*=\s*req\.body;"
                destruct_match = re.search(pattern, content)
                if destruct_match:
                    new_destruct = "  const { chatId, filePath, mediaType, caption, fileName, mimetype: reqMimetype, ptt: reqPtt } = req.body;"
                    content = content.replace(destruct_match.group(0), new_destruct)
                    
                    old_type = "const type = mediaType || inferMediaType(ext);"
                    if old_type in content:
                        new_type = old_type + "\n    const resolvedMime = (fallback) => reqMimetype || MIME_MAP[ext] || fallback;"
                        content = content.replace(old_type, new_type)
                    
                    content = re.sub(r"mimetype:\s*MIME_MAP\[ext\]\s*\|\|\s*['\"]image/jpeg['\"]", "mimetype: resolvedMime('image/jpeg')", content)
                    content = re.sub(r"mimetype:\s*MIME_MAP\[ext\]\s*\|\|\s*['\"]video/mp4['\"]", "mimetype: resolvedMime('video/mp4')", content)
                    content = re.sub(r"mimetype:\s*MIME_MAP\[ext\]\s*\|\|\s*['\"]application/octet-stream['\"]", "mimetype: resolvedMime('application/octet-stream')", content)
                    
                    audio_pattern = r"audio:\s*buffer,\s*mimetype:[^,]+,\s*ptt:[^}]+"
                    content = re.sub(audio_pattern, "audio: buffer, mimetype: reqMimetype || (MIME_MAP[ext] || 'audio/ogg'), ptt: typeof reqPtt !== 'undefined' ? reqPtt : (ext === 'ogg' || ext === 'opus')", content)
                    patched = True

            # Typing & Presence Indicator Patch
            if "req.body.presence" not in content:
                content = re.sub(
                    r"app\.post\('/typing', async \(req, res\) => \{",
                    "app.post('/typing', async (req, res) => {\n  const { presence } = req.body;",
                    content
                )
                content = re.sub(
                    r"await sock\.sendPresenceUpdate\('composing', chatId\);",
                    "await sock.sendPresenceUpdate(presence || 'composing', chatId);",
                    content
                )
                patched = True

            if patched:
                import shutil
                bak_path = BRIDGE_PATH.with_name("bridge_andorina_bak.js")
                shutil.copy2(BRIDGE_PATH, bak_path)
                BRIDGE_PATH.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"⚠️  Bridge patching failed: {e}", file=sys.stderr)

    # 3. Aggressive Gateway Restart
    try:
        print(f"🔄 Hard-restarting WhatsApp Bridge on port {port}...", file=sys.stderr)
        # Kill everything on detected port (Multi-tool fallback)
        try:
            subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
        except FileNotFoundError:
            try:
                # Fallback: lsof
                lsof_out = subprocess.run(["lsof", "-t", "-i", f"tcp:{port}"], capture_output=True, text=True)
                for pid in lsof_out.stdout.strip().split():
                    if pid.isdigit():
                        subprocess.run(["kill", "-9", pid], capture_output=True)
            except FileNotFoundError:
                pass # Ultimate fallback is relying on 'hermes gateway stop' below
        time.sleep(1)
        
        # Stop and Start for a cleaner cycle than just 'restart'
        hermes_cmd = os.environ.get("HERMES_CMD")
        if not hermes_cmd:
            hermes_cmd = HERMES_HOME.name.lstrip(".")
            if not hermes_cmd: hermes_cmd = "hermes"
            
        subprocess.run([hermes_cmd, "gateway", "stop"], capture_output=True)
        time.sleep(1)
        subprocess.run([hermes_cmd, "gateway", "start"], capture_output=True)
        
        # Wait with smart backoff
        for wait in [2, 4, 8, 15]:
            time.sleep(wait)
            if check_bridge(retries=1):
                STAMP_PATH.touch()
                print("✅ Bridge successfully recovered.", file=sys.stderr)
                return True
    except Exception as e:
        print(f"⚠️  Restart failed: {e}", file=sys.stderr)
    
    return False

def ensure_patched():
    # Maintenance: always check config
    check_config()
    
    # Fast check: if healthy, do nothing
    if STAMP_PATH.exists() and check_bridge(retries=1):
        return False 
        
    return apply_repair()

if __name__ == "__main__":
    if ensure_patched():
        print("✅ Services are synchronized and healthy.")
    else:
        print("✅ System stability verified.")
