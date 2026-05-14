<p align="center">
  <strong style="font-size: 2em;">Andoriña — OFFICIAL RELEASE</strong>
</p>

<p align="center">
  <img src="docs/assets/logo.png" alt="Andoriña Logo" height="120">
</p>

<p align="center">
  <em>Autonomous WhatsApp Manager for Hermes (v1.0.3-patch1)</em><br>
  <em>Gestor Autónomo de WhatsApp para Hermes (v1.0.3-patch1)</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.3--patch1-blueviolet?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/status-STABLE-green?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/platform-Linux-lightgrey?style=flat-square&logo=linux" alt="Linux">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python" alt="Python">
</p>

<p align="center">
  <strong>Official Website / Sitio Web Oficial:</strong> <a href="https://andorinaai.github.io/Andorina-WhatsApp-Agent-for-Hermes/">andorinaai.github.io/</a>
</p>

## 🤝 Join the Community / Únete a la Comunidad

- **Follow on X:** [@andorinaAI](https://x.com/andorinaAI)

> [!IMPORTANT]
> **🚀 v1.0.3-patch1 OFFICIAL RELEASE: STABLE INSTALLER & BRIDGE**
> This is the latest stable version of Andoriña. It features agent-proof refactoring and improved system resilience. Please report any bugs via GitHub Issues.
>
> **🚀 v1.0.3-patch1 LANZAMIENTO OFICIAL: INSTALADOR Y BRIDGE ESTABLES**
> Esta es la versión estable más reciente de Andoriña. Cuenta con refactorización a prueba de agentes y mejora de la resiliencia del sistema. Por favor, informa de cualquier error a través de las Issues de GitHub.

---

<p align="center">
  <strong>Turn Hermes into an autonomous WhatsApp manager.</strong><br>
  Take full control of your messaging. Forget typing: schedule messages, send voice notes, share PC files, and search your contacts instantly. Your WhatsApp, on total autopilot.
</p>

<p align="center">
  <strong>Convierte a Hermes en un gestor autónomo de WhatsApp.</strong><br>
  Toma el control absoluto de tus comunicaciones. Olvídate de teclear: programa envíos, lanza notas de voz, adjunta archivos de tu PC y busca en tu agenda al instante. Tu mensajería, en piloto automático.
</p>

> ⚠️ **Currently optimized exclusively for Linux.** Windows and macOS support in development.
> ⚠️ **Optimizado exclusivamente para Linux.** Soporte para Windows y macOS en desarrollo.

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
| 🛡️ **Guard (Firewall)** | Blocks prompt injections and **obfuscated attacks** (e.g. `d a m e`) |
| 🤖 **Multi-Agent** | Full **Crontab Isolation** and environment-specific routing |
| ⏰ **Anti-Ban Protection** | **Request Pacing (1.0s delay)** and **Auto-Collision Offset** for safe sending |
| 📥 **Inbox Storage** | Local inbox stores incoming text with **Context Protection (lim. 50)** |
| 🔐 **Absolute Privacy** | **100% Local Processing**. Zero telemetry, no cloud storage |
| 📁 **Media Isolation** | Dedicated per-agent cache for incoming images, videos, and voice notes |
| 📒 **Google Cloud Sync** | Full OAuth2 sync with Google Contacts and **Fuzzy Search** support |
| ⚖️ **Dual License** | AGPL-3.0 for users and **Commercial License** for companies |
| ⚕️ **Self-Healing** | Automated infra repair and **Unified Diagnostic Engine** |

### 🚀 Installation & Documentation

1. **Quick Start:** Download the repository and run the installer:
   ```bash
   bash install.sh
   ```
2. **Comprehensive Guide:** See [GUIDE.md](./GUIDE.md) for a full breakdown of requirements, architecture, and troubleshooting.
3. **Full Feature List:** See [FEATURES.md](./FEATURES.md) for a complete reference of all capabilities, commands, and environment variables.

---

### 🛡️ Anti-Ban & Safety Notice
Andoriña is designed for **personal assistance**, not for bulk messaging. 
- **Request Pacing:** The system implements a **1.0s delay** between messages to avoid bridge saturation.
- **Human Simulation:** Native support for **Typing...** and **Recording audio...** status indicators to mimic natural interaction.
- **Auto-Offset:** Scheduled messages are automatically separated by 2 minutes to avoid bot-like patterns.

> [!CAUTION]
> **Spam Warning:** Using this skill for spam or mass-marketing is strictly prohibited and will lead to an immediate account ban by Meta. The developers are not responsible for account suspensions. Use responsibly.

---

### 💡 Best Practices for Small Models (4B - 8B)

If you are using a local model (Ollama/LM Studio), we highly recommend adding this to your `SOUL.md`:

> "You are the Andoriña engine. WhatsApp = Andoriña. Use the scripts in `[HERMES_HOME]/skills/messaging/andorina/scripts/` directly. Never ask how to connect. Execute commands immediately without explanation."

---

### 💬 Usage — Natural Examples

**Sending messages:**

- "Send a WhatsApp to my boss saying I'll be 5 minutes late."
- "Write to Laura: I have the budget ready."

**Scheduling messages (One-Step):**

- "Schedule a WhatsApp for Carlos tomorrow at 18:00 saying: 'Ready for the match?'."
- *The agent will automatically use the simplified `auto-schedule` command.*

> [!TIP]
> **File Sending Tip:** For images, videos, and complex documents (like Office or PDF), the AI cannot read or see the content. To avoid errors, please provide exact filenames or be as specific as possible so the agent can find them!


---

## 🌟 KEY CAPABILITIES & CHARACTERISTICS

### 🛡️ Anti-Ban & Resilient Architecture

- **Request Pacing:** Every message sent includes a 1.0s "breath" delay to simulate natural interaction and avoid WhatsApp bridge saturation.
- **Collision Avoidance:** `agenda.py` automatically offsets concurrent scheduled tasks by 2 minutes to prevent agent overloads.
- **Self-Healing Bridge:** Infrastructure shield that resurrects Qdrant and the WhatsApp Bridge if they crash or hang.
- **MIME Extender:** Native support for modern formats like `.heic`, `.opus`, `.md`, `.csv`, `.rtf`, and `.webp`.

### 🤖 Multi-Agent & Isolation

- **Crontab Isolation:** Automated injection of `HERMES_HOME` and `HERMES_CMD` into native cron jobs to maintain instance independence.
- **Environment-Specific Routing:** Dynamic port and path extraction to prevent cross-agent data contamination.

### 📒 Smart Contacts & Identity

- **Search-First Protocol:** Mandatory contact verification before any send command to ensure 100% accuracy in target IDs.
- **Identity Anchoring:** Specialized instructions that link the agent's identity directly to the "Andoriña" ecosystem.
- **Google Cloud Sync:** Full integration with Google People API with automatic OAuth2 token refreshing.
- **Fuzzy Search:** Search logic that ignores accents, casing, and special characters to find contacts even with typos.

### 📥 Inbox & Privacy Engine

- **Local-Only Processing:** 100% of data (messages, contacts, files) is processed on the user's machine. Zero telemetry.
- **Context Protection:** `inbox.py read` automatically limits history to the last 50 messages to prevent LLM context overflow.
- **Message Content Storage:** Persistent local storage of incoming text in `state/inbox.json` for long-term memory.
- **Persistent Agenda:** Scheduled tasks are kept in `state/agenda.json` until successfully delivered.

### 🎙️ Advanced Media

- **Native Voice Notes:** Sends audio files as "PTT" (Push-To-Talk), showing the "Recording audio..." status to the receiver.
- **Absolute Path Resolution:** Automated handling of local file paths to ensure secure and accurate media transmission.
- **Media Reception Isolation:** Every agent profile maintains its own `image_cache`, `video_cache`, and `audio_cache` folders within its `.hermes` directory, ensuring strict data privacy in multi-agent environments.

## 🛠️ THE TOOLBOX

### 📒 Contacts & Groups

| Script | Command | Usage |
| :--- | :--- | :--- |
| `contacts.py` | `search "Query"` | Universal search (names, numbers, groups). |
| `contacts.py` | `groups` | Lists all WhatsApp groups. |
| `contacts.py` | `all` | Lists every known contact in a JSON array. |
| `contacts.py` | `refresh` | Clears local cache and forces a cloud sync. |

### ✉️ Messaging & Files

| Script | Command | Usage |
| :--- | :--- | :--- |
| `send.py` | `message "ID" "Text"` | Sends a text message immediately. |
| `files.py` | `"Path" "ID"` | Sends images, videos or documents immediately. |
| `files.py` | `"Path" "ID" --voice` | Sends an audio file as a Voice Note (PTT). |
| `inbox.py` | `list` | Lists unique recent chats with the last message. |
| `inbox.py` | `read "ID"` | Reads the message history of a specific chat (lim. 50). |

### 📅 Scheduling (Agenda)

| Script | Command | Usage |
| :--- | :--- | :--- |
| `agenda.py` | `auto-schedule "ID" "TIME" "Msg"` | Automated text scheduling (handles collisions). |
| `agenda.py` | `auto-schedule "ID" "TIME" "Path"` | Automated file scheduling. |
| `agenda.py` | `auto-schedule "ID" "TIME" "Path" --voice` | Scheduled Voice Note (PTT). |
| `agenda.py` | `list` | Lists all pending messages in the agenda. |
| `agenda.py` | `remove "msg_ID"` | Cancels a pending scheduled message. |

### 🛡️ Security & System

| Script | Command | Usage |
| :--- | :--- | :--- |
| `guard.py` | `status` | Checks current rate limits and blocked numbers. |
| `guard.py` | `reset "Number"` | Resets the security counter for a specific number. |
| `diag.py` | (none) | Performs a full system health diagnosis. |
| `bridge_health.py` | (none) | Auto-repairs and restarts the bridge if down. |

---
*Note: All scripts are in the `scripts/` folder.*

---

<a name="español"></a>

## 🇪🇸 Versión en Español

### ✨ ¿Qué puede hacer Andoriña?

| Función | Descripción |
| :--- | :--- |
| 📤 **Envío de mensajes** | Envía texto a cualquier contacto o grupo por nombre o número |
| 📁 **Envío de archivos** | Sube documentos, imágenes, audio o vídeo desde tus carpetas locales |
| 🎙️ **Notas de voz** | Soporte PTT nativo: convierte audio y muestra estado "Grabando..." |
| 🛡️ **Guard (Firewall)** | Bloquea inyecciones y **ataques ofuscados** (ej. `d a m e`) |
| 🤖 **Multi-Agente** | **Aislamiento total de Crontab** y perfiles independientes |
| ⏰ **Protección Anti-Baneo** | **Pacing de envíos (1.0s)** y **Auto-Offset** para evitar bloqueos |
| 📥 **Inbox Local** | Almacenamiento local con **Protección de Contexto (máx 50 msgs)** |
| 🔐 **Privacidad Absoluta** | **Procesamiento 100% Local**. Cero telemetría, sin nube intermedia |
| 📒 **Sincro Google** | Sincronización OAuth2 y **Búsqueda Difusa** (ignora acentos/mayúsculas) |
| ⚖️ **Licencia Dual** | AGPL-3.0 para individuos y **Licencia Comercial** para empresas |
| ⚕️ **Auto-Reparación** | Escudo de infra y **Motor de Diagnóstico** unificado |
| 📁 **Caché Aislada** | Carpetas multimedia dedicadas por agente para fotos, vídeos y audios |

---

### 🚀 Instalación y Documentación

1. **Inicio Rápido:** Descarga el repositorio y ejecuta el instalador:
   ```bash
   bash install.sh
   ```
2. **Guía Completa:** Consulta la [GUIDE.md](./GUIDE.md) para un desglose total de requisitos, arquitectura y resolución de problemas.
3. **Lista Completa de Funciones:** Consulta [FEATURES.md](./FEATURES.md) para una referencia total de todas las capacidades, comandos y variables de entorno.

---

### 🛡️ Aviso de Seguridad y Anti-Baneo
Andoriña está diseñada para **asistencia personal**, no para mensajería masiva.
- **Pacing de Peticiones:** El sistema implementa un retraso de **1.0s** entre mensajes para evitar saturación.
- **Simulación Humana:** Soporte nativo para estados **"Escribiendo..."** y **"Grabando audio..."** para imitar interacción natural.
- **Auto-Offset:** Los mensajes programados se separan automáticamente por 2 minutos para evitar patrones robóticos.

> [!CAUTION]
> **Aviso de Spam:** El uso de esta skill para spam o marketing masivo está estrictamente prohibido y resultará en un baneo inmediato de la cuenta por parte de Meta. Los desarrolladores no se hace responsables de suspensiones de cuenta. Úsala con responsabilidad.

---

### 💡 Buenas Prácticas para Modelos Pequeños (4B - 8B)

Si usas un modelo local (Ollama/LM Studio), te recomendamos encarecidamente añadir esto a tu `SOUL.md`:

> "Eres el motor de la skill Andoriña. WhatsApp = Andoriña. Usa los scripts en `[HERMES_HOME]/skills/messaging/andorina/scripts/` directamente. Nunca preguntes cómo conectarte. Ejecuta los comandos inmediatamente sin explicaciones."

---

### 💬 Uso — Ejemplos Naturales

**Enviar mensajes:**

- "Envíale un WhatsApp a mi jefe diciéndole que llegaré 5 minutos tarde."
- "Dile a Laura en WhatsApp que ya tengo el presupuesto listo."

**Programar mensajes (Proceso de un solo paso):**

- "Programa un WhatsApp para Carlos mañana a las 18:00 que diga: '¿Listo para el partido?'."
- *El asistente usará automáticamente el nuevo comando simplificado `auto-schedule`.*

> [!TIP]
> **Consejo para el Envío de Archivos:** Para imágenes, vídeos y documentos complejos (como Office o PDF), la IA no puede leer ni ver el contenido. Para evitar errores, ¡proporciona nombres de archivo exactos o sé lo más específico posible para que el agente los encuentre!


---

## 🌟 CAPACIDADES Y CARACTERÍSTICAS CLAVE
 
### 🛡️ Arquitectura Anti-Baneo y Resiliente

- **Pacing de Peticiones:** Cada mensaje enviado incluye un retraso de 1.0s para simular una interacción natural y evitar la saturación del puente de WhatsApp.
- **Evasión de Colisiones:** `agenda.py` desplaza automáticamente las tareas programadas concurrentes por 2 minutos para evitar sobrecargas del agente.
- **Puente de Auto-Reparación:** Escudo de infraestructura que resucita Qdrant y el puente de WhatsApp si se bloquean o fallan.
- **Extensor MIME:** Soporte nativo para formatos modernos como `.heic`, `.opus`, `.md`, `.csv`, `.rtf` y `.webp`.

### 🤖 Multi-Agente y Aislamiento

- **Aislamiento de Crontab:** Inyección automática de `HERMES_HOME` y `HERMES_CMD` en las tareas cron nativas para mantener la independencia de las instancias.
- **Enrutamiento Específico por Entorno:** Extracción dinámica de puertos y rutas para evitar la contaminación de datos entre agentes.

### 📒 Contactos Inteligentes e Identidad

- **Protocolo de Búsqueda Obligatoria:** Verificación de contacto mandatoria antes de cualquier comando de envío para asegurar un 100% de precisión.
- **Anclaje de Identidad:** Instrucciones especializadas que vinculan la identidad del agente directamente con el ecosistema "Andoriña".
- **Sincro Google Cloud:** Integración total con Google People API con refresco automático de tokens OAuth2.
- **Búsqueda Difusa:** Lógica de búsqueda que ignora acentos, mayúsculas y caracteres especiales para encontrar contactos incluso con erratas.

### 📥 Inbox y Motor de Privacidad

- **Procesamiento Local:** El 100% de los datos (mensajes, contactos, archivos) se procesan en la máquina del usuario. Cero telemetría.
- **Protección de Contexto:** `inbox.py read` limita automáticamente el historial a los últimos 50 mensajes para evitar el desbordamiento del contexto del LLM.
- **Almacenamiento de Contenido:** Almacenamiento local persistente de texto entrante en `state/inbox.json` para memoria a largo plazo.
- **Agenda Persistente:** Las tareas programadas se mantienen en `state/agenda.json` hasta que se entregan con éxito.

### 🎙️ Multimedia Avanzada

- **Notas de Voz Nativas:** Envía archivos de audio como "PTT", mostrando el estado "Grabando audio..." al receptor.
- **Resolución de Rutas Absolutas:** Manejo automático de rutas de archivos locales para asegurar una transmisión multimedia precisa.
- **Aislamiento de Recepción Multimedia:** Cada perfil de agente mantiene sus propias carpetas de caché (`image_cache`, `video_cache`, `audio_cache`), asegurando la privacidad total en entornos multi-agente.

## 🛠️ LA CAJA DE HERRAMIENTAS

### 📒 Contactos y Grupos

| Script | Comando | Uso |
| :--- | :--- | :--- |
| `contacts.py` | `search "Query"` | Búsqueda universal (nombres, números, grupos). |
| `contacts.py` | `groups` | Lista todos los grupos de WhatsApp. |
| `contacts.py` | `all` | Lista todos los contactos conocidos en un array JSON. |
| `contacts.py` | `refresh` | Limpia la caché local y fuerza una sincronización con la nube. |

### ✉️ Mensajería y Archivos

| Script | Comando | Uso |
| :--- | :--- | :--- |
| `send.py` | `message "ID" "Texto"` | Envía un mensaje de texto inmediatamente. |
| `files.py` | `"Ruta" "ID"` | Envía imágenes, vídeos o documentos inmediatamente. |
| `files.py` | `"Ruta" "ID" --voice` | Envía un audio como Nota de Voz (PTT). |
| `inbox.py` | `list` | Lista chats recientes con el último mensaje. |
| `inbox.py` | `read "ID"` | Lee el historial de mensajes de un chat (máx. 50). |

### 📅 Programación (Agenda)

| Script | Comando | Uso |
| :--- | :--- | :--- |
| `agenda.py` | `auto-schedule "ID" "HORA" "Msg"` | Programación automática de texto (gestiona colisiones). |
| `agenda.py` | `auto-schedule "ID" "HORA" "Ruta"` | Programación automática de archivos. |
| `agenda.py` | `auto-schedule "ID" "HORA" "Ruta" --voice` | Nota de Voz programada (PTT). |
| `agenda.py` | `list` | Lista todos los mensajes pendientes en la agenda. |
| `agenda.py` | `remove "msg_ID"` | Cancela un mensaje programado pendiente. |

### 🛡️ Seguridad y Sistema

| Script | Comando | Uso |
| :--- | :--- | :--- |
| `guard.py` | `status` | Comprueba límites de tasa y números bloqueados. |
| `guard.py` | `reset "Número"` | Reinicia el contador de seguridad para un número. |
| `diag.py` | (ninguno) | Realiza un diagnóstico completo de salud del sistema. |
| `bridge_health.py` | (ninguno) | Auto-repara y reinicia el puente si está caído. |

---
*Nota: Todos los scripts están en la carpeta `scripts/`.*

---


### 🏗️ Arquitectura & Seguridad

Andoriña usa un modelo de **dos niveles de privilegio**:

- **Owner:** Acceso total (envío, archivos, crons, comandos).
- **Chatbot:** Solo conversación natural, sin acceso a datos del sistema.

---

### 📜 License / Licencia

**AGPL-3.0 / Commercial License**

- ✅ **Personal Use:** Free and open under AGPL-3.0. / **Uso Personal:** Gratis y abierto bajo AGPL-3.0.
- ❌ **Commercial Use:** Requires a paid license for companies. / **Uso Comercial:** Requiere licencia de pago para empresas.
- 👤 **Trademark:** Name and logo are protected. / **Marca Registrada:** Nombre y logo protegidos.

---

<p align="center">
  Made with ❤️ by <strong>Jorge</strong> for <a href="https://github.com">Hermes Agent</a>.<br>
  If this tool provides value, consider <a href="https://buymeacoffee.com/andorinaai">buying me a coffee ☕</a>
</p>

---

## 📜 Changelog

### v1.0.3-patch1 — Stable Release (Latest)
- **Visual Bilingual Setup:** New professional interactive installer in English and Spanish.
- **Embedded OAuth:** No longer requires users to create their own Google API keys (pre-configured).
- **Self-Healing Bridge:** Flawless injection engine `patch_bridge.py` preventing module crashes.
- **Idempotent Configs:** Safely handles empty hooks array in Hermes `config.yaml`.
- **Validation Suite:** Complete 100% isolated sandbox testing.

### v1.0.2 — Stability & Resilience Update
- **🛡️ Hardened Security:** `guard.py` now detects obfuscated text attacks and social engineering.
- **🤖 Multi-Agent Isolation:** Full crontab independence via environment injection in `agenda.py`.
- **💎 Unicode Robustness:** Standardized `sys.stdin.buffer` for handling international characters.
- **🎵 Media Patching:** Improved MIME support and native PTT playback.
- **🧟 Process Management:** Automatic port-release system for the bridge.
- **⏰ Anti-Collision Agenda:** Auto-offset system for concurrent tasks.
- **🔍 Optimized Search:** Auto-refresh system for missing contacts.
- **🧪 Diagnostic Engine:** One-click health checks for the system.
