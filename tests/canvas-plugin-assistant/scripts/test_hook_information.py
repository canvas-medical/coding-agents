"""Tests for hook_information module."""
from pathlib import Path

from helpers import is_namedtuple

from hook_information import HookInformation


def test_class():
    """Verify HookInformation is a NamedTuple with correct fields."""
    tested = HookInformation
    fields = {
        "session_id": str,
        "exit_reason": str,
        "transcript_path": Path,
        "workspace_dir": Path,
        "working_directory": Path,
    }
    assert is_namedtuple(tested, fields)
