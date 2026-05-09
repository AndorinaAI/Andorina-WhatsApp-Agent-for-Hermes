# 📖 Andoriña v1.0.2 — Complete User Guide
## 🕊️ Autonomous WhatsApp Manager for Hermes

---

### 🇺🇸 English Version

#### 📋 Requirements
- **Operating System:** Linux (Ubuntu/Debian recommended).
- **Core Engine:** [Hermes Agent](https://github.com/AndorinaAI/Andorina-WhatsApp-Agent-for-Hermes) installed.
- **Python:** v3.8 or higher (No external pip dependencies required).
- **Node.js:** Required for the WhatsApp Bridge.

#### 🚀 Quick Installation
1. Navigate to the version folder.
2. Run the interactive installer:
   ```bash
   bash install.sh
   ```
3. Follow the prompts to configure your phone number, admin access, and optional Google Contacts sync.
4. For a full list of features and environment variables, see [FEATURES.md](./FEATURES.md).

#### 🧠 How it Works
Andoriña acts as a **bridge layer** between your AI Agent and WhatsApp:
1. **Inbox Hook:** Every incoming message is captured and stored locally in `state/inbox.json`.
2. **Security Guard:** Before the AI reads a message, the `guard.py` script checks for prompt injections or unauthorized requests.
3. **Task Execution:** When you give a command, the AI selects the appropriate script from `scripts/`.
4. **Resilient Sending:** Messages are sent through a local HTTP bridge. If the bridge is down, the `bridge_health.py` script automatically attempts a repair.

#### 📂 File Breakdown (The Toolbox)
- `install.sh`: Interactive CLI installer with agent auto-detection.
- `setup.py`: Core configuration engine (sets limits, paths, and hooks).
- `scripts/send.py`: High-speed text delivery with built-in pacing.
- `scripts/files.py`: Universal multimedia engine (Images, Videos, Docs, PTT).
- `scripts/agenda.py`: Crontab-powered scheduling with collision avoidance.
- `scripts/contacts.py`: Fuzzy-search engine for Google Contacts and WA Groups.
- `scripts/guard.py`: The security firewall (Anti-injection/Rate-limiting).
- `scripts/diag.py`: Comprehensive health check for all services.
- `scripts/bridge_health.py`: The auto-repair "medic" for the infrastructure.

#### 🛡️ Anti-Ban & Usage Warning
> [!IMPORTANT]
> **Safety First:** Andoriña implements a **Human Simulation Engine** and **Request Pacing (1.0s delay)** to mimic natural behavior:
> - **Typing Simulation:** The system shows "Typing..." status for a duration proportional to the message length.
> - **Recording Simulation:** For voice notes, it shows "Recording audio..." for 3 seconds before delivery.
> - **Spamming is strictly prohibited.** Using this skill for mass-messaging will lead to your account being banned by Meta.

#### 🏥 Basic Troubleshooting
- **"Bridge Offline":** Run `python3 scripts/bridge_health.py`. It kills zombie processes and restarts the gateway.
- **"Contact not found":** Run `python3 scripts/contacts.py refresh`. This clears the cache and refetches cloud data.
- **Group not found:** Groups are fetched from the live bridge. If the bridge is offline, only groups cached by Hermes are shown. Also, `inbox.py list` only shows groups that have sent at least one message. Use `contacts.py search` to find silent groups.
- **"Permission Denied":** Ensure the scripts have execution permissions: `chmod +x scripts/*.py`.
- **Custom bridge path:** If your `bridge.js` is not at the standard location, set `WHATSAPP_BRIDGE_PATH=/your/path/bridge.js` in your agent's `.env` or export it before running the installer.

---

### 🇪🇸 Versión en Español

#### 📋 Requisitos
- **Sistema Operativo:** Linux (Ubuntu/Debian recomendado).
- **Motor Principal:** [Hermes Agent](https://github.com/AndorinaAI/Andorina-WhatsApp-Agent-for-Hermes) instalado.
- **Python:** v3.8 o superior (Sin dependencias externas de pip).
- **Node.js:** Necesario para el WhatsApp Bridge.

#### 🚀 Instalación Rápida
1. Entra en la carpeta de la versión.
2. Ejecuta el instalador interactivo:
   ```bash
   bash install.sh
   ```
3. Sigue los pasos para configurar tu número, acceso admin y la sincronización opcional con Google Contacts.
4. Para una lista completa de funciones y variables de entorno, consulta [FEATURES.md](./FEATURES.md).

#### 🧠 Cómo Funciona
Andoriña actúa como una **capa intermedia** entre tu Agente de IA y WhatsApp:
1. **Hook de Entrada:** Cada mensaje entrante es capturado y guardado localmente en `state/inbox.json`.
2. **Guardia de Seguridad:** Antes de que la IA lea el mensaje, el script `guard.py` verifica inyecciones de prompt o peticiones no autorizadas.
3. **Ejecución de Tareas:** Cuando das una orden, la IA selecciona el script adecuado de la carpeta `scripts/`.
4. **Envío Resiliente:** Los mensajes salen vía un puente HTTP local. Si el puente falla, `bridge_health.py` intenta repararlo automáticamente.

#### 📂 Desglose de Archivos
- `install.sh`: Instalador interactivo con detección automática de agentes.
- `setup.py`: Motor de configuración (límites, rutas y hooks).
- `scripts/send.py`: Envío de texto con retrasos naturales incorporados.
- `scripts/files.py`: Motor multimedia universal (Imágenes, Vídeos, Docs, PTT).
- `scripts/agenda.py`: Programación mediante Crontab con evasión de colisiones.
- `scripts/contacts.py`: Motor de búsqueda inteligente para Google y Grupos.
- `scripts/guard.py`: El cortafuegos de seguridad (Anti-inyección/Límites).
- `scripts/diag.py`: Diagnóstico completo de salud de todos los servicios.
- `scripts/bridge_health.py`: El "médico" de auto-reparación de la infraestructura.

#### 🛡️ Aviso de Anti-Baneo y Uso
> [!IMPORTANT]
> **Seguridad Ante Todo:** Andoriña implementa un **Motor de Simulación Humana** y **Pacing de Peticiones (1.0s de retraso)**:
> - **Simulación de Escritura:** El sistema muestra "Escribiendo..." durante un tiempo proporcional a la longitud del mensaje.
> - **Simulación de Grabación:** Para notas de voz, muestra "Grabando audio..." durante 3 segundos antes del envío.
> - **El Spam está estrictamente prohibido.** El envío masivo resultará en el baneo de tu cuenta por parte de Meta.

#### 🏥 Resolución de Problemas Básica
- **"Bridge Offline":** Ejecuta `python3 scripts/bridge_health.py`. Limpiará procesos zombies y reiniciará el gateway.
- **"Contacto no encontrado":** Ejecuta `python3 scripts/contacts.py refresh`. Esto limpia la caché y vuelve a sincronizar la nube.
- **Grupo no encontrado:** Los grupos se obtienen en vivo del puente. Si el puente está offline, solo se muestran los grupos cacheados por Hermes. Además, `inbox.py list` solo muestra grupos que hayan enviado al menos un mensaje. Usa `contacts.py search` para encontrar grupos silenciosos.
- **"Permiso Denegado":** Asegúrate de que los scripts tengan permisos de ejecución: `chmod +x scripts/*.py`.
- **Ruta del bridge personalizada:** Si tu `bridge.js` no está en la ubicación estándar, añade `WHATSAPP_BRIDGE_PATH=/tu/ruta/bridge.js` al `.env` de tu agente o expórtalo antes de ejecutar el instalador.

---
*Developed with &#10084; by Jorge.*
