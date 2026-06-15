# Andoriña V2.0 — Developer Guide

Bienvenido a la documentación oficial para creadores de Sandboxes, Juegos y Plugins de Andoriña. 
El sistema de Andoriña V2 permite extender el asistente mediante módulos independientes sin modificar el núcleo del bot, asegurando total compatibilidad y prevención de fallos en cascada.

## 1. Guía de Inicio Rápido (Tu primer Plugin en 10 minutos)

1. Abre el panel web de Andoriña.
2. Ve a la pestaña **Sandboxes**.
3. Haz clic en **Crear Plugin (Modo Avanzado)** y dale un nombre, por ejemplo: `MiPrimerPlugin`.
4. En la configuración, asegúrate de marcar los permisos necesarios, por ejemplo, `can_send_proactive_messages`.
5. Ve a la pestaña **Código** y verás un archivo `tools.py` pre-generado. Este archivo es el corazón de tu plugin.
6. Ve a la pestaña **Asignación** y asígnalo a tu propio número de WhatsApp o a un grupo de pruebas.
7. ¡Listo! Todo lo que escribas en el código afectará inmediatamente a la conversación.

## 2. El Contrato del Plugin (`tools.py`)

Todo plugin debe exponer estas cinco funciones en su archivo `tools.py`. Andoriña buscará estas firmas para activar el módulo.

```python
def on_install(sdk):
    """
    Se ejecuta una sola vez cuando el plugin se crea o instala.
    Ideal para crear tablas en la base de datos (state.db).
    """
    sdk.db.execute("CREATE TABLE IF NOT EXISTS users (jid TEXT PRIMARY KEY, score INTEGER)")

def on_message(sdk, jid, message_text, plugin_role):
    """
    Se ejecuta cada vez que el usuario asignado envía un mensaje, ANTES de que el LLM lo procese.
    Retorna un string con contexto adicional que se inyectará de forma invisible en el prompt.
    """
    # Ejemplo: Inyectar la puntuación del jugador para que el LLM la conozca
    row = sdk.db.execute("SELECT score FROM users WHERE jid=?", [jid]).fetchone()
    score = row[0] if row else 0
    return f"INFO DEL SISTEMA: El usuario actual tiene {score} puntos."

def on_tool_call(sdk, jid, func_name, args, plugin_role):
    """
    Se ejecuta cuando la Inteligencia Artificial decide usar una herramienta de tu plugin.
    Debes devolver un string con el resultado para que el LLM sepa qué ocurrió.
    """
    if func_name == "sumar_puntos":
        puntos = args.get("puntos", 1)
        sdk.db.execute("INSERT OR REPLACE INTO users (jid, score) VALUES (?, COALESCE((SELECT score FROM users WHERE jid=?)+?, ?))", 
                       [jid, jid, puntos, puntos])
        return f"Éxito. Se sumaron {puntos} puntos."
    raise NotImplementedError(f"Herramienta {func_name} no implementada")

def on_event(sdk, event_type, payload):
    """
    Se ejecuta cuando un temporizador programado (scheduler) llega a su fin.
    """
    if event_type == "recordatorio":
        jid = payload.get("jid")
        sdk.send_message(jid, "¡Hola! Han pasado 5 minutos.")

def on_uninstall(sdk):
    """
    Limpieza antes de que el plugin sea eliminado.
    """
    pass
```

## 3. PluginSDK Reference

El `sdk` es el único puente permitido entre tu código y Andoriña. No puedes importar funciones internas de Andoriña.

| Método | Descripción | Requiere Permiso |
|---|---|---|
| `sdk.send_message(jid, text)` | Envía un mensaje de texto a un chat. | `can_send_proactive_messages` |
| `sdk.send_image(jid, path, caption)` | Envía una imagen local. | `can_send_proactive_messages` |
| `sdk.schedule_event(jid, delay_s, type, payload)` | Programa la ejecución de `on_event` en el futuro. | `can_schedule_events` |
| `sdk.cancel_event(event_id)` | Cancela un evento programado. | `can_schedule_events` |
| `sdk.get_contacts()` | Obtiene un diccionario de contactos conocidos. | `can_read_contacts` |
| `sdk.log(message)` | Registra un mensaje visible en la pestaña "Logs" del panel. | Ninguno |
| `sdk.db` | Objeto tipo `sqlite3.Connection` exclusivo para el plugin. | Ninguno |

### Memoria Dinámica (Game State)
Si tu plugin es un juego, el SDK provee métodos rápidos para el estado del jugador sin usar SQL directo:

- `sdk.get_player_state(jid)`: Devuelve un diccionario con el estado del jugador (fase, bloqueos, etc).
- `sdk.set_player_state(jid, data)`: Sobreescribe los datos del jugador.
- `sdk.block_player(jid, seconds, reason)`: Bloquea al jugador temporalmente (no puede hablar con el bot).

## 4. Guía del Sistema Híbrido (Python + LLM)

El secreto de un buen Juego/Plugin en Andoriña es la **separación estricta de responsabilidades**:

1. **Python es la Memoria y la Matemática.**
   Nunca confíes en el LLM para recordar cuánto oro tiene el jugador o si recogió una llave hace 3 días. La ventana de contexto se llena y la IA olvida o alucina.
   *Solución:* Guarda el inventario en `state.db`. En `on_message()`, lee la base de datos e inyecta al LLM: `[INVENTARIO ACTUAL: Espada, Llave roja]`.

2. **El LLM es el Narrador / Actor.**
   No escribas en Python "Le das un golpe con la espada y le quitas 5 de vida".
   *Solución:* En Python calcula el daño, guárdalo en la base de datos, y retorna al LLM: `[SISTEMA: El jugador acertó el golpe y quitó 5 de vida. El monstruo ahora tiene 10 de vida. Narra el impacto épicamente.]`.

## 5. Diseño de Juegos (Facciones, Roles y Equipos)

Puedes diseñar juegos multijugador asíncronos en grupos de WhatsApp.
En el `plugin.json` puedes definir Roles Internos:

```json
"internal_roles": {
  "dungeon_master": ["kick_player", "spawn_monster"],
  "guerrero": ["attack_melee"],
  "mago": ["cast_spell"]
}
```

Desde el Panel de Control, el administrador puede asignar estos roles a los números de teléfono de los jugadores del grupo.
Dentro de `tools.py`, el parámetro `plugin_role` te dirá si el usuario que acaba de hablar es "guerrero" o "mago", permitiéndote bloquear o permitir mecánicas de juego en `on_tool_call`.

## 6. Comandos en DM (Alternancia de Contexto)

Si un usuario tiene asignado un asistente personal (Soul) normal, pero también se ha unido a tu Juego, todo ocurre en el mismo chat privado.
Para que Andoriña no enloquezca mezclando su asistente con el juego, el usuario dispone de estos comandos nativos (tú no tienes que programarlos):

- `/play` — Activa el Sandbox de tu juego.
- `/bot` — Devuelve a Andoriña a su comportamiento normal.
- `/status` — Informa de qué modo está activo.

## 7. Eventos Asíncronos (El clima y los enemigos)

El motor asíncrono permite que tu mundo "esté vivo" aunque nadie hable.

```python
# Ejemplo: Disparar una lluvia en 2 horas
sdk.schedule_event(jid="global", delay_s=7200, type="clima", payload={"tipo": "lluvia"})

# En tu on_event:
def on_event(sdk, event_type, payload):
    if event_type == "clima":
        if payload["tipo"] == "lluvia":
            sdk.db.execute("UPDATE mundo SET clima='lloviendo'")
            sdk.send_message("12345678@g.us", "⛈️ El cielo se oscurece y empieza a llover fuertemente.")
```

## 8. Resolución de Problemas (Troubleshooting)

- **El plugin no aparece en el listado:** Revisa que el archivo `plugin.json` sea un JSON válido (sin comas sobrantes).
- **El bot no responde:** Verifica la pestaña **Logs** en el panel. Posiblemente tu `tools.py` tenga un error de sintaxis en Python o una excepción no controlada.
- **`PluginPermissionError`:** Estás intentando enviar un mensaje usando `sdk.send_message` pero no has activado `can_send_proactive_messages` en `plugin.json`.
