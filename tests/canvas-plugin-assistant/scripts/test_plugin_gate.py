"""Tests for plugin_gate.py, the PreToolUse gate that runs `canvas validate`."""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

import plugin_gate


def _plugin(root: Path, name: str = "acme_intake") -> Path:
    plugin = root / name
    plugin.mkdir(parents=True)
    (plugin / "CANVAS_MANIFEST.json").write_text("{}")
    return plugin


def _bash(cwd: Path, command: str = "git commit -m change") -> str:
    return json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)})


def _completed(returncode: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


class TestFindPluginDir:
    """Tests for find_plugin_dir."""

    def test_finds_the_plugin_from_inside_it(self, tmp_path: Path) -> None:
        """A cwd inside the plugin package resolves to the package."""
        plugin = _plugin(tmp_path)
        (plugin / "handlers").mkdir()

        assert plugin_gate.find_plugin_dir(plugin / "handlers") == plugin

    def test_finds_the_only_plugin_inside_a_repository_root(self, tmp_path: Path) -> None:
        """A repository root holding one plugin package resolves to that package."""
        plugin = _plugin(tmp_path)

        assert plugin_gate.find_plugin_dir(tmp_path) == plugin

    def test_finds_nothing_with_several_plugins_or_none(self, tmp_path: Path) -> None:
        """Several candidate packages, or a directory with no manifest anywhere, resolve to None."""
        _plugin(tmp_path / "several", "one")
        _plugin(tmp_path / "several", "two")
        (tmp_path / "unrelated").mkdir()

        assert plugin_gate.find_plugin_dir(tmp_path / "several") is None
        assert plugin_gate.find_plugin_dir(tmp_path / "unrelated") is None

    def test_finds_nothing_under_a_missing_directory(self, tmp_path: Path) -> None:
        """A path that does not exist resolves to None rather than raising."""
        assert plugin_gate.find_plugin_dir(tmp_path / "missing") is None


class TestTargetDir:
    """Tests for target_dir."""

    def test_the_installer_tool_targets_its_plugin_name_under_its_cwd(self, tmp_path: Path) -> None:
        """The MCP installer names the plugin and the directory it runs in."""
        plugin = _plugin(tmp_path)
        payload = {
            "tool_name": "mcp__plugin_cpa_canvas_cmd_line__installer",
            "tool_input": {"plugin_name": "acme_intake", "instance": "acme-dev", "cwd": str(tmp_path)},
            "cwd": "/elsewhere",
        }

        assert plugin_gate.target_dir(payload) == plugin

    def test_a_bash_call_targets_the_plugin_at_its_cwd(self, tmp_path: Path) -> None:
        """A Bash call resolves from the session's cwd."""
        plugin = _plugin(tmp_path)

        assert plugin_gate.target_dir(json.loads(_bash(tmp_path))) == plugin


class TestValidateCommand:
    """Tests for validate_command."""

    def test_a_uv_project_uses_its_own_canvas(self, tmp_path: Path) -> None:
        """A CPA project's `[project]` pins canvas, so its version wins over an older one on PATH."""
        plugin = _plugin(tmp_path)
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "acme"\ndependencies = ["canvas"]\n')
        with patch("plugin_gate.shutil.which", return_value="/usr/local/bin/canvas"):
            assert plugin_gate.validate_command(plugin) == ["uv", "run", "canvas", "validate", str(plugin)]

    def test_a_pyproject_without_a_project_table_uses_canvas_from_path(self, tmp_path: Path) -> None:
        """Studio's workspace pyproject has no `[project]`, where `uv run` exits before canvas starts."""
        plugin = _plugin(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[tool.coverage.run]\nsource = ['acme_intake']\n")
        with patch("plugin_gate.shutil.which", return_value="/usr/local/bin/canvas"):
            assert plugin_gate.validate_command(plugin) == ["canvas", "validate", str(plugin)]

    def test_no_canvas_on_path_falls_back_to_uv(self, tmp_path: Path) -> None:
        """With no pyproject and no `canvas` on PATH, uv is the only way to reach one."""
        with patch("plugin_gate.shutil.which", return_value=None):
            assert plugin_gate.validate_command(tmp_path) == ["uv", "run", "canvas", "validate", str(tmp_path)]


class TestRunValidate:
    """Tests for run_validate."""

    def test_a_passing_validate_has_nothing_to_fix(self, tmp_path: Path) -> None:
        """Exit 0 from `canvas validate` returns None."""
        with patch("plugin_gate.subprocess.run", return_value=_completed(0)):
            assert plugin_gate.run_validate(tmp_path) is None

    def test_a_failing_validate_returns_its_output(self, tmp_path: Path) -> None:
        """Both streams reach the agent, since handler loads print to stdout and errors to stderr."""
        failed = _completed(1, stdout="h.py:1 [type-blocked]", stderr="1 handler failed")
        with patch("plugin_gate.subprocess.run", return_value=failed):
            problem = plugin_gate.run_validate(tmp_path)

        assert problem is not None
        assert "h.py:1 [type-blocked]\n1 handler failed" in problem

    def test_a_cli_too_old_for_validate_is_not_read_as_plugin_errors(self, tmp_path: Path) -> None:
        """canvas releases before `validate` answer "No such command", which says nothing about the plugin."""
        too_old = _completed(2, stderr="Error: No such command 'validate'. Did you mean 'validate-manifest'?")
        with patch("plugin_gate.subprocess.run", return_value=too_old):
            problem = plugin_gate.run_validate(tmp_path)

        assert problem == (
            "`canvas validate` could not run: this canvas CLI predates it. Upgrade the `canvas` package."
        )

    def test_a_silent_failure_still_says_so(self, tmp_path: Path) -> None:
        """A non-zero exit with no output is still a failure."""
        with patch("plugin_gate.subprocess.run", return_value=_completed(1)):
            assert "(no output)" in plugin_gate.run_validate(tmp_path)

    @pytest.mark.parametrize(
        ("error", "expected"),
        [
            pytest.param(FileNotFoundError("uv"), "could not start", id="not_on_path"),
            pytest.param(subprocess.TimeoutExpired(["canvas"], 120), "did not finish within 120", id="timeout"),
        ],
    )
    def test_a_validate_that_cannot_run_is_a_problem(self, tmp_path: Path, error: Exception, expected: str) -> None:
        """A check that could not run is reported, never read as a pass."""
        with patch("plugin_gate.subprocess.run", side_effect=error):
            assert expected in plugin_gate.run_validate(tmp_path)


class TestMain:
    """Tests for main, the hook entry point."""

    def test_off_by_default_runs_nothing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """With CPA_PLUGIN_GATE unset the hook exits 0 before reading anything."""
        monkeypatch.delenv("CPA_PLUGIN_GATE", raising=False)
        _plugin(tmp_path)
        with patch("plugin_gate.subprocess.run") as run:
            assert plugin_gate.main(_bash(tmp_path)) == 0
        run.assert_not_called()

    def test_an_unknown_mode_is_a_visible_non_blocking_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A misspelled mode exits 1, which Claude Code shows without blocking."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "blocking")

        assert plugin_gate.main(_bash(tmp_path)) == 1
        assert "'blocking' is not one of off, advise, block" in capsys.readouterr().err

    def test_a_call_outside_any_plugin_passes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A commit in an unrelated repository is not the gate's business."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        with patch("plugin_gate.subprocess.run") as run:
            assert plugin_gate.main(_bash(tmp_path)) == 0
        run.assert_not_called()

    def test_a_passing_plugin_passes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A plugin that validates lets the call through silently."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        _plugin(tmp_path)
        with patch("plugin_gate.subprocess.run", return_value=_completed(0)):
            assert plugin_gate.main(_bash(tmp_path)) == 0

    def test_block_mode_stops_a_failing_plugin(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Exit 2 blocks the tool call, and stderr is the reason Claude reads."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        _plugin(tmp_path)
        with patch("plugin_gate.subprocess.run", return_value=_completed(1, stdout="h.py:1 [type-blocked]")):
            assert plugin_gate.main(_bash(tmp_path)) == 2

        err = capsys.readouterr().err
        assert err.startswith("CPA plugin gate (acme_intake):")
        assert "h.py:1 [type-blocked]" in err

    def test_advise_mode_reports_without_stopping(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Exit 0 with additionalContext hands the findings to Claude and lets the call run."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "Advise")
        _plugin(tmp_path)
        with patch("plugin_gate.subprocess.run", return_value=_completed(1, stdout="h.py:1 [type-blocked]")):
            assert plugin_gate.main(_bash(tmp_path)) == 0

        output = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
        assert output["hookEventName"] == "PreToolUse"
        assert output["additionalContext"].startswith("CPA plugin gate, advisory only (CPA_PLUGIN_GATE=advise)")
        assert "h.py:1 [type-blocked]" in output["additionalContext"]
