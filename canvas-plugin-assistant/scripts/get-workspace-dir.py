#!/usr/bin/env python3
"""
Get the workspace directory (git repository root) for storing workflow artifacts.
Falls back to current directory if not in a git repository.

Usage:
    workspace_dir = $(python scripts/get-workspace-dir.py)
"""
import subprocess
import sys
from pathlib import Path


def get_workspace_dir() -> Path:
    """
    Find the git repository root to use as workspace directory.
    Falls back to current directory if not in a git repo.
    """
    try:
        repo_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        return Path(repo_root)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to current directory if not in a git repo
        return Path.cwd()


if __name__ == "__main__":
    workspace_dir = get_workspace_dir()
    print(workspace_dir)
