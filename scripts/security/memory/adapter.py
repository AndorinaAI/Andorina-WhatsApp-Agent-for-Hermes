"""
adapter.py — Plugin lifecycle adapter (thin wrapper).

The real plugin entry point is __init__.py at the plugin root.
This module provides the AndorinaPlugin class for programmatic use
(e.g., GUI server, tests) and delegates to the existing scripts
via subprocess.
"""

import sys
from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent.parent.parent  # scripts/security/memory → scripts → root
sys.path.insert(0, str(_PLUGIN_DIR))

try:
    from __init__ import _run_script, _run_hook, _ensure_state
except ImportError:
    def _run_script(*a, **kw): return {"ok": False, "error": "entry point not loaded"}
    def _run_hook(*a, **kw): return {}
    def _ensure_state(*a, **kw): pass


class AndorinaPlugin:
    """Programmatic access to Andoriña plugin functionality."""
    
    name: str = "andorina"
    version: str = "2.0.0-alpha"
    kind: str = "tool"
    
    def __init__(self):
        self._scripts_dir = _PLUGIN_DIR / "scripts"
        self._state_dir = _PLUGIN_DIR / "state"
        _ensure_state()
    
    # Thin wrappers — all logic lives in __init__.py and the scripts
    def send_text(self, chat_id, message): return _run_script("transport/send.py", "message", chat_id, message)
    def send_file(self, chat_id, file_path, voice=False):
        args = [file_path, chat_id]
        if voice: args.append("--voice")
        return _run_script("tools/files.py", *args)
    def broadcast(self, message, jids): return _run_script("transport/send.py", "broadcast", message, jids)
    def read_inbox(self, chat_id=None, limit="50"):
        return _run_script("tools/inbox.py", "read", chat_id, limit) if chat_id else _run_script("tools/inbox.py", "list")
    def search_contacts(self, query): return _run_script("tools/contacts.py", "search", query)
    def list_groups(self): return _run_script("tools/contacts.py", "groups")
    def schedule_msg(self, chat_id, time_str, message): return _run_script("tools/agenda.py", "auto-schedule", chat_id, time_str, message)
    def add_note(self, jid, text): return _run_script("tools/contacts.py", "note-add", jid, text)
    def add_alert(self, source, target, keywords=None):
        args = ["add", source, target]
        if keywords: args.extend(["--keywords", keywords])
        return _run_script("tools/alerts.py", *args)
    def manage_role(self, action, jid, role=None):
        args = ["role", action, jid]
        if role: args.append(role)
        return _run_script("utils/admin_cli.py", *args)
    def manage_soul(self, action, jid, text=None):
        args = ["soul", action, jid]
        if text: args.append(text)
        return _run_script("utils/admin_cli.py", *args)
