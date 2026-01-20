"""Pytest configuration and shared fixtures for all tests."""

import sys
from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass as dataclass_is_dataclass
from pathlib import Path

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
