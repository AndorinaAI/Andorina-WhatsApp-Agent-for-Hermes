import sys
import sqlite3
import json
from pathlib import Path

# Fix relative import to reach scripts/common.py
sys.path.append(str(Path(__file__).parent.parent))
from common import post_json

class PluginPermissionError(Exception):
    pass

class PluginSDK:
    def __init__(self, plugin_dir: Path, plugin_id: str, permissions: dict):
        self.plugin_dir = plugin_dir
        self.plugin_id = plugin_id
        self.permissions = permissions
        self.db_path = self.plugin_dir / "state.db"
        
    @property
    def db(self):
        """Devuelve una conexión SQLite al state.db del plugin."""
        return sqlite3.connect(str(self.db_path))

    def check_permission(self, perm: str):
        if not self.permissions.get(perm, False):
            raise PluginPermissionError(f"Plugin {self.plugin_id} lacks permission: {perm}")

    def send_message(self, jid: str, text: str):
        self.check_permission("can_send_proactive_messages")
        res, err = post_json("/send", {"chatId": jid, "message": text})
        return res and res.get("success", False)

    def send_image(self, jid: str, path: str, caption: str = ""):
        self.check_permission("can_send_proactive_messages")
        # Invocar la tool the files internamente
        from tools.files import cmd_enviar
        try:
            cmd_enviar(path, jid, is_voice=False, caption=caption)
            return True
        except Exception as e:
            self.log(f"Error sending image: {e}")
            return False

    def schedule_event(self, jid: str, delay_minutes: int, event_type: str, payload: dict):
        self.check_permission("can_schedule_events")
        max_delay = self.permissions.get("max_event_delay_seconds", 86400) // 60
        if delay_minutes > max_delay:
            raise ValueError(f"Delay {delay_minutes}m exceeds max {max_delay}m")
        
        # En la V2.0 guardaremos el evento en agenda.py o en events del propio plugin.
        # Por ahora lo metemos en la tabla events de la db del plugin
        import time
        trigger_at = int(time.time()) + (delay_minutes * 60)
        import uuid
        event_id = str(uuid.uuid4())
        
        conn = self.db
        c = conn.cursor()
        try:
            c.execute("INSERT INTO events (id, jid, trigger_at, event_type, payload, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (event_id, jid, trigger_at, event_type, json.dumps(payload), 'pending'))
            conn.commit()
        except sqlite3.OperationalError:
            # Si no existe la tabla, la creamos al vuelo
            c.execute('''CREATE TABLE events (
                            id TEXT PRIMARY KEY,
                            jid TEXT NOT NULL,
                            trigger_at INTEGER NOT NULL,
                            event_type TEXT NOT NULL,
                            payload TEXT,
                            status TEXT DEFAULT 'pending'
                         )''')
            c.execute("INSERT INTO events (id, jid, trigger_at, event_type, payload, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (event_id, jid, trigger_at, event_type, json.dumps(payload), 'pending'))
            conn.commit()
        finally:
            conn.close()
        return event_id

    def cancel_event(self, event_id: str):
        self.check_permission("can_schedule_events")
        conn = self.db
        c = conn.cursor()
        c.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()

    def log(self, message: str):
        log_file = self.plugin_dir / "plugin.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{self.plugin_id}] {message}\n")

    def get_player_state(self, jid: str) -> dict:
        conn = self.db
        c = conn.cursor()
        try:
            c.execute("SELECT phase, blocked_until, block_reason, extra_data FROM game_state WHERE jid = ?", (jid,))
            row = c.fetchone()
            if row:
                return {
                    "phase": row[0],
                    "blocked_until": row[1],
                    "block_reason": row[2],
                    "extra_data": json.loads(row[3]) if row[3] else {}
                }
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()
        return {}

    def set_player_state(self, jid: str, phase: str = None, extra_data: dict = None):
        conn = self.db
        c = conn.cursor()
        try:
            # Upsert
            c.execute("SELECT 1 FROM game_state WHERE jid = ?", (jid,))
            if c.fetchone():
                if phase is not None:
                    c.execute("UPDATE game_state SET phase = ? WHERE jid = ?", (phase, jid))
                if extra_data is not None:
                    c.execute("UPDATE game_state SET extra_data = ? WHERE jid = ?", (json.dumps(extra_data), jid))
            else:
                p = phase or 'intro'
                ed = json.dumps(extra_data) if extra_data is not None else '{}'
                c.execute("INSERT INTO game_state (jid, phase, blocked_until, block_reason, extra_data) VALUES (?, ?, 0, '', ?)",
                          (jid, p, ed))
            conn.commit()
        except sqlite3.OperationalError:
            c.execute('''CREATE TABLE game_state (
                            jid TEXT PRIMARY KEY,
                            phase TEXT DEFAULT 'intro',
                            blocked_until INTEGER DEFAULT 0,
                            block_reason TEXT DEFAULT '',
                            extra_data TEXT DEFAULT '{}'
                         )''')
            p = phase or 'intro'
            ed = json.dumps(extra_data) if extra_data is not None else '{}'
            c.execute("INSERT INTO game_state (jid, phase, blocked_until, block_reason, extra_data) VALUES (?, ?, 0, '', ?)",
                      (jid, p, ed))
            conn.commit()
        finally:
            conn.close()
