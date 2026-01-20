"""Tests for user_input_logger module."""
import json
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from base_logger import BaseLogger
from hook_information import HookInformation
from user_input_logger import UserInputsLogger


def test_inheritance():
    """Verify UserInputsLogger inherits from BaseLogger."""
    assert issubclass(UserInputsLogger, BaseLogger)


def test_session_directory():
    """Test session_directory returns correct path."""
    hook_info = HookInformation(
        session_id="test123",
        exit_reason="user_exit",
        transcript_path=Path("/path/to/transcript.jsonl"),
        workspace_dir=Path("/home/user/project"),
        working_directory=Path("/home/user/project/subdir"),
    )

    result = UserInputsLogger.session_directory(hook_info)

    expected = Path("/home/user/project/.cpa-workflow-artifacts/user_inputs")
    assert result == expected


@pytest.mark.parametrize(
    "jsonl_lines,expected",
    [
        pytest.param(
            [
                '{"type":"user","isMeta":false,"message":{"content":"Hello world"}}\n',
            ],
            {"user_inputs": [{"input": "Hello world", "type": "free_text"}]},
            id="free_text_message",
        ),
        pytest.param(
            [
                '{"type":"user","isMeta":false,"message":{"content":"<command-name>/test-command</command-name>"}}\n',
            ],
            {"user_inputs": [{"input": "/test-command", "type": "slash_command"}]},
            id="slash_command",
        ),
        pytest.param(
            [
                '{"type":"user","isMeta":false,"message":{"content":"<command-name> /analyze </command-name>"}}\n',
            ],
            {"user_inputs": [{"input": "/analyze", "type": "slash_command"}]},
            id="slash_command_with_spaces",
        ),
        pytest.param(
            [
                '{"type":"user","isMeta":false,"message":{"content":"<xml>tag</xml>other"}}\n',
            ],
            {"user_inputs": []},
            id="xml_tag_not_command",
        ),
        pytest.param(
            [
                '{"type":"user","isMeta":false,"message":{"content":[{"type":"tool_result","content":"User has answered your questions: \\"What is your name?\\"=\\"John\\". You can now continue with the user\'s answers in mind."}]}}\n',
            ],
            {
                "user_inputs": [
                    {
                        "input": "John",
                        "type": "question_answer",
                        "question": "What is your name?",
                    }
                ]
            },
            id="single_question_answer",
        ),
        pytest.param(
            [
                '{"type":"user","isMeta":false,"message":{"content":[{"type":"tool_result","content":"User has answered your questions: \\"Question 1?\\"=\\"Answer 1\\", \\"Question 2?\\"=\\"Answer 2\\". You can now continue with the user\'s answers in mind."}]}}\n',
            ],
            {
                "user_inputs": [
                    {
                        "input": "Answer 1",
                        "type": "question_answer",
                        "question": "Question 1?",
                    },
                    {
                        "input": "Answer 2",
                        "type": "question_answer",
                        "question": "Question 2?",
                    },
                ]
            },
            id="multiple_question_answers",
        ),
        pytest.param(
            [
                '{"type":"user","isMeta":false,"message":{"content":"First message"}}\n',
                '{"type":"user","isMeta":false,"message":{"content":"<command-name>/cmd</command-name>"}}\n',
                '{"type":"user","isMeta":false,"message":{"content":[{"type":"tool_result","content":"User has answered your questions: \\"Q?\\"=\\"A\\". You can now continue with the user\'s answers in mind."}]}}\n',
            ],
            {
                "user_inputs": [
                    {"input": "First message", "type": "free_text"},
                    {"input": "/cmd", "type": "slash_command"},
                    {"input": "A", "type": "question_answer", "question": "Q?"},
                ]
            },
            id="mixed_content_types",
        ),
        pytest.param(
            [
                '{"type":"assistant","message":{"content":"Response"}}\n',
                '{"type":"user","isMeta":true,"message":{"content":"Meta message"}}\n',
                '{"type":"user","isMeta":false,"message":{"content":"Valid"}}\n',
            ],
            {"user_inputs": [{"input": "Valid", "type": "free_text"}]},
            id="filtered_non_user_and_meta",
        ),
        pytest.param(
            [
                "invalid json line\n",
                '{"type":"user","isMeta":false,"message":{"content":"Valid"}}\n',
                "\n",
                '{"type":"user","isMeta":false,"message":{}}\n',
            ],
            {"user_inputs": [{"input": "Valid", "type": "free_text"}]},
            id="invalid_and_empty_lines",
        ),
        pytest.param(
            [
                '{"type":"user","isMeta":false,"message":{"content":[{"type":"other","content":"not a tool result"}]}}\n',
            ],
            {"user_inputs": []},
            id="array_content_not_tool_result",
        ),
        pytest.param(
            [
                '{"type":"user","isMeta":false,"message":{"content":[{"type":"tool_result","content":123}]}}\n',
            ],
            {"user_inputs": []},
            id="tool_result_non_string_content",
        ),
        pytest.param(
            [
                '{"type":"user","isMeta":false,"message":{"content":[{"type":"tool_result","content":"Some other tool result"}]}}\n',
            ],
            {"user_inputs": []},
            id="tool_result_not_ask_user_question",
        ),
        pytest.param(
            [
                '{"type":"user","isMeta":false,"message":{"content":123}}\n',
            ],
            {"user_inputs": []},
            id="content_not_string_or_list",
        ),
        pytest.param(
            [
                '{"type":"user","isMeta":false,"message":{"content":{"nested":"object"}}}\n',
            ],
            {"user_inputs": []},
            id="content_is_dict",
        ),
        pytest.param(
            [],
            {"user_inputs": []},
            id="empty_file",
        ),
    ],
)
def test_extraction(jsonl_lines, expected):
    """Test extraction with various JSONL content scenarios."""
    hook_info = HookInformation(
        session_id="test456",
        exit_reason="user_exit",
        transcript_path=Path("/path/to/transcript.jsonl"),
        workspace_dir=Path("/home/user/project"),
        working_directory=Path("/home/user/project"),
    )

    mock_file = MagicMock()
    mock_file.__enter__.side_effect = [mock_file]
    mock_file.__exit__.side_effect = [None]
    mock_file.__iter__.side_effect = [iter(jsonl_lines)]

    with patch.object(Path, "open", side_effect=[mock_file]) as mock_open:
        result = UserInputsLogger.extraction(hook_info)

    assert result == expected

    exp_open_calls = [call("r")]
    assert mock_open.mock_calls == exp_open_calls

    exp_file_calls = [call.__enter__(), call.__iter__(), call.__exit__(None, None, None)]
    assert mock_file.mock_calls == exp_file_calls


def test_aggregation():
    """Test aggregation combines, sorts by timestamp, and flattens user inputs."""
    session_directory = Path(
        "/home/user/project/.cpa-workflow-artifacts/user_inputs"
    )

    mock_json_ctx1 = MagicMock()
    mock_json_ctx2 = MagicMock()
    mock_json_file1 = MagicMock()
    mock_json_file2 = MagicMock()
    mock_json_ctx1.__enter__.side_effect = [mock_json_file1]
    mock_json_ctx1.__exit__.side_effect = [None]
    mock_json_ctx2.__enter__.side_effect = [mock_json_file2]
    mock_json_ctx2.__exit__.side_effect = [None]

    mock_agg_file = MagicMock()
    mock_agg_file.__enter__.side_effect = [mock_agg_file]
    mock_agg_file.__exit__.side_effect = [None]

    mock_glob = MagicMock()
    mock_glob.side_effect = [[
        Path("/home/user/project/.cpa-workflow-artifacts/user_inputs/session1.json"),
        Path("/home/user/project/.cpa-workflow-artifacts/user_inputs/session2.json"),
    ]]

    mock_path_open = MagicMock()
    mock_path_open.side_effect = [mock_agg_file]

    with patch.object(Path, "glob", mock_glob):
        with patch.object(Path, "open", mock_path_open):
            with patch("builtins.open", side_effect=[mock_json_ctx1, mock_json_ctx2]) as mock_open:
                with patch("json.load", side_effect=[
                    {
                        "timestamp": "2024-01-01T12:00:00Z",
                        "user_inputs": [{"input": "Later", "type": "free_text"}],
                    },
                    {
                        "timestamp": "2024-01-01T08:00:00Z",
                        "user_inputs": [{"input": "Earlier", "type": "slash_command"}],
                    },
                ]) as mock_load:
                    with patch("json.dump") as mock_dump:
                        UserInputsLogger.aggregation(session_directory)

    exp_glob_calls = [call("*.json")]
    assert mock_glob.mock_calls == exp_glob_calls

    exp_open_calls = [
        call(
            Path(
                "/home/user/project/.cpa-workflow-artifacts/user_inputs/session1.json"
            ),
            "r",
        ),
        call(
            Path(
                "/home/user/project/.cpa-workflow-artifacts/user_inputs/session2.json"
            ),
            "r",
        ),
    ]
    assert mock_open.mock_calls == exp_open_calls

    exp_path_open_calls = [call("w")]
    assert mock_path_open.mock_calls == exp_path_open_calls

    exp_load_calls = [call(mock_json_file1), call(mock_json_file2)]
    assert mock_load.mock_calls == exp_load_calls

    exp_json_ctx1_calls = [call.__enter__(), call.__exit__(None, None, None)]
    assert mock_json_ctx1.mock_calls == exp_json_ctx1_calls

    exp_json_ctx2_calls = [call.__enter__(), call.__exit__(None, None, None)]
    assert mock_json_ctx2.mock_calls == exp_json_ctx2_calls

    exp_dump_calls = [
        call(
            {
                "inputs": [
                    {"input": "Earlier", "type": "slash_command"},
                    {"input": "Later", "type": "free_text"},
                ]
            },
            mock_agg_file,
            indent=2,
        )
    ]
    assert mock_dump.mock_calls == exp_dump_calls

    exp_agg_file_calls = [call.__enter__(), call.__exit__(None, None, None)]
    assert mock_agg_file.mock_calls == exp_agg_file_calls


def test_aggregation__json_decode_error():
    """Test aggregation skips files with invalid JSON."""
    session_directory = Path(
        "/home/user/project/.cpa-workflow-artifacts/user_inputs"
    )

    mock_json_ctx1 = MagicMock()
    mock_json_ctx2 = MagicMock()
    mock_json_file1 = MagicMock()
    mock_json_file2 = MagicMock()
    mock_json_ctx1.__enter__.side_effect = [mock_json_file1]
    mock_json_ctx1.__exit__.side_effect = [None]
    mock_json_ctx2.__enter__.side_effect = [mock_json_file2]
    mock_json_ctx2.__exit__.side_effect = [None]

    mock_agg_file = MagicMock()
    mock_agg_file.__enter__.side_effect = [mock_agg_file]
    mock_agg_file.__exit__.side_effect = [None]

    mock_glob = MagicMock()
    mock_glob.side_effect = [[
        Path("/home/user/project/.cpa-workflow-artifacts/user_inputs/invalid.json"),
        Path("/home/user/project/.cpa-workflow-artifacts/user_inputs/valid.json"),
    ]]

    mock_path_open = MagicMock()
    mock_path_open.side_effect = [mock_agg_file]

    with patch.object(Path, "glob", mock_glob):
        with patch.object(Path, "open", mock_path_open):
            with patch("builtins.open", side_effect=[mock_json_ctx1, mock_json_ctx2]):
                with patch("json.load", side_effect=[
                    json.JSONDecodeError("Invalid JSON", "", 0),
                    {
                        "timestamp": "2024-01-01T10:00:00Z",
                        "user_inputs": [{"input": "Valid", "type": "free_text"}],
                    },
                ]):
                    with patch("json.dump") as mock_dump:
                        UserInputsLogger.aggregation(session_directory)

    exp_dump_calls = [
        call(
            {"inputs": [{"input": "Valid", "type": "free_text"}]},
            mock_agg_file,
            indent=2,
        )
    ]
    assert mock_dump.mock_calls == exp_dump_calls


def test_aggregation__missing_timestamp():
    """Test aggregation handles sessions with missing timestamp field."""
    session_directory = Path(
        "/home/user/project/.cpa-workflow-artifacts/user_inputs"
    )

    mock_json_ctx1 = MagicMock()
    mock_json_file1 = MagicMock()
    mock_json_ctx1.__enter__.side_effect = [mock_json_file1]
    mock_json_ctx1.__exit__.side_effect = [None]

    mock_agg_file = MagicMock()
    mock_agg_file.__enter__.side_effect = [mock_agg_file]
    mock_agg_file.__exit__.side_effect = [None]

    mock_glob = MagicMock()
    mock_glob.side_effect = [[
        Path("/home/user/project/.cpa-workflow-artifacts/user_inputs/session.json"),
    ]]

    mock_path_open = MagicMock()
    mock_path_open.side_effect = [mock_agg_file]

    with patch.object(Path, "glob", mock_glob):
        with patch.object(Path, "open", mock_path_open):
            with patch("builtins.open", side_effect=[mock_json_ctx1]):
                with patch("json.load", side_effect=[
                    {"user_inputs": [{"input": "No timestamp", "type": "free_text"}]},
                ]):
                    with patch("json.dump") as mock_dump:
                        UserInputsLogger.aggregation(session_directory)

    exp_dump_calls = [
        call(
            {"inputs": [{"input": "No timestamp", "type": "free_text"}]},
            mock_agg_file,
            indent=2,
        )
    ]
    assert mock_dump.mock_calls == exp_dump_calls


def test_aggregation__empty_directory():
    """Test aggregation with no session files."""
    session_directory = Path(
        "/home/user/project/.cpa-workflow-artifacts/user_inputs"
    )

    mock_agg_file = MagicMock()
    mock_agg_file.__enter__.side_effect = [mock_agg_file]
    mock_agg_file.__exit__.side_effect = [None]

    mock_glob = MagicMock()
    mock_glob.side_effect = [[]]

    mock_path_open = MagicMock()
    mock_path_open.side_effect = [mock_agg_file]

    with patch.object(Path, "glob", mock_glob):
        with patch.object(Path, "open", mock_path_open):
            with patch("json.dump") as mock_dump:
                UserInputsLogger.aggregation(session_directory)

    exp_glob_calls = [call("*.json")]
    assert mock_glob.mock_calls == exp_glob_calls

    exp_path_open_calls = [call("w")]
    assert mock_path_open.mock_calls == exp_path_open_calls

    exp_dump_calls = [call({"inputs": []}, mock_agg_file, indent=2)]
    assert mock_dump.mock_calls == exp_dump_calls

    exp_agg_file_calls = [call.__enter__(), call.__exit__(None, None, None)]
    assert mock_agg_file.mock_calls == exp_agg_file_calls
