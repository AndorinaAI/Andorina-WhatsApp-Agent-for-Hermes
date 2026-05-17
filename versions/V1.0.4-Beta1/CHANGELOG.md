# 📝 Changelog - Andoriña v1.0.4-Beta1

## [v1.0.4-Beta1] - 2026-05-17
**"The Refactoring & Code Quality Update" / "Actualización de Refactorización y Calidad de Código"**

### 🇺🇸 English
#### ✨ New Features & Enhancements
- **Shared Code Module (`common.py`):** Consolidated duplicated HTTP requests, logging, and environment parsing logic from `send.py` and `files.py` into a unified `common.py` module, greatly reducing technical debt and maintenance overhead.
- **Improved Code Robustness:** Performed a codebase-wide audit to remove all bare `except:` clauses, replacing over 33 instances across 14 Python scripts with `except Exception:`. This prevents critical system exceptions (like `SystemExit` and `KeyboardInterrupt`) from being accidentally caught, ensuring correct program termination and debugging.
- **Test Runner Fixes:** Renamed internal testing wrapper from `test()` to `assert_test()` across `test_part1`, `test_part2`, `test_part3`, and `test_part4` to resolve silent collisions with `pytest`, enabling seamless native execution.
- **Git Hygiene:** Cleaned up repository tracking by securely removing the `state/` directory from git cache, deleting internal test `.zip` files, and automatically ignoring the Python virtual environment (`.venv/`).
- **Web UI & Documentation Bumping:** Fully audited `docs/index.html` and `docs/index-es.html` to ensure SEO compliance, modern CSS glassmorphism, and bumped all version indicators to the official `v1.0.4-Beta1`.

#### 🔧 Critical Fixes
- **Self-Healing Bridge Restored:** Added the missing `ensure_patched()` function to `bridge_health.py` to restore the primary self-healing infrastructure, preventing silent failures when `send.py` and `files.py` attempt to communicate with a degraded bridge.
- **Path Traversal Mitigation:** Added `filter='data'` to `tar.extractall` in `setup_portable.py` to prevent potential path traversal vulnerabilities during binary downloads, complying with the latest Python 3.12+ security guidelines.
- **Dead Code Elimination:** Removed the unused `STAMP_PATH` variable from `bridge_health.py` and eliminated unused imports (like `glob`) in `wipe_logs.py`.

### 🇪🇸 Español
#### ✨ Nuevas Funciones y Mejoras
- **Módulo de Código Compartido (`common.py`):** Consolidada la lógica duplicada de peticiones HTTP, registro y lectura de variables de entorno de `send.py` y `files.py` en un módulo unificado `common.py`, reduciendo drásticamente la deuda técnica.
- **Robustez del Código Mejorada:** Realizada una auditoría en todo el código para eliminar los bloques `except:` vacíos, reemplazando más de 33 instancias en 14 scripts Python por `except Exception:`. Esto evita que excepciones críticas (como `SystemExit`) sean atrapadas por error.
- **Correcciones del Test Runner:** Renombrada la función interna de pruebas de `test()` a `assert_test()` en toda la suite de pruebas para resolver colisiones silenciosas con `pytest`.
- **Higiene de Git:** Limpiado el control de versiones eliminando el directorio `state/` de la caché de git, borrando archivos `.zip` de pruebas internas y añadiendo `.venv/` al `.gitignore`.
- **Actualización de Web y Documentación:** Auditados `docs/index.html` y `docs/index-es.html` para asegurar cumplimiento SEO, mantener el moderno CSS glassmorphism, y actualizar todos los indicadores a la versión oficial `v1.0.4-Beta1`.

#### 🔧 Fixes Críticos
- **Self-Healing Restaurado:** Añadida la función faltante `ensure_patched()` a `bridge_health.py` para restaurar la infraestructura de auto-reparación, previniendo fallos silenciosos cuando `send.py` y `files.py` contactan con el puente.
- **Mitigación de Path Traversal:** Añadido `filter='data'` a `tar.extractall` en `setup_portable.py` para prevenir posibles vulnerabilidades durante la extracción de binarios.
- **Eliminación de Código Muerto:** Eliminada la variable `STAMP_PATH` sin uso en `bridge_health.py` e importaciones innecesarias en `wipe_logs.py`.

---

## [v1.0.3-patch2] - 2026-05-15
**"The Alert & Groups Update" / "La Actualización de Alertas y Grupos"**

### 🇺🇸 English
#### ✨ New Features & Enhancements
- **Semantic Topic Alerts:** Introduced a new `alerts.py` engine. The AI can now set up permanent listening rules based on keywords (synonyms, slang, and diminutives) to notify the owner automatically when specific topics are discussed, with zero extra LLM computation cost.
- **Advanced Group Management:** `guard.py` now implements "Mention-Only Mode" for groups. The AI will completely ignore group messages to prevent context overflow and API cost spikes, unless triggered by configurable wake words (e.g., `@andorina`).
- **Deep History Context:** Updated `inbox.py` to allow the AI to request a specific number of historical messages (e.g., `inbox.py read "ID" 200` or `all`), bypassing the previous 50-message limit for deep context analysis. Note: History is not retroactive and begins recording upon skill installation.
- **Atomic Persistence & POSIX Locking:** Implemented atomic file I/O and POSIX file locking (`fcntl`) across all state-management scripts to eliminate race conditions and prevent data corruption in high-concurrency scenarios.
- **Google OAuth Credentials Update:** Updated the default Client ID and Secret for Google Contacts synchronization. **Warning:** Users must re-authenticate and re-synchronize their contacts as previous tokens are now invalid.

#### 🔧 Critical Fixes
- **Universal Event Listener (Inbox Bugfix):** The skill was previously failing to read incoming messages. The new native Hermes Gateway changed its internal event broadcasting name to `whatsapp:message`, while our hook was strictly filtering for the legacy `message_received` event. `hook_inbox.py` has been patched to listen to both events simultaneously.
- **JSON Type Corruption Recovery:** Added strict type validation upon loading JSON state files. If a file is corrupted into a valid but wrong type (e.g., a list instead of a dict), the system now gracefully resets it to the correct default type instead of crashing with `AttributeError`.

### 🇪🇸 Español
#### ✨ Nuevas Funciones y Mejoras
- **Alertas Semánticas por Temas:** Introducido un nuevo motor `alerts.py`. La IA ahora puede configurar reglas de escucha permanente basadas en palabras clave (sinónimos y jerga) para notificar al administrador automáticamente cuando se discutan temas específicos, sin coste computacional extra para el LLM.
- **Gestión Avanzada de Grupos:** `guard.py` ahora implementa el "Modo de Mención" para grupos. La IA ignorará por completo los mensajes de grupos para evitar el colapso de contexto y el gasto de API, a menos que se invoque mediante palabras de despertar configurables (ej. `@andorina`).
- **Contexto de Historial Profundo:** Actualizado `inbox.py` para permitir a la IA solicitar un número específico de mensajes históricos (ej. `inbox.py read "ID" 200` o `all`), superando el límite anterior de 50 mensajes. **Aviso importante:** El historial NO es retroactivo y solo comienza a grabarse tras la instalación de la skill.
- **Persistencia Atómica y Bloqueo POSIX:** Implementada escritura atómica y bloqueo de archivos POSIX (`fcntl`) en todos los scripts de gestión de estado para eliminar condiciones de carrera y prevenir la corrupción de datos.
- **Actualización de Credenciales de Google OAuth:** Actualizadas las claves (Client ID y Secret) por defecto para la sincronización de contactos. **Aviso:** Los usuarios deberán volver a pasar por el proceso de autenticación y sincronizar sus contactos, ya que los tokens antiguos dejarán de funcionar.

#### 🔧 Fixes Críticos
- **Escucha Universal de Eventos (Fix de Inbox):** La skill fallaba al leer los mensajes entrantes en instalaciones nuevas. El nuevo Gateway nativo de Hermes actualizó el nombre de su evento interno a `whatsapp:message`, mientras que nuestro hook estaba programado para ignorar cualquier cosa que no fuera el evento antiguo (`message_received`). Se ha corregido `hook_inbox.py` para procesar ambos eventos.
- **Recuperación por Corrupción de Tipo JSON:** Añadida validación de tipo estricta al cargar archivos JSON. Si un archivo se corrompe guardando un tipo válido pero incorrecto (ej. una lista en vez de un diccionario), el sistema lo resetea al valor por defecto en lugar de crashear con `AttributeError`.

---

## [v1.0.3-patch1] - 2026-05-13
**"The Installer Updates & Refined File Search Protocol" / "Actualizaciones del Instalador y Protocolo de Búsqueda de Archivos Refinado"**

### 🇺🇸 English

#### 🔧 Critical Fixes & Improvements
- **Gateway Auto-Install:** Updated `setup.py` to automatically install the Hermes gateway binaries and start the service during the installation process. **Note:** The user still needs to manually link their WhatsApp via QR code in the Hermes UI, but the underlying service deployment is now fully automated.
- **Agent Command Hallucination Defense:** Added strict error handling in `send.py` and `contacts.py` to return JSON errors and exit code 1 on unknown commands, preventing agents from assuming success on invalid commands.
- **Refined File Search Protocol:** Updated `SKILL.md` with a strict step-by-step search algorithm using `xdg-user-dir` for localized paths and explicit placeholders to prevent small LLMs from over-fitting on examples.
- **Multimedia & Office Warning:** Added explicit warnings in `SKILL.md` and `README.md` about the inability of LLMs to read images, videos, and Office documents, advising users to use precise filenames.

### 🇪🇸 Español

#### 🔧 Fixes Críticos y Mejoras
- **Auto-instalación de Gateway:** Actualizado `setup.py` para instalar los binarios y arrancar automáticamente el servicio gateway de Hermes. **Nota:** El usuario aún debe escanear el QR manualmente en la interfaz de Hermes para vincular su cuenta, pero el despliegue del servicio queda totalmente automatizado.
- **Defensa contra Alucinaciones de Comandos:** Añadido control de errores estricto en `send.py` y `contacts.py` para devolver errores JSON y código 1 ante comandos desconocidos, evitando que la IA asuma éxito en comandos inventados.
- **Protocolo de Búsqueda Refinado:** Actualizado `SKILL.md` con un algoritmo de búsqueda estricto paso a paso usando `xdg-user-dir` para rutas localizadas y variables genéricas para evitar que modelos pequeños se confundan con los ejemplos.
- **Aviso de Multimedia y Office:** Añadidas advertencias explícitas en `SKILL.md` y `README.md` sobre la incapacidad de la IA para leer imágenes, vídeos y documentos de Office, aconsejando al usuario usar nombres de archivo precisos.

---

## [v1.0.3] - 2026-05-12
**"The Stable Installer Update" / "La Actualización del Instalador Estable"**

### 🇺🇸 English

#### ✨ New Features & Enhancements
- **Professional Bilingual Installer:** `setup.py` has been completely rewritten. It now features an interactive, color-coded CLI interface with step-by-step progress tracking, fully translated into English (default) and Spanish.
- **Embedded Zero-Config Auth:** Eliminated the friction of manual Google Cloud configuration. The system now uses pre-embedded OAuth keys, meaning users no longer need to provide their own `CLIENT_ID` or `SECRET` to sync contacts.
- **Extreme Validation Sandbox:** Engineered `test_sandbox_full.py`, an aggressive 92-assertion test suite that simulates complete environment installations, isolates modules, and ensures total codebase integrity across different OS conditions.
- **Web Interface Upgrades:** Improved responsive CSS Grid layouts for the documentation website to ensure perfect stacking of features on mobile devices, and corrected SVG alignment.

#### 🔧 Critical Architecture Fixes
- **ESM Self-Healing Engine:** The bridge patcher (`patch_bridge.py`) was entirely re-architected. It now dynamically locates the end of `import` blocks to inject global variables (like `globalLastQR`), completely eliminating `SyntaxError` crashes on modern Node environments.
- **Endpoint Injection Mastery:** The patcher now cleanly injects `/groups`, `/qr`, and `/health` REST endpoints into the Baileys bridge without damaging the original `express` server structure or removing the shebang (`#!/usr/bin/env node`).
- **YAML Idempotency & Bug Fix:** The installer now intelligently detects the known Hermes `hooks: {}` syntax bug in `config.yaml`, automatically re-casting it to a valid list (`[]`) and preventing silent activation failures.
- **Idempotent SOUL Anchoring:** Injecting the "Andoriña Identity" into `SKILL.md` is now 100% idempotent. The system detects existing anchors and prevents duplicating the system prompt upon multiple installations.
- **Safe Graceful Degradation:** Verified that modules like the Agenda (cron jobs) will not crash the system if the native service is unavailable, opting to return clean JSON error payloads instead.

---

### 🇪🇸 Español

#### ✨ Nuevas Funciones y Mejoras
- **Instalador Bilingüe Profesional:** `setup.py` ha sido reescrito por completo. Ahora cuenta con una interfaz CLI interactiva a todo color, con seguimiento de progreso paso a paso y traducida totalmente al Inglés (por defecto) y Español.
- **Zero-Configuración (Auth Embebido):** Se eliminó la fricción de configurar Google Cloud manualmente. El sistema ahora usa credenciales OAuth pre-embebidas, por lo que el usuario ya no debe proveer su propio `CLIENT_ID` o `SECRET` para sincronizar contactos.
- **Sandbox de Validación Extrema:** Desarrollado `test_sandbox_full.py`, una agresiva suite de 92 aserciones que simula instalaciones completas, aísla módulos y garantiza la integridad total del código en diferentes condiciones del SO.
- **Mejoras en la Web:** Mejorado el diseño responsivo (CSS Grid) de la página de documentación para asegurar un apilamiento perfecto en dispositivos móviles y corregido el centrado de iconos SVG.

#### 🔧 Arreglos Críticos de Arquitectura
- **Motor Self-Healing para ESM:** El parcheador del puente (`patch_bridge.py`) fue re-arquitectado. Ahora localiza dinámicamente el final de los bloques `import` para inyectar variables globales (como `globalLastQR`), eliminando de raíz los crasheos por `SyntaxError` en entornos Node modernos.
- **Inyección Maestra de Endpoints:** El parcheador ahora inyecta limpiamente los endpoints REST `/groups`, `/qr` y `/health` en el bridge de Baileys sin dañar el servidor `express` original ni eliminar el shebang (`#!/usr/bin/env node`).
- **Idempotencia y Fix YAML:** El instalador detecta de forma inteligente el conocido bug `hooks: {}` en el archivo `config.yaml` de Hermes, convirtiéndolo automáticamente en una lista válida (`[]`) y previniendo fallos silenciosos de activación de la skill.
- **Anclaje SOUL Idempotente:** La inyección de la "Identidad Andoriña" en `SKILL.md` ahora es 100% segura frente a repeticiones. El sistema detecta anclas existentes y evita duplicar el prompt del sistema tras múltiples instalaciones.
- **Degradación Segura:** Se verificó que módulos como la Agenda (cron jobs) no crashearán el sistema si el servicio nativo no está disponible, optando por devolver cargas JSON limpias en su lugar.

---

## [v1.0.2-hotfix3] - 2026-05-11
**"The Installer Visibility & QR Fix" / "El Fix de Visibilidad y QR en Instalador"**

### 🇺🇸 English
#### 🔧 Critical Fixes
- **WhatsApp QR Visibility:** Modified `bridge_health.py` and `install.sh` to allow the QR code to be displayed in the terminal during the setup process if a session is not active.
- **Smart Connection Check:** The bridge health engine now detects the actual WhatsApp connection state (Open/Connected). It skips unnecessary restarts if the session is already active.
- **Installer Input Alignment:** Fixed a bug in `install.sh` where the non-interactive setup was misaligned with the new memory limit prompts, causing EOF errors.
- **Custom Bridge URL Preservation:** `setup.py` no longer overwrites a custom `WHATSAPP_BRIDGE_URL` if it already exists in the `.env` file.

---

## [v1.0.2-hotfix2] - 2026-05-11
**"Integrity & Portability Fix" / "Fix de Integridad y Portabilidad"**

### 🇺🇸 English
#### 🔧 Critical Fixes
- **YAML Indentation Preservation:** Fixed a regression in `bridge_health.py` where updating Hermes configuration would strip leading indentation, corrupting `config.yaml`.
- **YAML-Safe Hook Injection:** Refactored `setup.py` to wrap hook commands in double quotes.
- **Universal Autostart:** Replaced hardcoded `gnome-terminal` with automatic detection of 6 terminal emulators with headless fallback.
- **ARM64 Support:** `setup_portable.py` now detects CPU architecture and downloads the correct Qdrant binary.
- **SyntaxError Fix:** Removed duplicate `chatId` declaration in bridge patching.

### 🇪🇸 Español
#### 🔧 Fixes Críticos
- **Preservación de Indentación YAML:** Corregida regresión en `bridge_health.py` que eliminaba la indentación inicial en `config.yaml`.
- **Inyección de Hooks YAML-Safe:** Refactorizado `setup.py` para envolver comandos en comillas dobles.
- **Autostart Universal:** Detección automática de 6 emuladores de terminal con fallback sin ventana.
- **Soporte ARM64:** Detección automática de arquitectura para descargar el binario de Qdrant correcto.
- **Fix SyntaxError:** Eliminada declaración duplicada de `chatId` en el parcheo del bridge.

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

