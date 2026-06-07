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

import sys
import json
import re
import time
import shlex
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

sys.path.append(str(Path(__file__).parent.parent))
from common import post_json
from utils.safe_json import read_json_safe, write_json_safe
try:
    from filelock import FileLock
except ImportError:
    print("❌ Error: 'filelock' no está instalado. Ejecuta: pip install filelock", file=sys.stderr)
    sys.exit(1)

# ─────────────── Paths ────────────────────────────────────────────────────────
SCRIPTS_DIR = Path(__file__).parent.parent.absolute()
HERMES_BASE = SCRIPTS_DIR.parent
AGENDA_FILE = HERMES_BASE / "state" / "agenda.json"
import os
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))

# ─────────────── Defaults (overridable via .env) ──────────────────────────────
DELIVERY_WINDOW_MINUTES = 60   # Task stays alive this many minutes after scheduled time
CRON_OFFSET_MINUTES     = 2    # Auto-separation between tasks scheduled at same minute

def load_env_config():
    """Load user-configurable settings from .env using centralized common.py"""
    global DELIVERY_WINDOW_MINUTES, CRON_OFFSET_MINUTES
    from common import load_env
    env = load_env()
    DELIVERY_WINDOW_MINUTES = int(env.get("ANDORINA_DELIVERY_WINDOW", DELIVERY_WINDOW_MINUTES))
    CRON_OFFSET_MINUTES = int(env.get("ANDORINA_CRON_OFFSET", CRON_OFFSET_MINUTES))

# ─────────────── Output ───────────────────────────────────────────────────────
def out(data):
    print(json.dumps(data, ensure_ascii=False))

# ─────────────── Agenda persistence ──────────────────────────────────────────
def load_agenda():
    data = read_json_safe(AGENDA_FILE, default={})
    return data if isinstance(data, dict) else {}

def save_agenda(agenda):
    if not write_json_safe(AGENDA_FILE, agenda):
        print("❌ Critical Error: Could not write agenda", file=sys.stderr)
        return False
    return True

def locked_update_agenda(action_func):
    """Acquires a lock, loads the agenda, runs action_func(agenda), saves if action_func returns True.

    IMPORTANT: Uses direct file I/O inside the lock — NOT read_json_safe/write_json_safe.
    Those helpers also acquire the same lock file (agenda.json.lock), which causes a
    nested-lock timeout (filelock Timeout exception caught silently → write never happens
    → agenda.json never created → cron fires but finds ID_NOT_FOUND).
    By reading/writing the file directly here, we avoid the double-lock entirely.
    """
    AGENDA_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock_file = str(AGENDA_FILE) + ".lock"
    with FileLock(lock_file, timeout=10):
        # Direct I/O — we already hold the lock, no need to re-lock.
        try:
            agenda = {}
            if AGENDA_FILE.exists():
                raw = AGENDA_FILE.read_text(encoding="utf-8").strip()
                if raw:
                    data = json.loads(raw)
                    agenda = data if isinstance(data, dict) else {}
        except Exception:
            agenda = {}

        if action_func(agenda):
            try:
                AGENDA_FILE.write_text(
                    json.dumps(agenda, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
            except Exception as e:
                print(f"❌ Critical Error: Could not write agenda: {e}", file=sys.stderr)
        return agenda

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
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})(?:[/-]\d{4})?\s+(\d{1,2}):(\d{1,2})$", time_str)
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
    existing_crons = set()
    for v in agenda.values():
        c = parse_cron_schedule(v["time"])
        if c != "INVALID_FORMAT":
            existing_crons.add(c)
            
    candidate = base_time_str.strip()

    offset = 0
    while parse_cron_schedule(candidate) in existing_crons and offset < 60:
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

        # Format: DD/MM/YYYY HH:MM or DD/MM HH:MM
        m = re.match(r"^(\d{1,2})[/-](\d{1,2})(?:[/-]\d{4})?\s+(\d{1,2}):(\d{1,2})$", time_str.strip())
        if m:
            base = now.replace(day=int(m.group(1)), month=int(m.group(2)), hour=int(m.group(3)), minute=int(m.group(4)), second=0, microsecond=0)
            return (base + timedelta(minutes=offset_minutes)).strftime("%d/%m %H:%M").replace("/0", "/")
    except Exception:
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
    out({"status": "OK", "error_code": "NONE", "payload": {"agenda": items}})

def cmd_send_pending(msg_id: str):
    """Triggered by cron or manually. Only deletes on success."""
    agenda = load_agenda()
    if msg_id not in agenda:
        out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "ID_NOT_FOUND", "id": msg_id}})
        sys.exit(0)

    data = agenda[msg_id]
    chat_id   = data["chatId"]
    file_path = data.get("file_path")
    message   = data.get("message", "")

    # ── Delivery window check ──────────────────────────────────────────────
    if not is_within_window(data.get("time", "")):
        out({"status": "DENY", "error_code": "TIMEOUT", "payload": {"error": "DELIVERY_WINDOW_EXPIRED", "id": msg_id, "scheduled": data.get("time"), "window_minutes": DELIVERY_WINDOW_MINUTES}})
        sys.exit(0)

    # ── Actual send ────────────────────────────────────────────────────────
    success = False
    if file_path:
        fpath = Path(file_path)
        if not fpath.exists():
            out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "FILE_NOT_FOUND", "path": file_path}})
            sys.exit(0)

        from files import cmd_enviar
        try:
            cmd_enviar(str(fpath), chat_id, is_voice=data.get("is_voice", False), caption=message)
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
        def do_delete(ag):
            if msg_id in ag:
                del ag[msg_id]
                return True
            return False
        locked_update_agenda(do_delete)

        # Try to remove the native cron job silently
        try:
            res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if res.returncode == 0:
                crons = [line for line in res.stdout.splitlines() if f"ANDORINA_AGENDA:{msg_id}" not in line]
                crons_str = "\n".join(crons) + "\n" if crons else "\n"
                subprocess.run(["crontab", "-"], input=crons_str, text=True, check=True)
        except Exception:
            pass

        out({"status": "OK", "error_code": "NONE", "payload": {"delivered": True, "id": msg_id}})
    else:
        out({"status": "ERROR", "error_code": "FATAL", "payload": {"error": "SEND_FAILED", "id": msg_id, "note": "Message kept in agenda for retry within delivery window."}})
        sys.exit(0)

def cmd_remove(msg_id: str, creator_jid: str = None):
    agenda = load_agenda()
    if msg_id not in agenda:
        out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "ID_NOT_FOUND"}})
        return
        
    if creator_jid:
        task_creator = agenda[msg_id].get("created_by")
        if task_creator and task_creator != creator_jid:
            out({"status": "DENY", "error_code": "PERMISSION_DENIED", "payload": {"message": "You can only remove tasks created by yourself."}})
            return

    def do_remove(ag):
        if msg_id in ag:
            del ag[msg_id]
            return True
        return False
        
    locked_update_agenda(do_remove)

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
    out({"status": "OK", "error_code": "NONE", "payload": {"message": f"Cancelled: {msg_id}"}})


def cmd_auto_schedule(chat_id: str, time_str: str, message: str,
                      file_path=None, is_voice: bool = False, creator_jid: str = None):
    if not (chat_id.endswith("@s.whatsapp.net") or chat_id.endswith("@g.us")):
        out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "INVALID_CHAT_ID"}})
        sys.exit(0)

    final_time = None
    cron_expr = None
    msg_id = None
    success = False
    error_msg = None

    # ── Calculate slot, ID, and persist INSIDE the lock ───────────────────
    def do_schedule(ag):
        nonlocal final_time, cron_expr, msg_id, success, error_msg
        
        final_time = get_next_free_slot(time_str, ag)
        cron_expr = parse_cron_schedule(final_time)
        if cron_expr == "INVALID_FORMAT":
            error_msg = "INVALID_TIME_FORMAT"
            return False

        # Ensure unique ID even if called in the same millisecond
        msg_id = f"msg_{datetime.now().strftime('%H%M%S%f')[:-3]}"
        while msg_id in ag:
            time.sleep(0.001)
            msg_id = f"msg_{datetime.now().strftime('%H%M%S%f')[:-3]}"

        ag[msg_id] = {
            "chatId": chat_id,
            "name": chat_id.split("@")[0],
            "time": final_time,
            "scheduled_original": time_str,
            "message": message,
            "file_path": str(Path(file_path).absolute()) if file_path else None,
            "is_voice": is_voice,
            "created_at": datetime.now().isoformat(),
            "created_by": creator_jid
        }
        success = True
        return True

    locked_update_agenda(do_schedule)

    if not success:
        out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": error_msg}})
        sys.exit(0)

    if final_time != time_str:
        print(f"ℹ️  Auto-offset applied: {time_str} → {final_time} "
              f"(collision avoidance)", file=sys.stderr)
    hermes_cmd = os.environ.get("HERMES_CMD", HERMES_HOME.name.lstrip(".") or "hermes")
    env_prefix = f"HERMES_HOME='{HERMES_HOME}' HERMES_CMD='{hermes_cmd}'"
    cmd_str = f"{env_prefix} python3 '{SCRIPTS_DIR}/tools/agenda.py' send {msg_id} >/dev/null 2>&1 # ANDORINA_AGENDA:{msg_id}"
    try:
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        current_crons = res.stdout if res.returncode == 0 else ""
        new_cron = f"{cron_expr} {cmd_str}\n"
        subprocess.run(["crontab", "-"], input=current_crons + new_cron, text=True, check=True)
        out({"status": "OK", "error_code": "NONE", "payload": {"id": msg_id, "time_requested": time_str, "time_scheduled": final_time, "offset_applied": final_time != time_str}})
    except Exception as e:
        out({"status": "ERROR", "error_code": "INTERNAL_ERROR", "payload": {"error": "CRON_FAILED", "detail": str(e)}})

# ─────────────── Recurring Tasks ────────────────────────────────────────────────
def get_recurring_dir():
    rdir = HERMES_BASE / "state" / "recurring"
    rdir.mkdir(parents=True, exist_ok=True)
    return rdir

def cmd_recurring_add(chat_id: str, cron_expr: str, message: str, file_path: str = None, creator_jid: str = None):
    if not (chat_id.endswith("@s.whatsapp.net") or chat_id.endswith("@g.us")):
        out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "INVALID_CHAT_ID"}})
        sys.exit(0)
    
    rec_id = f"rec_{datetime.now().strftime('%H%M%S%f')[:-3]}"
    rdir = get_recurring_dir()
    
    # Check existing crons and offset if necessary
    existing_crons = set()
    for f in rdir.glob("rec_*.json"):
        try:
            d = read_json_safe(f, default={})
            if d.get("cron"): existing_crons.add(d["cron"])
        except: pass
        
    original_cron = cron_expr
    offset = 0
    while cron_expr in existing_crons and offset < 60:
        offset += CRON_OFFSET_MINUTES
        parts = original_cron.split(" ")
        if len(parts) == 5 and parts[0].isdigit():
            m = int(parts[0]) + offset
            h_str = parts[1]
            if m >= 60 and h_str.isdigit():
                h = (int(h_str) + (m // 60)) % 24
                m = m % 60
                parts[1] = str(h)
            elif m >= 60:
                m = 59 # Cap if we can't parse hours
            parts[0] = str(m)
            cron_expr = " ".join(parts)
        else:
            break
            
    task_file = rdir / f"{rec_id}.json"
    
    task_data = {
        "id": rec_id,
        "chatId": chat_id,
        "cron": cron_expr,
        "message": message,
        "file_path": str(Path(file_path).absolute()) if file_path else None,
        "created_at": datetime.now().isoformat(),
        "created_by": creator_jid
    }
    
    write_json_safe(task_file, task_data)
    
    hermes_cmd = os.environ.get("HERMES_CMD", HERMES_HOME.name.lstrip(".") or "hermes")
    env_prefix = f"HERMES_HOME='{HERMES_HOME}' HERMES_CMD='{hermes_cmd}'"
    chat_id_esc = shlex.quote(chat_id)
    msg_esc = shlex.quote(message)
    script_esc = shlex.quote(str(SCRIPTS_DIR / 'transport' / 'send.py'))
    
    cmd_args = f"message {chat_id_esc} {msg_esc}"
    if file_path:
        cmd_args += f" --file {shlex.quote(str(Path(file_path).absolute()))}"
        
    cmd_str = f"{env_prefix} python3 {script_esc} {cmd_args} >/dev/null 2>&1 # ANDORINA_RECURRING:{rec_id}"
    
    try:
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        current_crons = res.stdout if res.returncode == 0 else ""
        new_cron = f"{cron_expr} {cmd_str}\n"
        subprocess.run(["crontab", "-"], input=current_crons + new_cron, text=True, check=True)
        out({"status": "OK", "error_code": "NONE", "payload": {"id": rec_id, "message": "Recurring task added."}})
    except Exception as e:
        task_file.unlink(missing_ok=True)
        out({"status": "ERROR", "error_code": "INTERNAL_ERROR", "payload": {"error": "CRON_FAILED", "detail": str(e)}})

def cmd_recurring_list():
    rdir = get_recurring_dir()
    tasks = []
    for f in rdir.glob("rec_*.json"):
        try:
            data = read_json_safe(f, default={})
            if data: tasks.append(data)
        except Exception: pass
    out({"status": "OK", "error_code": "NONE", "payload": {"recurring_tasks": tasks}})

def cmd_recurring_remove(rec_id: str, creator_jid: str = None):
    rdir = get_recurring_dir()
    task_file = rdir / f"{rec_id}.json"
    if task_file.exists():
        try:
            task_data = read_json_safe(task_file, default={})
            if creator_jid and task_data.get("created_by") and task_data.get("created_by") != creator_jid:
                out({"status": "DENY", "error_code": "PERMISSION_DENIED", "payload": {"message": "You can only remove tasks created by yourself."}})
                return
        except Exception:
            pass
        task_file.unlink()
    
    try:
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if res.returncode == 0:
            crons = [line for line in res.stdout.splitlines() if f"ANDORINA_RECURRING:{rec_id}" not in line]
            crons_str = "\n".join(crons) + "\n" if crons else "\n"
            subprocess.run(["crontab", "-"], input=crons_str, text=True, check=True)
    except Exception: pass
    
    out({"status": "OK", "error_code": "NONE", "payload": {"message": f"Cancelled recurring task: {rec_id}"}})


def cmd_cleanup_crons():
    """Remove stale ANDORINA_AGENDA and ANDORINA_RECURRING crontab entries.
    Checks:
      1. If the python3 script path does not exist on disk.
      2. If the message ID (for AGENDA) is no longer in agenda.json.
      3. If the recurring ID (for RECURRING) no longer exists as a JSON file.
    """
    try:
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if res.returncode != 0:
            out({"status": "OK", "error_code": "NONE",
                 "payload": {"removed": 0, "message": "No crontab found."}})
            return

        # Load active agenda and recurring directory
        agenda = load_agenda()
        rdir = get_recurring_dir()

        lines = res.stdout.splitlines()
        cleaned, removed = [], []
        for line in lines:
            stripped = line.strip()
            
            # Check if this is an Andorina cron entry
            is_agenda = "ANDORINA_AGENDA:" in stripped
            is_recurring = "ANDORINA_RECURRING:" in stripped
            
            if not is_agenda and not is_recurring:
                cleaned.append(line)
                continue
                
            # Extract script path
            m = re.search(r"python3 '([^']+)'", stripped)
            if not m:
                # Try search without single quotes in case format is slightly different
                m = re.search(r"python3 (\S+)", stripped)
                
            if not m:
                removed.append(stripped)
                continue
                
            script_path = m.group(1).strip("'\"")
            if not Path(script_path).exists():
                removed.append(stripped)
                continue
                
            # Now verify if the task still exists in the active state
            if is_agenda:
                m_id = None
                idx = stripped.find("ANDORINA_AGENDA:")
                if idx != -1:
                    m_id = stripped[idx + len("ANDORINA_AGENDA:"):].split()[0]
                if not m_id or m_id not in agenda:
                    removed.append(stripped)
                    continue
                    
            elif is_recurring:
                r_id = None
                idx = stripped.find("ANDORINA_RECURRING:")
                if idx != -1:
                    r_id = stripped[idx + len("ANDORINA_RECURRING:"):].split()[0]
                if not r_id or not (rdir / f"{r_id}.json").exists():
                    removed.append(stripped)
                    continue
                    
            cleaned.append(line)

        new_crontab = "\n".join(cleaned) + "\n" if cleaned else "\n"
        subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)
        out({"status": "OK", "error_code": "NONE", "payload": {
            "removed": len(removed),
            "message": f"Removed {len(removed)} stale cron entries.",
            "removed_entries": removed
        }})
    except Exception as e:
        out({"status": "ERROR", "error_code": "INTERNAL_ERROR",
             "payload": {"error": str(e)}})


def parse_creator_jid():
    if "--creator-jid" in sys.argv:
        idx = sys.argv.index("--creator-jid")
        if idx + 1 < len(sys.argv):
            jid = sys.argv[idx+1]
            sys.argv = sys.argv[:idx] + sys.argv[idx+2:]
            return jid
    return None

# ─────────────── Entry point ──────────────────────────────────────────────────
if __name__ == "__main__":
    load_env_config()
    creator_jid = parse_creator_jid()

    if len(sys.argv) < 2:
        print("Usage: agenda.py [list|send|remove|auto-schedule|recurring]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        cmd_list()

    elif cmd == "cleanup-crons":
        cmd_cleanup_crons()

    elif cmd == "send" and len(sys.argv) > 2:
        cmd_send_pending(sys.argv[2])

    elif cmd == "remove" and len(sys.argv) > 2:
        cmd_remove(sys.argv[2], creator_jid)

    elif cmd == "auto-schedule" and len(sys.argv) > 4:
        chat_id  = sys.argv[2]
        time_str = sys.argv[3]
        is_voice = "--voice" in sys.argv
        args     = [a for a in sys.argv[4:] if a != "--voice"]

        file_path = None
        message   = ""

        if args and args[0] and Path(args[0]).exists():
            file_path = args[0]
            message   = " ".join(args[1:]) if len(args) > 1 else ""
        else:
            message = " ".join(args)

        cmd_auto_schedule(chat_id, time_str, message, file_path, is_voice, creator_jid)

    elif cmd == "recurring":
        if len(sys.argv) < 3:
            out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "MISSING_ARGUMENTS", "usage": "agenda.py recurring [add|list|remove]"}})
            sys.exit(1)
        
        subcmd = sys.argv[2]
        if subcmd == "list":
            cmd_recurring_list()
        elif subcmd == "remove" and len(sys.argv) > 3:
            cmd_recurring_remove(sys.argv[3], creator_jid)
        elif subcmd == "add" and len(sys.argv) > 5:
            # agenda.py recurring add "CHAT_ID" "CRON" ["/path/to/file"] "Message"
            chat_id = sys.argv[3]
            cron_expr = sys.argv[4]
            args = sys.argv[5:]
            file_path = None
            message = ""
            if args and args[0] and Path(args[0]).exists():
                file_path = args[0]
                message = " ".join(args[1:]) if len(args) > 1 else ""
            else:
                message = " ".join(args)
            cmd_recurring_add(chat_id, cron_expr, message, file_path, creator_jid)
        else:
            out({"status": "DENY", "error_code": "INVALID_ARGS", "payload": {"error": "INVALID_RECURRING_COMMAND"}})
            sys.exit(1)
            
    else:
        print("Invalid command or missing arguments.")
        sys.exit(1)
