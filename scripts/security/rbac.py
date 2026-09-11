import json
import re
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.safe_json import read_json_safe, write_json_safe
from utils.jids import clean_number, extract_number, jid_match

SCRIPTS_DIR = Path(__file__).parent.parent.absolute()
STATE_DIR   = SCRIPTS_DIR.parent / "state"
RULES_FILE  = STATE_DIR / "guard_rules.json"

# ── Single source of truth for all possible permissions ─────────────────────
AVAILABLE_PERMISSIONS = [
    # Core message permissions
    "all",
    "send_text", "send_file", "send_voice", "broadcast",
    # Inbox / history
    "read_inbox", "search_history", "inbox_delete",
    # Contacts
    "search_contacts", "list_groups", "refresh_contacts",
    "add_note", "notes_clear",
    # Agenda
    "schedule_msg", "list_agenda", "remove_agenda",
    "recurring_add", "recurring_list", "recurring_remove",
    # Alerts
    "add_alert", "remove_alert", "list_alerts",
    # Admin / RBAC
    "run_diag", "run_repair", "wipe_logs", "run_script",
    "guard_status", "guard_reset",
    "set_role", "get_role", "remove_role", "list_roles",
    "set_soul", "get_soul",
    "chatbot_mute", "chatbot_toggle", "away_toggle",
    # Panel UI permissions
    "panel:send", "panel:contacts", "panel:inbox", "panel:agenda", "panel:alerts",
    "panel:send:direct", "panel:send:broadcast", "panel:send:file",
    "panel:contacts:notes", "panel:contacts:refresh",
    "panel:inbox:delete",
    "panel:agenda:schedule", "panel:agenda:delete",
    "panel:alerts:manage",
    # Admin panel sections
    "admin:dashboard", "admin:status", "admin:rbac", "admin:souls",
    "admin:chatbot", "admin:away", "admin:env", "admin:logs",
    "admin:system", "admin:system:engine", "admin:system:logs", "admin:system:repair",
]


def is_owner(number, env):
    num = clean_number(number)
    if not num:
        return False
    admin_phone = env.get("ADMIN_PHONE", "")
    admin_clean = clean_number(admin_phone)
    if not admin_clean:
        return False
    # V1.6: usar jid_match centralizado en lugar de reimplementación manual
    return jid_match(admin_clean, num)

def load_rules():
    """Load guard_rules.json. Returns default structure if missing/corrupt."""
    default_rules = {
        "global_default_role": "chatbot",
        "roles": {
            "owner":   {"permissions": ["all"]},
            "manager": {"permissions": ["send_text", "send_file", "send_voice",
                                         "read_inbox", "search_history",
                                         "search_contacts", "list_groups",
                                         "schedule_msg", "list_agenda", "remove_agenda",
                                         "add_alert", "get_role"],
                        "allowed_folders": [], "allowed_contact_tags": [],
                        "allowed_chats": ["self"], "max_requests_per_hour": 20},
            "chatbot": {
                "permissions": [],
                "command_rules": {
                    "cat":     {"path_must_be_in": "allowed_os_paths"},
                    "grep":    {"path_must_be_in": "allowed_os_paths"},
                    "ls":      {"path_must_be_in": "allowed_os_paths"},
                    "find":    {"denied_args": ["-exec", "-delete", "-execdir"]},
                    "python3": {"denied_args": ["-c", "-m"]},
                    "python":  {"denied_args": ["-c", "-m"]},
                }
            },
            "blocked": {"permissions": []},
        },
        "jids": {}
    }
    data = read_json_safe(RULES_FILE, default=default_rules)
    if isinstance(data, dict) and "roles" in data:
        return data
    return default_rules

def save_rules(rules):
    """Atomic write of guard_rules.json."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    write_json_safe(RULES_FILE, rules)

def resolve_role(jid, rules, env):
    """Determine the role for a given JID.
    Priority: 1) Owner from .env  2) JID-specific rule  3) global_default_role
    """
    # V1.6: usar clean_number para el fast lookup y suffix matching —
    # extract_number preserva caracteres no numéricos (+, espacios) que
    # rompen la búsqueda exacta por clave.
    num = clean_number(jid)

    # 1. Owner always takes priority (from .env ADMIN_PHONE)
    if is_owner(jid, env):
        return "owner"

    # 2. Check JID-specific assignment — suffix match so rules stored without
    #    country prefix (e.g. '612345678') still hit when JID arrives as
    #    '34612345678@s.whatsapp.net', and vice versa.
    jid_rules = rules.get("jids", {})
    jid_entry = jid_rules.get(num)  # fast exact path first
    # V1.6: usar jid_match centralizado en lugar de reinvención manual
    if jid_entry is None:
        for stored_num, entry in jid_rules.items():
            if jid_match(stored_num, num):
                jid_entry = entry
                break
    if jid_entry and jid_entry.get("role"):
        role_name = jid_entry["role"]
        if role_name in rules.get("roles", {}):
            return role_name

    # 3. Fall back to global default
    return rules.get("global_default_role", "chatbot")

def get_role_config(role_name, rules):
    """Get the full config dict for a role name."""
    if role_name == "owner":
        return {"permissions": ["all"]}
    return rules.get("roles", {}).get(role_name, {"permissions": []})

def has_permission(role_config, permission):
    """Check if a role has a specific permission."""
    perms = role_config.get("permissions", [])
    return "all" in perms or permission in perms
