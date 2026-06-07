import sys
import json
import inspect
from pathlib import Path
import importlib.util

sys.path.append(str(Path(__file__).parent.parent))
from utils.plugin_sdk import PluginSDK

STATE_DIR = Path(__file__).parent.parent.parent / "state"
SOULS_DIR = STATE_DIR / "souls"

class PluginContractError(Exception):
    pass

def load_plugin(plugin_name: str) -> dict:
    """Intenta cargar un plugin. Devuelve {sdk: PluginSDK, tools: module, config: dict} o None."""
    plugin_dir = SOULS_DIR / plugin_name
    plugin_json_path = plugin_dir / "plugin.json"
    tools_py_path = plugin_dir / "tools.py"
    
    if not plugin_json_path.exists() or not tools_py_path.exists():
        return None
        
    try:
        config = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading plugin.json for {plugin_name}: {e}")
        return None
        
    # Cargar módulo Python dinámicamente
    spec = importlib.util.spec_from_file_location(f"plugin_{plugin_name}", tools_py_path)
    if not spec or not spec.loader:
        return None
    tools_module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(tools_module)
    except Exception as e:
        print(f"Error loading tools.py for {plugin_name}: {e}")
        return None
        
    # Validar contrato mínimo
    required_funcs = ["on_install", "on_uninstall", "on_message", "on_tool_call", "on_event"]
    for func in required_funcs:
        if not hasattr(tools_module, func):
            raise PluginContractError(f"Plugin '{plugin_name}' is missing required function '{func}'")
            
    permissions = config.get("permissions", {})
    sdk = PluginSDK(plugin_dir, plugin_name, permissions)
    
    return {
        "sdk": sdk,
        "tools": tools_module,
        "config": config
    }

def route_on_message(plugin_name: str, jid: str, message_text: str, plugin_role: str):
    plugin = load_plugin(plugin_name)
    if not plugin:
        return None
    try:
        return plugin["tools"].on_message(plugin["sdk"], jid, message_text, plugin_role)
    except Exception as e:
        plugin["sdk"].log(f"Error in on_message: {e}")
        return None

def route_on_tool_call(plugin_name: str, jid: str, func_name: str, args: dict, plugin_role: str):
    plugin = load_plugin(plugin_name)
    if not plugin:
        return "ERROR: Plugin not found or disabled."
    try:
        return plugin["tools"].on_tool_call(plugin["sdk"], jid, func_name, args, plugin_role)
    except NotImplementedError as e:
        return f"ERROR: {str(e)}"
    except Exception as e:
        plugin["sdk"].log(f"Error in on_tool_call ({func_name}): {e}")
        return f"ERROR: Plugin execution failed: {e}"

def route_on_install(plugin_name: str):
    plugin = load_plugin(plugin_name)
    if plugin:
        try:
            plugin["tools"].on_install(plugin["sdk"])
            return True
        except Exception as e:
            plugin["sdk"].log(f"Error in on_install: {e}")
    return False

def get_plugin_role(plugin_config: dict, group_config: dict, user_jid: str) -> str:
    """Resuelve el rol de un usuario dentro de un plugin."""
    user_num = user_jid.split("@")[0]
    plugin_roles = group_config.get("plugin_roles", {})
    if user_num in plugin_roles:
        return plugin_roles[user_num]
    # Default: si es el dueño, podría ser admin, si no, player.
    return "player"
