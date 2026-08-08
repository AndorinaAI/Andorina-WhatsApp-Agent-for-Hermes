

<p align="center">
  <strong style="font-size: 2em;">Andoriña — VERSIÓN OFICIAL</strong>
</p>

<p align="center">
  <img src="docs/assets/logo.png" alt="Logotipo de Andoriña" height="120">
</p>

<p align="center">
  <em>Gestor Autónomo de WhatsApp para Hermes (v1.5.2-Beta5)</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.5.2--Beta5-blueviolet?style=flat-square" alt="Versión">
  <img src="https://img.shields.io/badge/status-BETA-orange?style=flat-square" alt="Estado">
  <img src="https://img.shields.io/badge/platform-Linux-lightgrey?style=flat-square&logo=linux" alt="Linux">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python" alt="Python">
</p>

<p align="center">
  <strong>Sitio Web Oficial:</strong> <a href="https://andorinaai.github.io/Andorina-WhatsApp-Agent-for-Hermes/">andorinaai.github.io/</a>
</p>

## 🤝 Únete a la Comunidad

- **Síguenos en X:** [@andorinaAI](https://x.com/andorinaAI)

> [!IMPORTANT]
> **🔧 v1.5.2-Beta5 — VERSIÓN DE CORRECCIÓN DE ERRORES**
> Corregido: Las alertas semánticas de grupo→grupo ahora funcionan correctamente. La causa era que `webhook.py` usaba el JID del miembro individual en lugar del JID del grupo para la coincidencia de origen de alertas.
>
> **🔧 v1.5.2-Beta4 — VERSIÓN DE CORRECCIÓN DE ERRORES**
> Corregido: Coincidencia de sufijos RBAC para roles · Coincidencia de origen de alertas por JID · Coincidencia de sufijos de admin en auto-respuesta · Autodetección de URL webhook multinivel. Mejoras: coincidencia difusa e insensible a acentos en alertas · Banner de estabilidad de webhook · Ayudante JID centralizado.
>
> ---
>
> **🔧 v1.5.2-Beta3 — VERSIÓN DE CORRECCIÓN DE ERRORES**
> Corregido: TUI/CLI bloqueado por RBAC · Puerto de webhooks fijado en 3001 · Notas de contacto sin escribir ni leer · Actualizador sin parchear el SOUL.md. Mejoras: banner i18n (EN/ES), banner visible siempre al cargar, velocidad de scroll reducida.

---

<p align="center">
  <strong>Convierte a Hermes en un gestor autónomo de WhatsApp.</strong><br>
  Toma el control absoluto de tus comunicaciones. Olvídate de teclear: programa envíos, lanza notas de voz, adjunta archivos de tu PC y busca en tu agenda al instante. Tu mensajería, en piloto automático.
</p>

> ⚠️ **Exclusivo para Linux.** Hemos cambiado de rumbo para priorizar a la comunidad y el software libre. Frente a la privatización y el control de las Big Tech, Andoriña se desarrolla ahora exclusivamente para Linux (sin cerrarnos a cambiar de idea en el futuro).

---

<p align="center">
  <a href="#funcionalidades">Funcionalidades</a> | <a href="#instalacion">Instalación</a>
</p>

---

## Soporte

<p align="center">
  <a href="https://buymeacoffee.com/andorinaai">
    <img src="https://img.shields.io/badge/Invítame%20un%20Café-FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=000000" alt="Invítame un Café" />
  </a>
  <a href="https://www.paypal.com/paypalme/j93gf">
    <img src="https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal" />
  </a>
</p>

---

## ✨ Funcionalidades

### ¿Qué puede hacer Andoriña?

| Función | Descripción |
| :--- | :--- |
| 📤 **Envío de mensajes** | Envía texto a cualquier contacto o grupo por nombre o número |
| 📁 **Envío de archivos** | Carga documentos, imágenes, audio o vídeo desde tus carpetas locales |
| 🎙️ **Notas de voz** | Soporte PTT nativo: convierte audio y muestra el estado "Grabando..." |
| 🧩 **Sandbox (V2)** | Ejecuta plugins y juegos aislados en Python con bases de datos locales **[Próximamente]** |
| 📚 **Conocimiento (RAG)** | Sube archivos PDF/TXT para inyectar contexto automáticamente en el LLM |
| 🛡️ **Guard Zero-Trust** | Validación de seguridad vía `input_guard.py` y `tool_guard.py`. Se aplican tiempos de espera y restricciones. |
| 🛂 **Motor RBAC** | Roles granulares (Dueño, Administrador, Chatbot, Bloqueado) con validación de `allowed_folders` |
| 🕵️ **Tubería DLP** | Prevención de pérdida de datos: trunca spam, elimina registros de razonamiento interno, bloquea fugas de API |
| 🧠 **Memoria a Largo Plazo**| Notas permanentes por secciones (`contacts.py note-section-set`) para guardar contexto sobre usuarios |
| 🖥️ **Panel de Control GUI** | Interfaz gráfica completa (modo oscuro/claro) para gestionar RBAC, Sub-Almas, Plugins y un **Monitor en Vivo** |
| ☁️ **Acceso Remoto** | **Túnel Cloudflare** (dominio gratuito o personalizado) para exponer el panel desde cualquier lugar |
| 🔄 **Auto-Actualización** | Actualizador de GitHub con un clic que preserva todos los datos de forma atómica |
| 🤖 **Multi-Agente** | **Aislamiento de Crontab** completo y enrutamiento específico del entorno |
| ⏰ **Protección Anti-Baneo** | **Regulación de Peticiones (retardo de 1.0s)** y **Compensación Automática de Colisiones (2 min)** para programación |
| 📥 **Almacenamiento de Bandeja** | Almacenamiento local idempotente de bandeja de entrada (`inbox.json`) mediante interceptores webhook |
| 🔕 **Ausencia y Silencio** | Silencio por contacto y auto-respondedor global de ausencia con periodos de refrigeración |
| 🔐 **Privacidad Absoluta** | **Procesamiento 100% Local**. Cero telemetría, sin almacenamiento en la nube |
| 📒 **Sincronización Google Cloud** | Sincronización completa OAuth2 con Contactos de Google, **Búsqueda Difusa** y **Mapeo LID** |
| ⚕️ **Autocuración** | Reparación automatizada de infraestructura, verificador de parches (`check_patches.py`) y Motor de Diagnóstico |
| 🧠 **Reinicio Cognitivo** | Borrado quirúrgico de memoria (logs + bandeja) sin romper sesiones de WhatsApp (`inbox.py delete`) |

<a name="instalacion"></a>
### 🚀 Instalación y Documentación

> [!IMPORTANT]
> **Requiere Hermes Agent >= v0.16.0.** Actualiza con `hermes update` antes de instalar. El instalador verifica esto automáticamente y ofrece actualizar si es necesario.

1. **Inicio Rápido:** Descomprime la carpeta descargada y haz doble clic en `Andorina-Panel.sh` (si no se abre, abre una terminal y ejecuta `bash ./Andorina-Panel.sh`). El Panel de Control de Andoriña se abrirá en tu navegador y te guiará visualmente por todo el proceso de instalación.
2. **Primer Inicio de Sesión:** En la pantalla de inicio de sesión, puedes ingresar **cualquier contraseña que desees** para establecerla como tu contraseña maestra.
3. **Post-Instalación:** Una vez completados todos los pasos, **debes cerrar la pestaña actual del navegador** (pertenece a la carpeta temporal de instalación). Abre el panel nuevamente desde el Acceso Directo del Escritorio o desde la carpeta final de la habilidad instalada.
4. **Guía Completa:** Consulta [GUIDE.md](./GUIDE.md) para un desglose completo de requisitos, arquitectura y solución de problemas.
5. **Lista Completa de Funciones:** Consulta [FEATURES.md](./FEATURES.md) para una referencia completa de todas las capacidades, comandos y variables de entorno.

---

### 🛡️ Aviso de Seguridad y Anti-Baneo
Andoriña está diseñada para **asistencia personal**, no para mensajería masiva. 
- **Regulación de Peticiones:** El sistema implementa un **retardo de 1.0s** entre mensajes para evitar la saturación del puente.
- **Simulación Humana:** Soporte nativo para indicadores de estado de **Escribiendo...** y **Grabando audio...** para imitar interacciones naturales.
- **Compensación Automática:** Las tareas programadas que comparten la misma marca de tiempo se desplazan internamente en 2 minutos mediante `agenda.py` para evitar tiempos de espera del LLM y spam de API.

> [!CAUTION]
> **Advertencia de Spam:** El uso de esta habilidad para spam o marketing masivo está estrictamente prohibido y resultará en un ban inmediato de la cuenta por parte de Meta. Los desarrolladores no se hacen responsables de suspensiones de cuenta. Úsalo responsablemente.

---

### 💬 Uso — Ejemplos Naturales

**Enviar mensajes:**
- "Envía un WhatsApp a mi jefe diciendo que llegaré 5 minutos tarde."

**Programar mensajes (Proceso de un solo paso):**
- "Programa un WhatsApp para Carlos mañana a las 18:00 que diga: '¿Listo para el partido?'."
- *El agente utiliza el comando `auto-schedule`, manteniendo la tarea en una ventana de entrega de 60 minutos incluso si la IA responde tarde.*

**Gestión de Información:**
- "Actualiza la nota del perfil de Laura en la sección 'Preferencias' para indicar que es vegana."
- *La IA utiliza `contacts.py note-section-set` para actualizar la memoria de forma segura.*

> [!TIP]
> **Consejo para Envío de Archivos:** Para imágenes, vídeos y documentos complejos, la IA no puede leer ni ver el contenido. ¡Proporciona nombres de archivo exactos o sé extremadamente específico para que el agente los encuentre usando `files.py`!

---

## 🌟 CAPACIDADES Y CARACTERÍSTICAS CLAVE

### 🛡️ Arquitectura Anti-Baneo y Resiliente
- **Regulación y Simulación:** Tiempo de "composición" simulado proporcional a la longitud del mensaje.
- **Evitación de Colisiones:** `agenda.py` desplaza automáticamente las tareas concurrentes en 2 minutos.
- **Puente Autocurativo:** Restaura automáticamente los procesos del puente Qdrant/Node.
- **Webhooks Idempotentes:** `whatsapp.py` parchea estrictamente para eliminar registros duplicados de mensajes entrantes.

### 🛂 Seguridad de Grado Militar (Tubería Zero-Trust)
- **Validación Pre-LLM y de Herramientas:** `input_guard.py` bloquea spam de caracteres específicos, mientras que `tool_guard.py` aplica limitaciones de lectura de directorios (`allowed_folders`) mediante roles de acceso restringido.
- **Tiempo de Espera de Subprocesos de Ejecución:** Los comandos externos ejecutados por el LLM tienen una TTL estricta de 30 segundos para evitar congelar el sistema.
- **Alertas Temáticas Semánticas:** Agrega reglas de escucha permanentes con notificaciones de transparencia mediante `alerts.py`.

### 📒 Contactos Inteligentes e Identidad
- **Resolución LID:** El motor de identidad intercepta correctamente los LID de WhatsApp de forma dinámica, aplicando un analizador heurístico de sufijos (`@g.us` vs `@s.whatsapp.net`) para interacciones fluidas en grupos.
- **Búsqueda Difusa:** `contacts.py` ignora acentos y casos de caracteres para encontrar contactos a través de APIs de Puente, cachés locales e integraciones de Google.

### 🎙️ Multimedia y UI Avanzada
- **Monitor de Servidor en Vivo:** Comprueba fácilmente eventos de ejecución del Puente, Agente y Servidor de forma visual dentro del panel web (`monitor.html`).
- **Soporte de Multimedia:** Resolución nativa de MIME `.heic`, `.opus`, `.xcf` y `.psd` para entregas basadas en documentos.

## 🛠️ LA CAJA DE HERRAMIENTAS

### 📒 Contactos y Grupos
| Script | Comando | Uso |
| :--- | :--- | :--- |
| `tools/contacts.py` | `search "Consulta"` | Búsqueda universal (nombres, números, grupos). |
| `tools/contacts.py` | `note-add` / `note-section-set` | Modifica notas de memoria permanente para un usuario. |
| `tools/contacts.py` | `groups` | Lista todos los grupos de WhatsApp. |
| `tools/contacts.py` | `refresh` | Limpia la caché local y fuerza una sincronización en la nube. |

### ✉️ Mensajería y Archivos
| Script | Comando | Uso |
| :--- | :--- | :--- |
| `transport/send.py` | `message "ID" "Txt"` | Envía un mensaje de texto inmediatamente con regulación. |
| `transport/send.py` | `broadcast "Txt" "IDs"` | Envía mensajes masivos regulados a varios usuarios. |
| `tools/files.py` | `"Ruta" "ID"` | Envía imágenes, vídeos o documentos inmediatamente. |
| `tools/inbox.py` | `list` / `search "Consulta"`| Lista chats recientes / busca en el caché de historial local. |
| `tools/alerts.py` | `add "Origen" "Destino"` | Crea una regla de palabras clave y notifica al destino. |

### 📅 Programación (Agenda)
| Script | Comando | Uso |
| :--- | :--- | :--- |
| `tools/agenda.py` | `auto-schedule "ID" "HORA" "Msj"` | Programación automatizada de textos (manea colisiones). |
| `tools/agenda.py` | `recurring add "ID" "CRON" "Msj"`| Agrega una tarea recurrente de crontab. |
| `tools/agenda.py` | `list` / `remove "ID"` | Lista / Cancela mensajes programados. |

### 🛡️ Seguridad y Sistema
| Script | Comando | Uso |
| :--- | :--- | :--- |
| `Andorina-Panel.sh` | (ninguno) | Abre el Panel de Control GUI completo para Linux Desktop. |
| `utils/admin_cli.py` | `role set "ID" "Rol"` | Asigna un rol RBAC a un usuario. |
| `utils/diag.py` / `bridge_health.py` | (ninguno) | Diagnóstico de salud del sistema y auto-reparación del Puente. |

---

### 📜 Licencia

**AGPL-3.0 / Licencia Comercial**
- ✅ **Uso Personal:** Gratis y abierto bajo AGPL-3.0.
- ❌ **Uso Comercial:** Requiere licencia de pago para empresas.
- 👤 **Marca Registrada:** Nombre y logotipo protegidos.

---

<p align="center">
  Creado con ❤️ por <strong>Jorge</strong> para <a href="https://github.com">Hermes Agent</a>.<br>
  Si esta herramienta aporta valor, considera <a href="https://buymeacoffee.com/andorinaai">invitarme a un café ☕</a>
</p>
