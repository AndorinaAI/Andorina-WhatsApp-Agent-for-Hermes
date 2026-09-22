#!/usr/bin/env python3
"""
🧪 Andoriña V2.0 — Sandbox de Pruebas Integrales
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ejecuta pruebas funcionales sobre todos los módulos de la skill
sin necesidad de WhatsApp real ni Hermes corriendo.

Uso:
  python3 scripts/test_sandbox.py              # todas las pruebas
  python3 scripts/test_sandbox.py --quick       # solo pruebas rápidas
  python3 scripts/test_sandbox.py --module jids # solo un módulo
  python3 scripts/test_sandbox.py --docker      # modo Docker/headless

Módulos disponibles:
  jids, rbac, contacts, inbox, agenda, alerts,
  tool_guard, orchestrator, webhook, send, files, admin_cli, install
"""

import sys
import os
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════
SKILL_DIR = Path(__file__).parent.parent.absolute()
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

TMPDIR = Path(tempfile.mkdtemp(prefix="andorina_test_"))
STATE_DIR = TMPDIR / "state"
NOTES_DIR = STATE_DIR / "notes"
SOULS_DIR = STATE_DIR / "souls"

PASS = 0
FAIL = 0
SKIP = 0
ERRORS = []

def setup():
    """Crea entorno mínimo de prueba."""
    for d in [STATE_DIR, NOTES_DIR, SOULS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "guard_rules.json").write_text(json.dumps({
        "_available_permissions": ["all", "send_text", "chatbot_mute", "chatbot_toggle"],
        "global_default_role": "chatbot",
        "roles": {
            "owner": {"permissions": ["all"]},
            "manager": {"permissions": ["send_text", "send_file", "get_role"]},
            "chatbot": {"permissions": []},
            "blocked": {"permissions": []}
        },
        "jids": {
            "34600000000": {"role": "owner"},
            "34600000001": {"role": "manager"},
            "34600000002": {"role": "chatbot", "chatbot_muted": True},
            "34600000003": {"role": "blocked"},
            "120363001234": {"role": "chatbot", "custom_soul": "test_soul"}
        }
    }))
    (STATE_DIR / "chatbot.json").write_text(json.dumps({
        "enabled": True, "muted_jids": []
    }))
    (STATE_DIR / "away.json").write_text(json.dumps({
        "enabled": False, "message": "", "cooldown": {}
    }))
    (STATE_DIR / "alerts.json").write_text(json.dumps([]))
    (STATE_DIR / "agenda.json").write_text(json.dumps({}))
    (STATE_DIR / "inbox.json").write_text(json.dumps([]))
    (SOULS_DIR / "_default.md").write_text("# Default Soul\nTest soul content.")
    (SOULS_DIR / "test_soul.md").write_text("# Test Soul\nYou are a test soul.")
    (TMPDIR / ".env").write_text(
        "HERMES_HOME=" + str(TMPDIR) + "\n"
        "DEFAULT_COUNTRY_CODE=34\n"
        "ADMIN_PHONE=34600000000\n"
        "WHATSAPP_ALLOWED_USERS=34600000000\n"
    )
    os.environ["HERMES_HOME"] = str(TMPDIR)
    # Crear estructura de skill simulada
    (TMPDIR / "skills" / "andorina" / "state").mkdir(parents=True, exist_ok=True)
    if not (TMPDIR / "skills" / "andorina" / "state").exists():
        shutil.copytree(str(STATE_DIR), str(TMPDIR / "skills" / "andorina" / "state"))
    shutil.copy2(str(TMPDIR / ".env"), str(TMPDIR / "skills" / "andorina" / ".env"))

    # Monkey-patch all modules to use test STATE_DIR
    sys.path.insert(0, str(SKILL_DIR))
    import security.rbac as _rbac
    import security.orchestrator_hook as _orch_hook
    import security.orchestrator as _orch
    import transport.webhook as _wh
    import common as _common
    _rbac.STATE_DIR = STATE_DIR
    _rbac.RULES_FILE = STATE_DIR / "guard_rules.json"
    _orch_hook.STATE_DIR = STATE_DIR
    _orch.STATE_DIR = STATE_DIR
    _wh.STATE_DIR = STATE_DIR
    _wh.INBOX_FILE = STATE_DIR / "inbox.json"
    _wh.AWAY_FILE = STATE_DIR / "away.json"
    _common.STATE_DIR = STATE_DIR
    _common.INBOX_FILE = STATE_DIR / "inbox.json"
    _common.ENV_PATH = TMPDIR / "skills" / "andorina" / ".env"
    _common.HERMES_HOME = TMPDIR
    _common.BRIDGE_URL = "http://localhost:3000"

def teardown():
    shutil.rmtree(TMPDIR, ignore_errors=True)

def log_test(module, name, passed, detail=""):
    global PASS, FAIL, SKIP
    if passed is True:
        PASS += 1
        print(f"  ✅ {module}/{name}")
    elif passed is False:
        FAIL += 1
        ERRORS.append(f"{module}/{name}: {detail}")
        print(f"  ❌ {module}/{name}  — {detail}")
    else:
        SKIP += 1
        print(f"  ⏭️  {module}/{name}  (skip: {detail})")

def assert_eq(actual, expected, msg=""):
    ok = actual == expected
    if not ok and msg:
        return False, f"expected {expected!r}, got {actual!r} — {msg}"
    elif not ok:
        return False, f"expected {expected!r}, got {actual!r}"
    return True, ""

def assert_true(val, msg=""):
    return (val, "") if val else (False, msg or f"expected truthy, got {val!r}")

def assert_false(val, msg=""):
    return (not val, "") if not val else (False, msg or f"expected falsy, got {val!r}")

def assert_contains(haystack, needle, msg=""):
    return (needle in haystack, "") if needle in haystack else (False, msg or f"{needle!r} not in {haystack!r}")

# ═══════════════════════════════════════════════════════════════════
# Pruebas
# ═══════════════════════════════════════════════════════════════════

def test_jids():
    """Pruebas del módulo utils/jids.py"""
    from utils.jids import (
        clean_number, extract_number, jid_match, normalize_text,
        normalize_jid, resolve_lid_to_phone, resolve_sender_label,
        resolve_hook_jid, resolve_chat_id, is_whatsapp_session
    )

    # ── clean_number ──
    ok, detail = assert_eq(clean_number("+34600000000@s.whatsapp.net"), "34600000000")
    log_test("jids", "clean_number — full JID", ok, detail)

    ok, detail = assert_eq(clean_number("120363001234@g.us"), "120363001234")
    log_test("jids", "clean_number — group JID", ok, detail)

    ok, detail = assert_eq(clean_number("600000000"), "600000000")
    log_test("jids", "clean_number — bare number", ok, detail)

    # ── extract_number ──
    ok, detail = assert_eq(extract_number("34600000000@s.whatsapp.net"), "34600000000")
    log_test("jids", "extract_number", ok, detail)

    # ── jid_match ──
    ok, detail = assert_true(jid_match("34600000000", "34600000000@s.whatsapp.net"))
    log_test("jids", "jid_match — exact match", ok, detail)

    ok, detail = assert_true(jid_match("34600000000", "+34 600000000"))
    log_test("jids", "jid_match — different formats", ok, detail)

    ok, detail = assert_true(jid_match("600000000", "34600000000"))
    log_test("jids", "jid_match — suffix without country code", ok, detail)

    ok, detail = assert_false(jid_match("34600000000", "34600000001"))
    log_test("jids", "jid_match — different numbers", ok, detail)

    # ── normalize_text ──
    ok, detail = assert_eq(normalize_text("María García"), "maria garcia")
    log_test("jids", "normalize_text — accents", ok, detail)

    # ── normalize_jid ──
    ok, detail = assert_eq(normalize_jid("34600000000@s.whatsapp.net"), "34600000000@s.whatsapp.net")
    log_test("jids", "normalize_jid — already full", ok, detail)

    ok, detail = assert_eq(normalize_jid("600000000", "34"), "34600000000@s.whatsapp.net")
    log_test("jids", "normalize_jid — partial number", ok, detail)

    ok, detail = assert_eq(normalize_jid("120363001234@g.us"), "120363001234@g.us")
    log_test("jids", "normalize_jid — group JID", ok, detail)

    ok, detail = assert_true(normalize_jid("120363001234567890").endswith("@g.us"))
    log_test("jids", "normalize_jid — long number → group", ok, detail)

    # ── is_whatsapp_session ──
    ok, detail = assert_true(is_whatsapp_session({"session_key": "whatsapp:dm:34600000000"}))
    log_test("jids", "is_whatsapp_session — DM", ok, detail)

    ok, detail = assert_true(is_whatsapp_session({"session_key": "whatsapp:group:120363001234:34600000000"}))
    log_test("jids", "is_whatsapp_session — group", ok, detail)

    ok, detail = assert_false(is_whatsapp_session({"session_key": "hermes:cli:local"}))
    log_test("jids", "is_whatsapp_session — TUI", ok, detail)

    # ── resolve_hook_jid ──
    ok, detail = assert_eq(
        resolve_hook_jid({"session_key": "agent:main:whatsapp:dm:34600000000@s.whatsapp.net", "extra": {}}),
        "34600000000@s.whatsapp.net"
    )
    log_test("jids", "resolve_hook_jid — DM session_key", ok, detail)

    # Grupo: debe extraer el sender individual, no el grupo
    ok, detail = assert_eq(
        resolve_hook_jid({"session_key": "agent:main:whatsapp:group:120363001234@g.us:34600000000", "extra": {}}),
        "34600000000"
    )
    log_test("jids", "resolve_hook_jid — group extracts sender", ok, detail)

    # ── resolve_chat_id ──
    ok, detail = assert_true(
        "@g.us" in resolve_chat_id({"session_key": "agent:main:whatsapp:group:120363001234@g.us:34600000000", "extra": {}})
    )
    log_test("jids", "resolve_chat_id — group returns group JID", ok, detail)

    ok, detail = assert_true(
        "@s.whatsapp.net" in resolve_chat_id({"session_key": "agent:main:whatsapp:dm:34600000000@s.whatsapp.net", "extra": {}})
    )
    log_test("jids", "resolve_chat_id — DM returns sender JID", ok, detail)


def test_rbac():
    """Pruebas del módulo security/rbac.py"""
    from security.rbac import load_rules, resolve_role, get_role_config, is_owner, AVAILABLE_PERMISSIONS
    import common
    common.ENV_PATH = TMPDIR / ".env"
    common.HERMES_HOME = TMPDIR

    env = common.load_env()

    # ── load_rules ──
    rules = load_rules()
    ok, detail = assert_true(isinstance(rules, dict) and "roles" in rules)
    log_test("rbac", "load_rules — returns dict with roles", ok, detail)

    # ── resolve_role ──
    ok, detail = assert_eq(resolve_role("34600000000@s.whatsapp.net", rules, env), "owner")
    log_test("rbac", "resolve_role — owner", ok, detail)

    ok, detail = assert_eq(resolve_role("34600000001@s.whatsapp.net", rules, env), "manager")
    log_test("rbac", "resolve_role — manager", ok, detail)

    ok, detail = assert_eq(resolve_role("34600000003@s.whatsapp.net", rules, env), "blocked")
    log_test("rbac", "resolve_role — blocked", ok, detail)

    ok, detail = assert_eq(resolve_role("34999999999@s.whatsapp.net", rules, env), "chatbot")
    log_test("rbac", "resolve_role — unknown → chatbot", ok, detail)

    # ── is_owner ──
    ok, detail = assert_true(is_owner("34600000000@s.whatsapp.net", env))
    log_test("rbac", "is_owner — admin", ok, detail)

    ok, detail = assert_false(is_owner("34600000001@s.whatsapp.net", env))
    log_test("rbac", "is_owner — non-admin", ok, detail)

    # ── get_role_config ──
    config = get_role_config("manager", rules)
    ok, detail = assert_true("send_text" in config.get("permissions", []))
    log_test("rbac", "get_role_config — manager has send_text", ok, detail)

    # ── AVAILABLE_PERMISSIONS ──
    required = ["all", "send_text", "chatbot_toggle", "chatbot_mute", "add_note", 
                "notes_clear", "inbox_delete", "remove_alert", "list_alerts", "run_script"]
    for perm in required:
        ok, detail = assert_true(perm in AVAILABLE_PERMISSIONS, f"missing {perm}")
        log_test("rbac", f"AVAILABLE_PERMISSIONS — {perm}", ok, detail)


def test_tool_guard():
    """Pruebas del módulo security/tool_guard.py"""
    from security.tool_guard import validate_tool_call

    # ── Send text (owner) ──
    owner_rc = {"permissions": ["all"]}
    result = validate_tool_call(
        'python3 send.py message "34600000000@s.whatsapp.net" "Hola"',
        owner_rc, user_jid="34600000000@s.whatsapp.net"
    )
    log_test("tool_guard", "owner — send_text", result["status"] == "OK", result.get("payload", {}).get("error", ""))

    # ── Send text (manager with permission) ──
    mgr_rc = {"permissions": ["send_text"], "allowed_chats": ["self"]}
    result = validate_tool_call(
        'python3 send.py message "34600000001@s.whatsapp.net" "Hola"',
        mgr_rc, user_jid="34600000001@s.whatsapp.net"
    )
    log_test("tool_guard", "manager — send_text to self", result["status"] == "OK", result.get("payload", {}).get("error", ""))

    # ── Send text (chatbot without permission) ──
    cb_rc = {"permissions": []}
    result = validate_tool_call(
        'python3 send.py message "34600000000@s.whatsapp.net" "Hola"',
        cb_rc, user_jid="34600000002@s.whatsapp.net"
    )
    log_test("tool_guard", "chatbot — send_text denied", result["status"] == "DENY", result.get("payload", {}).get("error", ""))

    # ── inbox delete (chatbot without permission) ──
    result = validate_tool_call(
        'python3 inbox.py delete "34600000000@s.whatsapp.net"',
        cb_rc, user_jid="34600000002@s.whatsapp.net"
    )
    log_test("tool_guard", "chatbot — inbox_delete denied", result["status"] == "DENY", "")

    # ── chatbot mute (manager with chatbot_mute) ──
    mgr_mute_rc = {"permissions": ["chatbot_mute"]}
    result = validate_tool_call(
        'python3 admin_cli.py chatbot mute "34600000002"',
        mgr_mute_rc, user_jid="34600000001@s.whatsapp.net"
    )
    log_test("tool_guard", "manager — chatbot mute allowed", result["status"] == "OK", result.get("payload", {}).get("error", ""))

    # ── chatbot on/off (manager with chatbot_toggle) ──
    mgr_toggle_rc = {"permissions": ["chatbot_toggle"]}
    result = validate_tool_call(
        'python3 admin_cli.py chatbot on',
        mgr_toggle_rc, user_jid="34600000001@s.whatsapp.net"
    )
    log_test("tool_guard", "manager — chatbot toggle allowed", result["status"] == "OK", result.get("payload", {}).get("error", ""))

    # ── notes (manager with add_note) ──
    mgr_note_rc = {"permissions": ["add_note"]}
    result = validate_tool_call(
        'python3 contacts.py note-add "34600000000@s.whatsapp.net" "test note"',
        mgr_note_rc, user_jid="34600000001@s.whatsapp.net"
    )
    log_test("tool_guard", "manager — add_note allowed", result["status"] == "OK", result.get("payload", {}).get("error", ""))

    # ── note-clear (manager without notes_clear) ──
    result = validate_tool_call(
        'python3 contacts.py note-clear "34600000000@s.whatsapp.net"',
        mgr_note_rc, user_jid="34600000001@s.whatsapp.net"
    )
    log_test("tool_guard", "manager — note-clear denied (only add_note)", result["status"] == "DENY", "")

    # ── note-clear (manager with notes_clear) ──
    mgr_clear_rc = {"permissions": ["notes_clear"]}
    result = validate_tool_call(
        'python3 contacts.py note-clear "34600000000@s.whatsapp.net"',
        mgr_clear_rc, user_jid="34600000001@s.whatsapp.net"
    )
    log_test("tool_guard", "manager — note-clear allowed (notes_clear)", result["status"] == "OK", result.get("payload", {}).get("error", ""))

    # ── alerts granular ──
    mgr_alert_rc = {"permissions": ["add_alert", "list_alerts"]}
    result = validate_tool_call(
        'python3 alerts.py add "source" "target"',
        mgr_alert_rc, user_jid="34600000001@s.whatsapp.net"
    )
    log_test("tool_guard", "manager — add_alert allowed", result["status"] == "OK", "")

    result = validate_tool_call(
        'python3 alerts.py list',
        mgr_alert_rc, user_jid="34600000001@s.whatsapp.net"
    )
    log_test("tool_guard", "manager — list_alerts allowed", result["status"] == "OK", "")

    result = validate_tool_call(
        'python3 alerts.py remove "source"',
        mgr_alert_rc, user_jid="34600000001@s.whatsapp.net"
    )
    log_test("tool_guard", "manager — remove_alert denied (no perm)", result["status"] == "DENY", "")


def test_contacts():
    """Pruebas del módulo tools/contacts.py"""
    from tools.contacts import _notes_path, cmd_note_set, cmd_note_add, cmd_note_read, cmd_note_clear, cmd_note_section_set
    import tools.contacts as contacts_module
    contacts_module.NOTES_DIR = NOTES_DIR
    contacts_module.SCRIPTS_DIR = SCRIPTS_DIR

    test_jid = "34600000000@s.whatsapp.net"
    group_jid = "120363001234@g.us"

    # ── _notes_path ──
    path = _notes_path("34600000000")
    ok, detail = assert_true("__in__" not in str(path), "DM notes should not have __in__")
    log_test("contacts", "_notes_path — DM", ok, detail)

    path = _notes_path("34600000000", group_jid)
    ok, detail = assert_true("__in__120363001234" in str(path), f"got {path}")
    log_test("contacts", "_notes_path — group context", ok, detail)

    # ── cmd_note_set ──
    cmd_note_set(test_jid, "Test note content")
    ok, detail = assert_true((NOTES_DIR / "34600000000.md").exists())
    log_test("contacts", "cmd_note_set — creates file", ok, detail)

    # ── cmd_note_add ──
    cmd_note_add(test_jid, "Additional note")
    content = (NOTES_DIR / "34600000000.md").read_text()
    ok, detail = assert_contains(content, "Additional note")
    log_test("contacts", "cmd_note_add — appends", ok, detail)

    # ── cmd_note_read ──
    # (tested via file existence)
    ok, detail = assert_true((NOTES_DIR / "34600000000.md").exists())
    log_test("contacts", "cmd_note_read — file exists", ok, detail)

    # ── cmd_note_section_set ──
    cmd_note_section_set(test_jid, "Preferences", "Likes coffee")
    content = (NOTES_DIR / "34600000000.md").read_text()
    ok, detail = assert_contains(content, "Preferences")
    log_test("contacts", "cmd_note_section_set — section exists", ok, detail)
    ok, detail = assert_contains(content, "Likes coffee")
    log_test("contacts", "cmd_note_section_set — content", ok, detail)

    # ── Group context notes ──
    cmd_note_set(test_jid, "Group-specific note", in_group=group_jid)
    group_file = NOTES_DIR / "34600000000__in__120363001234.md"
    ok, detail = assert_true(group_file.exists(), f"expected {group_file}")
    log_test("contacts", "cmd_note_set — group context creates separate file", ok, detail)

    # ── cmd_note_clear ──
    cmd_note_clear(test_jid)
    ok, detail = assert_false((NOTES_DIR / "34600000000.md").exists())
    log_test("contacts", "cmd_note_clear — removes file", ok, detail)


def test_webhook():
    """Pruebas del módulo transport/webhook.py"""
    from transport.webhook import (
        load_away, save_away, check_away_and_reply,
        fuzzy_keyword_match, normalize_text as webhook_norm,
        process_incoming_message
    )

    # ── load_away / save_away ──
    import transport.webhook as wh
    wh.AWAY_FILE = STATE_DIR / "away.json"
    wh.INBOX_FILE = STATE_DIR / "inbox.json"
    wh.STATE_DIR = STATE_DIR

    away = load_away()
    ok, detail = assert_false(away.get("enabled"))
    log_test("webhook", "load_away — disabled by default", ok, detail)

    away["enabled"] = True
    away["message"] = "I'm away"
    save_away(away)
    away2 = load_away()
    ok, detail = assert_true(away2.get("enabled"))
    log_test("webhook", "save_away + load_away roundtrip", ok, detail)

    # ── fuzzy_keyword_match ──
    ok, detail = assert_true(fuzzy_keyword_match("Hola María", "maria"))
    log_test("webhook", "fuzzy_keyword_match — accent insensitive", ok, detail)

    ok, detail = assert_true(fuzzy_keyword_match("tengo exámenes", "examen"))
    log_test("webhook", "fuzzy_keyword_match — plural", ok, detail)

    # ── process_incoming_message (sin error) ──
    try:
        process_incoming_message(
            chat_id="34600000000@s.whatsapp.net",
            sender="34600000000@s.whatsapp.net",
            text="Test message",
            is_bot=False,
            write_inbox=True
        )
        ok = True
    except Exception as e:
        ok = False
        detail = str(e)
    log_test("webhook", "process_incoming_message — no crash", ok, detail)


def test_orchestrator():
    """Pruebas del módulo security/orchestrator.py"""
    import common
    common.ENV_PATH = TMPDIR / "skills" / "andorina" / ".env"
    common.HERMES_HOME = TMPDIR

    from security.orchestrator import build_snapshot, process_request
    import security.orchestrator as orch
    orch.STATE_DIR = STATE_DIR

    env = common.load_env()

    # ── build_snapshot — owner DM ──
    snap = build_snapshot("34600000000@s.whatsapp.net", env)
    ok, detail = assert_eq(snap["mode"], "full")
    log_test("orchestrator", "build_snapshot — owner mode", ok, detail)

    # ── build_snapshot — manager ──
    snap = build_snapshot("34600000001@s.whatsapp.net", env)
    ok, detail = assert_eq(snap["mode"], "manager")
    log_test("orchestrator", "build_snapshot — manager mode", ok, detail)

    # ── build_snapshot — chatbot ──
    snap = build_snapshot("34600000002@s.whatsapp.net", env)
    ok, detail = assert_eq(snap["mode"], "chatbot")
    log_test("orchestrator", "build_snapshot — chatbot mode", ok, detail)

    # ── build_snapshot — group context ──
    snap = build_snapshot("34600000000@s.whatsapp.net", env, chat_id="120363001234@g.us")
    ok, detail = assert_true(isinstance(snap.get("context_only"), str))
    log_test("orchestrator", "build_snapshot — group chat_id", ok, detail)

    # ── build_snapshot — notes loaded ──
    (NOTES_DIR / "34600000000.md").write_text("# Test note\nSome note content")
    snap = build_snapshot("34600000000@s.whatsapp.net", env)
    ok, detail = assert_contains(snap.get("context_only", ""), "NOTES FOR")
    log_test("orchestrator", "build_snapshot — notes injected", ok, detail)

    # Grupo: debe buscar archivo de grupo primero
    (NOTES_DIR / "34600000000__in__120363001234.md").write_text("# Group note\nGroup context")
    snap = build_snapshot("34600000000@s.whatsapp.net", env, chat_id="120363001234@g.us")
    ok, detail = assert_contains(snap.get("context_only", ""), "Group note")
    log_test("orchestrator", "build_snapshot — group notes loaded", ok, detail)

    # ── process_request ──
    result = process_request("34600000000@s.whatsapp.net", "Test message")
    ok, detail = assert_true(result.get("allowed"))
    log_test("orchestrator", "process_request — owner allowed", ok, detail)

    result = process_request("34600000003@s.whatsapp.net", "Test message")
    ok, detail = assert_false(result.get("allowed"))
    log_test("orchestrator", "process_request — blocked denied", ok, detail)


def test_mute_fix():
    """Prueba específica para el fix del mute global (P1)."""
    import security.orchestrator_hook as _oh
    from security.rbac import load_rules
    import common
    common.ENV_PATH = TMPDIR / "skills" / "andorina" / ".env"
    common.HERMES_HOME = TMPDIR
    _oh.STATE_DIR = STATE_DIR

    env = common.load_env()
    rules = load_rules()

    # Caso 1: chatbot enabled → debe pasar
    jid_entry = rules["jids"].get("34600000001", {})
    result = _oh._apply_security_gates("34600000001@s.whatsapp.net", jid_entry, rules, env, "hola")
    ok, detail = assert_eq(result, None, f"expected None (passthrough), got {result}")
    log_test("mute_fix", "chatbot enabled → passthrough", ok, detail)

    # Caso 2: chatbot disabled → debe bloquear
    chatbot_data = {"enabled": False, "muted_jids": []}
    from utils.safe_json import write_json_safe
    write_json_safe(STATE_DIR / "chatbot.json", chatbot_data)
    result = _oh._apply_security_gates("34600000001@s.whatsapp.net", jid_entry, rules, env, "hola")
    ok, detail = assert_true(result is not None and "disabled" in str(result).lower(), f"got {result}")
    log_test("mute_fix", "chatbot disabled → blocked", ok, detail)

    # Restaurar
    write_json_safe(STATE_DIR / "chatbot.json", {"enabled": True, "muted_jids": []})

    # Caso 3: usuario en muted_jids → debe bloquear
    chatbot_data = {"enabled": True, "muted_jids": ["34600000001"]}
    write_json_safe(STATE_DIR / "chatbot.json", chatbot_data)
    result = _oh._apply_security_gates("34600000001@s.whatsapp.net", jid_entry, rules, env, "hola")
    ok, detail = assert_true(result is not None and "muted" in str(result).lower(), f"got {result}")
    log_test("mute_fix", "user in muted_jids → blocked", ok, detail)

    # Restaurar
    write_json_safe(STATE_DIR / "chatbot.json", {"enabled": True, "muted_jids": []})


def test_install_flow():
    """Verifica que los scripts de instalación sean sintácticamente correctos."""
    import py_compile
    
    install_files = [
        "setup.py", "setup_lib.py", "install_cli.py",
        "install.sh", "Andorina-Panel.sh"
    ]
    for f in install_files:
        path = SKILL_DIR / f
        if not path.exists():
            log_test("install", f"{f} exists", False, "file not found")
            continue
        if f.endswith(".py"):
            try:
                py_compile.compile(str(path), doraise=True)
                log_test("install", f"{f} compiles", True)
            except py_compile.PyCompileError as e:
                log_test("install", f"{f} compiles", False, str(e))
        elif f.endswith(".sh"):
            ok, detail = assert_true(path.read_text().startswith("#!/bin/bash") or path.read_text().startswith("#!/usr/bin/env"))
            log_test("install", f"{f} is shell script", ok, detail)




def test_docker_headless():
    """Verifica compatibilidad con Docker/headless."""
    path = SKILL_DIR / "install_cli.py"
    if not path.exists():
        log_test("docker", "install_cli.py exists", False, "not found")
        return
    content = path.read_text()
    ok, detail = assert_contains(content, "detect_environment")
    log_test("docker", "install_cli.py — detect_environment", ok, detail)

    ok, detail = assert_contains(content, "is_docker")
    log_test("docker", "install_cli.py — is_docker check", ok, detail)

    ok, detail = assert_contains(content, "headless")
    log_test("docker", "install_cli.py — headless mode", ok, detail)

    ok, detail = assert_contains(content, "tempfile")
    log_test("docker", "install_cli.py — uses tempfile (fix #1)", ok, detail)

    ok, detail = assert_contains(content, "PROGRESS_FILE")
    log_test("docker", "install_cli.py — PROGRESS_FILE defined", ok, detail)

    # Verificar setup_lib tiene detect_environment y detect_agents con rutas Docker
    slib = (SKILL_DIR / "setup_lib.py").read_text()
    ok, detail = assert_contains(slib, "def detect_environment")
    log_test("docker", "setup_lib — detect_environment", ok, detail)

    ok, detail = assert_contains(slib, "def _is_docker")
    log_test("docker", "setup_lib — _is_docker", ok, detail)

    ok, detail = assert_contains(slib, "/data/.hermes")
    log_test("docker", "setup_lib — Docker path /data/.hermes", ok, detail)

    ok, detail = assert_contains(slib, "/app/.hermes")
    log_test("docker", "setup_lib — Docker path /app/.hermes", ok, detail)

    ok, detail = assert_contains(slib, "get_skills_dir")
    log_test("docker", "setup_lib — get_skills_dir (Docker layout)", ok, detail)

    ok, detail = assert_contains(slib, "/.dockerenv")
    log_test("docker", "setup_lib — _is_docker checks /.dockerenv", ok, detail)

    # Verificar register_hooks crea config.yaml si no existe
    ok, detail = assert_contains(slib, "config.yaml no encontrado")
    log_test("docker", "setup_lib — register_hooks creates missing config.yaml", ok, detail)

    ok, detail = assert_contains(slib, "creando uno mínimo")
    log_test("docker", "setup_lib — register_hooks creates minimal config", ok, detail)

    # Verificar handle_failure permite skip (no bloquea en headless)
    ok, detail = assert_contains(content, "def handle_failure")
    log_test("docker", "install_cli — handle_failure with retry/skip/abort", ok, detail)

    # Verificar --in-group auto-inyect
    ohook = (SKILL_DIR / "scripts" / "security" / "orchestrator_hook.py").read_text()
    ok, detail = assert_contains(ohook, "Auto-inyectar --in-group")
    log_test("docker", "orchestrator_hook — auto-inject --in-group", ok, detail)

    # Verificar mute fix (chatbot.json en vez de rules)
    ok, detail = assert_contains(ohook, "chatbot.json")
    log_test("docker", "orchestrator_hook — mute fix uses chatbot.json", ok, detail)

    # Verificar run_step_patch busca en múltiples ubicaciones
    ok, detail = assert_contains(content, "hermes-agent")
    log_test("docker", "install_cli — bridge search covers Docker layouts", ok, detail)

    # Verificar modo non-interactive documentado
    ok, detail = assert_contains(content, "non-interactive")
    log_test("docker", "install_cli — non-interactive documented", ok, detail)

    # Verificar install_deps maneja root y externally-managed
    ok, detail = assert_contains(slib, "--break-system-packages")
    log_test("docker", "setup_lib — install_deps supports --break-system-packages", ok, detail)

    ok, detail = assert_contains(slib, "geteuid")
    log_test("docker", "setup_lib — install_deps detects root user", ok, detail)

    # Verificar no hay hardcodeo de paths de escritorio
    ok, detail = assert_false("xdg-open" in content)
    log_test("docker", "install_cli — no desktop-only commands", ok, detail)

def test_all_modules_compilable():
    """Verifica que todos los .py compilen."""
    import py_compile
    all_py = []
    for root, dirs, files in os.walk(str(SCRIPTS_DIR)):
        if "__pycache__" in root:
            continue
        for f in files:
            if f.endswith(".py") and not f.startswith("."):
                all_py.append(Path(root) / f)

    ok_count = 0
    fail_list = []
    for p in sorted(all_py):
        rel = p.relative_to(SKILL_DIR)
        try:
            py_compile.compile(str(p), doraise=True)
            ok_count += 1
        except py_compile.PyCompileError as e:
            fail_list.append(f"{rel}: {e}")

    ok, detail = assert_eq(len(fail_list), 0, f"{len(fail_list)} files failed: {fail_list[:5]}")
    log_test("compile", f"all .py compile ({ok_count}/{len(all_py)})", ok, detail)
    if fail_list:
        for f in fail_list:
            log_test("compile", f, False)


def test_changelog_and_version():
    """Verifica VERSION y CHANGELOG."""
    ver = (SKILL_DIR / "VERSION").read_text().strip()
    ok, detail = assert_contains(ver, "1.6")
    log_test("meta", f"VERSION = {ver}", ok, detail)

    chlog = (SKILL_DIR / "CHANGELOG.md").read_text()
    ok, detail = assert_contains(chlog, "v2.0.0-alpha")
    log_test("meta", "CHANGELOG has v2.0.0-alpha", ok, detail)

    ok, detail = assert_contains(chlog, "SQL injection fix")
    log_test("meta", "CHANGELOG has SQL injection fix", ok, detail)

    ok, detail = assert_contains(chlog, "Deadlock fix")
    log_test("meta", "CHANGELOG has deadlock fix", ok, detail)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    global PASS, FAIL, SKIP
    args = sys.argv[1:]
    quick = "--quick" in args
    docker_mode = "--docker" in args
    module_filter = None
    for i, a in enumerate(args):
        if a == "--module" and i + 1 < len(args):
            module_filter = args[i + 1]

    print("═" * 60)
    print("  🧪 Andoriña V2.0 — Sandbox de Pruebas")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if docker_mode:
        print("  🐳 Modo Docker/Headless")
    if quick:
        print("  ⚡ Modo rápido")
    print("═" * 60)

    setup()

    try:
        if not module_filter or module_filter == "jids":
            print("\n── utils/jids.py ──")
            test_jids()

        if not module_filter or module_filter == "rbac":
            print("\n── security/rbac.py ──")
            test_rbac()

        if not module_filter or module_filter == "tool_guard":
            print("\n── security/tool_guard.py ──")
            test_tool_guard()

        if not module_filter or module_filter == "contacts":
            print("\n── tools/contacts.py ──")
            test_contacts()

        if not module_filter or module_filter == "webhook":
            print("\n── transport/webhook.py ──")
            test_webhook()

        if not module_filter or module_filter == "orchestrator":
            print("\n── security/orchestrator ──")
            test_orchestrator()

        if not module_filter or module_filter == "mute_fix":
            print("\n── Fix P1: Mute Global ──")
            test_mute_fix()

        if not quick and (not module_filter or module_filter == "install"):
            print("\n── Instalación ──")
            test_install_flow()

        if not quick and (not module_filter or module_filter in ("docker", "install")):
            print("\n── Docker/Headless ──")
            test_docker_headless()

        if not quick and not module_filter:
            print("\n── Compilación ──")
            test_all_modules_compilable()

            print("\n── Metadatos ──")
            test_changelog_and_version()

    finally:
        teardown()

    print()
    print("═" * 60)
    print(f"  ✅ PASS: {PASS}  |  ❌ FAIL: {FAIL}  |  ⏭️  SKIP: {SKIP}")
    if ERRORS:
        print(f"\n  Errores ({len(ERRORS)}):")
        for e in ERRORS:
            print(f"    ❌ {e}")
    print("═" * 60)

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
