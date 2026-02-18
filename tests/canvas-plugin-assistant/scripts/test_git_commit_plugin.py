"""Tests for git_commit_plugin module."""

import subprocess
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

import pytest

from git_commit_plugin import GitCommitPlugin
from hook_information import HookInformation


def make_hook_info(tmp_path: Path) -> HookInformation:
    """Create a real HookInformation instance with tmp_path as workspace_dir."""
    return HookInformation(
        session_id="test-session-123",
        exit_reason="user_exit",
        transcript_path=tmp_path / "transcript.jsonl",
        workspace_dir=tmp_path / "my-plugin",
        working_directory=tmp_path,
    )


class TestGitCommitPlugin:
    """Tests for GitCommitPlugin class."""

    # ==================== run() tests ====================

    @patch("git_commit_plugin.sys.exit")
    def test_run__plugin_dir_not_exists(self, mock_exit, tmp_path):
        """Test run exits 0 when plugin directory does not exist."""
        hook_info = make_hook_info(tmp_path)
        # workspace_dir (my-plugin) does not exist
        mock_exit.side_effect = [SystemExit(0)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_exit_calls = [call(0)]
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("git_commit_plugin.sys.exit")
    def test_run__no_artifacts_dir(self, mock_exit, tmp_path):
        """Test run exits 0 when .cpa-workflow-artifacts directory does not exist."""
        hook_info = make_hook_info(tmp_path)
        hook_info.workspace_dir.mkdir(parents=True)
        # .cpa-workflow-artifacts does not exist
        mock_exit.side_effect = [SystemExit(0)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_exit_calls = [call(0)]
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("git_commit_plugin.sys.exit")
    def test_run__no_wrap_up_reports(self, mock_exit, tmp_path):
        """Test run exits 0 when no wrap-up-report-*.md files exist."""
        hook_info = make_hook_info(tmp_path)
        hook_info.workspace_dir.mkdir(parents=True)
        artifacts_dir = hook_info.workspace_dir / ".cpa-workflow-artifacts"
        artifacts_dir.mkdir()
        # No wrap-up-report-*.md files
        mock_exit.side_effect = [SystemExit(0)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_exit_calls = [call(0)]
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("git_commit_plugin.GitCommitPlugin._stage_files")
    @patch("git_commit_plugin.GitCommitPlugin._has_changes")
    @patch("git_commit_plugin.sys.exit")
    def test_run__no_changes_detected(
        self, mock_exit, mock_has_changes, mock_stage_files, tmp_path, capsys
    ):
        """Test run exits 0 when _has_changes returns False."""
        hook_info = make_hook_info(tmp_path)
        hook_info.workspace_dir.mkdir(parents=True)
        artifacts_dir = hook_info.workspace_dir / ".cpa-workflow-artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "wrap-up-report-20240101.md").write_text("report content")

        mock_stage_files.side_effect = [None]
        mock_has_changes.side_effect = [False]
        mock_exit.side_effect = [SystemExit(0)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_calls = [call(hook_info.workspace_dir)]
        assert mock_stage_files.mock_calls == exp_calls
        assert mock_has_changes.mock_calls == exp_calls

        # Verify print calls for wrap-up found and no changes detected
        captured = capsys.readouterr()
        assert "Wrap-up report found: wrap-up-report-20240101.md" in captured.err
        assert "No changes detected in plugin directory" in captured.err

        exp_exit_calls = [call(0)]
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("git_commit_plugin.GitCommitPlugin._stage_files")
    @patch("git_commit_plugin.GitCommitPlugin._commit_and_push")
    @patch("git_commit_plugin.GitCommitPlugin._has_changes")
    @patch("git_commit_plugin.sys.exit")
    def test_run__success(
        self, mock_exit, mock_has_changes, mock_commit_and_push, mock_stage_files, tmp_path, capsys
    ):
        """Test run exits 0 on successful commit and push."""
        hook_info = make_hook_info(tmp_path)
        hook_info.workspace_dir.mkdir(parents=True)
        artifacts_dir = hook_info.workspace_dir / ".cpa-workflow-artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "wrap-up-report-20240101.md").write_text("report content")

        mock_stage_files.side_effect = [None]
        mock_has_changes.side_effect = [True]
        mock_commit_and_push.side_effect = [None]
        mock_exit.side_effect = [SystemExit(0)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_calls = [call(hook_info.workspace_dir)]
        assert mock_stage_files.mock_calls == exp_calls
        assert mock_has_changes.mock_calls == exp_calls
        assert mock_commit_and_push.mock_calls == exp_calls

        # Verify print calls for wrap-up found and committing
        captured = capsys.readouterr()
        assert "Wrap-up report found: wrap-up-report-20240101.md" in captured.err
        assert "Committing plugin changes..." in captured.err

        exp_exit_calls = [call(0)]
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("git_commit_plugin.GitCommitPlugin._stage_files")
    @patch("git_commit_plugin.GitCommitPlugin._commit_and_push")
    @patch("git_commit_plugin.GitCommitPlugin._has_changes")
    @patch("git_commit_plugin.sys.exit")
    def test_run__subprocess_error(
        self, mock_exit, mock_has_changes, mock_commit_and_push, mock_stage_files, tmp_path, capsys
    ):
        """Test run exits 1 when subprocess.CalledProcessError is raised."""
        hook_info = make_hook_info(tmp_path)
        hook_info.workspace_dir.mkdir(parents=True)
        artifacts_dir = hook_info.workspace_dir / ".cpa-workflow-artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "wrap-up-report-20240101.md").write_text("report content")

        mock_stage_files.side_effect = [None]
        mock_has_changes.side_effect = [True]
        error = subprocess.CalledProcessError(1, "git push", stderr="push failed")
        mock_commit_and_push.side_effect = [error]
        mock_exit.side_effect = [SystemExit(1)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_calls = [call(hook_info.workspace_dir)]
        assert mock_stage_files.mock_calls == exp_calls
        assert mock_has_changes.mock_calls == exp_calls
        assert mock_commit_and_push.mock_calls == exp_calls

        # Verify print was called with error message to stderr
        captured = capsys.readouterr()
        assert "Wrap-up report found" in captured.err
        assert "Committing plugin changes..." in captured.err
        assert "Git command failed:" in captured.err

        exp_exit_calls = [call(1)]
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("git_commit_plugin.GitCommitPlugin._stage_files")
    @patch("git_commit_plugin.GitCommitPlugin._commit_and_push")
    @patch("git_commit_plugin.GitCommitPlugin._has_changes")
    @patch("git_commit_plugin.sys.exit")
    def test_run__generic_error(
        self, mock_exit, mock_has_changes, mock_commit_and_push, mock_stage_files, tmp_path, capsys
    ):
        """Test run exits 1 when a generic Exception is raised."""
        hook_info = make_hook_info(tmp_path)
        hook_info.workspace_dir.mkdir(parents=True)
        artifacts_dir = hook_info.workspace_dir / ".cpa-workflow-artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "wrap-up-report-20240101.md").write_text("report content")

        mock_stage_files.side_effect = [None]
        mock_has_changes.side_effect = [True]
        mock_commit_and_push.side_effect = [Exception("Unexpected error occurred")]
        mock_exit.side_effect = [SystemExit(1)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_calls = [call(hook_info.workspace_dir)]
        assert mock_stage_files.mock_calls == exp_calls
        assert mock_has_changes.mock_calls == exp_calls
        assert mock_commit_and_push.mock_calls == exp_calls

        # Verify print was called with error message to stderr
        captured = capsys.readouterr()
        assert "Wrap-up report found" in captured.err
        assert "Committing plugin changes..." in captured.err
        assert "Error in git commit hook:" in captured.err

        exp_exit_calls = [call(1)]
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("git_commit_plugin.GitCommitPlugin._stage_files")
    @patch("git_commit_plugin.GitCommitPlugin._has_changes")
    @patch("git_commit_plugin.sys.exit")
    def test_run__multiple_reports_selects_most_recent(
        self, mock_exit, mock_has_changes, mock_stage_files, tmp_path, capsys
    ):
        """Test run selects the most recent wrap-up report by mtime."""
        hook_info = make_hook_info(tmp_path)
        hook_info.workspace_dir.mkdir(parents=True)
        artifacts_dir = hook_info.workspace_dir / ".cpa-workflow-artifacts"
        artifacts_dir.mkdir()

        # Create multiple reports with different mtimes
        report_old = artifacts_dir / "wrap-up-report-old.md"
        report_old.write_text("old report")

        time.sleep(0.01)  # Ensure different mtime
        report_newest = artifacts_dir / "wrap-up-report-newest.md"
        report_newest.write_text("newest report")

        mock_stage_files.side_effect = [None]
        mock_has_changes.side_effect = [False]
        mock_exit.side_effect = [SystemExit(0)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_calls = [call(hook_info.workspace_dir)]
        assert mock_stage_files.mock_calls == exp_calls
        assert mock_has_changes.mock_calls == exp_calls

        # Verify the print shows the most recent report
        captured = capsys.readouterr()
        assert "wrap-up-report-newest.md" in captured.err

        exp_exit_calls = [call(0)]
        assert mock_exit.mock_calls == exp_exit_calls

    # ==================== _has_changes() tests ====================

    @patch("git_commit_plugin.subprocess.run")
    @patch("git_commit_plugin.os.chdir")
    @patch("git_commit_plugin.Path.cwd")
    def test__has_changes__has_changes(
        self, mock_cwd, mock_chdir, mock_subprocess_run, tmp_path
    ):
        """Test _has_changes returns True when there are uncommitted changes."""
        mock_cwd.side_effect = [tmp_path]

        mock_result = SimpleNamespace(stdout="M  modified_file.py\n")
        mock_subprocess_run.side_effect = [mock_result]

        plugin_dir = tmp_path / "my-plugin"
        plugin_dir.mkdir()

        tested = GitCommitPlugin

        result = tested._has_changes(plugin_dir)

        expected = True
        assert result is expected

        exp_cwd_calls = [call()]
        assert mock_cwd.mock_calls == exp_cwd_calls

        exp_chdir_calls = [call(plugin_dir), call(tmp_path)]
        assert mock_chdir.mock_calls == exp_chdir_calls

        exp_subprocess_run_calls = [
            call(
                ["git", "status", "--porcelain", "."],
                check=True,
                capture_output=True,
                text=True,
            )
        ]
        assert mock_subprocess_run.mock_calls == exp_subprocess_run_calls

    @patch("git_commit_plugin.subprocess.run")
    @patch("git_commit_plugin.os.chdir")
    @patch("git_commit_plugin.Path.cwd")
    def test__has_changes__no_changes(
        self, mock_cwd, mock_chdir, mock_subprocess_run, tmp_path
    ):
        """Test _has_changes returns False when there are no uncommitted changes."""
        mock_cwd.side_effect = [tmp_path]

        mock_result = SimpleNamespace(stdout="")
        mock_subprocess_run.side_effect = [mock_result]

        plugin_dir = tmp_path / "my-plugin"
        plugin_dir.mkdir()

        tested = GitCommitPlugin

        result = tested._has_changes(plugin_dir)

        expected = False
        assert result is expected

        exp_cwd_calls = [call()]
        assert mock_cwd.mock_calls == exp_cwd_calls

        exp_chdir_calls = [call(plugin_dir), call(tmp_path)]
        assert mock_chdir.mock_calls == exp_chdir_calls

        exp_subprocess_run_calls = [
            call(
                ["git", "status", "--porcelain", "."],
                check=True,
                capture_output=True,
                text=True,
            )
        ]
        assert mock_subprocess_run.mock_calls == exp_subprocess_run_calls

    @patch("git_commit_plugin.subprocess.run")
    @patch("git_commit_plugin.os.chdir")
    @patch("git_commit_plugin.Path.cwd")
    def test__has_changes__whitespace_only_output(
        self, mock_cwd, mock_chdir, mock_subprocess_run, tmp_path
    ):
        """Test _has_changes returns False when output is whitespace only."""
        mock_cwd.side_effect = [tmp_path]

        mock_result = SimpleNamespace(stdout="   \n\t\n  ")
        mock_subprocess_run.side_effect = [mock_result]

        plugin_dir = tmp_path / "my-plugin"
        plugin_dir.mkdir()

        tested = GitCommitPlugin

        result = tested._has_changes(plugin_dir)

        expected = False
        assert result is expected

        exp_cwd_calls = [call()]
        assert mock_cwd.mock_calls == exp_cwd_calls

        exp_chdir_calls = [call(plugin_dir), call(tmp_path)]
        assert mock_chdir.mock_calls == exp_chdir_calls

        exp_subprocess_run_calls = [
            call(
                ["git", "status", "--porcelain", "."],
                check=True,
                capture_output=True,
                text=True,
            )
        ]
        assert mock_subprocess_run.mock_calls == exp_subprocess_run_calls

    # ==================== _stage_files() tests ====================

    @patch("git_commit_plugin.subprocess.run")
    @patch("git_commit_plugin.os.chdir")
    @patch("git_commit_plugin.Path.cwd")
    def test__stage_files__success(
        self, mock_cwd, mock_chdir, mock_subprocess_run, tmp_path
    ):
        """Test _stage_files stages all files and restores cwd."""
        mock_cwd.side_effect = [tmp_path]

        mock_add_result = SimpleNamespace()
        mock_subprocess_run.side_effect = [mock_add_result]

        plugin_dir = tmp_path / "my-plugin"
        plugin_dir.mkdir()

        tested = GitCommitPlugin

        tested._stage_files(plugin_dir)

        exp_cwd_calls = [call()]
        assert mock_cwd.mock_calls == exp_cwd_calls

        exp_chdir_calls = [call(plugin_dir), call(tmp_path)]
        assert mock_chdir.mock_calls == exp_chdir_calls

        exp_subprocess_run_calls = [
            call(
                ["git", "add", "-A", "."],
                check=True,
                capture_output=True,
                text=True,
            )
        ]
        assert mock_subprocess_run.mock_calls == exp_subprocess_run_calls

    @patch("git_commit_plugin.subprocess.run")
    @patch("git_commit_plugin.os.chdir")
    @patch("git_commit_plugin.Path.cwd")
    def test__stage_files__restores_cwd_on_exception(
        self, mock_cwd, mock_chdir, mock_subprocess_run, tmp_path
    ):
        """Test _stage_files restores original cwd even when exception occurs."""
        mock_cwd.side_effect = [tmp_path]

        mock_subprocess_run.side_effect = [
            subprocess.CalledProcessError(1, "git add")
        ]

        plugin_dir = tmp_path / "my-plugin"
        plugin_dir.mkdir()

        tested = GitCommitPlugin

        with pytest.raises(subprocess.CalledProcessError):
            tested._stage_files(plugin_dir)

        exp_cwd_calls = [call()]
        assert mock_cwd.mock_calls == exp_cwd_calls

        exp_chdir_calls = [call(plugin_dir), call(tmp_path)]
        assert mock_chdir.mock_calls == exp_chdir_calls

        exp_subprocess_run_calls = [
            call(
                ["git", "add", "-A", "."],
                check=True,
                capture_output=True,
                text=True,
            )
        ]
        assert mock_subprocess_run.mock_calls == exp_subprocess_run_calls

    # ==================== _commit_and_push() tests ====================

    @patch("git_commit_plugin.subprocess.run")
    @patch("git_commit_plugin.os.chdir")
    @patch("git_commit_plugin.Path.cwd")
    def test__commit_and_push__with_changes(
        self, mock_cwd, mock_chdir, mock_subprocess_run, tmp_path, capsys
    ):
        """Test _commit_and_push commits and pushes when there are staged changes."""
        mock_cwd.side_effect = [tmp_path]

        mock_add_result = SimpleNamespace()
        mock_diff_result = SimpleNamespace(returncode=1)  # Non-zero means there are staged changes
        mock_commit_result = SimpleNamespace()
        mock_push_result = SimpleNamespace()
        mock_subprocess_run.side_effect = [
            mock_add_result,
            mock_diff_result,
            mock_commit_result,
            mock_push_result,
        ]

        plugin_dir = tmp_path / "my-test-plugin"
        plugin_dir.mkdir()

        tested = GitCommitPlugin

        tested._commit_and_push(plugin_dir)

        exp_cwd_calls = [call()]
        assert mock_cwd.mock_calls == exp_cwd_calls

        exp_chdir_calls = [call(plugin_dir), call(tmp_path)]
        assert mock_chdir.mock_calls == exp_chdir_calls

        exp_commit_message = (
            "complete my-test-plugin wrap-up\n\n"
            "Co-Authored-By: Claude <noreply@anthropic.com>"
        )
        exp_subprocess_run_calls = [
            call(
                ["git", "add", "-A", "."],
                check=True,
                capture_output=True,
                text=True,
            ),
            call(["git", "diff", "--cached", "--quiet"], capture_output=True),
            call(
                ["git", "commit", "-m", exp_commit_message],
                check=True,
                capture_output=True,
                text=True,
            ),
            call(["git", "push"], check=True, capture_output=True, text=True),
        ]
        assert mock_subprocess_run.mock_calls == exp_subprocess_run_calls

        # Verify success message printed to stderr
        captured = capsys.readouterr()
        assert "Plugin changes committed and pushed" in captured.err

    @patch("git_commit_plugin.subprocess.run")
    @patch("git_commit_plugin.os.chdir")
    @patch("git_commit_plugin.Path.cwd")
    def test__commit_and_push__no_staged_changes(
        self, mock_cwd, mock_chdir, mock_subprocess_run, tmp_path, capsys
    ):
        """Test _commit_and_push prints message when there are no staged changes."""
        mock_cwd.side_effect = [tmp_path]

        mock_add_result = SimpleNamespace()
        mock_diff_result = SimpleNamespace(returncode=0)  # Zero means no staged changes
        mock_subprocess_run.side_effect = [mock_add_result, mock_diff_result]

        plugin_dir = tmp_path / "my-test-plugin"
        plugin_dir.mkdir()

        tested = GitCommitPlugin

        tested._commit_and_push(plugin_dir)

        exp_cwd_calls = [call()]
        assert mock_cwd.mock_calls == exp_cwd_calls

        exp_chdir_calls = [call(plugin_dir), call(tmp_path)]
        assert mock_chdir.mock_calls == exp_chdir_calls

        exp_subprocess_run_calls = [
            call(
                ["git", "add", "-A", "."],
                check=True,
                capture_output=True,
                text=True,
            ),
            call(["git", "diff", "--cached", "--quiet"], capture_output=True),
        ]
        assert mock_subprocess_run.mock_calls == exp_subprocess_run_calls

        # Verify "No changes to commit" printed to stderr
        captured = capsys.readouterr()
        assert "No changes to commit" in captured.err

    @patch("git_commit_plugin.subprocess.run")
    @patch("git_commit_plugin.os.chdir")
    @patch("git_commit_plugin.Path.cwd")
    def test__commit_and_push__restores_cwd_on_exception(
        self, mock_cwd, mock_chdir, mock_subprocess_run, tmp_path, capsys
    ):
        """Test _commit_and_push restores original cwd even when exception occurs."""
        mock_cwd.side_effect = [tmp_path]

        mock_subprocess_run.side_effect = [
            subprocess.CalledProcessError(1, "git add")
        ]

        plugin_dir = tmp_path / "my-test-plugin"
        plugin_dir.mkdir()

        tested = GitCommitPlugin

        with pytest.raises(subprocess.CalledProcessError):
            tested._commit_and_push(plugin_dir)

        exp_cwd_calls = [call()]
        assert mock_cwd.mock_calls == exp_cwd_calls

        # Verify cwd is restored even after exception
        exp_chdir_calls = [call(plugin_dir), call(tmp_path)]
        assert mock_chdir.mock_calls == exp_chdir_calls

        exp_subprocess_run_calls = [
            call(
                ["git", "add", "-A", "."],
                check=True,
                capture_output=True,
                text=True,
            )
        ]
        assert mock_subprocess_run.mock_calls == exp_subprocess_run_calls

        # No output expected (no print calls)
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""
