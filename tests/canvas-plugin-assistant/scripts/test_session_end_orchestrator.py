"""Tests for session_end_orchestrator module."""

import sys
from pathlib import Path
from unittest.mock import call, patch

import pytest

from session_end_orchestrator import SessionEndOrchestrator
from hook_information import HookInformation


@pytest.fixture
def hook_info() -> HookInformation:
    """Create a HookInformation instance for testing."""
    return HookInformation(
        session_id="test-session-123",
        exit_reason="user_exit",
        transcript_path=Path("/path/to/transcript.jsonl"),
        workspace_dir=Path("/path/to/workspace"),
        working_directory=Path("/path/to/working/dir"),
    )


@patch("session_end_orchestrator.sys.exit")
@patch("session_end_orchestrator.GitCommitPlugin")
@patch("session_end_orchestrator.UserInputsLogger")
@patch("session_end_orchestrator.CostsLogger")
def test_run__all_hooks_succeed(
    mock_costs_logger,
    mock_user_inputs_logger,
    mock_git_commit_plugin,
    mock_sys_exit,
    hook_info,
):
    """Test run executes all hooks in order when all succeed."""
    mock_costs_logger.run.side_effect = [None]
    mock_user_inputs_logger.run.side_effect = [None]
    mock_git_commit_plugin.run.side_effect = [None]
    mock_sys_exit.side_effect = [None]

    tested = SessionEndOrchestrator

    tested.run(hook_info)

    exp_costs_logger_calls = [call.run(hook_info)]
    assert mock_costs_logger.mock_calls == exp_costs_logger_calls

    exp_user_inputs_logger_calls = [call.run(hook_info)]
    assert mock_user_inputs_logger.mock_calls == exp_user_inputs_logger_calls

    exp_git_commit_plugin_calls = [call.run(hook_info)]
    assert mock_git_commit_plugin.mock_calls == exp_git_commit_plugin_calls

    exp_sys_exit_calls = [call(0)]
    assert mock_sys_exit.mock_calls == exp_sys_exit_calls


@patch("session_end_orchestrator.sys.exit")
@patch("session_end_orchestrator.GitCommitPlugin")
@patch("session_end_orchestrator.UserInputsLogger")
@patch("session_end_orchestrator.CostsLogger")
def test_run__hook_raises_system_exit(
    mock_costs_logger,
    mock_user_inputs_logger,
    mock_git_commit_plugin,
    mock_sys_exit,
    hook_info,
):
    """Test run catches SystemExit from hooks and continues execution."""
    mock_costs_logger.run.side_effect = [SystemExit(0)]
    mock_user_inputs_logger.run.side_effect = [SystemExit(1)]
    mock_git_commit_plugin.run.side_effect = [None]
    mock_sys_exit.side_effect = [None]

    tested = SessionEndOrchestrator

    tested.run(hook_info)

    exp_costs_logger_calls = [call.run(hook_info)]
    assert mock_costs_logger.mock_calls == exp_costs_logger_calls

    exp_user_inputs_logger_calls = [call.run(hook_info)]
    assert mock_user_inputs_logger.mock_calls == exp_user_inputs_logger_calls

    exp_git_commit_plugin_calls = [call.run(hook_info)]
    assert mock_git_commit_plugin.mock_calls == exp_git_commit_plugin_calls

    exp_sys_exit_calls = [call(0)]
    assert mock_sys_exit.mock_calls == exp_sys_exit_calls


@patch("builtins.print")
@patch("session_end_orchestrator.sys.exit")
@patch("session_end_orchestrator.GitCommitPlugin")
@patch("session_end_orchestrator.UserInputsLogger")
@patch("session_end_orchestrator.CostsLogger")
def test_run__hook_raises_exception(
    mock_costs_logger,
    mock_user_inputs_logger,
    mock_git_commit_plugin,
    mock_sys_exit,
    mock_print,
    hook_info,
):
    """Test run prints warning to stderr when hook raises exception and continues."""
    mock_costs_logger.run.side_effect = [ValueError("Cost calculation failed")]
    mock_user_inputs_logger.run.side_effect = [None]
    mock_git_commit_plugin.run.side_effect = [None]
    mock_sys_exit.side_effect = [None]
    mock_print.side_effect = [None]

    tested = SessionEndOrchestrator

    tested.run(hook_info)

    exp_costs_logger_calls = [call.run(hook_info)]
    assert mock_costs_logger.mock_calls == exp_costs_logger_calls

    exp_user_inputs_logger_calls = [call.run(hook_info)]
    assert mock_user_inputs_logger.mock_calls == exp_user_inputs_logger_calls

    exp_git_commit_plugin_calls = [call.run(hook_info)]
    assert mock_git_commit_plugin.mock_calls == exp_git_commit_plugin_calls

    exp_print_calls = [
        call("Warning: Cost Logger failed: Cost calculation failed", file=sys.stderr)
    ]
    assert mock_print.mock_calls == exp_print_calls

    exp_sys_exit_calls = [call(0)]
    assert mock_sys_exit.mock_calls == exp_sys_exit_calls


@patch("builtins.print")
@patch("session_end_orchestrator.sys.exit")
@patch("session_end_orchestrator.GitCommitPlugin")
@patch("session_end_orchestrator.UserInputsLogger")
@patch("session_end_orchestrator.CostsLogger")
def test_run__multiple_hooks_raise_exceptions(
    mock_costs_logger,
    mock_user_inputs_logger,
    mock_git_commit_plugin,
    mock_sys_exit,
    mock_print,
    hook_info,
):
    """Test run handles multiple hooks failing and continues to completion."""
    mock_costs_logger.run.side_effect = [RuntimeError("Database connection failed")]
    mock_user_inputs_logger.run.side_effect = [IOError("File not found")]
    mock_git_commit_plugin.run.side_effect = [None]
    mock_sys_exit.side_effect = [None]
    mock_print.side_effect = [None, None]

    tested = SessionEndOrchestrator

    tested.run(hook_info)

    exp_costs_logger_calls = [call.run(hook_info)]
    assert mock_costs_logger.mock_calls == exp_costs_logger_calls

    exp_user_inputs_logger_calls = [call.run(hook_info)]
    assert mock_user_inputs_logger.mock_calls == exp_user_inputs_logger_calls

    exp_git_commit_plugin_calls = [call.run(hook_info)]
    assert mock_git_commit_plugin.mock_calls == exp_git_commit_plugin_calls

    exp_print_calls = [
        call(
            "Warning: Cost Logger failed: Database connection failed",
            file=sys.stderr,
        ),
        call(
            "Warning: User Input Logger failed: File not found",
            file=sys.stderr,
        ),
    ]
    assert mock_print.mock_calls == exp_print_calls

    exp_sys_exit_calls = [call(0)]
    assert mock_sys_exit.mock_calls == exp_sys_exit_calls


@patch("builtins.print")
@patch("session_end_orchestrator.sys.exit")
@patch("session_end_orchestrator.GitCommitPlugin")
@patch("session_end_orchestrator.UserInputsLogger")
@patch("session_end_orchestrator.CostsLogger")
def test_run__git_commit_plugin_raises_exception(
    mock_costs_logger,
    mock_user_inputs_logger,
    mock_git_commit_plugin,
    mock_sys_exit,
    mock_print,
    hook_info,
):
    """Test run handles GitCommitPlugin failure (last hook)."""
    mock_costs_logger.run.side_effect = [None]
    mock_user_inputs_logger.run.side_effect = [None]
    mock_git_commit_plugin.run.side_effect = [Exception("Git push failed")]
    mock_sys_exit.side_effect = [None]
    mock_print.side_effect = [None]

    tested = SessionEndOrchestrator

    tested.run(hook_info)

    exp_costs_logger_calls = [call.run(hook_info)]
    assert mock_costs_logger.mock_calls == exp_costs_logger_calls

    exp_user_inputs_logger_calls = [call.run(hook_info)]
    assert mock_user_inputs_logger.mock_calls == exp_user_inputs_logger_calls

    exp_git_commit_plugin_calls = [call.run(hook_info)]
    assert mock_git_commit_plugin.mock_calls == exp_git_commit_plugin_calls

    exp_print_calls = [
        call("Warning: Git Commit Plugin failed: Git push failed", file=sys.stderr)
    ]
    assert mock_print.mock_calls == exp_print_calls

    exp_sys_exit_calls = [call(0)]
    assert mock_sys_exit.mock_calls == exp_sys_exit_calls


@patch("session_end_orchestrator.sys.exit")
@patch("session_end_orchestrator.GitCommitPlugin")
@patch("session_end_orchestrator.UserInputsLogger")
@patch("session_end_orchestrator.CostsLogger")
def test_run__all_hooks_raise_system_exit(
    mock_costs_logger,
    mock_user_inputs_logger,
    mock_git_commit_plugin,
    mock_sys_exit,
    hook_info,
):
    """Test run handles all hooks raising SystemExit."""
    mock_costs_logger.run.side_effect = [SystemExit(0)]
    mock_user_inputs_logger.run.side_effect = [SystemExit(0)]
    mock_git_commit_plugin.run.side_effect = [SystemExit(0)]
    mock_sys_exit.side_effect = [None]

    tested = SessionEndOrchestrator

    tested.run(hook_info)

    exp_costs_logger_calls = [call.run(hook_info)]
    assert mock_costs_logger.mock_calls == exp_costs_logger_calls

    exp_user_inputs_logger_calls = [call.run(hook_info)]
    assert mock_user_inputs_logger.mock_calls == exp_user_inputs_logger_calls

    exp_git_commit_plugin_calls = [call.run(hook_info)]
    assert mock_git_commit_plugin.mock_calls == exp_git_commit_plugin_calls

    exp_sys_exit_calls = [call(0)]
    assert mock_sys_exit.mock_calls == exp_sys_exit_calls
