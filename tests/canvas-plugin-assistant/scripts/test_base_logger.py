"""Tests for base_logger module."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from base_logger import BaseLogger
from hook_information import HookInformation


# Concrete subclass for testing run() method
class ConcreteLogger(BaseLogger):
    """Concrete implementation for testing BaseLogger."""

    @classmethod
    def session_directory(cls, hook_info: HookInformation) -> Path:
        return hook_info.workspace_dir / ".cpa-workflow-artifacts" / "test-logs"

    @classmethod
    def extraction(cls, hook_info: HookInformation) -> dict:
        return {"extracted_key": "extracted_value"}

    @classmethod
    def aggregation(cls, session_directory: Path) -> None:
        pass


class TestHookInformation:
    """Tests for hook_information class method."""

    @patch("base_logger.PluginDir")
    @patch("base_logger.json")
    def test_hook_information__success(self, mock_json, mock_plugin_dir):
        """Test hook_information with valid JSON input returns HookInformation."""
        mock_json.load.side_effect = [
            {
                "session_id": "abc123",
                "reason": "completed",
                "transcript_path": "/tmp/transcript.json",
                "cwd": "/home/user/project",
            }
        ]
        mock_json.JSONDecodeError = json.JSONDecodeError
        mock_plugin_dir.run.side_effect = [Path("/workspace")]

        result = BaseLogger.hook_information()

        expected = HookInformation(
            session_id="abc123",
            exit_reason="completed",
            transcript_path=Path("/tmp/transcript.json"),
            working_directory=Path("/home/user/project"),
            workspace_dir=Path("/workspace"),
        )
        assert result == expected

        exp_json_calls = [call.load(sys.stdin)]
        assert mock_json.mock_calls == exp_json_calls

        exp_plugin_dir_calls = [call.run()]
        assert mock_plugin_dir.mock_calls == exp_plugin_dir_calls

    @patch("base_logger.sys")
    @patch("base_logger.PluginDir")
    @patch("base_logger.json")
    @patch("builtins.print")
    def test_hook_information__json_decode_error(
        self, mock_print, mock_json, mock_plugin_dir, mock_sys
    ):
        """Test hook_information with invalid JSON triggers error and exit."""
        mock_json.load.side_effect = [json.JSONDecodeError("test error", "doc", 0)]
        mock_json.JSONDecodeError = json.JSONDecodeError
        mock_sys.stdin = sys.stdin
        mock_sys.stderr = sys.stderr
        mock_sys.exit.side_effect = [SystemExit(1)]

        with pytest.raises(SystemExit):
            BaseLogger.hook_information()

        exp_print_calls = [
            call("Error parsing hook input: test error: line 1 column 1 (char 0)", file=sys.stderr)
        ]
        assert mock_print.mock_calls == exp_print_calls

        exp_sys_calls = [call.exit(1)]
        assert mock_sys.mock_calls == exp_sys_calls


class TestRun:
    """Tests for run class method."""

    @patch("base_logger.sys")
    @patch("base_logger.datetime")
    @patch("builtins.open")
    @patch("builtins.print")
    @patch("base_logger.json")
    def test_run__success(
        self, mock_json, mock_print, mock_open, mock_datetime, mock_sys
    ):
        """Test run creates directory, writes JSON, calls extraction/aggregation, exits 0."""
        mock_file = MagicMock()
        mock_open.return_value.__enter__ = MagicMock(side_effect=[mock_file])
        mock_open.return_value.__exit__ = MagicMock(side_effect=[None])

        # Mock datetime.now() to return a fixed datetime
        fixed_datetime = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        mock_datetime.now.side_effect = [fixed_datetime]
        mock_datetime.timezone = timezone

        mock_json.dump.side_effect = [None]
        mock_sys.stderr = sys.stderr
        mock_sys.exit.side_effect = [SystemExit(0)]

        hook_info = HookInformation(
            session_id="session123",
            exit_reason="completed",
            transcript_path=Path("/tmp/transcript.json"),
            working_directory=Path("/home/user/project"),
            workspace_dir=Path("/workspace"),
        )

        with patch.object(Path, "mkdir") as mock_mkdir:
            mock_mkdir.side_effect = [None]

            with pytest.raises(SystemExit):
                ConcreteLogger.run(hook_info)

            exp_mkdir_calls = [call(parents=True, exist_ok=True)]
            assert mock_mkdir.mock_calls == exp_mkdir_calls

        exp_datetime_calls = [call.now(timezone.utc)]
        assert mock_datetime.mock_calls == exp_datetime_calls

        exp_open_calls = [
            call(
                Path("/workspace/.cpa-workflow-artifacts/test-logs/session123.json"),
                "w",
            ),
            call().__enter__(),
            call().__exit__(None, None, None),
        ]
        assert mock_open.mock_calls == exp_open_calls

        exp_json_calls = [
            call.dump(
                {
                    "session_id": "session123",
                    "timestamp": "2024-01-15T10:30:00+00:00",
                    "exit_reason": "completed",
                    "working_directory": "/home/user/project",
                    "transcript_path": "/tmp/transcript.json",
                    "extracted_key": "extracted_value",
                },
                mock_file,
                indent=2,
            )
        ]
        assert mock_json.mock_calls == exp_json_calls

        exp_print_calls = [
            call(
                "Session data saved to: /workspace/.cpa-workflow-artifacts/test-logs/session123.json",
                file=sys.stderr,
            )
        ]
        assert mock_print.mock_calls == exp_print_calls

        exp_sys_calls = [call.exit(0)]
        assert mock_sys.mock_calls == exp_sys_calls

    @patch("base_logger.sys")
    @patch("builtins.open")
    @patch("builtins.print")
    def test_run__write_error(self, mock_print, mock_open, mock_sys):
        """Test run with write error triggers error message and exit 1."""
        mock_open.side_effect = [PermissionError("Permission denied")]
        mock_sys.stderr = sys.stderr
        mock_sys.exit.side_effect = [SystemExit(1)]

        hook_info = HookInformation(
            session_id="session456",
            exit_reason="error",
            transcript_path=Path("/tmp/transcript.json"),
            working_directory=Path("/home/user/project"),
            workspace_dir=Path("/workspace"),
        )

        with patch.object(Path, "mkdir") as mock_mkdir:
            mock_mkdir.side_effect = [None]

            with pytest.raises(SystemExit):
                ConcreteLogger.run(hook_info)

            exp_mkdir_calls = [call(parents=True, exist_ok=True)]
            assert mock_mkdir.mock_calls == exp_mkdir_calls

        exp_open_calls = [
            call(
                Path("/workspace/.cpa-workflow-artifacts/test-logs/session456.json"),
                "w",
            )
        ]
        assert mock_open.mock_calls == exp_open_calls

        exp_print_calls = [
            call("Error writing session data: Permission denied", file=sys.stderr)
        ]
        assert mock_print.mock_calls == exp_print_calls

        exp_sys_calls = [call.exit(1)]
        assert mock_sys.mock_calls == exp_sys_calls


class TestSessionDirectory:
    """Tests for session_directory abstract method."""

    def test_session_directory(self):
        """Test session_directory raises NotImplementedError."""
        hook_info = HookInformation(
            session_id="test123",
            exit_reason="completed",
            transcript_path=Path("/tmp/transcript.json"),
            working_directory=Path("/home/user/project"),
            workspace_dir=Path("/workspace"),
        )

        with pytest.raises(NotImplementedError):
            BaseLogger.session_directory(hook_info)


class TestExtraction:
    """Tests for extraction abstract method."""

    def test_extraction(self):
        """Test extraction raises NotImplementedError."""
        hook_info = HookInformation(
            session_id="test123",
            exit_reason="completed",
            transcript_path=Path("/tmp/transcript.json"),
            working_directory=Path("/home/user/project"),
            workspace_dir=Path("/workspace"),
        )

        with pytest.raises(NotImplementedError):
            BaseLogger.extraction(hook_info)


class TestAggregation:
    """Tests for aggregation abstract method."""

    def test_aggregation(self):
        """Test aggregation raises NotImplementedError."""
        tested = Path("/workspace/.cpa-workflow-artifacts/test-logs")

        with pytest.raises(NotImplementedError):
            BaseLogger.aggregation(tested)
