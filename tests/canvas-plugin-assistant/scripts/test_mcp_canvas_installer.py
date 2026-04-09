"""Tests for mcp_canvas_installer module."""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, call, patch

import pytest

from mcp_canvas_installer import CanvasInstallerMcp


class TestParseSecretNames:
    """Tests for CanvasInstallerMcp._parse_secret_names."""

    @pytest.mark.parametrize(
        ("raw_value", "expected"),
        [
            pytest.param(["API_KEY", "TOKEN"], ["API_KEY", "TOKEN"], id="list_input"),
            pytest.param(["  KEY  ", " VAL "], ["KEY", "VAL"], id="list_strips_whitespace"),
            pytest.param(["KEY", "", "  ", "VAL"], ["KEY", "VAL"], id="list_filters_empty"),
            pytest.param([123, "KEY"], ["123", "KEY"], id="list_non_string_items"),
            pytest.param("KEY1, KEY2, KEY3", ["KEY1", "KEY2", "KEY3"], id="string_comma_separated"),
            pytest.param("KEY1\nKEY2\nKEY3", ["KEY1", "KEY2", "KEY3"], id="string_newline_separated"),
            pytest.param("KEY1,,, KEY2", ["KEY1", "KEY2"], id="string_filters_empty"),
            pytest.param(12345, [], id="unsupported_type"),
            pytest.param(None, [], id="none_input"),
        ],
    )
    def test__parse_secret_names(self, raw_value: object, expected: list[str]) -> None:
        """Parse secret names from various input formats."""
        tested = CanvasInstallerMcp

        result = tested._parse_secret_names(raw_value)

        assert result == expected


class TestRunCanvasCommand:
    """Tests for CanvasInstallerMcp._run_canvas_command."""

    def test__run_canvas_command__invalid_cwd(self, tmp_path: Path) -> None:
        """Return error when cwd does not exist."""
        tested = CanvasInstallerMcp

        result = asyncio.run(tested._run_canvas_command(["echo", "hi"], str(tmp_path / "nonexistent")))

        expected = f"Invalid cwd: {tmp_path / 'nonexistent'}"
        assert result == expected

    def test__run_canvas_command__cwd_is_file(self, tmp_path: Path) -> None:
        """Return error when cwd is a file, not a directory."""
        tested = CanvasInstallerMcp
        a_file = tmp_path / "file.txt"
        a_file.write_text("content")

        result = asyncio.run(tested._run_canvas_command(["echo", "hi"], str(a_file)))

        expected = f"Invalid cwd: {a_file}"
        assert result == expected

    def test__run_canvas_command__success(self, tmp_path: Path) -> None:
        """Return stdout from a successful command."""
        tested = CanvasInstallerMcp

        result = asyncio.run(tested._run_canvas_command(["echo", "hello world"], str(tmp_path)))

        expected = "hello world"
        assert result == expected

    def test__run_canvas_command__combined_output(self, tmp_path: Path) -> None:
        """Return combined stdout and stderr."""
        tested = CanvasInstallerMcp

        result = asyncio.run(
            tested._run_canvas_command(["bash", "-c", "echo out && echo err >&2"], str(tmp_path))
        )

        expected_out = True
        assert ("out" in result) is expected_out
        expected_err = True
        assert ("err" in result) is expected_err

    def test__run_canvas_command__failure(self, tmp_path: Path) -> None:
        """Return error message with exit code for failed command."""
        tested = CanvasInstallerMcp

        result = asyncio.run(tested._run_canvas_command(["bash", "-c", "exit 1"], str(tmp_path)))

        expected = True
        assert ("Command failed with exit code 1" in result) is expected

    def test__run_canvas_command__no_output(self, tmp_path: Path) -> None:
        """Return '(no output)' when command produces no output."""
        tested = CanvasInstallerMcp

        result = asyncio.run(tested._run_canvas_command(["bash", "-c", "true"], str(tmp_path)))

        expected = "(no output)"
        assert result == expected


class TestInstall:
    """Tests for CanvasInstallerMcp.install."""

    def test_install__missing_plugin_name(self) -> None:
        """Return error when plugin_name is empty."""
        tested = CanvasInstallerMcp

        result = asyncio.run(tested.install(plugin_name="", instance="host", cwd="/tmp"))

        expected = "Error: missing plugin_name"
        assert result == expected

    def test_install__missing_instance(self) -> None:
        """Return error when instance is empty."""
        tested = CanvasInstallerMcp

        result = asyncio.run(tested.install(plugin_name="plug", instance="", cwd="/tmp"))

        expected = "Error: missing instance"
        assert result == expected

    def test_install__missing_cwd(self) -> None:
        """Return error when cwd is empty."""
        tested = CanvasInstallerMcp

        result = asyncio.run(tested.install(plugin_name="plug", instance="host", cwd=""))

        expected = "Error: missing cwd"
        assert result == expected

    def test_install__plugin_dir_not_found(self, tmp_path: Path) -> None:
        """Return error when plugin directory does not exist."""
        tested = CanvasInstallerMcp

        result = asyncio.run(tested.install(plugin_name="missing_plug", instance="host", cwd=str(tmp_path)))

        expected = True
        assert ("Error: plugin directory not found" in result) is expected

    def test_install__manifest_not_found(self, tmp_path: Path) -> None:
        """Return error when CANVAS_MANIFEST.json does not exist."""
        tested = CanvasInstallerMcp
        plugin_dir = tmp_path / "my_plugin"
        plugin_dir.mkdir()

        result = asyncio.run(tested.install(plugin_name="my_plugin", instance="host", cwd=str(tmp_path)))

        expected = True
        assert ("Error: manifest not found" in result) is expected

    def test_install__no_secrets(self, tmp_path: Path) -> None:
        """Install plugin with no secrets defined in manifest."""
        tested = CanvasInstallerMcp
        plugin_dir = tmp_path / "my_plugin"
        plugin_dir.mkdir()
        manifest = plugin_dir / "CANVAS_MANIFEST.json"
        manifest.write_text(json.dumps({"name": "my_plugin"}), encoding="utf-8")

        with patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.side_effect = ["Installed OK"]
            result = asyncio.run(tested.install(plugin_name="my_plugin", instance="host", cwd=str(tmp_path)))

        expected = "Install output:\nInstalled OK"
        assert result == expected

        exp_cmd_calls = [
            call(
                command=["uv", "run", "canvas", "install", "my_plugin", "--host", "host"],
                cwd=str(tmp_path),
            )
        ]
        assert mock_cmd.mock_calls == exp_cmd_calls

    def test_install__all_secrets_provided(self, tmp_path: Path) -> None:
        """Install plugin with all secrets provided."""
        tested = CanvasInstallerMcp
        plugin_dir = tmp_path / "my_plugin"
        plugin_dir.mkdir()
        manifest = plugin_dir / "CANVAS_MANIFEST.json"
        manifest.write_text(json.dumps({"secrets": ["API_KEY", "TOKEN"]}), encoding="utf-8")

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_installer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = ["Installed OK"]
            mock_secrets.side_effect = [{"API_KEY": "sk-1", "TOKEN": "tk-2"}]
            result = asyncio.run(tested.install(plugin_name="my_plugin", instance="host", cwd=str(tmp_path)))

        expected = "Install output:\nInstalled OK"
        assert result == expected

        exp_cmd_calls = [
            call(
                command=[
                    "uv", "run", "canvas", "install", "my_plugin", "--host", "host",
                    "--secret", "API_KEY=sk-1", "--secret", "TOKEN=tk-2",
                ],
                cwd=str(tmp_path),
            )
        ]
        assert mock_cmd.mock_calls == exp_cmd_calls

        exp_secrets_calls = [call(["API_KEY", "TOKEN"], "host", "my_plugin")]
        assert mock_secrets.mock_calls == exp_secrets_calls

    def test_install__missing_secrets_shows_warning(self, tmp_path: Path) -> None:
        """Show warning for secrets with empty values."""
        tested = CanvasInstallerMcp
        plugin_dir = tmp_path / "my_plugin"
        plugin_dir.mkdir()
        manifest = plugin_dir / "CANVAS_MANIFEST.json"
        manifest.write_text(json.dumps({"secrets": ["API_KEY", "MISSING_KEY"]}), encoding="utf-8")

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_installer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = ["Installed OK"]
            mock_secrets.side_effect = [{"API_KEY": "sk-1"}]
            result = asyncio.run(tested.install(plugin_name="my_plugin", instance="host", cwd=str(tmp_path)))

        expected = "Install output:\nInstalled OK\nWarning: secrets not provided (missing or empty): MISSING_KEY"
        assert result == expected

        exp_cmd_calls = [
            call(
                command=[
                    "uv", "run", "canvas", "install", "my_plugin", "--host", "host",
                    "--secret", "API_KEY=sk-1",
                ],
                cwd=str(tmp_path),
            )
        ]
        assert mock_cmd.mock_calls == exp_cmd_calls

        exp_secrets_calls = [call(["API_KEY", "MISSING_KEY"], "host", "my_plugin")]
        assert mock_secrets.mock_calls == exp_secrets_calls

    def test_install__skips_empty_value_secrets(self, tmp_path: Path) -> None:
        """Do not pass --secret flag for secrets with empty values."""
        tested = CanvasInstallerMcp
        plugin_dir = tmp_path / "my_plugin"
        plugin_dir.mkdir()
        manifest = plugin_dir / "CANVAS_MANIFEST.json"
        manifest.write_text(json.dumps({"secrets": ["KEY"]}), encoding="utf-8")

        with (
            patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd,
            patch("mcp_canvas_installer.SecretRequester.get_secrets") as mock_secrets,
        ):
            mock_cmd.side_effect = ["OK"]
            mock_secrets.side_effect = [{}]
            result = asyncio.run(tested.install(plugin_name="my_plugin", instance="host", cwd=str(tmp_path)))

        expected = "Install output:\nOK\nWarning: secrets not provided (missing or empty): KEY"
        assert result == expected

        exp_cmd_calls = [
            call(
                command=["uv", "run", "canvas", "install", "my_plugin", "--host", "host"],
                cwd=str(tmp_path),
            )
        ]
        assert mock_cmd.mock_calls == exp_cmd_calls

        exp_secrets_calls = [call(["KEY"], "host", "my_plugin")]
        assert mock_secrets.mock_calls == exp_secrets_calls


class TestListPlugins:
    """Tests for CanvasInstallerMcp.list_plugins."""

    def test_list_plugins__missing_instance(self) -> None:
        """Return error when instance is empty."""
        tested = CanvasInstallerMcp

        result = asyncio.run(tested.list_plugins(instance="", cwd="/tmp"))

        expected = "Error: missing instance"
        assert result == expected

    def test_list_plugins__missing_cwd(self) -> None:
        """Return error when cwd is empty."""
        tested = CanvasInstallerMcp

        result = asyncio.run(tested.list_plugins(instance="host", cwd=""))

        expected = "Error: missing cwd"
        assert result == expected

    def test_list_plugins__success(self) -> None:
        """Return formatted list of plugins."""
        tested = CanvasInstallerMcp

        with patch.object(tested, "_run_canvas_command", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.side_effect = ["plugin_a\nplugin_b"]
            result = asyncio.run(tested.list_plugins(instance="host", cwd="/tmp"))

        expected = "Installed plugins:\nplugin_a\nplugin_b"
        assert result == expected

        exp_cmd_calls = [
            call(command=["uv", "run", "canvas", "list", "--host", "host"], cwd="/tmp")
        ]
        assert mock_cmd.mock_calls == exp_cmd_calls


class TestCreateServer:
    """Tests for CanvasInstallerMcp.create_server."""

    def test_create_server__returns_server(self) -> None:
        """Return a FastMCP server with correct name."""
        tested = CanvasInstallerMcp

        result = tested.create_server()

        expected = "canvas_cmd_line"
        assert result.name == expected

    def test_create_server__has_installer_tool(self) -> None:
        """Server has the installer tool registered."""
        tested = CanvasInstallerMcp
        server = tested.create_server()

        tool_names = [tool.name for tool in server._tool_manager.list_tools()]

        expected = True
        assert ("installer" in tool_names) is expected

    def test_create_server__has_lister_tool(self) -> None:
        """Server has the lister tool registered."""
        tested = CanvasInstallerMcp
        server = tested.create_server()

        tool_names = [tool.name for tool in server._tool_manager.list_tools()]

        expected = True
        assert ("lister" in tool_names) is expected

    def test_create_server__installer_delegates(self) -> None:
        """The installer tool delegates to cls.install."""
        tested = CanvasInstallerMcp
        server = tested.create_server()

        with patch.object(tested, "install", new_callable=AsyncMock) as mock_install:
            mock_install.side_effect = ["mocked"]
            tool = server._tool_manager._tools["installer"]
            result = asyncio.run(tool.fn(plugin_name="p", instance="i", cwd="c"))

        expected = "mocked"
        assert result == expected

        exp_install_calls = [call("p", "i", "c")]
        assert mock_install.mock_calls == exp_install_calls

    def test_create_server__lister_delegates(self) -> None:
        """The lister tool delegates to cls.list_plugins."""
        tested = CanvasInstallerMcp
        server = tested.create_server()

        with patch.object(tested, "list_plugins", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = ["mocked"]
            tool = server._tool_manager._tools["lister"]
            result = asyncio.run(tool.fn(instance="i", cwd="c"))

        expected = "mocked"
        assert result == expected

        exp_list_calls = [call("i", "c")]
        assert mock_list.mock_calls == exp_list_calls
