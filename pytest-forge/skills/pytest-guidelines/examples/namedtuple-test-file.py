"""
Complete NamedTuple Test File Example

This file demonstrates pytest guidelines for testing NamedTuple classes, including:
- Proper test structure for NamedTuple verification
- Using is_namedtuple() helper function
- Testing NamedTuple methods
- Naming conventions
- Mock usage with NamedTuple instances
- 100% coverage

Source File: validation_result.py
Test File: test_validation_result.py
"""

# =============================================================================
# SOURCE FILE (validation_result.py)
# =============================================================================
"""
from typing import NamedTuple


class ValidationResult(NamedTuple):
    has_errors: bool
    errors: list[str]

    def is_valid(self) -> bool:
        return not self.has_errors

    def error_count(self) -> int:
        return len(self.errors)

    def add_error(self, error: str) -> 'ValidationResult':
        new_errors = self.errors + [error]
        return ValidationResult(has_errors=True, errors=new_errors)

    def format_errors(self) -> str:
        if not self.has_errors:
            return "No errors"
        return ", ".join(self.errors)
"""

# =============================================================================
# TEST FILE (test_validation_result.py)
# =============================================================================
import pytest
from validation_result import ValidationResult

# Note: is_namedtuple is automatically available from conftest.py
# See examples/conftest.py for the helper function definition


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_class():
    """Verify ValidationResult is a NamedTuple with correct fields."""
    tested = ValidationResult
    fields = {"has_errors": bool, "errors": list[str]}
    assert is_namedtuple(tested, fields)


# Test: is_valid
def test_is_valid__no_errors():
    """Test is_valid returns True when there are no errors"""
    tested = ValidationResult(has_errors=False, errors=[])
    result = tested.is_valid()

    expected = True
    assert result is expected


def test_is_valid__has_errors():
    """Test is_valid returns False when there are errors"""
    tested = ValidationResult(has_errors=True, errors=["Error 1"])
    result = tested.is_valid()

    expected = False
    assert result is expected


# Test: error_count
def test_error_count__no_errors():
    """Test error_count returns 0 for empty errors list"""
    tested = ValidationResult(has_errors=False, errors=[])
    result = tested.error_count()

    expected = 0
    assert result == expected


def test_error_count__multiple_errors():
    """Test error_count returns correct count for multiple errors"""
    tested = ValidationResult(has_errors=True, errors=["Error 1", "Error 2", "Error 3"])
    result = tested.error_count()

    expected = 3
    assert result == expected


@pytest.mark.parametrize(("errors", "expected"), [
    pytest.param([], 0, id="no_errors"),
    pytest.param(["Error 1"], 1, id="single_error"),
    pytest.param(["Error 1", "Error 2"], 2, id="two_errors"),
    pytest.param(["Error 1", "Error 2", "Error 3"], 3, id="three_errors"),
])
def test_error_count__parametrized(errors, expected):
    """Test error_count with multiple scenarios"""
    has_errors = len(errors) > 0
    tested = ValidationResult(has_errors=has_errors, errors=errors)
    result = tested.error_count()

    assert result == expected


# Test: add_error
def test_add_error__to_empty():
    """Test adding error to ValidationResult with no errors"""
    tested = ValidationResult(has_errors=False, errors=[])
    result = tested.add_error("New error")

    exp_has_errors = True
    exp_errors = ["New error"]

    assert result.has_errors is exp_has_errors
    assert result.errors == exp_errors
    # Verify original instance is unchanged (NamedTuple immutability)
    assert tested.has_errors is False
    assert tested.errors == []


def test_add_error__to_existing():
    """Test adding error to ValidationResult with existing errors"""
    tested = ValidationResult(has_errors=True, errors=["Error 1"])
    result = tested.add_error("Error 2")

    exp_has_errors = True
    exp_errors = ["Error 1", "Error 2"]

    assert result.has_errors is exp_has_errors
    assert result.errors == exp_errors
    # Verify original instance is unchanged
    assert tested.errors == ["Error 1"]


# Test: format_errors
def test_format_errors__no_errors():
    """Test format_errors returns message when there are no errors"""
    tested = ValidationResult(has_errors=False, errors=[])
    result = tested.format_errors()

    expected = "No errors"
    assert result == expected


def test_format_errors__single_error():
    """Test format_errors formats single error correctly"""
    tested = ValidationResult(has_errors=True, errors=["Invalid input"])
    result = tested.format_errors()

    expected = "Invalid input"
    assert result == expected


def test_format_errors__multiple_errors():
    """Test format_errors formats multiple errors correctly"""
    tested = ValidationResult(has_errors=True, errors=["Error 1", "Error 2", "Error 3"])
    result = tested.format_errors()

    expected = "Error 1, Error 2, Error 3"
    assert result == expected


@pytest.mark.parametrize(("has_errors", "errors", "expected"), [
    pytest.param(False, [], "No errors", id="no_errors"),
    pytest.param(True, ["Error 1"], "Error 1", id="single_error"),
    pytest.param(True, ["Error 1", "Error 2"], "Error 1, Error 2", id="two_errors"),
    pytest.param(True, ["A", "B", "C"], "A, B, C", id="three_errors"),
])
def test_format_errors__parametrized(has_errors, errors, expected):
    """Test format_errors with multiple scenarios"""
    tested = ValidationResult(has_errors=has_errors, errors=errors)
    result = tested.format_errors()

    assert result == expected


# =============================================================================
# KEY TAKEAWAYS FOR NAMEDTUPLE TESTING
# =============================================================================
"""
1. FIRST TEST - NamedTuple STRUCTURE:
   - MANDATORY: First test must be test_class()
   - Assigns the CLASS itself to 'tested' variable (not an instance)
   - Defines 'fields' dictionary with field names and types
   - Uses is_namedtuple() helper function to verify structure
   - Example: tested = ValidationResult (the class, not ValidationResult(...))

2. is_namedtuple() HELPER:
   - Define once in tests/conftest.py (automatically available to all tests)
   - No need to import - pytest makes conftest.py functions globally available
   - Verifies: tuple subclass, _fields attribute, correct fields, type hints
   - More comprehensive than simple issubclass() check

3. CREATING TEST INSTANCES:
   - Use keyword arguments for clarity: ValidationResult(has_errors=False, errors=[])
   - Don't use positional args: ValidationResult(False, [])
   - Makes tests more readable and maintainable

4. TESTING IMMUTABILITY:
   - NamedTuples are immutable - verify methods return NEW instances
   - Check original instance is unchanged after operations
   - Example: test_add_error verifies 'tested' is unchanged

5. FIELD ACCESS:
   - Access fields directly: tested.has_errors, tested.errors
   - NamedTuples provide both attribute and index access
   - Prefer attribute access for readability

6. NAMING CONVENTIONS:
   - Test naming: test_method_name or test_method_name__case
   - Variables: tested, result, expected, exp_*
   - Same conventions as regular class testing

7. ASSERTIONS:
   - Use 'is' for boolean singletons: assert result is True
   - Use '==' for other comparisons: assert result == "value"
   - Multiple expected values: exp_has_errors, exp_errors

8. PARAMETRIZATION:
   - Use @pytest.mark.parametrize for multiple scenarios
   - CRITICAL: First parameter must be TUPLE: ("has_errors", "errors", "expected")
   - Use pytest.param() with descriptive id parameter

9. TEST ORDERING:
   - First test: test_class() (NamedTuple structure verification)
   - Then: tests in same order as methods appear in source
   - is_valid, error_count, add_error, format_errors

10. COVERAGE:
    - Every method must be tested
    - Edge cases: empty lists, single items, multiple items
    - Both parametrized and individual tests shown for completeness

11. REAL INSTANCES vs MOCKS:
    - NamedTuples are simple data containers - ALWAYS use real instances
    - NEVER mock a NamedTuple class or instance
    - Easy to create, no side effects, provides type safety
    - Example: ValidationResult(has_errors=False, errors=[])

12. WHEN TO MOCK:
    - Mock external dependencies used BY methods
    - Don't mock the NamedTuple itself
    - Example: If format_errors() called an API, mock the API, not the NamedTuple

13. TYPE HINTS MATTER:
    - is_namedtuple() validates type hints match expectations
    - Catches changes to field types
    - Example: list[str] must match exactly, not just list

14. CONSISTENCY:
    - Follow same patterns as regular class testing
    - Mock verification rules apply if methods use external dependencies
    - Same variable naming, assertion style, parametrization approach
"""
