#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Paths
AUTOSTART_DIR = Path.home() / ".config" / "autostart"
hermes_cmd = os.environ.get("HERMES_CMD", "hermes")
DESKTOP_FILE  = AUTOSTART_DIR / f"{hermes_cmd}-agent.desktop"


def enable_autostart():
    print("🖥️ Configuring Autostart (Terminal Mode)...")

    try:
        AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)

        title = f"{hermes_cmd.capitalize()} Agent"

        # Configured to run headlessly in the background (no visible terminal window)
        exec_cmd = f"bash -c '{hermes_cmd} gateway start'"
        print("   Configured to run headlessly in the background.")

        content = f"""[Desktop Entry]
Type=Application
Name={title}
Comment=Start {title} Engine on Login
Exec={exec_cmd}
Icon=utilities-terminal
Terminal=false
Categories=System;Monitor;
X-GNOME-Autostart-enabled=true
"""

        DESKTOP_FILE.write_text(content, encoding="utf-8")
        DESKTOP_FILE.chmod(0o755)

        print(f"✅ Autostart enabled! It will run in the background at next login.")
        print(f"📂 Entry created at: {DESKTOP_FILE}")
        return True

    except Exception as e:
        print(f"❌ Error creating autostart entry: {e}")
        return False

def disable_autostart():
    if DESKTOP_FILE.exists():
        DESKTOP_FILE.unlink()
        print("🗑️ Autostart disabled.")
    else:
        print("ℹ️ Autostart was not enabled.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--disable":
        disable_autostart()
    else:
        enable_autostart()
