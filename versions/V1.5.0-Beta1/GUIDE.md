# 📖 Andoriña v1.5.0-Beta1 — Complete User Guide
## 🕊️ Autonomous WhatsApp Manager for Hermes

> [!WARNING]
> **🔬 BETA — Requires Testing / BETA — Requiere Testing**
> This version introduces a massive zero-trust security refactoring. While the installation process and core features should work perfectly, some edge-case functions related to the Sub-Soul sync and the `tool_guard` are in advanced testing.
> Esta versión introduce una refactorización de seguridad zero-trust masiva. Aunque la instalación y las funciones principales deberían funcionar perfectamente, algunas funciones límite relacionadas con la sincronización Sub-Soul y el `tool_guard` están en fase avanzada de prueba.

---

### 🇺🇸 English Version

#### 📋 Requirements
- **Operating System:** Linux (Ubuntu/Debian recommended).
- **Core Engine:** [Hermes Agent](https://github.com/AndorinaAI/Andorina-WhatsApp-Agent-for-Hermes) installed.
- **Python:** v3.8 or higher (No external pip dependencies required).
- **Node.js:** Required for the WhatsApp Bridge.

#### 🚀 Quick Installation
1. Unzip the downloaded folder.
2. Double-click on `Andorina-Panel.sh` to launch the Andoriña Control Panel. If double-clicking doesn't work, open a terminal in that folder and run `bash ./Andorina-Panel.sh`.
3. Follow the visual setup guide in your browser. On the first login screen, you can enter **any password you want** to set it as your master password.
4. **Important:** Once the setup is complete, **close the current browser tab** because it belongs to the temporary installation folder. To use the panel normally, open it from the new Desktop Shortcut or the installed skill folder.
5. For a full list of features and environment variables, see [FEATURES.md](./FEATURES.md).

#### 🧠 How the Architecture Works
Andoriña acts as a **zero-trust bridge layer** between your AI Agent and WhatsApp:
1. **Inbox Webhook Hook:** Every incoming message triggers a deduplicated dispatch through `whatsapp.py` to `webhook.py`, updating `inbox.json`.
2. **Identity & Orchestrator:** The `orchestrator_hook.py` dynamically resolves complex WhatsApp LID accounts to standard numbers using `lid-mapping-*_reverse.json`, injecting Sub-Soul RAG context directly.
3. **Guard Gates:** Before the AI reads a message or executes a tool, `input_guard.py` filters prompt injections, and `tool_guard.py` enforces directory traversal restrictions (`allowed_folders`).
4. **Task Execution:** External tools execute via `tool_executor.py` in isolated subprocesses with a hard 30-second TTL to avoid AI freezing.
5. **Resilient Sending:** Messages sent via `send.py` simulate human composing delays. Tasks in `agenda.py` auto-offset by 2 minutes to dodge bot collisions and persist within a 60-minute delivery window in case the AI arrives late.

#### 📂 File Breakdown (The Toolbox)
- `Andorina-Panel.sh`: The graphical Linux Dashboard.
- `GUI/static/monitor.html`: A real-time localized view of Bridge, Agent, and Server logs with autoscrolling.
- `setup.py`: Core configuration engine that auto-detects Hermes profiles and installs patch scripts.
- `scripts/security/orchestrator_hook.py`: The identity and context resolving engine.
- `scripts/security/output_pipeline/pipeline.py`: DLP engine for LLM output sanitization.
- `scripts/transport/send.py`: High-speed paced text delivery and typing simulator.
- `scripts/tools/files.py`: Universal multimedia engine detecting correct MIME types automatically (Images, Videos, Docs, PTT).
- `scripts/tools/agenda.py`: Crontab-powered scheduling (one-off, recurring) with collision avoidance offsets.
- `scripts/tools/contacts.py`: Fuzzy-search engine and Long-Term Memory (Notes) manager containing the `note-section-set` tool.
- `scripts/tools/alerts.py`: Subscribes listeners to contacts and automatically messages the target to ensure privacy notifications.
- `scripts/utils/admin_cli.py`: RBAC management (Roles, Chatbot toggles).
- `scripts/utils/bridge_health.py`: The auto-repair "medic" for the node infrastructure.

#### 🛂 Security & Roles (RBAC)
Andoriña uses strict Role-Based Access Control (`guard_rules.json`).
- **Owner:** Full access to all tools, files, and system settings (`all` permission).
- **Manager:** Can schedule messages, read inbox, and send files, restricted to `allowed_folders`.
- **Chatbot:** By default can only converse. When configured with `allowed_folders`, it is automatically promoted to a Restricted Read mode.
- **Blocked:** Ignored entirely by the system to save LLM tokens.
- **Sub-Souls:** Sub-Soul group sync is reliably determined by analyzing JIDs longer than 15 digits (`@g.us`). Assign personalities in `state/souls/` for individual/group chats.

#### 🏥 Basic Troubleshooting
- **"Bridge Offline":** Run `python3 scripts/utils/bridge_health.py`. It kills zombie processes and restarts the gateway.
- **"Contact not found":** Run `python3 scripts/tools/contacts.py refresh`. This clears the cache and refetches cloud data.
- **Group not found:** Groups are fetched from the live bridge. If the bridge is offline, only groups cached by Hermes are shown. Use `scripts/tools/contacts.py search` to find silent groups.
- **Permission Denied / Tool Blocked:** If the AI complains it cannot read a file, ensure the directory is registered in your `allowed_folders` array under `guard_rules.json`.
- **Personality Bleeding (Cognitive Reset):** If you assign a new Sub-Soul to a contact or group but the AI still responds like the old persona, it is reading the old conversation history. **Solution:** Go to the Control Panel, locate the contact, and click the "Brain" (🧠) icon to wipe their short-term memory (`inbox.py delete`).

---

### 🇪🇸 Versión en Español

#### 📋 Requisitos
- **Sistema Operativo:** Linux (Ubuntu/Debian recomendado).
- **Motor Principal:** [Hermes Agent](https://github.com/AndorinaAI/Andorina-WhatsApp-Agent-for-Hermes) instalado.
- **Python:** v3.8 o superior (Sin dependencias externas de pip).
- **Node.js:** Necesario para el WhatsApp Bridge.

#### 🚀 Instalación Rápida
1. Descomprime la carpeta descargada.
2. Haz doble clic en `Andorina-Panel.sh` para iniciar el Panel de Control de Andoriña. Si no abre, abre una terminal en la carpeta y ejecuta `bash ./Andorina-Panel.sh`.
3. Sigue la guía de configuración visual en tu navegador. En el primer login, puedes introducir **la contraseña que tú quieras** para establecerla como definitiva.
4. **Importante:** Al terminar la instalación, **cierra la pestaña actual del navegador**, ya que pertenece a la carpeta temporal. Para usar el panel normalmente, ábrelo desde el nuevo Acceso Directo del escritorio o desde la carpeta de la skill instalada.
5. Consulta [FEATURES.md](./FEATURES.md) para más variables.

#### 🧠 Cómo Funciona la Arquitectura
Andoriña actúa como una **capa Zero-Trust** entre tu IA y WhatsApp:
1. **Webhook Hook:** Cada mensaje entrante es capturado vía `whatsapp.py` y delegado a `webhook.py` idempotentemente, sin duplicados.
2. **Identidad y Orquestador:** `orchestrator_hook.py` resuelve IDs LID de dispositivos de WhatsApp a sus números base usando `lid-mapping-*_reverse.json`, inyectando contexto RAG y personalidades correctamente.
3. **Puertas (Guard):** `input_guard.py` filtra inyecciones de comandos malignos; `tool_guard.py` previene la navegación por fuera de `allowed_folders`.
4. **Ejecución y Resiliencia:** Los procesos corren con límites estrictos de 30s. `agenda.py` mueve 2 minutos las tareas que chocan y las retiene 60 mins para evitar olvidos. `send.py` emula la escritura natural del usuario.

#### 📂 Desglose de Archivos
- `Andorina-Panel.sh`: Interfaz gráfica Web (incluye modo oscuro).
- `GUI/static/monitor.html`: Un visor interactivo de eventos del servidor, puente y agente con desplazamiento automático.
- `setup.py`: Instalador.
- `scripts/security/orchestrator_hook.py`: Enrutador de roles e inyector RAG de contexto.
- `scripts/security/output_pipeline/pipeline.py`: Motor DLP para sanear salidas.
- `scripts/transport/send.py`: Envío de texto y simulación humana.
- `scripts/tools/agenda.py`: Motor Cron con desplazamientos automáticos (`auto-offset`) y eventos recurrentes.
- `scripts/tools/contacts.py`: Edición granular de memoria (`note-section-set`) y sincronizador difuso.
- `scripts/tools/alerts.py`: Establece reglas de rastreo, enviando avisos de privacidad automáticos al contacto monitorizado.
- `scripts/utils/bridge_health.py`: Reiniciador del puente.

#### 🛂 Seguridad y Roles (RBAC)
- **Dueño (Owner):** Acceso total (`all`).
- **Manager:** Restringido a `allowed_folders` y `allowed_chats`.
- **Chatbot:** Por defecto conversacional. Si se definen `allowed_folders`, es promovido dinámicamente a modo Lectura Restringida por `tool_guard.py`.
- **Sub-Souls:** La validación se apoya en reglas de tamaño (>15 caracs) asegurando la inyección prioritaria a grupos.

#### 🏥 Resolución de Problemas Básica
- **"Bridge Offline":** Ejecuta `python3 scripts/utils/bridge_health.py`.
- **"Contacto no encontrado":** Ejecuta `python3 scripts/tools/contacts.py refresh`.
- **Grupo no encontrado:** Revisa grupos con `scripts/tools/contacts.py search`. 
- **Herramienta Bloqueada:** Si la IA dice no poder leer, asegúrate de haber dado permiso de directorio en `allowed_folders` dentro de `guard_rules.json`.
- **Fuga de Personalidad (Reset Cognitivo):** Si cambias la Sub-Soul pero la IA actúa igual, ve al Panel Web, localiza al contacto y pulsa en el icono de "Cerebro" (🧠) para borrar la memoria (ejecuta un `inbox.py delete` seguro).

---
*Developed with &#10084; by Jorge.*
