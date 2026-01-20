"""Tests for get_plugin_dir.py module."""

from pathlib import Path
from unittest.mock import call, patch

import pytest

from get_plugin_dir import PluginDir


class TestPluginDir:
    """Tests for PluginDir class."""

    def test_run__cpa_plugin_dir_set(self) -> None:
        """Test run returns Path from CPA_PLUGIN_DIR when set."""
        tested = PluginDir
        with patch("get_plugin_dir.environ") as mock_environ:
            mock_environ.get.side_effect = ["/custom/plugin/dir"]

            result = tested.run()

            expected = Path("/custom/plugin/dir")
            assert result == expected

            exp_environ_calls = [call.get("CPA_PLUGIN_DIR", "")]
            assert mock_environ.mock_calls == exp_environ_calls

    def test_run__cpa_workspace_dir_fallback(self) -> None:
        """Test run falls back to CPA_WORKSPACE_DIR when CPA_PLUGIN_DIR is empty."""
        tested = PluginDir
        with patch("get_plugin_dir.environ") as mock_environ:
            mock_environ.get.side_effect = ["", "/workspace/dir"]

            result = tested.run()

            expected = Path("/workspace/dir")
            assert result == expected

            exp_environ_calls = [
                call.get("CPA_PLUGIN_DIR", ""),
                call.get("CPA_WORKSPACE_DIR", ""),
            ]
            assert mock_environ.mock_calls == exp_environ_calls

    def test_run__cwd_fallback(self) -> None:
        """Test run falls back to cwd when both env vars are empty."""
        tested = PluginDir
        with patch("get_plugin_dir.environ") as mock_environ, patch(
            "get_plugin_dir.Path"
        ) as mock_path:
            mock_environ.get.side_effect = ["", ""]
            mock_path.cwd.side_effect = [Path("/current/working/dir")]

            result = tested.run()

            expected = Path("/current/working/dir")
            assert result == expected

            exp_environ_calls = [
                call.get("CPA_PLUGIN_DIR", ""),
                call.get("CPA_WORKSPACE_DIR", ""),
            ]
            assert mock_environ.mock_calls == exp_environ_calls

            exp_path_calls = [call.cwd()]
            assert mock_path.mock_calls == exp_path_calls


class TestMainBlock:
    """Tests for the __main__ block execution."""

    def test_main_prints_plugin_dir(self) -> None:
        """Test that running the module as main prints the plugin directory."""
        with patch("get_plugin_dir.PluginDir") as mock_plugin_dir, patch(
            "builtins.print"
        ) as mock_print:
            mock_plugin_dir.run.side_effect = [Path("/test/dir")]

            exec(
                compile(
                    'if __name__ == "__main__":\n    print(PluginDir.run())',
                    "<string>",
                    "exec",
                ),
                {"__name__": "__main__", "PluginDir": mock_plugin_dir, "print": mock_print},
            )

            exp_plugin_dir_calls = [call.run()]
            assert mock_plugin_dir.mock_calls == exp_plugin_dir_calls

            exp_print_calls = [call(Path("/test/dir"))]
            assert mock_print.mock_calls == exp_print_calls
