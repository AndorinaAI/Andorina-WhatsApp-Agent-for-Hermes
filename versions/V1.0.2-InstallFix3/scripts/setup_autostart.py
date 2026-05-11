#!/usr/bin/env python3
import os, sys, shutil
from pathlib import Path

# Paths
AUTOSTART_DIR = Path.home() / ".config" / "autostart"
hermes_cmd = os.environ.get("HERMES_CMD", "hermes")
DESKTOP_FILE  = AUTOSTART_DIR / f"{hermes_cmd}-agent.desktop"

def detect_terminal():
    """Detect available terminal emulator on the system"""
    terminals = [
        ("gnome-terminal", 'gnome-terminal --title="⚕ {title}" -- bash -c "{cmd}"'),
        ("konsole", 'konsole --title "⚕ {title}" -e bash -c "{cmd}"'),
        ("xfce4-terminal", 'xfce4-terminal --title="⚕ {title}" -e bash -c "{cmd}"'),
        ("mate-terminal", 'mate-terminal --title="⚕ {title}" -e bash -c "{cmd}"'),
        ("lxterminal", 'lxterminal --title="⚕ {title}" -e bash -c "{cmd}"'),
        ("xterm", 'xterm -title "⚕ {title}" -e bash -c "{cmd}"'),
    ]
    for name, template in terminals:
        if shutil.which(name):
            return name, template
    return None, None

def enable_autostart():
    print("🖥️ Configuring Autostart (Terminal Mode)...")

    try:
        AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)

        title = f"{hermes_cmd.capitalize()} Agent"
        inner_cmd = f"{hermes_cmd} engine start; echo; echo [Motor detenido. Presiona cualquier tecla para cerrar]; read -n 1"

        term_name, template = detect_terminal()
        if template:
            exec_cmd = template.format(title=title, cmd=inner_cmd)
            print(f"   Detected terminal: {term_name}")
        else:
            # Fallback: run without a visible terminal window
            exec_cmd = f"bash -c '{hermes_cmd} engine start'"
            print("   ⚠️ No supported terminal found, using headless fallback.")

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
