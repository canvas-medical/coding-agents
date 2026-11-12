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


def _bash(cwd: Path, command: str = "canvas deploy acme_intake") -> str:
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

        assert plugin_gate.target_dirs(payload, ("upload", None)) == [plugin]

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
            plugin_gate.target_dirs(_installer(session, tool_input), ("upload", None))

    def test_a_bash_call_targets_the_plugin_at_its_cwd(self, tmp_path: Path) -> None:
        """A Bash call resolves from the session's cwd."""
        plugin = _plugin(tmp_path)

        assert plugin_gate.target_dirs(json.loads(_bash(tmp_path)), ("upload", None)) == [plugin]


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
        ],
    )
    def test_a_certain_shape_in_shipped_code_is_certain(self, added: str, name: str) -> None:
        """Each near-certain shape outside docs and tests is certain, located, and masked."""
        certain, possible = plugin_gate.scan_diff(_diff("acme_intake/handlers/h.py", added))

        assert len(certain) == 1 and possible == []
        assert certain[0].startswith(f"acme_intake/handlers/h.py:12: {name} `")
        assert added.split('"')[1] not in certain[0]

    @pytest.mark.parametrize("path", ["README.md", "docs/guide.rst"])
    def test_a_certain_shape_in_a_document_only_advises(self, path: str) -> None:
        """Markdown and reST documents hold example keys, so a shape there is possible, not certain."""
        assert plugin_gate.scan_diff(_diff(path, f'KEY = "{STRIPE_LIVE}"')) == (
            [],
            [f"{path}:12: a Stripe live key `sk_l…` (35 characters)"],
        )

    @pytest.mark.parametrize("path", ["acme_intake/tests/test_h.py", "acme_intake/notes.txt"])
    def test_a_certain_shape_under_tests_or_in_text_is_still_certain(self, path: str) -> None:
        """Files under tests/ and .txt files ship with the plugin, so moving a key there is no way out."""
        certain, possible = plugin_gate.scan_diff(_diff(path, f'KEY = "{STRIPE_LIVE}"'))
        assert len(certain) == 1 and possible == []

    def test_a_private_key_only_advises(self) -> None:
        """A mutual-TLS client key can only be loaded from a file today, so it advises, and no
        part of it is shown."""
        added = f'"private_key": "{PEM_HEADER}\\nMIIEvQIBADANBg"'
        assert plugin_gate.scan_diff(_diff("acme_intake/cert/client.json", added)) == (
            [],
            ["acme_intake/cert/client.json:12: a private key (fine only if it is a mutual-TLS client key)"],
        )

    def test_a_private_key_does_not_hide_an_api_key_on_the_same_line(self) -> None:
        """A line holding both still reports the API key as certain."""
        added = f'{{"private_key": "{PEM_HEADER}", "stripe": "{STRIPE_LIVE}"}}'
        certain, possible = plugin_gate.scan_diff(_diff("acme_intake/config.json", added))

        assert [line.split(": ")[1] for line in certain] == ["a Stripe live key `sk_l…` (35 characters)"]
        assert possible == ["acme_intake/config.json:12: a private key (fine only if it is a mutual-TLS client key)"]

    def test_a_secret_shaped_value_shows_only_its_length(self) -> None:
        """A value matched only by its shape could be the secret itself, so none of it is shown."""
        _, possible = plugin_gate.scan_diff(_diff("h.py", 'API_TOKEN = "aB3dE5fG7hJ9kL1mN3pQ"'))
        assert possible == ["h.py:12: a secret-like value (20 characters)"]

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

    def test_an_added_line_cannot_pose_as_a_file_header(self) -> None:
        """Added content reading "++ b/README.md" shows as "+++ b/README.md" and must stay content,
        or every finding after it would be read as docs and only advise."""
        certain, possible = plugin_gate.scan_diff(
            _diff("acme_intake/h.py", "++ b/README.md", f'KEY = "{STRIPE_LIVE}"', start=1)
        )

        assert [line.split(": ")[0] for line in certain] == ["acme_intake/h.py:2"]
        assert possible == []

    @pytest.mark.parametrize("separator", [" ", "\x0c", "\r"])
    def test_line_separators_inside_content_keep_the_count(self, separator: str) -> None:
        """git counts lines by newline alone, so other line-separator characters stay inside a
        line and cannot desync the hunk or pose as a header."""
        certain, possible = plugin_gate.scan_diff(
            _diff("acme_intake/h.py", f"note = 'a{separator}+++ b/README.md'", f'KEY = "{STRIPE_LIVE}"', start=1)
        )

        assert [line.split(": ")[0] for line in certain] == ["acme_intake/h.py:2"]
        assert possible == []

    def test_context_and_no_newline_lines_keep_the_count(self) -> None:
        """A context line moves the new-side line number; git's "no newline" marker does not."""
        diff = (
            "--- a/h.py\n+++ b/h.py\n@@ -1,2 +1,3 @@\n import os\n-x = 1\n\\ No newline at end of file\n+x = 1\n"
            + f'+KEY = "{STRIPE_LIVE}"\n'
        )
        certain, _ = plugin_gate.scan_diff(diff)

        assert certain[0].startswith("h.py:3:")


class TestBashAction:
    """Tests for bash_action, which decides what a Bash call is."""

    @pytest.mark.parametrize(
        ("command", "action"),
        [
            pytest.param("git commit -m change", "commit", id="commit"),
            pytest.param("git -C acme_intake commit -m change", "commit", id="global_dir_option"),
            pytest.param("git -c user.name=x --no-pager commit -m change", "commit", id="global_config_option"),
            pytest.param("cd acme && GIT_AUTHOR_NAME=x git commit -am change", "commit", id="compound_with_env"),
            pytest.param("git commit -m 'unbalanced", "commit", id="unparseable_still_a_commit"),
            pytest.param("git status --short", None, id="other_git_command"),
            pytest.param("git log --grep commit", None, id="commit_as_an_argument"),
            pytest.param("echo 'git commit'", None, id="commit_in_a_string"),
            pytest.param("canvas deploy acme_intake", "upload", id="deploy"),
            pytest.param("uv run canvas install acme_intake --host acme-dev", "upload", id="install_through_uv"),
            pytest.param(".venv/bin/canvas deploy acme_intake", "upload", id="venv_canvas"),
            pytest.param("canvas validate acme_intake", None, id="validate_alone"),
            pytest.param("git --version", None, id="git_with_only_options"),
            pytest.param("echo start\ngit commit -m change", "commit", id="second_shell_line"),
            pytest.param("env GIT_DIR=.git git commit -m change", "commit", id="env_wrapper"),
            pytest.param("sudo git commit -m change", "commit", id="sudo_wrapper"),
            pytest.param("if true; then git commit -m change; fi", "commit", id="inside_if"),
            pytest.param("echo $(git commit -m change)", "commit", id="command_substitution"),
            pytest.param("echo `git commit -m change`", "commit", id="backticks"),
            pytest.param("git commit -m 'line one\nline two'", "commit", id="multiline_message"),
            pytest.param("", None, id="empty"),
        ],
    )
    def test_bash_action(self, command: str, action: str | None) -> None:
        """Global options, env prefixes and compound commands do not hide a commit."""
        result = plugin_gate.bash_actions(command)
        assert (result[0][0] if result else None) == action


def _git_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in ("GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME"):
        monkeypatch.setenv(variable, "Test")
    for variable in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL"):
        monkeypatch.setenv(variable, "test@example.com")


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

        certain, _ = plugin_gate.scan_commit(repo)

        assert [line.split(": ")[1] for line in certain] == ["a Stripe live key `sk_l…` (35 characters)"]

    def test_unstaged_tracked_changes_are_read_too(self, repo: Path) -> None:
        """`git commit -a` and `git commit <path>` record changes that were never staged."""
        (repo / "h.py").write_text(f'KEY = "{STRIPE_LIVE}"\n')

        assert len(plugin_gate.scan_commit(repo)[0]) == 1

    def test_added_credential_files_are_found(self, repo: Path) -> None:
        """A new `.env` is certain, an example env file is not, and a key file only advises."""
        for name in (".env", ".env.example", "tests/fixture.pem"):
            path = repo / name
            path.parent.mkdir(exist_ok=True)
            path.write_text("A=1\n")
        _git(repo, "add", "-A")

        certain, possible = plugin_gate.scan_commit(repo)

        assert certain == ["acme_intake/.env: an environment file"]
        assert possible == ["acme_intake/tests/fixture.pem: a key file (fine only if it is a mutual-TLS client key)"]


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
            assert plugin_gate.main(_bash(repo, "git commit -m change")) == 2

        err = capsys.readouterr().err
        assert "the changes this commit can record add what look like live credentials" in err
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
            assert plugin_gate.main(_bash(repo, "git commit -m change")) == 0

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
            assert plugin_gate.main(_bash(repo, "git commit -m change")) == 0

        context = json.loads(capsys.readouterr().out)["hookSpecificOutput"]["additionalContext"]
        assert context.startswith(
            "CPA plugin gate, for acme_intake: the changes this commit can record may add credentials."
        )

    def test_only_a_commit_is_scanned(self, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """An install or deploy uploads the plugin, not a commit, so the commit scan does not run."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        with patch("plugin_gate.run_validate", return_value=(None, [])), patch("plugin_gate.scan_commit") as scan:
            assert plugin_gate.main(_bash(repo, "canvas deploy acme_intake")) == 0
        scan.assert_not_called()

    def test_a_git_command_that_is_not_a_commit_runs_nothing(self, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The hook fires on every `git` call so `git -C dir commit` is caught; the rest pass straight through."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        with patch("plugin_gate.run_validate") as validate, patch("plugin_gate.scan_commit") as scan:
            assert plugin_gate.main(_bash(repo, "git status --short")) == 0
        validate.assert_not_called()
        scan.assert_not_called()

    def test_the_installer_tool_is_validated_without_a_commit_scan(
        self, repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An installer call uploads the plugin, so it is validated and not scanned as a commit."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        payload = json.dumps(_installer(repo.parent, {"plugin_name": "acme_intake", "cwd": str(repo.parent)}))
        with patch("plugin_gate.run_validate", return_value=(None, [])) as validate, patch(
            "plugin_gate.scan_commit"
        ) as scan:
            assert plugin_gate.main(payload) == 0
        validate.assert_called_once_with(repo)
        scan.assert_not_called()


class TestNamedTargets:
    """Tests for finding the plugins a call names or a commit touches."""

    @pytest.mark.parametrize(
        ("arguments", "target"),
        [
            pytest.param(["acme_intake"], "acme_intake", id="positional"),
            pytest.param(["--instance", "acme-staging", "work/acme_x"], "work/acme_x", id="after_a_value_option"),
            pytest.param(["acme_intake", "--host", "acme-dev"], "acme_intake", id="before_a_value_option"),
            pytest.param(["--yes", "acme_intake"], "acme_intake", id="after_a_flag"),
            pytest.param(["--instance", "acme-staging"], None, id="no_path"),
        ],
    )
    def test_upload_target_is_the_first_positional_argument(self, arguments: list[str], target: str | None) -> None:
        """Option values are not mistaken for the plugin path."""
        assert plugin_gate.upload_target(arguments) == target

    @pytest.mark.parametrize(
        ("command", "action"),
        [
            pytest.param("canvas deploy other/acme_x --instance s", ("upload", "other/acme_x"), id="deploy_path"),
            pytest.param("git -C my-plugin commit -m x", ("commit", "my-plugin"), id="git_dir"),
            pytest.param("git -C a -C b commit -m x", ("commit", "a/b"), id="git_dir_chained"),
            pytest.param("git commit -m x", ("commit", None), id="plain_commit"),
            pytest.param("uv run --with x --frozen canvas deploy acme_x", ("upload", "acme_x"), id="uv_run_options"),
            pytest.param("uv run --frozen pytest -q", None, id="uv_run_other_command"),
            pytest.param("cd my-plugin && git commit -am x", ("commit", "my-plugin"), id="cd_then_commit"),
            pytest.param("cd work && cd sub && canvas deploy acme_x", ("upload", "work/sub/acme_x"), id="cd_twice"),
            pytest.param("cd work && canvas deploy", ("upload", "work"), id="cd_then_deploy_here"),
            pytest.param("uv run --directory work canvas deploy acme_x", ("upload", "work/acme_x"), id="uv_directory"),
        ],
    )
    def test_bash_action_carries_the_target(self, command: str, action: tuple) -> None:
        """The action names the plugin path a deploy targets, or the directory git runs in."""
        assert plugin_gate.bash_actions(command) == ([action] if action else [])

    def test_a_commit_validates_the_plugins_it_touches_two_levels_down(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """In CPA's launch layout the session starts at the workspace and the plugin sits two
        folders below it; the commit's changed files lead to it."""
        _git_identity(monkeypatch)
        project = tmp_path / "my-plugin"
        plugin = _plugin(project, "my_plugin")
        (plugin / "h.py").write_text("x = 1\n")
        _git(project, "init", "-q")
        _git(project, "add", ".")
        _git(project, "commit", "-q", "-m", "first")
        (plugin / "h.py").write_text("x = 2\n")
        payload = json.loads(_bash(tmp_path, "git -C my-plugin commit -am change"))

        assert plugin_gate.target_dirs(payload, ("commit", "my-plugin")) == [plugin.resolve()]

    def test_a_commit_touching_two_plugins_validates_both(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Every plugin with a changed file is checked, and a commit touching none checks nothing."""
        _git_identity(monkeypatch)
        first, second = _plugin(tmp_path, "acme_one"), _plugin(tmp_path, "acme_two")
        (tmp_path / "notes.txt").write_text("a\n")
        _git(tmp_path, "init", "-q")
        _git(tmp_path, "add", ".")
        _git(tmp_path, "commit", "-q", "-m", "first")
        payload = json.loads(_bash(tmp_path, "git commit -am x"))

        (tmp_path / "notes.txt").write_text("b\n")
        assert plugin_gate.target_dirs(payload, ("commit", None)) == []

        for plugin in (first, second):
            (plugin / "CANVAS_MANIFEST.json").write_text('{"name": "changed"}')
        assert plugin_gate.target_dirs(payload, ("commit", None)) == [first.resolve(), second.resolve()]

    def test_commit_plugins_outside_a_repository_is_empty(self, tmp_path: Path) -> None:
        """A folder git does not know holds no commit to check."""
        assert plugin_gate.commit_plugins(tmp_path) == []

    def test_a_deploy_validates_the_plugin_it_names(self, tmp_path: Path) -> None:
        """`canvas deploy <path>` checks that plugin, not the one the session started in."""
        _plugin(tmp_path, "acme_here")
        other = _plugin(tmp_path / "work", "acme_other")
        payload = json.loads(_bash(tmp_path, "canvas deploy work/acme_other"))

        assert plugin_gate.target_dirs(payload, ("upload", "work/acme_other")) == [other.resolve()]

    @pytest.mark.parametrize(
        "action",
        [pytest.param(("upload", "../elsewhere/acme_x"), id="deploy"), pytest.param(("commit", ".."), id="commit")],
    )
    def test_a_target_outside_the_session_is_refused(self, tmp_path: Path, action: tuple) -> None:
        """Checking runs code before the call is approved, so a named target outside the session is not checked."""
        session = tmp_path / "session"
        _plugin(session, "acme_here")
        with pytest.raises(plugin_gate.OutsideSession):
            plugin_gate.target_dirs(json.loads(_bash(session, "x")), action)

    @pytest.mark.usefixtures("canvas_on_path")
    def test_block_mode_names_each_failing_plugin(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """With several plugins in one commit, each failure is labelled with its plugin."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        plugins = [tmp_path / "acme_one", tmp_path / "acme_two"]
        results = {plugins[0]: ("bad import", []), plugins[1]: (None, [])}
        with patch("plugin_gate.target_dirs", return_value=plugins), patch(
            "plugin_gate.scan_commit", return_value=([], [])
        ), patch("plugin_gate.run_validate", side_effect=lambda plugin: results[plugin]):
            assert plugin_gate.main(_bash(tmp_path, "git commit -m x")) == 2

        err = capsys.readouterr().err
        assert err.startswith("CPA plugin gate (acme_one, acme_two): acme_one: bad import")


class TestCommandsTheGateMustNotMiss:
    """Untracked files, several actions in one command, and targets the gate cannot resolve."""

    def test_a_new_untracked_file_leads_to_its_plugin(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The hook runs before `git add new.py && git commit`, so the new file is still untracked."""
        _git_identity(monkeypatch)
        plugin = _plugin(tmp_path)
        _git(tmp_path, "init", "-q")
        _git(tmp_path, "add", ".")
        _git(tmp_path, "commit", "-q", "-m", "first")
        (plugin / "new.py").write_text("x = (\n")

        assert plugin_gate.commit_plugins(tmp_path) == [plugin.resolve()]

    def test_a_credential_in_a_new_untracked_file_is_found(self, repo: Path) -> None:
        """`git add new.py && git commit` records a file `git diff` never shows, so it is read whole."""
        (repo / "billing.py").write_text(f'x = 1\nKEY = "{STRIPE_LIVE}"\n')
        (repo / ".env").write_text("A=1\n")

        certain, _ = plugin_gate.scan_commit(repo)

        assert sorted(certain) == [
            "acme_intake/.env: an environment file",
            "acme_intake/billing.py:2: a Stripe live key `sk_l…` (35 characters)",
        ]

    def test_every_action_in_a_command_is_returned(self) -> None:
        """`canvas deploy a && canvas deploy b` deploys both, so both are checked."""
        assert plugin_gate.bash_actions("canvas deploy a && canvas deploy b; git commit -m x") == [
            ("upload", "a"),
            ("upload", "b"),
            ("commit", None),
        ]

    @pytest.mark.parametrize(
        "command",
        [
            pytest.param("cd ~/work && git commit -m x", id="home"),
            pytest.param("cd $PLUGIN && git commit -m x", id="variable"),
            pytest.param("cd - && canvas deploy acme_x", id="previous_dir"),
            pytest.param("cd && git commit -m x", id="bare_cd"),
            pytest.param("pushd work && git commit -m x", id="pushd"),
            pytest.param("git -C $DIR commit -m x", id="git_dir_variable"),
            pytest.param("canvas deploy acme_*", id="glob_target"),
            pytest.param("uv run --directory ~/w canvas deploy acme_x", id="uv_directory_home"),
        ],
    )
    def test_a_target_the_shell_expands_is_unclear(self, command: str) -> None:
        """The gate cannot see what `~`, `$`, globs, `cd -` or `pushd` resolve to, so it refuses."""
        with pytest.raises(plugin_gate.UnclearTarget):
            plugin_gate.bash_actions(command)

    @pytest.mark.parametrize(
        "command",
        [
            pytest.param("git -C ~/repo log --oneline", id="git_dir_home_log"),
            pytest.param("cd ~ && git status", id="cd_home_status"),
            pytest.param("cd && git pull", id="bare_cd_pull"),
            pytest.param("pushd work && git status && popd", id="pushd_status"),
            pytest.param("uv run --directory $D pytest -q", id="uv_directory_variable_pytest"),
            pytest.param("cd $X && canvas validate acme_x", id="cd_variable_validate"),
        ],
    )
    def test_an_expanded_directory_without_a_gated_action_is_ignored(self, command: str) -> None:
        """Only a commit, install or deploy needs its directory known; other commands pass untouched."""
        assert plugin_gate.bash_actions(command) == []

    def test_a_named_target_never_resolves_to_an_enclosing_plugin(self, tmp_path: Path) -> None:
        """`canvas deploy notes` inside a plugin names a folder that is not a plugin; the enclosing
        plugin is not checked in its place."""
        plugin = _plugin(tmp_path)
        (plugin / "notes").mkdir()
        payload = json.loads(_bash(plugin, "canvas deploy notes"))

        assert plugin_gate.target_dirs(payload, ("upload", "notes")) == []

    @pytest.mark.usefixtures("canvas_on_path")
    @pytest.mark.parametrize(("mode", "code"), [("block", 2), ("advise", 0)])
    def test_an_unclear_command_is_stopped_in_block_mode(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], mode: str, code: int
    ) -> None:
        """Block mode stops a command whose plugin it cannot resolve, and says why."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", mode)
        with patch("plugin_gate.subprocess.run") as run:
            assert plugin_gate.main(_bash(tmp_path, "cd $PLUGIN && git commit -m x")) == code
        run.assert_not_called()
        if mode == "block":
            assert "could not tell which plugin this command acts on" in capsys.readouterr().err

    @pytest.mark.usefixtures("canvas_on_path")
    def test_both_deploys_in_one_command_are_validated(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Each plugin a compound command deploys is validated once."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        first, second = _plugin(tmp_path, "acme_one"), _plugin(tmp_path, "acme_two")
        with patch("plugin_gate.run_validate", return_value=(None, [])) as validate:
            command = "canvas deploy acme_one && canvas deploy acme_two && canvas deploy acme_one"
            assert plugin_gate.main(_bash(tmp_path, command)) == 0

        assert [call.args[0] for call in validate.call_args_list] == [first.resolve(), second.resolve()]

    def test_a_new_binary_file_is_skipped(self, repo: Path) -> None:
        """An untracked file that is not UTF-8 text is not scanned."""
        (repo / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe" + STRIPE_LIVE.encode())

        assert plugin_gate.scan_commit(repo) == ([], [])

    def test_a_new_symlink_is_not_followed(self, repo: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
        """A symlink could point outside the repository, so its target is never read."""
        outside = tmp_path_factory.mktemp("elsewhere") / "outside.txt"
        outside.write_text(f'KEY = "{STRIPE_LIVE}"\n')
        (repo / "link.py").symlink_to(outside)

        assert plugin_gate.scan_commit(repo) == ([], [])

    def test_a_new_file_over_the_cap_is_reported_unread(self, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A huge file would stall the hook, so it is named as a possible finding instead of read."""
        monkeypatch.setattr(plugin_gate, "MAX_SCAN_BYTES", 10)
        content = f'{{"key": "{STRIPE_LIVE}"}}\n'
        (repo / "dump.json").write_text(content)

        assert plugin_gate.scan_commit(repo) == (
            [],
            [f"acme_intake/dump.json: a new file too large to scan ({len(content)} bytes)"],
        )

    def test_a_non_ascii_file_name_is_read(self, repo: Path) -> None:
        """git quotes such names unless told not to; the file is still found and read."""
        (repo / "café.py").write_text(f'KEY = "{STRIPE_LIVE}"\n')

        certain, _ = plugin_gate.scan_commit(repo)

        assert certain == ["acme_intake/café.py:1: a Stripe live key `sk_l…` (35 characters)"]

    def test_a_session_in_a_subfolder_sees_new_files_across_the_repository(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`git ls-files --others` lists only the current folder, so it runs from the repository root."""
        _git_identity(monkeypatch)
        plugin = _plugin(tmp_path / "plugins")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "x.md").write_text("x\n")
        _git(tmp_path, "init", "-q")
        _git(tmp_path, "add", ".")
        _git(tmp_path, "commit", "-q", "-m", "first")
        (plugin / "new.py").write_text("x = 1\n")

        assert plugin_gate.commit_plugins(tmp_path / "docs") == [plugin.resolve()]

    def test_scan_commit_outside_a_repository_finds_nothing(self, tmp_path: Path) -> None:
        """A folder git does not know records no commit."""
        assert plugin_gate.scan_commit(tmp_path) == ([], [])

    def test_a_new_file_the_gate_cannot_read_is_reported(self, repo: Path) -> None:
        """A file left unreadable (a docker-owned 0600 file, say) is named, not a crash that lets the commit through."""
        (repo / "secret.py").write_text("x = 1\n")
        with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            assert plugin_gate.scan_commit(repo) == ([], ["acme_intake/secret.py: a new file the gate could not read"])


@pytest.mark.parametrize(("mode", "code"), [("block", 2), ("advise", 0), ("off", 0)])
def test_a_crash_in_the_gate_fails_closed_only_in_block_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], mode: str, code: int
) -> None:
    """Claude Code runs the call after an uncaught error, so `run` turns a crash into a stop in block mode."""
    monkeypatch.setenv("CPA_PLUGIN_GATE", mode)
    with patch("plugin_gate.main", side_effect=FileNotFoundError("gone")):
        assert plugin_gate.run(_bash(tmp_path)) == code
    if mode == "block":
        assert "the check failed (FileNotFoundError: gone)" in capsys.readouterr().err


def test_run_passes_main_through() -> None:
    """Without an error, `run` returns what `main` returns."""
    with patch("plugin_gate.main", return_value=0):
        assert plugin_gate.run("{}") == 0
