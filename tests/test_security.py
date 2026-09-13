
"""F3 Security tests: _hermes_ guard, path traversal, OAuth credentials."""
import sys, os, json, tempfile, shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))


class TestHermesGuard:
    """S3: _hermes_ bypass protection."""

    def test_normal_soul_allowed(self):
        from utils import admin_cli
        with patch('utils.admin_cli.out') as mock_out,              patch('utils.admin_cli.read_json_safe', return_value={}),              patch('utils.admin_cli.write_json_safe'),              patch('utils.admin_cli.normalize_jid', return_value='34600000000@s.whatsapp.net'),              patch('utils.admin_cli.clean_number', return_value='34600000000'):
            admin_cli.cmd_soul_set('34600000000', 'friendly_pirate')
            assert mock_out.called
            assert 'FORBIDDEN' not in str(mock_out.call_args)

    def test_hermes_soul_rejected(self):
        from utils import admin_cli
        with patch('utils.admin_cli.out') as mock_out,              patch('utils.admin_cli.read_json_safe', return_value={}),              patch('utils.admin_cli.write_json_safe'),              patch('utils.admin_cli.normalize_jid', return_value='34600000000@s.whatsapp.net'),              patch('utils.admin_cli.clean_number', return_value='34600000000'):
            admin_cli.cmd_soul_set('34600000000', '_hermes_')
            result = mock_out.call_args[0][0]
            assert result['status'] == 'DENY'
            assert result['error_code'] == 'FORBIDDEN'

    def test_hermes_whitespace_rejected(self):
        from utils import admin_cli
        with patch('utils.admin_cli.out') as mock_out,              patch('utils.admin_cli.read_json_safe', return_value={}),              patch('utils.admin_cli.write_json_safe'),              patch('utils.admin_cli.normalize_jid', return_value='34600000000@s.whatsapp.net'),              patch('utils.admin_cli.clean_number', return_value='34600000000'):
            admin_cli.cmd_soul_set('34600000000', '  _hermes_  ')
            result = mock_out.call_args[0][0]
            assert result['status'] == 'DENY'

    def test_hermes_uppercase_rejected(self):
        from utils import admin_cli
        with patch('utils.admin_cli.out') as mock_out,              patch('utils.admin_cli.read_json_safe', return_value={}),              patch('utils.admin_cli.write_json_safe'),              patch('utils.admin_cli.normalize_jid', return_value='34600000000@s.whatsapp.net'),              patch('utils.admin_cli.clean_number', return_value='34600000000'):
            admin_cli.cmd_soul_set('34600000000', '_HERMES_')
            result = mock_out.call_args[0][0]
            assert result['status'] == 'DENY'

    def test_normal_after_rejection(self):
        from utils import admin_cli
        with patch('utils.admin_cli.out') as mock_out,              patch('utils.admin_cli.read_json_safe', return_value={}),              patch('utils.admin_cli.write_json_safe'),              patch('utils.admin_cli.normalize_jid', return_value='34600000000@s.whatsapp.net'),              patch('utils.admin_cli.clean_number', return_value='34600000000'):
            # First: _hermes_ rejected
            admin_cli.cmd_soul_set('34600000000', '_hermes_')
            mock_out.reset_mock()
            # Then: normal should still work
            admin_cli.cmd_soul_set('34600000001', 'helpful')
            assert mock_out.called
            assert 'FORBIDDEN' not in str(mock_out.call_args)


class TestPathTraversal:
    """S4: Path traversal protection in notes."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from tools import contacts
        self.contacts = contacts
        self.original_notes = contacts.NOTES_DIR
        self.tmpdir = Path(tempfile.mkdtemp())
        contacts.NOTES_DIR = self.tmpdir / 'notes'
        contacts.NOTES_DIR.mkdir(parents=True, exist_ok=True)
        yield
        contacts.NOTES_DIR = self.original_notes
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_normal_dm_path(self):
        path = self.contacts._notes_path('34600000000')
        assert str(path).startswith(str(self.contacts.NOTES_DIR))

    def test_normal_group_path(self):
        path = self.contacts._notes_path('34600000000', '120363001234@g.us')
        assert str(path).startswith(str(self.contacts.NOTES_DIR))
        assert '__in__' in str(path)

    def test_num_traversal_blocked(self):
        with pytest.raises(ValueError):
            self.contacts._notes_path('x/../../etc')

    def test_group_traversal_blocked(self):
        with pytest.raises(ValueError):
            self.contacts._notes_path('34600000000', 'x/../../etc@g.us')

    def test_absolute_path_blocked(self):
        with pytest.raises(ValueError):
            self.contacts._notes_path('/etc/passwd')

    def test_deep_traversal_blocked(self):
        with pytest.raises(ValueError):
            self.contacts._notes_path('a/b/../../../etc')

    def test_null_byte_blocked(self):
        with pytest.raises(ValueError):
            self.contacts._notes_path('34600000000\x00/etc')

    def test_normal_after_rejections(self):
        # After rejecting bad paths, good paths still work
        try:
            self.contacts._notes_path('/etc/passwd')
        except ValueError:
            pass
        path = self.contacts._notes_path('34600000001')
        assert str(path).startswith(str(self.contacts.NOTES_DIR))


class TestOAuthCredentials:
    """S5: OAuth credentials no longer hardcoded."""

    def test_default_cid_removed(self):
        import utils.auth as auth_mod
        assert not hasattr(auth_mod, 'DEFAULT_CID')

    def test_default_sec_removed(self):
        import utils.auth as auth_mod
        assert not hasattr(auth_mod, 'DEFAULT_SEC')

    def test_auth_module_imports(self):
        import utils.auth
        assert True

    def test_env_example_has_credentials(self):
        from common import load_env
        env_ex = _PROJECT_ROOT / '.env.example'
        vars = load_env(env_ex)
        assert vars.get('GOOGLE_CONTACTS_CLIENT_ID'), "Missing CLIENT_ID in .env.example"
        assert vars.get('GOOGLE_CONTACTS_CLIENT_SECRET'), "Missing CLIENT_SECRET in .env.example"

    def test_no_hardcoded_creds_in_scripts(self):
        import subprocess
        r = subprocess.run(
            ['grep', '-r', 'DEFAULT_CID|DEFAULT_SEC',
             str(_PROJECT_ROOT / 'scripts')],
            capture_output=True, text=True
        )
        assert r.returncode != 0, f"Hardcoded creds found: {r.stdout[:200]}"
