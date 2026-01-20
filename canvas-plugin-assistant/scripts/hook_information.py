"""
Data structures for Claude Code session hook information.

This module defines the HookInformation NamedTuple, which encapsulates all the
context information provided to hooks when a Claude Code session ends.
"""

from pathlib import Path
from typing import NamedTuple


class HookInformation(NamedTuple):
    """
    Encapsulates information passed to hooks when a Claude Code session ends.

    Attributes:
        session_id: Unique identifier for the Claude Code session
        exit_reason: Reason why the session ended (e.g., 'user_exit', 'error')
        transcript_path: Path to the session transcript JSONL file
        workspace_dir: Root directory of the workspace (git repository root or cwd)
        working_directory: Directory where Claude Code was invoked
    """
    session_id: str
    exit_reason: str
    transcript_path: Path
    workspace_dir: Path
    working_directory: Path