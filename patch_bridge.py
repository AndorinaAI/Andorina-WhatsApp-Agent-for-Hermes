#!/usr/bin/env python3
"""
🔧 Andoriña — Bridge Patch Script
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ensures all advanced endpoints (/health, /groups, /qr) are present in the bridge.
"""

import sys, re, subprocess, shutil, time
from pathlib import Path
import os

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
main_hermes = HERMES_HOME
if main_hermes.parent.name == "profiles":
    main_hermes = main_hermes.parent.parent

_default_bridge = main_hermes / "hermes-agent" / "scripts" / "whatsapp-bridge" / "bridge.js"
BRIDGE_PATH = Path(os.environ.get("WHATSAPP_BRIDGE_PATH", str(_default_bridge)))

REQUIRED_MIMES = {
    "txt": "text/plain", "md": "text/markdown", "csv": "text/csv", "rtf": "application/rtf",
    "xls": "application/vnd.ms-excel", "zip": "application/zip", "bmp": "image/bmp",
    "heic": "image/heic", "mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg", "opus": "audio/ogg",
    "xcf": "image/x-xcf", "psd": "image/vnd.adobe.photoshop",
    # Common docs & archives
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "7z": "application/x-7z-compressed",
    "rar": "application/vnd.rar",
    "gz": "application/gzip", "tar": "application/x-tar",
    # Audio formats
    "m4a": "audio/mp4", "flac": "audio/flac", "aac": "audio/aac",
}

def read_bridge():
    if not BRIDGE_PATH.exists():
        print(f"❌ bridge.js not found at {BRIDGE_PATH}"); sys.exit(1)
    return BRIDGE_PATH.read_text(encoding="utf-8")

def patch_mime_map(content):
    pattern = r"(MIME_MAP\s*=\s*\{)"
    match = re.search(pattern, content)
    if not match: return content, False

    missing = []
    for ext, mime in REQUIRED_MIMES.items():
        if not re.search(rf"['\"]?{ext}['\"]?\s*:", content):
            missing.append(f"  '{ext}': '{mime}',")

    if not missing: return content, False

    insertion = "\n" + "\n".join(missing)
    closing = content.find("};", match.start())
    if closing == -1: return content, False

    return content[:closing] + insertion + "\n" + content[closing:], True

def patch_logic(content):
    patched = False

    # 1. Health Endpoint
    if "app.get('/health'" not in content:
        health_code = "\napp.get('/health', (req, res) => { res.json({ status: connectionState, uptime: process.uptime(), version: '1.5.1-Beta1' }); });\n"
        content = re.sub(r"app\.listen\s*\(", health_code + "app.listen(", content)
        patched = True

    # 2. Groups Endpoint
    if "app.get('/groups'" not in content:
        groups_code = """
// ANDORINA: Group Listing
app.get('/groups', async (req, res) => {
  if (!sock || connectionState !== 'connected') return res.status(503).json({ error: 'Not connected' });
  try {
    const groups = await sock.groupFetchAllParticipating();
    res.json(groups);
  } catch (err) { res.status(500).json({ error: err.message }); }
});
"""
        content = re.sub(r"app\.listen\s*\(", groups_code + "\napp.listen(", content)
        patched = True

    # 3. QR Endpoint
    if "globalLastQR" not in content:
        # Insert globalLastQR AFTER the last import statement (never before the shebang!)
        last_import = content.rfind("import ")
        if last_import != -1:
            # Find the end of that import line
            end_of_import_line = content.index("\n", last_import)
            insert_pos = end_of_import_line + 1
            content = content[:insert_pos] + "\n// ANDORINA: QR code cache for remote retrieval\nlet globalLastQR = null;\n" + content[insert_pos:]
        # Inject QR capture into connection.update handler
        content = re.sub(
            r"(case\s*['\"]connection\.update['\"]:\s*\{)",
            r"\1\n      if (update.qr) globalLastQR = update.qr;",
            content
        )
        qr_code = "\napp.get('/qr', (req, res) => { res.json({ qr: globalLastQR }); });\n"
        content = re.sub(r"app\.listen\s*\(", qr_code + "app.listen(", content)
        patched = True

    # 4. Media Mimetype/PTT Fixes
    if "reqMimetype" not in content:
        pattern = r"const\s*\{[^}]*chatId[^}]*filePath[^}]*\}\s*=\s*req\.body;"
        match = re.search(pattern, content)
        if match:
            new_destruct = "  const { chatId, filePath, mediaType, caption, fileName, mimetype: reqMimetype, ptt: reqPtt } = req.body;"
            content = content.replace(match.group(0), new_destruct)
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

    # 5. Presence / Typing Indicator
    if "req.body.presence" not in content:
        if "app.post('/typing'" in content:
            content = re.sub(
                r"await sock\.sendPresenceUpdate\('composing', chatId\);",
                "await sock.sendPresenceUpdate(req.body.presence || 'composing', chatId);",
                content
            )
            patched = True

    # 6. Profile Picture Endpoint
    if "app.get('/profile-pic'" not in content:
        pic_code = """
// ANDORINA: Profile Picture Fetch
app.get('/profile-pic/:jid', async (req, res) => {
  if (!sock || connectionState !== 'connected') return res.status(503).json({ error: 'Not connected' });
  try {
    const url = await sock.profilePictureUrl(req.params.jid, 'image');
    res.json({ url });
  } catch (err) { res.status(404).json({ error: 'Not found' }); }
});
"""
        content = re.sub(r"app\.listen\s*\(", pic_code + "\napp.listen(", content)
        patched = True

    # 7. fromMe Inbox Fix (v2 — universal CJS + ESM compatible)
    # The key insight: bridge.js from Hermes uses "type":"module" (ESM), so
    # require() is not available. It imports existsSync/readFileSync/writeFileSync
    # and `path` directly. We use `typeof require === 'function'` to detect CJS
    # at runtime and fall back to the in-scope ESM bindings if not.
    INBOX_FIX_V2_MARKER = "# ANDORINA INBOX FIX v2"
    if INBOX_FIX_V2_MARKER not in content:
        from_me_pattern = r"(if\s*\(\s*msg\.key\.fromMe\s*\)\s*\{)"
        from_me_fix = r"""\1
        // # ANDORINA INBOX FIX v2 — universal CJS+ESM, no external scope assumptions
        try {
            const body = msg.message?.conversation || msg.message?.extendedTextMessage?.text || "";
            if (body) {
                // Works in both CommonJS (require available) and ES Modules (named imports in scope)
                const _fsAnd = typeof require === 'function' ? require('fs') : { existsSync, readFileSync, writeFileSync };
                const _pathAnd = typeof require === 'function' ? require('path') : path;
                const _hmAnd = process.env.HERMES_HOME || _pathAnd.join(process.env.HOME || '/root', '.hermes');
                const _inboxAnd = _pathAnd.join(_hmAnd, 'skills', 'andorina', 'state', 'inbox.json');
                let _boxAnd = [];
                try {
                    if (_fsAnd.existsSync(_inboxAnd)) {
                        _boxAnd = JSON.parse(_fsAnd.readFileSync(_inboxAnd, 'utf8'));
                    }
                } catch(e) {}
                const _nowAnd = Date.now();
                const _dupAnd = _boxAnd.some(m => {
                    if (m.from !== "Me" || m.text !== body) return false;
                    return Math.abs(_nowAnd - new Date(m.date).getTime()) < 15000;
                });
                if (!_dupAnd) {
                    _boxAnd.push({
                        chatId: chatId,
                        chatName: chatId.split('@')[0],
                        from: "Me",
                        senderName: "Me",
                        text: body,
                        date: new Date().toLocaleString('sv-SE', {timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone}).replace(' ', 'T').substring(0, 19),
                        type: "text",
                        read: true
                    });
                    _fsAnd.writeFileSync(_inboxAnd, JSON.stringify(_boxAnd, null, 2));
                }
            }
        } catch(e) {
            console.error("Andorina inbox fix v2 failed:", e);
        }
        // --- END INBOX FIX v2 ---
"""
        # Remove old broken fix if present so we don't double-inject
        content = re.sub(
            r"// --- ANDORINA INBOX FIX ---.*?// --- END FIX ---\n",
            "",
            content,
            flags=re.DOTALL,
        )
        content = re.sub(from_me_pattern, from_me_fix, content)
        patched = True

    return content, patched

def main():
    content = read_bridge()
    content, m1 = patch_mime_map(content)
    content, m2 = patch_logic(content)

    if m1 or m2:
        bak_path = BRIDGE_PATH.with_name("bridge_andorina_bak.js")
        shutil.copy2(BRIDGE_PATH, bak_path)
        BRIDGE_PATH.write_text(content, encoding="utf-8")
        print(f"✅ bridge.js patched at {BRIDGE_PATH}")
        hermes_cmd = os.environ.get("HERMES_CMD")
        if not hermes_cmd:
            hermes_cmd = HERMES_HOME.name.lstrip(".")
            if not hermes_cmd: hermes_cmd = "hermes"
        subprocess.run(["bash", "-c", f"{hermes_cmd} gateway stop"], capture_output=True)
        time.sleep(1)
        subprocess.Popen(["bash", "-c", f"{hermes_cmd} gateway start"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print("✅ bridge.js already fully patched.")

if __name__ == "__main__":
    main()
