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

        assert plugin_gate.target_dir(_installer(session, tool_input)) is None

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


# Fake credentials, joined at runtime so this public repository never holds one whole.
STRIPE_LIVE = "sk_" + "live_" + "Ab3" * 9
ANTHROPIC = "sk-ant-" + "api03-" + "A1b2C3" * 15
SLACK_BOT = "xox" + "b-" + "123456789012-123456789012-" + "AbCdEf123456" * 2
PEM_HEADER = "-----BEGIN " + "PRIVATE KEY-----"


def _diff(path: str, *added: str, start: int = 12) -> str:
    lines = [f"diff --git a/{path} b/{path}", f"--- a/{path}", f"+++ b/{path}", f"@@ -0,0 +{start},{len(added)} @@"]
    return "\n".join(lines + [f"+{line}" for line in added]) + "\n"


class TestScanDiff:
    """Tests for scan_diff."""

    @pytest.mark.parametrize(
        ("added", "name"),
        [
            pytest.param(f'KEY = "{STRIPE_LIVE}"', "a Stripe live key", id="stripe"),
            pytest.param(f'client = Anthropic(api_key="{ANTHROPIC}")', "an Anthropic API key", id="anthropic"),
            pytest.param(f'SLACK = "{SLACK_BOT}"', "a Slack token", id="slack"),
            pytest.param(f'"private_key": "{PEM_HEADER}\\nMIIE..."', "a private key", id="pem_in_json"),
        ],
    )
    def test_a_certain_shape_in_shipped_code_is_certain(self, added: str, name: str) -> None:
        """Each near-certain shape outside docs and tests is certain, located, and masked."""
        certain, possible = plugin_gate.scan_diff(_diff("acme_intake/handlers/h.py", added))

        assert len(certain) == 1 and possible == []
        assert certain[0].startswith(f"acme_intake/handlers/h.py:12: {name} `")
        assert added.split('"')[1] not in certain[0]

    @pytest.mark.parametrize("path", ["README.md", "acme_intake/tests/test_h.py"])
    def test_a_certain_shape_in_docs_or_tests_only_advises(self, path: str) -> None:
        """Docs and tests hold example keys, so a shape there is possible, not certain."""
        assert plugin_gate.scan_diff(_diff(path, f'KEY = "{STRIPE_LIVE}"')) == (
            [],
            [f"{path}:12: a Stripe live key `sk_l…` (35 characters)"],
        )

    def test_line_numbers_follow_each_hunk(self) -> None:
        """The second added line of a hunk is reported one past the hunk start."""
        certain, _ = plugin_gate.scan_diff(_diff("h.py", "x = 1", f'KEY = "{STRIPE_LIVE}"', start=40))
        assert certain[0].startswith("h.py:41:")

    @pytest.mark.parametrize(
        ("added", "found"),
        [
            pytest.param('API_TOKEN = "aB3dE5fG7hJ9kL1mN3pQ"', True, id="random_value_on_a_secret_name"),
            pytest.param('API_KEY_SECRET_NAME = "CANVAS_PLUGIN_SIMPLE_API_KEY"', False, id="a_secret_name"),
            pytest.param('TOKEN_URL = "https://auth.Example.com/oauth2/Token1"', False, id="a_url"),
            pytest.param('label = "aB3dE5fG7hJ9kL1mN3pQ"', False, id="not_a_secret_name"),
        ],
    )
    def test_a_secret_shaped_value_only_advises(self, added: str, found: bool) -> None:
        """A random-looking value on a secret-like name is possible; names, URLs and other fields are not."""
        certain, possible = plugin_gate.scan_diff(_diff("h.py", added))

        assert certain == []
        assert bool(possible) is found

    def test_removed_lines_are_ignored(self) -> None:
        """Deleting a credential is the fix, not a finding."""
        diff = "--- a/h.py\n+++ b/h.py\n@@ -3 +2,0 @@\n" + f'-KEY = "{STRIPE_LIVE}"\n'
        assert plugin_gate.scan_diff(diff) == ([], [])


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A git repository holding one committed plugin, `acme_intake`."""
    for variable in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(variable, "Test")
    for variable in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(variable, "test@example.com")
    plugin = _plugin(tmp_path)
    (plugin / "h.py").write_text("x = 1\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "first")
    return plugin


class TestScanCommit:
    """Tests for scan_commit, against a real git repository."""

    def test_a_staged_credential_is_found(self, repo: Path) -> None:
        """What `git commit` is about to record is read from the index."""
        (repo / "h.py").write_text(f'KEY = "{STRIPE_LIVE}"\n')
        _git(repo, "add", "h.py")

        certain, _ = plugin_gate.scan_commit(repo, "git commit -m change")

        assert [line.split(": ")[1] for line in certain] == ["a Stripe live key `sk_l…` (35 characters)"]

    def test_commit_all_also_reads_unstaged_tracked_changes(self, repo: Path) -> None:
        """`git commit -am` records tracked changes that were never staged, so they are read too."""
        (repo / "h.py").write_text(f'KEY = "{STRIPE_LIVE}"\n')

        assert plugin_gate.scan_commit(repo, "git commit -m change") == ([], [])
        assert len(plugin_gate.scan_commit(repo, "git commit -am change")[0]) == 1

    def test_added_credential_files_are_found(self, repo: Path) -> None:
        """A new `.env` or key file is certain; an example env file is not; one under tests only advises."""
        for name in (".env", ".env.example", "tests/fixture.pem"):
            path = repo / name
            path.parent.mkdir(exist_ok=True)
            path.write_text("A=1\n")
        _git(repo, "add", "-A")

        certain, possible = plugin_gate.scan_commit(repo, "git commit -m change")

        assert certain == ["acme_intake/.env: a credential file"]
        assert possible == ["acme_intake/tests/fixture.pem: a credential file"]


@pytest.mark.usefixtures("canvas_on_path")
class TestMainSecretScan:
    """Tests for main's handling of the commit secret scan."""

    def test_block_mode_stops_a_commit_adding_a_certain_credential(
        self, repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A certain credential stops the commit even when validate passes, and is never printed whole."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        (repo / "h.py").write_text(f'KEY = "{STRIPE_LIVE}"\n')
        _git(repo, "add", "h.py")
        with patch("plugin_gate.run_validate", return_value=(None, [])):
            assert plugin_gate.main(_bash(repo)) == 2

        err = capsys.readouterr().err
        assert "this commit adds what look like live credentials" in err
        assert "acme_intake/h.py:1: a Stripe live key" in err
        assert STRIPE_LIVE not in err

    def test_advise_mode_reports_a_certain_credential_without_stopping(
        self, repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """In advise mode the same finding reaches Claude as context."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "advise")
        (repo / "h.py").write_text(f'KEY = "{STRIPE_LIVE}"\n')
        _git(repo, "add", "h.py")
        with patch("plugin_gate.run_validate", return_value=(None, [])):
            assert plugin_gate.main(_bash(repo)) == 0

        context = json.loads(capsys.readouterr().out)["hookSpecificOutput"]["additionalContext"]
        assert context.startswith("CPA plugin gate, advisory only (CPA_PLUGIN_GATE=advise)")
        assert "a Stripe live key" in context

    def test_a_possible_credential_never_stops_a_commit(
        self, repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A value matched only by its shape advises, in block mode too."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        (repo / "h.py").write_text('API_TOKEN = "aB3dE5fG7hJ9kL1mN3pQ"\n')
        _git(repo, "add", "h.py")
        with patch("plugin_gate.run_validate", return_value=(None, [])):
            assert plugin_gate.main(_bash(repo)) == 0

        context = json.loads(capsys.readouterr().out)["hookSpecificOutput"]["additionalContext"]
        assert context.startswith("CPA plugin gate, for acme_intake: this commit may add credentials.")

    def test_only_a_commit_is_scanned(self, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """An install or deploy uploads the plugin, not a commit, so the commit scan does not run."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        with patch("plugin_gate.run_validate", return_value=(None, [])), patch("plugin_gate.scan_commit") as scan:
            assert plugin_gate.main(_bash(repo, "canvas deploy acme_intake")) == 0
        scan.assert_not_called()
