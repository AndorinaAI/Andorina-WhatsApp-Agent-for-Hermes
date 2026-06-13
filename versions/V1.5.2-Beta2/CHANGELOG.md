# 📝 Changelog - Andoriña

---

## [v1.5.2-Beta2] - 2026-06-10
**🔧 Bug Fix Release — Security Bypass, Webhooks, Memory & Banner**
**🔧 Versión de Corrección de Errores — Seguridad, Webhooks, Memoria y Banner**

> [!NOTE]
> Patch release — all fixes are applied automatically on update via the GUI updater.
> Versión de parche — todas las correcciones se aplican automáticamente al actualizar desde el panel.

### 🇺🇸 English

#### 🐛 Bug Fixes
- **TUI/CLI Blocked by RBAC (Critical):** `orchestrator_hook.py` was applying WhatsApp identity checks to ALL Hermes sessions, including local TUI/CLI sessions. The owner using Hermes TUI was denied all actions. Fixed by adding `_is_whatsapp_session()` — RBAC now only applies to incoming WhatsApp messages; local sessions are allowed through unconditionally.
- **Webhook Port Hardcoded to 3001:** `GUI/server.py` `_detect_public_url()` fallback used `"3001"` instead of the actual server port (`PORT = 8888`), making all webhook URLs point to the wrong port. Fixed to use `str(PORT)`.
- **Contacts Notes Never Written or Read:** The LLM had no instructions to proactively save or retrieve contact notes. Added `MEMORY RULES` to `setup_lib.py` `optimize_soul()` so the SOUL.md instructs the agent to silently run `note-add` after meaningful conversations and `note-read` at the start of each new conversation.
- **Updater Didn't Patch SOUL.md:** `andorina_updater.py` registered hooks on update but never called `optimize_soul()`, so improvements to the system prompt were never applied on existing installations. Fixed in step 7c — the updater now reads `ADMIN_PHONE` from `.env` and runs `optimize_soul()` after every successful update.

#### ✨ Improvements
- **Banner i18n:** The live announcement banner now fetches `banner_andorina_en.txt` when the panel language is set to English, and the Spanish file when in ES. Banner scroll speed slowed from 35s to 55s for readability.
- **Banner Loaded at Startup:** The remote banner is now fetched and displayed on every panel load (not only when an update is pending).

---

### 🇪🇸 Español

#### 🐛 Correcciones de Errores
- **TUI/CLI Bloqueado por RBAC (Crítico):** `orchestrator_hook.py` aplicaba las comprobaciones de identidad de WhatsApp a TODAS las sesiones de Hermes, incluidas las sesiones locales TUI/CLI. El dueño usando el TUI de Hermes tenía denegadas todas las acciones. Corregido añadiendo `_is_whatsapp_session()` — el RBAC ahora solo se aplica a mensajes de WhatsApp entrantes; las sesiones locales pasan sin restricciones.
- **Puerto de Webhooks Fijado en 3001:** El fallback de `_detect_public_url()` en `GUI/server.py` usaba `"3001"` en lugar del puerto real del servidor (`PORT = 8888`), haciendo que todas las URLs de webhook apuntasen al puerto incorrecto. Corregido usando `str(PORT)`.
- **Notas de Contactos Sin Escribir ni Leer:** El LLM no tenía instrucciones para guardar o recuperar notas de contactos de forma proactiva. Añadidas `MEMORY RULES` en `optimize_soul()` de `setup_lib.py` para que el SOUL.md instruya al agente a ejecutar silenciosamente `note-add` tras conversaciones relevantes y `note-read` al inicio de cada nueva conversación.
- **El Actualizador No Parcheaba el SOUL.md:** `andorina_updater.py` registraba los hooks en cada actualización pero nunca llamaba a `optimize_soul()`, por lo que las mejoras al system prompt nunca se aplicaban en instalaciones existentes. Corregido en el paso 7c — el actualizador ahora lee `ADMIN_PHONE` del `.env` y ejecuta `optimize_soul()` tras cada actualización exitosa.

#### ✨ Mejoras
- **Banner i18n:** El banner de anuncios en vivo ahora descarga `banner_andorina_en.txt` cuando el panel está en inglés, y el archivo en español cuando está en ES. La velocidad de desplazamiento del banner se ha reducido de 35s a 55s para mayor legibilidad.
- **Banner Visible al Cargar:** El banner remoto ahora se descarga y muestra en cada carga del panel (no solo cuando hay una actualización pendiente).

---

## [v1.5.1-Beta1] - 2026-06-07
**🩹 Hotfix — Bridge Stability / Hotfix — Estabilidad del Puente**

### 🇺🇸 English

#### 🐛 Critical Fixes
- **Bridge Restart Loop (Critical):** `bridge_health.py` was checking for the string `"from: senderId"` as a patch marker — a string that `patch_bridge.py` has never written. This caused `apply_repair()` to always consider the bridge "unpatched" and restart it on every call, including from scheduled message cron jobs. The bridge was being killed every time a scheduled message fired. Fixed by aligning markers with what `patch_bridge.py` actually writes.
- **Node.js `ReferenceError` Crash (Critical):** The `fromMe` inbox patch in `patch_bridge.py` injected code using `existsSync`, `readFileSync`, `writeFileSync`, and `path.join()` without declaring them locally. Different Hermes/Baileys versions import them differently (or as `fs.*`). This caused a silent `ReferenceError` that killed the Node.js bridge process. Fixed with inline `require('fs')` / `require('path')` — the fix is now self-contained.
- **Stale Hook Warnings:** `setup.py` now removes obsolete hook events (`message_received`, `whatsapp:message`) from `config.yaml` on install/upgrade, eliminating the `WARNING agent.shell_hooks: unknown hook event` log spam.

#### 🔧 Improvements
- `ensure_patched()` now retries 3 times (6s total) before triggering repair, avoiding false alarms from a slow bridge startup or momentary load.
- `check_patches.py` markers updated: removed phantom `sender_id_fix` marker, `fromMe` check updated to detect the new v2 patch.

---

### 🇪🇸 Español

#### 🐛 Correcciones Críticas
- **Bucle de Reinicio del Bridge (Crítico):** `bridge_health.py` buscaba la cadena `"from: senderId"` como marcador de parche — una cadena que `patch_bridge.py` nunca ha escrito. Esto hacía que `apply_repair()` considerase siempre el bridge como "no parcheado" y lo reiniciase en cada llamada, incluso desde los trabajos cron de mensajes programados. El bridge se terminaba cada vez que se disparaba un mensaje programado. Corregido alineando los marcadores con lo que `patch_bridge.py` realmente escribe.
- **Crash `ReferenceError` de Node.js (Crítico):** El parche del inbox `fromMe` en `patch_bridge.py` inyectaba código usando `existsSync`, `readFileSync`, `writeFileSync` y `path.join()` sin declararlos localmente. Distintas versiones de Hermes/Baileys los importan de forma diferente (o como `fs.*`). Esto causaba un `ReferenceError` silencioso que mataba el proceso Node.js del bridge. Corregido con `require('fs')` / `require('path')` en línea — la corrección es ahora autocontenida.
- **Advertencias de Hooks Obsoletos:** `setup.py` ahora elimina eventos de hook obsoletos (`message_received`, `whatsapp:message`) de `config.yaml` en cada instalación/actualización, eliminando el spam de `WARNING agent.shell_hooks: unknown hook event` en los logs.

#### 🔧 Mejoras
- `ensure_patched()` ahora reintenta 3 veces (6s en total) antes de activar la reparación, evitando falsas alarmas por un arranque lento del bridge o carga momentánea.
- Marcadores de `check_patches.py` actualizados: eliminado el marcador fantasma `sender_id_fix`, comprobación de `fromMe` actualizada para detectar el nuevo parche v2.

---

## [v1.5.2-Beta2] - 2026-06-07
**"The Architectural Refactor & Tool Polish Update" / "Actualización de Refactor Arquitectónico y Pulido de Herramientas"**

> [!WARNING]
> **🔬 BETA — Requires Testing / BETA — Requiere Testing**
> This is a major architectural refactor covering the security pipeline, scheduling mechanisms, UI components, and webhook routing.
> Esta es una refactorización arquitectónica mayor que abarca la tubería de seguridad, los mecanismos de programación, los componentes UI y el enrutamiento de webhooks.

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
**"The Security Refactor & Knowledge Engine Fix" / "Refactor de Seguridad y Corrección del Motor de Conocimiento"**

- **Root Cause Found & Fixed / Causa Raíz Encontrada y Corregida:** Knowledge Base injection moved from `messages` to `context` to ensure RAG delivery on Hermes. / La inyección de la Base de Conocimiento se movió de `messages` a `context` para asegurar la entrega RAG en Hermes.
- **Restricted Access Mode / Modo de Acceso Restringido:** Chatbots with `allowed_folders` correctly promote to `restricted_access` mode with explicit file-read permissions via RBAC `tool_guard.py`. / Los chatbots con `allowed_folders` promueven correctamente al modo `restricted_access` con permisos explícitos de lectura de archivos vía RBAC `tool_guard.py`.
- **Auto-Patch Installer / Instalador de Parches Automático:** `patch_*.py` tools bundled into the deploy directory. / Las herramientas `patch_*.py` se incluyeron en el directorio de despliegue.

---

## [v1.5-Beta1] - 2026-05-28
**"The V2 Sandbox & Knowledge Update" / "Actualización V2 Sandbox y Conocimiento"**

- **Sandbox Engine / Motor Sandbox:** Groundwork for V2 Sandbox architecture (plugins & games). / Base para la arquitectura V2 Sandbox (plugins y juegos).
- **Auto-RAG:** Automatic TXT/PDF file context injection. / Inyección automática de contexto desde archivos TXT/PDF.
- **Sub-Soul Icons / Iconos Sub-Soul:** UI rendering for `[icon: X]` Markdown tags. / Renderizado UI para etiquetas Markdown `[icon: X]`.

---

## [v1.5.0] - 2026-05-25
**"Modular Refactor" / "Refactor Modular"**

- **Modular Directory / Directorio Modular:** Flatted scripts refactored to `security/`, `tools/`, `transport/`, `utils/`. / Scripts reorganizados en `security/`, `tools/`, `transport/`, `utils/`.
- **RBAC Foundation / Base RBAC:** Intro of `owner`, `manager`, `chatbot`, `blocked` rules. / Introducción de los roles `owner`, `manager`, `chatbot`, `blocked`.
- **Output Pipeline (DLP):** Truncation limits for Anti-DoS. / Límites de truncado Anti-DoS.

---

## [v1.0.5] - 2026-05-21
- **Fuzzy Semantic Alerts / Alertas Semánticas Difusas:** Rules engine normalizing accents. / Motor de reglas normalizando acentos.
- **Mass Messaging & Recurring Tasks / Mensajería Masiva y Tareas Recurrentes:** `broadcast` added. / Añadido `broadcast`.

---

## [v1.0.4-Beta2] - 2026-05-19
- **Test Runner Fixes / Correcciones del Test Runner:** Validation tests fixed for pytest environments. / Tests de validación corregidos para entornos pytest.
- **Common Module / Módulo Común:** Unified `common.py` HTTP methods. / Métodos HTTP unificados en `common.py`.

---

## [v1.0.3] - 2026-05-12
- **Embedded Zero-Config Auth / Autenticación Sin Configuración Embebida:** Embedded Google OAuth setup via `auth.py`. / Flujo OAuth de Google embebido vía `auth.py`.

---

## [v1.0.2] - 2026-05-09
- **Media Isolation / Aislamiento de Medios:** Per-agent image cache isolation. / Aislamiento de caché de imágenes por agente.
