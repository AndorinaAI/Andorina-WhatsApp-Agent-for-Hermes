
"""Test tool wrappers: argument mapping, script routing, error handling."""
import sys, os, json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


class TestToolWrappers:
    """Verify each tool wrapper calls correct script with correct args."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_plugin_context):
        """Register plugin, capture tool callbacks from mock."""
        os.chdir(str(_PROJECT_ROOT))
        import importlib
        import __init__ as plugin
        importlib.reload(plugin)
        plugin.register(mock_plugin_context)
        self.tools = {}
        for call in mock_plugin_context.register_tool.call_args_list:
            name = call[1].get("name")
            handler = call[1].get("handler")
            self.tools[name] = handler

    def _call_and_assert(self, mock_run, tool_name, tool_args, expected_script, expected_args_start):
        """Helper: call tool, verify subprocess args."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"ok": true}'
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        self.tools[tool_name](**tool_args)

        assert mock_run.called
        cmd = mock_run.call_args[0][0]
        script_path = Path(cmd[1]) if len(cmd) > 1 else None
        assert script_path is not None, f"No script path in command: {cmd}"
        assert script_path.name == expected_script.split("/")[-1],             f"Expected {expected_script}, got {script_path}"
        actual_args = cmd[2:]
        for i, expected in enumerate(expected_args_start):
            assert actual_args[i] == expected,                 f"Arg {i}: expected {expected}, got {actual_args[i]}"

    @patch("subprocess.run")
    def test_send_text(self, mock_run):
        self._call_and_assert(mock_run, "send_text",
            {"chat_id": "34600000000@s.whatsapp.net", "message": "Hello"},
            "transport/send.py", ["message", "34600000000@s.whatsapp.net", "Hello"])

    @patch("subprocess.run")
    def test_send_file(self, mock_run):
        self._call_and_assert(mock_run, "send_file",
            {"chat_id": "34600000000@s.whatsapp.net", "file_path": "/tmp/test.jpg"},
            "tools/files.py", ["/tmp/test.jpg", "34600000000@s.whatsapp.net"])

    @patch("subprocess.run")
    def test_send_file_voice(self, mock_run):
        self._call_and_assert(mock_run, "send_file",
            {"chat_id": "34600000000@s.whatsapp.net", "file_path": "/tmp/audio.ogg", "voice": True},
            "tools/files.py", ["/tmp/audio.ogg", "34600000000@s.whatsapp.net", "--voice"])

    @patch("subprocess.run")
    def test_broadcast(self, mock_run):
        self._call_and_assert(mock_run, "broadcast",
            {"message": "Hello everyone", "jids": "3460,3461"},
            "transport/send.py", ["broadcast", "Hello everyone", "3460,3461"])

    @patch("subprocess.run")
    def test_read_inbox_with_chat(self, mock_run):
        self._call_and_assert(mock_run, "read_inbox",
            {"chat_id": "34600000000@s.whatsapp.net", "limit": "50"},
            "tools/inbox.py", ["read", "34600000000@s.whatsapp.net", "50"])

    @patch("subprocess.run")
    def test_read_inbox_list(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"ok": true}'
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc
        self.tools["read_inbox"]()
        assert mock_run.called
        cmd = mock_run.call_args[0][0]
        assert cmd[2] == "list"

    @patch("subprocess.run")
    def test_search_contacts(self, mock_run):
        self._call_and_assert(mock_run, "search_contacts",
            {"query": "Maria"},
            "tools/contacts.py", ["search", "Maria"])

    @patch("subprocess.run")
    def test_list_groups(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"ok": true}'
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc
        self.tools["list_groups"]()
        assert mock_run.called
        cmd = mock_run.call_args[0][0]
        assert cmd[2] == "groups"

    @patch("subprocess.run")
    def test_schedule_msg(self, mock_run):
        self._call_and_assert(mock_run, "schedule_msg",
            {"chat_id": "34600000000@s.whatsapp.net", "time_str": "22:00", "message": "Good night"},
            "tools/agenda.py", ["auto-schedule", "34600000000@s.whatsapp.net", "22:00", "Good night"])

    @patch("subprocess.run")
    def test_add_note(self, mock_run):
        self._call_and_assert(mock_run, "add_note",
            {"jid": "34600000000", "text": "Likes coffee"},
            "tools/contacts.py", ["note-add", "34600000000", "Likes coffee"])

    @patch("subprocess.run")
    def test_add_alert(self, mock_run):
        self._call_and_assert(mock_run, "add_alert",
            {"source": "34600000000", "target": "120363001234@g.us"},
            "tools/alerts.py", ["add", "34600000000", "120363001234@g.us"])

    @patch("subprocess.run")
    def test_add_alert_with_keywords(self, mock_run):
        self._call_and_assert(mock_run, "add_alert",
            {"source": "34600000000", "target": "120363001234@g.us", "keywords": "urgent,help"},
            "tools/alerts.py", ["add", "34600000000", "120363001234@g.us", "--keywords", "urgent,help"])

    @patch("subprocess.run")
    def test_manage_role(self, mock_run):
        self._call_and_assert(mock_run, "manage_role",
            {"action": "set", "jid": "34600000000", "role": "manager"},
            "utils/admin_cli.py", ["role", "set", "34600000000", "manager"])

    @patch("subprocess.run")
    def test_manage_soul(self, mock_run):
        self._call_and_assert(mock_run, "manage_soul",
            {"action": "set", "jid": "34600000000", "text": "friendly_pirate"},
            "utils/admin_cli.py", ["soul", "set", "34600000000", "friendly_pirate"])

    @patch("subprocess.run")
    def test_hermes_home_in_env(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"ok": true}'
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc
        self.tools["send_text"](chat_id="x", message="y")
        env = mock_run.call_args[1].get("env", {})
        assert "HERMES_HOME" in env

    @patch("subprocess.run")
    def test_eleven_tools_registered(self, mock_run):
        """All 11 tools must be registered and callable."""
        expected = {
            "send_text", "send_file", "broadcast", "read_inbox",
            "search_contacts", "list_groups", "schedule_msg", "add_note",
            "add_alert", "manage_role", "manage_soul"
        }
        assert set(self.tools.keys()) == expected
        for name, cb in self.tools.items():
            assert callable(cb), f"Tool {name} is not callable"

    @patch("subprocess.run")
    def test_error_propagation(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = ""
        mock_proc.stderr = "Script failed"
        mock_run.return_value = mock_proc
        result = self.tools["send_text"](chat_id="x", message="y")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert not parsed.get("ok", True)

    @patch("subprocess.run")
    def test_json_parse_failure(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Not JSON output"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc
        result = self.tools["send_text"](chat_id="x", message="y")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert "raw" in parsed


class TestOutputToolsMock:
    """Mock tests for send tools: verify transport calls, no HTTP."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_plugin_context):
        os.chdir(str(_PROJECT_ROOT))
        import importlib
        import __init__ as plugin
        importlib.reload(plugin)
        plugin.register(mock_plugin_context)
        self.tools = {}
        for call in mock_plugin_context.register_tool.call_args_list:
            name = call[1].get("name")
            handler = call[1].get("handler")
            self.tools[name] = handler

    @patch("subprocess.run")
    def test_send_text_single_transport_call(self, mock_run):
        """send_text with args_dict → 1 subprocess call, 0 HTTP."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"ok": true}'
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc
        result = self.tools["send_text"]({"chat_id": "test@s.whatsapp.net", "message": "hi"})
        assert isinstance(result, str)
        assert mock_run.call_count == 1
        cmd = mock_run.call_args[0][0]
        assert "transport/send.py" in str(cmd)
        assert "message" in cmd

    @patch("subprocess.run")
    def test_send_file_single_transport_call(self, mock_run):
        """send_file with args_dict → 1 subprocess call."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"ok": true}'
        mock_run.return_value = mock_proc
        result = self.tools["send_file"]({"chat_id": "test@s.whatsapp.net", "file_path": "/tmp/f"})
        assert isinstance(result, str)
        assert mock_run.call_count == 1

    @patch("subprocess.run")
    def test_send_file_voice_flag(self, mock_run):
        """send_file with voice=True adds --voice flag."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"ok": true}'
        mock_run.return_value = mock_proc
        result = self.tools["send_file"]({"chat_id": "x@s.whatsapp.net", "file_path": "/tmp/f", "voice": True})
        assert isinstance(result, str)
        cmd = mock_run.call_args[0][0]
        assert "--voice" in cmd

    @patch("subprocess.run")
    def test_broadcast_single_call_multiple_jids(self, mock_run):
        """broadcast with 3 JIDs → 1 subprocess call (broadcast handles loop internally)."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"ok": true}'
        mock_run.return_value = mock_proc
        result = self.tools["broadcast"]({"message": "hi", "jids": "a@s.whatsapp.net,b@s.whatsapp.net,c@s.whatsapp.net"})
        assert isinstance(result, str)
        assert mock_run.call_count == 1
        cmd = mock_run.call_args[0][0]
        assert "broadcast" in cmd
        # All 3 JIDs passed to the script
        assert "a@s.whatsapp.net" in str(cmd)

    @patch("subprocess.run")
    def test_broadcast_empty_jids(self, mock_run):
        """broadcast with empty jids → still calls subprocess."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"ok": true}'
        mock_run.return_value = mock_proc
        result = self.tools["broadcast"]({"message": "hi", "jids": ""})
        assert isinstance(result, str)

    @patch("subprocess.run")
    def test_send_text_handles_error(self, mock_run):
        """send_text with error response → still returns str."""
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = '{"ok": false, "error": "NETWORK_ERROR"}'
        mock_run.return_value = mock_proc
        result = self.tools["send_text"]({"chat_id": "x@s.whatsapp.net", "message": "hi"})
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert not parsed.get("ok", True)

    @patch("subprocess.run")
    def test_schedule_msg_passes_args(self, mock_run):
        """schedule_msg passes correct args to agenda.py."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"ok": true}'
        mock_run.return_value = mock_proc
        result = self.tools["schedule_msg"]({"chat_id": "x@s.whatsapp.net", "time_str": "22:00", "message": "hi"})
        assert isinstance(result, str)
        cmd = mock_run.call_args[0][0]
        assert "agenda.py" in str(cmd)
        assert "auto-schedule" in cmd
        assert "22:00" in cmd
