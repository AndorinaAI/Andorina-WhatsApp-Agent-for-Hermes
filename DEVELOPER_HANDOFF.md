# Andoriña V2 — Developer Handoff

> Language: English | Last updated: 2026-09-14

## Overview

Andoriña V2 is a **backend plugin** (`kind: backend`) for Hermes Agent v0.21.2 providing WhatsApp management via native plugin integration.

| Property | Value |
|---|---|
| Hermes | v0.21.2 |
| Plugin kind | backend |
| Runtime | `~/.hermes/plugins/andorina/` |
| Dev source | `~/Documentos/andorinaDEV/Andorina-WhatsApp-Agent-for-Hermes/` |
| Entry | `register(ctx)` in `__init__.py` |
| Tests | 105 passing (pytest) |

## Architecture

```
Hermes → PluginManager → register(ctx)
  ├── 3 Hooks (pre_llm_call, pre_tool_call, post_llm_call)
  └── 11 Tools (send_text, send_file, broadcast, read_inbox,
                 search_contacts, list_groups, schedule_msg,
                 add_note, add_alert, manage_role, manage_soul)
```

Hooks delegate to `orchestrator_hook.py` via subprocess. Tools delegate to scripts under `scripts/tools/`, `scripts/transport/`, and `scripts/utils/`.

## WhatsApp Inbound Pipeline

```
WhatsApp → Hermes → pre_llm_call → _run_hook → orchestrator_hook.py
  → is_whatsapp_session() → resolve_hook_jid()
  → _get_last_message_text() → process_incoming_message() → inbox.json
```

## Hermes v0.21.2 Compatibility

Tool handlers receive `handler(args_dict)`. The `_adapt_handler()` wrapper converts dict to kwargs.

Tools must return `str` (JSON). `_run_script()` returns `json.dumps(result)`.

Hook payload fields (`platform`, `sender_id`, `user_message`) are at top level, not in `extra`. Handled by `is_whatsapp_session()` and `resolve_hook_jid()` in `utils/jids.py`.

Hook event name is injected via `_run_hook(event, kwargs)` → `{"hook_event_name": event, **kwargs}`.

## Verification Matrix

| Tool | Status |
|---|---|
| read_inbox | E2E verified |
| search_contacts, list_groups, add_note, add_alert, manage_role, manage_soul | Functionally verified |
| send_text, send_file, broadcast, schedule_msg | Mock verified (E2E pending) |

## Security

Input Guard, Tool Guard, RBAC, Soul restrictions, DLP pipeline, JID validation, Path traversal protection — all implemented. Test coverage is partial.

## Outbound Testing Safety

`broadcast` sends to N recipients per call. Do not use for casual testing. Use mocks. Single-message E2E only when bridge is connected.

## Running Tests

```bash
cd ~/Documentos/andorinaDEV/Andorina-WhatsApp-Agent-for-Hermes
pytest -q
hermes plugins validate .
```

## Key Files

| File | Role |
|---|---|
| `__init__.py` | register(), 11 handlers, 3 hooks, _run_script, _run_hook, _adapt_handler |
| `scripts/security/orchestrator_hook.py` | Main hook processor |
| `scripts/utils/jids.py` | WhatsApp detection, JID resolution |
| `scripts/transport/webhook.py` | process_incoming_message() |
| `scripts/transport/send.py` | Message sending + broadcast |
| `plugin.yaml` | kind: backend, 11 tools, 3 hooks |

## V1 Obsolescence

V1 archived at `~/.hermes/skills/andorina.V1.disabled/` (inactive) and `~/.hermes/backup/andorina-v1-skill/` (backup). Shell hooks, SKILL.md, terminal-only pattern removed.

## Deployment

Dev repo → copy to `~/.hermes/plugins/andorina/`. Preserve `state/` and `logs/` directories.

## Remaining Work

- send_text / send_file E2E (requires WhatsApp bridge connected)
- broadcast E2E intentionally not performed (multi-send risk)
- Security test coverage expansion
- Documentation updates (README, MIGRATION, CHANGELOG, GUIDE, FEATURES)
