import os, glob
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
targets = [
    HERMES_HOME / "memories" / "USER.md",
    HERMES_HOME / "memories" / "MEMORY.md",
    HERMES_HOME / ".hermes_history"
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
logs_dir = HERMES_HOME / "logs"
if logs_dir.exists():
    for f in logs_dir.glob("*"):
        try:
            if f.is_file(): f.unlink()
            print(f"✅ Log cleared: {f.name}")
        except:
            pass

print("\n✨ Cognitive reset successful. (WhatsApp session remains safe).")
