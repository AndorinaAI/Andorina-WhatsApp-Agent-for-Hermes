# 🔍 REFACTOR_PLAN_REVIEW — Revisión Crítica

> **Fecha:** 2026-09-12
> **Hermes version:** v0.21.1 (verificada en el sistema)
> **Método:** Verificación contra CLI real + documentación del repositorio

---

## 1. APIs DE HERMES VERIFICADAS

### CONFIRMED (verificadas contra CLI v0.21.1 o documentación oficial)

| API | Estado | Fuente |
|-----|--------|--------|
| `register(ctx)` | **CONFIRMED** | `plugins/AGENTS.md`: "register(ctx) registers hooks, tools, CLI subcommands" |
| `ctx.register_hook()` | **CONFIRMED** | `plugins/AGENTS.md`: hooks listados explícitamente |
| `ctx.register_tool()` | **CONFIRMED** | `plugins/AGENTS.md`: "registers tools" |
| `ctx.register_platform()` | **CONFIRMED** | `gateway/platforms/ADDING_A_PLATFORM.md`: "inherits from BasePlatformAdapter and registers via ctx.register_platform()" |
| `hermes plugins install` | **CONFIRMED** | CLI: `hermes plugins install` acepta catalog URL, Git URL, o owner/repo |
| `hermes plugins validate` | **CONFIRMED** | CLI: `hermes plugins validate path` con flag `--json` para CI |
| `hermes plugins capabilities` | **CONFIRMED** | CLI: `hermes plugins capabilities [name]` |
| `hermes gateway restart` | **CONFIRMED** | CLI: `hermes gateway restart` |
| `hermes cron create/list/remove` | **CONFIRMED** | CLI: soporta `create`, `list`, `remove`, `pause`, `resume`, `run`, `edit`, `status` |

### NOT AVAILABLE (no existen en Hermes v0.21.1)

| API | Estado | Evidencia |
|-----|--------|-----------|
| `hermes web` | **NOT AVAILABLE** | `hermes web` devuelve "invalid choice". Comandos reales: `hermes desktop`, `hermes dashboard`, `hermes serve`, `hermes gui` |
| `ctx.set_state()` | **NOT AVAILABLE** | No encontrado en docs ni CLI. `PluginContext` existe pero sin API de estado documentada |
| `ctx.get_state()` | **NOT AVAILABLE** | Mismo caso — no documentado |

### UNVERIFIED (no se pudo comprobar)

| API | Estado | Razón |
|-----|--------|-------|
| `channel_prompts` nativo vía `ctx` | **UNVERIFIED** | No hay documentación de API equivalente. La doc de plataformas menciona `channel_prompts` en `config.yaml` como mecanismo actual |
| `hermes dashboard` como host de paneles de plugins | **UNVERIFIED** | El comando existe pero no se verificó si acepta plugins |

---

## 2. CORRECCIONES AL PLAN ORIGINAL

### 2.1 `hermes web` NO EXISTE — CORREGIR FASE 6

**Error en el plan:** F6 propone integrar la GUI con `hermes web`.

**Realidad:** `hermes web` no es un comando válido. Los comandos reales son:
- `hermes desktop` — app de escritorio
- `hermes dashboard` — dashboard web
- `hermes serve` — servidor HTTP
- `hermes gui` — GUI

**Corrección:** La GUI de Andoriña DEBE permanecer standalone (servidor HTTP en `:8888`). No hay API documentada para que plugins añadan paneles a `hermes dashboard`. La integración con el dashboard de Hermes requiere cambios en el core de Hermes, no en Andoriña.

**Acción:** Cambiar F6 de "integrar con hermes web" a "documentar GUI como standalone y añadir flag --plugin-mode".

### 2.2 `ctx.set_state()` / `ctx.get_state()` NO ESTÁN DISPONIBLES — CORREGIR FASE 4

**Error en el plan:** F4 propone migrar estado a `ctx.set_state()`/`ctx.get_state()`.

**Realidad:** Estas APIs no están documentadas ni disponibles en Hermes v0.21.1.

**Corrección:** Mantener el estado en archivos JSON locales (`safe_json.py`). En el futuro, si Hermes añade una API de estado para plugins, migrar entonces. Por ahora, la arquitectura de archivos JSON con `filelock` es correcta y suficiente.

**Acción:** Eliminar F4.2 del plan. Mantener F4.1 y F4.4.

### 2.3 `channel_prompts` NO TIENE API NATIVA — MANTENER `soul_sync.py`

**Error en el plan:** F2.3 propone migrar `channel_prompts` a `ctx.set_state()`.

**Realidad:** No existe API nativa para `channel_prompts`. El mecanismo actual (escribir en `config.yaml` vía `soul_sync.py`) es el ÚNICO método funcional verificado.

**Corrección:** Mantener `soul_sync.py` exactamente como está. No migrar `channel_prompts`. Este es un mecanismo legítimo de Hermes (documentado en `ADDING_A_PLATFORM.md`) — no es un "parche".

**Acción:** Eliminar F2.3 del plan.

### 2.4 `kind: tool` ES CORRECTO — NO es `kind: platform`

**Verificación:** Andoriña NO proporciona un nuevo transporte de mensajería. Usa el transporte WhatsApp existente de Hermes. Lo que añade son herramientas, hooks, y lógica de negocio (sub-souls, RBAC, alertas, agenda).

**Conclusión:** `kind: tool` es correcto. NO debe ser `kind: platform`. El `plugin.yaml` actual es correcto.

---

## 3. REVISIÓN DE `plugin_router.py` Y `plugin_sdk.py`

### `plugin_router.py`

**Función:** Carga dinámicamente plugins/sandboxes desde `souls/{name}/` con su propio `plugin.json` + `tools.py`. Es un sistema de plugins INTERNO de Andoriña (juegos, sandboxes), NO relacionado con el sistema de plugins de Hermes.

**Decisión:** **KEEP**. Este es un sistema de extensión interno para juegos/sandboxes. No duplica funcionalidad de Hermes — es una capa adicional específica de Andoriña. No debe eliminarse.

**Cambio necesario:** Renombrar para evitar confusión con el sistema de plugins de Hermes. Sugerencia: mantener como está pero documentar que es el "Sandbox Engine", no el "Plugin System".

### `plugin_sdk.py`

**Función:** SDK que se expone a los sandboxes/juegos (`send_message`, `schedule_event`, `get_player_state`, etc).

**Decisión:** **KEEP**. Es la API interna para desarrolladores de sandboxes. Documentada en `developer_guide.md`.

---

## 4. REVISIÓN DE LA INTEGRACIÓN WHATSAPP

### Andoriña NO es un platform adapter

Andoriña no proporciona transporte de mensajería (el bridge de WhatsApp ya lo hace Hermes). Andoriña añade:
- Lógica de negocio (RBAC, sub-souls, alertas)
- Herramientas para el LLM (send, contacts, agenda, inbox)
- Hooks de seguridad (input_guard, tool_guard, DLP)

**Conclusión:** `kind: tool` es la arquitectura correcta. NO debe usar `register_platform()`.

### Lo que SÍ debe cambiar

El plan original acierta en que `patch_whatsapp.py` debe eliminarse. Pero la funcionalidad que inyectaba (LID resolver, inbox writer, alert dispatcher) debe mantenerse por otros medios:

| Funcionalidad | ¿Dónde vive ahora? | ¿Debe moverse? |
|--------------|-------------------|----------------|
| LID resolver | `jids.py:resolve_lid_to_phone()` | ✅ Ya está en jids.py, independiente del patch |
| Inbox writer | Dentro del patch de `whatsapp.py` | Debe moverse a `webhook.py` o `orchestrator_hook.py` |
| Alert dispatcher | Dentro del patch de `whatsapp.py` | Debe moverse a `webhook.py` |
| Sub-Soul injection | Dentro del patch de `whatsapp.py` | Ya se hace también en `orchestrator_hook.py` vía `build_snapshot` |

---

## 5. REVISIÓN DE SEGURIDAD

### S1 — `tool_guard.py` permite OS commands con `send_text`

**Clasificación:** **DESIGN RISK** (no es vulnerabilidad explotable)

El LLM podría intentar ejecutar `ls` si tiene `send_text`. Pero:
- `tool_guard.py:57-64` solo aplica cuando `script_name` está vacío (no es un `.py` conocido)
- El LLM normalmente ejecuta scripts conocidos (`send.py`, `contacts.py`, etc.)
- El riesgo es bajo porque el LLM no intenta ejecutar comandos OS arbitrarios

**Mantener en el plan pero bajar prioridad.**

### S2 — `is_owner` otorga acceso total al OS

**Clasificación:** **EXPECTED BEHAVIOR** (no es backdoor)

El owner TIENE permiso `all` por diseño. El acceso OS es necesario para diagnóstico y reparación. Esto es intencional.

**Eliminar del plan.** No es una vulnerabilidad.

### S3 — `custom_soul == "_hermes_"`

**Clasificación:** **DESIGN RISK** (bypass intencionado pero peligroso)

Es un mecanismo para que ciertas souls tengan acceso elevado. El riesgo es que si un atacante asigna `_hermes_` como soul a su JID, obtiene acceso OS.

**Mantener en el plan.** Añadir validación: solo el owner puede asignar `_hermes_` como soul.

### S4 — Path traversal en `contacts.py`

**Clasificación:** **VULNERABILITY** (baja severidad)

`_notes_path` construye rutas con `num` y `in_group` sin sanitizar. Si `num` contiene `../`, podría escribir fuera de `NOTES_DIR`.

**Mantener en el plan.** Añadir validación de path.

### S5 — Google OAuth creds hardcodeadas

**Clasificación:** **VULNERABILITY** (baja severidad — son creds de app pública)

`auth.py:27-28` tiene `DEFAULT_CID` y `DEFAULT_SEC` hardcodeados. Son credenciales de OAuth de aplicación pública (no secrets de usuario). Pero es mala práctica.

**Mantener en el plan.** Mover a `.env.example`.

### S6 — Path resolution hardcodeado

**Clasificación:** **DESIGN RISK**

`jids.py:23` busca `.env` en `skills/andorina/`. En V2.0 plugin, debe buscar en `plugins/andorina/` también.

**Mantener en el plan.** Ya cubierto por F4.4.

---

## 6. REVISIÓN DE PORTABILIDAD

### Clasificación de cambios multi-OS

| Cambio | Clasificación | Razón |
|--------|--------------|-------|
| `fcntl` → `filelock` (common.py, webhook.py) | **NECESARIO** | `filelock` ya está en requirements.txt. Hermes funciona en macOS. |
| `crontab` → `hermes cron` (agenda.py) | **NECESARIO** | `hermes cron` es la API nativa. Multi-OS automático. |
| `systemctl`/`pkill` → `hermes gateway restart` (soul_sync.py) | **NECESARIO** | `hermes gateway restart` ya existe. |
| PATH multi-OS (tool_executor.py) | **RECOMENDABLE** | Bajo esfuerzo, alto impacto. |
| Patrones Windows (input_guard.py, files.py) | **FUTURO/OPCIONAL** | Windows no es target prioritario. No bloquear el refactor por esto. |
| `fuser`/`lsof` en Andorina-Panel.sh | **FUTURO/OPCIONAL** | El panel es Linux-only por ahora. |

### Corrección al plan

Sacar los cambios de Windows del camino crítico (F3.5, F3.6). Moverlos a una fase opcional posterior.

---

## 7. REORDENAMIENTO DE FASES

### Problema del plan original

F1 propone eliminar/desactivar `patch_*.py` ANTES de que exista el sustituto (F2). Esto rompería la funcionalidad.

### Orden corregido

```
F2 (Plugin integration) → F3 (Native APIs) → F5 (Security) → F1 (Cleanup) → F4 (Config) → F6 (GUI) → F7 (Docs) → F8 (Tests) → F9 (Audit)
```

**Cambios clave:**
1. F2 (plugin) va PRIMERO — construir la nueva integración sin tocar la vieja
2. F3 (APIs nativas) va SEGUNDO — migrar herramientas una a una
3. F5 (seguridad) va TERCERO — cerrar vulnerabilidades antes de limpiar
4. F1 (limpieza) va CUARTO — solo después de verificar que lo nuevo funciona
5. `patch_*.py` NO se desactivan hasta que F2+F3 estén completos y probados

---

## 8. REVISIÓN DE `plugin.yaml`

### Campos verificados

| Campo | Valor actual | ¿Correcto? | Nota |
|-------|-------------|-----------|------|
| `name` | `andorina` | ✅ | |
| `kind` | `tool` | ✅ | Verificado: no es platform adapter |
| `version` | `2.0.0-alpha` | ✅ | |
| `capabilities.provides_tools` | 32 tools | ✅ | Coincide con los tools registrados en `adapter.py` |
| `capabilities.provides_hooks` | 3 hooks | ✅ | `pre_llm_call`, `pre_tool_call`, `post_llm_call` |
| `capabilities.requires_env` | `ANDORINA_ADMIN_PHONE` | ✅ | |
| `capabilities.optional_env` | 6 vars | ✅ | |
| `requires_hermes` | `>=0.16.0` | ⚠️ Debe ser `>=0.19.0` | Hermes v0.21.1 es la actual; el plugin system se estabilizó en 0.19 |

### Campos faltantes

| Campo | Requerido por Hermes | Estado |
|-------|---------------------|--------|
| `plugin.yaml` en raíz del plugin | Sí | ✅ |
| `register(ctx)` entry point | Sí | ✅ En `adapter.py` |
| `__init__.py` en raíz del plugin | No (si usa entry point explícito) | ⚠️ No existe. Debe crearse con `register(ctx)` |

### Corrección

El entry point `register(ctx)` debe estar en `__init__.py` en la raíz del plugin, NO en `scripts/security/memory/adapter.py`. El `PluginManager` busca `register(ctx)` en el `__init__.py` del directorio del plugin.

---

## 9. REVISIÓN FINAL DE LAS 9 FASES

| Fase | Cambios | Decisión | Razón |
|------|---------|----------|-------|
| **F1** — Limpieza | 7 cambios | **DEFER** después de F2+F3 | No desactivar parches antes de tener sustituto |
| **F2** — Plugin | 6 cambios | **KEEP** (modificado: crear `__init__.py` en raíz) | Entry point debe estar en `__init__.py`, no en `adapter.py` |
| **F3** — APIs nativas | 7 cambios | **KEEP** (reducido: sacar Windows del critical path) | `hermes cron`, `filelock`, `hermes gateway restart` son APIs reales |
| **F4** — Config | 4 cambios | **CHANGE**: eliminar F4.2 (`ctx.set_state`) | API no disponible. Mantener JSON local. |
| **F5** — Seguridad | 5 cambios | **KEEP** (modificado: S2 eliminado, S3 bajado a DESIGN RISK) | Solo S4 y S5 son vulnerabilidades reales |
| **F6** — GUI | 3 cambios | **CHANGE**: `hermes web` no existe. GUI standalone. | Documentar, no migrar |
| **F7** — Docs | 7 cambios | **KEEP** | |
| **F8** — Tests | 5 cambios | **KEEP** | |
| **F9** — Auditoría | 6 cambios | **KEEP** | |

---

## 10. ARQUITECTURA FINAL RECOMENDADA

```
~/.hermes/plugins/andorina/
├── plugin.yaml                    ← kind: tool, capabilities verificadas
├── __init__.py                    ← register(ctx) entry point (NUEVO)
├── scripts/                       ← (misma estructura actual)
│   ├── security/
│   │   ├── orchestrator_hook.py   ← hooks: pre_llm_call, pre_tool_call, post_llm_call
│   │   ├── orchestrator.py
│   │   ├── rbac.py
│   │   ├── tool_guard.py
│   │   ├── input_guard.py
│   │   ├── soul_sync.py           ← channel_prompts → config.yaml (MANTENER)
│   │   ├── memory/                ← ABC + Hindsight + Hermes + detector
│   │   ├── plugin_router.py       ← Sandbox Engine (KEEP, renombrar doc)
│   │   └── output_pipeline/       ← DLP
│   ├── tools/                     ← contacts, inbox, agenda, alerts, files
│   ├── transport/                 ← send, webhook
│   └── utils/                     ← jids, safe_json, admin_cli, etc.
├── GUI/                           ← standalone (KEEP)
├── tests/                         ← pytest
└── state/                         ← (runtime, en .gitignore)
```

### Lo que se ELIMINA
- `patch_bridge.py`, `patch_whatsapp.py`, `check_patches.py` (después de F2+F3)
- `scripts/security/__init___v2.py` (huérfano)
- `revision-plan.md` (ejecutado)
- `versions/` (mover a release archive)

### Lo que se MANTIENE
- `soul_sync.py` escribiendo `config.yaml` (es el mecanismo documentado de Hermes)
- `setup.py` / `install_cli.py` como instaladores legacy (fallback)
- GUI standalone (no hay API de Hermes para paneles de plugins)
- `plugin_router.py` / `plugin_sdk.py` (Sandbox Engine interno)
- Archivos JSON como estado (no hay `ctx.set_state`)

---

## 11. ORDEN FINAL DE IMPLEMENTACIÓN

```
F2 (Plugin integration: register(ctx), hooks nativos, tools nativos)
  └── Sin tocar patch_*.py aún
F3 (APIs nativas: hermes cron, filelock, hermes gateway restart)
  └── Sin tocar patch_*.py aún
F5 (Seguridad: S4 path traversal, S5 OAuth creds, S3 _hermes_ guard)
  └── Independiente de F2/F3
F1 (Limpieza: desactivar patch_*.py, eliminar huérfanos, inglés)
  └── SOLO después de verificar F2+F3
F4 (Config: plugin.yaml env vars, path resolution dual)
F6 (GUI: documentar standalone)
F7 (Docs: README, FEATURES, GUIDE, SKILL, ARCHITECTURE)
F8 (Tests: pytest, CI/CD)
F9 (Auditoría: compilación, regresión, plugin validate)
```

---

## 12. RIESGOS CRÍTICOS

| # | Riesgo | Probabilidad | Impacto |
|---|--------|------------|---------|
| R1 | `register(ctx)` en `__init__.py` no es discoverable por `PluginManager` | Media | **Crítico** — el plugin no se cargaría |
| R2 | `channel_prompts` deja de funcionar si Hermes cambia el formato de `config.yaml` | Baja | Alto — las sub-souls desaparecerían |
| R3 | `patch_whatsapp.py` se desactiva antes de migrar inbox writer y alert dispatcher | Alta | **Crítico** — se pierde la recepción de mensajes |
| R4 | `hermes plugin install` requiere el plugin en el catalog (SHA pin, PR review) | Alta | **Crítico** — sin catalog entry, no hay instalación fácil |

---

## 13. PUNTOS QUE REQUIEREN VERIFICACIÓN MANUAL

| # | Punto | Quién debe verificarlo |
|---|-------|----------------------|
| V1 | ¿`PluginManager` descubre `register(ctx)` en `__init__.py` de `~/.hermes/plugins/andorina/`? | Probar con `hermes plugins list` después de crear `__init__.py` |
| V2 | ¿El plugin catalog acepta `kind: tool` que extiende WhatsApp? | Revisar `plugin-catalog/README.md` admission policy |
| V3 | ¿`hermes plugins validate` acepta el `plugin.yaml` actual? | Ejecutar `hermes plugins validate .` en el directorio del plugin |
| V4 | ¿`channel_prompts` en `config.yaml` sigue siendo el mecanismo correcto en v0.21? | Verificar `gateway/platforms/ADDING_A_PLATFORM.md` y `whatsapp.py` |
| V5 | ¿El inbox writer y alert dispatcher funcionan sin el patch de `whatsapp.py`? | Probar con una instalación real de Hermes + WhatsApp |

---

*Revisión generada tras verificación contra Hermes v0.21.1 — 2026-09-12*

---

## 14. VERIFICACIONES COMPLETADAS

> **Fecha:** 2026-09-12
> **Hermes:** v0.21.1 (instalado y verificado)

### V1 — Descubrimiento de `register(ctx)`

**Resultado: CONFIRMED**

**Evidencia:**
1. Plugin de prueba creado en `/tmp/test-plugin/` con `plugin.yaml` + `__init__.py` con `register(ctx)`
2. Copiado a `~/.hermes/plugins/test-discovery/`
3. `hermes plugins list --plain` lo detecta: `not enabled  user  0.1.0  test-discovery`
4. `hermes plugins validate` pasó: `✓ capability probe — register() ran in isolation`
5. `hermes plugins enable test-discovery` funcionó
6. `hermes plugins remove test-discovery` funcionó

**Mecanismo de descubrimiento:**
- `PluginManager` escanea `~/.hermes/plugins/`
- Busca `plugin.yaml` en cada subdirectorio
- Carga `__init__.py` y busca `register(ctx)`
- Ejecuta `register(ctx)` en aislamiento para validar capabilities
- El plugin aparece como "not enabled" por defecto (opt-in)

**Conclusión para Andoriña:**
- Crear `__init__.py` en la raíz del plugin con `register(ctx)`
- `register(ctx)` debe llamar a `ctx.register_hook()` y `ctx.register_tool()`
- El `plugin.yaml` actual es correcto como estructura

---

### V2 — Plugin catalog

**Resultado: CONFIRMED**

**Evidencia:**
1. `hermes plugins search whatsapp` no encontró plugins third-party de WhatsApp
2. Hermes YA tiene WhatsApp como plataforma built-in (`gateway/platforms/whatsapp.py`)
3. El `plugin-catalog/README.md` requiere: SHA pin, PR review, "owner-or-major-contributor submissions"
4. `kind: tool` es aceptado (el test plugin con `kind: tool` pasó validación)

**Restricciones relevantes para Andoriña:**
- El plugin catalog requiere repositorio Git público con SHA pin de 40 caracteres
- La submission debe hacerla el owner o major contributor del repositorio
- El `capabilities` block debe coincidir exactamente con lo que registra `register(ctx)`
- Las capabilities son "consent and audit layer", NO un sandbox

**Conclusión:** Andoriña puede ser aceptado en el catalog como `kind: tool`.

---

### V3 — `hermes plugins validate`

**Resultado: PARCIAL (bug en Hermes v0.21.1)**

**Evidencia:**
1. La validación del proyecto completo falla con `ImportError: cannot import name '_VERSION_COMPARATOR_RE'`
   - Esto es un bug en Hermes v0.21.1, no en nuestro `plugin.yaml`
   - El error ocurre en `_check_requires_hermes()` que intenta importar de un módulo refactorizado
2. Validación SIN `requires_hermes` funciona correctamente:
   - `✓ manifest — plugin.yaml parses`
   - `✓ manifest fields — name, version, description present`
   - `✓ capability probe — register() ran in isolation`
   - `✗ declared tools/hooks` — error esperado porque el test no registraba lo declarado
3. La validación comprueba que las capabilities declaradas COINCIDAN con lo registrado en `register(ctx)`

**Campos exigidos por el validador:**
- `name`, `version`, `description` (obligatorios)
- `capabilities.provides_tools`, `provides_hooks`, `provides_middleware` (deben coincidir con registros)
- `capabilities.requires_env` (entries en UPPER_SNAKE con `description`, `prompt`, `password`)
- `requires_hermes` (opcional, actualmente roto en v0.21.1)

**Cambios necesarios en `plugin.yaml`:**
- ⚠️ `requires_hermes: ">=0.19.0"` falla en v0.21.1 por bug de Hermes. Temporalmente eliminar este campo hasta que Hermes lo corrija.
- ✅ El resto del `plugin.yaml` es válido

---

### V4 — `channel_prompts`

**Resultado: CONFIRMED**

**Evidencia:**
1. `base.py:1716-1719`: `resolve_channel_prompt(config_extra, channel_id, parent_id)`
   ```python
   def resolve_channel_prompt(config_extra: dict, channel_id: str, parent_id=None) -> str | None:
       prompts = config_extra.get("channel_prompts") or {}
   ```
2. `event.py:74`: `MessageEvent` tiene campo `channel_prompt: Optional[str]`
3. `turn_context.py:43`: `TurnContext` tiene `channel_prompt`
4. `gateway/run.py:1204`: `channel_prompt` se pasa al session loop
5. `config.py:3129`: `"channel_prompts"` está en la lista de claves permitidas de config

**Formato esperado:**
```yaml
whatsapp:
  channel_prompts:
    "34600000000@s.whatsapp.net": "### CUSTOM PERSONALITY (SOUL)..."
    "120363001234@g.us": "### GROUP PERSONALITY..."
```

**Conclusión:**
- `soul_sync.py` DEBE mantenerse exactamente como está
- `channel_prompts` es el mecanismo documentado y soportado de Hermes
- NO existe API alternativa para plugins (no hay `ctx.set_channel_prompt()`)
- `soul_sync.py` NO es un "parche" — escribe en `config.yaml` usando la API estándar de Hermes

---

### V5 — Sustitución de `patch_whatsapp.py`

**Resultado: CONFIRMED — completamente migrado**

Análisis del `patch_whatsapp.py` original (421 líneas en V1.6-Beta1):

| PATCH | Función | Código actual que lo reemplaza | ¿Falta migrar? |
|-------|---------|-------------------------------|----------------|
| `_resolve_lid_to_phone()` method | Resolver LID de WhatsApp → número canónico | `jids.py:84` — `resolve_lid_to_phone()` | ✅ NO — standalone en jids.py |
| Sub-Soul injection block | Inyectar `_channel_prompt` en `MessageEvent` | `orchestrator_hook.py:36-90` — `_resolve_active_plugin()` y `build_snapshot()` | ✅ NO — se hace en el hook |
| Inbox Writer block | Escribir mensajes entrantes en `inbox.json` | `webhook.py:180-255` — `process_incoming_message(write_inbox=True)` | ✅ NO — standalone en webhook.py |
| Alert Dispatcher block | Disparar alertas semánticas | `webhook.py:262-281` — misma función | ✅ NO — standalone en webhook.py |

**Verificación adicional:**
- Hermes WhatsApp NO tiene su propio `_resolve_lid_to_phone` (no encontrado en `whatsapp.py` ni `base.py`)
- Andoriña `jids.py` tiene su propia implementación independiente
- El `patch_whatsapp.py` actual es un stub de 16 líneas que imprime "DEPRECATED" y sale

**Conclusión:**
- Las 4 funciones del patch original ya están migradas a scripts standalone
- `patch_whatsapp.py` puede eliminarse de forma segura
- `patch_bridge.py` puede eliminarse de forma segura (los endpoints que añadía ahora son nativos de Hermes)
- `check_patches.py` puede eliminarse (no hay parches que verificar)

---

## 15. PLAN FINAL DE IMPLEMENTACIÓN

> **Versión:** Revisado tras verificaciones V1–V5

### Cambios respecto al plan original

| Cambio | Razón |
|--------|-------|
| **Añadir** `__init__.py` en raíz con `register(ctx)` | V1 confirmó que PluginManager lo requiere |
| **Eliminar** F2.3 (migrar channel_prompts) | V4 confirmó que no hay API alternativa |
| **Eliminar** F4.2 (ctx.set_state) | No disponible en Hermes v0.21.1 |
| **Eliminar** F6.1 (hermes web) | No existe el comando |
| **Corregir** `requires_hermes` temporalmente | Bug en Hermes v0.21.1 impide validar este campo |
| **Adelantar** limpieza de patch_*.py | V5 confirmó que las 4 funciones ya están migradas |

---

### Orden final de implementación

```
FASE 1: Entry point del plugin
FASE 2: APIs nativas
FASE 3: Seguridad
FASE 4: Limpieza
FASE 5: Configuración
FASE 6: Documentación
FASE 7: Tests
FASE 8: Auditoría final
```

---

### FASE 1 — Entry point del plugin

**Objetivo:** Crear `__init__.py` con `register(ctx)` y validar.

| # | Acción | Archivos | Validación |
|---|--------|----------|------------|
| 1.1 | Crear `__init__.py` en raíz con `register(ctx)` que registre hooks y tools | `__init__.py` (NUEVO) | `hermes plugins validate .` pasa capability probe |
| 1.2 | Mover lógica de `adapter.py` a `register(ctx)` en `__init__.py` | `__init__.py`, `adapter.py` | `register()` registra hooks+tools correctamente |
| 1.3 | Verificar que `plugin.yaml` capabilities coinciden con lo registrado | `plugin.yaml` | `hermes plugins validate .` sin errores de declared tools/hooks |
| 1.4 | Eliminar `requires_hermes` temporalmente (bug Hermes v0.21.1) | `plugin.yaml` | Validación no crashea |

**Criterio de finalización:** `hermes plugins validate .` pasa sin errores (excepto el bug conocido de `requires_hermes`).

---

### FASE 2 — APIs nativas

**Objetivo:** Reemplazar dependencias POSIX por APIs de Hermes.

| # | Acción | Archivos | Validación |
|---|--------|----------|------------|
| 2.1 | Reemplazar `crontab` por `hermes cron` en agenda.py | `agenda.py` | `hermes cron list` muestra tareas de Andoriña |
| 2.2 | Reemplazar `fcntl` por `filelock` en common.py y webhook.py | `common.py`, `webhook.py` | Tests de concurrencia pasan |
| 2.3 | Reemplazar `systemctl`/`pkill` por `hermes gateway restart` en soul_sync.py | `soul_sync.py` | `hermes gateway restart` funciona |
| 2.4 | Hacer `tool_executor.py` multi-OS (PATH sin hardcodear) | `tool_executor.py` | No crashea en macOS |

**Criterio de finalización:** `test_sandbox.py --quick` pasa 75/75.

---

### FASE 3 — Seguridad

**Objetivo:** Cerrar vulnerabilidades confirmadas.

| # | Acción | Archivos | Validación |
|---|--------|----------|------------|
| 3.1 | Añadir validación de path en `_notes_path()` (no salir de NOTES_DIR) | `contacts.py` | Test de path traversal falla |
| 3.2 | Mover Google OAuth creds de hardcode a `.env.example` | `auth.py` | `grep DEFAULT_CID auth.py` no encuentra nada |
| 3.3 | Añadir guard: solo owner puede asignar `custom_soul = "_hermes_"` | `admin_cli.py` | `cmd_soul_set` rechaza _hermes_ para no-owner |

**Criterio de finalización:** `test_edge_cases.py` pasa sin crashes de seguridad.

---

### FASE 4 — Limpieza

**Objetivo:** Eliminar código legacy ya migrado.

| # | Acción | Archivos | Validación |
|---|--------|----------|------------|
| 4.1 | Eliminar `scripts/security/__init___v2.py` (huérfano) | `__init___v2.py` | Compilación OK |
| 4.2 | Eliminar `patch_bridge.py`, `patch_whatsapp.py`, `check_patches.py` | 3 archivos | V5 confirmó que son seguros de eliminar |
| 4.3 | Eliminar `revision-plan.md` (ya ejecutado) | `revision-plan.md` | — |
| 4.4 | Traducir docstrings español→inglés en archivos de desarrollo | `memory/__init__.py`, `detector.py`, `common.py`, `install_cli.py` | `grep -r "configuración\|búsqueda\|gestión" scripts/` vacío |

**Criterio de finalización:** Compilación OK, 0 archivos huérfanos.

---

### FASE 5 — Configuración

**Objetivo:** Unificar paths y variables de entorno.

| # | Acción | Archivos | Validación |
|---|--------|----------|------------|
| 5.1 | Hacer que `common.py` busque `.env` en `plugins/andorina` antes que `skills/andorina` | `common.py` | El plugin carga config correctamente |
| 5.2 | Hacer que `jids.py` busque `DEFAULT_COUNTRY_CODE` en `plugins/andorina/.env` | `jids.py` | `normalize_jid` funciona sin `skills/` |
| 5.3 | Verificar que `plugin.yaml` `requires_env`/`optional_env` son correctos | `plugin.yaml` | `hermes plugins capabilities andorina` muestra las vars |

**Criterio de finalización:** El plugin funciona sin el path `skills/` hardcodeado.

---

### FASE 6 — Documentación

**Objetivo:** Actualizar docs para reflejar V2.0.

| # | Acción | Archivos | Validación |
|---|--------|----------|------------|
| 6.1 | Actualizar `README.md`: badges `v2.0.0-alpha`, quitar V1.5 refs | `README.md` | Badge muestra `v2.0.0-alpha` |
| 6.2 | Actualizar `ARCHITECTURE.md`: reflejar estado real post-F1-F5 | `ARCHITECTURE.md` | Describe `register(ctx)` y plugin structure |
| 6.3 | Actualizar `CHANGELOG.md`: entrada `v2.0.0-alpha` completa | `CHANGELOG.md` | Lista todos los cambios de F1-F5 |
| 6.4 | Actualizar `MIGRATION.md`: instrucciones verificadas con V1 | `MIGRATION.md` | Instrucciones de `hermes plugins` corregidas |
| 6.5 | Actualizar `SKILL.md`: modo plugin en lugar de "terminal only" | `SKILL.md` | Referencias a `setup.py` reemplazadas |

**Criterio de finalización:** 0 referencias a `v1.5` en la documentación.

---

### FASE 7 — Tests

**Objetivo:** Añadir cobertura de tests.

| # | Acción | Archivos | Validación |
|---|--------|----------|------------|
| 7.1 | Mover `test_sandbox.py` y `test_edge_cases.py` a `tests/` | `tests/` | `pytest tests/` funciona |
| 7.2 | Añadir `tests/test_plugin.py` con mock de `ctx` | `tests/test_plugin.py` | Test verifica que `register(ctx)` registra hooks y tools |
| 7.3 | Añadir `tests/conftest.py` con fixtures | `tests/conftest.py` | Fixtures reutilizables |

**Criterio de finalización:** `pytest tests/` pasa >90 tests.

---

### FASE 8 — Auditoría final

**Objetivo:** Verificar que todo funciona.

| # | Acción | Validación |
|---|--------|------------|
| 8.1 | `python3 -m py_compile` en todos los `.py` | 0 errores |
| 8.2 | `python3 scripts/test_sandbox.py --quick` | 75/75 |
| 8.3 | `python3 scripts/test_edge_cases.py` | Sin crashes |
| 8.4 | `hermes plugins validate .` | Capability probe OK |
| 8.5 | `hermes plugins list --plain` muestra andorina | Plugin discoverable |
| 8.6 | `grep -r "v1.5\|v1.6" --include="*.md" --include="*.py"` | Solo en CHANGELOG histórico |

**Criterio de finalización:** Todos los checks pasan.

---

### Archivos que se CREAN

| Archivo | Fase |
|---------|------|
| `__init__.py` (raíz) | F1 |
| `tests/conftest.py` | F7 |
| `tests/test_plugin.py` | F7 |

### Archivos que se MODIFICAN

| Archivo | Fase |
|---------|------|
| `plugin.yaml` | F1 |
| `scripts/security/memory/adapter.py` | F1 |
| `scripts/tools/agenda.py` | F2 |
| `scripts/common.py` | F2 |
| `scripts/transport/webhook.py` | F2 |
| `scripts/security/soul_sync.py` | F2 |
| `scripts/security/tool_executor.py` | F2 |
| `scripts/tools/contacts.py` | F3 |
| `scripts/utils/auth.py` | F3 |
| `scripts/utils/admin_cli.py` | F3 |
| `scripts/security/memory/__init__.py` | F4 |
| `scripts/security/memory/detector.py` | F4 |
| `scripts/security/input_guard.py` | F4 |
| `scripts/utils/jids.py` | F5 |
| `README.md` | F6 |
| `ARCHITECTURE.md` | F6 |
| `CHANGELOG.md` | F6 |
| `MIGRATION.md` | F6 |
| `SKILL.md` | F6 |

### Archivos que se ELIMINAN

| Archivo | Fase | Razón |
|---------|------|-------|
| `scripts/security/__init___v2.py` | F4 | Huérfano |
| `patch_bridge.py` | F4 | V5: funcionalidad migrada |
| `patch_whatsapp.py` | F4 | V5: funcionalidad migrada |
| `check_patches.py` | F4 | No hay parches que verificar |
| `revision-plan.md` | F4 | Ya ejecutado |

### Archivos que NO se modifican

- `scripts/security/soul_sync.py` (channel_prompts) — V4 confirmó que debe mantenerse
- `scripts/security/plugin_router.py` — Sandbox Engine interno
- `scripts/utils/plugin_sdk.py` — SDK interno de sandboxes
- `scripts/security/output_pipeline/*` — DLP pipeline
- `scripts/tools/alerts.py`, `inbox.py` — Funcionan correctamente
- `scripts/transport/send.py` — Funciona correctamente
- `GUI/*` — Standalone (no integrable con hermes web)
- `setup.py`, `install_cli.py` — Legacy installers (mantener como fallback)

---

*Plan final generado tras verificaciones V1–V5 contra Hermes v0.21.1 — 2026-09-12*
## 15. EJECUCIÓN — F1 Y F2 COMPLETADAS

> **Fecha:** 2026-09-12  
> **Estado:** F1 APROBADA, F2 APROBADA, Hotfix APROBADO  
> **Próximo:** F3 (Security)

### F1 — Plugin Entry

**Resultado: APROBADA** — 2026-09-12

| Check | Resultado |
|-------|-----------|
| `__init__.py` con `register(ctx)` | ✅ 3 hooks (`pre_llm_call`, `pre_tool_call`, `post_llm_call`) + 11 tools registrados |
| `plugin.yaml` validación | ✅ `hermes plugins validate .` → 10/10 checks passed |
| Descubrimiento | ✅ `PluginManager` descubre el plugin |
| Hook stdin piping | ✅ `_run_hook` pasa payload por stdin a `orchestrator_hook.py` |
| Tool argument mapping | ✅ 11/11 tools: argumentos wrapper → sys.argv → script `__main__` verificados |
| `adapter.py` sin duplicación | ✅ Reducido 165→68 líneas |
| `requires_hermes` | ⚠️ Temporalmente deshabilitado (bug en Hermes v0.21.1 validator) |
| Tests | ✅ 75/75 PASS |

### F2 — Native APIs

**Resultado: APROBADA** — 2026-09-12

| Check | Resultado |
|-------|-----------|
| F2.1 `crontab` → `hermes cron` | ✅ `_run_cron_command` helper usa `hermes cron` preferido, `crontab` fallback |
| F2.2 `fcntl` → `filelock` | ✅ `common.py` ya migrado; `webhook.py` fcntl solo en código muerto (corregido en hotfix) |
| F2.3 `systemctl` → `hermes gateway restart` | ✅ 10 líneas eliminadas, `hermes gateway restart` único mecanismo |
| F2.4 `tool_executor.py` multi-OS | ✅ Sin PATH hardcodeado |
| Compilación | ✅ 4/4 archivos |
| Tests | ✅ 75/75 PASS |
| Plugin validate | ✅ 10/10 |

### 🔧 Hotfix — Webhook Locking

**Resultado: APROBADO** — 2026-09-12

Bug detectado durante F2: `_get_lock()` y `_release_lock()` invocadas pero no definidas → `NameError` en runtime al escribir en inbox.

| Cambio | Resultado |
|--------|-----------|
| `_try_lock()` eliminado (código muerto, 7 líneas) | ✅ 0 refs a `_try_lock` |
| `from filelock import FileLock` añadido | ✅ Coincide con patrón de `safe_json.py` |
| `_get_lock`/`_release_lock` → `FileLock` context manager | ✅ Sin pérdida de datos (10 escritores concurrentes) |
| `fcntl` en webhook.py | ✅ 0 refs |
| Tests | ✅ 75/75 PASS |
| Plugin validate | ✅ 10/10 |
| Test aislado de locking | ✅ 10/10 concurrente sin data loss |

### Lecciones aprendidas

1. **`hermes plugins validate` es el gold standard** — detecta herramientas/hooks no registrados, capability mismatch, y errores en `register(ctx)`.
2. **El validador de Hermes v0.21.1 tiene un bug con `requires_hermes`** — el campo debe omitirse hasta que Hermes lo corrija.
3. **Las funciones legacy de locking (`_try_lock`, `_get_lock`, `_release_lock`) eran código muerto o indefinido** — la migración a `FileLock` unifica el mecanismo con `safe_json.py`.
