import os
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
SCRIPTS_DIR = Path(__file__).parent.absolute()
STATE_DIR = SCRIPTS_DIR.parent / "state"

targets = [
    HERMES_HOME / "memories" / "USER.md",
    HERMES_HOME / "memories" / "MEMORY.md",
    HERMES_HOME / ".hermes_history",
    STATE_DIR / "inbox.json",
    STATE_DIR / "agenda.json"
]

print("🧠 Starting surgical memory wipe...")

# Clear files
for t in targets:
    if t.exists():
        try:
            t.unlink()
            print(f"✅ Deleted: {t.name}")
        except Exception:
            pass

# Clear logs folder
logs_dir = HERMES_HOME / "logs"
if logs_dir.exists():
    for f in logs_dir.glob("*"):
        try:
            if f.is_file(): f.unlink()
            print(f"✅ Log cleared: {f.name}")
        except Exception:
            pass

print("\n✨ Cognitive reset successful. (WhatsApp session remains safe).")
