"""Tests for mcp_canvas_deployer module."""

import asyncio
import json
import os
import shlex
from pathlib import Path
from unittest.mock import AsyncMock, call, patch

import pytest

from mcp_canvas_deployer import CanvasDeployerMcp


class TestParseVariableNames:
    """Tests for CanvasDeployerMcp._parse_variable_names."""

    @pytest.mark.parametrize(
        ("manifest", "expected"),
        [
            pytest.param(
                {"variables": [{"name": "API_KEY"}, {"name": "TOKEN"}]},
                ["API_KEY", "TOKEN"],
                id="variables",
            ),
            pytest.param(
                {"variables": [{"name": "  KEY  "}, {"name": " VAL "}]},
                ["KEY", "VAL"],
                id="variables_strip_whitespace",
            ),
            pytest.param(
                {"variables": [{"name": "KEY"}, {"name": ""}, {"name": "   "}, {"name": "VAL"}]},
                ["KEY", "VAL"],
                id="variables_filter_blank_names",
            ),
            pytest.param(
                {"variables": [{"name": 123}, {"name": "KEY"}, {}]},
                ["KEY"],
                id="variables_filter_non_string_and_missing_names",
            ),
            pytest.param(
                {"variables": ["API_KEY", {"name": "KEY"}]},
                ["KEY"],
                id="variables_filter_non_dict_entries",
            ),
            pytest.param(
                {"variables": [], "secrets": ["KEY", "", "  ", 123]},
                ["KEY", "123"],
                id="legacy_secrets_list_used_when_variables_empty",
            ),
            pytest.param(
                {"secrets": "KEY1, KEY2, KEY3"},
                ["KEY1", "KEY2", "KEY3"],
                id="legacy_secrets_string_comma_separated",
            ),
            pytest.param(
                {"secrets": "KEY1\nKEY2"},
                ["KEY1", "KEY2"],
                id="legacy_secrets_string_newline_separated",
            ),
            pytest.param(
                {"secrets": "KEY1,,, KEY2"},
                ["KEY1", "KEY2"],
                id="legacy_secrets_string_filters_empty",
            ),
            pytest.param({"secrets": 12345}, [], id="unsupported_secrets_type"),
            pytest.param({}, [], id="no_variables_and_no_secrets"),
        ],
    )
    def test__parse_variable_names(self, manifest: dict, expected: list[str]) -> None:
        """Parse variable names from a manifest, falling back to the legacy secrets key."""
        tested = CanvasDeployerMcp

        result = tested._parse_variable_names(manifest)

        assert result == expected


class TestRunCanvasCommand:
    """Tests for CanvasDeployerMcp._run_canvas_command."""

    def test__run_canvas_command__invalid_cwd(self, tmp_path: Path) -> None:
        """Return error when cwd does not exist."""
        tested = CanvasDeployerMcp

        result = asyncio.run(tested._run_canvas_command(["echo", "hi"], str(tmp_path / "nonexistent")))

        expected = f"Invalid cwd: {tmp_path / 'nonexistent'}"
        assert result == expected

    def test__run_canvas_command__cwd_is_file(self, tmp_path: Path) -> None:
        """Return error when cwd is a file, not a directory."""
        tested = CanvasDeployerMcp
        a_file = tmp_path / "file.txt"
        a_file.write_text("content")

        result = asyncio.run(tested._run_canvas_command(["echo", "hi"], str(a_file)))

        expected = f"Invalid cwd: {a_file}"
        assert result == expected

    def test__run_canvas_command__success(self, tmp_path: Path) -> None:
        """Return stdout from a successful command."""
        tested = CanvasDeployerMcp

        result = asyncio.run(tested._run_canvas_command(["echo", "hello world"], str(tmp_path)))

        expected = "hello world"
        assert result == expected

    def test__run_canvas_command__combined_output(self, tmp_path: Path) -> None:
        """Return combined stdout and stderr."""
        tested = CanvasDeployerMcp

        result = asyncio.run(
            tested._run_canvas_command(["bash", "-c", "echo out && echo err >&2"], str(tmp_path))
        )

        expected_out = True
        assert ("out" in result) is expected_out
        expected_err = True
        assert ("err" in result) is expected_err

    def test__run_canvas_command__failure(self, tmp_path: Path) -> None:
        """Return error message with exit code for failed command."""
        tested = CanvasDeployerMcp

        result = asyncio.run(tested._run_canvas_command(["bash", "-c", "exit 1"], str(tmp_path)))

        expected = True
        assert ("Command failed with exit code 1" in result) is expected

    def test__run_canvas_command__no_output(self, tmp_path: Path) -> None:
        """Return '(no output)' when command produces no output."""
        tested = CanvasDeployerMcp

        result = asyncio.run(tested._run_canvas_command(["bash", "-c", "true"], str(tmp_path)))

        expected = "(no output)"
        assert result == expected


PLUGIN = "acme__vitals_alert"
INSTANCE = "acme-staging"
MANIFEST: dict = {
    "name": PLUGIN,
    "variables": [{"name": "API_KEY", "sensitive": True}, {"name": "API_URL"}],
}
DEPLOY_CMD: list[str] = ["uv", "run", "canvas", "deploy", PLUGIN, "--instance", INSTANCE]
CONSENT_OUTPUT = (
    "Command failed with exit code 1\n"
    "This deployment needs consent (1 request(s)):\n\n"
    "  \u2022 beta__reader asks for read access to the custom data namespace 'acme__intake' on acme-staging.\n\n"
    "Deployment 6f1c is waiting on these requests, and there is no terminal to ask at. "
    "Run the command again at a terminal, without --yes, to approve or deny them."
)


def make_plugin(tmp_path: Path, manifest: dict | None) -> str:
    """Create a plugin package under tmp_path and return the container directory."""
    plugin_dir = tmp_path / PLUGIN
    plugin_dir.mkdir()
    if manifest is not None:
        (plugin_dir / "CANVAS_MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return str(tmp_path)


def config_set_cmd(*pairs: str) -> list[str]:
    """Build the expected `canvas config set` command."""
    return ["uv", "run", "canvas", "config", "set", PLUGIN, *pairs, "--instance", INSTANCE]


class TestDeploy:
    """Tests for CanvasDeployerMcp.deploy."""

    @pytest.mark.parametrize(
        ("kwargs", "expected"),
        [
            pytest.param(
                {"plugin_name": "", "instance": INSTANCE, "cwd": "/tmp"},
                "Error: missing plugin_name",
                id="missing_plugin_name",
            ),
            pytest.param(
                {"plugin_name": PLUGIN, "instance": "", "cwd": "/tmp"},
                "Error: missing instance",
                id="missing_instance",
            ),
            pytest.param(
                {"plugin_name": PLUGIN, "instance": INSTANCE, "cwd": ""},
                "Error: missing cwd",
                id="missing_cwd",
            ),
        ],
    )
    def test_deploy__missing_argument(self, kwargs: dict, expected: str) -> None:
        """Return an error and run nothing when an argument is empty."""
        tested = CanvasDeployerMcp

        with patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd:
            result = asyncio.run(tested.deploy(**kwargs))

        assert result == expected
        assert mock_cmd.mock_calls == []

    def test_deploy__plugin_dir_not_found(self, tmp_path: Path) -> None:
        """Return an error when the plugin directory does not exist."""
        tested = CanvasDeployerMcp

        result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=str(tmp_path)))

        expected = f"Error: plugin directory not found: {tmp_path / PLUGIN}"
        assert result == expected

    def test_deploy__manifest_not_found(self, tmp_path: Path) -> None:
        """Return an error when CANVAS_MANIFEST.json does not exist."""
        tested = CanvasDeployerMcp
        cwd = make_plugin(tmp_path, None)

        result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        expected = f"Error: manifest not found: {tmp_path / PLUGIN / 'CANVAS_MANIFEST.json'}"
        assert result == expected

    def test_deploy__runs_canvas_deploy_then_config_set(self, tmp_path: Path) -> None:
        """Deploy first, then set manifest variables from the secrets file, never echoing values."""
        tested = CanvasDeployerMcp
        cwd = make_plugin(tmp_path, MANIFEST)

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_deployer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = ["Deployed", "Set 2 variable(s)"]
            mock_secrets.side_effect = [{"API_KEY": "sk-1", "API_URL": "https://x"}]
            result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        expected = "Deploy output:\nDeployed\n\nConfigure output:\nSet 2 variable(s)"
        assert result == expected
        assert "sk-1" not in result

        exp_cmd_calls = [
            call(command=DEPLOY_CMD, cwd=cwd),
            call(command=config_set_cmd("API_KEY=sk-1", "API_URL=https://x"), cwd=cwd),
        ]
        assert mock_cmd.mock_calls == exp_cmd_calls

        exp_secrets_calls = [call(["API_KEY", "API_URL"], INSTANCE, PLUGIN)]
        assert mock_secrets.mock_calls == exp_secrets_calls

    def test_deploy__consent_pending_skips_configure(self, tmp_path: Path) -> None:
        """Stop at pending consent: only a person at a terminal may answer it, and the next step is theirs."""
        tested = CanvasDeployerMcp
        cwd = make_plugin(tmp_path, MANIFEST)

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_deployer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = [CONSENT_OUTPUT]
            result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        expected = (
            f"Deploy output:\n{CONSENT_OUTPUT}\n\n"
            "Consent needed: this deployment is waiting on custom data access consent that only a person at a "
            "terminal can answer. Show the requests above to the user and have them run the command below in "
            "their own terminal. Do not retry with --yes.\n"
            f"  cd {cwd} && uv run canvas deploy {PLUGIN} --no-push --instance {INSTANCE}\n"
            "After it succeeds there, call the configurer tool to set variables."
        )
        assert result == expected
        assert mock_cmd.mock_calls == [call(command=DEPLOY_CMD, cwd=cwd)]
        assert mock_secrets.mock_calls == []

    def test_deploy__failure_skips_configure(self, tmp_path: Path) -> None:
        """Return a failed deploy as is: setting variables on a plugin that did not deploy would target nothing."""
        tested = CanvasDeployerMcp
        cwd = make_plugin(tmp_path, MANIFEST)
        failure = "Command failed with exit code 2\nManifest name is not publisher-prefixed"

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_deployer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = [failure]
            result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        expected = f"Deploy output:\n{failure}"
        assert result == expected
        assert mock_cmd.mock_calls == [call(command=DEPLOY_CMD, cwd=cwd)]
        assert mock_secrets.mock_calls == []

    def test_deploy__no_variables_skips_config_set(self, tmp_path: Path) -> None:
        """Skip config set when the manifest declares no variables, since there is nothing to store."""
        tested = CanvasDeployerMcp
        cwd = make_plugin(tmp_path, {"name": PLUGIN})

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_deployer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = ["Deployed"]
            result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        expected = "Deploy output:\nDeployed\n\nConfigure skipped: no variable values found in the secrets file."
        assert result == expected
        assert mock_cmd.mock_calls == [call(command=DEPLOY_CMD, cwd=cwd)]
        assert mock_secrets.mock_calls == []

    def test_deploy__missing_values_warns_and_sets_rest(self, tmp_path: Path) -> None:
        """Set the values that exist and warn about the empty ones."""
        tested = CanvasDeployerMcp
        cwd = make_plugin(tmp_path, MANIFEST)

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_deployer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = ["Deployed", "Set 1 variable(s)"]
            mock_secrets.side_effect = [{"API_KEY": "sk-1"}]
            result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        expected = (
            "Deploy output:\nDeployed\n\nConfigure output:\nSet 1 variable(s)"
            "\nWarning: secrets not provided (missing or empty): API_URL"
        )
        assert result == expected
        assert mock_cmd.mock_calls[1] == call(command=config_set_cmd("API_KEY=sk-1"), cwd=cwd)


class TestConfigure:
    """Tests for CanvasDeployerMcp.configure."""

    @pytest.mark.parametrize(
        ("kwargs", "expected"),
        [
            pytest.param(
                {"plugin_name": "", "instance": INSTANCE, "cwd": "/tmp"},
                "Error: missing plugin_name",
                id="missing_plugin_name",
            ),
            pytest.param(
                {"plugin_name": PLUGIN, "instance": "", "cwd": "/tmp"},
                "Error: missing instance",
                id="missing_instance",
            ),
        ],
    )
    def test_configure__missing_argument(self, kwargs: dict, expected: str) -> None:
        """Return an error when an argument is empty."""
        tested = CanvasDeployerMcp

        result = asyncio.run(tested.configure(**kwargs))

        assert result == expected

    def test_configure__sets_only(self, tmp_path: Path) -> None:
        """Run config set without deploying, for use after the person approves consent."""
        tested = CanvasDeployerMcp
        cwd = make_plugin(tmp_path, MANIFEST)

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_deployer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = ["Set 2 variable(s)"]
            mock_secrets.side_effect = [{"API_KEY": "sk-1", "API_URL": "https://x"}]
            result = asyncio.run(tested.configure(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        expected = "Configure output:\nSet 2 variable(s)"
        assert result == expected
        assert "sk-1" not in result
        exp_cmd_calls = [call(command=config_set_cmd("API_KEY=sk-1", "API_URL=https://x"), cwd=cwd)]
        assert mock_cmd.mock_calls == exp_cmd_calls

    def test_configure__no_values(self, tmp_path: Path) -> None:
        """Skip config set when the secrets file has no values: the CLI rejects zero pairs."""
        tested = CanvasDeployerMcp
        cwd = make_plugin(tmp_path, MANIFEST)

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_deployer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_secrets.side_effect = [{}]
            result = asyncio.run(tested.configure(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        expected = (
            "Configure skipped: no variable values found in the secrets file."
            "\nWarning: secrets not provided (missing or empty): API_KEY, API_URL"
        )
        assert result == expected
        assert mock_cmd.mock_calls == []


class TestCreateServer:
    """Tests for CanvasDeployerMcp.create_server."""

    def test_create_server__returns_server(self) -> None:
        """Return a FastMCP server with correct name."""
        tested = CanvasDeployerMcp

        result = tested.create_server()

        expected = "canvas_cmd_line"
        assert result.name == expected

    def test_create_server__tools(self) -> None:
        """Server registers exactly the deployer and configurer tools."""
        tested = CanvasDeployerMcp
        server = tested.create_server()

        tool_names = {tool.name for tool in server._tool_manager.list_tools()}

        expected = {"deployer", "configurer"}
        assert tool_names == expected

    @pytest.mark.parametrize(
        ("tool_name", "method"),
        [
            pytest.param("deployer", "deploy", id="deployer"),
            pytest.param("configurer", "configure", id="configurer"),
        ],
    )
    def test_create_server__tool_delegates(self, tool_name: str, method: str) -> None:
        """Each tool delegates to the matching classmethod."""
        tested = CanvasDeployerMcp
        server = tested.create_server()

        with patch.object(tested, method, new_callable=AsyncMock) as mock_method:
            mock_method.side_effect = ["mocked"]
            tool = server._tool_manager._tools[tool_name]
            result = asyncio.run(tool.fn(plugin_name="p", instance="i", cwd="c"))

        expected = "mocked"
        assert result == expected
        assert mock_method.mock_calls == [call("p", "i", "c")]


# Scenario tests: the deployer driven through a fake `uv` on PATH, so the real subprocess and secrets-file paths run.

SDK_MANIFEST: dict = {
    "name": PLUGIN,
    "variables": [{"name": "WEBHOOK_ID", "sensitive": True}, {"name": "AUTH_TOKEN", "sensitive": True}],
}
CLI_CONSENT_STDOUT = (
    "Pushed 3f2a9c1d0b7e to main.\n"
    "Deploying acme__vitals_alert@3f2a9c1d0b7e to acme-staging…\n"
    "Deployment 6f1c created.\n"
    "\n"
    "This deployment needs consent (1 request(s)):\n"
    "\n"
    "  • beta__reader asks for read access to the custom data namespace 'acme__intake' on acme-staging.\n"
    "\n"
    "Deployment 6f1c is waiting on these requests, and there is no terminal to ask at. "
    "Run the command again at a terminal, without --yes, to approve or deny them.\n"
)
CLI_DEPLOY_OK_STDOUT = (
    "Pushed 3f2a9c1d0b7e to main.\n"
    "Deploying acme__vitals_alert@3f2a9c1d0b7e to acme-staging…\n"
    "Deployment 6f1c created.\n"
    "  in_progress…\n"
    "  succeeded…\n"
    "  acme__vitals_alert on acme-staging: succeeded\n"
    "Deploy of acme__vitals_alert succeeded.\n"
)
CLI_CONFIG_OK_STDOUT = (
    "Stored 2 value(s) for acme__vitals_alert on acme-staging.\n"
    "Deployment 7a2d created.\n"
    "  acme__vitals_alert on acme-staging: succeeded\n"
    "Configuring acme__vitals_alert succeeded.\n"
)
UV_NOISE = "Installed 52 packages in 87ms"


def install_fake_uv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    deploy: tuple[str, str, int],
    config: tuple[str, str, int] = (CLI_CONFIG_OK_STDOUT, "", 0),
) -> Path:
    """Put a fake `uv` first on PATH that logs its argv and answers like the canvas CLI.

    Args:
        tmp_path (Path): Where the fake and its canned output live.
        monkeypatch (pytest.MonkeyPatch): Used to prepend the fake to PATH.
        deploy (tuple[str, str, int]): stdout, stderr and exit code for `canvas deploy`.
        config (tuple[str, str, int]): stdout, stderr and exit code for `canvas config set`.

    Returns:
        Path: The argv log, one record per call.
    """
    fake_dir = tmp_path / "fake-bin"
    fake_dir.mkdir()
    for label, (out, err, _) in {"deploy": deploy, "config": config}.items():
        (fake_dir / f"{label}.out").write_text(out, encoding="utf-8")
        (fake_dir / f"{label}.err").write_text(err, encoding="utf-8")
    log = fake_dir / "argv.log"
    script = fake_dir / "uv"
    script.write_text(
        "#!/bin/bash\n"
        f'printf "%s\\0" uv "$@" >> "{log}"\n'
        f'printf "\\036" >> "{log}"\n'
        'case "$3" in\n'
        f'  deploy) cat "{fake_dir}/deploy.out"; cat "{fake_dir}/deploy.err" >&2; exit {deploy[2]};;\n'
        f'  config) cat "{fake_dir}/config.out"; cat "{fake_dir}/config.err" >&2; exit {config[2]};;\n'
        "esac\n"
        "exit 99\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_dir}{os.pathsep}{os.environ['PATH']}")
    return log


def read_argv_log(log: Path) -> list[list[str]]:
    """Return the argv of each fake `uv` call, in order."""
    if not log.exists():
        return []
    records = log.read_text(encoding="utf-8").split("\x1e")
    return [record.split("\0")[:-1] for record in records if record]


def write_secrets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, content: dict | None) -> Path:
    """Point SecretRequester at a tmp secrets file, written with content when given."""
    secrets_file = tmp_path / "secrets" / f"{INSTANCE}.json"
    if content is not None:
        secrets_file.parent.mkdir()
        secrets_file.write_text(json.dumps(content), encoding="utf-8")
    monkeypatch.setenv("CPA_SECRET_FILEPATH", str(secrets_file))
    return secrets_file


class TestDeployScenarios:
    """Cross-step scenarios for the deployer: the CLI's real output shapes, the secrets file and the consent hand-off."""

    def test_deploy__consent_then_configurer_after_approval(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Consent stop surfaces the request lines and the hand-off command; configurer later sets the variables."""
        tested = CanvasDeployerMcp
        container = tmp_path / "vitals-alert"
        container.mkdir()
        cwd = make_plugin(container, SDK_MANIFEST)
        secrets = {PLUGIN: {"WEBHOOK_ID": "wh_01J9QX", "AUTH_TOKEN": "tok_9f2"}}
        secrets_file = write_secrets(tmp_path, monkeypatch, secrets)
        log = install_fake_uv(tmp_path, monkeypatch, deploy=(CLI_CONSENT_STDOUT, UV_NOISE, 1))

        result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        request_line = (
            "  • beta__reader asks for read access to the custom data namespace 'acme__intake' on acme-staging."
        )
        assert request_line in result.splitlines()
        assert result.startswith("Deploy output:\nCommand failed with exit code 1\n")
        assert UV_NOISE in result
        assert "Consent needed" in result
        assert f"uv run canvas deploy {PLUGIN} --no-push --instance {INSTANCE}" in result
        assert read_argv_log(log) == [DEPLOY_CMD]
        # SecretRequester never ran: the file it would sync is untouched.
        assert json.loads(secrets_file.read_text(encoding="utf-8")) == secrets

        # The person approved at their terminal; the agent calls configurer in a later turn.
        result = asyncio.run(tested.configure(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        expected = f"Configure output:\n{CLI_CONFIG_OK_STDOUT.strip()}"
        assert result == expected
        exp_argv = [DEPLOY_CMD, config_set_cmd("WEBHOOK_ID=wh_01J9QX", "AUTH_TOKEN=tok_9f2")]
        assert read_argv_log(log) == exp_argv

    def test_deploy__secret_values_pass_as_single_arguments(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Values holding spaces and `=` reach the CLI intact, one argv element per pair, and never come back."""
        tested = CanvasDeployerMcp
        cwd = make_plugin(tmp_path, SDK_MANIFEST)
        stored = {"WEBHOOK_ID": "wh_01J9QX", "AUTH_TOKEN": "Bearer c2stbGl2ZS05ZjI="}
        write_secrets(tmp_path, monkeypatch, {PLUGIN: stored})
        log = install_fake_uv(tmp_path, monkeypatch, deploy=(CLI_DEPLOY_OK_STDOUT, UV_NOISE, 0))

        result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        calls = read_argv_log(log)
        exp_argv = [DEPLOY_CMD, config_set_cmd("WEBHOOK_ID=wh_01J9QX", "AUTH_TOKEN=Bearer c2stbGl2ZS05ZjI=")]
        assert calls == exp_argv
        # The CLI splits each pair on its first `=` (canvas_cli `_parse_pair`).
        pairs = calls[1][6:-2]
        parsed = {key: value for key, _, value in (pair.partition("=") for pair in pairs)}
        assert parsed == stored
        for value in stored.values():
            assert value not in result
        assert "Configuring acme__vitals_alert succeeded." in result

    def test_deploy__secrets_under_unprefixed_name_are_not_sent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Values kept under the pre-rename plugin name are another plugin's: skip, warn, and leave them in place."""
        tested = CanvasDeployerMcp
        cwd = make_plugin(tmp_path, SDK_MANIFEST)
        legacy = {"WEBHOOK_ID": "wh_01J9QX", "AUTH_TOKEN": "tok_9f2"}
        secrets_file = write_secrets(tmp_path, monkeypatch, {"vitals_alert": legacy})
        log = install_fake_uv(tmp_path, monkeypatch, deploy=(CLI_DEPLOY_OK_STDOUT, "", 0))

        result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        expected = (
            f"Deploy output:\n{CLI_DEPLOY_OK_STDOUT.strip()}\n\n"
            "Configure skipped: no variable values found in the secrets file."
            "\nWarning: secrets not provided (missing or empty): WEBHOOK_ID, AUTH_TOKEN"
        )
        assert result == expected
        assert read_argv_log(log) == [DEPLOY_CMD]
        exp_file = {"vitals_alert": legacy, PLUGIN: {"WEBHOOK_ID": "", "AUTH_TOKEN": ""}}
        assert json.loads(secrets_file.read_text(encoding="utf-8")) == exp_file

    def test_deploy__consent_command_survives_a_space_in_cwd(self, tmp_path: Path) -> None:
        """The hand-off command the person pastes stays one runnable command when the plugin path has a space."""
        tested = CanvasDeployerMcp
        container = tmp_path / "Canvas Plugins" / "vitals-alert"
        container.mkdir(parents=True)
        cwd = make_plugin(container, MANIFEST)

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_deployer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = [CONSENT_OUTPUT]
            result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        command_line = next(line for line in result.splitlines() if "--no-push" in line)
        expected = ["cd", cwd, "&&", "uv", "run", "canvas", "deploy", PLUGIN, "--no-push", "--instance", INSTANCE]
        assert shlex.split(command_line) == expected
        assert mock_secrets.mock_calls == []

    def test_deploy__configures_the_manifest_name_not_a_mismatched_folder(self, tmp_path: Path) -> None:
        """A folder left unrenamed (`vitals_alert/` holding `acme__vitals_alert`) must not send values to the unprefixed name.

        `canvas config set vitals_alert` is unmanaged to the CLI, which writes the values straight to the instance.
        """
        tested = CanvasDeployerMcp
        folder = tmp_path / "vitals_alert"
        folder.mkdir()
        (folder / "CANVAS_MANIFEST.json").write_text(json.dumps(MANIFEST), encoding="utf-8")

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_deployer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = [CLI_DEPLOY_OK_STDOUT.strip(), "Configuring acme__vitals_alert succeeded."]
            mock_secrets.side_effect = [{"API_KEY": "sk-1", "API_URL": "https://x"}]
            asyncio.run(tested.deploy(plugin_name="vitals_alert", instance=INSTANCE, cwd=str(tmp_path)))

        config_targets = [
            c.kwargs["command"][5] for c in mock_cmd.mock_calls if c.kwargs["command"][2:5] == ["canvas", "config", "set"]
        ]
        assert all(target == PLUGIN for target in config_targets), config_targets
        secrets_keys = [c.args[2] for c in mock_secrets.mock_calls]
        assert all(key == PLUGIN for key in secrets_keys), secrets_keys

    def test_deploy__still_running_hands_off_to_configurer(self, tmp_path: Path) -> None:
        """A deploy that outlives the CLI's wait is not a failure: say variables are unset and to call configurer later."""
        tested = CanvasDeployerMcp
        cwd = make_plugin(tmp_path, MANIFEST)
        still_running = (
            "Command failed with exit code 1\n"
            "Pushed 3f2a9c1d0b7e to main.\n"
            "Deploying acme__vitals_alert@3f2a9c1d0b7e to acme-staging…\n"
            "Deployment 6f1c created.\n"
            "  in_progress…\n"
            "Deploy of acme__vitals_alert is still running after 300s (deployment 6f1c)."
        )

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_deployer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = [still_running]
            result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        prefix = f"Deploy output:\n{still_running}"
        assert result.startswith(prefix)
        note = result[len(prefix):]
        assert "still running" in note
        assert "configurer" in note
        assert mock_cmd.mock_calls == [call(command=DEPLOY_CMD, cwd=cwd)]
        assert mock_secrets.mock_calls == []

    def test_deploy__uncommitted_changes_never_points_at_yes(self, tmp_path: Path) -> None:
        """A dirty tree refusal says to commit or exclude the files, never to retry with --yes, which commits every file."""
        tested = CanvasDeployerMcp
        cwd = make_plugin(tmp_path, MANIFEST)
        dirty = (
            "Command failed with exit code 2\n"
            "Usage: canvas deploy [OPTIONS] PLUGIN_DIR\n"
            "Try 'canvas deploy --help' for help.\n"
            "Error: Invalid value: You have uncommitted changes, and deploy only pushes committed work. "
            "Commit them and run deploy again, pass --yes to commit them, or pass --ref / --no-push to "
            "deploy a ref that is already pushed."
        )

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_deployer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = [dirty]
            result = asyncio.run(tested.deploy(plugin_name=PLUGIN, instance=INSTANCE, cwd=cwd))

        expected = (
            f"Deploy output:\n{dirty}\n\n"
            "Uncommitted files: canvas deploy refuses any uncommitted or untracked file in the repository. "
            "Do not retry with --yes: it commits every file, including ones the user left out, and pushes them "
            "to Canvas Platform. Commit the files the user approves and add the rest to .git/info/exclude, "
            "then call the deployer tool again."
        )
        assert result == expected
        assert mock_cmd.mock_calls == [call(command=DEPLOY_CMD, cwd=cwd)]
        assert mock_secrets.mock_calls == []


class TestPluginLauncher:
    """Tests for the canvas_cmd_line launcher declared in plugin.json."""

    def test_launcher_pins_mcp_v1(self) -> None:
        """The launcher pins mcp below 2.x, which has no mcp.server.fastmcp module."""
        plugin_json = Path(__file__).parents[3] / "canvas-plugin-assistant" / ".claude-plugin" / "plugin.json"
        args = json.loads(plugin_json.read_text(encoding="utf-8"))["mcpServers"]["canvas_cmd_line"]["args"]

        result = args[args.index("--with") + 1]
        assert result.startswith("mcp") and "<2" in result, (
            "mcp_canvas_deployer.py imports mcp.server.fastmcp, which mcp 2.x renamed to "
            "mcp.server.mcpserver; drop this pin only after porting the script to MCPServer"
        )
