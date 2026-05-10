#!/usr/bin/env python3
"""
🚀 Andoriña — Smart Scheduling Engine v3 (Resilient + Auto-Offset)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Key features:
  - Configurable delivery window: messages persist in agenda.json until
    successfully sent, even if the model is late by up to DELIVERY_WINDOW_MINUTES.
  - Auto-offset: when multiple tasks share the same minute, each is
    automatically pushed by CRON_OFFSET_MINUTES to avoid agent collisions.
  - Only deleted on successful delivery (never silently dropped).

User-configurable via ~/.hermes/.env:
  ANDORINA_DELIVERY_WINDOW=60   # Minutes a task stays alive after its time
  ANDORINA_CRON_OFFSET=2        # Minutes of separation between concurrent tasks
"""

import sys, json, re, time, urllib.request
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

sys.path.append(str(Path(__file__).parent))
from send import post_json

# ─────────────── Paths ────────────────────────────────────────────────────────
# ─────────────── Paths ────────────────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).parent.absolute()
HERMES_BASE = SCRIPTS_DIR.parent
AGENDA_FILE = HERMES_BASE / "state" / "agenda.json"
import os
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
ENV_FILE    = HERMES_HOME / ".env"

# ─────────────── Defaults (overridable via .env) ──────────────────────────────
DELIVERY_WINDOW_MINUTES = 60   # Task stays alive this many minutes after scheduled time
CRON_OFFSET_MINUTES     = 2    # Auto-separation between tasks scheduled at same minute

def load_env_config():
    """Load user-configurable settings from .env"""
    global DELIVERY_WINDOW_MINUTES, CRON_OFFSET_MINUTES
    if not ENV_FILE.exists():
        return
    try:
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if "=" not in line or line.strip().startswith("#"):
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip()
            if k == "ANDORINA_DELIVERY_WINDOW":
                DELIVERY_WINDOW_MINUTES = int(v)
            elif k == "ANDORINA_CRON_OFFSET":
                CRON_OFFSET_MINUTES = int(v)
    except Exception:
        pass

# ─────────────── Output ───────────────────────────────────────────────────────
def out(data):
    print(json.dumps(data, ensure_ascii=False))

# ─────────────── Agenda persistence ──────────────────────────────────────────
def load_agenda():
    if not AGENDA_FILE.exists():
        try:
            AGENDA_FILE.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return {}
    try:
        return json.loads(AGENDA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_agenda(agenda):
    try:
        AGENDA_FILE.write_text(json.dumps(agenda, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception as e:
        print(f"❌ Critical Error: Could not write agenda: {e}", file=sys.stderr)
        return False

# ─────────────── Delivery window check ───────────────────────────────────────
def is_within_window(scheduled_time_str: str) -> bool:
    """
    Returns True if we are still within DELIVERY_WINDOW_MINUTES of the
    scheduled time (handles messages that arrive late due to slow models).
    Supports HH:MM, DD HH:MM, DD/MM HH:MM formats.
    """
    now = datetime.now()
    try:
        # Try HH:MM only
        m = re.match(r"^(\d{1,2}):(\d{1,2})$", scheduled_time_str.strip())
        if m:
            scheduled = now.replace(hour=int(m.group(1)), minute=int(m.group(2)),
                                    second=0, microsecond=0)
            # If time is in the past by more than the window, skip
            delta = (now - scheduled).total_seconds() / 60
            return -5 <= delta <= DELIVERY_WINDOW_MINUTES  # 5 min early tolerance

        # Try DD/MM HH:MM or DD-MM HH:MM
        m = re.match(r"^(\d{1,2})[/-](\d{1,2})\s+(\d{1,2}):(\d{1,2})$", scheduled_time_str.strip())
        if m:
            day, mon, h, minute = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            scheduled = now.replace(day=day, month=mon, hour=h, minute=minute,
                                    second=0, microsecond=0)
            delta = (now - scheduled).total_seconds() / 60
            return -5 <= delta <= DELIVERY_WINDOW_MINUTES

        # Try DD HH:MM
        m = re.match(r"^(\d{1,2})\s+(\d{1,2}):(\d{1,2})$", scheduled_time_str.strip())
        if m:
            day, h, minute = int(m.group(1)), int(m.group(2)), int(m.group(3))
            scheduled = now.replace(day=day, hour=h, minute=minute,
                                    second=0, microsecond=0)
            delta = (now - scheduled).total_seconds() / 60
            return -5 <= delta <= DELIVERY_WINDOW_MINUTES

    except Exception:
        pass
    # For dates far in the future (e.g., Christmas), always allow
    return True

# ─────────────── Cron schedule parser ────────────────────────────────────────
def parse_cron_schedule(time_str: str) -> str:
    time_str = time_str.strip()
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})\s+(\d{1,2}):(\d{1,2})$", time_str)
    if m:
        day, mon, h, minute = m.groups()
        return f"{int(minute)} {int(h)} {int(day)} {int(mon)} *"
    m = re.match(r"^(\d{1,2})\s+(\d{1,2}):(\d{1,2})$", time_str)
    if m:
        day, h, minute = m.groups()
        return f"{int(minute)} {int(h)} {int(day)} * *"
    m = re.match(r"^(\d{1,2}):(\d{1,2})$", time_str)
    if m:
        h, minute = m.groups()
        return f"{int(minute)} {int(h)} * * *"
    return "INVALID_FORMAT"

def apply_offset(time_str: str, offset_minutes: int) -> str:
    """Add offset_minutes to a HH:MM time string, returns new time string."""
    m = re.match(r"^(\d{1,2}):(\d{1,2})$", time_str.strip())
    if not m:
        return time_str  # Non-HH:MM formats don't get auto-offset
    base = datetime.now().replace(hour=int(m.group(1)), minute=int(m.group(2)),
                                  second=0, microsecond=0)
    new_time = base + timedelta(minutes=offset_minutes)
    return new_time.strftime("%H:%M")

# ─────────────── Auto-offset logic ───────────────────────────────────────────
def get_next_free_slot(base_time_str: str, agenda: dict) -> str:
    """
    Given a desired time, check if other tasks are already scheduled at that
    exact minute. If so, offset by CRON_OFFSET_MINUTES until a free slot is found.
    """
    existing_times = {v["time"] for v in agenda.values()}
    candidate = base_time_str.strip()

    offset = 0
    while candidate in existing_times and offset < 60:
        offset += CRON_OFFSET_MINUTES
        candidate = apply_offset_universal(base_time_str, offset)

    return candidate

def apply_offset_universal(time_str: str, offset_minutes: int) -> str:
    """Add offset_minutes to any supported date/time format."""
    now = datetime.now()
    try:
        # Format: HH:MM
        m = re.match(r"^(\d{1,2}):(\d{1,2})$", time_str.strip())
        if m:
            base = now.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
            return (base + timedelta(minutes=offset_minutes)).strftime("%H:%M")

        # Format: DD HH:MM
        m = re.match(r"^(\d{1,2})\s+(\d{1,2}):(\d{1,2})$", time_str.strip())
        if m:
            base = now.replace(day=int(m.group(1)), hour=int(m.group(2)), minute=int(m.group(3)), second=0, microsecond=0)
            return (base + timedelta(minutes=offset_minutes)).strftime("%d %H:%M").lstrip("0")

        # Format: DD/MM HH:MM
        m = re.match(r"^(\d{1,2})[/-](\d{1,2})\s+(\d{1,2}):(\d{1,2})$", time_str.strip())
        if m:
            base = now.replace(day=int(m.group(1)), month=int(m.group(2)), hour=int(m.group(3)), minute=int(m.group(4)), second=0, microsecond=0)
            return (base + timedelta(minutes=offset_minutes)).strftime("%d/%m %H:%M").replace("/0", "/")
    except:
        pass
    return time_str

# ─────────────── Commands ─────────────────────────────────────────────────────
def cmd_list():
    agenda = load_agenda()
    items = []
    for mid, data in agenda.items():
        items.append({
            "id": mid,
            "to": data.get("chatId", data.get("name")),
            "time": data.get("time"),
            "message": data.get("message"),
            "file": data.get("file_path"),
        })
    out({"ok": True, "agenda": items})

def cmd_send_pending(msg_id: str):
    """Triggered by cron or manually. Only deletes on success."""
    agenda = load_agenda()
    if msg_id not in agenda:
        out({"ok": False, "error": "ID_NOT_FOUND", "id": msg_id})
        sys.exit(1)

    data = agenda[msg_id]
    chat_id   = data["chatId"]
    file_path = data.get("file_path")
    message   = data.get("message", "")

    # ── Delivery window check ──────────────────────────────────────────────
    if not is_within_window(data.get("time", "")):
        out({"ok": False, "error": "DELIVERY_WINDOW_EXPIRED",
             "id": msg_id, "scheduled": data.get("time"),
             "window_minutes": DELIVERY_WINDOW_MINUTES})
        # Do NOT delete — let the user decide
        sys.exit(1)

    # ── Actual send ────────────────────────────────────────────────────────
    success = False
    if file_path:
        fpath = Path(file_path)
        if not fpath.exists():
            out({"ok": False, "error": "FILE_NOT_FOUND", "path": file_path})
            sys.exit(1)

        from files import cmd_enviar
        try:
            cmd_enviar(str(fpath), chat_id, is_voice=data.get("is_voice", False))
            success = True
        except SystemExit as e:
            success = (e.code == 0)
        except Exception:
            success = False
    else:
        res, err = post_json("/send", {"chatId": chat_id, "message": message})
        success = bool(res and res.get("success"))

    # ── Only delete on success ─────────────────────────────────────────────
    if success:
        del agenda[msg_id]
        save_agenda(agenda)
        out({"ok": True, "delivered": True, "id": msg_id})
    else:
        out({"ok": False, "error": "SEND_FAILED", "id": msg_id,
             "note": "Message kept in agenda for retry within delivery window."})
        sys.exit(1)

def cmd_remove(msg_id: str):
    agenda = load_agenda()
    if msg_id in agenda:
        del agenda[msg_id]
        if save_agenda(agenda):
            # Try to remove the native cron job silently
            try:
                res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
                if res.returncode == 0:
                    crons = [line for line in res.stdout.splitlines() if f"ANDORINA_AGENDA:{msg_id}" not in line]
                    # If crons list is empty, crontab - requires at least a newline
                    crons_str = "\n".join(crons) + "\n" if crons else "\n"
                    subprocess.run(["crontab", "-"], input=crons_str, text=True, check=True)
            except Exception:
                pass
            out({"ok": True, "message": f"Cancelled: {msg_id}"})
        else:
            out({"ok": False, "error": "DISK_ERROR"})
    else:
        out({"ok": False, "error": "ID_NOT_FOUND"})

def cmd_auto_schedule(chat_id: str, time_str: str, message: str,
                      file_path=None, is_voice: bool = False):
    if not (chat_id.endswith("@s.whatsapp.net") or chat_id.endswith("@g.us")):
        out({"ok": False, "error": "INVALID_CHAT_ID"}); sys.exit(1)

    agenda = load_agenda()

    # ── Auto-offset: find next free minute slot ───────────────────────────
    final_time = get_next_free_slot(time_str, agenda)
    if final_time != time_str:
        print(f"ℹ️  Auto-offset applied: {time_str} → {final_time} "
              f"(collision avoidance)", file=sys.stderr)

    cron_expr = parse_cron_schedule(final_time)
    if cron_expr == "INVALID_FORMAT":
        out({"ok": False, "error": "INVALID_TIME_FORMAT"}); sys.exit(1)

    # ── Unique ID ─────────────────────────────────────────────────────────
    msg_id = f"msg_{datetime.now().strftime('%H%M%S%f')[:-3]}"

    # ── Persist to agenda BEFORE creating the cron ────────────────────────
    agenda[msg_id] = {
        "chatId": chat_id,
        "name": chat_id.split("@")[0],
        "time": final_time,
        "scheduled_original": time_str,
        "message": message,
        "file_path": str(Path(file_path).absolute()) if file_path else None,
        "is_voice": is_voice,
        "created_at": datetime.now().isoformat(),
    }

    if not save_agenda(agenda):
        out({"ok": False, "error": "STORAGE_FAILED"}); sys.exit(1)

    # ── Register native cron ──────────────────────────────────────────────
    # Export environment variables for the cronjob to maintain agent isolation
    hermes_cmd = os.environ.get("HERMES_CMD", HERMES_HOME.name.lstrip(".") or "hermes")
    env_prefix = f"HERMES_HOME='{HERMES_HOME}' HERMES_CMD='{hermes_cmd}'"
    cmd_str = f"{env_prefix} python3 '{SCRIPTS_DIR}/agenda.py' send {msg_id} >/dev/null 2>&1 # ANDORINA_AGENDA:{msg_id}"
    try:
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        current_crons = res.stdout if res.returncode == 0 else ""
        new_cron = f"{cron_expr} {cmd_str}\n"
        subprocess.run(["crontab", "-"], input=current_crons + new_cron, text=True, check=True)
        out({"ok": True, "id": msg_id,
             "time_requested": time_str,
             "time_scheduled": final_time,
             "offset_applied": final_time != time_str})
    except Exception as e:
        out({"ok": False, "error": "CRON_FAILED", "detail": str(e)})

# ─────────────── Entry point ──────────────────────────────────────────────────
if __name__ == "__main__":
    load_env_config()

    if len(sys.argv) < 2:
        print("Usage: agenda.py [list|send|remove|auto-schedule]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        cmd_list()

    elif cmd == "send" and len(sys.argv) > 2:
        cmd_send_pending(sys.argv[2])

    elif cmd == "remove" and len(sys.argv) > 2:
        cmd_remove(sys.argv[2])

    elif cmd == "auto-schedule" and len(sys.argv) > 4:
        chat_id  = sys.argv[2]
        time_str = sys.argv[3]
        is_voice = "--voice" in sys.argv
        args     = [a for a in sys.argv[4:] if a != "--voice"]

        file_path = None
        message   = ""

        if args and Path(args[0]).exists():
            file_path = args[0]
            message   = " ".join(args[1:]) if len(args) > 1 else ""
        else:
            message = " ".join(args)

        cmd_auto_schedule(chat_id, time_str, message, file_path, is_voice)

    else:
        print("Invalid command or missing arguments.")
        sys.exit(1)
