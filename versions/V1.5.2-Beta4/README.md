<p align="center">
  <strong style="font-size: 2em;">Andoriña — OFFICIAL RELEASE</strong>
</p>

<p align="center">
  <img src="docs/assets/logo.png" alt="Andoriña Logo" height="120">
</p>

<p align="center">
  <em>Autonomous WhatsApp Manager for Hermes (v1.5.2-Beta4)</em><br>
  <em>Gestor Autónomo de WhatsApp para Hermes (v1.5.2-Beta4)</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.5.2-Beta4-blueviolet?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/status-BETA-orange?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/platform-Linux-lightgrey?style=flat-square&logo=linux" alt="Linux">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python" alt="Python">
</p>

<p align="center">
  <strong>Official Website / Sitio Web Oficial:</strong> <a href="https://andorinaai.github.io/Andorina-WhatsApp-Agent-for-Hermes/">andorinaai.github.io/</a>
</p>

## 🤝 Join the Community / Únete a la Comunidad

- **Follow on X:** [@andorinaAI](https://x.com/andorinaAI)

> [!IMPORTANT]
> **🔧 v1.5.2-Beta4 — BUG FIX RELEASE**
> Fixed: RBAC JID suffix match fallback · Alert source matching using JID check · Away admin phone JID exclusion fallback · Webhook public URL multi-tier detection. Improvements: fuzzy accent-insensitive keyword matching for alerts · Webhook stability dashboard banner · Centralized JID helper.
>
> **🔧 v1.5.2-Beta4 — VERSIÓN DE CORRECCIÓN DE ERRORES**
> Corregido: Coincidencia de sufijos RBAC para roles · Coincidencia de origen de alertas por JID · Coincidencia de sufijos de admin en auto-respuesta · Autodetección de URL webhook multinivel. Mejoras: coincidencia difusa e insensible a acentos en alertas · Banner de estabilidad de webhook · Ayudante JID centralizado.
>
> ---
>
> **🔧 v1.5.2-Beta3 — BUG FIX RELEASE**
> Fixed: TUI/CLI blocked by RBAC · Webhook port hardcoded to 3001 · Contact notes never written or read · Updater not patching SOUL.md. Improvements: banner i18n (EN/ES), banner shown on every panel load, scroll speed reduced.
>
> **🔧 v1.5.2-Beta3 — VERSIÓN DE CORRECCIÓN DE ERRORES**
> Corregido: TUI/CLI bloqueado por RBAC · Puerto de webhooks fijado en 3001 · Notas de contacto sin escribir ni leer · Actualizador sin parchear el SOUL.md. Mejoras: banner i18n (EN/ES), banner visible siempre al cargar, velocidad de scroll reducida.

---

<p align="center">
  <strong>Turn Hermes into an autonomous WhatsApp manager.</strong><br>
  Take full control of your messaging. Forget typing: schedule messages, send voice notes, share PC files, and search your contacts instantly. Your WhatsApp, on total autopilot.
</p>

<p align="center">
  <strong>Convierte a Hermes en un gestor autónomo de WhatsApp.</strong><br>
  Toma el control absoluto de tus comunicaciones. Olvídate de teclear: programa envíos, lanza notas de voz, adjunta archivos de tu PC y busca en tu agenda al instante. Tu mensajería, en piloto automático.
</p>

> ⚠️ **Exclusive for Linux.** We have shifted our direction to prioritize the free software community. To resist privatization and Big Tech monopolies, Andoriña is currently developed exclusively for Linux (though we remain open to future possibilities).
> ⚠️ **Exclusivo para Linux.** Hemos cambiado de rumbo para priorizar a la comunidad y el software libre. Frente a la privatización y el control de las Big Tech, Andoriña se desarrolla ahora exclusivamente para Linux (sin cerrarnos a cambiar de idea en el futuro).

---

<p align="center">
  <a href="#english">English</a> | <a href="#español">Español</a>
</p>

---

## Support / Soporte

<p align="center">
  <a href="https://buymeacoffee.com/andorinaai">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=000000" alt="Buy Me A Coffee" />
  </a>
  <a href="https://www.paypal.com/paypalme/j93gf">
    <img src="https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal" />
  </a>
</p>

---

<a name="english"></a>

## 🇬🇧 English Version

### ✨ What can Andoriña do?

| Feature | Description |
| :--- | :--- |
| 📤 **Message sending** | Send text to any contact or group by name or number |
| 📁 **File sending** | Upload documents, images, audio, or video from your local folders |
| 🎙️ **Voice notes** | Native PTT support: converts audio and shows "Recording..." status |
| 🧩 **Sandbox (V2)** | Execute isolated Python plugins & games with local DBs **[Coming Soon]** |
| 📚 **Knowledge (RAG)** | Upload PDF/TXT files to automatically inject context into the LLM |
| 🛡️ **Zero-Trust Guard** | Security validation via `input_guard.py` & `tool_guard.py`. Timeouts & restrictions applied. |
| 🛂 **RBAC Engine** | Granular roles (Owner, Manager, Chatbot, Blocked) with allowed_folders validation |
| 🕵️ **DLP Pipeline** | Data Loss Prevention truncates spam, deletes internal reasoning logs, blocks API leakage |
| 🧠 **Long-Term Memory**| Permanent section-based notes (`contacts.py note-section-set`) to save context about users |
| 🖥️ **GUI Dashboard** | Fully graphical UI (Dark/Light mode) to manage RBAC, Sub-Souls, Plugins, and a **Live Monitor** |
| ☁️ **Remote Access** | **Cloudflare Tunnel** (free or custom domain) to expose the panel from anywhere |
| 🔄 **Auto-Update** | One-click GitHub updater that preserves all user data atomically |
| 🤖 **Multi-Agent** | Full **Crontab Isolation** and environment-specific routing |
| ⏰ **Anti-Ban Protection** | **Request Pacing (1.0s delay)** and **Auto-Collision Offset (2 mins)** for scheduling |
| 📥 **Inbox Storage** | Idempotent local inbox storage (`inbox.json`) via webhook interceptors |
| 🔕 **Away & Mute** | Per-contact mute and global away auto-responder with cooldowns |
| 🔐 **Absolute Privacy** | **100% Local Processing**. Zero telemetry, no cloud storage |
| 📒 **Google Cloud Sync** | Full OAuth2 sync with Google Contacts, **Fuzzy Search**, and **LID-Mapping** |
| ⚕️ **Self-Healing** | Automated infra repair, patch checker (`check_patches.py`), and Diagnostic Engine |
| 🧠 **Cognitive Reset** | Surgical memory wipe (logs + inbox) without breaking WhatsApp sessions (`inbox.py delete`) |

### 🚀 Installation & Documentation

> [!IMPORTANT]
> **Requires Hermes Agent >= v0.16.0.** Update with `hermes update` before installing. The installer checks this automatically and offers to update if needed.

1. **Quick Start:** Unzip the downloaded folder and double-click `Andorina-Panel.sh` (If it doesn't open, open a terminal and run `bash ./Andorina-Panel.sh`). The Andoriña Control Panel will open in your browser and guide you visually through the entire installation process.
2. **First Login:** On the first login screen, you can enter **any password you want** to set it as your master password.
3. **Post-Installation:** Once all steps are complete, **you must close the current browser tab** (it belongs to the temporary installation folder). Open the panel again from the Desktop Shortcut or from the final installed skill folder.
4. **Comprehensive Guide:** See [GUIDE.md](./GUIDE.md) for a full breakdown of requirements, architecture, and troubleshooting.
5. **Full Feature List:** See [FEATURES.md](./FEATURES.md) for a complete reference of all capabilities, commands, and environment variables.

---

### 🛡️ Anti-Ban & Safety Notice
Andoriña is designed for **personal assistance**, not for bulk messaging. 
- **Request Pacing:** The system implements a **1.0s delay** between messages to avoid bridge saturation.
- **Human Simulation:** Native support for **Typing...** and **Recording audio...** status indicators to mimic natural interaction.
- **Auto-Offset:** Scheduled tasks sharing the same timestamp are safely offset by 2 minutes internally via `agenda.py` to prevent LLM timeouts and API spam.

> [!CAUTION]
> **Spam Warning:** Using this skill for spam or mass-marketing is strictly prohibited and will lead to an immediate account ban by Meta. The developers are not responsible for account suspensions. Use responsibly.

---

### 💬 Usage — Natural Examples

**Sending messages:**
- "Send a WhatsApp to my boss saying I'll be 5 minutes late."

**Scheduling messages (One-Step):**
- "Schedule a WhatsApp for Carlos tomorrow at 18:00 saying: 'Ready for the match?'."
- *The agent leverages the `auto-schedule` command, keeping the task in a 60-minute delivery window even if the AI responds late.*

**Information Management:**
- "Update Laura's profile note in the 'Preferences' section to state she is vegan."
- *The AI uses `contacts.py note-section-set` to update memory safely.*

> [!TIP]
> **File Sending Tip:** For images, videos, and complex documents, the AI cannot read or see the content. Provide exact filenames or be extremely specific so the agent finds them using `files.py`!

---

## 🌟 KEY CAPABILITIES & CHARACTERISTICS

### 🛡️ Anti-Ban & Resilient Architecture
- **Request Pacing & Simulation:** Simulated "composing" time proportionate to the message length.
- **Collision Avoidance:** `agenda.py` offsets concurrent tasks by 2 minutes automatically.
- **Self-Healing Bridge:** Auto-restores Qdrant/Node bridge processes.
- **Idempotent Webhooks:** `whatsapp.py` patches strictly eliminate duplicate incoming message records.

### 🛂 Military-Grade Security (Zero-Trust Pipeline)
- **Pre-LLM & Tool Validation:** `input_guard.py` blocks specific character spam, while `tool_guard.py` enforces directory reading limitations (`allowed_folders`) via restricted access roles.
- **Execution Subprocess Timeout:** External commands executed by the LLM are given a strict 30-second TTL to avoid freezing the system.
- **Semantic Topic Alerts:** Add permanent listening rules with transparency notifications via `alerts.py`.

### 📒 Smart Contacts & Identity
- **LID Resolution:** The identity engine correctly intercepts WhatsApp LIDs dynamically, applying a heuristic suffix parser (`@g.us` vs `@s.whatsapp.net`) for seamless Group interactions.
- **Fuzzy Search:** `contacts.py` ignores accents and character cases to find contacts across Bridge APIs, Local caches, and Google integrations.

### 🎙️ Advanced Media & UI
- **Live Server Monitor:** Easily check Bridge, Agent, and Server execution events visually inside the Web panel (`monitor.html`).
- **Media Support:** Native `.heic`, `.opus`, `.xcf`, and `.psd` MIME resolving for document-based deliveries.

## 🛠️ THE TOOLBOX

### 📒 Contacts & Groups
| Script | Command | Usage |
| :--- | :--- | :--- |
| `tools/contacts.py` | `search "Query"` | Universal search (names, numbers, groups). |
| `tools/contacts.py` | `note-add` / `note-section-set` | Modifies permanent memory notes for a user. |
| `tools/contacts.py` | `groups` | Lists all WhatsApp groups. |
| `tools/contacts.py` | `refresh` | Clears local cache and forces a cloud sync. |

### ✉️ Messaging & Files
| Script | Command | Usage |
| :--- | :--- | :--- |
| `transport/send.py` | `message "ID" "Txt"` | Sends a text message immediately with pacing. |
| `transport/send.py` | `broadcast "Txt" "IDs"` | Sends paced mass messages to multiple users. |
| `tools/files.py` | `"Path" "ID"` | Sends images, videos or documents immediately. |
| `tools/inbox.py` | `list` / `search "Query"`| Lists recent chats / searches local history cache. |
| `tools/alerts.py` | `add "Source" "Target"` | Creates a keyword rule and notifies the target. |

### 📅 Scheduling (Agenda)
| Script | Command | Usage |
| :--- | :--- | :--- |
| `tools/agenda.py` | `auto-schedule "ID" "TIME" "Msg"` | Automated text scheduling (handles collisions). |
| `tools/agenda.py` | `recurring add "ID" "CRON" "Msg"`| Adds a recurring crontab task. |
| `tools/agenda.py` | `list` / `remove "ID"` | Lists / Cancels scheduled messages. |

### 🛡️ Security & System
| Script | Command | Usage |
| :--- | :--- | :--- |
| `Andorina-Panel.sh` | (none) | Opens the full Linux Desktop GUI Dashboard. |
| `utils/admin_cli.py` | `role set "ID" "Role"` | Assigns an RBAC role to a user. |
| `utils/diag.py` / `bridge_health.py` | (none) | System health diagnosis & Bridge auto-repair. |

---

<a name="español"></a>

## 🇪🇸 Versión en Español

### ✨ ¿Qué puede hacer Andoriña?

| Función | Descripción |
| :--- | :--- |
| 📤 **Envío de mensajes** | Envía texto a cualquier contacto o grupo por nombre o número |
| 📁 **Envío de archivos** | Sube documentos, imágenes, audio o vídeo desde tus carpetas locales |
| 🎙️ **Notas de voz** | Soporte PTT nativo: convierte audio y muestra estado "Grabando..." |
| 🧩 **Sandbox (V2)** | Ejecutará plugins y juegos aislados en Python con BD local **[Próximamente]** |
| 📚 **Conocimiento (RAG)** | Sube PDFs o TXTs para inyectar contexto automáticamente en la IA |
| 🛡️ **Tubería Zero-Trust** | Validación vía `input_guard.py` y `tool_guard.py` (Límites y Carpetas seguras) |
| 🛂 **Motor RBAC** | Roles granulares (Dueño, Manager, Chatbot, Bloqueado) con restricciones |
| 🕵️ **Motor DLP** | Trunca spam, borra metadatos de razonamiento interno, bloquea claves API |
| 🧠 **Memoria a Largo Plazo**| Sistema de notas por secciones (`note-section-set`) para contexto de usuarios |
| 🖥️ **Panel Web** | Panel gráfico multi-tema para gestionar RBAC, Plugins y **Monitor de Servidor en Vivo** |
| ☁️ **Acceso Remoto** | **Túnel Cloudflare** (gratis o dominio personalizado) para acceso web |
| 🔄 **Auto-Actualización** | Actualizador de GitHub con un clic conservando estado atómicamente |
| 🤖 **Multi-Agente** | **Aislamiento de Crontab** y enrutamiento dinámico de perfiles |
| ⏰ **Anti-Baneos** | **Ritmo de envíos (1.0s)** y **Auto-Offset de Colisiones (2 min)** al programar |
| 📥 **Inbox Local** | Almacenamiento idempotente de historial (`inbox.json`) vía webhooks |
| 🔕 **Ausencia y Silencio** | Silencio por contacto y auto-respuesta de ausencia global |
| 🔐 **Privacidad Absoluta** | **Procesamiento 100% Local**. Cero telemetría |
| 📒 **Sincro Google** | Sincronización OAuth2, **Búsqueda Difusa** e Identidad **LID-Mapping** |
| ⚕️ **Auto-Reparación** | Infraestructura que auto-reinicia y diagnostica el puente (`bridge_health.py`) |
| 🧠 **Reset Cognitivo** | Borrado quirúrgico de memoria y logs vía interfaz (`inbox.py delete`) |

### 🚀 Instalación y Documentación

> [!IMPORTANT]
> **Requiere Hermes Agent >= v0.16.0.** Actualiza con `hermes update` antes de instalar. El instalador lo comprueba automáticamente y ofrece actualizar si es necesario.

1. **Inicio Rápido:** Descomprime la carpeta y haz doble clic en `Andorina-Panel.sh` (Si no abre, abre una terminal en la carpeta y ejecuta `bash ./Andorina-Panel.sh`). El Panel Web te guiará.
2. **Primer Login:** En el primer inicio de sesión, introduce **la contraseña que tú quieras** para establecerla como tu contraseña maestra.
3. **Post-Instalación:** Una vez termines todos los pasos, **debes cerrar la pestaña actual del navegador** (ya que pertenece a la carpeta temporal de instalación). A partir de ahora, abre el panel desde el Acceso Directo de tu escritorio o desde la carpeta final de la skill instalada.
4. **Guía Completa:** Consulta la [GUIDE.md](./GUIDE.md) para un desglose total de requisitos.
5. **Lista de Funciones:** Consulta [FEATURES.md](./FEATURES.md) para las variables de entorno.

### 🛡️ Aviso de Seguridad y Anti-Baneo
Andoriña está diseñada para **asistencia personal**, no para mensajería masiva.
- **Pacing de Peticiones:** Retraso de 1.0s entre mensajes y simulación de tiempo "escribiendo...".
- **Auto-Offset:** Para prevenir que el LLM sature la red, la programación simultánea de mensajes (`agenda.py`) desplaza cada mensaje 2 minutos.

> [!CAUTION]
> **Aviso de Spam:** El uso masivo resultará en el baneo de tu cuenta por parte de Meta. Úsala con responsabilidad.

### 💬 Uso — Ejemplos Naturales

**Enviar mensajes:**
- "Dile a Laura en WhatsApp que ya tengo el presupuesto listo."

**Programar mensajes (Proceso de un solo paso):**
- "Programa un WhatsApp para Carlos mañana a las 18:00 que diga: '¿Listo para el partido?'."
- *El asistente mantiene los mensajes programados en una ventana de vida de 60 minutos incluso si la IA se retrasa.*

**Gestión de Información:**
- "Añade a la sección de 'Preferencias' de las notas de Laura que es vegana."
- *La IA utilizará `contacts.py note-section-set` preservando memorias a largo plazo.*

## 🌟 CAPACIDADES CLAVE

### 🛡️ Arquitectura Anti-Baneo y Tubería Zero-Trust
- **Evasión de Colisiones:** `agenda.py` desplaza automáticamente tareas concurrentes por 2 min.
- **Aislamiento de Tareas:** Ejecución de herramientas por subprocessos aislados limitados a 30 segundos.
- **Bloqueo Restricto:** `tool_guard.py` revisa las listas `allowed_folders` para detener cualquier escape de lectura.

### 📒 Identidad y Búsqueda Difusa
- **Resolución LID Dinámica:** Detecta cuentas multi-dispositivo y los traduce a los números estándar, infiriendo si son grupos (`@g.us`) analizando la longitud del JID.
- **Monitor de Servidor en Vivo:** Inspector visual e interactivo de logs dentro de la interfaz web (`monitor.html`).

## 🛠️ LA CAJA DE HERRAMIENTAS

| Herramienta | Comando | Uso |
| :--- | :--- | :--- |
| `contacts.py` | `search`, `note-section-set`, `groups` | Búsqueda global (ignora acentos) y memoria de usuario. |
| `send.py` | `message`, `broadcast` | Envío inteligente de texto masivo y unitario. |
| `files.py` | `"Ruta"` | Mapeo de mimes automáticos para imágenes/documentos. |
| `agenda.py` | `auto-schedule`, `recurring add` | Tareas programadas en crontab con offsets. |
| `alerts.py` | `add "Origen" "Destino"` | Reglas semánticas notificando al usuario de la vigilancia. |
| `inbox.py` | `search "Query"`, `delete "ID"` | Búsqueda local de historial y resets cognitivos puros. |
| `admin_cli.py` | `role set`, `chatbot mute` | Gestión integral del sistema de roles RBAC. |

---

### 📜 License / Licencia

**AGPL-3.0 / Commercial License**
- ✅ **Personal Use:** Free and open under AGPL-3.0. / **Uso Personal:** Gratis y abierto bajo AGPL-3.0.
- ❌ **Commercial Use:** Requires a paid license for companies. / **Uso Comercial:** Requiere licencia de pago.
- 👤 **Trademark:** Name and logo are protected. / **Marca Registrada:** Nombre y logo protegidos.

---

<p align="center">
  Made with ❤️ by <strong>Jorge</strong> for <a href="https://github.com">Hermes Agent</a>.<br>
  If this tool provides value, consider <a href="https://buymeacoffee.com/andorinaai">buying me a coffee ☕</a>
</p>
