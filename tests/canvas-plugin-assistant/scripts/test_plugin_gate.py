"""Tests for plugin_gate.py, the PreToolUse gate that runs `canvas validate`."""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import plugin_gate
import pytest


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

    def test_a_warning_on_a_file_whose_name_has_a_space_is_kept(self) -> None:
        """The credential lint reads every shipped file, and a file name can hold a space."""
        line = "⚠ client key.pem:1  [hardcoded-credential]  A private key ships inside the plugin package."
        assert plugin_gate.validate_warnings(f"  {line}\n") == [line]

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
        """Canvas releases before `validate` answer "No such command", which says nothing about the plugin."""
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
        gate silently being off.
        """
        monkeypatch.setenv("CPA_PLUGIN_GATE", "blocking")

        assert plugin_gate.main(_bash(tmp_path)) == 2
        assert "'blocking' is not one of off, advise, block" in capsys.readouterr().err

    def test_a_call_outside_any_plugin_passes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A deploy that names no plugin, run from a folder holding none, is not the gate's business."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        with patch("plugin_gate.subprocess.run") as run:
            assert plugin_gate.main(_bash(tmp_path, "canvas deploy --instance acme")) == 0
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
HEX_TOKEN = "0123456789abcdef" * 2
MIXED_TOKEN = "aB3dE5fG7hJ9kL1mN3pQr5s"


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
        part of it is shown.
        """
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

    @pytest.mark.parametrize(
        ("path", "value", "found"),
        [
            pytest.param("acme_intake/h.py", HEX_TOKEN, True, id="hex_token_in_code"),
            pytest.param("acme_intake/h.py", MIXED_TOKEN, True, id="mixed_token_in_code"),
            pytest.param("acme_intake/tests/test_h.py", HEX_TOKEN, False, id="hex_token_in_tests"),
            pytest.param("acme_intake/tests/test_h.py", MIXED_TOKEN, False, id="mixed_token_in_tests"),
            pytest.param("acme_intake/test/fixtures.py", MIXED_TOKEN, False, id="mixed_token_in_test"),
            pytest.param("README.md", MIXED_TOKEN, False, id="mixed_token_in_docs"),
            pytest.param("docs/GUIDE.RST", MIXED_TOKEN, False, id="mixed_token_in_upper_case_docs"),
        ],
    )
    def test_possible_values_follow_canvas_validate(self, path: str, value: str, found: bool) -> None:
        """The same values `canvas validate` warns on: a long lowercase hex run counts as random,
        and tests and docs are skipped, so Claude hears one story from both tools.
        """
        assert bool(plugin_gate.scan_diff(_diff(path, f'auth_token = "{value}"'))[1]) is found

    def test_removed_lines_are_ignored(self) -> None:
        """Deleting a credential is the fix, not a finding."""
        diff = "--- a/h.py\n+++ b/h.py\n@@ -3 +2,0 @@\n" + f'-KEY = "{STRIPE_LIVE}"\n'
        assert plugin_gate.scan_diff(diff) == ([], [])

    def test_an_added_line_cannot_pose_as_a_file_header(self) -> None:
        """Added content reading "++ b/README.md" shows as "+++ b/README.md" and must stay content,
        or every finding after it would be read as docs and only advise.
        """
        certain, possible = plugin_gate.scan_diff(
            _diff("acme_intake/h.py", "++ b/README.md", f'KEY = "{STRIPE_LIVE}"', start=1)
        )

        assert [line.split(": ")[0] for line in certain] == ["acme_intake/h.py:2"]
        assert possible == []

    @pytest.mark.parametrize("separator", [" ", "\x0c", "\r"])
    def test_line_separators_inside_content_keep_the_count(self, separator: str) -> None:
        """Git counts lines by newline alone, so other line-separator characters stay inside a
        line and cannot desync the hunk or pose as a header.
        """
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
            pytest.param("git status --short", None, id="other_git_command"),
            pytest.param("git log --grep commit", None, id="commit_as_an_argument"),
            pytest.param("echo 'git commit'", None, id="commit_in_a_string"),
            pytest.param("canvas deploy acme_intake", "upload", id="deploy"),
            # `canvas install` is not a deploy path, so the gate has nothing to validate for it.
            pytest.param("uv run canvas install acme_intake --host acme-dev", None, id="install_through_uv"),
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
            pytest.param("# stage and commit\ngit add a.py && git commit -m x", "commit", id="comment_line_first"),
            pytest.param("git status\n# now commit\ngit commit -am x", "commit", id="comment_line_between"),
            pytest.param("echo done#1; git commit -am x", "commit", id="hash_inside_a_word"),
            pytest.param("# git commit -m change", None, id="commit_in_a_comment"),
            pytest.param("timeout 60 git commit -am x", "commit", id="timeout_wrapper"),
            pytest.param("timeout -k 5 --signal TERM 60s git commit -am x", "commit", id="timeout_with_options"),
            pytest.param("nice git commit -am x", "commit", id="nice_wrapper"),
            pytest.param("timeout --preserve-status 60 git commit -am x", "commit", id="timeout_flag_without_value"),
            pytest.param("nice -n 10 timeout 60 git commit -am x", "commit", id="nice_then_timeout"),
            pytest.param("stdbuf -oL git commit -am x", "commit", id="stdbuf_wrapper"),
            pytest.param("stdbuf -o L canvas deploy acme_intake", "upload", id="stdbuf_option_value"),
            pytest.param("builtin git commit -am x", "commit", id="builtin_prefix"),
            pytest.param("noglob git commit -am x", "commit", id="noglob_prefix"),
            pytest.param("git merge --continue", "commit", id="merge_continue"),
            pytest.param("git rebase --continue", "commit", id="rebase_continue"),
            pytest.param("git -C acme cherry-pick --continue", "commit", id="cherry_pick_continue"),
            pytest.param("git am --continue", "commit", id="am_continue"),
            pytest.param("git revert --continue", "commit", id="revert_continue"),
            pytest.param("git rebase --abort", None, id="rebase_abort"),
            pytest.param("git merge main", None, id="merge_without_continue"),
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

    @pytest.mark.parametrize("command", ["clean", "process"])
    def test_a_filter_driver_never_runs(self, repo: Path, tmp_path_factory: pytest.TempPathFactory, command: str) -> None:
        """Reading the worktree runs any filter driver the repository assigns, which is code the
        hook would run before the call is approved, so every driver is switched off and the diff
        still reads, even for a driver marked required.
        """
        marker = tmp_path_factory.mktemp("probe") / "ran"
        _git(repo, "config", f"filter.probe.{command}", f"touch {marker}")
        _git(repo, "config", "filter.probe.required", "true")
        (repo.parent / ".git" / "info" / "attributes").write_text("*.py filter=probe\n")
        (repo / "h.py").write_text(f'KEY = "{STRIPE_LIVE}"\n')

        plugin_gate.commit_plugins(repo)
        certain, _ = plugin_gate.scan_commit(repo)

        assert not marker.exists()
        assert len(certain) == 1

    def test_a_git_read_that_fails_raises(self, repo: Path) -> None:
        """A diff git cannot produce is not an empty commit."""
        (repo.parent / ".git" / "index").write_bytes(b"not an index")

        with pytest.raises(plugin_gate.GitFailed, match=r"`git diff` exited \d+"):
            plugin_gate.scan_commit(repo)


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
        """A deploy uploads the plugin, not a commit, so the commit scan does not run."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        with patch("plugin_gate.run_validate", return_value=(None, [])) as validate, patch(
            "plugin_gate.scan_commit"
        ) as scan:
            assert plugin_gate.main(_bash(repo.parent, "canvas deploy acme_intake")) == 0
        validate.assert_called_once()
        scan.assert_not_called()

    def test_a_git_command_that_is_not_a_commit_runs_nothing(self, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The hook fires on every `git` call so `git -C dir commit` is caught; the rest pass straight through."""
        monkeypatch.setenv("CPA_PLUGIN_GATE", "block")
        with patch("plugin_gate.run_validate") as validate, patch("plugin_gate.scan_commit") as scan:
            assert plugin_gate.main(_bash(repo, "git status --short")) == 0
        validate.assert_not_called()
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
            pytest.param(["--plugin", "acme_x@1.2.0", "--instance", "s"], None, id="released_version"),
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
            pytest.param("uv run --directory=work canvas deploy acme_x", ("upload", "work/acme_x"), id="uv_directory_equals"),
            pytest.param("canvas deploy \\\n  work/acme_x \\\n  --instance s", ("upload", "work/acme_x"), id="continued_deploy"),
            pytest.param("git -C my-plugin \\\n  commit -am x", ("commit", "my-plugin"), id="continued_commit"),
            pytest.param("echo a\\\\\ngit -C b commit -am x", ("commit", "b"), id="escaped_backslash_ends_the_line"),
            pytest.param("# note \\\ngit -C b commit -am x", ("commit", "b"), id="backslash_ending_a_comment"),
            pytest.param("git status # x \\\ngit -C b commit -am x", ("commit", "b"), id="backslash_ending_a_trailing_comment"),
            pytest.param("echo a#b \\\n  c; git -C b commit -am x", ("commit", "b"), id="hash_inside_a_word_continues"),
            pytest.param('git -C "a #b" \\\n  commit -am x', ("commit", "a #b"), id="quoted_hash_continues"),
            pytest.param("git -C a\\ #b \\\n  commit -am x", ("commit", "a #b"), id="escaped_space_hash_continues"),
            pytest.param("echo 'a \\\ngit -C b commit -am x'", None, id="backslash_inside_single_quotes"),
            pytest.param("# it's\ngit -C b commit -am x # isn't", ("commit", "b"), id="apostrophes_in_comments"),
            pytest.param("git status\n\ngit -C b commit -am x", ("commit", "b"), id="blank_line_between"),
            pytest.param("echo $(date)#; git -C b commit -am x", ("commit", "b"), id="hash_after_a_substitution"),
            pytest.param("uv run --directory= canvas deploy acme_x", ("upload", "acme_x"), id="uv_empty_equals_value"),
            pytest.param(
                'out="$(canvas deploy my-plugin/my_plugin --instance acme 2>&1)"',
                ("upload", "my-plugin/my_plugin"),
                id="deploy_in_a_quoted_substitution",
            ),
            pytest.param('echo "done: `canvas deploy acme_x`"', ("upload", "acme_x"), id="deploy_in_quoted_backticks"),
            pytest.param('out="$(cd work && (canvas deploy acme_x))"', ("upload", "work/acme_x"), id="parens_inside"),
            pytest.param('out="$(echo ")" && canvas deploy acme_x)"', ("upload", "acme_x"), id="quoted_paren_inside"),
            pytest.param('echo "$(date) then git commit"', None, id="text_after_a_substitution_stays_quoted"),
            pytest.param(
                "git -C b commit -m \"$(cat <<'EOF'\nDon't merge (yet\nEOF\n)\"",
                ("commit", "b"),
                id="claude_code_commit_message_heredoc",
            ),
            pytest.param(
                'out="$(cat <<-END\n\tgit -C b commit )\n\tEND\n)"; canvas deploy acme_x',
                ("upload", "acme_x"),
                id="tab_stripped_heredoc_in_a_substitution",
            ),
            pytest.param(
                'x="$(cat <<EOF\nhi\nEOF)"\ncanvas deploy acme_x\nEOF', ("upload", "acme_x"), id="delimiter_then_paren"
            ),
            pytest.param('git -c user.name="$(whoami)" commit -am x', ("commit", None), id="substitution_in_a_git_option"),
            pytest.param(
                'canvas deploy --instance "$(cat .instance)" work/acme_x',
                ("upload", "work/acme_x"),
                id="substitution_in_a_deploy_option",
            ),
            pytest.param(
                "canvas deploy --instance $(cat .instance) work/acme_x",
                ("upload", "work/acme_x"),
                id="unquoted_substitution_in_a_deploy_option",
            ),
            pytest.param(
                'cd my-plugin && git commit -am "$(cd .. && echo change)"',
                ("commit", "my-plugin"),
                id="cd_in_a_substitution_after_the_commit",
            ),
            pytest.param(
                'echo "(" ; cd my-plugin ; git commit -am x',
                ("commit", "my-plugin"),
                id="quoted_open_paren_without_a_close",
            ),
            pytest.param(
                "(cd my-plugin && git commit -am x) && ls",
                ("commit", "my-plugin"),
                id="commit_inside_a_subshell",
            ),
            pytest.param("(ls);git commit -am x", ("commit", None), id="close_paren_joined_to_a_separator"),
            pytest.param("true;(git commit -am x)", ("commit", None), id="separator_joined_to_an_open_paren"),
            pytest.param("ls|&git commit -am x", ("commit", None), id="pipe_with_stderr"),
            pytest.param(
                "echo hi>&2;git -C my-plugin commit -am x",
                ("commit", "my-plugin"),
                id="redirection_before_a_separator",
            ),
        ],
    )
    def test_bash_action_carries_the_target(self, command: str, action: tuple) -> None:
        """The action names the plugin path a deploy targets, or the directory git runs in."""
        assert plugin_gate.bash_actions(command) == ([action] if action else [])

    def test_a_commit_validates_the_plugins_it_touches_two_levels_down(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """In CPA's launch layout the session starts at the workspace and the plugin sits two
        folders below it; the commit's changed files lead to it.
        """
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
        """`git add new.py && git commit` records a file `git diff` never shows, so it is read whole.
        An ignored file is one `git add -A` would not record, so it is skipped.
        """
        (repo / "billing.py").write_text(f'x = 1\nKEY = "{STRIPE_LIVE}"\n')
        (repo / ".env").write_text("A=1\n")
        (repo / "ignored.py").write_text(f'KEY = "{STRIPE_LIVE}"\n')
        (repo / ".gitignore").write_text("ignored.py\n")

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
            pytest.param('git -C "$(git rev-parse --show-toplevel)" commit -am x', id="git_dir_quoted_substitution"),
            pytest.param("git -C $(pwd) commit -am x", id="git_dir_substitution"),
            pytest.param("git -C `pwd` commit -am x", id="git_dir_backticks"),
            pytest.param('"$(command -v canvas)" deploy acme_x', id="program_quoted_substitution"),
            pytest.param("`which canvas` deploy acme_x", id="program_backticks"),
            pytest.param('"$(command -v git)" commit -am x', id="git_program_substitution"),
        ],
    )
    def test_a_target_the_shell_expands_is_unclear(self, command: str) -> None:
        """The gate cannot see what `~`, `$`, globs, `cd -` or `pushd` resolve to, so it refuses."""
        with pytest.raises(plugin_gate.UnclearTarget):
            plugin_gate.bash_actions(command)

    @pytest.mark.parametrize(
        "command",
        [
            pytest.param('cd my-plugin && top="$(cd .. && pwd)" && git commit -am x', id="quoted_substitution"),
            pytest.param("cd my-plugin && top=$(cd .. && pwd) && git commit -am x", id="substitution"),
            pytest.param("cd my-plugin && (cd .. && ls) && git commit -am x", id="subshell"),
            pytest.param("(cd work && ls) && canvas deploy acme_x", id="deploy_after_a_subshell"),
            pytest.param('echo "(" ; cd my-plugin ; echo ")" ; git commit -am x', id="quoted_parens"),
            pytest.param("echo \\( ; cd my-plugin ; echo \\) ; git commit -am x", id="escaped_parens"),
            pytest.param('(cd my-plugin ; echo "(") ; git commit -am x', id="quoted_open_inside_a_subshell"),
            pytest.param('(echo ")" ; cd my-plugin) ; git commit -am x', id="quoted_close_inside_a_subshell"),
            pytest.param(
                '( echo ")" ; cd my-plugin ; echo "(" ) ; git commit -am x',
                id="quoted_close_then_open_around_a_cd",
            ),
            pytest.param("cd my-plugin && (cd ..);git commit -am x", id="close_paren_joined_to_a_separator"),
        ],
    )
    def test_a_cd_inside_parentheses_is_unclear_after_them(self, command: str) -> None:
        """A subshell's `cd` ends with it, but shlex reads a quoted paren as a real one, so a commit
        or deploy after a `)` that may close a `cd` is refused rather than placed.
        """
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
        """Only a commit or deploy needs its directory known; other commands pass untouched."""
        assert plugin_gate.bash_actions(command) == []

    def test_a_named_target_never_resolves_to_an_enclosing_plugin(self, tmp_path: Path) -> None:
        """`canvas deploy notes` inside a plugin names a folder that is not a plugin; the enclosing
        plugin is not checked in its place.
        """
        plugin = _plugin(tmp_path)
        (plugin / "notes").mkdir()
        payload = json.loads(_bash(plugin, "canvas deploy notes"))

        with pytest.raises(plugin_gate.UnclearTarget):
            plugin_gate.target_dirs(payload, ("upload", "notes"))

    def test_a_named_folder_resolves_to_the_one_plugin_inside_it(self, tmp_path: Path) -> None:
        """From the workspace, `canvas deploy my-plugin` names the project, whose plugin is inside it."""
        plugin = _plugin(tmp_path / "my-plugin", "my_plugin")
        payload = json.loads(_bash(tmp_path, "canvas deploy my-plugin"))

        assert plugin_gate.target_dirs(payload, ("upload", "my-plugin")) == [plugin.resolve()]

    @pytest.mark.parametrize(
        "command",
        [
            pytest.param("cp -R acme_intake acme_copy && canvas deploy acme_copy", id="target_made_earlier"),
            pytest.param("(cd acme_intake && ls) && canvas deploy acme_intake", id="cd_inside_a_subshell"),
            pytest.param("uv run -p 3.13 canvas deploy acme_intake", id="uv_option_value_unknown"),
        ],
    )
    def test_a_deploy_the_gate_cannot_resolve_is_unclear(self, tmp_path: Path, command: str) -> None:
        """A deploy whose plugin the gate cannot find at hook time is stopped, not waved through."""
        _plugin(tmp_path)
        payload = json.loads(_bash(tmp_path, command))

        with pytest.raises(plugin_gate.UnclearTarget):
            for action in plugin_gate.bash_actions(command):
                plugin_gate.target_dirs(payload, action)

    @pytest.mark.parametrize(
        "command",
        [
            pytest.param("cat > n.md <<'EOF'\nThe plugin's notes\nEOF\ngit -C b commit -am x", id="heredoc_then_commit"),
            pytest.param("cat > n.md <<'EOF'\nThe plugin's notes\nEOF\ncanvas deploy acme_x", id="heredoc_then_deploy"),
            pytest.param("git -C b commit -a -F - <<'EOF'\nDon't merge yet\nEOF", id="commit_message_heredoc"),
            pytest.param("echo $'it\\'s' && canvas deploy acme_x", id="ansi_c_quote"),
            pytest.param("git commit -m 'unbalanced", id="unbalanced_commit"),
            pytest.param("cat > n.md <<'EOF'\nThe plugin's notes\nEOF\ngit rebase --continue", id="heredoc_then_continue"),
            pytest.param('out="$(case x in a) echo;; esac; canvas deploy acme_x)"', id="case_in_a_substitution"),
            pytest.param("git commit -m \"$(cat <<'EOF'\nno closing line\n)\"", id="unclosed_heredoc_in_a_substitution"),
            pytest.param('out="$(cat << )"; git commit -m x', id="heredoc_without_a_delimiter"),
            pytest.param('git commit -m "$(echo x', id="unclosed_substitution"),
            pytest.param('x="$(echo $((1<<2)))"\ngit commit -m x\n2', id="arithmetic_inside_a_substitution"),
            pytest.param('x="$((1<<2))"\ncanvas deploy acme_x\n2', id="quoted_arithmetic_shift"),
            pytest.param('x="$((cd work && canvas deploy acme_x))"', id="quoted_subshell_read_as_arithmetic"),
        ],
    )
    def test_a_command_shlex_cannot_read_is_unclear(self, command: str) -> None:
        """A quote shlex cannot close hides where a commit or deploy runs, so the gate does not guess."""
        with pytest.raises(plugin_gate.UnclearTarget):
            plugin_gate.bash_actions(command)

    def test_an_unreadable_command_that_neither_commits_nor_uploads_passes(self) -> None:
        """Nothing gated is in it, so an unclosed quote alone stops nothing."""
        assert plugin_gate.bash_actions("cat > n.md <<'EOF'\nThe plugin's notes\nEOF\ngit status") == []

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
        """Git quotes such names unless told not to; the file is still found and read."""
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


@pytest.mark.parametrize(("mode", "code"), [("block", 2), ("advise", 0)])
def test_a_commit_whose_changes_cannot_be_read_is_stopped_in_block_mode(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], mode: str, code: int
) -> None:
    """A broken index leaves the gate unable to see what the commit records, so `block` stops it."""
    monkeypatch.setenv("CPA_PLUGIN_GATE", mode)
    (repo.parent / ".git" / "index").write_bytes(b"not an index")

    assert plugin_gate.run(_bash(repo, "git commit -am change")) == code
    if mode == "block":
        assert "could not read the changes this commit can record (`git " in capsys.readouterr().err


def test_run_passes_main_through() -> None:
    """Without an error, `run` returns what `main` returns."""
    with patch("plugin_gate.main", return_value=0):
        assert plugin_gate.run("{}") == 0
