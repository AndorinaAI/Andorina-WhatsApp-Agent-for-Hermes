
"""Test hook callbacks: stdin piping, JSON serialization, error handling."""
import sys, os, json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


class TestHooks:
    """Verify hook callbacks pipe payload correctly to orchestrator_hook.py."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_plugin_context):
        """Register plugin to create hook callbacks, then capture them."""
        os.chdir(str(_PROJECT_ROOT))
        import importlib
        import __init__ as plugin
        importlib.reload(plugin)
        plugin.register(mock_plugin_context)
        self.ctx = mock_plugin_context
        # Extract hook callbacks from the mock
        self.hooks = {}
        for call_args in mock_plugin_context.register_hook.call_args_list:
            name, callback = call_args[0]
            self.hooks[name] = callback

    def test_three_hooks_registered(self):
        """Exactly 3 hooks should be registered."""
        assert len(self.hooks) == 3
        assert "pre_llm_call" in self.hooks
        assert "pre_tool_call" in self.hooks
        assert "post_llm_call" in self.hooks

    def test_all_hooks_are_callable(self):
        """All hook callbacks must be callable."""
        for name, cb in self.hooks.items():
            assert callable(cb), f"Hook {name} is not callable"

    @patch("subprocess.run")
    def test_hook_pipes_json_to_stdin(self, mock_run):
        """Hook should pass kwargs as JSON to subprocess stdin."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"action": "allow"}'
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        payload = {"hook_event_name": "pre_llm_call", "user_id": "test_user"}
        result = self.hooks["pre_llm_call"](**payload)

        assert mock_run.called
        input_data = mock_run.call_args[1].get("input")
        assert input_data is not None
        parsed = json.loads(input_data)
        assert parsed["hook_event_name"] == "pre_llm_call"
        assert parsed["user_id"] == "test_user"

    @patch("subprocess.run")
    def test_hook_returns_parsed_json(self, mock_run):
        """Hook should return parsed JSON from orchestrator_hook.py stdout."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{"action": "block", "message": "test rejection"}'
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result = self.hooks["pre_llm_call"](test=True)
        assert result == {"action": "block", "message": "test rejection"}

    @patch("subprocess.run")
    def test_hook_handles_non_json_stdout(self, mock_run):
        """Non-JSON stdout should return empty dict."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Not JSON"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result = self.hooks["pre_llm_call"]()
        assert result == {}

    @patch("subprocess.run")
    def test_hook_handles_subprocess_error(self, mock_run):
        """Subprocess crash should return empty dict, not raise."""
        mock_run.side_effect = Exception("Boom")
        result = self.hooks["pre_llm_call"]()
        assert result == {}

    @patch("subprocess.run")
    def test_all_three_hooks_pipe_correctly(self, mock_run):
        """All 3 hooks should pipe via subprocess."""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = '{}'
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        self.hooks["pre_llm_call"](event="pre_llm_call")
        self.hooks["pre_tool_call"](event="pre_tool_call")
        self.hooks["post_llm_call"](event="post_llm_call")

        assert mock_run.call_count == 3
        for call_args in mock_run.call_args_list:
            input_data = call_args[1].get("input")
            assert input_data is not None
            parsed = json.loads(input_data)
            assert "event" in parsed
