
"""Test plugin entry point: register(ctx), manifest compatibility."""
import sys, os, json, yaml
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


class TestRegister:
    """Tests for register(ctx) entry point."""

    def test_register_runs_without_crashing(self, mock_plugin_context):
        """register(ctx) should execute without exceptions."""
        os.chdir(str(_PROJECT_ROOT))
        try:
            import importlib
            import __init__ as plugin
            importlib.reload(plugin)
            plugin.register(mock_plugin_context)
        finally:
            os.chdir(os.environ.get("HOME", "/tmp"))

    def test_registers_11_tools(self, mock_plugin_context):
        """Must register exactly 11 tools."""
        os.chdir(str(_PROJECT_ROOT))
        try:
            import importlib
            import __init__ as plugin
            importlib.reload(plugin)
            plugin.register(mock_plugin_context)
        finally:
            os.chdir(os.environ.get("HOME", "/tmp"))
        
        tool_calls = mock_plugin_context.register_tool.call_args_list
        registered_names = {c[0][0] for c in tool_calls}
        expected = {
            "send_text", "send_file", "broadcast", "read_inbox",
            "search_contacts", "list_groups", "schedule_msg", "add_note",
            "add_alert", "manage_role", "manage_soul"
        }
        assert registered_names == expected, f"Missing/extra tools: {registered_names ^ expected}"
        assert len(tool_calls) == 11

    def test_registers_3_hooks(self, mock_plugin_context):
        """Must register exactly 3 hooks."""
        os.chdir(str(_PROJECT_ROOT))
        try:
            import importlib
            import __init__ as plugin
            importlib.reload(plugin)
            plugin.register(mock_plugin_context)
        finally:
            os.chdir(os.environ.get("HOME", "/tmp"))
        
        hook_calls = mock_plugin_context.register_hook.call_args_list
        registered_hooks = {c[0][0] for c in hook_calls}
        expected = {"pre_llm_call", "pre_tool_call", "post_llm_call"}
        assert registered_hooks == expected
        assert len(hook_calls) == 3

    def test_no_duplicate_registrations(self, mock_plugin_context):
        """Each tool/hook should be registered exactly once."""
        os.chdir(str(_PROJECT_ROOT))
        try:
            import importlib
            import __init__ as plugin
            importlib.reload(plugin)
            plugin.register(mock_plugin_context)
        finally:
            os.chdir(os.environ.get("HOME", "/tmp"))
        
        tool_names = [c[0][0] for c in mock_plugin_context.register_tool.call_args_list]
        hook_names = [c[0][0] for c in mock_plugin_context.register_hook.call_args_list]
        assert len(tool_names) == len(set(tool_names)), f"Duplicate tools: {tool_names}"
        assert len(hook_names) == len(set(hook_names)), f"Duplicate hooks: {hook_names}"

    def test_register_does_not_require_whatsapp(self, mock_plugin_context):
        """register(ctx) must not need WhatsApp runtime."""
        os.chdir(str(_PROJECT_ROOT))
        try:
            import importlib
            import __init__ as plugin
            importlib.reload(plugin)
            # Should not crash even without Hermes/WhatsApp running
            plugin.register(mock_plugin_context)
        finally:
            os.chdir(os.environ.get("HOME", "/tmp"))

    def test_register_does_not_depend_on_cwd(self, mock_plugin_context, tmp_path):
        """register(ctx) works from any directory."""
        os.chdir(str(tmp_path))
        try:
            import importlib
            import __init__ as plugin
            importlib.reload(plugin)
            plugin.register(mock_plugin_context)
        finally:
            os.chdir(os.environ.get("HOME", "/tmp"))
        
        assert mock_plugin_context.register_tool.called
        assert mock_plugin_context.register_hook.called

    def test_all_tools_are_callable(self, mock_plugin_context):
        """Each registered tool callback must be callable."""
        os.chdir(str(_PROJECT_ROOT))
        try:
            import importlib
            import __init__ as plugin
            importlib.reload(plugin)
            plugin.register(mock_plugin_context)
        finally:
            os.chdir(os.environ.get("HOME", "/tmp"))
        
        for call_args in mock_plugin_context.register_tool.call_args_list:
            _, callback = call_args[0]
            assert callable(callback), f"Tool {call_args[0][0]} callback is not callable"

    def test_all_hooks_are_callable(self, mock_plugin_context):
        """Each registered hook callback must be callable."""
        os.chdir(str(_PROJECT_ROOT))
        try:
            import importlib
            import __init__ as plugin
            importlib.reload(plugin)
            plugin.register(mock_plugin_context)
        finally:
            os.chdir(os.environ.get("HOME", "/tmp"))
        
        for call_args in mock_plugin_context.register_hook.call_args_list:
            _, callback = call_args[0]
            assert callable(callback), f"Hook {call_args[0][0]} callback is not callable"


class TestPluginYamlCompatibility:
    """Verify plugin.yaml declarations match register(ctx) registrations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.yaml_path = _PROJECT_ROOT / "plugin.yaml"
        self.manifest = yaml.safe_load(self.yaml_path.read_text())

    def test_tools_declared_match_registered(self, mock_plugin_context):
        """Every declared tool must be registered, and vice versa."""
        os.chdir(str(_PROJECT_ROOT))
        try:
            import importlib
            import __init__ as plugin
            importlib.reload(plugin)
            plugin.register(mock_plugin_context)
        finally:
            os.chdir(os.environ.get("HOME", "/tmp"))
        
        declared = set(self.manifest.get("provides_tools", []))
        registered = {c[0][0] for c in mock_plugin_context.register_tool.call_args_list}
        
        missing_decl = registered - declared
        missing_reg = declared - registered
        assert not missing_decl, f"Tools registered but not declared: {missing_decl}"
        assert not missing_reg, f"Tools declared but not registered: {missing_reg}"
        assert declared == registered

    def test_hooks_declared_match_registered(self, mock_plugin_context):
        """Every declared hook must be registered, and vice versa."""
        os.chdir(str(_PROJECT_ROOT))
        try:
            import importlib
            import __init__ as plugin
            importlib.reload(plugin)
            plugin.register(mock_plugin_context)
        finally:
            os.chdir(os.environ.get("HOME", "/tmp"))
        
        declared = set(self.manifest.get("provides_hooks", []))
        registered = {c[0][0] for c in mock_plugin_context.register_hook.call_args_list}
        
        missing_decl = registered - declared
        missing_reg = declared - registered
        assert not missing_decl, f"Hooks registered but not declared: {missing_decl}"
        assert not missing_reg, f"Hooks declared but not registered: {missing_reg}"
        assert declared == registered
