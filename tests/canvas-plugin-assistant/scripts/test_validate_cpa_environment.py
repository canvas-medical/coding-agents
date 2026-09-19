"""Tests for validate_cpa_environment module."""

from types import SimpleNamespace
from unittest.mock import call, patch

import pytest

from validate_cpa_environment import CpaEnvironmentValidator


class TestRun:
    """Tests for CpaEnvironmentValidator.run method."""

    def test_run__cpa_running_not_set(self, capsys):
        """Test run exits with error when CPA_RUNNING is not set to 1."""
        tested = CpaEnvironmentValidator

        with pytest.raises(SystemExit) as exc_info:
            tested.run(
                cpa_running="",
                workspace_dir="/some/dir",
                plugin_dir="",
                require_plugin_dir=False,
            )

        result = exc_info.value.code
        expected = 1
        assert result == expected

        captured = capsys.readouterr()
        assert "CPA_RUNNING is not set to 1" in captured.out
        assert "export CPA_RUNNING=1 && claude" in captured.out

    def test_run__cpa_running_wrong_value(self, capsys):
        """Test run exits with error when CPA_RUNNING has wrong value."""
        tested = CpaEnvironmentValidator

        with pytest.raises(SystemExit) as exc_info:
            tested.run(
                cpa_running="0",
                workspace_dir="/some/dir",
                plugin_dir="",
                require_plugin_dir=False,
            )

        result = exc_info.value.code
        expected = 1
        assert result == expected

        captured = capsys.readouterr()
        assert "CPA_RUNNING is not set to 1" in captured.out

    def test_run__workspace_dir_empty(self, capsys):
        """Test run exits with error when CPA_WORKSPACE_DIR is empty."""
        tested = CpaEnvironmentValidator

        with pytest.raises(SystemExit) as exc_info:
            tested.run(
                cpa_running="1",
                workspace_dir="",
                plugin_dir="",
                require_plugin_dir=False,
            )

        result = exc_info.value.code
        expected = 1
        assert result == expected

        captured = capsys.readouterr()
        assert "CPA_WORKSPACE_DIR is not set or directory doesn't exist" in captured.out
        assert "export CPA_WORKSPACE_DIR=$(pwd) && claude" in captured.out

    def test_run__workspace_dir_not_exists(self, capsys):
        """Test run exits with error when CPA_WORKSPACE_DIR directory doesn't exist."""
        tested = CpaEnvironmentValidator

        with pytest.raises(SystemExit) as exc_info:
            tested.run(
                cpa_running="1",
                workspace_dir="/nonexistent/directory/path",
                plugin_dir="",
                require_plugin_dir=False,
            )

        result = exc_info.value.code
        expected = 1
        assert result == expected

        captured = capsys.readouterr()
        assert "CPA_WORKSPACE_DIR is not set or directory doesn't exist" in captured.out

    def test_run__plugin_dir_required_but_not_set(self, tmp_path, capsys):
        """Test run exits with error when plugin dir is required but not set."""
        tested = CpaEnvironmentValidator
        workspace_dir = str(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            tested.run(
                cpa_running="1",
                workspace_dir=workspace_dir,
                plugin_dir="",
                require_plugin_dir=True,
            )

        result = exc_info.value.code
        expected = 1
        assert result == expected

        captured = capsys.readouterr()
        assert "CPA_PLUGIN_DIR is not set" in captured.out
        assert "This command requires an existing plugin" in captured.out

    def test_run__plugin_dir_not_exists(self, tmp_path, capsys):
        """Test run exits with error when plugin dir doesn't exist."""
        tested = CpaEnvironmentValidator
        workspace_dir = str(tmp_path)
        plugin_dir = str(tmp_path / "nonexistent_plugin")

        with pytest.raises(SystemExit) as exc_info:
            tested.run(
                cpa_running="1",
                workspace_dir=workspace_dir,
                plugin_dir=plugin_dir,
                require_plugin_dir=True,
            )

        result = exc_info.value.code
        expected = 1
        assert result == expected

        captured = capsys.readouterr()
        assert "CPA_PLUGIN_DIR directory doesn't exist" in captured.out
        assert plugin_dir in captured.out

    def test_run__plugin_dir_not_under_workspace(self, tmp_path, capsys):
        """Test run exits with error when plugin dir is not under workspace."""
        tested = CpaEnvironmentValidator
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        plugin_dir = tmp_path / "other_location"
        plugin_dir.mkdir()

        with pytest.raises(SystemExit) as exc_info:
            tested.run(
                cpa_running="1",
                workspace_dir=str(workspace_dir),
                plugin_dir=str(plugin_dir),
                require_plugin_dir=True,
            )

        result = exc_info.value.code
        expected = 1
        assert result == expected

        captured = capsys.readouterr()
        assert "CPA_PLUGIN_DIR must be a subdirectory of CPA_WORKSPACE_DIR" in captured.out

    def test_run__success_with_plugin_dir(self, tmp_path, capsys):
        """Test run succeeds with valid plugin directory."""
        tested = CpaEnvironmentValidator
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        plugin_dir = workspace_dir / "my_plugin"
        plugin_dir.mkdir()

        with pytest.raises(SystemExit) as exc_info:
            tested.run(
                cpa_running="1",
                workspace_dir=str(workspace_dir),
                plugin_dir=str(plugin_dir),
                require_plugin_dir=True,
            )

        result = exc_info.value.code
        expected = 0
        assert result == expected

        captured = capsys.readouterr()
        assert "Environment validated. Working in plugin: my_plugin" in captured.out

    def test_run__success_without_plugin_dir(self, tmp_path, capsys):
        """Test run succeeds without plugin directory when not required."""
        tested = CpaEnvironmentValidator
        workspace_dir = str(tmp_path)

        with pytest.raises(SystemExit) as exc_info:
            tested.run(
                cpa_running="1",
                workspace_dir=workspace_dir,
                plugin_dir="",
                require_plugin_dir=False,
            )

        result = exc_info.value.code
        expected = 0
        assert result == expected

        captured = capsys.readouterr()
        assert "Environment validated. Ready for new plugin creation." in captured.out

    def test_run__plugin_dir_optional_but_provided(self, tmp_path, capsys):
        """Test run succeeds when plugin dir is optional and provided."""
        tested = CpaEnvironmentValidator
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        plugin_dir = workspace_dir / "optional_plugin"
        plugin_dir.mkdir()

        with pytest.raises(SystemExit) as exc_info:
            tested.run(
                cpa_running="1",
                workspace_dir=str(workspace_dir),
                plugin_dir=str(plugin_dir),
                require_plugin_dir=False,
            )

        result = exc_info.value.code
        expected = 0
        assert result == expected

        captured = capsys.readouterr()
        assert "Environment validated. Working in plugin: optional_plugin" in captured.out


class TestExitWithError:
    """Tests for CpaEnvironmentValidator.exit_with_error method."""

    def test_exit_with_error(self, capsys):
        """Test exit_with_error prints message and exits with code 1."""
        tested = CpaEnvironmentValidator

        with pytest.raises(SystemExit) as exc_info:
            tested.exit_with_error("Test error message")

        result = exc_info.value.code
        expected = 1
        assert result == expected

        captured = capsys.readouterr()
        assert "ERROR: Test error message" in captured.out


class TestMain:
    """Tests for CpaEnvironmentValidator.main method."""

    @patch("validate_cpa_environment.CpaEnvironmentValidator.run")
    def test_main__require_plugin_dir(self, mock_run, monkeypatch, tmp_path):
        """Test main with --require-plugin-dir flag."""
        tested = CpaEnvironmentValidator
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()
        plugin_dir = workspace_dir / "test_plugin"
        plugin_dir.mkdir()

        monkeypatch.setenv("CPA_RUNNING", "1")
        monkeypatch.setenv("CPA_WORKSPACE_DIR", str(workspace_dir))
        monkeypatch.setenv("CPA_PLUGIN_DIR", str(plugin_dir))
        monkeypatch.setattr("sys.argv", ["validate_cpa_environment.py", "--require-plugin-dir"])
        mock_run.side_effect = [None]

        tested.main()

        exp_run_calls = [
            call(
                cpa_running="1",
                workspace_dir=str(workspace_dir),
                plugin_dir=str(plugin_dir),
                require_plugin_dir=True,
                require_style_tools=False,
            )
        ]
        assert mock_run.mock_calls == exp_run_calls

    @patch("validate_cpa_environment.CpaEnvironmentValidator.run")
    def test_main__plugin_dir_optional(self, mock_run, monkeypatch, tmp_path):
        """Test main with --plugin-dir-optional flag."""
        tested = CpaEnvironmentValidator
        workspace_dir = str(tmp_path)

        monkeypatch.setenv("CPA_RUNNING", "1")
        monkeypatch.setenv("CPA_WORKSPACE_DIR", workspace_dir)
        monkeypatch.delenv("CPA_PLUGIN_DIR", raising=False)
        monkeypatch.setattr("sys.argv", ["validate_cpa_environment.py", "--plugin-dir-optional"])
        mock_run.side_effect = [None]

        tested.main()

        exp_run_calls = [
            call(
                cpa_running="1",
                workspace_dir=workspace_dir,
                plugin_dir="",
                require_plugin_dir=False,
                require_style_tools=False,
            )
        ]
        assert mock_run.mock_calls == exp_run_calls


class TestCheckStyleTools:
    """Tests for the opt-in style-toolchain check.

    /cpa:style resolves ruff and mypy through uv rather than assuming them on
    PATH. Checking up front turns an unresolvable toolchain into a stated setup
    error instead of a verdict of `null` discovered several steps later.
    """

    def test_missing_tools_are_a_setup_error(self, tmp_path, capsys):
        """Both tools unresolvable exits 1 and names each spec."""
        tested = CpaEnvironmentValidator

        with patch(
            "validate_cpa_environment.tool_available", return_value=False
        ), pytest.raises(SystemExit) as exc_info:
            tested.check_style_tools(tmp_path)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "could not resolve the style toolchain" in captured.out
        assert "ruff==" in captured.out
        assert "mypy>=" in captured.out

    def test_resolvable_tools_do_not_exit(self, tmp_path, capsys):
        """The negative case above only means something if this one passes."""
        tested = CpaEnvironmentValidator

        with patch("validate_cpa_environment.tool_available", return_value=True):
            tested.check_style_tools(tmp_path)

        assert "Style toolchain resolved" in capsys.readouterr().out

    def test_the_check_is_opt_in(self, tmp_path, capsys):
        """Without the flag, run() never probes — the other commands are untouched.

        new-plugin, wrap-up and deploy call this script too, and must not start
        failing on a toolchain they do not use.
        """
        tested = CpaEnvironmentValidator

        with patch("validate_cpa_environment.tool_available") as probe, pytest.raises(
            SystemExit
        ) as exc_info:
            tested.run(
                cpa_running="1",
                workspace_dir=str(tmp_path),
                plugin_dir="",
                require_plugin_dir=False,
            )

        assert exc_info.value.code == 0
        probe.assert_not_called()

    def test_the_flag_makes_run_probe(self, tmp_path, capsys):
        """With the flag, an unresolvable toolchain fails the whole validation."""
        tested = CpaEnvironmentValidator

        with patch(
            "validate_cpa_environment.tool_available", return_value=False
        ), pytest.raises(SystemExit) as exc_info:
            tested.run(
                cpa_running="1",
                workspace_dir=str(tmp_path),
                plugin_dir="",
                require_plugin_dir=False,
                require_style_tools=True,
            )

        assert exc_info.value.code == 1
        assert "could not resolve the style toolchain" in capsys.readouterr().out
