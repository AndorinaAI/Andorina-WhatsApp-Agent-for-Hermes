#!/usr/bin/env python3
"""Andoriña Self-Updater

Checks the GitHub releases API for a newer version of Andoriña, downloads it,
backs up user data, replaces scripts+GUI, re-applies patches, syncs souls, and
restarts the gateway.

Usage:
    python3 andorina_updater.py --check     → JSON: {up_to_date, current, latest}
    python3 andorina_updater.py --update    → full update, stdout progress
    python3 andorina_updater.py --json      → --check but emit JSON (for GUI)
"""

import sys
import json
import os
import shutil
import zipfile
import subprocess
import tempfile
import time
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
GITHUB_REPO   = "AndorinaAI/Andorina-WhatsApp-Agent-for-Hermes"   # adjust if needed
GITHUB_API    = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
VERSION_FILE  = Path(__file__).parent / "VERSION"          # e.g. "1.5.0"
SKILL_DIR     = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))) / "skills" / "andorina"

# Directories/files to preserve during update (relative to SKILL_DIR)
PRESERVE = [
    "state/",
    ".env",
    "state/guard_rules.json",
    "state/inbox.json",
    "state/souls/",
    "state/agenda.json",
    "state/alerts.json",
    "state/sessions.json",
    "state/notes/",
    "state/recurring/",
    "state/uploads/",
]

SOURCE_DIR = Path(__file__).parent


def _log(msg):
    print(msg, flush=True)


def get_current_version():
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    # Fallback: read from SKILL_DIR/VERSION
    sv = SKILL_DIR / "VERSION"
    if sv.exists():
        return sv.read_text(encoding="utf-8").strip()
    return "0.0.0"


def get_latest_release():
    """Fetch latest release info from GitHub. Returns dict or raises."""
    try:
        import urllib.request
        req = urllib.request.Request(
            GITHUB_API,
            headers={"User-Agent": "andorina-updater/1.0", "Accept": "application/vnd.github+json"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"Cannot reach GitHub: {e}")


def check_update(json_output=False):
    current = get_current_version()
    try:
        release = get_latest_release()
    except RuntimeError as e:
        result = {"ok": False, "error": str(e), "current": current, "latest": None, "up_to_date": None}
        if json_output:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ {e}")
        return result

    tag = release.get("tag_name", "").lstrip("vV")
    name = release.get("name", tag)
    body = release.get("body", "")[:500]
    assets = release.get("assets", [])
    zip_asset = next((a for a in assets if a["name"].endswith(".zip")), None)
    tarball = release.get("zipball_url")
    download_url = zip_asset["browser_download_url"] if zip_asset else tarball

    up_to_date = _version_tuple(current) >= _version_tuple(tag)

    result = {
        "ok": True,
        "current": current,
        "latest": tag,
        "release_name": name,
        "release_notes": body,
        "up_to_date": up_to_date,
        "download_url": download_url,
    }

    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if up_to_date:
            print(f"✅ Andoriña {current} está actualizada (última: {tag})")
        else:
            print(f"⬆️  Nueva versión disponible: {tag}  (tienes: {current})")
            if body:
                print(f"\n📋 Novedades:\n{body}\n")

    return result


def _version_tuple(v):
    import re
    try:
        parts = []
        for x in str(v).replace("-", ".").replace("_", ".").split("."):
            m = re.search(r'\d+', x)
            if m:
                parts.append(int(m.group()))
            else:
                parts.append(0)
        return tuple(parts)
    except Exception:
        return (0,)


def backup_user_data(target_dir: Path) -> Path:
    """Copy preserved paths from SKILL_DIR into target_dir/backup/."""
    backup = target_dir / "backup"
    backup.mkdir(parents=True, exist_ok=True)
    for rel in PRESERVE:
        src = SKILL_DIR / rel.rstrip("/")
        dst = backup / rel.rstrip("/")
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return backup


def restore_user_data(backup: Path):
    """Restore preserved data from backup into SKILL_DIR."""
    for rel in PRESERVE:
        src = backup / rel.rstrip("/")
        dst = SKILL_DIR / rel.rstrip("/")
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def download_zip(url: str, dest: Path):
    import urllib.request
    _log(f"⬇️  Descargando {url} ...")
    urllib.request.urlretrieve(url, dest)
    _log(f"   ✅ Descargado → {dest.name}")


def update(download_url: str, new_version: str):
    with tempfile.TemporaryDirectory(prefix="andorina_update_") as tmp:
        tmp = Path(tmp)
        zip_path = tmp / "release.zip"

        # 1. Download
        download_zip(download_url, zip_path)

        # 2. Extract
        _log("📦 Extrayendo...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp / "extracted")
        # Find the root of extracted content (GitHub adds a subfolder)
        extracted_root = tmp / "extracted"
        subdirs = [d for d in extracted_root.iterdir() if d.is_dir()]
        new_skill_root = subdirs[0] if subdirs else extracted_root
        # Validate structure — if scripts/ not present, look one level deeper
        if not (new_skill_root / "scripts").exists():
            deeper = [d for d in new_skill_root.iterdir() if d.is_dir() and (d / "scripts").exists()]
            if deeper:
                new_skill_root = deeper[0]
        if not (new_skill_root / "scripts").exists():
            _log("❌ Estructura del zip inesperada — no se encontró scripts/ en el contenido descargado")
            return
        _log(f"   Raíz extraída: {new_skill_root.name}")

        # 3. Backup user data
        _log("💾 Haciendo backup de datos de usuario...")
        backup = backup_user_data(tmp)
        _log(f"   Backup en: {backup}")

        # 4. Replace skill files (preserve user data dirs)
        _log("🔄 Actualizando archivos...")
        skip_dirs = {p.split("/")[0] for p in PRESERVE if "/" in p}
        skip_files = {p for p in PRESERVE if "/" not in p}

        for item in new_skill_root.iterdir():
            if item.name in skip_dirs or item.name in skip_files:
                continue
            dst = SKILL_DIR / item.name
            if item.is_dir():
                shutil.copytree(item, dst, dirs_exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dst)
        _log("   ✅ Archivos actualizados")

        # 5. Restore user data
        _log("♻️  Restaurando datos de usuario...")
        restore_user_data(backup)
        _log("   ✅ Datos restaurados")

        # 6. Re-apply patches & verify health
        health_script = SKILL_DIR / "scripts" / "utils" / "bridge_health.py"
        if health_script.exists():
            _log("🩹 Ejecutando diagnóstico y reparación automática...")
            r = subprocess.run([sys.executable, str(health_script)], capture_output=True, text=True)
            for line in (r.stdout + r.stderr).splitlines():
                _log(f"   {line}")
        else:
            # Fallback to individual patch scripts if bridge_health.py doesn't exist
            patch_script = SKILL_DIR / "patch_whatsapp.py"
            if patch_script.exists():
                _log("🩹 Reaplicando patches...")
                r = subprocess.run([sys.executable, str(patch_script)], capture_output=True, text=True)
                for line in (r.stdout + r.stderr).splitlines():
                    _log(f"   {line}")
            patch_bridge = SKILL_DIR / "patch_bridge.py"
            if patch_bridge.exists():
                _log("🩹 Reaplicando bridge patch...")
                r = subprocess.run([sys.executable, str(patch_bridge)], capture_output=True, text=True)
                for line in (r.stdout + r.stderr).splitlines():
                    _log(f"   {line}")

        # 7. Soul sync
        soul_sync = SKILL_DIR / "scripts" / "security" / "soul_sync.py"
        if soul_sync.exists():
            _log("🧬 Sincronizando souls...")
            r = subprocess.run([sys.executable, str(soul_sync)], capture_output=True, text=True)
            _log("   ✅ Souls sincronizadas" if r.returncode == 0 else f"   ⚠️  {r.stderr[:200]}")

        # 7b. Re-registrar hooks en config.yaml (por si han cambiado entre versiones)
        _log("🔧 Re-registrando hooks en config.yaml...")
        try:
            src_dir = Path(__file__).parent
            sys.path.insert(0, str(src_dir))
            import importlib
            import setup_lib as _sl
            importlib.reload(_sl)  # asegura versión recién descargada
            agent_path = SKILL_DIR.parent.parent  # ~/.hermes
            ok = _sl.register_hooks(str(agent_path), str(SKILL_DIR / "scripts"), log_fn=_log)
            if ok:
                _log("   ✅ Hooks actualizados")
            else:
                _log("   ⚠️  No se pudieron re-registrar los hooks")
        except Exception as e:
            _log(f"   ⚠️  hooks: {e}")

        # 8. Write new version
        (SKILL_DIR / "VERSION").write_text(new_version, encoding="utf-8")
        SOURCE_DIR / "VERSION" and (SOURCE_DIR / "VERSION").write_text(new_version, encoding="utf-8")
        _log(f"📌 Versión actualizada a {new_version}")

        # 9. Restart gateway
        _log("🔄 Reiniciando hermes-gateway...")
        r = subprocess.run(
            ["systemctl", "--user", "restart", "hermes-gateway"],
            capture_output=True, timeout=15
        )
        if r.returncode == 0:
            _log("   ✅ Gateway reiniciado")
        else:
            _log("   ⚠️  No se pudo reiniciar automáticamente — reinicia manualmente")

        # 9b. Restart Andoriña Panel GUI server
        _log("🔄 Reiniciando Andoriña Panel...")
        panel_launcher = SKILL_DIR / "Andorina-Panel.sh"
        if panel_launcher.exists():
            try:
                subprocess.Popen(["bash", str(panel_launcher)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                _log("   ✅ Panel reiniciado")
            except Exception as e:
                _log(f"   ⚠️  No se pudo reiniciar el panel automáticamente: {e}")

        _log(f"\n✅ Actualización a {new_version} completada.")


def run():
    check_only = "--check" in sys.argv
    json_output = "--json" in sys.argv
    do_update   = "--update" in sys.argv

    if check_only or json_output:
        result = check_update(json_output=json_output)
        return 0 if result.get("ok") else 1

    if do_update:
        info = check_update(json_output=False)
        if not info.get("ok"):
            return 1
        if info.get("up_to_date"):
            _log("✅ Ya estás en la última versión.")
            return 0
        if not info.get("download_url"):
            _log("❌ No se encontró URL de descarga en el release.")
            return 1
        update(info["download_url"], info["latest"])
        return 0

    # Default: just check
    check_update(json_output=False)
    return 0


if __name__ == "__main__":
    sys.exit(run())
