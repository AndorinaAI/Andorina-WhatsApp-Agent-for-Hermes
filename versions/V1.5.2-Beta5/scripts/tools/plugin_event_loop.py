import sys
import time
import sqlite3
import json
from pathlib import Path

# Fix relative import to reach scripts/common.py
sys.path.append(str(Path(__file__).parent.parent))
from security.plugin_router import load_plugin

STATE_DIR = Path(__file__).parent.parent.parent / "state"
SOULS_DIR = STATE_DIR / "souls"

def process_plugin_events(plugin_name: str):
    plugin = load_plugin(plugin_name)
    if not plugin:
        return
        
    sdk = plugin["sdk"]
    conn = sdk.db
    c = conn.cursor()
    
    try:
        now = int(time.time())
        c.execute("SELECT id, jid, event_type, payload FROM events WHERE status = 'pending' AND trigger_at <= ?", (now,))
        events = c.fetchall()
        
        for row in events:
            event_id, jid, event_type, payload_str = row
            payload = json.loads(payload_str) if payload_str else {}
            
            try:
                plugin["tools"].on_event(sdk, event_type, payload)
                # Marcar como fired
                c.execute("UPDATE events SET status = 'fired' WHERE id = ?", (event_id,))
            except Exception as e:
                sdk.log(f"Error executing event {event_id} ({event_type}): {e}")
                # Marcar como failed
                c.execute("UPDATE events SET status = 'failed' WHERE id = ?", (event_id,))
                
        conn.commit()
    except sqlite3.OperationalError:
        # Tabla events no existe, ignorar
        pass
    finally:
        conn.close()

def main():
    if not SOULS_DIR.exists():
        return
        
    for plugin_dir in SOULS_DIR.iterdir():
        if plugin_dir.is_dir() and (plugin_dir / "plugin.json").exists():
            process_plugin_events(plugin_dir.name)

if __name__ == "__main__":
    main()
