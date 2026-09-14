
"""Test that the plugin can be imported from expected locations."""
import sys, os, shutil
from pathlib import Path
import pytest

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


class TestPluginImports:
    """Plugin must be importable without special PYTHONPATH."""

    def test_init_imports(self, tmp_path):
        """__init__.py should import without runtime errors."""
        os.chdir(str(_PROJECT_ROOT))
        try:
            import importlib
            import __init__ as plugin
            importlib.reload(plugin)
            assert hasattr(plugin, 'register')
            assert callable(plugin.register)
        finally:
            os.chdir(os.environ.get("HOME", "/tmp"))

    def test_plugin_yaml_loads(self):
        """plugin.yaml should be valid YAML."""
        import yaml
        manifest = yaml.safe_load((_PROJECT_ROOT / "plugin.yaml").read_text())
        assert manifest["name"] == "andorina"
        assert manifest["kind"] == "backend"
        assert "provides_tools" in manifest
        assert "provides_hooks" in manifest

    def test_scripts_module_imports(self):
        """Key scripts modules should import."""
        sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))
        from common import load_env
        from utils.jids import normalize_jid
        from utils.safe_json import read_json_safe
        assert callable(load_env)
        assert callable(normalize_jid)
        assert callable(read_json_safe)

    def test_security_module_imports(self):
        """Security modules should import."""
        sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))
        from security.rbac import resolve_role
        from security.tool_guard import validate_tool_call
        assert callable(resolve_role)
        assert callable(validate_tool_call)

    def test_does_not_depend_on_skills_path(self):
        """Plugin should not require a skills/andorina path to import."""
        import __init__ as plugin
        assert not any("skills/andorina" in str(p) for p in sys.path
                       if "skills" in str(p) and "andorina" in str(p)),             "Plugin depends on legacy skills/andorina path"
