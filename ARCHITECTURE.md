# 🏗️ Andoriña V2.0 — Architecture & Plugin Reference

> **Language policy:** Development documentation is in English.
> End-user documentation supports English (en) and Spanish (es).
> Translation-ready architecture via `locales/` directory.

---

## ★ Plugin Architecture (Hermes Official)

Andoriña V2.0 is a **backend plugin** that extends the built-in WhatsApp platform
of Hermes Agent. It follows the official Hermes plugin contract:

- **Entry point:** `register(ctx)` — called by `PluginManager` at discovery
- **Hooks:** `pre_llm_call`, `pre_tool_call`, `post_llm_call` — registered via `ctx.register_hook()`
- **Tools:** 11 tools registered via `ctx.register_tool()`
- **Manifest:** `plugin.yaml` with capabilities, hooks, required/env vars
- **Zero core modifications:** Plugins never touch `run_agent.py`, `cli.py`, or `gateway/run.py`

### Directory Structure
```
andorina/
├── plugin.yaml              ← Manifest (capabilities, env vars, i18n)
├── __init__.py              ← register(ctx) entry point
├── scripts/
│   ├── security/
│   │   ├── orchestrator_hook.py  ← pre_llm_call / pre_tool_call handlers
│   │   ├── orchestrator.py       ← build_snapshot, process_request
│   │   ├── rbac.py               ← Role-based access control
│   │   ├── tool_guard.py         ← Tool permission validation
│   │   ├── input_guard.py        ← Input rate limiting + injection
│   │   ├── soul_sync.py          ← Sub-soul synchronization
│   │   ├── memory/
│   │   │   ├── backend.py        ← MemoryBackend ABC
│   │   │   ├── hindsight.py      ← HindsightBackend (PostgreSQL)
│   │   │   ├── hermes_memory.py  ← HermesMemoryBackend (native API)
│   │   │   └── detector.py       ← Auto-detection
│   │   └── output_pipeline/      ← DLP sanitization pipeline
│   ├── tools/
│   │   ├── contacts.py           ← Universal contact search + notes
│   │   ├── inbox.py              ← Message inbox + history
│   │   ├── agenda.py             ← Scheduling (Hermes cron)
│   │   ├── alerts.py             ← Semantic alerts
│   │   └── files.py              ← Multi-OS file sending
│   ├── transport/
│   │   ├── send.py               ← Message sending
│   │   └── webhook.py            ← Incoming message handler
│   └── utils/
│       ├── jids.py               ← Canonical JID normalization
│       ├── safe_json.py          ← Atomic JSON with filelock
│       ├── admin_cli.py          ← RBAC + chatbot administration
│       └── tunnel.py             ← Cloudflare tunnel (remote access)
├── GUI/                          ← Web panel (server.py + static/)
├── tests/                        ← pytest test suite
├── locales/
│   ├── en/                       ← English translations
│   └── es/                       ← Spanish translations
├── ARCHITECTURE.md               ← This file
├── CHANGELOG.md                  ← Version history
├── MIGRATION.md                  ← V1.6 → V2.0 migration guide
└── developer_guide.md            ← Plugin development guide
```

---

## 🔄 Message Flow

```
WhatsApp → Hermes Gateway (built-in platform)
  └── Session → pre_llm_call hook
       └── Andoriña Plugin:
            ├── JID resolution (utils/jids.py)
            ├── RBAC check (security/rbac.py)
            ├── Input validation (security/input_guard.py)
            ├── Sub-soul injection (security/soul_sync.py)
            ├── Build context snapshot (security/orchestrator.py)
            ├── Knowledge retrieval (security/knowledge_retrieval.py)
            └── DLP sanitization (security/output_pipeline/)
```

---

## 🌐 i18n Architecture

All user-facing strings are externalized in `locales/<lang>/`:
- `locales/en/` — English (default, development language)
- `locales/es/` — Spanish

To add a new language:
1. Copy `locales/en/` to `locales/<code>/`
2. Translate all string values
3. The plugin auto-detects language from Hermes locale settings

---

## 📊 Permission Map (37 permissions → 32 actions)

| Tool | Permission | Granular? |
|------|-----------|-----------|
| `send.py message` | `send_text` | ✅ |
| `send.py broadcast` | `broadcast` | ✅ |
| `files.py` | `send_file` | ✅ |
| `files.py --voice` | `send_voice` | ✅ |
| `inbox.py list/read` | `read_inbox` | ✅ |
| `inbox.py search` | `search_history` | ✅ |
| `inbox.py delete` | `inbox_delete` | ✅ V2.0 |
| `contacts.py search` | `search_contacts` | ✅ |
| `contacts.py groups` | `list_groups` | ✅ |
| `contacts.py refresh` | `refresh_contacts` | ✅ |
| `contacts.py note-add/read` | `add_note` | ✅ |
| `contacts.py note-clear` | `notes_clear` | ✅ V2.0 |
| `agenda.py auto-schedule` | `schedule_msg` | ✅ |
| `agenda.py list` | `list_agenda` | ✅ |
| `agenda.py remove` | `remove_agenda` | ✅ |
| `agenda.py recurring` | `recurring_*` | ✅ |
| `alerts.py add` | `add_alert` | ✅ |
| `alerts.py remove` | `remove_alert` | ✅ V2.0 |
| `alerts.py list` | `list_alerts` | ✅ V2.0 |
| `diag.py` | `run_diag` | ✅ |
| `bridge_health.py` | `run_repair` | ✅ |
| `wipe_logs.py` | `wipe_logs` | ✅ |
| `orchestrator.py status` | `guard_status` | ✅ |
| `orchestrator.py reset` | `guard_reset` | ✅ |
| `admin_cli.py role` | `set/get/remove/list_role` | ✅ |
| `admin_cli.py chatbot` | `chatbot_toggle`/`chatbot_mute` | ✅ V2.0 |
| `admin_cli.py away` | `away_toggle` | ✅ |
| `admin_cli.py soul` | `set_soul`/`get_soul` | ✅ |
| Unknown `.py` scripts | `run_script` | ✅ V2.0 |

---

## 🔗 Compatibility with Hermes

| Version | Hermes Requirement | Status |
|---------|-------------------|--------|
| V1.0 — V1.6 | Hermes >= 0.16.0 | ✅ (legacy — replaced by V2 plugin) |
| V2.0-alpha | Hermes >= 0.21.2 | ✅ (plugin in `~/.hermes/plugins/`) |

---

---
