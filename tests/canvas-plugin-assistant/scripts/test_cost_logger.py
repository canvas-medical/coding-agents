"""Tests for CostsLogger module."""

import json
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from base_logger import BaseLogger
from cost_logger import CostsLogger
from hook_information import HookInformation


def test_inheritance() -> None:
    """Verify CostsLogger inherits from BaseLogger."""
    assert issubclass(CostsLogger, BaseLogger)


class TestLoadPricing:
    """Tests for the load_pricing method."""

    @patch("cost_logger.json.load")
    @patch("cost_logger.Path")
    def test_load_pricing__success(self, mock_path_cls, mock_json_load) -> None:
        """Test load_pricing returns converted pricing data."""
        mock_file = MagicMock()
        mock_pricing_file = MagicMock()
        mock_pricing_file.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_pricing_file.open.return_value.__exit__ = MagicMock(return_value=False)
        # Path(__file__).parent.parent / "model_costs.json"
        mock_path_cls.return_value.parent.parent.__truediv__.return_value = mock_pricing_file

        mock_json_load.side_effect = [{
            "models": {
                "claude-sonnet-4-5": {
                    "input": 3.0,
                    "output": 15.0,
                    "cache_write": 3.75,
                    "cache_read": 0.30,
                }
            }
        }]

        tested = CostsLogger
        result = tested.load_pricing()

        expected = {
            "claude-sonnet-4-5": {
                "input": 3.0 / 1_000_000,
                "output": 15.0 / 1_000_000,
                "cache_write": 3.75 / 1_000_000,
                "cache_read": 0.30 / 1_000_000,
            }
        }
        assert result == expected

        exp_json_load_calls = [call(mock_file)]
        assert mock_json_load.mock_calls == exp_json_load_calls

    @patch("cost_logger.sys")
    @patch("cost_logger.Path")
    def test_load_pricing__file_not_found(self, mock_path_cls, mock_sys) -> None:
        """Test load_pricing returns empty dict when file not found."""
        mock_pricing_file = MagicMock()
        mock_pricing_file.open.side_effect = [FileNotFoundError()]
        mock_path_cls.return_value.parent.parent.__truediv__.return_value = mock_pricing_file

        tested = CostsLogger
        result = tested.load_pricing()

        expected = {}
        assert result == expected

        exp_sys_calls = [
            call.stderr.write("Warning: Pricing file not found at " + str(mock_pricing_file)),
            call.stderr.write("\n"),
        ]
        assert mock_sys.mock_calls == exp_sys_calls

    @patch("cost_logger.sys")
    @patch("cost_logger.json.load")
    @patch("cost_logger.Path")
    def test_load_pricing__json_decode_error(self, mock_path_cls, mock_json_load, mock_sys) -> None:
        """Test load_pricing returns empty dict on JSONDecodeError."""
        mock_file = MagicMock()
        mock_pricing_file = MagicMock()
        mock_pricing_file.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_pricing_file.open.return_value.__exit__ = MagicMock(return_value=False)
        mock_path_cls.return_value.parent.parent.__truediv__.return_value = mock_pricing_file

        mock_json_load.side_effect = [json.JSONDecodeError("test error", "doc", 0)]

        tested = CostsLogger
        result = tested.load_pricing()

        expected = {}
        assert result == expected

        exp_json_load_calls = [call(mock_file)]
        assert mock_json_load.mock_calls == exp_json_load_calls

    @patch("cost_logger.sys")
    @patch("cost_logger.json.load")
    @patch("cost_logger.Path")
    def test_load_pricing__key_error(self, mock_path_cls, mock_json_load, mock_sys) -> None:
        """Test load_pricing returns empty dict on KeyError."""
        mock_file = MagicMock()
        mock_pricing_file = MagicMock()
        mock_pricing_file.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        mock_pricing_file.open.return_value.__exit__ = MagicMock(return_value=False)
        mock_path_cls.return_value.parent.parent.__truediv__.return_value = mock_pricing_file

        mock_json_load.side_effect = [{
            "models": {
                "claude-sonnet": {
                    "input": 3.0,
                    # Missing "output", "cache_write", "cache_read"
                }
            }
        }]

        tested = CostsLogger
        result = tested.load_pricing()

        expected = {}
        assert result == expected


class TestDetectModelFromTranscript:
    """Tests for the detect_model_from_transcript method."""

    @pytest.mark.parametrize(
        ("messages", "expected"),
        [
            pytest.param(
                [{"model": "claude-sonnet-4-5-20250929"}],
                "claude-sonnet-4-5-20250929",
                id="direct_model",
            ),
            pytest.param(
                [{"message": {"model": "claude-opus-4-5-20251101"}}],
                "claude-opus-4-5-20251101",
                id="nested_in_message",
            ),
            pytest.param(
                [{"metadata": {"model": "claude-haiku-3-5-20250929"}}],
                "claude-haiku-3-5-20250929",
                id="in_metadata",
            ),
            pytest.param(
                [{"other": "data"}, {"content": "text"}],
                None,
                id="not_found",
            ),
            pytest.param(
                [],
                None,
                id="empty_messages",
            ),
            pytest.param(
                ["not a dict", {"model": "claude-sonnet"}],
                "claude-sonnet",
                id="skips_non_dict",
            ),
            pytest.param(
                [{"message": "not a dict"}, {"model": "claude-opus"}],
                "claude-opus",
                id="message_not_dict",
            ),
            pytest.param(
                [{"metadata": "not a dict"}, {"model": "claude-haiku"}],
                "claude-haiku",
                id="metadata_not_dict",
            ),
            pytest.param(
                [{"message": {"other": "data"}}, {"model": "claude-sonnet"}],
                "claude-sonnet",
                id="message_dict_no_model",
            ),
            pytest.param(
                [{"metadata": {"other": "data"}}, {"model": "claude-opus"}],
                "claude-opus",
                id="metadata_dict_no_model",
            ),
            pytest.param(
                [{"message": {"other": "data"}, "metadata": {"model": "claude-haiku"}}],
                "claude-haiku",
                id="message_no_model_metadata_has_model",
            ),
        ],
    )
    def test_detect_model_from_transcript(self, messages: list, expected: str | None) -> None:
        """Test detect_model_from_transcript with various message formats."""
        tested = CostsLogger
        result = tested.detect_model_from_transcript(messages)

        assert result == expected


class TestCalculateCost:
    """Tests for the calculate_cost method."""

    @patch.object(CostsLogger, "load_pricing")
    def test_calculate_cost__known_model(self, mock_load_pricing) -> None:
        """Test calculate_cost with known model returns correct cost."""
        mock_load_pricing.side_effect = [{
            "claude-sonnet-4-5": {
                "input": 0.000003,
                "output": 0.000015,
                "cache_write": 0.00000375,
                "cache_read": 0.0000003,
            }
        }]

        tested = CostsLogger
        token_counts = {
            "input": 1000,
            "output": 500,
            "cache_write": 200,
            "cache_read": 300,
        }
        result = tested.calculate_cost(token_counts, "claude-sonnet-4-5")

        # (1000 * 0.000003) + (500 * 0.000015) + (200 * 0.00000375) + (300 * 0.0000003)
        # = 0.003 + 0.0075 + 0.00075 + 0.00009 = 0.01134
        expected = 0.01134
        assert result == expected

        exp_load_pricing_calls = [call()]
        assert mock_load_pricing.mock_calls == exp_load_pricing_calls

    @patch.object(CostsLogger, "load_pricing")
    def test_calculate_cost__versioned_model(self, mock_load_pricing) -> None:
        """Test calculate_cost normalizes versioned model names."""
        mock_load_pricing.side_effect = [{
            "claude-sonnet-4-5": {
                "input": 0.000003,
                "output": 0.000015,
                "cache_write": 0.00000375,
                "cache_read": 0.0000003,
            }
        }]

        tested = CostsLogger
        token_counts = {"input": 1000, "output": 0, "cache_write": 0, "cache_read": 0}
        result = tested.calculate_cost(token_counts, "claude-sonnet-4-5-20250929")

        expected = 0.003
        assert result == expected

        exp_load_pricing_calls = [call()]
        assert mock_load_pricing.mock_calls == exp_load_pricing_calls

    @patch.object(CostsLogger, "load_pricing")
    def test_calculate_cost__unknown_model(self, mock_load_pricing) -> None:
        """Test calculate_cost returns None for unknown model."""
        mock_load_pricing.side_effect = [{
            "claude-sonnet-4-5": {"input": 0.000003, "output": 0.000015, "cache_write": 0.00000375, "cache_read": 0.0000003}
        }]

        tested = CostsLogger
        token_counts = {"input": 1000, "output": 500, "cache_write": 0, "cache_read": 0}
        result = tested.calculate_cost(token_counts, "unknown-model")

        expected = None
        assert result is expected

        exp_load_pricing_calls = [call()]
        assert mock_load_pricing.mock_calls == exp_load_pricing_calls

    @patch.object(CostsLogger, "load_pricing")
    def test_calculate_cost__empty_pricing(self, mock_load_pricing) -> None:
        """Test calculate_cost returns None when pricing is empty."""
        mock_load_pricing.side_effect = [{}]

        tested = CostsLogger
        token_counts = {"input": 1000, "output": 500, "cache_write": 0, "cache_read": 0}
        result = tested.calculate_cost(token_counts, "claude-sonnet-4-5")

        expected = None
        assert result is expected

    @patch.object(CostsLogger, "load_pricing")
    def test_calculate_cost__missing_token_counts(self, mock_load_pricing) -> None:
        """Test calculate_cost handles missing token count keys."""
        mock_load_pricing.side_effect = [{
            "claude-sonnet-4-5": {
                "input": 0.000003,
                "output": 0.000015,
                "cache_write": 0.00000375,
                "cache_read": 0.0000003,
            }
        }]

        tested = CostsLogger
        token_counts = {}  # Empty dict - should default to 0 for all
        result = tested.calculate_cost(token_counts, "claude-sonnet-4-5")

        expected = 0.0
        assert result == expected


class TestParseTimestamp:
    """Tests for the parse_timestamp method."""

    @pytest.mark.parametrize(
        ("timestamp_str", "expected_year", "expected_month", "expected_day"),
        [
            pytest.param("2024-01-15T10:30:45.123456Z", 2024, 1, 15, id="format_with_microseconds_z"),
            pytest.param("2024-02-20T14:00:00Z", 2024, 2, 20, id="format_without_microseconds"),
            pytest.param("2024-03-25T08:15:30.500000+00:00", 2024, 3, 25, id="format_with_timezone_offset"),
            pytest.param("2024-04-10T12:45:00", 2024, 4, 10, id="fromisoformat_fallback"),
        ],
    )
    def test_parse_timestamp__valid_formats(
        self, timestamp_str: str, expected_year: int, expected_month: int, expected_day: int
    ) -> None:
        """Test parse_timestamp handles various valid timestamp formats."""
        tested = CostsLogger
        result = tested.parse_timestamp(timestamp_str)

        assert result is not None
        assert result.year == expected_year
        assert result.month == expected_month
        assert result.day == expected_day

    def test_parse_timestamp__invalid_format(self) -> None:
        """Test parse_timestamp returns None for invalid format."""
        tested = CostsLogger
        result = tested.parse_timestamp("not-a-timestamp")

        expected = None
        assert result is expected


class TestSessionDirectory:
    """Tests for the session_directory method."""

    def test_session_directory(self) -> None:
        """Test session_directory returns correct path."""
        hook_info = HookInformation(
            session_id="test-session-123",
            exit_reason="user_exit",
            transcript_path=Path("/tmp/transcript.jsonl"),
            workspace_dir=Path("/home/user/project"),
            working_directory=Path("/home/user/project/src"),
        )

        tested = CostsLogger
        result = tested.session_directory(hook_info)

        expected = Path("/home/user/project/.cpa-workflow-artifacts/costs")
        assert result == expected


class TestExtraction:
    """Tests for the extraction method."""

    @patch.object(CostsLogger, "calculate_cost")
    @patch.object(CostsLogger, "detect_model_from_transcript")
    @patch.object(CostsLogger, "parse_timestamp")
    def test_extraction__full_transcript(
        self, mock_parse_timestamp, mock_detect_model, mock_calculate_cost
    ) -> None:
        """Test extraction with full transcript data."""
        mock_detect_model.side_effect = ["claude-sonnet-4-5-20250929"]
        mock_parse_timestamp.side_effect = [
            datetime(2024, 1, 15, 10, 0, 0),
            datetime(2024, 1, 15, 10, 5, 30),
        ]
        mock_calculate_cost.side_effect = [0.0123]

        transcript_content = (
            '{"timestamp": "2024-01-15T10:00:00Z", "message": {"usage": {"input_tokens": 100, "output_tokens": 50, "cache_read_input_tokens": 10, "cache_creation_input_tokens": 5}}}\n'
            '{"timestamp": "2024-01-15T10:05:30Z", "message": {"usage": {"input_tokens": 200, "output_tokens": 100, "cache_read_input_tokens": 20, "cache_creation_input_tokens": 10}}}\n'
        )

        mock_file = StringIO(transcript_content)
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        hook_info.transcript_path.open.return_value.__exit__ = MagicMock(return_value=False)

        tested = CostsLogger
        result = tested.extraction(hook_info)

        assert "cost_data" in result
        cost_data = result["cost_data"]
        assert cost_data["message_count"] == 2
        assert cost_data["model"] == "claude-sonnet-4-5-20250929"
        assert cost_data["duration_seconds"] == 330.0
        assert cost_data["duration_formatted"] == "5m 30s"
        assert cost_data["total_tokens"]["input"] == 300
        assert cost_data["total_tokens"]["output"] == 150
        assert cost_data["cache_usage"]["cache_read"] == 30
        assert cost_data["cache_usage"]["cache_write"] == 15
        assert cost_data["cost_usd"] == 0.0123
        assert cost_data["cost_formatted"] == "$0.0123"

        exp_detect_model_calls = [call([
            {"timestamp": "2024-01-15T10:00:00Z", "message": {"usage": {"input_tokens": 100, "output_tokens": 50, "cache_read_input_tokens": 10, "cache_creation_input_tokens": 5}}},
            {"timestamp": "2024-01-15T10:05:30Z", "message": {"usage": {"input_tokens": 200, "output_tokens": 100, "cache_read_input_tokens": 20, "cache_creation_input_tokens": 10}}},
        ])]
        assert mock_detect_model.mock_calls == exp_detect_model_calls

        exp_calculate_cost_calls = [call(
            {"input": 300, "output": 150, "cache_read": 30, "cache_write": 15},
            "claude-sonnet-4-5-20250929"
        )]
        assert mock_calculate_cost.mock_calls == exp_calculate_cost_calls

    @patch.object(CostsLogger, "detect_model_from_transcript")
    def test_extraction__minimal_transcript(self, mock_detect_model) -> None:
        """Test extraction with minimal transcript data (no model, no tokens)."""
        mock_detect_model.side_effect = [None]

        transcript_content = '{"content": "Hello"}\n'

        mock_file = StringIO(transcript_content)
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        hook_info.transcript_path.open.return_value.__exit__ = MagicMock(return_value=False)

        tested = CostsLogger
        result = tested.extraction(hook_info)

        assert "cost_data" in result
        cost_data = result["cost_data"]
        assert cost_data["message_count"] == 1
        assert "model" not in cost_data
        assert "total_tokens" not in cost_data
        assert "cost_usd" not in cost_data

    def test_extraction__parse_error(self) -> None:
        """Test extraction handles file read errors."""
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.side_effect = [IOError("Cannot read file")]

        tested = CostsLogger
        result = tested.extraction(hook_info)

        assert "cost_data" in result
        cost_data = result["cost_data"]
        assert "transcript_parse_error" in cost_data
        assert "Cannot read file" in cost_data["transcript_parse_error"]

    @patch.object(CostsLogger, "detect_model_from_transcript")
    def test_extraction__invalid_json_line(self, mock_detect_model) -> None:
        """Test extraction skips invalid JSON lines."""
        mock_detect_model.side_effect = [None]

        transcript_content = 'not valid json\n{"content": "valid"}\n'

        mock_file = StringIO(transcript_content)
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        hook_info.transcript_path.open.return_value.__exit__ = MagicMock(return_value=False)

        tested = CostsLogger
        result = tested.extraction(hook_info)

        assert result["cost_data"]["message_count"] == 1

    @patch.object(CostsLogger, "calculate_cost")
    @patch.object(CostsLogger, "detect_model_from_transcript")
    def test_extraction__cost_not_available(self, mock_detect_model, mock_calculate_cost) -> None:
        """Test extraction handles cost calculation returning None."""
        mock_detect_model.side_effect = ["unknown-model"]
        mock_calculate_cost.side_effect = [None]

        transcript_content = '{"usage": {"input_tokens": 100, "output_tokens": 50}}\n'

        mock_file = StringIO(transcript_content)
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        hook_info.transcript_path.open.return_value.__exit__ = MagicMock(return_value=False)

        tested = CostsLogger
        result = tested.extraction(hook_info)

        cost_data = result["cost_data"]
        assert "cost_usd" not in cost_data
        assert "cost_calculation_note" in cost_data
        assert "Pricing not available for model: unknown-model" in cost_data["cost_calculation_note"]

    @patch.object(CostsLogger, "detect_model_from_transcript")
    @patch.object(CostsLogger, "parse_timestamp")
    def test_extraction__duration_hours(self, mock_parse_timestamp, mock_detect_model) -> None:
        """Test extraction formats duration with hours correctly."""
        mock_detect_model.side_effect = [None]
        mock_parse_timestamp.side_effect = [
            datetime(2024, 1, 15, 10, 0, 0),
            datetime(2024, 1, 15, 12, 30, 45),
        ]

        transcript_content = '{"timestamp": "2024-01-15T10:00:00Z"}\n{"timestamp": "2024-01-15T12:30:45Z"}\n'

        mock_file = StringIO(transcript_content)
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        hook_info.transcript_path.open.return_value.__exit__ = MagicMock(return_value=False)

        tested = CostsLogger
        result = tested.extraction(hook_info)

        cost_data = result["cost_data"]
        assert cost_data["duration_formatted"] == "2h 30m 45s"

    @patch.object(CostsLogger, "detect_model_from_transcript")
    @patch.object(CostsLogger, "parse_timestamp")
    def test_extraction__duration_seconds_only(self, mock_parse_timestamp, mock_detect_model) -> None:
        """Test extraction formats duration with seconds only."""
        mock_detect_model.side_effect = [None]
        mock_parse_timestamp.side_effect = [
            datetime(2024, 1, 15, 10, 0, 0),
            datetime(2024, 1, 15, 10, 0, 45),
        ]

        transcript_content = '{"timestamp": "2024-01-15T10:00:00Z"}\n{"timestamp": "2024-01-15T10:00:45Z"}\n'

        mock_file = StringIO(transcript_content)
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        hook_info.transcript_path.open.return_value.__exit__ = MagicMock(return_value=False)

        tested = CostsLogger
        result = tested.extraction(hook_info)

        cost_data = result["cost_data"]
        assert cost_data["duration_formatted"] == "45s"

    @patch.object(CostsLogger, "detect_model_from_transcript")
    def test_extraction__usage_directly_in_message(self, mock_detect_model) -> None:
        """Test extraction handles usage directly in message (not nested)."""
        mock_detect_model.side_effect = [None]

        transcript_content = '{"usage": {"input_tokens": 100, "output_tokens": 50}}\n'

        mock_file = StringIO(transcript_content)
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        hook_info.transcript_path.open.return_value.__exit__ = MagicMock(return_value=False)

        tested = CostsLogger
        result = tested.extraction(hook_info)

        cost_data = result["cost_data"]
        assert cost_data["total_tokens"]["input"] == 100
        assert cost_data["total_tokens"]["output"] == 50

    @patch.object(CostsLogger, "detect_model_from_transcript")
    def test_extraction__empty_lines_skipped(self, mock_detect_model) -> None:
        """Test extraction skips empty lines in transcript."""
        mock_detect_model.side_effect = [None]

        transcript_content = '{"content": "valid"}\n\n   \n{"content": "also_valid"}\n'

        mock_file = StringIO(transcript_content)
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        hook_info.transcript_path.open.return_value.__exit__ = MagicMock(return_value=False)

        tested = CostsLogger
        result = tested.extraction(hook_info)

        # Only 2 messages should be parsed (empty lines skipped)
        assert result["cost_data"]["message_count"] == 2

    @patch.object(CostsLogger, "detect_model_from_transcript")
    @patch.object(CostsLogger, "parse_timestamp")
    def test_extraction__timestamp_parse_returns_none(self, mock_parse_timestamp, mock_detect_model) -> None:
        """Test extraction handles parse_timestamp returning None."""
        mock_detect_model.side_effect = [None]
        mock_parse_timestamp.side_effect = [None, datetime(2024, 1, 15, 10, 0, 0)]

        transcript_content = '{"timestamp": "invalid"}\n{"timestamp": "2024-01-15T10:00:00Z"}\n'

        mock_file = StringIO(transcript_content)
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        hook_info.transcript_path.open.return_value.__exit__ = MagicMock(return_value=False)

        tested = CostsLogger
        result = tested.extraction(hook_info)

        # Only one valid timestamp, so no duration
        assert "duration_seconds" not in result["cost_data"]

    @patch.object(CostsLogger, "detect_model_from_transcript")
    def test_extraction__non_dict_in_messages_for_usage(self, mock_detect_model) -> None:
        """Test extraction handles non-dict items in messages during usage extraction."""
        mock_detect_model.side_effect = [None]

        # Second item is not a valid JSON object but a string
        transcript_content = '{"usage": {"input_tokens": 100, "output_tokens": 50}}\n"just a string"\n'

        mock_file = StringIO(transcript_content)
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        hook_info.transcript_path.open.return_value.__exit__ = MagicMock(return_value=False)

        tested = CostsLogger
        result = tested.extraction(hook_info)

        # Should still get usage from first message
        assert result["cost_data"]["total_tokens"]["input"] == 100

    @patch.object(CostsLogger, "detect_model_from_transcript")
    def test_extraction__message_dict_without_usage(self, mock_detect_model) -> None:
        """Test extraction handles message dict that has no usage key."""
        mock_detect_model.side_effect = [None]

        # Message is dict but has no "usage" key
        transcript_content = '{"message": {"other": "data"}}\n{"usage": {"input_tokens": 50, "output_tokens": 25}}\n'

        mock_file = StringIO(transcript_content)
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        hook_info.transcript_path.open.return_value.__exit__ = MagicMock(return_value=False)

        tested = CostsLogger
        result = tested.extraction(hook_info)

        # Should still get usage from second message
        assert result["cost_data"]["total_tokens"]["input"] == 50
        assert result["cost_data"]["total_tokens"]["output"] == 25

    @patch.object(CostsLogger, "detect_model_from_transcript")
    def test_extraction__zero_tokens(self, mock_detect_model) -> None:
        """Test extraction handles usage with zero tokens (no total_tokens created)."""
        mock_detect_model.side_effect = [None]

        # Usage exists but with zero tokens
        transcript_content = '{"usage": {"other_field": "value"}}\n'

        mock_file = StringIO(transcript_content)
        hook_info = HookInformation(
            session_id="test-session",
            exit_reason="user_exit",
            transcript_path=MagicMock(),
            workspace_dir=Path("/workspace"),
            working_directory=Path("/workspace/src"),
        )
        hook_info.transcript_path.open.return_value.__enter__ = MagicMock(return_value=mock_file)
        hook_info.transcript_path.open.return_value.__exit__ = MagicMock(return_value=False)

        tested = CostsLogger
        result = tested.extraction(hook_info)

        # token_usage_details should exist but total_tokens should not (no input/output)
        assert "token_usage_details" in result["cost_data"]
        assert "total_tokens" not in result["cost_data"]


class TestAggregation:
    """Tests for the aggregation method."""

    @patch("cost_logger.datetime")
    @patch("cost_logger.json.dump")
    @patch("cost_logger.json.load")
    @patch("cost_logger.open", new_callable=mock_open)
    @patch("cost_logger.sys")
    def test_aggregation__success(
        self, mock_sys, mock_open_func, mock_json_load, mock_json_dump, mock_datetime
    ) -> None:
        """Test aggregation creates summary file from session files."""
        mock_datetime.now.return_value.isoformat.side_effect = ["2024-01-15T12:00:00+00:00"]

        session_dir = MagicMock(spec=Path)
        session_dir.parent = MagicMock(spec=Path)
        aggregated_file = MagicMock(spec=Path)
        aggregated_file.exists.side_effect = [False]
        session_dir.parent.__truediv__.side_effect = [aggregated_file]

        session_file_1 = MagicMock(spec=Path)
        session_file_2 = MagicMock(spec=Path)
        session_dir.glob.side_effect = [[session_file_1, session_file_2]]

        mock_json_load.side_effect = [
            {
                "session_id": "session-1",
                "timestamp": "2024-01-15T10:00:00Z",
                "cost_data": {
                    "duration_formatted": "5m",
                    "cost_usd": 0.01,
                    "total_tokens": {"input": 100, "output": 50, "total": 150},
                    "cache_usage": {"cache_write": 10, "cache_read": 5},
                }
            },
            {
                "session_id": "session-2",
                "timestamp": "2024-01-15T11:00:00Z",
                "cost_data": {
                    "duration_formatted": "10m",
                    "cost_usd": 0.02,
                    "total_tokens": {"input": 200, "output": 100, "total": 300},
                    "cache_usage": {"cache_write": 20, "cache_read": 10},
                }
            },
        ]

        tested = CostsLogger
        result = tested.aggregation(session_dir)

        expected = None
        assert result is expected

        exp_json_dump_calls = [call(
            {
                "created_date": "2024-01-15T12:00:00+00:00",
                "last_update": "2024-01-15T12:00:00+00:00",
                "session_count": 2,
                "total_tokens": {"input": 300, "output": 150, "total": 450},
                "cache_usage": {"cache_write": 30, "cache_read": 15},
                "cost_usd": 0.03,
                "cost_formatted": "$0.0300",
                "sessions": [
                    {"session_id": "session-1", "date": "2024-01-15T10:00:00Z", "duration": "5m", "cost_usd": 0.01},
                    {"session_id": "session-2", "date": "2024-01-15T11:00:00Z", "duration": "10m", "cost_usd": 0.02},
                ]
            },
            mock_open_func.return_value.__enter__.return_value,
            indent=2
        )]
        assert mock_json_dump.mock_calls == exp_json_dump_calls

    @patch("cost_logger.datetime")
    @patch("cost_logger.json.dump")
    @patch("cost_logger.json.load")
    @patch("cost_logger.open", new_callable=mock_open)
    @patch("cost_logger.sys")
    def test_aggregation__preserves_created_date(
        self, mock_sys, mock_open_func, mock_json_load, mock_json_dump, mock_datetime
    ) -> None:
        """Test aggregation preserves existing created_date."""
        mock_datetime.now.return_value.isoformat.side_effect = ["2024-01-16T12:00:00+00:00"]

        session_dir = MagicMock(spec=Path)
        session_dir.parent = MagicMock(spec=Path)
        aggregated_file = MagicMock(spec=Path)
        aggregated_file.exists.side_effect = [True]
        session_dir.parent.__truediv__.side_effect = [aggregated_file]

        session_file = MagicMock(spec=Path)
        session_dir.glob.side_effect = [[session_file]]

        mock_json_load.side_effect = [
            {"created_date": "2024-01-10T08:00:00+00:00"},  # Existing aggregation file
            {
                "session_id": "session-1",
                "timestamp": "2024-01-16T10:00:00Z",
                "cost_data": {"cost_usd": 0.05, "total_tokens": {"input": 500, "output": 250, "total": 750}},
            },
        ]

        tested = CostsLogger
        result = tested.aggregation(session_dir)

        expected = None
        assert result is expected

        # Verify created_date is preserved
        exp_json_dump_calls = [call(
            {
                "created_date": "2024-01-10T08:00:00+00:00",  # Preserved!
                "last_update": "2024-01-16T12:00:00+00:00",
                "session_count": 1,
                "total_tokens": {"input": 500, "output": 250, "total": 750},
                "cache_usage": {"cache_write": 0, "cache_read": 0},
                "cost_usd": 0.05,
                "cost_formatted": "$0.0500",
                "sessions": [
                    {"session_id": "session-1", "date": "2024-01-16T10:00:00Z", "duration": None, "cost_usd": 0.05},
                ]
            },
            mock_open_func.return_value.__enter__.return_value,
            indent=2
        )]
        assert mock_json_dump.mock_calls == exp_json_dump_calls

    @patch("cost_logger.sys")
    def test_aggregation__failure(self, mock_sys) -> None:
        """Test aggregation handles exceptions gracefully."""
        session_dir = MagicMock(spec=Path)
        session_dir.parent.__truediv__.side_effect = [Exception("Disk error")]

        tested = CostsLogger
        result = tested.aggregation(session_dir)

        expected = None
        assert result is expected

        exp_sys_calls = [
            call.stderr.write("Warning: Failed to aggregate data: Disk error"),
            call.stderr.write("\n"),
        ]
        assert mock_sys.mock_calls == exp_sys_calls

    @patch("cost_logger.datetime")
    @patch("cost_logger.json.dump")
    @patch("cost_logger.json.load")
    @patch("cost_logger.open", new_callable=mock_open)
    @patch("cost_logger.sys")
    def test_aggregation__empty_directory(
        self, mock_sys, mock_open_func, mock_json_load, mock_json_dump, mock_datetime
    ) -> None:
        """Test aggregation handles empty directory."""
        mock_datetime.now.return_value.isoformat.side_effect = ["2024-01-15T12:00:00+00:00"]

        session_dir = MagicMock(spec=Path)
        session_dir.parent = MagicMock(spec=Path)
        aggregated_file = MagicMock(spec=Path)
        aggregated_file.exists.side_effect = [False]
        session_dir.parent.__truediv__.side_effect = [aggregated_file]
        session_dir.glob.side_effect = [[]]  # No files

        tested = CostsLogger
        result = tested.aggregation(session_dir)

        expected = None
        assert result is expected

        exp_json_dump_calls = [call(
            {
                "created_date": "2024-01-15T12:00:00+00:00",
                "last_update": "2024-01-15T12:00:00+00:00",
                "session_count": 0,
                "total_tokens": {"input": 0, "output": 0, "total": 0},
                "cache_usage": {"cache_write": 0, "cache_read": 0},
                "cost_usd": 0.0,
                "cost_formatted": "$0.0000",
                "sessions": []
            },
            mock_open_func.return_value.__enter__.return_value,
            indent=2
        )]
        assert mock_json_dump.mock_calls == exp_json_dump_calls

    @patch("cost_logger.datetime")
    @patch("cost_logger.json.dump")
    @patch("cost_logger.json.load")
    @patch("cost_logger.open", new_callable=mock_open)
    @patch("cost_logger.sys")
    def test_aggregation__existing_file_read_error(
        self, mock_sys, mock_open_func, mock_json_load, mock_json_dump, mock_datetime
    ) -> None:
        """Test aggregation handles error reading existing aggregation file."""
        mock_datetime.now.return_value.isoformat.side_effect = ["2024-01-15T12:00:00+00:00"]

        session_dir = MagicMock(spec=Path)
        session_dir.parent = MagicMock(spec=Path)
        aggregated_file = MagicMock(spec=Path)
        aggregated_file.exists.side_effect = [True]
        session_dir.parent.__truediv__.side_effect = [aggregated_file]
        session_dir.glob.side_effect = [[]]

        # First call (reading existing file) raises error, no subsequent calls
        mock_json_load.side_effect = [json.JSONDecodeError("Invalid", "doc", 0)]

        tested = CostsLogger
        result = tested.aggregation(session_dir)

        expected = None
        assert result is expected

        # Should still create new aggregation file with new created_date
        exp_json_dump_calls = [call(
            {
                "created_date": "2024-01-15T12:00:00+00:00",  # New date since existing file couldn't be read
                "last_update": "2024-01-15T12:00:00+00:00",
                "session_count": 0,
                "total_tokens": {"input": 0, "output": 0, "total": 0},
                "cache_usage": {"cache_write": 0, "cache_read": 0},
                "cost_usd": 0.0,
                "cost_formatted": "$0.0000",
                "sessions": []
            },
            mock_open_func.return_value.__enter__.return_value,
            indent=2
        )]
        assert mock_json_dump.mock_calls == exp_json_dump_calls

    @patch("cost_logger.datetime")
    @patch("cost_logger.json.dump")
    @patch("cost_logger.json.load")
    @patch("cost_logger.open", new_callable=mock_open)
    @patch("cost_logger.sys")
    def test_aggregation__session_with_null_date(
        self, mock_sys, mock_open_func, mock_json_load, mock_json_dump, mock_datetime
    ) -> None:
        """Test aggregation handles sessions with null dates in sorting."""
        mock_datetime.now.return_value.isoformat.side_effect = ["2024-01-15T12:00:00+00:00"]

        session_dir = MagicMock(spec=Path)
        session_dir.parent = MagicMock(spec=Path)
        aggregated_file = MagicMock(spec=Path)
        aggregated_file.exists.side_effect = [False]
        session_dir.parent.__truediv__.side_effect = [aggregated_file]

        session_file_1 = MagicMock(spec=Path)
        session_file_2 = MagicMock(spec=Path)
        session_dir.glob.side_effect = [[session_file_1, session_file_2]]

        mock_json_load.side_effect = [
            {"session_id": "session-1", "timestamp": None, "cost_data": {}},
            {"session_id": "session-2", "timestamp": "2024-01-15T11:00:00Z", "cost_data": {}},
        ]

        tested = CostsLogger
        result = tested.aggregation(session_dir)

        expected = None
        assert result is expected

        # Verify sessions are sorted with null dates first (empty string comparison)
        call_args = mock_json_dump.call_args
        sessions = call_args[0][0]["sessions"]
        assert sessions[0]["session_id"] == "session-1"  # null date comes first
        assert sessions[1]["session_id"] == "session-2"

    @patch("cost_logger.datetime")
    @patch("cost_logger.json.dump")
    @patch("cost_logger.json.load")
    @patch("cost_logger.open", new_callable=mock_open)
    @patch("cost_logger.sys")
    def test_aggregation__total_tokens_not_dict(
        self, mock_sys, mock_open_func, mock_json_load, mock_json_dump, mock_datetime
    ) -> None:
        """Test aggregation handles total_tokens that is not a dict."""
        mock_datetime.now.return_value.isoformat.side_effect = ["2024-01-15T12:00:00+00:00"]

        session_dir = MagicMock(spec=Path)
        session_dir.parent = MagicMock(spec=Path)
        aggregated_file = MagicMock(spec=Path)
        aggregated_file.exists.side_effect = [False]
        session_dir.parent.__truediv__.side_effect = [aggregated_file]

        session_file = MagicMock(spec=Path)
        session_dir.glob.side_effect = [[session_file]]

        # total_tokens is a number instead of a dict
        mock_json_load.side_effect = [
            {
                "session_id": "session-1",
                "timestamp": "2024-01-15T10:00:00Z",
                "cost_data": {
                    "total_tokens": 500,  # Not a dict!
                    "cost_usd": 0.01,
                }
            },
        ]

        tested = CostsLogger
        result = tested.aggregation(session_dir)

        expected = None
        assert result is expected

        # Verify total_tokens remains at 0 since the value wasn't a dict
        call_args = mock_json_dump.call_args
        total_tokens = call_args[0][0]["total_tokens"]
        assert total_tokens == {"input": 0, "output": 0, "total": 0}
