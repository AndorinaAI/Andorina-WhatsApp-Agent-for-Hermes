# 🏗️ Andoriña V2.0 — Plan de Refactorización para Plugin Platform de Hermes

> **Fecha:** 2026-09-12
> **Rama:** `dev`
> **Versión actual:** `2.0.0-alpha` (VERSION)
> **Objetivo:** Migrar de skill legacy que parchea Hermes a plugin nativo oficial

---

## 1. RESUMEN DE LA ARQUITECTURA ACTUAL

### 1.1 Modelo de integración con Hermes (V1.x — skill legacy)

```
WhatsApp → Bridge (Node.js, puerto 3000)
  └── whatsapp.py (gateway de Hermes, PARCHADO por patch_whatsapp.py)
       ├── patch_whatsapp.py inyecta:
       │   ├── _resolve_lid_to_phone()  → resolución LID→JID
       │   ├── Inbox Writer              → escribe inbox.json directamente
       │   └── Alert Dispatcher          → llama a webhook.py como subprocess
       └── session_key → Hermes Agent → LLM
            ├── pre_llm_call hook  → orchestrator_hook.py (registrado en config.yaml)
            └── pre_tool_call hook → orchestrator_hook.py
```

**Problema principal:** Andoriña parchea archivos del core de Hermes (`whatsapp.py`, `bridge.js`, `config.yaml`) en lugar de usar el sistema de plugins nativo.

### 1.2 Entrypoints actuales

| Entrypoint | Archivo | Descripción |
|-----------|---------|-------------|
| Instalación desktop | `Andorina-Panel.sh` | Lanza GUI y navegador en `localhost:8888` |
| Instalación headless | `install_cli.py` | Wizard interactivo por terminal |
| Instalación shell | `install.sh` | Auto-detecta entorno y ejecuta `setup.py` |
| Setup wizard | `setup.py` | 9 pasos: idioma, región, Google, rendimiento, deploy, hooks, autostart, parches, SOUL |
| Panel web | `GUI/server.py` | Servidor HTTP stdlib en puerto 8888, API REST |
| Hooks | `orchestrator_hook.py` | Registrado manualmente en `~/.hermes/config.yaml` |
| Actualizador | `andorina_updater.py` | GitHub Releases, re-aplica parches |

### 1.3 Estado del repositorio

| Directorio/Archivo | Contenido | Estado |
|-------------------|-----------|--------|
| `scripts/security/` | RBAC, tool_guard, input_guard, orchestrator, soul_sync, DLP pipeline | ✅ Funcional |
| `scripts/security/memory/` | ABC + Hindsight + Hermes + detector | ✅ V2.0 nuevo |
| `scripts/tools/` | contacts, inbox, agenda, alerts, files | ✅ Funcional |
| `scripts/transport/` | send (bridge HTTP), webhook (inbox + alerts) | ✅ Funcional |
| `scripts/utils/` | jids, safe_json, admin_cli, auth, tunnel, etc. | ✅ Funcional |
| `GUI/` | server.py + static (app.js, index.html, style.css, monitor.html) | ✅ Funcional |
| `plugin.yaml` | Manifiesto V2.0 (capabilities, hooks, env vars, i18n) | ✅ Creado |
| `scripts/security/__init___v2.py` | Docstring huérfano de refactor parcial | ⚠️ A eliminar |
| `patch_bridge.py` | Parchea bridge.js (endpoints, MIME, PTT) | ⚠️ DEPRECATED |
| `patch_whatsapp.py` | Parchea whatsapp.py (LID, Sub-Soul, inbox) | ⚠️ DEPRECATED |
| `check_patches.py` | Verifica que los parches estén aplicados | ⚠️ DEPRECATED |
| `andorina_updater.py` | Self-updater vía GitHub, re-aplica parches | ⚠️ A simplificar |

---

## 2. CÓMO FUNCIONA ACTUALMENTE LA INTEGRACIÓN CON HERMES

### 2.1 Hooks (V1.6)

Los hooks se registran **manualmente** escribiendo en `~/.hermes/config.yaml`:

```yaml
hooks:
  pre_llm_call:
    - command: "python3 'path/to/orchestrator_hook.py'"
  pre_tool_call:
    - command: "python3 'path/to/orchestrator_hook.py'"
```

Esto lo hace `setup.py` → `setup_lib.register_hooks()` durante la instalación.

### 2.2 Channel Prompts (Sub-Souls)

`soul_sync.py` escribe en `config.yaml` bajo `whatsapp.channel_prompts`:

```yaml
whatsapp:
  channel_prompts:
    "34600000000@s.whatsapp.net": "### CUSTOM PERSONALITY..."
    "120363001234@g.us": "### GROUP PERSONALITY..."
```

Esto también lo hace manualmente, no vía API de Hermes.

### 2.3 Parches al core

- **patch_whatsapp.py:** Modifica `gateway/platforms/whatsapp.py` con regex para inyectar:
  - `_resolve_lid_to_phone()` method
  - Sub-Soul injection block (antes de `return MessageEvent`)
  - Andoriña Inbox Writer (escribe `inbox.json` y despacha alertas)

- **patch_bridge.py:** Modifica `scripts/whatsapp-bridge/bridge.js` para añadir:
  - `/health` endpoint
  - `/groups` endpoint
  - `/qr` endpoint
  - MIME expansion (`reqMimetype`)
  - PTT/typing indicators
  - fromMe inbox fix v2

### 2.4 Cómo DEBERÍA funcionar (sistema de plugins de Hermes)

Según la documentación oficial de Hermes:

1. **Plugin discovery:** `PluginManager` busca en `~/.hermes/plugins/`, `./.hermes/plugins/`, y pip entry points
2. **Entry point:** `register(ctx)` — llamado automáticamente al descubrir el plugin
3. **Hooks:** `ctx.register_hook("pre_llm_call", callback)` — nativo, sin modificar `config.yaml`
4. **Tools:** `ctx.register_tool("tool_name", callback)` — el LLM las descubre automáticamente
5. **Platform adapters:** `plugins/platforms/<name>/adapter.py` — extienden plataformas existentes
6. **Plugin catalog:** `plugin-catalog/` con SHA pins, PR review, `removed.yaml`
7. **Manifest:** `plugin.yaml` con `capabilities`, `requires_env`, `optional_env`

**Comparación:**

| Aspecto | V1.6 (actual) | V2.0 (plugin) |
|---------|--------------|---------------|
| Registro de hooks | Escribe `config.yaml` manualmente | `ctx.register_hook()` |
| Sub-Souls | Escribe `channel_prompts` en `config.yaml` | API de `ctx` o `hermes` CLI |
| Instalación | `setup.py` + `install_cli.py` | `hermes plugin install andorina` |
| Parches | Modifica `whatsapp.py` y `bridge.js` | **Eliminados** — funcionalidad nativa |
| GUI | Servidor standalone `:8888` | Integración con `hermes web` |

---

## 3. PROBLEMAS ENCONTRADOS

### 3.1 Arquitectura (🔴 Críticos)

| # | Problema | Archivos afectados |
|---|---------|-------------------|
| A1 | La skill parchea el core de Hermes (`whatsapp.py`, `bridge.js`) | `patch_whatsapp.py`, `patch_bridge.py` |
| A2 | Hooks registrados manualmente en `config.yaml`, no vía `ctx.register_hook()` | `setup_lib.py:469-534`, `setup.py:520-560` |
| A3 | Channel prompts escritos manualmente en `config.yaml` | `soul_sync.py:470-496` |
| A4 | Instalación no usa `hermes plugin install` | `setup.py`, `install_cli.py`, `install.sh` |
| A5 | GUI es servidor standalone, no integrado con `hermes web` | `GUI/server.py` |
| A6 | Entry point es `__name__ == "__main__"` en cada script, no `register(ctx)` | Todos los scripts |

### 3.2 Portabilidad (🟠 Altos)

| # | Problema | Archivos afectados |
|---|---------|-------------------|
| P1 | `fcntl` (POSIX-only) usado en common.py y webhook.py | `common.py`, `webhook.py` |
| P2 | `crontab` directo como scheduling | `agenda.py`, `bridge_health.py` |
| P3 | `systemctl`/`pkill` para reiniciar gateway (Linux-only) | `soul_sync.py` |
| P4 | PATH hardcodeado `/usr/bin:/bin` | `tool_executor.py` (ya corregido parcialmente) |
| P5 | `fuser`, `lsof`, `ss` en Andorina-Panel.sh (Linux-only) | `Andorina-Panel.sh` |
| P6 | `apt-get`, `pacman`, `dnf` para instalar dependencias | `GUI/server.py` |

### 3.3 Seguridad (🟠 Altos)

| # | Problema | Archivos afectados |
|---|---------|-------------------|
| S1 | `tool_guard.py` valida permisos pero el LLM podría intentar ejecutar comandos OS directamente si tiene `send_text` | `tool_guard.py:57-64` |
| S2 | `is_owner` en `tool_guard` otorga acceso total al OS sin restricciones | `tool_guard.py:59-61` |
| S3 | `custom_soul == "_hermes_"` otorga bypass total de seguridad | `tool_guard.py:63` |
| S4 | No hay validación de que `add_note` solo escriba en `NOTES_DIR` | `contacts.py` |
| S5 | Google OAuth credentials hardcodeadas en `auth.py:27-28` | `auth.py` |
| S6 | `DEFAULT_COUNTRY_CODE` leído de `skills/andorina/.env` hardcodeado | `jids.py:23` |

### 3.4 Código legacy / innecesario (🟡 Medios)

| # | Problema | Archivos afectados |
|---|---------|-------------------|
| L1 | `__init___v2.py` — archivo huérfano sin propósito | `scripts/security/__init___v2.py` |
| L2 | `patch_bridge.py`, `patch_whatsapp.py`, `check_patches.py` — parches al core | Raíz del proyecto |
| L3 | `andorina_updater.py` — re-aplica parches que ya no existirán | Raíz del proyecto |
| L4 | `setup.py` — instalador legacy que modifica `config.yaml` | Raíz del proyecto |
| L5 | `install.sh` — wrapper shell que llama a `setup.py` | Raíz del proyecto |
| L6 | `FEATURES.md`, `GUIDE.md` — referencias a `v1.5.2-Beta5` | Raíz del proyecto |
| L7 | `README.md` — badges de `v1.5.2-Beta5` | Raíz del proyecto |
| L8 | `SKILL.md` — referencias a `v1.5.2` | Raíz del proyecto |
| L9 | `revision-plan.md` — plan de auditoría V1.6 ya ejecutado | Raíz del proyecto |
| L10 | Versiones antiguas en `versions/` — 18 versiones legacy (~300MB) | `versions/` |

### 3.5 Documentación (🟡 Medios)

| # | Problema | Archivos afectados |
|---|---------|-------------------|
| D1 | `ARCHITECTURE.md` describe V2.0 pero el código aún es V1.6 | `ARCHITECTURE.md` |
| D2 | `MIGRATION.md` menciona `hermes plugin install` que no funciona aún | `MIGRATION.md` |
| D3 | `CHANGELOG.md` no tiene entrada `v2.0.0-alpha` completa | `CHANGELOG.md` |
| D4 | `plugin.yaml` declara `kind: tool` pero el adapter está en `scripts/security/memory/` | `plugin.yaml` |
| D5 | Mix de español/inglés en docstrings y comentarios | ~30 archivos |

---

## 4. PLAN DE REFACTORIZACIÓN POR FASES

### FASE 1 — Limpieza y preparación

**Objetivo:** Eliminar archivos legacy, normalizar idioma, preparar estructura.

| # | Cambio | Motivo | Archivos | Riesgo |
|---|--------|--------|----------|--------|
| F1.1 | Eliminar `scripts/security/__init___v2.py` | Archivo huérfano sin imports ni uso | `__init___v2.py` | Bajo |
| F1.2 | Marcar `patch_bridge.py`, `patch_whatsapp.py`, `check_patches.py` como deprecated con `sys.exit(0)` | Ya no se necesitan en V2.0 | 3 archivos | Bajo |
| F1.3 | Simplificar `andorina_updater.py` — eliminar pasos de re-aplicación de parches | Los parches ya no existen | `andorina_updater.py` | Medio |
| F1.4 | Traducir docstrings español→inglés en `memory/__init__.py`, `detector.py`, `adapter.py`, `common.py`, `install_cli.py`, `setup.py` | Requisito del plugin catalog de Hermes | 6 archivos | Bajo |
| F1.5 | Eliminar `state/` del repo (está en `.gitignore`) | No debe comitearse estado de runtime | `.gitignore` ya lo cubre | Bajo |
| F1.6 | Eliminar `versions/` del repo activo (mover a release archive) | 18 versiones legacy, ~300MB | `versions/` | Bajo |
| F1.7 | Actualizar `VERSION` a `2.0.0-alpha` y `CHANGELOG.md` con entrada completa | Documentar el estado actual | `VERSION`, `CHANGELOG.md` | Bajo |

### FASE 2 — Integración con el sistema de plugins de Hermes

**Objetivo:** Hacer que Andoriña se comporte como un plugin nativo de Hermes.

| # | Cambio | Motivo | Archivos | Riesgo |
|---|--------|--------|----------|--------|
| F2.1 | Crear `register(ctx)` en el entry point del plugin | Requisito de `PluginManager` | `__init__.py` (raíz del plugin) | Crítico |
| F2.2 | Mover hooks de `config.yaml` a `ctx.register_hook()` en `register(ctx)` | No modificar archivos core | `orchestrator_hook.py`, `__init__.py` | Crítico |
| F2.3 | Mover `channel_prompts` de `config.yaml` a `ctx.set_state()` o API nativa | No modificar `config.yaml` | `soul_sync.py` | Alto |
| F2.4 | Registrar tools vía `ctx.register_tool()` en lugar de ejecutarlas como subprocess | El LLM las descubre automáticamente | `adapter.py`, `__init__.py` | Alto |
| F2.5 | Eliminar `setup_lib.register_hooks()` — ya no escribe en `config.yaml` | Migrado a `ctx.register_hook()` | `setup_lib.py` | Medio |
| F2.6 | Actualizar `plugin.yaml` con `kind: tool` correcto y capabilities verificadas | Validación del plugin catalog | `plugin.yaml` | Medio |

### FASE 3 — Migración de herramientas a APIs nativas

**Objetivo:** Reemplazar dependencias de subprocess/system por APIs nativas de Hermes.

| # | Cambio | Motivo | Archivos | Riesgo |
|---|--------|--------|----------|--------|
| F3.1 | Reemplazar `crontab` por `hermes cron` nativo en agenda.py | Multi-OS, más fiable | `agenda.py` | Alto |
| F3.2 | Reemplazar `fcntl` por `filelock` (ya en requirements.txt) | Multi-OS locking | `common.py`, `webhook.py` | Medio |
| F3.3 | Reemplazar `systemctl`/`pkill` por `hermes gateway restart` | Multi-OS, API nativa | `soul_sync.py` | Medio |
| F3.4 | Hacer `tool_executor.py` multi-OS (PATH sin hardcodear) | Windows/macOS | `tool_executor.py` | Bajo |
| F3.5 | Hacer `input_guard.py` multi-OS (patrones Windows + Linux) | Windows/macOS | `input_guard.py` | Bajo |
| F3.6 | Hacer `files.py` multi-OS (`blocked_prefixes` Windows + Linux) | Windows/macOS | `files.py` | Bajo |
| F3.7 | Reemplazar `fuser`/`lsof`/`ss` en Andorina-Panel.sh por `hermes web` | El panel se integra con Hermes | `Andorina-Panel.sh` | Alto |

### FASE 4 — Configuración y estado

**Objetivo:** Centralizar configuración en `plugin.yaml` y estado en APIs de Hermes.

| # | Cambio | Motivo | Archivos | Riesgo |
|---|--------|--------|----------|--------|
| F4.1 | Mover `.env` vars a `plugin.yaml` `requires_env`/`optional_env` | Hermes las gestiona | `plugin.yaml`, `setup.py`, `common.py` | Alto |
| F4.2 | Usar `ctx.get_state()`/`ctx.set_state()` para estado del plugin | API nativa de Hermes | `orchestrator_hook.py`, `admin_cli.py` | Alto |
| F4.3 | Mantener archivos JSON locales como caché (compatibilidad) | Migración gradual | `safe_json.py`, `rbac.py` | Medio |
| F4.4 | Unificar path resolution: `plugins/andorina` antes que `skills/andorina` | Compatibilidad V1→V2 | `common.py`, `jids.py` | Medio |

### FASE 5 — Seguridad

**Objetivo:** Cerrar brechas de seguridad identificadas.

| # | Cambio | Motivo | Archivos | Riesgo |
|---|--------|--------|----------|--------|
| F5.1 | Eliminar bypass `custom_soul == "_hermes_"` en tool_guard | Backdoor de seguridad | `tool_guard.py:63` | Crítico |
| F5.2 | Restringir `is_owner` OS access en tool_guard a comandos whitelisteados | Principio de mínimo privilegio | `tool_guard.py:59-61` | Crítico |
| F5.3 | Añadir validación de path en `contacts.py` para `note-add` (solo NOTES_DIR) | Path traversal prevention | `contacts.py` | Alto |
| F5.4 | Mover Google OAuth credentials de hardcode a `.env.example` | Seguridad de credenciales | `auth.py:27-28` | Alto |
| F5.5 | Sanitizar `jids.py` path resolution para usar `plugins/` dinámico | No hardcodear `skills/` | `jids.py:23` | Medio |

### FASE 6 — GUI

**Objetivo:** Integrar el panel con `hermes web` o mantener standalone documentado.

| # | Cambio | Motivo | Archivos | Riesgo |
|---|--------|--------|----------|--------|
| F6.1 | Documentar que la GUI es standalone (no integrada con `hermes web`) | Transparencia | `ARCHITECTURE.md`, `README.md` | Bajo |
| F6.2 | Añadir flag `--plugin-mode` a `GUI/server.py` para rutas de plugin | Compatibilidad forward | `GUI/server.py` | Bajo |
| F6.3 | Actualizar `Andorina-Panel.sh` para detectar entorno plugin vs skill | Dual boot V1/V2 | `Andorina-Panel.sh` | Bajo |

### FASE 7 — Documentación

**Objetivo:** Actualizar toda la documentación para reflejar V2.0.

| # | Cambio | Motivo | Archivos | Riesgo |
|---|--------|--------|----------|--------|
| F7.1 | Actualizar `README.md` — badges `v2.0.0-alpha`, quitar referencias V1.5 | Primer contacto del usuario | `README.md` | Bajo |
| F7.2 | Actualizar `FEATURES.md` — versión `v2.0.0-alpha`, añadir plugin features | Referencia de funcionalidades | `FEATURES.md` | Bajo |
| F7.3 | Actualizar `GUIDE.md` — comandos `hermes plugin *` en lugar de `setup.py` | Guía de usuario | `GUIDE.md` | Bajo |
| F7.4 | Actualizar `SKILL.md` — modo plugin (ya no "terminal only") | Prompt del agente | `SKILL.md` | Medio |
| F7.5 | Actualizar `ARCHITECTURE.md` — reflejar estado real V2.0-alpha | Documentación técnica | `ARCHITECTURE.md` | Bajo |
| F7.6 | Eliminar o archivar `revision-plan.md` — ya ejecutado | Limpieza | `revision-plan.md` | Bajo |
| F7.7 | Actualizar `MIGRATION.md` — instrucciones verificadas | Migración V1→V2 | `MIGRATION.md` | Bajo |

### FASE 8 — Tests y CI/CD

**Objetivo:** Asegurar calidad con tests automatizados.

| # | Cambio | Motivo | Archivos | Riesgo |
|---|--------|--------|----------|--------|
| F8.1 | Mover `test_sandbox.py` y `test_edge_cases.py` a `tests/` con pytest | Estructura estándar | `tests/` | Bajo |
| F8.2 | Añadir tests para `memory/` backend (Hindsight, Hermes, Noop) | Cobertura del nuevo módulo | `tests/test_memory.py` | Bajo |
| F8.3 | Añadir tests de integración con `register(ctx)` mock | Validar plugin API | `tests/test_plugin.py` | Medio |
| F8.4 | Crear `tests/conftest.py` con fixtures (temp dirs, mock Hermes ctx) | Reutilización de fixtures | `tests/conftest.py` | Bajo |
| F8.5 | Añadir CI/CD con GitHub Actions (lint + test + build) | Integración continua | `.github/workflows/ci.yml` | Bajo |

### FASE 9 — Auditoría final

**Objetivo:** Verificar que todo funciona antes del release.

| # | Cambio | Motivo | Archivos | Riesgo |
|---|--------|--------|----------|--------|
| F9.1 | Ejecutar `test_sandbox.py` completo (90 tests) | Regresión | Todos | Bajo |
| F9.2 | Ejecutar `test_edge_cases.py` (78 tests) | Casos límite | Todos | Bajo |
| F9.3 | Verificar compilación de todos los `.py` | Sintaxis | Todos | Bajo |
| F9.4 | Verificar que `plugin.yaml` es válido según schema de Hermes | Catálogo | `plugin.yaml` | Medio |
| F9.5 | Verificar que no quedan imports de `skills/` hardcodeados | Migración paths | Todos | Bajo |
| F9.6 | Verificar que `register(ctx)` es llamado correctamente | Entry point | `__init__.py` | Crítico |

---

## 5. ORDEN RECOMENDADO DE IMPLEMENTACIÓN

```
F1 (Limpieza) → F2 (Plugin) → F3 (APIs nativas) → F4 (Config) → F5 (Seguridad) → F6 (GUI) → F7 (Docs) → F8 (Tests) → F9 (Auditoría)
```

**Dependencias críticas:**
- F2.1-F2.4 deben hacerse juntas (el entry point `register(ctx)` necesita hooks y tools)
- F3.1-F3.3 dependen de F2 (las APIs nativas de Hermes están disponibles en el contexto del plugin)
- F5.1-F5.2 son independientes y pueden hacerse en cualquier momento
- F7 depende de F1-F6 (la documentación refleja el estado final)

---

## 6. RIESGOS

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|------------|---------|------------|
| `hermes plugin install` no funciona como se espera | Media | Alto | Mantener `setup.py` como fallback durante la transición |
| `ctx.register_hook()` no soporta los mismos hooks que `config.yaml` | Baja | Crítico | Verificar documentación de Hermes antes de migrar |
| `channel_prompts` no tiene equivalente en `ctx` API | Media | Alto | Mantener `soul_sync.py` escribiendo `config.yaml` como fallback |
| Romper compatibilidad con instalaciones V1.x existentes | Alta | Crítico | Path resolution dual (`plugins/` → `skills/` fallback) |
| El plugin catalog rechaza el plugin por issues de formato | Media | Alto | Validar `plugin.yaml` contra schema antes de enviar PR |

---

## 7. ARCHIVOS QUE REQUIEREN CAMBIOS

### Modificar (35 archivos)

`__init__.py` (nuevo en raíz), `plugin.yaml`, `scripts/security/memory/__init__.py`, `scripts/security/memory/detector.py`, `scripts/security/memory/adapter.py`, `scripts/common.py`, `scripts/security/orchestrator_hook.py`, `scripts/security/orchestrator.py`, `scripts/security/soul_sync.py`, `scripts/security/tool_guard.py`, `scripts/security/tool_executor.py`, `scripts/security/input_guard.py`, `scripts/security/rbac.py`, `scripts/tools/agenda.py`, `scripts/tools/files.py`, `scripts/tools/contacts.py`, `scripts/transport/webhook.py`, `scripts/utils/jids.py`, `scripts/utils/auth.py`, `setup_lib.py`, `setup.py`, `install_cli.py`, `install.sh`, `Andorina-Panel.sh`, `andorina_updater.py`, `GUI/server.py`, `ARCHITECTURE.md`, `README.md`, `FEATURES.md`, `GUIDE.md`, `SKILL.md`, `MIGRATION.md`, `CHANGELOG.md`, `VERSION`, `developer_guide.md`

### Eliminar o archivar (7 archivos)

`scripts/security/__init___v2.py`, `patch_bridge.py`, `patch_whatsapp.py`, `check_patches.py`, `revision-plan.md`, `state/` (ya en `.gitignore`), `versions/` (mover a release archive)

### NO modificar (20 archivos)

`scripts/security/output_pipeline/*`, `scripts/security/plugin_router.py`, `scripts/security/sec_types.py`, `scripts/security/knowledge_retrieval.py`, `scripts/tools/alerts.py`, `scripts/tools/inbox.py`, `scripts/tools/plugin_event_loop.py`, `scripts/transport/send.py`, `scripts/utils/safe_json.py`, `scripts/utils/admin_cli.py`, `scripts/utils/bridge_health.py`, `scripts/utils/diag.py`, `scripts/utils/tunnel.py`, `scripts/utils/wipe_logs.py`, `scripts/utils/plugin_sdk.py`, `scripts/utils/setup_autostart.py`, `GUI/static/*`, `tests/*`, `.env.example`, `.gitignore`, docs legales (`LICENSE.md`, `TRADEMARK.md`, `CLA.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`)

---

## 8. PUNTOS NO VERIFICADOS (UNVERIFIED)

| # | Punto | Razón |
|---|-------|-------|
| UV1 | Si `hermes plugin install` funciona con `kind: tool` plugins | No se pudo probar — requiere Hermes >= 0.19 instalado |
| UV2 | Si `ctx.register_hook("channel_prompt", ...)` existe como API | La doc de Hermes menciona `channel_prompts` en `config.yaml` pero no en `ctx` |
| UV3 | Si el plugin catalog acepta plugins que extienden plataformas existentes (WhatsApp) | La política de admission requiere "owner-or-major-contributor submissions" |
| UV4 | Si `hermes web` tiene API para incrustar paneles de plugins | No se encontró documentación específica |
| UV5 | Compatibilidad del adapter.py con el sistema de imports de Hermes | El path `scripts/security/memory/adapter.py` puede no ser el esperado por `PluginManager` |

---

*Plan generado tras auditoría completa del repositorio — 2026-09-12*
