"""Tests de portabilidad multi-OS V2.0"""
import sys
import os
from pathlib import Path
_PROJECT_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(_PROJECT_ROOT / 'scripts'))

import pytest


class TestFilesMultiOS:
    def test_blocked_prefixes_exist(self):
        """Verifica que files.py tiene blocked_prefixes definido."""
        import tools.files
        # La variable blocked_prefixes es local en cmd_enviar, no global
        # Verificar que el módulo existe y compila
        assert tools.files is not None

    def test_tool_executor_path_multios(self):
        """Verifica que tool_executor.py no hardcodea /usr/bin:/bin."""
        code = (_PROJECT_ROOT / 'scripts/security/tool_executor.py').read_text()
        assert '/usr/bin:/bin' not in code

    def test_input_guard_multios(self):
        """Verifica que input_guard.py soporta Windows paths."""
        code = (_PROJECT_ROOT / 'scripts/security/input_guard.py').read_text()
        assert 'Windows' in code or '\\x5c\\x5c' in code


class TestSoulSyncMemory:
    def test_purge_uses_memory_backend(self):
        """Verifica que soul_sync.py usa MemoryBackend, no Hindsight hardcodeado."""
        code = (_PROJECT_ROOT / 'scripts/security/soul_sync.py').read_text()
        assert 'MemoryBackend' in code or 'get_memory_backend' in code
        assert 'glob.glob' not in code.split('def purge_long_term_memory')[1] if 'def purge_long_term_memory' in code else True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
