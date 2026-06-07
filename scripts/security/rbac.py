import json
import re
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.safe_json import read_json_safe, write_json_safe

SCRIPTS_DIR = Path(__file__).parent.parent.absolute()
STATE_DIR   = SCRIPTS_DIR.parent / "state"
RULES_FILE  = STATE_DIR / "guard_rules.json"

# ── Single source of truth for all possible permissions ─────────────────────
AVAILABLE_PERMISSIONS = [
    # Core message permissions
    "all",
    "send_text", "send_file", "send_voice", "broadcast",
    # Inbox / history
    "read_inbox", "search_history",
    # Contacts
    "search_contacts", "list_groups", "refresh_contacts", "add_note",
    # Agenda
    "schedule_msg", "list_agenda", "remove_agenda",
    "recurring_add", "recurring_list", "recurring_remove",
    # Alerts
    "add_alert",
    # Admin / RBAC
    "run_diag", "run_repair", "wipe_logs",
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

def clean_number(n):
    return re.sub(r"[^\d]", "", n)

def is_owner(number, env):
    num = clean_number(number)
    if not num:
        return False
    admin_phone = env.get("ADMIN_PHONE", "")
    admin_clean = clean_number(admin_phone)
    if admin_clean and admin_clean == num:
        return True
    return False

def extract_number(jid):
    """Extract the numeric/group part from a JID for lookup."""
    return jid.split("@")[0] if "@" in jid else jid

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
    num = extract_number(jid)

    # 1. Owner always takes priority (from .env ADMIN_PHONE)
    if is_owner(jid, env):
        return "owner"

    # 2. Check JID-specific assignment
    jid_entry = rules.get("jids", {}).get(num, {})
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
