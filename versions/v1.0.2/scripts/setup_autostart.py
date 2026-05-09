#!/usr/bin/env python3
import os, sys
from pathlib import Path

# Paths
AUTOSTART_DIR = Path.home() / ".config" / "autostart"
hermes_cmd = os.environ.get("HERMES_CMD", "hermes")
DESKTOP_FILE  = AUTOSTART_DIR / f"{hermes_cmd}-agent.desktop"

def enable_autostart():
    print("🖥️ Configuring Autostart (Terminal Mode)...")
    
    try:
        AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
        
        # Command to run: starts gnome-terminal and keeps it open with the logs
        # We use 'bash -c' to keep the window open even if hermes stops (for debugging)
        cmd = f'gnome-terminal --title="⚕ {hermes_cmd.capitalize()} Agent" -- bash -c "{hermes_cmd} engine start; echo; echo [Motor detenido. Presiona cualquier tecla para cerrar]; read -n 1"'
        
        content = f"""[Desktop Entry]
Type=Application
Name={hermes_cmd.capitalize()} Agent
Comment=Start {hermes_cmd.capitalize()} Agent Engine on Login
Exec={cmd}
Icon=utilities-terminal
Terminal=false
Categories=System;Monitor;
X-GNOME-Autostart-enabled=true
"""
        
        DESKTOP_FILE.write_text(content, encoding="utf-8")
        DESKTOP_FILE.chmod(0o755)
        
        print(f"✅ Autostart enabled! You'll see a terminal at next login.")
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
