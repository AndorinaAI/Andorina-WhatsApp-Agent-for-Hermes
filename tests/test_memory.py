"""Test memory backends: Noop, Hermes, auto-detection."""
import sys, os
from pathlib import Path
from unittest.mock import patch
import pytest

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))


class TestNoopBackend:
    """Noop backend is always available as safe fallback."""

    def test_noop_constructible(self):
        from security.memory.backend import NoopBackend
        b = NoopBackend()
        assert b.get_name() == "NoopBackend"

    def test_noop_search(self):
        from security.memory.backend import NoopBackend
        b = NoopBackend()
        result = b.search(jid="test", query="anything")
        assert isinstance(result, list)

    def test_noop_purge_does_not_crash(self):
        from security.memory.backend import NoopBackend
        b = NoopBackend()
        b.purge(jid="test")  # should not raise

    def test_noop_get_status(self):
        from security.memory.backend import NoopBackend
        b = NoopBackend()
        status = b.get_status()
        assert isinstance(status, dict)


class TestMemoryDetector:
    """Auto-detection should fall back to Noop when nothing is available."""

    def test_detect_returns_backend(self):
        from security.memory.detector import detect_memory_backend
        backend = detect_memory_backend()
        assert backend is not None

    def test_get_memory_backend_singleton(self):
        from security.memory.detector import get_memory_backend, reset_memory_backend
        reset_memory_backend()
        b1 = get_memory_backend()
        b2 = get_memory_backend()
        assert b1 is b2

    def test_reset_memory_backend(self):
        from security.memory.detector import get_memory_backend, reset_memory_backend
        reset_memory_backend()
        b1 = get_memory_backend()
        reset_memory_backend()
        b2 = get_memory_backend()
        assert b1 is not b2


class TestHermesMemoryBackend:
    """Hermes native memory backend."""

    def test_hermes_backend_imports(self):
        from security.memory.hermes_memory import HermesMemoryBackend
        assert HermesMemoryBackend is not None

    def test_hermes_backend_not_available_without_binary(self):
        from security.memory.hermes_memory import HermesMemoryBackend
        with patch('shutil.which', return_value=None):
            b = HermesMemoryBackend()
            assert not b.is_available()
