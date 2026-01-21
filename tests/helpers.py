"""Shared test helper functions."""

from dataclasses import fields as dataclass_fields
from dataclasses import is_dataclass as dataclass_is_dataclass
from typing import get_type_hints


def is_dataclass(cls, fields: dict) -> bool:
    """
    Verify that a class is a dataclass with the expected fields and types.

    Args:
        cls: The class to check
        fields: Dictionary mapping field names to their expected types (can be type objects or strings)

    Returns:
        bool: True if cls is a dataclass with exactly the specified fields and types
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


def is_namedtuple(cls, fields: dict) -> bool:
    """
    Verify that a class is a NamedTuple with the expected fields and types.

    Args:
        cls: The class to check
        fields: Dictionary mapping field names to their expected types

    Returns:
        bool: True if cls is a NamedTuple with exactly the specified fields and types
    """
    return (
        issubclass(cls, tuple)
        and hasattr(cls, "_fields")
        and isinstance(cls._fields, tuple)
        and len([field for field in cls._fields if field in fields]) == len(fields.keys())
        and get_type_hints(cls) == fields
    )
