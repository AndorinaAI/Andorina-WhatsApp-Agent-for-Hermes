#!/usr/bin/env python3
"""
🔧 Andoriña — Bridge Patch Script
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys, re, subprocess
from pathlib import Path

BRIDGE_PATH = Path.home() / ".hermes" / "hermes-agent" / "scripts" / "whatsapp-bridge" / "bridge.js"

REQUIRED_MIMES = {
    "txt": "text/plain", "md": "text/markdown", "csv": "text/csv", "rtf": "application/rtf",
    "xls": "application/vnd.ms-excel", "zip": "application/zip", "bmp": "image/bmp",
    "heic": "image/heic", "mp3": "audio/mpeg", "wav": "audio/wav"
}

def read_bridge():
    if not BRIDGE_PATH.exists():
        print(f"❌ bridge.js not found at {BRIDGE_PATH}"); sys.exit(1)
    return BRIDGE_PATH.read_text(encoding="utf-8")

def patch_mime_map(content):
    # Flexible regex to find MIME_MAP regardless of spaces or const/let/var
    pattern = r"(MIME_MAP\s*=\s*\{)"
    match = re.search(pattern, content)
    if not match: return content, False

    missing = []
    for ext, mime in REQUIRED_MIMES.items():
        if not re.search(rf"['\"]?{ext}['\"]?\s*:", content):
            missing.append(f"  {ext}: '{mime}',")
    
    if not missing: return content, False
    
    insertion = "\n" + "\n".join(missing)
    # Find the first }; after the match
    closing = content.find("};", match.start())
    if closing == -1: return content, False
    
    return content[:closing] + insertion + "\n" + content[closing:], True

def patch_logic(content):
    if "reqMimetype" in content: return content, False
    
    # Robust destructuring patch
    pattern = r"const\s*\{[^}]*chatId[^}]*filePath[^}]*\}\s*=\s*req\.body;"
    match = re.search(pattern, content)
    if not match: return content, False

    new_destruct = "  const { chatId, filePath, mediaType, caption, fileName, mimetype: reqMimetype, ptt: reqPtt } = req.body;"
    content = content.replace(match.group(0), new_destruct)

    # Resolve Mime logic
    old_type = "const type = mediaType || inferMediaType(ext);"
    if old_type in content:
        new_type = old_type + "\n    const resolvedMime = (fallback) => reqMimetype || MIME_MAP[ext] || fallback;"
        content = content.replace(old_type, new_type)

    content = content.replace("mimetype: MIME_MAP[ext] || 'image/jpeg'", "mimetype: resolvedMime('image/jpeg')")
    content = content.replace("mimetype: MIME_MAP[ext] || 'video/mp4'", "mimetype: resolvedMime('video/mp4')")
    content = content.replace("mimetype: MIME_MAP[ext] || 'application/octet-stream'", "mimetype: resolvedMime('application/octet-stream')")
    
    # PTT Support
    audio_pattern = r"audio:\s*buffer,\s*mimetype:[^,]+,\s*ptt:[^}]+"
    content = re.sub(audio_pattern, "audio: buffer, mimetype: reqMimetype || (MIME_MAP[ext] || 'audio/ogg'), ptt: typeof reqPtt !== 'undefined' ? reqPtt : (ext === 'ogg' || ext === 'opus')", content)
    
    return content, True

def main():
    content = read_bridge()
    content, m1 = patch_mime_map(content)
    content, m2 = patch_logic(content)

    if m1 or m2:
        BRIDGE_PATH.write_text(content, encoding="utf-8")
        print("✅ bridge.js patched.")
        subprocess.run(["hermes", "gateway", "restart"], capture_output=True)
    else:
        print("✅ bridge.js already patched.")

if __name__ == "__main__":
    main()
