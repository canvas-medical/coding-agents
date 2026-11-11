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


# A warning line as `canvas validate` prints it (captured from canvas 0.269.0).
WARNING = (
    "  ⚠ handlers/h.py:1  [custom-model-id-vs-dbid]  `Widget.objects.filter(id=…)` — CustomModels use `dbid` "
    "as their primary key (only core SDK models have `id`). Use `dbid=…` instead."
)


def _installer(session: Path, tool_input: dict) -> dict:
    return {
        "tool_name": "mcp__plugin_cpa_canvas_cmd_line__installer",
        "tool_input": {"instance": "acme-dev", **tool_input},
        "cwd": str(session),
    }


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
        container = tmp_path / "acme-intake"
        plugin = _plugin(container)
        payload = _installer(tmp_path, {"plugin_name": "acme_intake", "cwd": str(container)})

        assert plugin_gate.target_dir(payload) == plugin

    @pytest.mark.parametrize(
        "tool_input",
        [
            pytest.param({"plugin_name": "acme_intake", "cwd": "/"}, id="cwd_outside_the_session"),
            pytest.param({"plugin_name": "../outside"}, id="parent_traversal"),
            pytest.param({"plugin_name": "/etc"}, id="absolute_name"),
            pytest.param({"plugin_name": ""}, id="empty_name"),
        ],
    )
    def test_the_installer_tool_never_reaches_outside_the_session(self, tmp_path: Path, tool_input: dict) -> None:
        """The hook runs before approval, so a target outside the session's cwd is not checked."""
        session = tmp_path / "session"
        _plugin(session)
        _plugin(tmp_path, "outside")

        with pytest.raises(plugin_gate.OutsideSession):
            plugin_gate.target_dir(_installer(session, tool_input))

    def test_a_bash_call_targets_the_plugin_at_its_cwd(self, tmp_path: Path) -> None:
        """A Bash call resolves from the session's cwd."""
        plugin = _plugin(tmp_path)

        assert plugin_gate.target_dir(json.loads(_bash(tmp_path))) == plugin


class TestCanvasExecutable:
    """Tests for canvas_executable."""

    def test_the_projects_own_venv_wins_over_path(self, tmp_path: Path) -> None:
        """CPA's scaffold keeps `.venv` in the container above the plugin, pinning its canvas."""
        plugin = _plugin(tmp_path)
        venv_canvas = tmp_path / ".venv" / "bin" / "canvas"
        venv_canvas.parent.mkdir(parents=True)
        venv_canvas.write_text("")
        with patch("plugin_gate.shutil.which", return_value="/usr/local/bin/canvas"):
            assert plugin_gate.canvas_executable(plugin) == str(venv_canvas)

    def test_without_a_venv_canvas_comes_from_path(self, tmp_path: Path) -> None:
        """Studio's image installs canvas system-wide and its workspaces have no `.venv` canvas."""
        plugin = _plugin(tmp_path)
        with patch("plugin_gate.shutil.which", return_value="/usr/local/bin/canvas"):
            assert plugin_gate.canvas_executable(plugin) == "/usr/local/bin/canvas"


@pytest.fixture
def canvas_on_path():
    """A `canvas` executable to run, so these tests do not depend on the machine's PATH."""
    with patch("plugin_gate.canvas_executable", return_value="/usr/local/bin/canvas"):
        yield


@pytest.mark.usefixtures("canvas_on_path")
class TestRunValidate:
    """Tests for run_validate."""

    def test_no_canvas_anywhere_is_a_problem(self, tmp_path: Path) -> None:
        """With no project `.venv` canvas and none on PATH, the check could not run."""
        with patch("plugin_gate.canvas_executable", return_value=None):
            problem, warnings = plugin_gate.run_validate(tmp_path)

        assert "Run `uv sync`" in problem
        assert warnings == []

    def test_a_clean_pass_has_nothing_to_report(self, tmp_path: Path) -> None:
        """Exit 0 with no warnings returns no problem and no warnings."""
        clean = _completed(0, stdout="Plugin acme_intake has a valid CANVAS_MANIFEST.json file\n")
        with patch("plugin_gate.subprocess.run", return_value=clean):
            assert plugin_gate.run_validate(tmp_path) == (None, [])

    def test_a_pass_with_warnings_returns_each_warning(self, tmp_path: Path) -> None:
        """Validate exits 0 on warnings, so they are read from its output rather than its exit code."""
        warned = _completed(0, stdout=f"Plugin acme_intake has a valid CANVAS_MANIFEST.json file\n{WARNING}\n")
        with patch("plugin_gate.subprocess.run", return_value=warned):
            assert plugin_gate.run_validate(tmp_path) == (None, [WARNING.strip()])

    def test_warning_blocks_are_returned_with_their_items(self, tmp_path: Path) -> None:
        """Validate also prints `Warning:` blocks, such as handlers the manifest never loads."""
        stdout = (
            "\nWarning: Found handler classes that are not referenced in the CANVAS_MANIFEST.json:\n"
            "  - handlers.extra:Extra\n"
            "These handlers will not be loaded unless you add them to the manifest.\n\n"
            "Plugin acme_intake has a valid CANVAS_MANIFEST.json file\n"
            "  - not part of a warning\n"
        )
        with patch("plugin_gate.subprocess.run", return_value=_completed(0, stdout=stdout)):
            assert plugin_gate.run_validate(tmp_path) == (
                None,
                [
                    "Warning: Found handler classes that are not referenced in the "
                    "CANVAS_MANIFEST.json:\n  - handlers.extra:Extra"
                ],
            )

    def test_a_failing_validate_returns_its_output(self, tmp_path: Path) -> None:
        """Both streams reach the agent, since handler loads print to stdout and errors to stderr."""
        failed = _completed(1, stdout="h.py:1 [type-blocked]", stderr="1 handler failed")
        with patch("plugin_gate.subprocess.run", return_value=failed):
            problem, warnings = plugin_gate.run_validate(tmp_path)

        assert "h.py:1 [type-blocked]\n1 handler failed" in problem
        assert warnings == []

    def test_a_cli_too_old_for_validate_is_not_read_as_plugin_errors(self, tmp_path: Path) -> None:
        """canvas releases before `validate` answer "No such command", which says nothing about the plugin."""
        too_old = _completed(2, stderr="Error: No such command 'validate'. Did you mean 'validate-manifest'?")
        with patch("plugin_gate.subprocess.run", return_value=too_old):
            problem, _ = plugin_gate.run_validate(tmp_path)

        assert problem == (
            "`canvas validate` could not run: this canvas CLI predates it. Upgrade the `canvas` package."
        )

    def test_a_silent_failure_still_says_so(self, tmp_path: Path) -> None:
        """A non-zero exit with no output is still a failure."""
        with patch("plugin_gate.subprocess.run", return_value=_completed(1)):
            problem, _ = plugin_gate.run_validate(tmp_path)

        assert "(no output)" in problem

    @pytest.mark.parametrize(
        ("error", "expected"),
        [
            pytest.param(PermissionError("canvas"), "could not start (canvas)", id="not_executable"),
            pytest.param(subprocess.TimeoutExpired(["canvas"], 120), "did not finish within 120", id="timeout"),
        ],
    )
    def test_a_validate_that_cannot_run_is_a_problem(self, tmp_path: Path, error: Exception, expected: str) -> None:
        """A check that could not run is reported, never read as a pass."""
        with patch("plugin_gate.subprocess.run", side_effect=error):
            problem, warnings = plugin_gate.run_validate(tmp_path)

        assert expected in problem
        assert warnings == []


@pytest.mark.usefixtures("canvas_on_path")
class TestMain:
    """Tests for main, the hook entry point."""

    def test_off_by_default_runs_nothing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """With CPA_PLUGIN_GATE unset the hook exits 0 before reading anything."""
        monkeypatch.delenv("CPA_PLUGIN_GATE", raising=False)
        _plugin(tmp_path)
        with patch("plugin_gate.subprocess.run") as run:
            assert plugin_gate.main(_bash(tmp_path)) == 0
        run.assert_not_called()

    def test_an_unknown_mode_stops_the_call(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A misspelled mode exits 2, so the typo shows on the first gated call instead of the
        gate silently being off."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "blocking")

        assert plugin_gate.main(_bash(tmp_path)) == 2
        assert "'blocking' is not one of off, advise, block" in capsys.readouterr().err

    @pytest.mark.parametrize(("mode", "code"), [("block", 2), ("advise", 0)])
    def test_an_installer_target_outside_the_session_is_stopped_in_block_mode(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, code: int
    ) -> None:
        """An install the gate will not check is stopped in block mode and passed in advise mode."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", mode)
        payload = json.dumps(_installer(tmp_path, {"plugin_name": "../elsewhere"}))
        with patch("plugin_gate.subprocess.run") as run:
            assert plugin_gate.main(payload) == code
        run.assert_not_called()

    def test_a_call_outside_any_plugin_passes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A commit in an unrelated repository is not the gate's business."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        with patch("plugin_gate.subprocess.run") as run:
            assert plugin_gate.main(_bash(tmp_path)) == 0
        run.assert_not_called()

    def test_a_passing_plugin_passes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A plugin that validates cleanly lets the call through silently."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        _plugin(tmp_path)
        with patch("plugin_gate.subprocess.run", return_value=_completed(0)):
            assert plugin_gate.main(_bash(tmp_path)) == 0
        assert capsys.readouterr().out == ""

    @pytest.mark.parametrize("mode", ["advise", "block"])
    def test_warnings_reach_claude_in_either_mode_without_stopping(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], mode: str
    ) -> None:
        """A pass with warnings exits 0 and hands each warning to Claude as context."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", mode)
        _plugin(tmp_path)
        with patch("plugin_gate.subprocess.run", return_value=_completed(0, stdout=f"{WARNING}\n")):
            assert plugin_gate.main(_bash(tmp_path)) == 0

        context = json.loads(capsys.readouterr().out)["hookSpecificOutput"]["additionalContext"]
        assert context.startswith("CPA plugin gate: `canvas validate` passed for acme_intake with warnings.")
        assert context.endswith(WARNING.strip())

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
