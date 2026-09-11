# 🩺 V1.6-Beta1 — Plan de Revisión (Auditoría Completa)

> **Fecha:** 16/07/2026
> **Alcance:** Todos los archivos de la skill (excepto `docs/`)
> **Estado:** Solo lectura — no modificar hasta aprobación del plan

---

## 🔴 CRÍTICOS (Riesgo de fallo funcional / pérdida de datos)

### 1. `orchestrator_hook.py` — DLP pipeline no funcional para mensajes salientes

- **Líneas 547-564:** El pipeline DLP se ejecuta correctamente (`_dlp_run_pipeline()`), pero el resultado saneado (`_clean_text`) solo se escribe al log. El hook emite `{"action": "allow"}` incondicionalmente, por lo que Hermes entrega el texto original sin sanear.
- **Líneas 554-560:** Cuando `dlp_result.get("status") != "OK"`, se loguea `[DLP BLOCKED]` pero se sigue emitiendo `{"action": "allow"}`. No existe código que devuelva `{"action": "block"}` para un bloqueo DLP.
- **Impacto:** El pipeline DLP (truncado, sanitización, paginación) no tiene efecto real sobre lo que el usuario recibe.

### 2. `GUI/server.py` — Deadlock en guardado de sesiones

- **Línea 227:** `save_sessions()` se llama dentro de `with SESSION_LOCK:` (línea 222-228), pero `save_sessions()` (línea 198) intenta adquirir el mismo `SESSION_LOCK`. `threading.Lock` no es reentrante → deadlock inmediato cuando una sesión expira.
- **Impacto:** El panel web se congela cuando una sesión expira.

### 3. `GUI/server.py` — Sin autenticación en rutas DELETE

- **Líneas 2724-2811:** El método `do_DELETE` entero carece de comprobaciones de autenticación. Cualquier llamada no autenticada puede eliminar agenda items, souls, knowledge files, webhooks, roles, notas y recurring items.
- **Impacto:** Vulnerabilidad de seguridad crítica — cualquier persona con acceso de red al panel puede borrar datos.

### 4. `GUI/server.py` — `NameError` en `/api/auth/status`

- **Línea 419-421:** La variable `session` solo se define dentro del bloque `if not is_auth:` (líneas 394-398). Para rutas públicas que saltan auth, `session` nunca se asigna → `NameError`.
- **Impacto:** El endpoint `/api/auth/status` falla para rutas públicas.

### 5. `soul_sync.py` — SQL injection en `transition_short_term_memory`

- **Línea 402:** Se construye consulta SQL con concatenación de strings sin sanitizar. El texto del mensaje puede contener caracteres especiales que rompan la query.
- **Impacto:** Posible corrupción de la base de datos de memoria a largo plazo.

### 6. `webhook.py` — JID construido manualmente en `pre_llm_call` bypassa `normalize_jid()`

- **Líneas 329, 331, 338:** Los JIDs se construyen con `group_jid_raw + "@g.us"` y `sender + "@s.whatsapp.net"` en lugar de usar `normalize_jid()`. El path legacy (líneas 184-185) sí usa `normalize_jid()`.
- **Impacto:** Si el bridge envía JIDs sin código de país en el path `pre_llm_call`, las alertas y el RBAC pueden fallar porque el JID no coincide con las reglas guardadas.

### 7. `webhook.py` — Fallback de sender incorrecto para grupos

- **Líneas 338-342:** `sender else effective_chat_id` — si `sender` está vacío, se pasa el JID del grupo como remitente individual, haciendo que el mensaje parezca provenir del grupo mismo.
- **Impacto:** Mensajes de grupo sin sender identificable se atribuyen incorrectamente al grupo.

---

## 🟠 ALTOS (Riesgo de comportamiento incorrecto)

### 8. `jids.py` — `resolve_hook_jid` usa substring matching en lugar de `jid_match()`

- **Línea 223:** `bare and (bare in c_id or c_id in bare)` — comparación por subcadena. Si `bare = "34"`, coincide con `c_id = "341234567"` → falso positivo.
- **Impacto:** Resolución de contactos por LID puede devolver el contacto equivocado.

### 9. `jids.py` — `resolve_hook_jid` importa `sys` dentro de un `else`

- **Línea 312:** `import sys as _sys` dentro de una rama `else`. Si se añade código antes que referencie `_sys`, causa `UnboundLocalError`.
- **Impacto:** Fragilidad ante cambios futuros.

### 10. `alerts.py` — `cmd_remove` no normaliza `source` antes de comparar con `jid_match`

- Al usar `jid_match`, la comparación es tolerante, pero si el source almacenado está en un formato y el parámetro en otro, `jid_match` lo maneja. Sin embargo, hay un edge case: si `source` pasado es `""` o `None`, `normalize_jid` retorna el valor sin cambios, y `jid_match` con string vacío puede dar falsos positivos.
- **Impacto:** Posible eliminación accidental de reglas de alerta si se pasa un JID mal formado.

### 11. `inbox.py` — `cmd_listar` no normaliza `filter_chats`

- **Línea 64:** `filter_chats` recibido del comando `--filter-chats` no se normaliza. Si el orquestador pasa JIDs con formato inconsistente, el filtrado falla.
- **Impacto:** Usuarios pueden ver chats que no deberían (fuga de privacidad).

### 12. `input_guard.py` — No importa desde `jids.py`

- El archivo implementa su propia lógica de limpieza de números sin usar `clean_number()` o `normalize_jid()` del módulo centralizado.
- **Impacto:** Inconsistencia — si se cambia la lógica en `jids.py`, `input_guard.py` no se beneficia.

### 13. `dlp.py` (output_pipeline) — Falso positivo en detección de API keys

- **Líneas 29-30:** El patrón de substring para detectar API keys es demasiado amplio y puede marcar texto legítimo como fuga.
- **Impacto:** Falsos positivos que bloquean mensajes válidos (aunque el bug #1 hace que el bloqueo no sea efectivo).

### 14. `dlp.py` (output_pipeline) — Regex de base64 demasiado amplio

- **Línea 11:** El patrón `[A-Za-z0-9+/]{40,}={0,2}` captura cualquier string largo alfanumérico, no solo base64 real.
- **Impacto:** Falsos positivos en detección de tokens.

---

## 🟡 MEDIOS (Inconsistencias / problemas de mantenibilidad)

### 15. `send.py` — No normaliza JID antes de enviar

- El `chat_id` recibido se usa tal cual. Si el LLM pasa un número parcial (ej. `612345678`), el bridge puede rechazarlo.
- **Impacto:** Mensajes fallidos si el LLM no normaliza antes de llamar a `send.py`.

### 16. `files.py` — Igual que `send.py`, no normaliza JID

- **Impacto:** Envío de archivos fallido con JIDs parciales.

### 17. `agenda.py` — `cmd_send_pending` no normaliza `chat_id` al recuperar de agenda.json

- Si una tarea se guardó con JID no normalizado (antes de la corrección V1.6), `send.py` recibirá un JID potencialmente inválido.
- **Impacto:** Tareas programadas antiguas pueden fallar tras la actualización.

### 18. `admin_cli.py` — Implementa su propia lógica de JID sin usar `jids.py`

- Funciones como `role set`, `soul set`, `chatbot mute` aceptan JIDs y los procesan manualmente en lugar de delegar en `normalize_jid()`.
- **Impacto:** Inconsistencia con el resto de la skill.

### 19. `GUI/server.py` — Race condition en renovación de sesión

- **Línea 231:** La expiración de sesión se actualiza fuera del `SESSION_LOCK` (lock liberado en línea 228, modificación en 231). Requests concurrentes pueden corromper el estado.
- **Impacto:** Sesiones pueden expirar prematuramente o no renovarse.

### 20. `GUI/server.py` — `send_json` muta el estado de respuesta

- El método `send_json` modifica `self._auth_checked` y otros atributos después de enviar la respuesta, causando comportamiento impredecible en requests concurrentes.
- **Impacto:** Posible corrupción de estado en el servidor HTTP.

### 21. `setup.py` — `DEFAULT_COUNTRY_CODE` no se escribe en `.env` si el usuario deja el campo vacío

- Si el usuario no introduce código de país, `normalize_jid()` usará el fallback `"34"` pero no hay registro explícito en `.env`.
- **Impacto:** Comportamiento inconsistente entre instalaciones.

### 22. `patch_whatsapp.py` — Inbox writer no respeta `write_inbox: False`

- El webhook dispatch en `patch_whatsapp.py` envía `"write_inbox": False` en el payload, pero el inbox writer en `whatsapp.py` ya escribió antes de llamar al webhook. El flag es redundante e ignorado.
- **Impacto:** No hay bug funcional, pero el flag es engañoso.

---

## 🟢 BAJOS (Mejoras / issues menores)

### 23. `jids.py` — Importaciones locales inconsistentes

- Algunas funciones usan imports locales (ej. `import json as _json` dentro de la función), otras usan imports a nivel de módulo. El estilo no es uniforme.

### 24. `contacts.py` — `get_jid()` como función helper duplica lógica de `normalize_jid()`

- `get_jid()` añade `@s.whatsapp.net` o `@g.us` manualmente. Debería delegar en `normalize_jid()`.

### 25. `inbox.py` — `load_canonical_map()` duplica parcialmente `resolve_lid_to_phone()`

- La canonicalización de LID en inbox es independiente de la de jids.py. Si una cambia, la otra no.

### 26. `webhook.py` — `_norm` local renombrada a `normalize_jid` pero aún hay referencias al nombre antiguo

- Verificar que no queden llamadas a `_norm()` en lugar de `normalize_jid()`.

### 27. `GUI/static/app.js` — Posible XSS en renderizado de mensajes

- El panel web renderiza contenido de mensajes WhatsApp sin sanitización adecuada en algunas secciones.

### 28. `install_cli.py` — Archivo nuevo sin documentación

- No está claro su propósito ni cómo se relaciona con `install.sh` y `setup.py`.

### 29. `VERSION` — Sigue diciendo `1.5.2-Beta5`

- Debería actualizarse a `1.6-Beta1` para reflejar la versión real.

### 30. `CHANGELOG.md` — No incluye entradas para V1.6

- El changelog termina en v1.5.2-Beta5. No documenta los cambios del refactor V1.6.

---

## 📊 RESUMEN POR CATEGORÍA

| Categoría | Archivos afectados | Issues |
|:---|:---|:---:|
| **JID Normalization** | `webhook.py`, `send.py`, `files.py`, `admin_cli.py`, `input_guard.py`, `inbox.py`, `jids.py`, `contacts.py` | 10 |
| **DLP Pipeline** | `orchestrator_hook.py`, `dlp.py` | 3 |
| **GUI Server** | `server.py` | 5 |
| **Seguridad** | `server.py`, `soul_sync.py`, `app.js` | 3 |
| **Documentación** | `VERSION`, `CHANGELOG.md`, `install_cli.py` | 3 |
| **Output Pipeline** | `dlp.py`, `sanitizer.py`, `truncation.py` | 2 |
| **Import/Estilo** | `jids.py`, `contacts.py` | 2 |
| **Race Conditions** | `server.py` | 2 |

---

## ✅ ARCHIVOS SIN PROBLEMAS DETECTADOS

- `scripts/security/orchestrator.py` — Sin bugs aparentes
- `scripts/security/tool_executor.py` — Sin bugs aparentes
- `scripts/security/tool_guard.py` — Sin bugs aparentes
- `scripts/security/sec_types.py` — Sin bugs aparentes
- `scripts/security/plugin_router.py` — Sin bugs aparentes
- `scripts/security/debug_soul_chain.py` — Sin bugs aparentes
- `scripts/security/output_pipeline/pagination.py` — Sin bugs aparentes
- `scripts/security/output_pipeline/truncation.py` — Sin bugs aparentes
- `scripts/security/output_pipeline/sanitizer.py` — Sin bugs aparentes
- `scripts/security/output_pipeline/__init__.py` — Sin bugs aparentes
- `scripts/utils/auth.py` — Sin bugs aparentes
- `scripts/utils/bridge_health.py` — Sin bugs aparentes
- `scripts/utils/diag.py` — Sin bugs aparentes
- `scripts/utils/disk_monitor.py` — Sin bugs aparentes
- `scripts/utils/plugin_sdk.py` — Sin bugs aparentes
- `scripts/utils/safe_json.py` — Sin bugs aparentes
- `scripts/utils/setup_autostart.py` — Sin bugs aparentes
- `scripts/utils/tunnel.py` — Sin bugs aparentes
- `scripts/utils/wipe_logs.py` — Sin bugs aparentes
- `scripts/tools/plugin_event_loop.py` — Sin bugs aparentes
- `scripts/common.py` — Sin bugs aparentes
- `scripts/security/knowledge_retrieval.py` — Sin bugs aparentes

---

## 📋 PLAN DE ACCIÓN RECOMENDADO (para cuando se apruebe)

### Fase 1 — Críticos (7 issues)

1. Arreglar DLP pipeline en `orchestrator_hook.py` para que aplique el texto saneado
2. Arreglar deadlock en `GUI/server.py` (lock reentrante o refactor)
3. Añadir autenticación a rutas DELETE en `GUI/server.py`
4. Arreglar `NameError` en `/api/auth/status`
5. Sanitizar query SQL en `soul_sync.py`
6. Usar `normalize_jid()` en path `pre_llm_call` de `webhook.py`
7. Arreglar fallback de sender en `webhook.py`

### Fase 2 — Altos (7 issues)

8. Usar `jid_match()` en `resolve_hook_jid` (jids.py)
2. Mover `import sys` al nivel de módulo en `jids.py`
3. Validar JID vacío en `alerts.py` `cmd_remove`
4. Normalizar `filter_chats` en `inbox.py`
5. Importar desde `jids.py` en `input_guard.py`
6. Refinar regex de API key en `dlp.py`
7. Refinar regex de base64 en `dlp.py`

### Fase 3 — Medios (8 issues)

15-22. Normalizar JIDs en `send.py`, `files.py`, `agenda.py`, `admin_cli.py`; arreglar race condition en server.py; arreglar `send_json`; asegurar `DEFAULT_COUNTRY_CODE` en setup

### Fase 4 — Bajos (8 issues)

23-30. Uniformizar imports, eliminar `get_jid()` helper, unificar canonicalización LID, actualizar VERSION y CHANGELOG, documentar `install_cli.py`, sanitizar HTML en app.js

---

*Este plan es solo de diagnóstico. No se ejecutará hasta aprobación explícita.*
