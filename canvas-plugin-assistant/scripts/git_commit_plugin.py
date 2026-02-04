#!/usr/bin/env python3
"""
SessionEnd hook that automatically commits and pushes plugin changes after wrap-up.

This script checks if a wrap-up report exists in .cpa-workflow-artifacts/ and if so,
commits all plugin changes with an appropriate message and pushes to the remote.
"""

import os
import subprocess
import sys
from pathlib import Path

from base_logger import BaseLogger
from hook_information import HookInformation


class GitCommitPlugin:
    """
    Hook that automatically commits plugin changes when wrap-up is complete.

    This hook detects the presence of a wrap-up report and commits all plugin
    changes with a standardized message, then pushes to the remote repository.
    """

    @classmethod
    def run(cls, hook_info: HookInformation) -> None:
        """
        Execute the git commit workflow if wrap-up report exists.

        This method:
        1. Checks if a wrap-up report exists in .cpa-workflow-artifacts/
        2. If found, stages all changes in the plugin directory
        3. Commits with a standardized message
        4. Pushes to the remote repository

        Args:
            hook_info: Context information about the session

        Raises:
            SystemExit: With code 0 on success or if no action needed, 1 on failure
        """
        try:
            # Get the plugin directory from workspace_dir
            plugin_dir = hook_info.workspace_dir

            # Check if we're in a plugin directory
            if not plugin_dir.exists():
                sys.exit(0)  # Not in a plugin directory, exit silently

            # Check for wrap-up report in .cpa-workflow-artifacts/
            artifacts_dir = plugin_dir / ".cpa-workflow-artifacts"
            if not artifacts_dir.exists():
                sys.exit(0)  # No artifacts directory, exit silently

            # Look for any wrap-up-report-*.md file
            wrap_up_reports = list(artifacts_dir.glob("wrap-up-report-*.md"))
            if not wrap_up_reports:
                sys.exit(0)  # No wrap-up report, exit silently

            # Get the most recent wrap-up report
            latest_report = max(wrap_up_reports, key=lambda p: p.stat().st_mtime)

            print(f"Wrap-up report found: {latest_report.name}", file=sys.stderr)

            # Stage all files in the plugin directory
            cls._stage_files(plugin_dir)

            # Check if there are any changes in the plugin directory
            if not cls._has_changes(plugin_dir):
                print("No changes detected in plugin directory, skipping commit", file=sys.stderr)
                sys.exit(0)

            print("Committing plugin changes...", file=sys.stderr)

            # Execute git commands
            cls._commit_and_push(plugin_dir)

            sys.exit(0)

        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e.stderr}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error in git commit hook: {e}", file=sys.stderr)
            sys.exit(1)

    @classmethod
    def _has_changes(cls, plugin_dir: Path) -> bool:
        """
        Check if there are any uncommitted changes in the plugin directory.

        Uses `git status --porcelain` to detect modified, added, or deleted files
        within the plugin directory.

        Args:
            plugin_dir: Path to the plugin directory

        Returns:
            True if there are changes, False otherwise
        """
        original_cwd = Path.cwd()
        try:
            os.chdir(plugin_dir)

            # Use git status --porcelain to check for changes
            # This shows modified, added, deleted files
            result = subprocess.run(
                ["git", "status", "--porcelain", "."],
                check=True,
                capture_output=True,
                text=True
            )

            # If output is empty, there are no changes
            return bool(result.stdout.strip())

        finally:
            os.chdir(original_cwd)

    @classmethod
    def _stage_files(cls, plugin_dir: Path) -> None:
        """
        Stage all files in the plugin directory.

        Uses `git add -A .` to stage all modified, added, and deleted files
        within the plugin directory.

        Args:
            plugin_dir: Path to the plugin directory

        Raises:
            subprocess.CalledProcessError: If the git command fails
        """
        original_cwd = Path.cwd()
        try:
            os.chdir(plugin_dir)

            # Stage all changes in plugin directory
            subprocess.run(
                ["git", "add", "-A", "."],
                check=True,
                capture_output=True,
                text=True
            )

        finally:
            os.chdir(original_cwd)

    @classmethod
    def _commit_and_push(cls, plugin_dir: Path) -> None:
        """
        Stage, commit, and push changes in the plugin directory.

        Args:
            plugin_dir: Path to the plugin directory

        Raises:
            subprocess.CalledProcessError: If any git command fails
        """
        # Change to plugin directory
        original_cwd = Path.cwd()
        try:
            os.chdir(plugin_dir)

            # Get plugin name from directory
            plugin_name = plugin_dir.name

            # Stage all changes in plugin directory
            subprocess.run(
                ["git", "add", "-A", "."],
                check=True,
                capture_output=True,
                text=True
            )

            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                capture_output=True
            )

            if result.returncode != 0:  # There are changes
                # Commit with descriptive message
                commit_message = f"complete {plugin_name} wrap-up\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
                subprocess.run(
                    ["git", "commit", "-m", commit_message],
                    check=True,
                    capture_output=True,
                    text=True
                )

                # Push to remote
                subprocess.run(
                    ["git", "push"],
                    check=True,
                    capture_output=True,
                    text=True
                )

                print(f"✓ Plugin changes committed and pushed", file=sys.stderr)
            else:
                print("No changes to commit", file=sys.stderr)

        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    GitCommitPlugin.run(BaseLogger.hook_information())
