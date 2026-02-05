"""
Validates CPA environment variables before commands are executed.

Usage:
    uv run python validate_cpa_environment.py --require-plugin-dir
    uv run python validate_cpa_environment.py --plugin-dir-optional
"""

import argparse
import os
import sys
from pathlib import Path

from constants import Constants


class CpaEnvironmentValidator:
    """Validates CPA environment variables for Canvas plugin commands."""

    @classmethod
    def run(cls, cpa_running: str, workspace_dir: str, plugin_dir: str, require_plugin_dir: bool) -> None:
        """
        Validate environment variables and exit with appropriate code.

        Args:
            cpa_running: Value of CPA_RUNNING env var
            workspace_dir: Value of CPA_WORKSPACE_DIR env var
            plugin_dir: Value of CPA_PLUGIN_DIR env var
            require_plugin_dir: Whether CPA_PLUGIN_DIR is required
        """
        # Check CPA_RUNNING
        if cpa_running != "1":
            cls.exit_with_error(f"""{Constants.CPA_RUNNING} is not set to 1.

Please /exit and run:
export {Constants.CPA_RUNNING}=1 && claude""")

        # Check CPA_WORKSPACE_DIR
        if not workspace_dir or not Path(workspace_dir).is_dir():
            cls.exit_with_error(f"""{Constants.CPA_WORKSPACE_DIR} is not set or directory doesn't exist.

Please /exit, navigate to your workspace directory, and run:
export {Constants.CPA_WORKSPACE_DIR}=$(pwd) && claude""")

        # Check CPA_PLUGIN_DIR
        if require_plugin_dir and not plugin_dir:
            cls.exit_with_error(f"""{Constants.CPA_PLUGIN_DIR} is not set.

This command requires an existing plugin. To work on a plugin:
1. /exit
2. Run: export {Constants.CPA_PLUGIN_DIR}=${Constants.CPA_WORKSPACE_DIR}/[plugin-name]
3. Run: claude""")

        if plugin_dir:
            plugin_path = Path(plugin_dir)
            workspace_path = Path(workspace_dir)

            if not plugin_path.is_dir():
                cls.exit_with_error(f"{Constants.CPA_PLUGIN_DIR} directory doesn't exist: {plugin_dir}")

            if workspace_path not in plugin_path.parents:
                cls.exit_with_error(f"""{Constants.CPA_PLUGIN_DIR} must be a subdirectory of {Constants.CPA_WORKSPACE_DIR}
  {Constants.CPA_PLUGIN_DIR}: {plugin_dir}
  {Constants.CPA_WORKSPACE_DIR}: {workspace_dir}""")

        # Validation passed
        if plugin_dir:
            print(f"Environment validated. Working in plugin: {Path(plugin_dir).name}")
        else:
            print("Environment validated. Ready for new plugin creation.")

        sys.exit(0)

    @classmethod
    def exit_with_error(cls, message: str) -> None:
        """Print error message and exit with code 1."""
        print(f"ERROR: {message}")
        sys.exit(1)

    @classmethod
    def main(cls) -> None:
        """Parse arguments, read environment variables, and run validation."""
        parser = argparse.ArgumentParser(description="Validate CPA environment variables")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--require-plugin-dir", action="store_true")
        group.add_argument("--plugin-dir-optional", action="store_true")
        args = parser.parse_args()

        cls.run(
            cpa_running=os.environ.get(Constants.CPA_RUNNING, ""),
            workspace_dir=os.environ.get(Constants.CPA_WORKSPACE_DIR, ""),
            plugin_dir=os.environ.get(Constants.CPA_PLUGIN_DIR, ""),
            require_plugin_dir=args.require_plugin_dir,
        )


if __name__ == "__main__":
    CpaEnvironmentValidator.main()
