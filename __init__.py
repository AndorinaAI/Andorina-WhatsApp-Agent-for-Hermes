"""
Andoriña V2.0 — WhatsApp Enhancement Plugin for Hermes Agent.

Entry point for the Hermes plugin system. Called by PluginManager
when this plugin is discovered in ~/.hermes/plugins/andorina/.

Registers hooks (pre_llm_call, pre_tool_call, post_llm_call) and
tools (send_text, send_file, broadcast, read_inbox, search_contacts,
list_groups, schedule_msg, add_note, add_alert, manage_role, manage_soul).
"""

import sys
import os
import subprocess
import json
from pathlib import Path

_PLUGIN_DIR = Path(__file__).parent.absolute()
_SCRIPTS_DIR = _PLUGIN_DIR / "scripts"
_STATE_DIR = _PLUGIN_DIR / "state"


def _ensure_state():
    """Create state directories if they don't exist."""
    for d in ["souls", "notes", "recurring"]:
        (_STATE_DIR / d).mkdir(parents=True, exist_ok=True)


def _run_script(script: str, *args) -> str:
    """Execute an Andoriña script and return JSON-encoded result string."""
    script_path = _SCRIPTS_DIR / script
    if not script_path.exists():
        return json.dumps({"ok": False, "error": f"Script not found: {script}"}, ensure_ascii=False)
    try:
        env = os.environ.copy()
        env["HERMES_HOME"] = env.get("HERMES_HOME", str(Path.home() / ".hermes"))
        cmd = [sys.executable, str(script_path)] + list(args)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        try:
            result = json.loads(r.stdout) if r.stdout.strip() else {"ok": r.returncode == 0}
            return json.dumps(result, ensure_ascii=False)
        except json.JSONDecodeError:
            result = {"ok": r.returncode == 0, "raw": r.stdout.strip()[:500]}
            return json.dumps(result, ensure_ascii=False)
    except subprocess.TimeoutExpired:
        return json.dumps({"ok": False, "error": "Timeout"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)


def _adapt_handler(fn):
    """Adapt a handler expecting keyword args to Hermes' args_dict positional contract.
    
    Hermes v0.21.2 dispatches as ``entry.handler(args_dict, **kwargs)`` where
    ``args_dict`` is the tool's parameters dict. This wrapper unpacks it into
    keyword arguments matching the original handler signatures.
    """
    def wrapper(args=None, **kw):
        if args is None:
            args = {}
        if isinstance(args, dict):
            return fn(**args, **kw)
        return fn(args, **kw)
    wrapper.__name__ = fn.__name__
    wrapper.__qualname__ = fn.__qualname__
    return wrapper


def register(ctx):
    """
    Register hooks and tools with the Hermes plugin context.

    This is the canonical entry point called by PluginManager when
    the plugin is discovered. It registers:
    - 3 hooks: pre_llm_call, pre_tool_call, post_llm_call
    - 11 tools: send_text, send_file, broadcast, read_inbox,
      search_contacts, list_groups, schedule_msg, add_note,
      add_alert, manage_role, manage_soul
    """
    _ensure_state()

    # ── Register hooks ──────────────────────────────────────
    # Each hook delegates to orchestrator_hook.py via subprocess,
    # passing the Hermes hook payload as JSON via stdin.
    # orchestrator_hook.py reads sys.stdin.read() and outputs JSON to stdout.

    def _run_hook(event: str, kwargs: dict) -> dict:
        """Execute orchestrator_hook.py, piping hook event + kwargs as JSON to stdin."""
        script = _SCRIPTS_DIR / "security" / "orchestrator_hook.py"
        if not script.exists():
            return {}
        try:
            env = os.environ.copy()
            env["HERMES_HOME"] = env.get("HERMES_HOME", str(Path.home() / ".hermes"))
            proc = subprocess.run(
                [sys.executable, str(script)],
                input=json.dumps({"hook_event_name": event, **kwargs}),
                capture_output=True, text=True, timeout=30, env=env
            )
            try:
                return json.loads(proc.stdout) if proc.stdout.strip() else {}
            except json.JSONDecodeError:
                return {}
        except Exception:
            return {}

    def _hook_pre_llm(**kwargs):
        return _run_hook("pre_llm_call", kwargs)

    def _hook_pre_tool(**kwargs):
        return _run_hook("pre_tool_call", kwargs)

    def _hook_post_llm(**kwargs):
        return _run_hook("post_llm_call", kwargs)

    ctx.register_hook("pre_llm_call", _hook_pre_llm)
    ctx.register_hook("pre_tool_call", _hook_pre_tool)
    ctx.register_hook("post_llm_call", _hook_post_llm)


    # ── Tool schemas (Hermes v0.21.2 API) ────────────────────

    _S = lambda name, desc, props, req=None: {
        "name": name, "description": desc,
        "parameters": {"type": "object", "properties": props, "required": list(req or props.keys())}
    }
    _STR = lambda d: {"type": "string", "description": d}

    _SEND_TEXT_SCHEMA = _S("send_text", "Send a text message to a WhatsApp chat or group",
        {"chat_id": _STR("WhatsApp JID (e.g. 34600000000@s.whatsapp.net or group @g.us)"),
         "message": _STR("Message text to send")})

    _SEND_FILE_SCHEMA = _S("send_file", "Send a file (image, document, audio) to a WhatsApp chat",
        {"chat_id": _STR("WhatsApp JID"), "file_path": _STR("Absolute path to the file"),
         "voice": {"type": "boolean", "description": "Send as voice note (PTT)"}}, ["chat_id", "file_path"])

    _BROADCAST_SCHEMA = _S("broadcast", "Send a text message to multiple recipients",
        {"message": _STR("Message text"), "jids": _STR("Comma-separated JIDs")})

    _READ_INBOX_SCHEMA = _S("read_inbox", "Read recent messages from the WhatsApp inbox",
        {"chat_id": _STR("Filter by chat JID (optional)"), "limit": _STR("Max messages to return (default 50)")}, [])

    _SEARCH_CONTACTS_SCHEMA = _S("search_contacts", "Search Google Contacts by name or phone",
        {"query": _STR("Name, phone, or partial match")})

    _LIST_GROUPS_SCHEMA = _S("list_groups", "List all WhatsApp groups the bot belongs to", {}, [])

    _SCHEDULE_MSG_SCHEMA = _S("schedule_msg", "Schedule a message to be sent at a specific time",
        {"chat_id": _STR("WhatsApp JID"), "time_str": _STR("Time in HH:MM format"),
         "message": _STR("Message text to send")})

    _ADD_NOTE_SCHEMA = _S("add_note", "Save a persistent text note about a contact",
        {"jid": _STR("Contact JID or phone number"), "text": _STR("Note content")})

    _ADD_ALERT_SCHEMA = _S("add_alert", "Create a semantic alert rule for WhatsApp messages",
        {"source": _STR("Source JID to monitor"), "target": _STR("Target JID to notify"),
         "keywords": _STR("Optional comma-separated trigger keywords")}, ["source", "target"])

    _MANAGE_ROLE_SCHEMA = _S("manage_role", "Assign or remove a user role (owner, manager, chatbot, blocked)",
        {"action": _STR("set, get, remove, or list"), "jid": _STR("WhatsApp JID"),
         "role": _STR("Role name (for set action)")}, ["action", "jid"])

    _MANAGE_SOUL_SCHEMA = _S("manage_soul", "Set or get a custom personality (sub-soul) for a contact",
        {"action": _STR("set or get"), "jid": _STR("WhatsApp JID"),
         "text": _STR("Personality description (for set action)")}, ["action", "jid"])

    # ── Register tools ──────────────────────────────────────
    # Each tool delegates to the corresponding Andoriña script.

    def _tool_send_text(chat_id: str, message: str, **kw):
        return _run_script("transport/send.py", "message", chat_id, message)

    def _tool_send_file(chat_id: str, file_path: str, **kw):
        args = [file_path, chat_id]
        if kw.get("voice"):
            args.append("--voice")
        return _run_script("tools/files.py", *args)

    def _tool_broadcast(message: str, jids: str, **kw):
        return _run_script("transport/send.py", "broadcast", message, jids)

    def _tool_read_inbox(chat_id: str = None, limit: str = "50", **kw):
        if chat_id:
            return _run_script("tools/inbox.py", "read", chat_id, limit)
        return _run_script("tools/inbox.py", "list")

    def _tool_search_contacts(query: str, **kw):
        return _run_script("tools/contacts.py", "search", query)

    def _tool_list_groups(**kw):
        return _run_script("tools/contacts.py", "groups")

    def _tool_schedule_msg(chat_id: str, time_str: str, message: str, **kw):
        return _run_script("tools/agenda.py", "auto-schedule", chat_id, time_str, message)

    def _tool_add_note(jid: str, text: str, **kw):
        return _run_script("tools/contacts.py", "note-add", jid, text)

    def _tool_add_alert(source: str, target: str, **kw):
        args = ["add", source, target]
        if kw.get("keywords"):
            args.extend(["--keywords", kw["keywords"]])
        return _run_script("tools/alerts.py", *args)

    def _tool_manage_role(action: str, jid: str, **kw):
        args = ["role", action, jid]
        if kw.get("role"):
            args.append(kw["role"])
        return _run_script("utils/admin_cli.py", *args)

    def _tool_manage_soul(action: str, jid: str, **kw):
        args = ["soul", action, jid]
        if kw.get("text"):
            args.append(kw["text"])
        return _run_script("utils/admin_cli.py", *args)

    ctx.register_tool(name="send_text", toolset="andorina", schema=_SEND_TEXT_SCHEMA, handler=_adapt_handler(_tool_send_text))
    ctx.register_tool(name="send_file", toolset="andorina", schema=_SEND_FILE_SCHEMA, handler=_adapt_handler(_tool_send_file))
    ctx.register_tool(name="broadcast", toolset="andorina", schema=_BROADCAST_SCHEMA, handler=_adapt_handler(_tool_broadcast))
    ctx.register_tool(name="read_inbox", toolset="andorina", schema=_READ_INBOX_SCHEMA, handler=_adapt_handler(_tool_read_inbox))
    ctx.register_tool(name="search_contacts", toolset="andorina", schema=_SEARCH_CONTACTS_SCHEMA, handler=_adapt_handler(_tool_search_contacts))
    ctx.register_tool(name="list_groups", toolset="andorina", schema=_LIST_GROUPS_SCHEMA, handler=_adapt_handler(_tool_list_groups))
    ctx.register_tool(name="schedule_msg", toolset="andorina", schema=_SCHEDULE_MSG_SCHEMA, handler=_adapt_handler(_tool_schedule_msg))
    ctx.register_tool(name="add_note", toolset="andorina", schema=_ADD_NOTE_SCHEMA, handler=_adapt_handler(_tool_add_note))
    ctx.register_tool(name="add_alert", toolset="andorina", schema=_ADD_ALERT_SCHEMA, handler=_adapt_handler(_tool_add_alert))
    ctx.register_tool(name="manage_role", toolset="andorina", schema=_MANAGE_ROLE_SCHEMA, handler=_adapt_handler(_tool_manage_role))
    ctx.register_tool(name="manage_soul", toolset="andorina", schema=_MANAGE_SOUL_SCHEMA, handler=_adapt_handler(_tool_manage_soul))
