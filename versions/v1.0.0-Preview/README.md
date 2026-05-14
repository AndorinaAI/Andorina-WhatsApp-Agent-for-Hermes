# <p align="center"><img src="docs/assets/logo.png" alt="Andoriña Logo" height="120"></p>
# <p align="center"><strong>Andoriña — DEBUG TESTING PREVIEW</strong></p>
# <p align="center"><em>The Ultimate WhatsApp Skill for Hermes Agent (Initial Release)</em></p>
# <p align="center"><em>La Skill Definitiva de WhatsApp para el Agente Hermes (Lanzamiento Inicial)</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blueviolet?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/status-DEBUG--TESTING--PREVIEW-red?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/platform-Linux-lightgrey?style=flat-square&logo=linux" alt="Linux">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python" alt="Python">
</p>

<p align="center">
  <strong>Official Website / Sitio Web Oficial:</strong> <a href="https://andorinaai.github.io/Andorina-WhatsApp-Agent-for-Hermes/">andorinaai.github.io/andorina/</a>
</p>

> [!IMPORTANT]
> **🚀 v1.0.0 INITIAL RELEASE: DEBUG TESTING PREVIEW**
> This is the first public version of Andoriña. It features agent-proof refactoring and hardening. Please report any bugs via GitHub Issues.
>
> **🚀 v1.0.0 LANZAMIENTO INICIAL: VISTA PREVIA DE PRUEBAS**
> Esta es la primera versión pública de Andoriña. Cuenta con refactorización y blindaje a prueba de agentes. Por favor, informa de cualquier error a través de las Issues de GitHub.

---

<p align="center">
  <strong>Turn your Hermes agent into a total WhatsApp manager.</strong><br>
  Send messages and files, search contacts, schedule messages, and function as a secure chatbot for third parties.
</p>

<p align="center">
  <strong>Convierte a tu agente Hermes en un gestor total de WhatsApp.</strong><br>
  Envía mensajes y archivos, busca contactos, programa envíos y funciona como un chatbot seguro para terceros.
</p>

> ⚠️ **Currently optimized exclusively for Linux.** Windows and macOS support in development.
> ⚠️ **Optimizado exclusivamente para Linux.** Soporte para Windows y macOS en desarrollo.

---

<p align="center">
  <a href="#english">English</a> | <a href="#español">Español</a>
</p>

---

<h2 align="center">Support</h2>
<p align="center">
  <a href="https://buymeacoffee.com/andorinaai">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=000000" />
  </a>
  <a href="https://www.paypal.com/paypalme/jorge93gf">
    <img src="https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white" />
  </a>
</p>

---

<a name="english"></a>
## 🇬🇧 English Version

### ✨ What can Andoriña do?

| Feature | Description |
|---|---|
| 📤 **Message sending** | Send text to any contact or group by name or number |
| 📁 **File sending** | Upload documents, images, audio, or video from your local folders |
| 🎙️ **Voice notes** | Convert any MP3/WAV into a real voice note with the native WhatsApp player |
| ⏰ **One-Step Agenda** | Simplified 3-argument command for fail-proof scheduling |
| 🤖 **Chatbot Mode** | Allow third parties to interact with Hermes via WhatsApp safely and isolated |
| 🛡️ **Guard (Firewall)** | Blocks prompt injections, data extraction, path traversal, and spam |
| 🧩 **Small Model Ready** | Optimized for 4B-8B models (Qwen, Llama, Mistral) |

### 🚀 Installation

1. Copy the skill folder to your Hermes skills directory:
   ```bash
   cp -r andorina/ ~/.hermes/skills/messaging/andorina/
   ```

2. Run the interactive setup assistant:
   ```bash
   python3 ~/.hermes/skills/messaging/andorina/setup.py
   ```

---

### 💡 Best Practices for Small Models (4B - 8B)

If you are using a local model (Ollama/LM Studio), we highly recommend adding this to your `SOUL.md`:

> "You are the Andoriña engine. WhatsApp = Andoriña. Use the scripts in `~/.hermes/skills/messaging/andorina/scripts/` directly. Never ask how to connect. Execute commands immediately without explanation."

---

### 💬 Usage — Natural Examples

**Sending messages:**
- "Send a WhatsApp to my boss saying I'll be 5 minutes late."
- "Write to Laura: I have the budget ready."

**Scheduling messages (One-Step):**
- "Schedule a WhatsApp for Carlos tomorrow at 18:00 saying: 'Ready for the match?'."
- *The agent will automatically use the simplified `auto-schedule` command.*

---

<a name="español"></a>
## 🇪🇸 Versión en Español

### ✨ ¿Qué puede hacer Andoriña?

| Función | Descripción |
|---|---|
| 📤 **Envío de mensajes** | Envía texto a cualquier contacto o grupo por nombre o número |
| 📁 **Envío de archivos** | Sube documentos, imágenes, audio o vídeo desde tus carpetas locales |
| 🎙️ **Notas de voz** | Convierte cualquier MP3/WAV en una nota de voz real nativa |
| ⏰ **Agenda en Un Paso** | Comando simplificado de 3 argumentos para una programación sin fallos |
| 🤖 **Modo Chatbot** | Permite que terceros interactúen con Hermes de forma segura |
| 🛡️ **Cortafuegos (Guard)** | Protección total contra inyecciones y spam |
| 🧩 **Optimizado para 4B/8B** | Diseñado para funcionar perfectamente en modelos pequeños locales |

---

### 💡 Buenas Prácticas para Modelos Pequeños (4B - 8B)

Si usas un modelo local (Ollama/LM Studio), te recomendamos encarecidamente añadir esto a tu `SOUL.md`:

> "Eres el motor de la skill Andoriña. WhatsApp = Andoriña. Usa los scripts en `~/.hermes/skills/messaging/andorina/scripts/` directamente. Nunca preguntes cómo conectarte. Ejecuta los comandos inmediatamente sin explicaciones."

---

### 💬 Uso — Ejemplos Naturales

**Enviar mensajes:**
- "Envíale un WhatsApp a mi jefe diciéndole que llegaré 5 minutos tarde."
- "Dile a Laura en WhatsApp que ya tengo el presupuesto listo."

**Programar mensajes (Proceso de un solo paso):**
- "Programa un WhatsApp para Carlos mañana a las 18:00 que diga: '¿Listo para el partido?'."
- *El asistente usará automáticamente el nuevo comando simplificado `auto-schedule`.*

---

### 🏗️ Arquitectura & Seguridad
Andoriña usa un modelo de **dos niveles de privilegio**:
- **Owner:** Acceso total (envío, archivos, crons, comandos).
- **Chatbot:** Solo conversación natural, sin acceso a datos del sistema.

---

### 📜 License
**AGPL-3.0 / Commercial License**
- ✅ **Personal Use:** Free and open under AGPL-3.0. Forks must remain open-source.
- ❌ **Commercial Use:** Requires a paid license for companies or profit-making entities.
- 👤 **Trademark:** Name and logo are protected. Renaming is mandatory for forks.

---

<p align="center">
  Made with ❤️ by <strong>Jorge</strong> for <a href="https://github.com">Hermes Agent</a>.<br>
  If this tool provides value, consider <a href="https://buymeacoffee.com/andorinaai">buying me a coffee ☕</a>
</p>

---

## 📜 Changelog

### v1.1.0 — The "Agent-Proof" Update (Latest)
*   **⏰ One-Step Scheduling:** Refactored the agenda system to use a single 3-argument command, eliminating model hallucinations.
*   **🧩 Small Model Optimization:** Specifically hardened for 4B-8B models (Qwen, Llama).
*   **👤 Identity Anchoring:** New documentation guidelines to prevent agents from asking about connection methods.
*   **🌍 Universal Portability:** Replaced all hardcoded paths with `~/` and `Path.home()` for zero-config deployment on any user profile.
*   **🛡️ Guard v2:** Improved protection against data extraction in chatbot mode.
