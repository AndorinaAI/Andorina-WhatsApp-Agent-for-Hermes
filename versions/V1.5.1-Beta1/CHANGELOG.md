# 📝 Changelog - Andoriña

---

## [v1.5.1-Beta1] - 2026-06-07
**🩹 Hotfix — Bridge Stability / Hotfix — Estabilidad del Puente**

### 🐛 Critical Fixes

- **Bridge Restart Loop (Critical):** `bridge_health.py` was checking for the string `"from: senderId"` as a patch marker — a string that `patch_bridge.py` has never written. This caused `apply_repair()` to always consider the bridge "unpatched" and restart it on every call, including from scheduled message cron jobs. The bridge was being killed every time a scheduled message fired. Fixed by aligning markers with what `patch_bridge.py` actually writes.
- **Node.js `ReferenceError` Crash (Critical):** The `fromMe` inbox patch in `patch_bridge.py` injected code using `existsSync`, `readFileSync`, `writeFileSync`, and `path.join()` without declaring them locally, assuming they were available from bridge.js global imports. Different Hermes/Baileys versions import them differently (or as `fs.*`). This caused a silent `ReferenceError` that killed the Node.js bridge process. Fixed with inline `require('fs')` / `require('path')` — the fix is now self-contained.
- **Stale Hook Warnings:** `setup.py` now removes obsolete hook events (`message_received`, `whatsapp:message`) from `config.yaml` on install/upgrade, eliminating the `WARNING agent.shell_hooks: unknown hook event` log spam.

### 🔧 Improvements
- `ensure_patched()` now retries 3 times (6s total) before triggering repair, avoiding false alarms from a slow bridge startup or momentary load.
- `check_patches.py` markers updated: removed phantom `sender_id_fix` marker, `fromMe` check updated to detect the new v2 patch.

---

## [v1.5.0-Beta1] - 2026-06-07
**"The Architectural Refactor & Tool Polish Update" / "Actualización de Refactor Arquitectónico y Pulido de Herramientas"**


> [!WARNING]
> **🔬 BETA — Requires Testing / BETA — Requiere Testing**
> This is a major architectural refactor covering the security pipeline, scheduling mechanisms, UI components, and webhook routing.

### 🇺🇸 English

#### 🔒 Security & Orchestration Pipeline (Zero-Trust Refactor)
- **Centralized `_resolve_jid()` Identity Layer:** Identity resolution has been moved to a module-level function executed *before* all other logic. It robustly resolves WhatsApp LIDs to Canonical phone numbers via `lid-mapping-*_reverse.json` or local cache.
- **Input & Tool Guard:** Added `input_guard.py` and `tool_guard.py` acting as pre-execution validation gates. They restrict access to allowed folders and chats, enforce strict 30-second execution timeouts for subprocesses, and sanitize LLM tool calls.
- **`reasoning_content` Strip:** System actively recursively strips reasoning and thinking blocks from conversation histories to avoid context contamination in the RAG engine.
- **Group Soul Sync Heuristic:** Fixed a critical routing bug by implementing a length-based heuristic (≥15 digits) in `soul_sync.py` to differentiate Group Epoch IDs (`@g.us`) from personal numbers (`@s.whatsapp.net`), ensuring Group Sub-Souls apply properly.

#### 🛠️ Tool Enhancements
- **Agenda (Collision Avoidance):** `agenda.py` now implements an intelligent **Delivery Window** (60 min default) and an **Auto-Offset Mechanism** (2 mins default) for tasks scheduled simultaneously, preventing LLM bot collision. It also supports `recurring` cron jobs safely.
- **Semantic Alerts Notification:** `alerts.py` now automatically sends a privacy notification to the alert target when a new forwarding rule is established, increasing transparency.
- **Advanced Contacts & Notes:** `contacts.py` now supports section-based permanent memory updating via `note-section-set`, in addition to `note-add`, `note-read`, and `note-clear`, serving as the LLM's Long Term Memory.
- **Inbox Idempotency:** The `patch_whatsapp.py` hook payload now explicitly defines `"write_inbox": False` for webhook executions, fully eliminating the duplicate message logging bug in `inbox.json`.
- **Typing Simulation:** `send.py` actively queries the `/typing` bridge endpoint to simulate human composing time based on message length.

#### 🖥️ GUI & Live Monitor
- **Live Monitor (`monitor.html`):** Added a new, fully localized real-time log inspector component in the Web UI for tracking Bridge, Agent, and Server events with autoscroll functionality.
- **UI Localization & Sticky Headers:** The entire interface now supports dynamic i18n translation strings (EN/ES) with persistent chat sticky headers and toggle states for chatbots/away messages.

---

### 🇪🇸 Español

#### 🔒 Tubería de Seguridad y Orquestación (Refactor Zero-Trust)
- **Capa de Identidad `_resolve_jid()` Centralizada:** La resolución de identidad se ha movido para ejecutarse *antes* de toda lógica. Resuelve robustamente LIDs de WhatsApp a números Canónicos mediante `lid-mapping-*_reverse.json` o caché local.
- **Guardias de Entrada y Herramientas:** Añadidos `input_guard.py` y `tool_guard.py` como puertas de validación previas a la ejecución. Restringen el acceso a carpetas y chats permitidos, imponen tiempos de espera estrictos de 30 segundos y sanean llamadas de herramientas.
- **Borrado de `reasoning_content`:** El sistema elimina recursiva y activamente los bloques de razonamiento del historial de conversaciones para evitar contaminación del contexto en el motor RAG.
- **Heurística de Sincronización de Souls de Grupo:** Corregido un bug crítico de enrutamiento implementando una heurística basada en la longitud (≥15 dígitos) en `soul_sync.py` para diferenciar IDs de Grupo (`@g.us`) de números personales (`@s.whatsapp.net`), asegurando que las personalidades de grupo se apliquen.

#### 🛠️ Mejoras en Herramientas
- **Agenda (Evasión de Colisiones):** `agenda.py` ahora implementa una **Ventana de Entrega** (60 min) y un mecanismo de **Auto-Offset** (2 mins) para tareas programadas simultáneamente, evitando choques del bot. También soporta tareas recurrentes.
- **Notificación de Alertas Semánticas:** `alerts.py` ahora envía automáticamente una notificación de privacidad al objetivo cuando se establece una regla de reenvío.
- **Contactos y Notas Avanzadas:** `contacts.py` soporta edición de memoria a largo plazo por secciones vía `note-section-set`, además de `note-add/read/clear`.
- **Idempotencia del Inbox:** El payload en `patch_whatsapp.py` ahora define `"write_inbox": False`, eliminando por completo la duplicación de mensajes en `inbox.json`.
- **Simulación de Escritura:** `send.py` envía solicitudes activas de `composing` basadas en la longitud del mensaje.

#### 🖥️ GUI y Monitor en Vivo
- **Monitor en Vivo (`monitor.html`):** Añadido un componente UI inspector de logs en tiempo real para rastrear eventos del Bridge, Agente y Servidor, completamente traducido y con autoscroll.
- **Localización UI:** La interfaz completa soporta strings i18n (EN/ES), cabeceras pegajosas y estados globales visuales.

---

## [v1.5-Beta1.1] - 2026-06-01
**"The Security Refactor & Knowledge Engine Fix"**
- **Root Cause Found & Fixed:** Knowledge Base injection moved from `messages` to `context` to ensure RAG delivery on Hermes.
- **Restricted Access Mode:** Chatbots with `allowed_folders` correctly promote to `restricted_access` mode with explicit file-read permissions via RBAC `tool_guard.py`.
- **Auto-Patch Installer:** `patch_*.py` tools bundled into the deploy directory.

---

## [v1.5-Beta1] - 2026-05-28
**"The V2 Sandbox & Knowledge Update"**
- **Sandbox Engine:** Groundwork for V2 Sandbox architecture (plugins & games).
- **Auto-RAG:** Automatic TXT/PDF file context injection.
- **Sub-Soul Icons:** UI rendering for `[icon: X]` Markdown tags.

---

## [v1.5.0] - 2026-05-25
- **Modular Directory:** Flatted scripts refactored to `security/`, `tools/`, `transport/`, `utils/`.
- **RBAC Foundation:** Intro of `owner`, `manager`, `chatbot`, `blocked` rules.
- **Output Pipeline (DLP):** Truncation limits for Anti-DoS.

---

## [v1.0.5] - 2026-05-21
- **Fuzzy Semantic Alerts:** Rules engine normalizing accents.
- **Mass Messaging & Recurring Tasks:** `broadcast` added.

---

## [v1.0.4-Beta2] - 2026-05-19
- **Test Runner Fixes:** Validation tests fixed for pytest environments.
- **Common Module:** Unified `common.py` HTTP methods.

---

## [v1.0.3] - 2026-05-12
- **Embedded Zero-Config Auth:** Embedded Google OAuth setup via `auth.py`.

---

## [v1.0.2] - 2026-05-09
- **Media Isolation:** Per-agent image cache isolation.
