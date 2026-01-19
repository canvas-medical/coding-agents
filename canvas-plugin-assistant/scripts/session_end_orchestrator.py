#!/usr/bin/env python3
"""
SessionEnd hook orchestrator that runs all session end actions in order.

This script ensures all SessionEnd hooks run in the correct sequence:
1. CostsLogger - Log session costs
2. UserInputsLogger - Log user inputs
3. GitCommitPlugin - Commit and push plugin changes (must run last)
"""

import sys

from base_logger import BaseLogger
from cost_logger import CostsLogger
from git_commit_plugin import GitCommitPlugin
from user_input_logger import UserInputsLogger


class SessionEndOrchestrator:
    """
    Orchestrates all SessionEnd hook actions in the correct order.

    This class ensures hooks run sequentially, with git commit always running last.
    If any hook fails, it logs the error but continues with the next hook.
    """

    @classmethod
    def run(cls, hook_info) -> None:
        """
        Execute all SessionEnd hooks in the correct order.

        Args:
            hook_info: Context information about the session

        Raises:
            SystemExit: With code 0 on success, 1 on failure
        """
        # Define hooks to run in order
        hooks = [
            (CostsLogger, "Cost Logger"),
            (UserInputsLogger, "User Input Logger"),
            (GitCommitPlugin, "Git Commit Plugin"),
        ]

        # Run each hook in sequence
        for hook_class, display_name in hooks:
            try:
                hook_class.run(hook_info)
            except SystemExit:
                # Hooks call sys.exit(), which raises SystemExit
                # This is expected behavior, so we catch it and continue
                pass
            except Exception as e:
                print(f"Warning: {display_name} failed: {e}", file=sys.stderr)
                # Continue with next hook even if this one failed

        sys.exit(0)


if __name__ == "__main__":
    SessionEndOrchestrator.run(BaseLogger.hook_information())
