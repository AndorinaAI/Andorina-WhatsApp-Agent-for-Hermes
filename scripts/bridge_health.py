#!/usr/bin/env python3
import sys, re, subprocess
from pathlib import Path

# Paths
BRIDGE_PATH = Path.home() / ".hermes" / "hermes-agent" / "scripts" / "whatsapp-bridge" / "bridge.js"
STAMP_FILE  = Path.home() / ".hermes" / ".andorina_bridge_patched"

REQUIRED_MIMES = {
    "txt": "text/plain", "md": "text/markdown", "csv": "text/csv", "rtf": "application/rtf",
    "xls": "application/vnd.ms-excel", "zip": "application/zip", "bmp": "image/bmp",
    "heic": "image/heic", "mp3": "audio/mpeg", "wav": "audio/wav"
}

def is_patched():
    """Checks if the bridge is already patched without reading the whole file if possible."""
    if not BRIDGE_PATH.exists(): return True # Nothing to patch yet
    
    # Fast check: if stamp exists and bridge hasn't changed since then
    if STAMP_FILE.exists() and STAMP_FILE.stat().st_mtime > BRIDGE_PATH.stat().st_mtime:
        return True
    
    # Deep check
    content = BRIDGE_PATH.read_text(encoding="utf-8")
    return "resolvedMime" in content

def apply_patch():
    """Applies the professional regex-based patch to bridge.js"""
    if not BRIDGE_PATH.exists(): return False
    
    content = BRIDGE_PATH.read_text(encoding="utf-8")
    
    # 1. Patch MIME_MAP
    pattern_mime = r"(MIME_MAP\s*=\s*\{)"
    match_mime = re.search(pattern_mime, content)
    if match_mime:
        missing = []
        for ext, mime in REQUIRED_MIMES.items():
            if not re.search(rf"['\"]?{ext}['\"]?\s*:", content):
                missing.append(f"  {ext}: '{mime}',")
        if missing:
            insertion = "\n" + "\n".join(missing)
            closing = content.find("};", match_mime.start())
            if closing != -1:
                content = content[:closing] + insertion + "\n" + content[closing:]

    # 2. Patch Logic (destructuring & resolvedMime)
    if "resolvedMime" not in content:
        # Destructuring
        p_destruct = r"const\s*\{[^}]*chatId[^}]*filePath[^}]*\}\s*=\s*req\.body;"
        new_destruct = "  const { chatId, filePath, mediaType, caption, fileName, mimetype: reqMimetype, ptt: reqPtt } = req.body;"
        content = re.sub(p_destruct, new_destruct, content)

        # Logic Injection
        p_logic = r"(const\s+ext\s*=\s*path\.extname\(filePath\)\.slice\(1\)\.toLowerCase\(\);)"
        if re.search(p_logic, content):
            content = re.sub(p_logic, r"\1\n    const resolvedMime = (fallback) => reqMimetype || MIME_MAP[ext] || fallback;", content)

        # Apply resolvedMime
        content = re.sub(r"mimetype:\s*MIME_MAP\[ext\]\s*\|\|\s*['\"]image/jpeg['\"]", "mimetype: resolvedMime('image/jpeg')", content)
        content = re.sub(r"mimetype:\s*MIME_MAP\[ext\]\s*\|\|\s*['\"]video/mp4['\"]", "mimetype: resolvedMime('video/mp4')", content)
        content = re.sub(r"mimetype:\s*MIME_MAP\[ext\]\s*\|\|\s*['\"]application/octet-stream['\"]", "mimetype: resolvedMime('application/octet-stream')", content)

        # PTT Support
        p_audio = r"audio:\s*buffer,\s*mimetype:[^,]+,\s*ptt:[^}]+"
        new_audio = "audio: buffer, mimetype: reqMimetype || (MIME_MAP[ext] || 'audio/ogg'), ptt: typeof reqPtt !== 'undefined' ? reqPtt : (ext === 'ogg' || ext === 'opus')"
        content = re.sub(p_audio, new_audio, content)

    # Save and update stamp
    BRIDGE_PATH.write_text(content, encoding="utf-8")
    STAMP_FILE.touch()
    
    # Restart gateway to apply changes
    subprocess.run(["hermes", "gateway", "restart"], capture_output=True)
    return True

def ensure_patched():
    if not is_patched():
        return apply_patch()
    return False

if __name__ == "__main__":
    if ensure_patched():
        print("✅ Bridge repaired successfully.")
    else:
        print("✅ Bridge is healthy.")
