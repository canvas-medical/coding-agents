"""Tests for git_commit_plugin module."""

import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, call, patch

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

    @patch("git_commit_plugin.print")
    @patch("git_commit_plugin.GitCommitPlugin._has_changes")
    @patch("git_commit_plugin.sys.exit")
    def test_run__no_changes_detected(
        self, mock_exit, mock_has_changes, mock_print, tmp_path
    ):
        """Test run exits 0 when _has_changes returns False."""
        hook_info = make_hook_info(tmp_path)
        hook_info.workspace_dir.mkdir(parents=True)
        artifacts_dir = hook_info.workspace_dir / ".cpa-workflow-artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "wrap-up-report-20240101.md").write_text("report content")

        mock_has_changes.side_effect = [False]
        mock_exit.side_effect = [SystemExit(0)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_has_changes_calls = [call(hook_info.workspace_dir)]
        assert mock_has_changes.mock_calls == exp_has_changes_calls

        # Verify print calls for wrap-up found and no changes detected
        assert len(mock_print.mock_calls) == 2
        assert "Wrap-up report found: wrap-up-report-20240101.md" in str(
            mock_print.mock_calls[0]
        )
        assert "No changes detected in plugin directory" in str(mock_print.mock_calls[1])

        exp_exit_calls = [call(0)]
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("git_commit_plugin.print")
    @patch("git_commit_plugin.GitCommitPlugin._commit_and_push")
    @patch("git_commit_plugin.GitCommitPlugin._has_changes")
    @patch("git_commit_plugin.sys.exit")
    def test_run__success(
        self, mock_exit, mock_has_changes, mock_commit_and_push, mock_print, tmp_path
    ):
        """Test run exits 0 on successful commit and push."""
        hook_info = make_hook_info(tmp_path)
        hook_info.workspace_dir.mkdir(parents=True)
        artifacts_dir = hook_info.workspace_dir / ".cpa-workflow-artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "wrap-up-report-20240101.md").write_text("report content")

        mock_has_changes.side_effect = [True]
        mock_commit_and_push.side_effect = [None]
        mock_exit.side_effect = [SystemExit(0)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_has_changes_calls = [call(hook_info.workspace_dir)]
        assert mock_has_changes.mock_calls == exp_has_changes_calls

        exp_commit_and_push_calls = [call(hook_info.workspace_dir)]
        assert mock_commit_and_push.mock_calls == exp_commit_and_push_calls

        # Verify print calls for wrap-up found and committing
        assert len(mock_print.mock_calls) == 2
        assert "Wrap-up report found: wrap-up-report-20240101.md" in str(
            mock_print.mock_calls[0]
        )
        assert "Committing plugin changes..." in str(mock_print.mock_calls[1])

        exp_exit_calls = [call(0)]
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("git_commit_plugin.print")
    @patch("git_commit_plugin.GitCommitPlugin._commit_and_push")
    @patch("git_commit_plugin.GitCommitPlugin._has_changes")
    @patch("git_commit_plugin.sys.exit")
    def test_run__subprocess_error(
        self, mock_exit, mock_has_changes, mock_commit_and_push, mock_print, tmp_path
    ):
        """Test run exits 1 when subprocess.CalledProcessError is raised."""
        hook_info = make_hook_info(tmp_path)
        hook_info.workspace_dir.mkdir(parents=True)
        artifacts_dir = hook_info.workspace_dir / ".cpa-workflow-artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "wrap-up-report-20240101.md").write_text("report content")

        mock_has_changes.side_effect = [True]
        error = subprocess.CalledProcessError(1, "git push", stderr="push failed")
        mock_commit_and_push.side_effect = [error]
        mock_exit.side_effect = [SystemExit(1)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_has_changes_calls = [call(hook_info.workspace_dir)]
        assert mock_has_changes.mock_calls == exp_has_changes_calls

        exp_commit_and_push_calls = [call(hook_info.workspace_dir)]
        assert mock_commit_and_push.mock_calls == exp_commit_and_push_calls

        # Verify print was called with error message to stderr
        assert len(mock_print.mock_calls) == 3
        assert "Wrap-up report found" in str(mock_print.mock_calls[0])
        assert "Committing plugin changes..." in str(mock_print.mock_calls[1])
        assert "Git command failed:" in str(mock_print.mock_calls[2])

        exp_exit_calls = [call(1)]
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("git_commit_plugin.print")
    @patch("git_commit_plugin.GitCommitPlugin._commit_and_push")
    @patch("git_commit_plugin.GitCommitPlugin._has_changes")
    @patch("git_commit_plugin.sys.exit")
    def test_run__generic_error(
        self, mock_exit, mock_has_changes, mock_commit_and_push, mock_print, tmp_path
    ):
        """Test run exits 1 when a generic Exception is raised."""
        hook_info = make_hook_info(tmp_path)
        hook_info.workspace_dir.mkdir(parents=True)
        artifacts_dir = hook_info.workspace_dir / ".cpa-workflow-artifacts"
        artifacts_dir.mkdir()
        (artifacts_dir / "wrap-up-report-20240101.md").write_text("report content")

        mock_has_changes.side_effect = [True]
        mock_commit_and_push.side_effect = [Exception("Unexpected error occurred")]
        mock_exit.side_effect = [SystemExit(1)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_has_changes_calls = [call(hook_info.workspace_dir)]
        assert mock_has_changes.mock_calls == exp_has_changes_calls

        exp_commit_and_push_calls = [call(hook_info.workspace_dir)]
        assert mock_commit_and_push.mock_calls == exp_commit_and_push_calls

        # Verify print was called with error message to stderr
        assert len(mock_print.mock_calls) == 3
        assert "Wrap-up report found" in str(mock_print.mock_calls[0])
        assert "Committing plugin changes..." in str(mock_print.mock_calls[1])
        assert "Error in git commit hook:" in str(mock_print.mock_calls[2])

        exp_exit_calls = [call(1)]
        assert mock_exit.mock_calls == exp_exit_calls

    @patch("git_commit_plugin.print")
    @patch("git_commit_plugin.GitCommitPlugin._has_changes")
    @patch("git_commit_plugin.sys.exit")
    def test_run__multiple_reports_selects_most_recent(
        self, mock_exit, mock_has_changes, mock_print, tmp_path
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

        mock_has_changes.side_effect = [False]
        mock_exit.side_effect = [SystemExit(0)]

        tested = GitCommitPlugin

        with pytest.raises(SystemExit):
            tested.run(hook_info)

        exp_has_changes_calls = [call(hook_info.workspace_dir)]
        assert mock_has_changes.mock_calls == exp_has_changes_calls

        # Verify the print shows the most recent report
        assert len(mock_print.mock_calls) == 2
        assert "wrap-up-report-newest.md" in str(mock_print.mock_calls[0])

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

        mock_result = MagicMock()
        mock_result.stdout = "M  modified_file.py\n"
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

        mock_result = MagicMock()
        mock_result.stdout = ""
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

        mock_result = MagicMock()
        mock_result.stdout = "   \n\t\n  "
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

    # ==================== _commit_and_push() tests ====================

    @patch("git_commit_plugin.print")
    @patch("git_commit_plugin.subprocess.run")
    @patch("git_commit_plugin.os.chdir")
    @patch("git_commit_plugin.Path.cwd")
    def test__commit_and_push__with_changes(
        self, mock_cwd, mock_chdir, mock_subprocess_run, mock_print, tmp_path
    ):
        """Test _commit_and_push commits and pushes when there are staged changes."""
        mock_cwd.side_effect = [tmp_path]

        mock_add_result = MagicMock()
        mock_diff_result = MagicMock()
        mock_diff_result.returncode = 1  # Non-zero means there are staged changes
        mock_commit_result = MagicMock()
        mock_push_result = MagicMock()
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
        assert len(mock_print.mock_calls) == 1
        assert "Plugin changes committed and pushed" in str(mock_print.mock_calls[0])

    @patch("git_commit_plugin.print")
    @patch("git_commit_plugin.subprocess.run")
    @patch("git_commit_plugin.os.chdir")
    @patch("git_commit_plugin.Path.cwd")
    def test__commit_and_push__no_staged_changes(
        self, mock_cwd, mock_chdir, mock_subprocess_run, mock_print, tmp_path
    ):
        """Test _commit_and_push prints message when there are no staged changes."""
        mock_cwd.side_effect = [tmp_path]

        mock_add_result = MagicMock()
        mock_diff_result = MagicMock()
        mock_diff_result.returncode = 0  # Zero means no staged changes
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
        assert len(mock_print.mock_calls) == 1
        assert "No changes to commit" in str(mock_print.mock_calls[0])

    @patch("git_commit_plugin.print")
    @patch("git_commit_plugin.subprocess.run")
    @patch("git_commit_plugin.os.chdir")
    @patch("git_commit_plugin.Path.cwd")
    def test__commit_and_push__restores_cwd_on_exception(
        self, mock_cwd, mock_chdir, mock_subprocess_run, mock_print, tmp_path
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

        assert mock_print.mock_calls == []
