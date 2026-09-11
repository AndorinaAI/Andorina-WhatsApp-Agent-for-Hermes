# 🏗️ Andoriña V1.6‑Beta1 — Arquitectura y Referencia Centralizada

> **Regla de oro:** Antes de crear cualquier función nueva, verifica que no exista ya en este documento o en los módulos listados. Toda manipulación de JIDs debe pasar por `utils/jids.py`.

---

## ★ MÓDULO CANÓNICO: `scripts/utils/jids.py`

**NUNCA escribas manipulación de JIDs inline.** Usa siempre estas funciones:

### Funciones públicas

| Función | Qué hace |
|---------|----------|
| `clean_number(jid)` | Extrae solo dígitos de un JID (quita `@s.whatsapp.net`, `@g.us`, `+`, espacios) |
| `extract_number(jid)` | Extrae la parte "bare" del JID (antes del `@`), sin limpiar dígitos |
| `jid_match(stored, incoming)` | Compara dos JIDs por sufijo numérico. Tolera prefijos de país distintos |
| `normalize_text(text)` | Lowercase + strip de acentos (NFD unicode) |
| `normalize_jid(val, country_code=None)` | Convierte número parcial a JID canónico completo. Respeta `DEFAULT_COUNTRY_CODE` de `.env`. Auto-detecta grupo (>13 dígitos o contiene `-` → `@g.us`) |
| `resolve_lid_to_phone(lid_str, ...)` | Resuelve LID de WhatsApp a número de teléfono canónico |
| `resolve_sender_label(jid, state_dir, ...)` | Resuelve JID a nombre legible (Google Contacts → inbox → pushName → fallback) |
| `resolve_hook_jid(data)` | Resuelve identidad del sender desde el payload completo del hook de Hermes |
| `is_whatsapp_session(data)` | True solo si el evento del hook viene de una sesión WhatsApp (no TUI/CLI) |

### Función privada

| Función | Qué hace |
|---------|----------|
| `_get_default_country_code()` | Lee `DEFAULT_COUNTRY_CODE` de `.env`, fallback `"34"` |

---

## �� Código PROHIBIDO (usar la función canónica en su lugar)

| ❌ NO uses esto | ✅ Usa esto |
|-----------------|-------------|
| `re.sub(r"[^\d]", "", ...)` | `clean_number(jid)` de `utils/jids.py` |
| `jid.split("@")[0]` | `extract_number(jid)` de `utils/jids.py` |
| `if bare in other_bare` o `endswith` manual | `jid_match(stored, incoming)` de `utils/jids.py` |
| `unicodedata.normalize("NFD", ...)` | `normalize_text(text)` de `utils/jids.py` |
| `f"{num}@s.whatsapp.net"` o `f"{num}@g.us"` manual | `normalize_jid(val)` de `utils/jids.py` |
| `_norm()` o `_norm_jid()` local | `normalize_jid()` de `utils/jids.py` |
| `json.loads(open(...).read())` | `read_json_safe(path)` de `utils/safe_json.py` |
| `open(...).write(json.dumps(...))` | `write_json_safe(path, data)` de `utils/safe_json.py` |

---

## 📊 Funciones clave por módulo

### `scripts/common.py`
- `BRIDGE_URL` (str) — URL del bridge WhatsApp
- `INBOX_FILE` (Path) — Ruta al inbox.json
- `STATE_DIR` (Path) — Ruta al directorio state/
- `load_env(env_path=None)` → dict — Carga .env
- `log_outgoing(chat_id, text, msg_type)` — Guarda mensaje saliente en inbox
- `post_json(endpoint, data, silent_pacing)` → dict — POST al bridge

### `scripts/utils/safe_json.py`
- `read_json_safe(path, default={})` — Lee JSON con filelock
- `write_json_safe(path, data)` — Escribe JSON atómicamente (tmp → replace)

### `scripts/security/rbac.py`
- `RULES_FILE` — Ruta a `state/guard_rules.json`
- `AVAILABLE_PERMISSIONS` — Lista canónica de permisos
- `load_rules()` — Carga reglas RBAC
- `resolve_role(number, rules, env)` — Resuelve rol de un JID
- `get_role_config(role, rules)` — Config de un rol
- `is_owner(number, env)` — True si es el dueño

### `scripts/security/soul_sync.py`
- `load_soul_text(rules, jid)` — Carga texto de Sub-Soul
- `resolve_soul_knowledge_dir(rules, jid)` — Directorio de knowledge base
- `build_channel_prompts()` — Construye mapa channel_prompts
- `sync_to_config()` — Escribe channel_prompts en config.yaml
- `transition_short_term_memory(jid)` — Purga memoria corto plazo
- `purge_long_term_memory(jid)` — Purga memoria vectorial (Hindsight)

### `scripts/security/input_guard.py`
- `validate_input(number, message, msg_type)` — Rate limiting, blocklist, inyección
- `anon(number)` — Hash SHA256 del número para logs

### `scripts/security/tool_guard.py`
- `validate_tool_call(command_line, role_config, user_jid)` — Validación RBAC de herramientas

### `scripts/security/orchestrator.py`
- `build_snapshot(number, env)` — Construye snapshot de contexto
- `process_request(number, message, msg_type)` — Procesa solicitud completa

### `scripts/security/orchestrator_hook.py`
- `pre_llm_call(data)` — Hook pre_llm_call
- `pre_tool_call(data)` — Hook pre_tool_call

### `scripts/security/knowledge_retrieval.py`
- `_build_knowledge_context(jid, soul_entry=None)` — Construye contexto RAG

### `scripts/security/output_pipeline/pipeline.py`
- `run_pipeline(text, bypass_truncation=False)` → dict — Pipeline DLP completo

### `scripts/tools/agenda.py`
- `cmd_auto_schedule(chat_id, time_str, message, ...)` — Programa mensaje
- `cmd_send_pending(msg_id)` — Envía tarea pendiente (cron)
- `cmd_recurring_add(chat_id, cron_expr, message, ...)` — Tarea recurrente

### `scripts/tools/alerts.py`
- `cmd_add(source, target, keywords=None)` — Crea regla de alerta
- `cmd_remove(source)` — Elimina regla de alerta

### `scripts/tools/contacts.py`
- `cmd_search(query)` — Búsqueda difusa de contactos
- `cmd_note_add(jid, text)` — Añade nota permanente
- `cmd_note_section_set(jid, section, text)` — Actualiza sección de nota
- `cmd_note_read(jid)` — Lee notas
- `cmd_note_clear(jid)` — Borra todas las notas

### `scripts/transport/send.py`
- `cmd_mensaje(chat_id_raw, message, file_path=None)` — Envía mensaje
- `cmd_broadcast(message, jids_str)` — Envía a múltiples destinatarios

### `scripts/transport/webhook.py`
- `process_incoming_message(chat_id, sender, text, ...)` — Procesa mensaje entrante (inbox + away + alerts)
- `check_away_and_reply(chat_id, sender)` — Auto-respuesta de ausencia

---

## 🔄 Flujo de una solicitud WhatsApp

```
WhatsApp → Bridge → whatsapp.py (patch_whatsapp)
  ├── _resolve_lid_to_phone()         ← utils/jids.py
  ├── Inbox Writer (inbox.json)       ← patch_whatsapp inline
  └── Alert Dispatcher → webhook.py   ← subprocess

Hermes Hook → orchestrator_hook.py
  ├── pre_llm_call:
  │   ├── resolve_hook_jid()          ← utils/jids.py
  │   ├── is_whatsapp_session()       ← utils/jids.py
  │   ├── resolve_role()              ← rbac.py
  │   ├── validate_input()            ← input_guard.py
  │   ├── load_soul_text()            ← soul_sync.py
  │   ├── _build_knowledge_context()  ← knowledge_retrieval.py
  │   └── build_snapshot()            ← orchestrator.py
  │
  └── pre_tool_call:
      ├── validate_tool_call()        ← tool_guard.py
      └── tool_executor.py            ← subprocess aislado (TTL 30s)

DLP Pipeline (tras respuesta LLM):
  sanitizer.py → dlp.py → truncation.py → pagination.py → dlp_final.py
```

---

## 📊 Variables de entorno (.env)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `HERMES_HOME` | `~/.hermes` | Directorio base del agente |
| `WHATSAPP_BRIDGE_URL` | `http://localhost:3000` | URL del bridge WhatsApp |
| `WHATSAPP_ALLOWED_USERS` | - | Números de teléfono autorizados (owner) |
| `ADMIN_PHONE` | - | Teléfono del admin |
| `DEFAULT_COUNTRY_CODE` | `34` | Código de país para normalizar JIDs |
| `ANDORINA_DELIVERY_WINDOW` | `60` | Minutos que una tarea agendada sigue viva |
| `ANDORINA_CRON_OFFSET` | `2` | Minutos de separación entre tareas concurrentes |
| `ANDORINA_TARGET_CONTEXT` | `75000` | Ventana de contexto (tokens) |
| `ANDORINA_TARGET_USER_MEM` | `5000` | Límite memoria usuario (chars) |
| `ANDORINA_TARGET_SYS_MEM` | `5000` | Límite memoria sistema (chars) |
| `ANDORINA_BOT_PHONE` | - | Teléfono del bot |
| `ANDORINA_WEBHOOK_URL` | - | URL pública del webhook |
| `AWAY_COOLDOWN_SECS` | `3600` | Cooldown auto-respuesta ausencia |
| `GOOGLE_CONTACTS_CLIENT_ID` | - | OAuth2 Client ID Google |
| `GOOGLE_CONTACTS_CLIENT_SECRET` | - | OAuth2 Client Secret Google |
| `GOOGLE_CONTACTS_REFRESH_TOKEN` | - | Refresh token OAuth2 |

---

## 📝 Notas finales

- Los `__init__.py` están vacíos intencionalmente (imports vía `sys.path.append`).
- El directorio `scripts/bin/` está vacío (reservado para futuros binarios compilados).
- `docs/` es la web pública — no contiene lógica de la skill.
- Para crear nuevas funcionalidades, extiende los módulos existentes; no crees nuevos archivos sin consultar este documento.
