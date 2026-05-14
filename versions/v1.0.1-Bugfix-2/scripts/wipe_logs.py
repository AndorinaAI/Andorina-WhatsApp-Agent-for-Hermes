import os, glob
from pathlib import Path

home = Path.home()
targets = [
    home / ".hermes" / "memories" / "USER.md",
    home / ".hermes" / "memories" / "MEMORY.md",
    home / ".hermes" / ".hermes_history"
]

print("🧠 Starting surgical memory wipe...")

# Clear files
for t in targets:
    if t.exists():
        try:
            t.unlink()
            print(f"✅ Deleted: {t.name}")
        except:
            pass

# Clear logs folder
logs_dir = home / ".hermes" / "logs"
if logs_dir.exists():
    for f in logs_dir.glob("*"):
        try:
            if f.is_file(): f.unlink()
            print(f"✅ Log cleared: {f.name}")
        except:
            pass

print("\n✨ Cognitive reset successful. (WhatsApp session remains safe).")
