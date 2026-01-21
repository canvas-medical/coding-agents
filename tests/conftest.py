"""Pytest configuration and shared fixtures for all tests."""

import sys
from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass as dataclass_is_dataclass
from pathlib import Path
from typing import Any


class MockContextManager:
    """
    A simple context manager for testing that avoids MagicMock.

    Use this instead of MagicMock when mocking context managers like urlopen or open.
    This class doesn't require mock_calls verification since it's just a data container.

    Example:
        mock_response = MockContextManager(read_data=b'{"data": "value"}')
        mock_urlopen.side_effect = [mock_response]
    """

    def __init__(self, read_data: bytes | str | None = None, **kwargs: Any) -> None:
        """
        Initialize the mock context manager.

        Args:
            read_data: Data to return from read() method
            **kwargs: Additional attributes to set on the instance
        """
        self._read_data = read_data
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __enter__(self) -> "MockContextManager":
        return self

    def __exit__(self, *args: Any) -> bool:
        return False

    def read(self) -> bytes | str | None:
        return self._read_data

# Add the tests directory to sys.path for helper imports
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

# Add the scripts directory to sys.path for module imports
scripts_dir = Path(__file__).parent.parent / "canvas-plugin-assistant" / "scripts"
sys.path.insert(0, str(scripts_dir))


def is_dataclass(cls: type, fields: dict) -> bool:
    """
    Verify that a class is a dataclass with the expected fields and types.

    Args:
        cls: The class to check
        fields: Dictionary mapping field names to their expected types

    Returns:
        bool: True if cls is a dataclass with exactly the specified fields and types
    """
    if not dataclass_is_dataclass(cls):
        return False
    actual_fields = dataclass_fields(cls)
    if len([field for field in actual_fields if field.name in fields]) != len(
        fields.keys()
    ):
        return False
    for field in actual_fields:
        expected_type = fields[field.name]
        actual_type = field.type
        if expected_type != actual_type:
            return False
    return True
