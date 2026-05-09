# 📑 Engineering Memory & Nuclear Audit — Andoriña

This document details the exhaustive hardening, sanitation, and optimization effort performed since the conception of the project.

---

## [1.0.0] - 2026-05-09 (TODAY)
### 🚀 INITIAL RELEASE: "The Agent-Proof Milestone"
Final Nuclear Audit and global hardening.

#### 🇬🇧 English
- **🛡️ Nuclear Hardening:** UTF-8 Shield implementation for binary-safe `stdin` (emojis/special chars support) and Guard v2 Logical Firewall with 37+ detection patterns.
- **🧠 Agent-Proofing:** Refactored `agenda.py` for one-step scheduling to eliminate LLM hallucinations. Identity Anchoring in `SOUL.md`.
- **🩹 Integrity:** Purged corrupted assets, synced legal dual-licensing (AGPL-3.0/Commercial), and finalized the "Zero-Config" installer.

#### 🇪🇸 Español
- **🛡️ Blindaje Nuclear:** Implementación de UTF-8 Shield para `stdin` y Guard v2 con 37+ patrones de detección de inyecciones.
- **🧠 Agent-Proofing:** Refactorización de `agenda.py` para programación en un paso (cero alucinaciones). Anclaje de identidad en `SOUL.md`.
- **🩹 Integridad:** Purga de assets corruptos, sincronización de licencia dual y finalización del instalador "Zero-Config".

---

## [0.9.0] - 2026-05-08
### 🎨 Documentation & Visual Identity
#### 🇬🇧 English
- Created premium visual assets and finalized the bilingual documentation (`index.html` / `index-es.html`).
- Standardized the multi-language README for professional GitHub distribution.
- Integrated donation links (Buy Me a Coffee / PayPal) and official branding.

#### 🇪🇸 Español
- Creación de assets visuales premium y finalización de la web bilingüe.
- Estandarización del README multilenguaje para distribución profesional.
- Integración de enlaces de soporte y branding oficial.

---

## [0.8.0] - 2026-05-07
### 🦅 The Birth of Andoriña (Rebranding & Stabilization)
#### 🇬🇧 English
- Global rebranding from "MensaWhats/Hermes" to **Andoriña**.
- Implementation of the self-healing bridge patch (`patch_bridge.py`) for MIME and PTT support.
- Initial audit of the messaging logic and syntax validation suite.

#### 🇪🇸 Español
- Rebranding global de "MensaWhats" a **Andoriña**.
- Implementación del parche de "puente auto-curativo" para soporte de MIME y notas de voz (PTT).
- Auditoría inicial de la lógica de mensajería y creación de la suite de pruebas.

---

## [0.5.0] - 2026-05-06
### ⏰ Smart Scheduling & Multimedia
#### 🇬🇧 English
- Development of the first `agenda.py` version integrated with system `cron`.
- Implementation of the multimedia engine (`files.py`) with support for documents, images, and video.
- International number normalization logic.

#### 🇪🇸 Español
- Desarrollo de la primera versión de `agenda.py` integrada con `cron`.
- Implementación del motor multimedia (`files.py`) con soporte para documentos, imágenes y vídeo.
- Lógica de normalización de números internacionales.

---

## [0.3.0] - 2026-05-05
### 🔑 Authentication & Foundation
#### 🇬🇧 English
- OAuth2 integration for Google Contacts API (`auth.py`).
- Creation of the asynchronous `hook_inbox.py` for persistent message logging.
- Setup of the core messaging bridge communication logic.

#### 🇪🇸 Español
- Integración de OAuth2 para la API de Google Contacts.
- Creación del hook de entrada asíncrono para el registro persistente de mensajes.
- Configuración de la lógica base de comunicación con el bridge de WhatsApp.

---

## [0.1.0] - 2026-05-04
### 💡 Conception & Security Architecture
#### 🇬🇧 English
- Initial project architecture design.
- **Security Tier Separation:** Defined "Owner" (Full Access) vs "General Contact" (Chatbot Mode) roles.
- Draft of the "Absolute Local Privacy" policy.

#### 🇪🇸 Español
- Diseño inicial de la arquitectura del proyecto.
- **Separación de Niveles de Seguridad:** Definición de roles "Dueño" vs "Contacto General".
- Borrador de la política de "Privacidad Local Absoluta".