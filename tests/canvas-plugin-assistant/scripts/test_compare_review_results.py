"""Tests for compare_review_results module."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest

from compare_review_results import call_anthropic, compare_findings, main


class TestCallAnthropic:
    """Tests for the call_anthropic function."""

    @patch("compare_review_results.requests.post")
    def test_call_anthropic__success(self, mock_post) -> None:
        """Test call_anthropic returns success response."""
        mock_post.side_effect = [
            SimpleNamespace(
                status_code=200,
                json=lambda: {
                    "content": [{"text": "Response text"}]
                }
            )
        ]

        tested = call_anthropic
        result = tested("test-api-key", "test prompt")

        expected = {"success": True, "content": "Response text"}
        assert result == expected

        exp_post_calls = [
            call(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                    "x-api-key": "test-api-key",
                },
                json={
                    "model": "claude-sonnet-4-5-20250929",
                    "temperature": 0.0,
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": "test prompt"}],
                },
                timeout=60,
            )
        ]
        assert mock_post.mock_calls == exp_post_calls

    @patch("compare_review_results.requests.post")
    def test_call_anthropic__failure(self, mock_post) -> None:
        """Test call_anthropic returns error on non-200 status."""
        mock_post.side_effect = [
            SimpleNamespace(
                status_code=401,
                text="Unauthorized"
            )
        ]

        tested = call_anthropic
        result = tested("invalid-key", "test prompt")

        expected = {"success": False, "error": "Unauthorized"}
        assert result == expected

        exp_post_calls = [
            call(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                    "x-api-key": "invalid-key",
                },
                json={
                    "model": "claude-sonnet-4-5-20250929",
                    "temperature": 0.0,
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": "test prompt"}],
                },
                timeout=60,
            )
        ]
        assert mock_post.mock_calls == exp_post_calls

    @patch("compare_review_results.requests.post")
    def test_call_anthropic__empty_content(self, mock_post) -> None:
        """Test call_anthropic handles empty content array."""
        mock_post.side_effect = [
            SimpleNamespace(
                status_code=200,
                json=lambda: {"content": [{}]}
            )
        ]

        tested = call_anthropic
        result = tested("test-api-key", "test prompt")

        expected = {"success": True, "content": ""}
        assert result == expected

        exp_post_calls = [
            call(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                    "x-api-key": "test-api-key",
                },
                json={
                    "model": "claude-sonnet-4-5-20250929",
                    "temperature": 0.0,
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": "test prompt"}],
                },
                timeout=60,
            )
        ]
        assert mock_post.mock_calls == exp_post_calls


class TestCompareFindings:
    """Tests for the compare_findings function."""

    @patch("compare_review_results.call_anthropic")
    def test_compare_findings__success_with_json_block(self, mock_call_anthropic) -> None:
        """Test compare_findings parses JSON block response successfully."""
        mock_call_anthropic.side_effect = [
            {
                "success": True,
                "content": """Here is the analysis:
```json
{
  "findings": [
    {"category": "SQL Injection", "severity": "high", "detected": true, "explanation": "Found in report"}
  ],
  "overall_verdict_matches": true,
  "explanation": "All findings detected"
}
```"""
            }
        ]

        tested = compare_findings
        result = tested(
            security_report="Security issues found: SQL Injection",
            database_report="",
            expected={
                "eval_name": "test-eval",
                "expected_findings": [
                    {"category": "SQL Injection", "severity": "high", "description": "SQL injection vulnerability", "must_detect": True}
                ]
            },
            api_key="test-key"
        )

        assert result["eval_name"] == "test-eval"
        assert result["overall_pass"] is True
        assert len(result["findings"]) == 1
        assert result["findings"][0]["detected"] is True

        exp_call_anthropic_calls = [call("test-key", pytest.approx(str, abs=1000))]
        assert len(mock_call_anthropic.mock_calls) == 1

    @patch("compare_review_results.call_anthropic")
    def test_compare_findings__success_raw_json(self, mock_call_anthropic) -> None:
        """Test compare_findings parses raw JSON response."""
        mock_call_anthropic.side_effect = [
            {
                "success": True,
                "content": '{"findings": [{"category": "XSS", "severity": "medium", "detected": false, "explanation": "Not found"}], "overall_verdict_matches": false, "explanation": "Missing"}'
            }
        ]

        tested = compare_findings
        result = tested(
            security_report="No issues",
            database_report="",
            expected={
                "eval_name": "xss-test",
                "expected_findings": [
                    {"category": "XSS", "severity": "medium", "description": "XSS vulnerability", "must_detect": True}
                ]
            },
            api_key="test-key"
        )

        assert result["eval_name"] == "xss-test"
        assert result["overall_pass"] is False
        assert result["findings"][0]["detected"] is False

        assert len(mock_call_anthropic.mock_calls) == 1

    @patch("compare_review_results.call_anthropic")
    def test_compare_findings__api_failure(self, mock_call_anthropic) -> None:
        """Test compare_findings handles API failure."""
        mock_call_anthropic.side_effect = [
            {"success": False, "error": "Rate limited"}
        ]

        tested = compare_findings
        result = tested(
            security_report="Report content",
            database_report="",
            expected={"eval_name": "rate-limit-test"},
            api_key="test-key"
        )

        assert result["eval_name"] == "rate-limit-test"
        assert result["error"] == "Rate limited"
        assert result["overall_pass"] is False

        assert len(mock_call_anthropic.mock_calls) == 1

    @patch("compare_review_results.call_anthropic")
    def test_compare_findings__json_decode_error(self, mock_call_anthropic) -> None:
        """Test compare_findings handles invalid JSON response."""
        mock_call_anthropic.side_effect = [
            {"success": True, "content": "This is not JSON at all"}
        ]

        tested = compare_findings
        result = tested(
            security_report="Report",
            database_report="",
            expected={"eval_name": "json-error-test"},
            api_key="test-key"
        )

        assert result["eval_name"] == "json-error-test"
        assert "Failed to parse API response" in result["error"]
        assert result["raw_response"] == "This is not JSON at all"
        assert result["overall_pass"] is False

        assert len(mock_call_anthropic.mock_calls) == 1

    @patch("compare_review_results.call_anthropic")
    def test_compare_findings__both_reports(self, mock_call_anthropic) -> None:
        """Test compare_findings includes both security and database reports."""
        mock_call_anthropic.side_effect = [
            {
                "success": True,
                "content": '```json\n{"findings": [], "overall_verdict_matches": true, "explanation": "OK"}\n```'
            }
        ]

        tested = compare_findings
        result = tested(
            security_report="Security content",
            database_report="Database content",
            expected={"eval_name": "both-reports", "expected_findings": []},
            api_key="test-key"
        )

        assert result["overall_pass"] is True

        # Verify both reports are in the prompt
        call_args = mock_call_anthropic.call_args
        prompt = call_args[0][1]
        assert "Security Review Report" in prompt
        assert "Security content" in prompt
        assert "Database Performance Review Report" in prompt
        assert "Database content" in prompt

        assert len(mock_call_anthropic.mock_calls) == 1

    @patch("compare_review_results.call_anthropic")
    def test_compare_findings__partial_detection(self, mock_call_anthropic) -> None:
        """Test compare_findings with some findings detected."""
        mock_call_anthropic.side_effect = [
            {
                "success": True,
                "content": '```json\n{"findings": [{"category": "A", "severity": "high", "detected": true, "explanation": "Found"}, {"category": "B", "severity": "low", "detected": false, "explanation": "Not found"}], "overall_verdict_matches": false, "explanation": "Partial"}\n```'
            }
        ]

        tested = compare_findings
        result = tested(
            security_report="Found A",
            database_report="",
            expected={
                "eval_name": "partial-test",
                "expected_findings": [
                    {"category": "A", "severity": "high", "description": "Issue A", "must_detect": True},
                    {"category": "B", "severity": "low", "description": "Issue B", "must_detect": True}
                ]
            },
            api_key="test-key"
        )

        # 1 detected but 2 must_detect, so overall_pass is False
        assert result["overall_pass"] is False

        assert len(mock_call_anthropic.mock_calls) == 1

    @patch("compare_review_results.call_anthropic")
    def test_compare_findings__no_must_detect(self, mock_call_anthropic) -> None:
        """Test compare_findings when no must_detect findings exist."""
        mock_call_anthropic.side_effect = [
            {
                "success": True,
                "content": '```json\n{"findings": [], "overall_verdict_matches": true, "explanation": "OK"}\n```'
            }
        ]

        tested = compare_findings
        result = tested(
            security_report="Report",
            database_report="",
            expected={
                "eval_name": "no-must-detect",
                "expected_findings": [
                    {"category": "Optional", "severity": "low", "description": "Optional issue", "must_detect": False}
                ]
            },
            api_key="test-key"
        )

        # No must_detect findings, so 0 detected >= 0 must_detect = True
        assert result["overall_pass"] is True

        assert len(mock_call_anthropic.mock_calls) == 1

    @patch("compare_review_results.call_anthropic")
    def test_compare_findings__empty_expected_findings(self, mock_call_anthropic) -> None:
        """Test compare_findings with empty expected_findings list."""
        mock_call_anthropic.side_effect = [
            {
                "success": True,
                "content": '```json\n{"findings": [], "overall_verdict_matches": true, "explanation": "No findings expected"}\n```'
            }
        ]

        tested = compare_findings
        result = tested(
            security_report="Report",
            database_report="",
            expected={"eval_name": "empty-findings"},
            api_key="test-key"
        )

        assert result["overall_pass"] is True

        assert len(mock_call_anthropic.mock_calls) == 1

    @patch("compare_review_results.call_anthropic")
    def test_compare_findings__database_only(self, mock_call_anthropic) -> None:
        """Test compare_findings with only database report (no security report)."""
        mock_call_anthropic.side_effect = [
            {
                "success": True,
                "content": '```json\n{"findings": [], "overall_verdict_matches": true, "explanation": "OK"}\n```'
            }
        ]

        tested = compare_findings
        result = tested(
            security_report="",
            database_report="Database performance content",
            expected={"eval_name": "db-only", "expected_findings": []},
            api_key="test-key"
        )

        assert result["overall_pass"] is True

        # Verify only database report is in the prompt (not security)
        call_args = mock_call_anthropic.call_args
        prompt = call_args[0][1]
        assert "Security Review Report" not in prompt
        assert "Database Performance Review Report" in prompt
        assert "Database performance content" in prompt

        assert len(mock_call_anthropic.mock_calls) == 1

    @patch("compare_review_results.call_anthropic")
    def test_compare_findings__unknown_eval_name(self, mock_call_anthropic) -> None:
        """Test compare_findings uses 'unknown' when eval_name missing."""
        mock_call_anthropic.side_effect = [
            {"success": False, "error": "Error"}
        ]

        tested = compare_findings
        result = tested(
            security_report="Report",
            database_report="",
            expected={},  # No eval_name
            api_key="test-key"
        )

        assert result["eval_name"] == "unknown"

        assert len(mock_call_anthropic.mock_calls) == 1


class TestMain:
    """Tests for the main function."""

    @patch("compare_review_results.sys.exit")
    @patch("compare_review_results.compare_findings")
    @patch("compare_review_results.json.loads")
    @patch("compare_review_results.Path")
    @patch("compare_review_results.os.environ.get")
    @patch("compare_review_results.argparse.ArgumentParser")
    def test_main__success_with_output(
        self, mock_argparse, mock_env_get, mock_path_cls, mock_json_loads, mock_compare, mock_exit
    ) -> None:
        """Test main with successful comparison and output file."""
        mock_parser = MagicMock()
        mock_argparse.return_value = mock_parser
        mock_args = MagicMock()
        mock_args.security_report = "/path/to/security.md"
        mock_args.database_report = None
        mock_args.expected = "/path/to/expected.json"
        mock_args.output = "/path/to/output.json"
        mock_parser.parse_args.return_value = mock_args

        mock_env_get.side_effect = ["test-api-key"]

        mock_expected_path = MagicMock()
        mock_expected_path.exists.return_value = True
        mock_expected_path.read_text.return_value = '{"eval_name": "test"}'

        mock_security_path = MagicMock()
        mock_security_path.exists.return_value = True
        mock_security_path.read_text.return_value = "Security report content"

        mock_output_path = MagicMock()

        # Track Path() calls
        path_call_results = {
            "/path/to/expected.json": mock_expected_path,
            "/path/to/security.md": mock_security_path,
            "/path/to/output.json": mock_output_path,
        }
        mock_path_cls.side_effect = lambda p: path_call_results.get(p, MagicMock())

        mock_json_loads.side_effect = [{"eval_name": "test"}]

        mock_compare.side_effect = [{"overall_pass": True, "findings": []}]

        tested = main
        tested()

        exp_env_get_calls = [call("EVALS_ANTHROPIC_API_KEY")]
        assert mock_env_get.mock_calls == exp_env_get_calls

        exp_compare_calls = [call("Security report content", "", {"eval_name": "test"}, "test-api-key")]
        assert mock_compare.mock_calls == exp_compare_calls

        exp_exit_calls = [call(0)]
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("compare_review_results.sys.exit")
    @patch("compare_review_results.sys.stderr", new_callable=MagicMock)
    @patch("compare_review_results.argparse.ArgumentParser")
    def test_main__no_reports_provided(self, mock_argparse, mock_stderr, mock_exit) -> None:
        """Test main exits when no reports provided."""
        mock_parser = MagicMock()
        mock_argparse.return_value = mock_parser
        mock_args = MagicMock()
        mock_args.security_report = None
        mock_args.database_report = None
        mock_args.expected = "/path/to/expected.json"
        mock_parser.parse_args.return_value = mock_args

        mock_exit.side_effect = [SystemExit(1)]

        tested = main
        with pytest.raises(SystemExit):
            tested()

        exp_exit_calls = [call(1)]
        assert mock_exit.mock_calls == exp_exit_calls

        exp_stderr_calls = [
            call.write("ERROR: At least one of --security-report or --database-report is required"),
            call.write("\n"),
        ]
        assert mock_stderr.mock_calls == exp_stderr_calls

    @patch("compare_review_results.sys.exit")
    @patch("compare_review_results.sys.stderr", new_callable=MagicMock)
    @patch("compare_review_results.os.environ.get")
    @patch("compare_review_results.argparse.ArgumentParser")
    def test_main__no_api_key(self, mock_argparse, mock_env_get, mock_stderr, mock_exit) -> None:
        """Test main exits when API key not set."""
        mock_parser = MagicMock()
        mock_argparse.return_value = mock_parser
        mock_args = MagicMock()
        mock_args.security_report = "/path/to/security.md"
        mock_args.database_report = None
        mock_args.expected = "/path/to/expected.json"
        mock_parser.parse_args.return_value = mock_args

        mock_env_get.side_effect = [None]
        mock_exit.side_effect = [SystemExit(1)]

        tested = main
        with pytest.raises(SystemExit):
            tested()

        exp_env_get_calls = [call("EVALS_ANTHROPIC_API_KEY")]
        assert mock_env_get.mock_calls == exp_env_get_calls

        exp_exit_calls = [call(1)]
        assert mock_exit.mock_calls == exp_exit_calls

        exp_stderr_calls = [
            call.write("ERROR: EVALS_ANTHROPIC_API_KEY environment variable not set"),
            call.write("\n"),
        ]
        assert mock_stderr.mock_calls == exp_stderr_calls

    @patch("compare_review_results.sys.exit")
    @patch("compare_review_results.sys.stderr", new_callable=MagicMock)
    @patch("compare_review_results.Path")
    @patch("compare_review_results.os.environ.get")
    @patch("compare_review_results.argparse.ArgumentParser")
    def test_main__expected_file_not_found(
        self, mock_argparse, mock_env_get, mock_path_cls, mock_stderr, mock_exit
    ) -> None:
        """Test main exits when expected file not found."""
        mock_parser = MagicMock()
        mock_argparse.return_value = mock_parser
        mock_args = MagicMock()
        mock_args.security_report = "/path/to/security.md"
        mock_args.database_report = None
        mock_args.expected = "/path/to/expected.json"
        mock_parser.parse_args.return_value = mock_args

        mock_env_get.side_effect = ["test-api-key"]

        mock_expected_path = MagicMock()
        mock_expected_path.exists.return_value = False
        mock_path_cls.return_value = mock_expected_path

        mock_exit.side_effect = [SystemExit(1)]

        tested = main
        with pytest.raises(SystemExit):
            tested()

        exp_exit_calls = [call(1)]
        assert mock_exit.mock_calls == exp_exit_calls

        exp_stderr_calls = [
            call.write(f"ERROR: Expected file not found: {mock_expected_path}"),
            call.write("\n"),
        ]
        assert mock_stderr.mock_calls == exp_stderr_calls

    @patch("compare_review_results.sys.exit")
    @patch("compare_review_results.sys.stderr")
    @patch("compare_review_results.compare_findings")
    @patch("compare_review_results.json.loads")
    @patch("compare_review_results.Path")
    @patch("compare_review_results.os.environ.get")
    @patch("compare_review_results.argparse.ArgumentParser")
    def test_main__security_report_not_found(
        self, mock_argparse, mock_env_get, mock_path_cls, mock_json_loads, mock_compare, mock_stderr, mock_exit
    ) -> None:
        """Test main warns when security report not found."""
        mock_parser = MagicMock()
        mock_argparse.return_value = mock_parser
        mock_args = MagicMock()
        mock_args.security_report = "/path/to/security.md"
        mock_args.database_report = None
        mock_args.expected = "/path/to/expected.json"
        mock_args.output = None
        mock_parser.parse_args.return_value = mock_args

        mock_env_get.side_effect = ["test-api-key"]

        mock_expected_path = MagicMock()
        mock_expected_path.exists.return_value = True
        mock_expected_path.read_text.return_value = '{"eval_name": "test"}'

        mock_security_path = MagicMock()
        mock_security_path.exists.return_value = False

        path_calls = [mock_expected_path, mock_security_path]
        mock_path_cls.side_effect = path_calls

        mock_json_loads.side_effect = [{"eval_name": "test"}]
        mock_compare.side_effect = [{"overall_pass": True}]

        tested = main
        tested()

        # Should still call compare_findings with empty security_report
        exp_compare_calls = [call("", "", {"eval_name": "test"}, "test-api-key")]
        assert mock_compare.mock_calls == exp_compare_calls

    @patch("compare_review_results.sys.exit")
    @patch("compare_review_results.sys.stderr")
    @patch("compare_review_results.compare_findings")
    @patch("compare_review_results.json.loads")
    @patch("compare_review_results.Path")
    @patch("compare_review_results.os.environ.get")
    @patch("compare_review_results.argparse.ArgumentParser")
    def test_main__database_report_not_found(
        self, mock_argparse, mock_env_get, mock_path_cls, mock_json_loads, mock_compare, mock_stderr, mock_exit
    ) -> None:
        """Test main warns when database report not found."""
        mock_parser = MagicMock()
        mock_argparse.return_value = mock_parser
        mock_args = MagicMock()
        mock_args.security_report = None
        mock_args.database_report = "/path/to/database.md"
        mock_args.expected = "/path/to/expected.json"
        mock_args.output = None
        mock_parser.parse_args.return_value = mock_args

        mock_env_get.side_effect = ["test-api-key"]

        mock_expected_path = MagicMock()
        mock_expected_path.exists.return_value = True
        mock_expected_path.read_text.return_value = '{"eval_name": "test"}'

        mock_database_path = MagicMock()
        mock_database_path.exists.return_value = False

        path_calls = [mock_expected_path, mock_database_path]
        mock_path_cls.side_effect = path_calls

        mock_json_loads.side_effect = [{"eval_name": "test"}]
        mock_compare.side_effect = [{"overall_pass": True}]

        tested = main
        tested()

        # Should still call compare_findings with empty database_report
        exp_compare_calls = [call("", "", {"eval_name": "test"}, "test-api-key")]
        assert mock_compare.mock_calls == exp_compare_calls

    @patch("compare_review_results.sys.exit")
    @patch("compare_review_results.print")
    @patch("compare_review_results.compare_findings")
    @patch("compare_review_results.json.loads")
    @patch("compare_review_results.Path")
    @patch("compare_review_results.os.environ.get")
    @patch("compare_review_results.argparse.ArgumentParser")
    def test_main__no_output_prints_json(
        self, mock_argparse, mock_env_get, mock_path_cls, mock_json_loads, mock_compare, mock_print, mock_exit
    ) -> None:
        """Test main prints JSON when no output file specified."""
        mock_parser = MagicMock()
        mock_argparse.return_value = mock_parser
        mock_args = MagicMock()
        mock_args.security_report = "/path/to/security.md"
        mock_args.database_report = None
        mock_args.expected = "/path/to/expected.json"
        mock_args.output = None
        mock_parser.parse_args.return_value = mock_args

        mock_env_get.side_effect = ["test-api-key"]

        mock_expected_path = MagicMock()
        mock_expected_path.exists.return_value = True
        mock_expected_path.read_text.return_value = '{"eval_name": "test"}'

        mock_security_path = MagicMock()
        mock_security_path.exists.return_value = True
        mock_security_path.read_text.return_value = "Security content"

        path_calls = [mock_expected_path, mock_security_path]
        mock_path_cls.side_effect = path_calls

        mock_json_loads.side_effect = [{"eval_name": "test"}]
        mock_compare.side_effect = [{"overall_pass": False, "error": "Test error"}]

        tested = main
        tested()

        # Verify JSON is printed (second call after potential warning)
        assert any(
            '{\n  "overall_pass": false' in str(c) or '"overall_pass": false' in str(c)
            for c in mock_print.mock_calls
        )

        exp_exit_calls = [call(1)]  # Fails because overall_pass is False
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("compare_review_results.sys.exit")
    @patch("compare_review_results.compare_findings")
    @patch("compare_review_results.json.loads")
    @patch("compare_review_results.Path")
    @patch("compare_review_results.os.environ.get")
    @patch("compare_review_results.argparse.ArgumentParser")
    def test_main__both_reports(
        self, mock_argparse, mock_env_get, mock_path_cls, mock_json_loads, mock_compare, mock_exit
    ) -> None:
        """Test main handles both security and database reports."""
        mock_parser = MagicMock()
        mock_argparse.return_value = mock_parser
        mock_args = MagicMock()
        mock_args.security_report = "/path/to/security.md"
        mock_args.database_report = "/path/to/database.md"
        mock_args.expected = "/path/to/expected.json"
        mock_args.output = None
        mock_parser.parse_args.return_value = mock_args

        mock_env_get.side_effect = ["test-api-key"]

        mock_expected_path = MagicMock()
        mock_expected_path.exists.return_value = True
        mock_expected_path.read_text.return_value = '{"eval_name": "test"}'

        mock_security_path = MagicMock()
        mock_security_path.exists.return_value = True
        mock_security_path.read_text.return_value = "Security content"

        mock_database_path = MagicMock()
        mock_database_path.exists.return_value = True
        mock_database_path.read_text.return_value = "Database content"

        path_calls = [mock_expected_path, mock_security_path, mock_database_path]
        mock_path_cls.side_effect = path_calls

        mock_json_loads.side_effect = [{"eval_name": "test"}]
        mock_compare.side_effect = [{"overall_pass": True}]

        tested = main
        tested()

        exp_compare_calls = [call("Security content", "Database content", {"eval_name": "test"}, "test-api-key")]
        assert mock_compare.mock_calls == exp_compare_calls

        exp_exit_calls = [call(0)]
        assert mock_exit.mock_calls == exp_exit_calls
