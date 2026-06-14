#!/usr/bin/env python3
"""Disk space monitor — runs as a Hermes cron job.

Checks free disk space on the home partition and sends a WhatsApp
alert to the admin when usage exceeds the warning threshold.

Can also be run manually: python3 disk_monitor.py
"""
import os
import sys
import shutil
from pathlib import Path

WARN_THRESHOLD_PCT = 85   # warn at 85% used
CRIT_THRESHOLD_PCT = 95   # critical at 95% used

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
SKILL_BASE  = HERMES_HOME / "skills" / "andorina"

sys.path.insert(0, str(SKILL_BASE / "scripts"))

def check_disk():
    stat = shutil.disk_usage(Path.home())
    used_pct = (stat.used / stat.total) * 100
    free_gb  = stat.free  / (1024 ** 3)
    total_gb = stat.total / (1024 ** 3)
    return used_pct, free_gb, total_gb

def get_admin_jid():
    try:
        from common import ENV_PATH
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            # Prefer ADMIN_PHONE (specific), fall back to WHATSAPP_ALLOWED_USERS (skip wildcards)
            if line.startswith("ADMIN_PHONE="):
                num = line.split("=", 1)[1].strip()
                if num and num != "*":
                    return f"{num}@s.whatsapp.net" if "@" not in num else num
            if line.startswith("WHATSAPP_ALLOWED_USERS="):
                num = line.split("=", 1)[1].strip().split(",")[0].strip()
                if num and num != "*" and "@" not in num:
                    return f"{num}@s.whatsapp.net"
    except Exception:
        pass
    return None

def send_alert(message: str, admin_jid: str):
    send_script = SKILL_BASE / "scripts" / "transport" / "send.py"
    if send_script.exists() and admin_jid:
        import subprocess
        subprocess.run(
            [sys.executable, str(send_script), "message", admin_jid, message],
            capture_output=True, timeout=15
        )

def main():
    used_pct, free_gb, total_gb = check_disk()

    if used_pct >= CRIT_THRESHOLD_PCT:
        level = "🔴 CRÍTICO"
        emoji = "🚨"
    elif used_pct >= WARN_THRESHOLD_PCT:
        level = "🟡 AVISO"
        emoji = "⚠️"
    else:
        # All good — silent exit
        print(f"✅ Disco OK: {used_pct:.1f}% usado ({free_gb:.1f}GB libres)")
        return

    msg = (
        f"{emoji} {level}: Espacio en disco bajo\n"
        f"Usado: {used_pct:.1f}% ({total_gb - free_gb:.1f}GB / {total_gb:.1f}GB)\n"
        f"Libre: {free_gb:.1f}GB\n\n"
        f"Limpia cachés con:\n"
        f"rm -rf ~/.hermes/image_cache/* ~/.hermes/audio_cache/* ~/.hermes/document_cache/*"
    )

    print(msg)
    admin = get_admin_jid()
    if admin:
        send_alert(msg, admin)
    else:
        print("⚠️  No se pudo determinar el JID del admin para enviar alerta")

if __name__ == "__main__":
    main()
