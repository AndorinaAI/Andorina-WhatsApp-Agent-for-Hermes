# 🌟 Andoriña v1.0.3-patch1 — Complete Feature Reference
## 🇬🇧 English | 🇪🇸 Español

---

## 🇬🇧 ENGLISH — ALL FEATURES & CAPABILITIES

### 📤 1. Text Messaging
- Send a text message to **any contact or group** immediately via `send.py message`.
- Messages are sent through a local HTTP bridge (default `http://localhost:3000`).
- The bridge URL is fully configurable via `WHATSAPP_BRIDGE_URL` in `.env`.
- Supports **group IDs** (`@g.us`) and **individual contacts** (`@s.whatsapp.net`).
- **Self-healing:** If the bridge fails mid-send, the system automatically attempts repair and retry (up to 3 attempts).

### 🎙️ 2. Voice Notes (PTT)
- Send audio files as native **Push-To-Talk (PTT)** messages via `files.py --voice`.
- Before sending, the agent shows **"Recording audio..."** status to the receiver for 3 seconds.
- Supports `.ogg` and `.opus` formats natively.
- The `ptt` flag is sent to the bridge to trigger the native voice note player on the recipient's device.

### 📁 3. Multimedia & Document Sending
- Send **images**, **videos**, **documents**, and **audio** from any local path via `files.py`.
- Supports absolute path resolution — no need to `cd` to the file location.
- Before sending, the agent shows **"Composing..."** presence to mimic natural behavior.
- Extended MIME support via the bridge patcher: `.heic`, `.bmp`, `.webp`, `.zip`, `.md`, `.csv`, `.rtf`, `.xls`, `.mp3`, `.wav`, `.ogg`, `.opus`, `.txt`.
- File existence and read-permission are checked **before** any network request.

### 📅 4. Smart Scheduling (Agenda)
- Schedule text messages, files, or voice notes via `agenda.py auto-schedule`.
- Supported time formats: `HH:MM`, `DD HH:MM`, `DD/MM HH:MM` (24-hour clock).
- Schedules are registered as **native Linux `crontab` jobs** — no daemon needed.
- **Crontab Isolation:** `HERMES_HOME` and `HERMES_CMD` are injected into every cron job for multi-agent compatibility.
- **Atomic Persistence:** The task is written to `state/agenda.json` **before** the cron is created. If cron fails, the task is still retained.
- **Delivery-Only Delete:** Messages are removed from `agenda.json` **only** on a confirmed successful delivery.
- **Auto-Offset (Collision Avoidance):** If two tasks share the same minute, the second is automatically pushed by 2 minutes (configurable via `ANDORINA_CRON_OFFSET`).
- **Delivery Window:** A task remains active for up to 60 minutes after its scheduled time (configurable via `ANDORINA_DELIVERY_WINDOW`), allowing late models to still deliver.
- List all pending tasks: `agenda.py list`.
- Cancel a pending task: `agenda.py remove <msg_id>` (also removes the cron job).

### 📒 5. Contact & Group Discovery
- **Universal Search** across Google Contacts and WhatsApp Groups: `contacts.py search "Query"`.
- **Fuzzy Search:** NFD unicode normalization — ignores accents, casing, and special characters. Finds "María" even if you type "maria".
- **Auto-refresh on miss:** If a contact is not found, the system automatically clears the local cache and re-fetches from Google Cloud before reporting failure.
- **Google People API** integration with full OAuth2 flow (`auth.py`) and automatic `refresh_token` rotation.
- **Group listing:** `contacts.py groups` — fetches live from bridge, falls back to `channel_directory.json` cache.
- **Full contact dump:** `contacts.py all` — JSON array of all known contacts.
- **Manual cache reset:** `contacts.py refresh` — forces a fresh cloud sync.
- Country code normalization: short numbers (8-10 digits) are automatically prefixed with `DEFAULT_COUNTRY_CODE`.

> **⚠️ Group Discovery Limitation:** `contacts.py groups` and `contacts.py search` retrieve groups directly from the live WhatsApp bridge (`/groups` endpoint) and will list **all groups** the account belongs to, regardless of chat history. However, if the **bridge is offline**, the fallback is `channel_directory.json` — a Hermes-managed local cache. If a group has **never appeared in that cache** (because Hermes hasn't registered it yet), it will not be found while offline. **The solution is always to ensure the bridge is online before searching for groups.**
>
> Additionally: `inbox.py list` will **only show groups that have sent at least one message** through the hook. A group where the assistant is a member but has received **no incoming messages** will not appear in the inbox. It can still be found and messaged via `contacts.py search` as long as the bridge is online.

### 📥 6. Inbox (Incoming Messages)
- Every incoming WhatsApp message is **captured and stored locally** in `state/inbox.json` via `hook_inbox.py`.
- The hook is registered in Hermes for both `message_received` and `whatsapp:message` events.
- **List conversations:** `inbox.py list` — shows unique chats sorted by most recent message.
- **Read history:** `inbox.py read <chatId>` — returns the last **50 messages** of a conversation (configurable in code).
- Chat ID normalization: if `@s.whatsapp.net` or `@g.us` suffix is missing, it is appended automatically.
- **History cap:** Inbox is capped at 500 entries to prevent file bloat.
- **Unicode-safe:** Input is read via `sys.stdin.buffer` to handle emojis and international characters without crashes.
- The agent can use the inbox to **summarize conversations**, **check who messaged**, **draft replies**, and **get context** before sending.

> **⚠️ Inbox Limitation — Silent Groups:** The inbox (`state/inbox.json`) is populated **exclusively by messages received through the hook** (`hook_inbox.py`). If the assistant is a member of a WhatsApp group but **no message has ever been sent to that group** (or no member has written since the skill was installed), that group will be **invisible to `inbox.py`**. It will not appear in `inbox.py list` and `inbox.py read` will return an empty result. This is expected behavior, not a bug. To interact with such a group, use `contacts.py search "group name"` to get its `chatId`, then send to it directly.

### 🛡️ 7. Security Firewall (Guard)
- **Two privilege tiers:**
  - **Owner mode (`full`):** Authorized phone numbers in `WHATSAPP_ALLOWED_USERS` get full AI access.
  - **Chatbot mode:** All other contacts interact with a restricted, friendly persona with no system access.
- **Prompt Injection Blocking:** 30+ regex patterns detect commands like `cat /etc/passwd`, path traversal (`../`), shell injections (`$(cmd)`), and social engineering phrases.
- **Obfuscation Detection:** Input is double-checked after stripping spaces and separators (catches `i g n o r e  r u l e s`).
- **Rate Limiting:** Non-owner contacts are subject to:
  - 5-minute cooldown between messages (`COOLDOWN_SECS=300`).
  - Max 10 messages per hour (`MAX_MSGS_PER_HOUR`).
- **Input Length Cap:** Messages over 500 characters are blocked.
- **Privacy Hashing:** Contact identifiers are stored as `sha256` hashes — no raw phone numbers in the rate-limit state.
- **State commands:** `guard.py status` (view limits), `guard.py reset <number>` (unblock a contact).
- **Media Block:** Non-text messages from non-owner contacts are automatically blocked.

### 🤖 8. Multi-Agent Support
- **Full profile isolation:** All paths, logs, caches, and cron jobs are scoped to `HERMES_HOME`.
- **Auto-detection in installer:** `install.sh` scans both `$HOME` hidden folders and `$HOME/.hermes/profiles/` for agent profiles and presents a selection menu.
- **Environment injection:** `HERMES_HOME` and `HERMES_CMD` are exported before all sub-processes.
- **Independent cron jobs:** Each agent's scheduled messages run in their own environment context.
- **Media isolation:** Incoming images, videos, and audio are stored in per-agent subdirectories.
- **Bridge path override:** `WHATSAPP_BRIDGE_PATH` env var allows pointing to a non-standard `bridge.js` location.
- **Bridge URL override:** `WHATSAPP_BRIDGE_URL` env var allows custom port/host for the WhatsApp bridge.

### 🔧 9. Anti-Ban & Human Simulation Engine
- **Request Pacing (1.0s):** Every message and media send includes a 1-second delay before the HTTP request.
- **Typing Simulation:** Before sending text, the agent triggers `"composing"` presence. Duration scales with message length (15 chars/sec, capped at 5 seconds).
- **Recording Simulation:** Before sending voice notes, the agent triggers `"recording"` presence for 3 seconds.
- **Auto-Offset Scheduling:** Concurrent scheduled tasks are spread across minutes to avoid bot-like burst patterns.
- **Finite Retries:** Self-healing retries are capped at 3 attempts — no infinite loops that could trigger spam detection.

> ⚠️ **Note:** These measures significantly reduce — but do not eliminate — the risk of detection. Using this skill for spam or mass-messaging is strictly prohibited and will result in account suspension.

### ⚕️ 10. Infrastructure & Self-Healing
- **`bridge_health.py`:** The main "medic". Runs automatically on every send attempt.
  - Starts portable Qdrant from `bin/qdrant` if offline.
  - Kills zombie processes on the bridge port using a **multi-tool fallback** (`fuser` -> `lsof` -> `stop`) for full Linux compatibility.
  - Patches `bridge.js` dynamically for MIME, PTT, health endpoint, and presence indicators.
  - **Always creates a backup** (`bridge_andorina_bak.js`) before writing any patch, ensuring the user can restore to the pre-patch state.
  - Restarts the gateway via `hermes gateway stop/start` with smart backoff (2s → 4s → 8s → 15s).
  - Uses a stamp file (`.andorina_bridge_patched`) to skip unnecessary re-patching.
- **`patch_bridge.py`:** Standalone manual patcher (also called during install).
  - Patches `MIME_MAP` with missing formats.
  - Injects the `/health` endpoint canary.
  - Adds `reqMimetype`/`reqPtt` destructuring for advanced media routing.
  - Adds `presence` parameter support to the `/typing` endpoint.
  - **Creates a backup** of `bridge.js` before any modification.
- **`diag.py`:** One-shot health check showing Qdrant status, bridge status/version, WhatsApp connection state, and Google Contacts link status.
- **`check_config()`:** On every health check run, syncs `ANDORINA_TARGET_CONTEXT`, `ANDORINA_TARGET_USER_MEM`, and `ANDORINA_TARGET_SYS_MEM` from `.env` to Hermes `config.yaml`.

### 🔑 11. Google OAuth2 Authentication
- **`auth.py`:** Interactive terminal-based OAuth2 flow for Google People API.
- Generates the authorization URL, receives the code, and exchanges it for `access_token` + `refresh_token`.
- Tokens are saved directly to the agent's `.env`.
- **Auto-refresh:** If the access token expires, `contacts.py` automatically requests a new one using the `refresh_token` — no user interaction required.

### 🖥️ 12. Autostart & Persistence
- **`setup_autostart.py`:** Creates a `.desktop` entry in `~/.config/autostart/` that starts the agent in a terminal window on login.
- **Universal terminal detection:** Automatically detects the available terminal emulator (gnome-terminal, konsole, xfce4-terminal, mate-terminal, lxterminal, xterm) with a headless fallback.
- The terminal window is labeled with the agent name and kept open for debugging even if the engine stops.
- Disable with `setup_autostart.py --disable`.

### 🧠 13. Qdrant Memory Engine
- **`setup_portable.py`:** Downloads a portable Qdrant binary from GitHub releases if not found in system PATH or `bin/`.
- **Architecture-aware:** Detects `x86_64` vs `aarch64` (ARM64) and downloads the correct binary.
- Vectors are stored in `~/.qdrant_storage` (global, shared across agents) for unified memory.
- The health system starts Qdrant automatically if it is offline.

### 🏗️ 14. Architecture & Privilege Model
- **Owner tier:** Full access to all scripts, file system, scheduling, and agent commands.
- **Chatbot tier:** Friendly, restricted persona. Cannot access files, execute commands, or reveal system configuration. Responds in the user's language. Character limit: 400 chars.
- The `CHATBOT_INSTRUCTION` system prompt is injected by `guard.py` and passed to the LLM on every non-owner interaction.

### ⚙️ 15. Configurable Environment Variables
| Variable | Default | Description |
|:---|:---|:---|
| `HERMES_HOME` | `~/.hermes` | Base directory for the agent profile. |
| `HERMES_CMD` | `hermes` | CLI command for the agent. |
| `WHATSAPP_BRIDGE_URL` | `http://localhost:3000` | URL of the WhatsApp bridge. |
| `WHATSAPP_BRIDGE_PATH` | `HERMES_HOME/.../bridge.js` | Full path to `bridge.js` (custom installs). |
| `DEFAULT_COUNTRY_CODE` | `34` (Spain) | Country prefix for normalizing short phone numbers. |
| `WHATSAPP_ALLOWED_USERS` | _(empty)_ | Comma-separated list of authorized phone numbers (owners). |
| `GOOGLE_CONTACTS_CLIENT_ID` | _(empty)_ | Google Cloud OAuth2 client ID. |
| `GOOGLE_CONTACTS_CLIENT_SECRET` | _(empty)_ | Google Cloud OAuth2 client secret. |
| `GOOGLE_CONTACTS_ACCESS_TOKEN` | _(auto)_ | Current Google access token (auto-refreshed). |
| `GOOGLE_CONTACTS_REFRESH_TOKEN` | _(auto)_ | Google refresh token for token rotation. |
| `ANDORINA_TARGET_CONTEXT` | `75000` | Context window limit synced to Hermes `config.yaml`. |
| `ANDORINA_TARGET_USER_MEM` | `5000` | User memory char limit synced to `config.yaml`. |
| `ANDORINA_TARGET_SYS_MEM` | `5000` | System memory char limit synced to `config.yaml`. |
| `ANDORINA_DELIVERY_WINDOW` | `60` | Minutes a scheduled task stays alive after its time. |
| `ANDORINA_CRON_OFFSET` | `2` | Minutes between concurrent cron tasks. |

---

## 🇪🇸 ESPAÑOL — TODAS LAS FUNCIONALIDADES Y CARACTERÍSTICAS

### 📤 1. Envío de Mensajes de Texto
- Envía un mensaje de texto a **cualquier contacto o grupo** de forma inmediata mediante `send.py message`.
- Los mensajes se envían a través de un puente HTTP local (por defecto `http://localhost:3000`).
- La URL del puente es totalmente configurable mediante `WHATSAPP_BRIDGE_URL` en `.env`.
- Compatible con **IDs de grupo** (`@g.us`) e **individuales** (`@s.whatsapp.net`).
- **Auto-reparación:** Si el puente falla durante el envío, el sistema intenta repararlo y reintenta (hasta 3 veces).

### 🎙️ 2. Notas de Voz (PTT)
- Envía archivos de audio como mensajes de **Push-To-Talk (PTT)** nativos mediante `files.py --voice`.
- Antes de enviar, el agente muestra el estado **"Grabando audio..."** al receptor durante 3 segundos.
- Compatible de forma nativa con formatos `.ogg` y `.opus`.
- El flag `ptt` se envía al puente para que el receptor vea el reproductor nativo de nota de voz.

### 📁 3. Envío de Multimedia y Documentos
- Envía **imágenes**, **vídeos**, **documentos** y **audio** desde cualquier ruta local mediante `files.py`.
- Resolución de ruta absoluta: no es necesario hacer `cd` a la carpeta del archivo.
- Antes de enviar, el agente muestra la presencia **"Escribiendo..."** para imitar comportamiento humano.
- Soporte MIME ampliado mediante el parcheo del puente: `.heic`, `.bmp`, `.webp`, `.zip`, `.md`, `.csv`, `.rtf`, `.xls`, `.mp3`, `.wav`, `.ogg`, `.opus`, `.txt`.
- Se verifica la existencia del archivo y los permisos de lectura **antes** de cualquier petición de red.

### 📅 4. Programación Inteligente (Agenda)
- Programa mensajes de texto, archivos o notas de voz mediante `agenda.py auto-schedule`.
- Formatos de hora soportados: `HH:MM`, `DD HH:MM`, `DD/MM HH:MM` (formato 24 horas).
- Las programaciones se registran como **trabajos nativos de `crontab` de Linux** — no requiere ningún daemon.
- **Aislamiento en Crontab:** `HERMES_HOME` y `HERMES_CMD` se inyectan en cada trabajo cron para compatibilidad multi-agente.
- **Persistencia Atómica:** La tarea se escribe en `state/agenda.json` **antes** de crear el cron. Si el cron falla, la tarea se mantiene.
- **Borrado Solo en Entrega:** Los mensajes se eliminan de `agenda.json` **únicamente** cuando se confirma una entrega exitosa.
- **Auto-Offset (Evasión de Colisiones):** Si dos tareas comparten el mismo minuto, la segunda se desplaza automáticamente 2 minutos (configurable con `ANDORINA_CRON_OFFSET`).
- **Ventana de Entrega:** Una tarea permanece activa hasta 60 minutos después de su hora programada (configurable con `ANDORINA_DELIVERY_WINDOW`), permitiendo entregas tardías.
- Listar tareas pendientes: `agenda.py list`.
- Cancelar una tarea: `agenda.py remove <msg_id>` (también elimina el cron job).

### 📒 5. Descubrimiento de Contactos y Grupos
- **Búsqueda Universal** en Google Contacts y Grupos de WhatsApp: `contacts.py search "Consulta"`.
- **Búsqueda Difusa:** Normalización unicode NFD — ignora acentos, mayúsculas y caracteres especiales. Encuentra "María" aunque escribas "maria".
- **Auto-refresco en fallo:** Si no se encuentra un contacto, el sistema limpia la caché y vuelve a obtener datos de Google Cloud antes de reportar error.
- Integración con **Google People API** con flujo OAuth2 completo (`auth.py`) y rotación automática de `refresh_token`.
- **Listado de grupos:** `contacts.py groups` — obtiene datos en vivo del puente, con fallback a la caché `channel_directory.json`.
- **Volcado completo:** `contacts.py all` — array JSON de todos los contactos conocidos.
- **Reseteo manual de caché:** `contacts.py refresh` — fuerza una sincronización fresca con la nube.
- Normalización de código de país: los números cortos (8-10 dígitos) se prefijan automáticamente con `DEFAULT_COUNTRY_CODE`.

> **⚠️ Limitación en la Detección de Grupos:** `contacts.py groups` y `contacts.py search` obtienen grupos directamente desde el endpoint `/groups` del puente de WhatsApp en tiempo real, listando **todos los grupos** a los que pertenece la cuenta, independientemente del historial de chat. Sin embargo, si el **puente está offline**, el fallback es `channel_directory.json` — una caché local gestionada por Hermes. Si un grupo **nunca ha aparecido en esa caché** (porque Hermes aún no lo ha registrado), no se encontrará mientras el puente esté caído. **La solución es siempre asegurarse de que el puente esté online antes de buscar grupos.**
>
> Además: `inbox.py list` **solo mostrará grupos que hayan enviado al menos un mensaje** a través del hook. Un grupo en el que el asistente es miembro pero del que **no se ha recibido ningún mensaje** no aparecerá en el inbox. Se puede encontrar y enviarle mensajes mediante `contacts.py search` siempre que el puente esté online.

### 📥 6. Bandeja de Entrada (Mensajes Entrantes)
- Cada mensaje de WhatsApp entrante se **captura y almacena localmente** en `state/inbox.json` mediante `hook_inbox.py`.
- El hook se registra en Hermes para los eventos `message_received` y `whatsapp:message`.
- **Listar conversaciones:** `inbox.py list` — muestra chats únicos ordenados por el más reciente.
- **Leer historial:** `inbox.py read <chatId>` — devuelve los últimos **50 mensajes** de una conversación (configurable en el código).
- Normalización de Chat ID: si falta el sufijo `@s.whatsapp.net` o `@g.us`, se añade automáticamente.
- **Límite de historial:** La bandeja se limita a 500 entradas para evitar el crecimiento excesivo del archivo.
- **Seguridad Unicode:** La entrada se lee mediante `sys.stdin.buffer` para manejar emojis y caracteres internacionales sin fallos.
- El agente puede usar la bandeja de entrada para **resumir conversaciones**, **ver quién escribió**, **redactar respuestas** y **obtener contexto** antes de enviar.

> **⚠️ Limitación del Inbox — Grupos Silenciosos:** El inbox (`state/inbox.json`) se alimenta **únicamente de mensajes recibidos a través del hook** (`hook_inbox.py`). Si el asistente es miembro de un grupo de WhatsApp pero **no se ha recibido ningún mensaje en ese grupo** (o ningún miembro ha escrito desde que se instaló la skill), ese grupo será **invisible para `inbox.py`**. No aparecerá en `inbox.py list` y `inbox.py read` devolverá un resultado vacío. Este comportamiento es esperado, no un error. Para interactuar con ese grupo, usa `contacts.py search "nombre del grupo"` para obtener su `chatId` y envíale mensajes directamente.

### 🛡️ 7. Cortafuegos de Seguridad (Guard)
- **Dos niveles de privilegio:**
  - **Modo Owner (`full`):** Los números autorizados en `WHATSAPP_ALLOWED_USERS` tienen acceso completo a la IA.
  - **Modo Chatbot:** El resto de contactos interactúa con una persona amable y restringida sin acceso al sistema.
- **Bloqueo de Inyección de Prompts:** Más de 30 patrones regex detectan comandos como `cat /etc/passwd`, traversal de rutas (`../`), inyecciones de shell (`$(cmd)`) y frases de ingeniería social.
- **Detección de Ofuscación:** La entrada se verifica dos veces tras eliminar espacios y separadores (detecta `i g n o r a  r e g l a s`).
- **Límite de Tasa:** Los contactos no-owner están sujetos a:
  - Enfriamiento de 5 minutos entre mensajes (`COOLDOWN_SECS=300`).
  - Máximo 10 mensajes por hora (`MAX_MSGS_PER_HOUR`).
- **Límite de Longitud:** Los mensajes de más de 500 caracteres son bloqueados.
- **Hashing de Privacidad:** Los identificadores de contacto se almacenan como hashes `sha256` — nunca números de teléfono en bruto en el estado de límite de tasa.
- **Comandos de estado:** `guard.py status` (ver límites), `guard.py reset <número>` (desbloquear un contacto).
- **Bloqueo de Medios:** Los mensajes no-texto de contactos no-owner son bloqueados automáticamente.

### 🤖 8. Soporte Multi-Agente
- **Aislamiento total de perfil:** Todas las rutas, logs, cachés y cron jobs están delimitados a `HERMES_HOME`.
- **Auto-detección en el instalador:** `install.sh` escanea tanto las carpetas ocultas de `$HOME` como `$HOME/.hermes/profiles/` en busca de perfiles de agente y muestra un menú de selección.
- **Inyección de entorno:** `HERMES_HOME` y `HERMES_CMD` se exportan antes de todos los subprocesos.
- **Cron jobs independientes:** Los mensajes programados de cada agente se ejecutan en su propio contexto de entorno.
- **Aislamiento multimedia:** Las imágenes, vídeos y audios entrantes se almacenan en subdirectorios por agente.
- **Override de ruta del puente:** La variable `WHATSAPP_BRIDGE_PATH` permite apuntar a una ubicación no estándar de `bridge.js`.
- **Override de URL del puente:** La variable `WHATSAPP_BRIDGE_URL` permite usar un puerto/host personalizado para el puente de WhatsApp.

### 🔧 9. Motor Anti-Baneo y Simulación Humana
- **Pacing de Peticiones (1.0s):** Cada envío de mensaje o multimedia incluye un retraso de 1 segundo antes de la petición HTTP.
- **Simulación de Escritura:** Antes de enviar texto, el agente activa la presencia `"composing"`. La duración escala con la longitud del mensaje (15 chars/seg, máximo 5 segundos).
- **Simulación de Grabación:** Antes de enviar notas de voz, el agente activa la presencia `"recording"` durante 3 segundos.
- **Programación con Auto-Offset:** Las tareas concurrentes se distribuyen en diferentes minutos para evitar patrones robóticos de ráfaga.
- **Reintentos Finitos:** Los reintentos de auto-reparación están limitados a 3 intentos — sin bucles infinitos que puedan activar la detección de spam.

> ⚠️ **Nota:** Estas medidas reducen significativamente — pero no eliminan — el riesgo de detección. Usar esta skill para spam o mensajería masiva está estrictamente prohibido y resultará en la suspensión de la cuenta.

### ⚕️ 10. Infraestructura y Auto-Reparación
- **`bridge_health.py`:** El "médico" principal. Se ejecuta automáticamente en cada intento de envío.
  - Arranca Qdrant portable desde `bin/qdrant` si está offline.
  - Mata procesos zombies en el puerto del puente usando un **fallback multi-herramienta** (`fuser` -> `lsof` -> `stop`) para compatibilidad Linux total.
  - Parchea `bridge.js` dinámicamente para MIME, PTT, endpoint de salud e indicadores de presencia.
  - **Siempre crea una copia de seguridad** (`bridge_andorina_bak.js`) antes de escribir cualquier parche, asegurando que el usuario pueda restaurar al estado pre-parcheo.
  - Reinicia el gateway con `hermes gateway stop/start` con backoff inteligente (2s → 4s → 8s → 15s).
  - Usa un archivo de sello (`.andorina_bridge_patched`) para evitar re-parcheos innecesarios.
- **`patch_bridge.py`:** Parcheador manual independiente (también invocado durante la instalación).
  - Parchea `MIME_MAP` con los formatos que faltan.
  - Inyecta el endpoint canario `/health`.
  - Añade la desestructuración `reqMimetype`/`reqPtt` para enrutamiento multimedia avanzado.
  - Añade soporte del parámetro `presence` al endpoint `/typing`.
  - **Crea una copia de seguridad** de `bridge.js` antes de cualquier modificación.
- **`diag.py`:** Diagnóstico de un solo uso que muestra el estado de Qdrant, estado/versión del puente, estado de conexión de WhatsApp y estado del enlace con Google Contacts.
- **`check_config()`:** En cada ejecución de verificación de salud, sincroniza `ANDORINA_TARGET_CONTEXT`, `ANDORINA_TARGET_USER_MEM` y `ANDORINA_TARGET_SYS_MEM` desde `.env` al archivo `config.yaml` de Hermes.

### 🔑 11. Autenticación OAuth2 con Google
- **`auth.py`:** Flujo OAuth2 interactivo en terminal para la API de Google People.
- Genera la URL de autorización, recibe el código e intercambia por `access_token` + `refresh_token`.
- Los tokens se guardan directamente en el `.env` del agente.
- **Auto-refresco:** Si el token de acceso caduca, `contacts.py` solicita uno nuevo automáticamente usando el `refresh_token` — sin interacción del usuario.

### 🖥️ 12. Arranque Automático y Persistencia
- **`setup_autostart.py`:** Crea una entrada `.desktop` en `~/.config/autostart/` que arranca el agente en una ventana de terminal al iniciar sesión.
- **Detección universal de terminal:** Detecta automáticamente el emulador de terminal disponible (gnome-terminal, konsole, xfce4-terminal, mate-terminal, lxterminal, xterm) con fallback sin terminal.
- La ventana del terminal está etiquetada con el nombre del agente y se mantiene abierta para depuración incluso si el motor se detiene.
- Desactivar con `setup_autostart.py --disable`.

### 🧠 13. Motor de Memoria Qdrant
- **`setup_portable.py`:** Descarga un binario portátil de Qdrant desde las releases de GitHub si no se encuentra en el PATH del sistema ni en la carpeta `bin/`.
- **Detección de arquitectura:** Detecta `x86_64` vs `aarch64` (ARM64) y descarga el binario correcto.
- Los vectores se almacenan en `~/.qdrant_storage` (global, compartido entre agentes) para una memoria unificada.
- El sistema de salud arranca Qdrant automáticamente si está offline.

### 🏗️ 14. Arquitectura y Modelo de Privilegios
- **Nivel Owner:** Acceso completo a todos los scripts, sistema de archivos, programación y comandos del agente.
- **Nivel Chatbot:** Persona amable y restringida. No puede acceder a archivos, ejecutar comandos ni revelar la configuración del sistema. Responde en el idioma del usuario. Límite de caracteres: 400.
- La instrucción de sistema `CHATBOT_INSTRUCTION` es inyectada por `guard.py` y pasada al LLM en cada interacción no-owner.

### ⚙️ 15. Variables de Entorno Configurables
| Variable | Por defecto | Descripción |
|:---|:---|:---|
| `HERMES_HOME` | `~/.hermes` | Directorio base del perfil del agente. |
| `HERMES_CMD` | `hermes` | Comando CLI del agente. |
| `WHATSAPP_BRIDGE_URL` | `http://localhost:3000` | URL del puente de WhatsApp. |
| `WHATSAPP_BRIDGE_PATH` | `HERMES_HOME/.../bridge.js` | Ruta completa a `bridge.js` (instalaciones personalizadas). |
| `DEFAULT_COUNTRY_CODE` | `34` (España) | Prefijo de país para normalizar números cortos. |
| `WHATSAPP_ALLOWED_USERS` | _(vacío)_ | Lista de números autorizados separados por comas (owners). |
| `GOOGLE_CONTACTS_CLIENT_ID` | _(vacío)_ | Client ID OAuth2 de Google Cloud. |
| `GOOGLE_CONTACTS_CLIENT_SECRET` | _(vacío)_ | Client Secret OAuth2 de Google Cloud. |
| `GOOGLE_CONTACTS_ACCESS_TOKEN` | _(auto)_ | Token de acceso de Google actual (se auto-refresca). |
| `GOOGLE_CONTACTS_REFRESH_TOKEN` | _(auto)_ | Token de refresco de Google para la rotación de tokens. |
| `ANDORINA_TARGET_CONTEXT` | `75000` | Límite de ventana de contexto sincronizado con `config.yaml` de Hermes. |
| `ANDORINA_TARGET_USER_MEM` | `5000` | Límite de caracteres de memoria de usuario sincronizado con `config.yaml`. |
| `ANDORINA_TARGET_SYS_MEM` | `5000` | Límite de caracteres de memoria del sistema sincronizado con `config.yaml`. |
| `ANDORINA_DELIVERY_WINDOW` | `60` | Minutos que una tarea programada permanece activa después de su hora. |
| `ANDORINA_CRON_OFFSET` | `2` | Minutos entre tareas cron concurrentes. |

---
*Developed with ❤️ by Jorge. — Andoriña v1.0.3-patch1*
