# 🌟 Andoriña v1.5.2-Beta1 — Complete Feature Reference
## 🇬🇧 English | 🇪🇸 Español

> [!WARNING]
> **🔬 BETA — Requires Testing / BETA — Requiere Testing**
> This version includes a massive architectural refactor to the security engine. While the installation process and core features should work perfectly, some edge-case functions have not been fully tested in production yet.
> Esta versión incluye una refactorización arquitectónica masiva del motor de seguridad. Aunque la instalación y las funciones principales deberían funcionar perfectamente, algunas funciones de casos límite aún no se han probado completamente.

---

## 🔧 What's New in v1.5.2-Beta1 (Bug Fix Release)
## 🔧 Novedades en v1.5.2-Beta1 (Versión de Corrección de Errores)

### 🇺🇸 English

| # | Bug / Feature | Files Changed |
|:---|:---|:---|
| 🐛 | **TUI/CLI bypass** — RBAC no longer blocks the local owner using Hermes TUI. `_is_whatsapp_session()` added to only apply security checks to real WhatsApp sessions. | `orchestrator_hook.py` |
| 🐛 | **Webhook port 3001 → 8888** — `_detect_public_url()` now uses `str(PORT)` instead of hardcoded `"3001"`. | `GUI/server.py` |
| 🐛 | **Contacts notes never persisted** — Added `MEMORY RULES` to `optimize_soul()` so the agent silently calls `note-add` after conversations and `note-read` at the start of each new one. | `setup_lib.py`, `SOUL.md` |
| 🐛 | **Updater skipped SOUL.md patch** — `andorina_updater.py` now calls `optimize_soul()` (step 7c) on every update, ensuring system prompt improvements propagate to existing installs. | `andorina_updater.py` |
| ✨ | **Banner i18n** — Banner fetches `banner_andorina_en.txt` when the UI is in English, ES file otherwise. Scroll speed reduced to 55 s. | `server.py`, `app.js`, `index.html` |
| ✨ | **Banner on every load** — Remote announcement banner now displays on startup, not only when an update is pending. | `app.js` |

### 🇪🇸 Español

| # | Error / Mejora | Archivos Modificados |
|:---|:---|:---|
| 🐛 | **Bypass TUI/CLI** — El RBAC ya no bloquea al dueño local usando el TUI de Hermes. Añadida `_is_whatsapp_session()` para aplicar comprobaciones de seguridad solo a sesiones reales de WhatsApp. | `orchestrator_hook.py` |
| 🐛 | **Puerto webhook 3001 → 8888** — `_detect_public_url()` ahora usa `str(PORT)` en lugar del `"3001"` hardcodeado. | `GUI/server.py` |
| 🐛 | **Notas de contactos sin persistir** — Añadidas `MEMORY RULES` a `optimize_soul()` para que el agente llame silenciosamente a `note-add` tras conversaciones y a `note-read` al inicio de cada nueva. | `setup_lib.py`, `SOUL.md` |
| 🐛 | **El actualizador omitía el parche del SOUL.md** — `andorina_updater.py` ahora llama a `optimize_soul()` (paso 7c) en cada actualización, asegurando que las mejoras al system prompt se propaguen a instalaciones existentes. | `andorina_updater.py` |
| ✨ | **Banner i18n** — El banner descarga `banner_andorina_en.txt` cuando la UI está en inglés, y el archivo ES en caso contrario. Velocidad de scroll reducida a 55 s. | `server.py`, `app.js`, `index.html` |
| ✨ | **Banner en cada carga** — El banner remoto ahora se muestra al arrancar el panel, no solo cuando hay una actualización pendiente. | `app.js` |

---


## 🇬🇧 ENGLISH — ALL FEATURES & CAPABILITIES

### 📤 1. Text Messaging
- Send a text message to **any contact or group** immediately via `transport/send.py message`.
- Mass messaging supported via `transport/send.py broadcast`, with built-in pacing (2-5s random delays) to prevent bans.
- Messages are sent through a local HTTP bridge (default `http://localhost:3000`).
- The bridge URL is fully configurable via `WHATSAPP_BRIDGE_URL` in `.env`.
- Supports **group IDs** (`@g.us`) and **individual contacts** (`@s.whatsapp.net`).

### 🎙️ 2. Voice Notes (PTT)
- Send audio files as native **Push-To-Talk (PTT)** messages via `tools/files.py --voice`.
- Before sending, the agent shows **"Recording audio..."** status to the receiver for 3 seconds.
- Supports `.ogg` and `.opus` formats natively.
- The `ptt` flag is sent to the bridge to trigger the native voice note player on the recipient's device.

### 📁 3. Multimedia & Document Sending
- Send **images**, **videos**, **documents**, and **audio** from any local path via `tools/files.py` or `transport/send.py message --file`.
- Supports absolute path resolution — instantly blocked by Path Traversal shields if targeting sensitive folders (`/etc/`, `/var/`).
- Before sending, the agent shows **"Composing..."** presence to mimic natural behavior.
- Extended MIME support via the bridge patcher: `.heic`, `.webp`, `.md`, `.csv`, `.xcf`, `.psd`, `.opus`, etc.
- **Caption support:** Add text directly to images and documents.

### 📅 4. Smart Scheduling (Agenda)
- Schedule text messages, files, or voice notes via `tools/agenda.py auto-schedule`.
- Create **recurring tasks** via `tools/agenda.py recurring add <cron_expr> <msg>`.
- Supported time formats: `HH:MM`, `DD HH:MM`, `DD/MM/YYYY HH:MM` (24-hour clock).
- Schedules are registered as **native Linux `crontab` jobs** — no daemon needed.
- **Crontab Isolation:** `HERMES_HOME` and `HERMES_CMD` are injected into every cron job for multi-agent compatibility.
- **Auto-Offset (Collision Avoidance):** If two tasks share the same minute, the second is automatically pushed by 2 minutes.
- List all pending tasks: `tools/agenda.py list`.
- Cancel a pending task: `tools/agenda.py remove <msg_id>` (protected by RBAC `--creator-jid`).

### 📒 5. Contact & Group Discovery
- **Universal Search** across Google Contacts and WhatsApp Groups: `tools/contacts.py search "Query"`.
- **Long-Term Memory (Notes):** Add permanent memories for a user via `tools/contacts.py note-add "JID" "Text"`. These notes are stored in `state/notes/`.
- **Contextual Search:** Filter contacts by their saved notes using `--filter-tags`.
- **Avatar Fetching:** Automatically downloads high-res avatars from Google Photos API.
- **Fuzzy Search:** NFD unicode normalization — ignores accents, casing, and special characters. Finds "María" even if you type "maria".
- **Google People API** integration with full OAuth2 flow (`auth.py`) and automatic `refresh_token` rotation.
- **Group listing:** `tools/contacts.py groups` — fetches live from bridge, falls back to `channel_directory.json` cache.

> **⚠️ Group Discovery Limitation:** `contacts.py groups` and `contacts.py search` retrieve groups directly from the live WhatsApp bridge. If the bridge is offline, it falls back to Hermes cache. Always ensure the bridge is online before searching for groups.

### 📥 6. Inbox (Incoming Messages)
- Every incoming WhatsApp message is **captured and stored locally** in `state/inbox.json` via `transport/webhook.py`.
- **Deep History Search:** Search past conversations via `tools/inbox.py search "query" --days 7`.
- **List conversations:** `tools/inbox.py list` — shows unique chats sorted by most recent message.
- **History cap:** Inbox is capped at 500 entries to prevent file bloat. Users can wipe specific chats via `tools/inbox.py delete`.
- **RBAC Privacy:** Users can only read chats they are authorized for via `--filter-chats`.

### 🛡️ 7. Security Firewall (Guard) & DLP
- **Multi-layered Orchestrator:** Tools are executed in strict `shlex`-parsed subprocesses with a 30-second hard timeout.
- **Pre-LLM Fast-Fail:** Uses `pre_llm_call` hooks in Hermes `config.yaml` to reject blocked users before invoking the LLM, saving 100% of API token costs.
- **RBAC Engine (`guard_rules.json`):** Assign dynamic roles (Owner, Manager, Chatbot, Blocked). Control exactly who can use which commands and which folders (`allowed_folders`).
- **Data Loss Prevention (DLP):** Post-generation pipeline (`pipeline.py`) sanitizes the LLM's raw output to prevent token or API key leakage and forcefully truncates/paginates massive spam responses.
- **Semantic Topic Alerts:** Configure the bot to listen to specific groups/chats and forward you alerts if fuzzy keywords are mentioned via `tools/alerts.py`.
- **Away Auto-Responder:** Completely integrated `away.json` into the message webhook. Checks user cooldowns and automatically routes responses through the DLP pipeline.

### 🤖 8. Multi-Agent Support
- **Full profile isolation:** All paths, logs, caches, and cron jobs are scoped to `HERMES_HOME`.
- **Auto-detection in installer:** `install.sh` scans for agent profiles and presents a selection menu.
- **Environment injection:** `HERMES_HOME` and `HERMES_CMD` are exported before all sub-processes.
- **Independent cron jobs:** Each agent's scheduled messages run in their own environment context.

### 🔧 9. Anti-Ban & Human Simulation Engine
- **Request Pacing (1.0s):** Every message and media send includes a 1-second delay before the HTTP request.
- **Typing Simulation:** Before sending text, the agent triggers `"composing"` presence. Duration scales with message length.
- **Recording Simulation:** Before sending voice notes, the agent triggers `"recording"` presence for 3 seconds.
- **Auto-Offset Scheduling:** Concurrent scheduled tasks are spread across minutes to avoid bot-like burst patterns.

### ⚕️ 10. Infrastructure & Self-Healing
- **`bridge_health.py`:** Patches `bridge.js` dinámicamente for MIME, PTT, health endpoint, and presence indicators.
- **Always creates a backup** (`bridge_andorina_bak.js`) before writing any patch.
- **`patch_bridge.py`:** Adds the `/profile-pic/:jid` endpoint directly into the Baileys bridge.

### 🔑 11. Google OAuth2 Authentication
- **`auth.py`:** Interactive terminal-based OAuth2 flow for Google People API.
- Generates the authorization URL, receives the code, and exchanges it for `access_token` + `refresh_token`.
- Tokens are saved directly to the agent's `.env`.

### 🖥️ 12. Andoriña Desktop Panel (GUI)
- **`Andorina-Panel.sh`:** A fully graphical Linux Dashboard for visual management.
- Manage RBAC states, Sub-Souls, and Inbox histories without touching the terminal.
- Built-in installer automation generating all JSON states (`chatbot.json`, `away.json`, `guard_rules.json`).

### 🏗️ 13. Sub-Soul & Sandbox Engine (V2)
- **Sub-Soul Personalities:** Personalities are now modular. The system assigns instructions dynamically with priority: JSON rules, Markdown files (`state/souls/`), or safe defaults.
- **Custom Icons:** Dynamically extract avatars from Sub-Souls using `[icon: X]` Markdown tags.
- **Plugins & Games (Sandboxes) [Coming Soon]:** Owners will be able to create completely isolated Python environments that run locally for specific groups or users. 
- **Sandboxed Local DB [Coming Soon]:** Each Plugin/Game will get its own `state.db` to save game state, inventory, or plugin memory.
- **Background Processes [Coming Soon]:** Plugins will be able to schedule background events using `sdk.schedule_event()` without needing a cronjob.

### 📚 14. Knowledge Base (RAG)
- **Upload Documents:** Owners can upload TXT, PDF, and CSV files directly from the Web Panel's Knowledge tab.
- **Auto-Injection:** The system automatically extracts text from the documents and seamlessly injects it into the LLM's prompt context when a user talks to that specific Sandbox or Sub-Soul.

### ☁️ 15. Cloudflare Tunnel (Remote Access)
- **Built-in Tunnel Engine (`tunnel.py`):** Exposes the Web Panel to the internet through an encrypted Cloudflare tunnel with zero configuration required.
- **Quick Tunnel (Free):** With a single click in the Panel, `cloudflared` is auto-downloaded and a temporary `*.trycloudflare.com` URL is generated — no account needed.
- **Custom Domain (Paid Cloudflare):** If you have a Cloudflare account and a custom domain, you can supply a `--token` to bind the tunnel to your own permanent domain (e.g., `panel.midominio.com`).
- **Auto-Notification:** When the tunnel URL changes, the system automatically sends the new URL to all admin JIDs via WhatsApp.
- **GUI Integration:** Start/stop the tunnel and check its current status directly from the Web Panel's Settings tab.

### 🔄 16. Auto-Update System
- **GitHub-Based Updater (`andorina_updater.py`):** Polls the GitHub Releases API to detect new versions.
- **Check Mode (`--check`):** Returns JSON with current version, latest version, and download URL — safe and read-only.
- **Full Update Mode (`--update`):** Downloads the new ZIP, backs up all user data (`state/`, `.env`, `notes/`, `souls/`, `guard_rules.json`, `inbox.json`, etc.), replaces all code files, re-applies all bridge patches, and restores user data atomically.
- **Beta-Safe Parsing:** Uses semantic regex to parse version tags like `1.5.2-Beta1` — non-numeric suffixes never break the comparison.
- **GUI Integration:** The Web Panel's Settings tab shows current version, latest version, and a one-click "Update" button.

### 🛂 17. Granular RBAC — Full Permission Matrix
- **Four Built-in Roles:** `owner` (all), `manager` (subset), `chatbot` (LLM-only, no tools), `blocked` (immediate fast-fail before LLM).
- **Per-Role Permissions:** Each role has a list of explicit permissions:

| Permission Token | What it allows |
|:---|:---|
| `all` | Unrestricted access (owner-only) |
| `send_text` | Send text messages via `send.py message` |
| `send_file` | Send files via `files.py` |
| `send_voice` | Send PTT voice notes |
| `read_inbox` | Read `inbox.py read` |
| `search_history` | Search past messages with `inbox.py search` |
| `search_contacts` | Look up contacts with `contacts.py search` |
| `list_groups` | List WhatsApp groups |
| `add_alert` | Create semantic topic alerts |
| `get_role` | Query their own role |

- **`allowed_folders`:** Comma-separated list of absolute paths — a user with this restriction can only send files from these folders.
- **`allowed_chats`:** List of JIDs — restricts who a user can send messages *to* (prevents cross-user snooping). `"self"` is a special alias for their own JID.
- **`allowed_contact_tags`:** When set, the AI will only search/contact people who have these keywords saved in their notes profile.
- **`max_requests_per_hour`:** Rate-limits a specific user (e.g., `manager` gets 20 requests/hour, `owner` is unlimited).
- **`global_default_role`:** The role assigned to any unknown user not explicitly listed in `guard_rules.json`. Defaults to `chatbot`.
- **Live Management:**
  - Set role: `utils/admin_cli.py role set "JID" "manager"`
  - List all roles: `utils/admin_cli.py role list`
  - Remove from rules: `utils/admin_cli.py role remove "JID"`

### 🤖 18. Chatbot, Mute & Away Controls
- **Global Chatbot Toggle:** Completely enable/disable the LLM for all users: `utils/admin_cli.py chatbot on|off`.
- **Per-Contact Mute:** Silence the bot for a specific JID without changing their role: `utils/admin_cli.py chatbot mute "JID"` / `unmute "JID"`.
- **Away Auto-Responder:** Set a custom away message that fires automatically for any unanswered message (with a per-JID 1-hour cooldown): `utils/admin_cli.py away set "Texto..."`.
- **Away Status:** Check the current away text and cooldowns: `utils/admin_cli.py away status`.

### 🧠 19. Cognitive Reset & Log Wipe
- **Surgical Memory Wipe (`wipe_logs.py`):** Deletes Hermes `USER.md`, `MEMORY.md`, `.hermes_history`, local `inbox.json` and `agenda.json`, and all skill/Hermes log files — without touching the WhatsApp session, contacts, notes, or `guard_rules.json`.
- **Keeps WhatsApp safe:** Session files are never touched. The bot reconnects automatically.

### ⚙️ 20. Configurable Environment Variables
| Variable | Default | Description |
|:---|:---|:---|
| `HERMES_HOME` | `~/.hermes` | Base directory for the agent profile. |
| `WHATSAPP_BRIDGE_URL` | `http://localhost:3000` | URL of the WhatsApp bridge. |
| `WHATSAPP_ALLOWED_USERS` | _(empty)_ | Comma-separated list of authorized phone numbers (owners). |
| `ANDORINA_DELIVERY_WINDOW` | `60` | Minutes a scheduled task stays alive after its time. |
| `ANDORINA_CRON_OFFSET` | `2` | Minutes between concurrent cron tasks. |

---

## 🇪🇸 ESPAÑOL — TODAS LAS FUNCIONALIDADES Y CARACTERÍSTICAS

### 📤 1. Envío de Mensajes de Texto
- Envía un mensaje de texto a **cualquier contacto o grupo** de forma inmediata mediante `transport/send.py message`.
- Envío masivo mediante `transport/send.py broadcast`, con ritmo anti-baneo (retrasos aleatorios de 2-5s).
- Compatible con **IDs de grupo** (`@g.us`) e **individuales** (`@s.whatsapp.net`).

### 🎙️ 2. Notas de Voz (PTT)
- Envía archivos de audio como mensajes de **Push-To-Talk (PTT)** nativos mediante `tools/files.py --voice`.
- Antes de enviar, el agente muestra el estado **"Grabando audio..."** al receptor durante 3 segundos.

### 📁 3. Envío de Multimedia y Documentos
- Envía **imágenes**, **vídeos**, **documentos** y **audio** desde cualquier ruta local mediante `tools/files.py` o `transport/send.py message --file`.
- Escudo de Rutas Absolutas (Path Traversal) que bloquea accesos a `/etc/` o `/var/`.
- Soporte MIME ampliado: `.heic`, `.webp`, `.md`, `.csv`, `.xcf`, `.psd`, `.opus`, etc.
- **Pies de foto (Captions):** Añade texto directamente a las imágenes.

### 📅 4. Programación Inteligente (Agenda)
- Programa mensajes mediante `tools/agenda.py auto-schedule`.
- Tareas recurrentes (cron jobs) mediante `tools/agenda.py recurring add <cron_expr> <msg>`.
- **Aislamiento en Crontab:** `HERMES_HOME` y `HERMES_CMD` se inyectan en cada trabajo cron.
- Protección RBAC (`--creator-jid`) para evitar que un usuario borre alarmas de otro.

### 📒 5. Descubrimiento de Contactos y Grupos
- **Búsqueda Universal** en Google Contacts y WhatsApp: `tools/contacts.py search`.
- **Memoria a Largo Plazo (Notes):** Guarda datos sobre un usuario mediante `tools/contacts.py note-add`. Todo se guarda en `state/notes/`.
- **Búsqueda Contextual:** Filtra contactos por etiquetas en sus notas con `--filter-tags`.
- **Fotos de Perfil:** Descarga avatares de alta resolución mediante la API de Google Photos.
- **Búsqueda Difusa:** Ignora acentos y mayúsculas. Encuentra "María" aunque escribas "maria".

### 📥 6. Bandeja de Entrada (Mensajes Entrantes)
- Captura de mensajes en `state/inbox.json` mediante `transport/webhook.py`.
- **Búsqueda Histórica:** Busca en conversaciones pasadas con `tools/inbox.py search "query" --days 7`.
- **Privacidad RBAC:** Argumento `--filter-chats` para asegurar que cada usuario solo lee sus chats permitidos.
- **Borrado Selectivo:** Elimina chats locales con `tools/inbox.py delete`.

### 🛡️ 7. Cortafuegos de Seguridad y DLP (Guard)
- **Orquestador Multicapa:** Todas las herramientas se ejecutan en subprocesos aislados con límite estricto de 30s.
- **Hooks Nativos de Hermes:** Inyección de `pre_llm_call` para bloquear a usuarios no autorizados antes de gastar tokens de la IA.
- **Motor RBAC (`guard_rules.json`):** Control de acceso por roles (Owner, Manager, Chatbot). Límite de carpetas (`allowed_folders`) y chats de destino.
- **Tubería DLP (`pipeline.py`):** Sanea la salida bruta del LLM para evitar fuga de claves API y trunca respuestas gigantes.
- **Auto-Respuesta (Away):** Integrado en el webhook. Comprueba cooldowns y envía la respuesta por el escáner DLP.
- **Búsqueda Difusa de Alertas:** Algoritmo fuzzy en `tools/alerts.py` que normaliza tildes y plurales para capturar keywords siempre.

### 🤖 8. Soporte Multi-Agente
- **Aislamiento total de perfil:** Rutas, logs y cron jobs están delimitados a `HERMES_HOME`.
- **Detección automática en instalador:** Menú de selección de perfiles en `install.sh`.

### 🔧 9. Motor Anti-Baneo y Simulación Humana
- **Pacing de Peticiones (1.0s):** Retraso de 1 segundo antes de la petición HTTP.
- **Simulación de Escritura y Grabación:** Presencias `"composing"` y `"recording"`.

### ⚕️ 10. Infraestructura y Auto-Reparación
- **`bridge_health.py`:** Parchea `bridge.js` dinámicamente y crea backups.
- **`patch_bridge.py`:** Añadido el endpoint `/profile-pic/:jid`.

### 🔑 11. Autenticación OAuth2 con Google
- Flujo OAuth2 interactivo mediante `auth.py`. Auto-refresco de tokens en segundo plano.

### 🖥️ 12. Panel de Escritorio (GUI)
- **`Andorina-Panel.sh`:** Dashboard gráfico para Linux para gestión visual de RBAC, Sub-Souls y logs sin tocar la terminal.
- Auto-Setup de todos los estados JSON.

### 🏗️ 13. Arquitectura Sub-Soul y Sandboxes (V2)
- **Personalidades Modulares:** Permite asignar comportamientos completamente distintos por usuario vía `state/souls/`.
- **Iconos Personalizados:** El panel web parsea dinámicamente etiquetas Markdown `[icon: X]` para mostrar avatares de Sub-Souls.
- **Plugins y Juegos (Sandboxes) [Próximamente]:** Se podrán crear entornos aislados de Python que se ejecutan localmente e interceptan los mensajes antes que el LLM.
- **Base de Datos Local (State DB) [Próximamente]:** Cada plugin o juego obtendrá su propia base de datos aislada para guardar progreso o memoria del usuario.
- **Eventos en Segundo Plano [Próximamente]:** Los plugins podrán programar bucles infinitos (`sdk.schedule_event()`) sin depender de cronjobs.

### 📚 14. Base de Conocimiento (RAG)
- **Subida de Documentos:** Sube PDFs, TXTs o CSVs directamente desde la pestaña "Knowledge" del panel web.
- **Inyección Automática (Auto-RAG):** El motor lee dinámicamente el contenido de los archivos y lo inyecta ocultamente en el contexto de la Inteligencia Artificial al chatear.

### ☁️ 15. Túnel Cloudflare (Acceso Remoto)
- **Motor de Túnel Integrado (`tunnel.py`):** Expone el Panel Web a Internet mediante un túnel cifrado de Cloudflare sin configuración.
- **Túnel Rápido (Gratis):** Con un clic en el Panel, se descarga `cloudflared` automáticamente y se genera una URL temporal `*.trycloudflare.com` — sin cuenta.
- **Dominio Personalizado (Cloudflare de pago):** Si tienes cuenta en Cloudflare y un dominio propio, puedes vincular el túnel a una URL permanente (ej. `panel.midominio.com`) usando tu `--token`.
- **Notificación Automática:** Cuando la URL del túnel cambia, el sistema envía automáticamente la nueva URL a todos los JIDs administradores por WhatsApp.
- **Integración con GUI:** Inicia/detiene el túnel y consulta su estado desde la pestaña de Ajustes del Panel Web.

### 🔄 16. Sistema de Auto-Actualización
- **Actualizador basado en GitHub (`andorina_updater.py`):** Consulta la API de Releases de GitHub para detectar versiones nuevas.
- **Modo Consulta (`--check`):** Devuelve JSON con la versión actual, la última y la URL de descarga — seguro y sin cambios.
- **Modo Actualización (`--update`):** Descarga el ZIP, hace backup de todos los datos del usuario (`state/`, `.env`, `notes/`, `souls/`, `guard_rules.json`, `inbox.json`, etc.), reemplaza el código, re-aplica todos los parches del bridge y restaura los datos de forma atómica.
- **Soporte de Etiquetas Beta:** Usa regex semántico para parsear versiones como `1.5.2-Beta1` sin errores.
- **Integración GUI:** La pestaña de Ajustes muestra la versión actual, la última disponible y un botón "Actualizar" con un clic.

### 🛂 17. RBAC Granular — Matriz Completa de Permisos
- **Cuatro Roles Integrados:** `owner` (todo), `manager` (subconjunto), `chatbot` (solo LLM, sin herramientas), `blocked` (rechazo instantáneo antes del LLM).
- **Permisos por Rol:** Cada rol tiene una lista de tokens de permiso explícitos:

| Token de Permiso | Qué permite |
|:---|:---|
| `all` | Acceso sin restricciones (solo owner) |
| `send_text` | Enviar mensajes de texto con `send.py message` |
| `send_file` | Enviar archivos con `files.py` |
| `send_voice` | Enviar notas de voz PTT |
| `read_inbox` | Leer mensajes con `inbox.py read` |
| `search_history` | Buscar historial con `inbox.py search` |
| `search_contacts` | Buscar contactos con `contacts.py search` |
| `list_groups` | Listar grupos de WhatsApp |
| `add_alert` | Crear alertas semánticas |
| `get_role` | Consultar su propio rol |

- **`allowed_folders`:** Lista de rutas absolutas — el usuario solo puede enviar archivos desde esas carpetas.
- **`allowed_chats`:** Lista de JIDs — restringe a quién puede enviar mensajes. `"self"` es un alias especial para su propio JID.
- **`allowed_contact_tags`:** Cuando se establece, la IA solo busca/contacta personas que tengan estas palabras clave en sus notas.
- **`max_requests_per_hour`:** Limita el número de solicitudes por hora de un usuario específico.
- **`global_default_role`:** El rol asignado a cualquier usuario desconocido no listado en `guard_rules.json`. Por defecto: `chatbot`.
- **Gestión en Vivo:**
  - Asignar rol: `utils/admin_cli.py role set "JID" "manager"`
  - Listar todos: `utils/admin_cli.py role list`
  - Eliminar de las reglas: `utils/admin_cli.py role remove "JID"`

### 🤖 18. Control de Chatbot, Silencio y Ausencia
- **Toggle Global del Chatbot:** Activa/desactiva por completo el LLM para todos: `utils/admin_cli.py chatbot on|off`.
- **Silencio por Contacto:** Silencia al bot para un JID concreto sin cambiar su rol: `utils/admin_cli.py chatbot mute "JID"` / `unmute "JID"`.
- **Auto-Respuesta por Ausencia:** Configura un mensaje de ausencia que se envía automáticamente (con cooldown de 1 hora por JID): `utils/admin_cli.py away set "Texto..."`.
- **Estado de Ausencia:** Consulta el texto actual y los cooldowns activos: `utils/admin_cli.py away status`.

### 🧠 19. Reset Cognitivo y Limpieza de Logs
- **Borrado Quirúrgico de Memoria (`wipe_logs.py`):** Elimina `USER.md`, `MEMORY.md`, `.hermes_history`, `inbox.json`, `agenda.json` de Hermes y todos los logs de la skill — sin tocar la sesión de WhatsApp, los contactos, las notas ni `guard_rules.json`.
- **WhatsApp permanece seguro:** Los archivos de sesión nunca se tocan. El bot se reconecta solo.

### ⚙️ 20. Variables de Entorno Configurables
- Totalmente configurable en el archivo `.env` del agente (`HERMES_HOME`, `ANDORINA_CRON_OFFSET`, etc.).

---
*Developed with ❤️ by Jorge. — Andoriña v1.5.2*
