# Andoriña V2.0 — Developer Guide

Welcome to the official documentation for Andoriña Sandbox, Game, and Plugin developers.

The Andoriña V2 system allows extending the assistant through independent modules without modifying the bot core, ensuring full compatibility and preventing cascade failures.

## 1. Quick Start Guide (Your first Plugin in 10 minutes)

1. Open the Andoriña web panel.
2. Go to the **Sandboxes** tab.
3. Click **Create Plugin (Advanced Mode)** and give it a name, e.g.: `MyFirstPlugin`.
4. In the configuration, ensure you check the necessary permissions, e.g. `can_send_proactive_messages`.
5. Go to the **Code** tab and you'll see a pre-generated `tools.py` file. This file is the heart of your plugin.
6. Go to the **Assignment** tab and assign it to your own WhatsApp number or a test group.
7. Done! Everything you write in the code will immediately affect the conversation.

## 2. The Plugin Contract (`tools.py`)

Every plugin must expose these five functions in its `tools.py` file. Andoriña will look for these signatures to activate the module.

### Required Functions

- `on_message(jid, text, chat_type)` — Called when a message is received
- `on_tool_call(tool_name, args)` — Called before a tool executes
- `get_system_prompt(jid)` — Returns custom system prompt for the user
- `get_tools()` — Returns list of custom tools the plugin provides
- `get_hooks()` — Returns list of lifecycle hooks

## 3. Sandbox Architecture

Sandboxes are isolated execution environments for plugins. Each sandbox has:
- Its own directory under `state/souls/<name>/`
- A `tools.py` file with the plugin logic
- Configurable permissions via the web panel
- Assignment to specific users or groups

## 4. Hermes Plugin System (V2 Native)

Andoriña V2 itself is a native Hermes backend plugin (`kind: backend`). See:
- `DEVELOPER_HANDOFF.md` — Project architecture and current state
- `ARCHITECTURE.md` — Complete system architecture
- `MIGRATION.md` — V1 to V2 migration guide

### Key APIs

```python
def register(ctx):
    ctx.register_tool(name="...", toolset="andorina", schema={...}, handler=...)
    ctx.register_hook("pre_llm_call", callback)
    ctx.register_hook("pre_tool_call", callback)
    ctx.register_hook("post_llm_call", callback)
```

## 5. Testing

```bash
cd ~/Documentos/andorinaDEV/Andorina-WhatsApp-Agent-for-Hermes
pytest tests/
hermes plugins validate .
hermes plugins doctor . --ci
```

Current baseline: 105 tests passing, plugin validation passed.
