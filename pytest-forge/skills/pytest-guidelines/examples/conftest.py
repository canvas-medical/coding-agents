"""
conftest.py - Pytest configuration and shared fixtures

This file should be placed in your tests/ directory root.
All helper functions and fixtures defined here are automatically
available to all test files without explicit imports.
"""

from typing import get_type_hints
from dataclasses import fields as dataclass_fields, is_dataclass as dataclass_is_dataclass


def is_namedtuple(cls, fields: dict) -> bool:
    """
    Verify that a class is a NamedTuple with the expected fields and types.

    Args:
        cls: The class to check
        fields: Dictionary mapping field names to their expected types
                Example: {"has_errors": bool, "errors": list[str]}

    Returns:
        bool: True if cls is a NamedTuple with exactly the specified fields and types

    Usage in tests:
        def test_class():
            tested = ValidationResult
            fields = {"has_errors": bool, "errors": list[str]}
            assert is_namedtuple(tested, fields)
    """
    return (
        issubclass(cls, tuple)
        and hasattr(cls, "_fields")
        and isinstance(cls._fields, tuple)
        and len([field for field in cls._fields if field in fields]) == len(fields.keys())
        and get_type_hints(cls) == fields
    )


def is_dataclass(cls, fields: dict) -> bool:
    """
    Verify that a class is a dataclass with the expected fields and types.

    Args:
        cls: The class to check
        fields: Dictionary mapping field names to their expected types (can be type objects or strings)
                Example: {"speaker": "str", "text": "str", "chunk": "int"}

    Returns:
        bool: True if cls is a dataclass with exactly the specified fields and types

    Usage in tests:
        def test_class():
            tested = TranscriptSegment
            fields = {"speaker": "str", "text": "str", "chunk": "int"}
            assert is_dataclass(tested, fields)
    """
    if not dataclass_is_dataclass(cls):
        return False
    actual_fields = dataclass_fields(cls)
    if len([field for field in actual_fields if field.name in fields]) != len(fields.keys()):
        return False
    for field in actual_fields:
        expected_type = fields[field.name]
        actual_type = field.type
        if expected_type != actual_type:
            return False
    return True
