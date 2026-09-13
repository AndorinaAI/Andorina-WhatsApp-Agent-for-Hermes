"""Shared fixtures for Andoriña V2.0 tests."""
import sys, os, shutil, tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

@pytest.fixture
def project_root():
    return _PROJECT_ROOT

@pytest.fixture
def temp_home():
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        home.mkdir()
        old = os.environ.get("HOME")
        os.environ["HOME"] = str(home)
        yield home
        if old: os.environ["HOME"] = old

@pytest.fixture
def mock_plugin_context():
    ctx = MagicMock()
    ctx.register_hook = MagicMock()
    ctx.register_tool = MagicMock()
    ctx.register_middleware = MagicMock()
    return ctx

@pytest.fixture
def fake_subprocess():
    with patch("subprocess.run") as m:
        p = MagicMock()
        p.returncode = 0
        p.stdout = '{"ok": true}'
        p.stderr = ""
        m.return_value = p
        yield m
