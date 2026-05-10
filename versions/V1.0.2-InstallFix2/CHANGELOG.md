# 📝 Changelog - Andoriña v1.0.2

## [v1.0.2-hotfix1] - 2026-05-11
**"The Linux Portability Fix" / "El Fix de Portabilidad Linux"**

---

### 🇺🇸 English

#### 🔧 Critical Fixes
- **Bridge Backup Safety:** `patch_bridge.py` and `bridge_health.py` now **always** create a backup of `bridge.js` before patching (not just the first time), ensuring the user always has the latest clean version to restore from after Hermes updates.
- **SyntaxError Fix:** Removed the duplicate `chatId` declaration in the presence/typing injection that caused `SyntaxError: Identifier 'chatId' has already been declared` and crashed the bridge on fresh installs.
- **Contacts `.env` Parsing:** Fixed `contacts.py` `load_env()` not filtering comments — a commented-out line like `# TOKEN=old` was being parsed as a real value, potentially overriding active tokens.

#### 🖥️ Linux Portability & Stability
- **Universal Autostart:** Replaced hardcoded `gnome-terminal` with automatic detection of 6 terminal emulators (gnome-terminal, konsole, xfce4-terminal, mate-terminal, lxterminal, xterm) with headless fallback. Now works on GNOME, KDE, XFCE, MATE, LXDE, and tiling WMs.
- **ARM64 Support:** `setup_portable.py` now detects the CPU architecture via `platform.machine()` and downloads the correct Qdrant binary (x86_64 or aarch64). Previously hardcoded to x86_64.
- **Multi-Profile Detection:** `install.sh` now scans `$HOME/.hermes/profiles/*/` in addition to `$HOME/.*` to correctly detect agents installed as Hermes sub-profiles.
- **Multi-Tool Zombie Killer:** `bridge_health.py` now implements a graceful degradation fallback (`fuser` -> `lsof` -> standard stop) to securely kill stuck WhatsApp bridge ports on minimal Linux distributions.
- **Installer Resilience:** `install.sh` now locks its execution to its own directory (`cd "$(dirname "$0")"`) to prevent silent failures when executed from outside its folder.
- **Strict Dependency Check:** The installer now enforces a hard stop with a clear error message if Python 3 is not detected on the host system, rather than silently failing downstream.

---

### 🇪🇸 Español

#### 🔧 Fixes Críticos
- **Seguridad del Backup del Bridge:** `patch_bridge.py` y `bridge_health.py` ahora **siempre** crean una copia de seguridad de `bridge.js` antes de parchear (no solo la primera vez), asegurando que el usuario siempre tenga la versión limpia más reciente para restaurar tras actualizaciones de Hermes.
- **Fix SyntaxError:** Eliminada la declaración duplicada de `chatId` en la inyección de presencia/typing que causaba `SyntaxError: Identifier 'chatId' has already been declared` y crasheaba el bridge en instalaciones nuevas.
- **Parseo del `.env` en Contactos:** Corregido `contacts.py` `load_env()` que no filtraba comentarios — una línea comentada como `# TOKEN=viejo` se parseaba como valor real, pudiendo sobreescribir tokens activos.

#### 🖥️ Estabilidad y Portabilidad Linux
- **Autostart Universal:** Reemplazado `gnome-terminal` hardcodeado por detección automática de 6 emuladores de terminal (gnome-terminal, konsole, xfce4-terminal, mate-terminal, lxterminal, xterm) con fallback sin terminal. Ahora funciona en GNOME, KDE, XFCE, MATE, LXDE y tiling WMs.
- **Soporte ARM64:** `setup_portable.py` ahora detecta la arquitectura de CPU mediante `platform.machine()` y descarga el binario correcto de Qdrant (x86_64 o aarch64). Antes estaba hardcodeado a x86_64.
- **Detección Multi-Perfil:** `install.sh` ahora escanea `$HOME/.hermes/profiles/*/` además de `$HOME/.*` para detectar correctamente agentes instalados como sub-perfiles de Hermes.
- **Asesino de Zombies Multi-Herramienta:** `bridge_health.py` ahora implementa un fallback de degradación (`fuser` -> `lsof` -> parada estándar) para matar de forma segura los puertos atascados del puente de WhatsApp en distribuciones Linux minimalistas.
- **Resiliencia del Instalador:** `install.sh` ahora bloquea su ejecución a su propio directorio (`cd "$(dirname "$0")"`) para prevenir fallos silenciosos al ejecutarse desde fuera de su carpeta.
- **Verificación Estricta de Dependencias:** El instalador ahora fuerza una parada total con un mensaje de error claro si no detecta Python 3 en el sistema host, en lugar de fallar silenciosamente en pasos posteriores.

---

## [v1.0.2] - 2026-05-09
**"The Autonomous Manager Update" / "La Actualización del Gestor Autónomo"**

---

### 🇺🇸 English

#### 🛡️ Security & Firewall Hardening
- **Enhanced Anti-Ban:** Increased request pacing to **1.0s** and implemented a native **Human Simulation Engine**.
- **Typing & Recording Indicators:** The system now triggers "Escribiendo..." (Typing) and "Grabando audio..." (Recording) statuses before sending messages or media, significantly reducing bot detection risks.
- **Input Normalization:** Implemented a new defense layer in `guard.py` that strips spaces and common separators.
- **Social Engineering Defense:** Strengthened pattern matching against identity spoofing.
- **Path Traversal Blocking:** Improved regex to block advanced directory traversal.

#### 🤖 Multi-Agent & Isolation
- **Crontab Isolation:** Rewrote `agenda.py` to inject `HERMES_HOME` and `HERMES_CMD` into native Linux cron jobs, ensuring tasks are executed within the correct agent profile.
- **Atomic Persistence:** Scheduled messages now stay in `agenda.json` until a successful HTTP 200/Success response is received from the bridge, preventing message loss during downtime.
- **Unicode Robustness:** Migrated `hook_inbox.py` to `sys.stdin.buffer` to handle complex emojis and international characters without process crashes.
- **Media Reception Isolation:** Integrated support for per-agent media storage. Incoming images, videos, and audio are now stored in dedicated cache folders within each agent's `HERMES_HOME`, preventing cross-agent data leakage.
- **Inbox Assistance Engine:** Standardized `inbox.py` for persistent local storage of incoming text, allowing the agent to query conversation history (up to 50 messages) for better context and summaries.
- **Bridge Self-Healing & Patching:** Implemented an automated MIME-patching engine in `bridge_health.py` that dynamically adds support for `.heic`, `.zip`, `.ogg`, `.md`, and presence indicators (`presence: "recording"`) to the core WhatsApp bridge.

#### 🛠️ Web Refactoring & Stability
- **Eliminated Inline Styles:** Complete migration of 30+ `style="..."` attributes to semantic classes in `styles.css`.
- **Structural Validation:** Fixed tag nesting and normalized tag endings for 100% W3C HTML5 compliance.
- **Safe Navigation:** Implemented `rel="noopener noreferrer"` on all external links.

#### 🔌 Portability & Compatibility
- **Bridge Path Override (`WHATSAPP_BRIDGE_PATH`):** Both `bridge_health.py` and `patch_bridge.py` now support a custom bridge path via environment variable, enabling installations where Hermes uses a non-standard directory structure.

#### 📦 Repository Management
- **Professional History:** Cleaned and consolidated commits (Squash) for a professional GitHub timeline.
- **Version Parity:** Ensured absolute parity between the main website and the version package.

---

### 🇪🇸 Español

#### 🛡️ Seguridad y Blindaje del Cortafuegos
- **Anti-Baneo Reforzado:** Incrementado el pacing de peticiones a **1.0s** e implementado un **Motor de Simulación Humana** nativo.
- **Indicadores de Actividad:** El sistema ahora activa los estados "Escribiendo..." y "Grabando audio..." antes de enviar mensajes o archivos, reduciendo drásticamente el riesgo de detección por parte de Meta.
- **Normalización de Entradas:** Implementada una nueva capa de defensa en `guard.py` que elimina espacios y separadores comunes.
- **Defensa contra Ingeniería Social:** Reforzado el emparejamiento de patrones contra la suplantación de identidad.
- **Bloqueo de Traversal de Rutas:** Mejoradas las expresiones regulares para bloquear saltos de directorio.

#### 🤖 Multi-Agente y Aislamiento
- **Aislamiento en Crontab:** Reescrito `agenda.py` para inyectar `HERMES_HOME` y `HERMES_CMD` en los cron jobs nativos de Linux, asegurando que las tareas se ejecuten en el perfil de agente correcto.
- **Persistencia Atómica:** Los mensajes programados permanecen en `agenda.json` hasta recibir una respuesta exitosa (HTTP 200/Success) del puente, evitando la pérdida de mensajes durante caídas de servicio.
- **Robustez Unicode:** Migrado `hook_inbox.py` a `sys.stdin.buffer` para manejar emojis complejos y caracteres internacionales sin caídas del proceso.
- **Aislamiento de Recepción Multimedia:** Soporte integrado para almacenamiento de medios por agente. Imágenes, vídeos y audios entrantes se guardan en carpetas de caché dedicadas dentro del `HERMES_HOME` de cada agente, evitando fugas de datos entre perfiles.
- **Motor de Asistencia de Inbox:** Estandarizado `inbox.py` para el almacenamiento local persistente de texto entrante, permitiendo al agente consultar el historial (hasta 50 mensajes) para obtener mejor contexto y resúmenes.
- **Auto-Reparación y Parcheo del Puente:** Implementado un motor de parcheo MIME automático en `bridge_health.py` que añade soporte dinámico para `.heic`, `.zip`, `.ogg`, `.md` e indicadores de presencia (`presence: "recording"`) al puente de WhatsApp.

#### 🛠️ Refactorización y Estabilidad Web
- **Adiós a los Estilos Inline:** Migración total de más de 30 estilos `style="..."` a clases semánticas en `styles.css`.
- **Validación Estructural:** Corrección de anidamiento de etiquetas y normalización de cierres para cumplir con el estándar HTML5 de la W3C al 100%.
- **Navegación Segura:** Implementación de `rel="noopener noreferrer"` en todos los enlaces externos.

#### 🔌 Portabilidad y Compatibilidad
- **Override de Ruta del Puente (`WHATSAPP_BRIDGE_PATH`):** Tanto `bridge_health.py` como `patch_bridge.py` ahora admiten una ruta personalizada del puente mediante variable de entorno, permitiendo instalaciones donde Hermes usa una estructura de directorios no estándar.

#### 📦 Gestión de Repositorio
- **Historial Profesional:** Limpieza y consolidación de commits (Squash) para una línea de tiempo clara en GitHub.
- **Sincronización de Versiones:** Asegurada la paridad absoluta entre la web principal y los archivos contenidos en el paquete.

---
*Developed with &#10084; by Jorge.*
