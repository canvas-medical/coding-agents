---
name: Pytest Testing Guidelines
description: This skill should be used when the user asks to "write tests", "create tests", "generate tests", "unit tests", "pytest", "test guidelines", "testing rules", "test standards", "how to test", "test this code", "add tests", "validate tests", "check tests", "improve tests", or when working with Python test files. Provides comprehensive guidelines for creating pytest unit tests with 100% coverage following strict naming conventions, mock patterns, and parametrization standards.
version: 0.1.0
---

# Pytest Testing Guidelines

## Overview

These guidelines define a rigorous testing approach for Python projects using pytest, emphasizing 100% code coverage, strict naming conventions, comprehensive mock verification, and maintainable test structure. Follow these guidelines to create tests that ensure code reliability and prevent regressions.

## Core Principles

**100% Coverage Requirement**: Every line of code must be tested. This ensures that any code change will not have negative impact on untested code.

**Comprehensive Mock Verification**: All mock interactions must be verified through the `mock_calls` property. This ensures that all manipulations of mocks are checked, preventing incomplete test coverage of external dependencies.

**Consistent Naming**: Strict naming conventions improve test readability and maintenance, making it immediately clear what each test covers.

**Test Order Matches Source**: Tests should appear in the same order as methods in the source file, making it easy to verify complete coverage by visual inspection.

## Source Code Requirements

### Type Annotations Validation

**MANDATORY PRE-CHECK**: Before generating tests, improving tests, or validating tests, the commands `generate-tests`, `improve-tests`, and `validate-tests` must first verify that the source code has complete type annotations.

**Required type annotations**:
- All method/function parameters must have type annotations
- All method/function return values must have type annotations
- Class attributes should have type annotations where applicable

**Example of properly typed code**:
```python
class DataProcessor:
    def __init__(self, config: dict[str, str]) -> None:
        self.config = config

    def process(self, data: list[str], validate: bool = True) -> dict[str, int]:
        # Implementation
        pass

    def _validate(self, item: str) -> bool:
        # Implementation
        pass
```

**Example of code missing type annotations** (will be rejected):
```python
class DataProcessor:
    def __init__(self, config):  # Missing parameter and return types
        self.config = config

    def process(self, data, validate=True):  # Missing all type annotations
        pass

    def _validate(self, item):  # Missing parameter and return types
        pass
```

**Validation process**:
1. Parse the source file to identify all functions and methods
2. Check each function/method for:
   - Type annotations on ALL parameters (except `self` and `cls`)
   - Return type annotation (including `-> None` for void functions)
3. If any type annotations are missing:
   - Report which functions/methods are missing annotations
   - List the specific parameters or return types that need annotations
   - **STOP** - do not proceed with test generation/improvement/validation
4. Only proceed with the requested operation if all type annotations are present

**Why this matters**:
- Type annotations enable better test generation with correct expected types
- They improve mock configuration accuracy
- They help verify test assertions match the expected return types
- They ensure tests validate the documented contract of the code

## Naming Conventions

### Test File Names

Mirror the source file structure in the `tests/` directory:

```
src/utils/parser.py → tests/utils/test_parser.py
src/models/user.py → tests/models/test_user.py
```

Each test file name must start with `test_` prefix.

### Test Function Names

Follow this pattern: `test_<method_name>` for single-scenario tests, or `test_<method_name>__<case_description>` for multiple scenarios.

**Basic format**:
```python
def test_calculate_total():
    # Tests the calculate_total method
```

**Include underscore prefix for private methods**:
```python
# For method named _private_helper
def test__private_helper():
    # Underscore is included in test name
```

**Multiple test cases**:
```python
def test_validate_input__valid_data():
    # Test with valid data

def test_validate_input__invalid_format():
    # Test with invalid format

def test_validate_input__empty_input():
    # Test with empty input
```

The double underscore `__` separates the method name from the case description.

### Variable Names

Use these standard names consistently across all tests:

- **`tested`**: The class or instance being tested (MUST be assigned FIRST in every test)
- **`result`**: The value returned from the method under test (MUST be used for return values)
- **`expected`**: The expected value for single assertions (MUST be used when comparing result)
- **`exp_*`**: Expected values for multiple assertions (e.g., `exp_calls`, `exp_output`, `exp_status`)

**CRITICAL - Variable Naming Requirements**:

Every test MUST follow these naming conventions strictly:

#### 1. The `tested` Variable

- Assign the class or instance being tested to a `tested` variable FIRST
- Call methods on `tested`, NEVER directly on the class name

**Example for instance methods**:
```python
def test_format_name():
    tested = NameFormatter()  # Assign instance to tested
    result = tested.format_name("john", "doe")  # Call on tested
    expected = "John Doe"
    assert result == expected
```

**Example for class/static methods**:
```python
def test_parse_arguments():
    tested = SvgToPngConverter  # Assign CLASS to tested (not an instance)
    result = tested.parse_arguments()  # Call on tested
    expected = ConversionInput(...)
    assert result == expected
```

**FORBIDDEN**:
```python
# WRONG - calling directly on class name
def test_parse_arguments():
    result = SvgToPngConverter.parse_arguments()  # FORBIDDEN
    ...
```

#### 2. The `result` Variable

- ALWAYS store the return value from the method under test in a variable named `result`
- NEVER use alternative names like `output`, `ret`, `actual`, `response`, `value`, etc.

**CORRECT**:
```python
def test_calculate_total():
    tested = Calculator()
    result = tested.calculate_total([1, 2, 3])  # CORRECT: use 'result'
    expected = 6
    assert result == expected
```

**FORBIDDEN**:
```python
def test_calculate_total():
    tested = Calculator()
    output = tested.calculate_total([1, 2, 3])  # FORBIDDEN: don't use 'output'
    total = tested.calculate_total([1, 2, 3])   # FORBIDDEN: don't use 'total'
    ret = tested.calculate_total([1, 2, 3])     # FORBIDDEN: don't use 'ret'
    ...
```

#### 3. The `expected` Variable

- ALWAYS store the expected value for the main assertion in a variable named `expected`
- NEVER use alternative names like `want`, `exp`, `correct`, `answer`, etc.
- NEVER inline the expected value in the assertion

**CORRECT**:
```python
def test_format_date():
    tested = DateFormatter()
    result = tested.format("2024-01-15")
    expected = "January 15, 2024"  # CORRECT: use 'expected'
    assert result == expected
```

**FORBIDDEN**:
```python
def test_format_date():
    tested = DateFormatter()
    result = tested.format("2024-01-15")
    assert result == "January 15, 2024"  # FORBIDDEN: inlined expected value

def test_format_date():
    tested = DateFormatter()
    result = tested.format("2024-01-15")
    want = "January 15, 2024"  # FORBIDDEN: don't use 'want'
    assert result == want
```

#### 4. The `exp_*` Pattern for Multiple Assertions

- Use `exp_` prefix for expected values when a test has multiple assertions
- Common patterns: `exp_calls`, `exp_output`, `exp_status`, `exp_error`, `exp_mock_calls`
- NEVER use `expected_` prefix (too long) - always use `exp_`

**CORRECT**:
```python
@patch('module.api')
def test_fetch_data(mock_api):
    mock_api.get.side_effect = [{"data": "value"}]

    tested = DataFetcher()
    result = tested.fetch("http://example.com")

    expected = {"data": "value"}
    assert result == expected

    exp_api_calls = [call.get("http://example.com")]  # CORRECT: use 'exp_' prefix
    assert mock_api.mock_calls == exp_api_calls
```

**FORBIDDEN**:
```python
@patch('module.api')
def test_fetch_data(mock_api):
    ...
    expected_calls = [call.get("http://example.com")]  # FORBIDDEN: don't use 'expected_'
    expected_api_calls = [call.get("http://example.com")]  # FORBIDDEN: too long
    calls = [call.get("http://example.com")]  # FORBIDDEN: not descriptive
    ...
```

For detailed naming examples, see `references/naming-conventions.md`.

### Assertion Style

**Singleton Comparisons**: Use `is` (not `==`) when comparing to singletons: `True`, `False`, `None`.

**Correct**:
```python
def test_is_valid():
    tested = Validator()
    result = tested.is_valid("data")
    expected = True
    assert result is expected  # Use 'is' for boolean singletons
```

**Incorrect**:
```python
def test_is_valid():
    tested = Validator()
    result = tested.is_valid("data")
    expected = True
    assert result == expected  # Wrong: use 'is' not '=='
```

**When to use `is`**:
- Comparing to `True`
- Comparing to `False`
- Comparing to `None`

**When to use `==`**:
- All other comparisons (strings, numbers, lists, dicts, objects, etc.)

## Test Structure and Order

### Test Order Matches Source Code

Tests must appear in the same order as methods appear in the source file. This enables:
- Quick visual verification of coverage
- Easy navigation between source and tests
- Clear indication of missing tests

**Source file order**:
```python
class Calculator:
    def __init__(self):
        pass

    def add(self, a, b):
        pass

    def subtract(self, a, b):
        pass

    def _validate(self, value):
        pass
```

**Test file order**:
```python
def test_add():
    pass

def test_subtract():
    pass

def test__validate():
    pass
```

### First Test: Verify Inheritance

**MANDATORY**: When testing a class that inherits from a base class, the very first test in the test file must verify the inheritance relationship using `issubclass()`.

This test ensures that:
- The class is properly inheriting from the expected base class
- The inheritance hierarchy is correct
- Any refactoring that breaks inheritance is immediately caught

**Example**:
```python
# Source: scripts/user_input_logger.py
class UserInputsLogger(BaseLogger):
    def process(self, data):
        pass

# Test file: tests/scripts/test_user_input_logger.py
def test_inheritance():
    """Verify UserInputsLogger inherits from BaseLogger."""
    assert issubclass(UserInputsLogger, BaseLogger)

def test_process():
    # Remaining tests follow...
    pass
```

**Pattern**:
```python
def test_inheritance():
    """Verify <ClassName> inherits from <BaseClassName>."""
    assert issubclass(ClassName, BaseClassName)
```

This test should:
- Always be named `test_inheritance`
- Always be the first test in the file
- Include a docstring describing the inheritance relationship
- Use a simple `assert issubclass(DerivedClass, BaseClass)` statement

### Testing NamedTuple Classes

**MANDATORY**: When testing a NamedTuple class, the first test must verify the NamedTuple structure using the `is_namedtuple()` helper function.

The test must:
1. Be named `test_class` (not `test_inheritance`)
2. Assign the class itself to the `tested` variable (not an instance)
3. Define a `fields` dictionary with field names and their types
4. Use the `is_namedtuple()` helper function to verify the structure

**Setup - Add helper to conftest.py**:

Add this function to your `tests/conftest.py` file (create if it doesn't exist). This makes the helper available to all test files automatically:

```python
# tests/conftest.py
from typing import get_type_hints


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
```

**Example usage in tests**:
```python
# Source: models/validation_result.py
from typing import NamedTuple

class ValidationResult(NamedTuple):
    has_errors: bool
    errors: list[str]

# Test file: tests/models/test_validation_result.py
from validation_result import ValidationResult

# Note: is_namedtuple is automatically available from conftest.py

def test_class():
    """Verify ValidationResult is a NamedTuple with correct fields."""
    tested = ValidationResult
    fields = {"has_errors": bool, "errors": list[str]}
    assert is_namedtuple(tested, fields)
```

**Why use `is_namedtuple()` instead of `issubclass()`:**
- Verifies it's a tuple subclass
- Checks the `_fields` attribute exists and is correct
- Validates all expected fields are present
- Ensures field types match expectations using `get_type_hints()`
- Catches any changes to the NamedTuple structure

For a complete NamedTuple testing example, see `examples/namedtuple-test-file.py`.

### Testing Dataclass Classes

**MANDATORY**: When testing a dataclass, the first test must verify the dataclass structure using the `is_dataclass()` helper function.

The test must:
1. Be named `test_class` (not `test_inheritance`)
2. Assign the class itself to the `tested` variable (not an instance)
3. Define a `fields` dictionary with field names and their type strings
4. Use the `is_dataclass()` helper function to verify the structure

**Setup - Add helper to conftest.py**:

Add this function to your `tests/conftest.py` file alongside `is_namedtuple()`:

```python
# tests/conftest.py
from dataclasses import fields as dataclass_fields, is_dataclass as dataclass_is_dataclass


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

```

**Example usage in tests**:
```python
# Source: models/transcript_segment.py
from dataclasses import dataclass

@dataclass
class TranscriptSegment:
    speaker: str
    text: str
    chunk: int
    start: float
    end: float

# Test file: tests/models/test_transcript_segment.py
from transcript_segment import TranscriptSegment

# Note: is_dataclass is automatically available from conftest.py

def test_class():
    """Verify TranscriptSegment is a dataclass with correct fields."""
    tested = TranscriptSegment
    fields = {
        "speaker": "str",
        "text": "str",
        "chunk": "int",
        "start": "float",
        "end": "float",
    }
    assert is_dataclass(tested, fields)
```

**Why use `is_dataclass()` helper:**
- Verifies the class is decorated with `@dataclass`
- Checks all expected fields are present
- Validates field types match expectations
- Catches any changes to the dataclass structure
- More comprehensive than checking `__dataclass_fields__` manually

For a complete dataclass testing example, see `examples/dataclass-test-file.py`.

### One Test Per Method Minimum

Every method must have at least one test. If a method requires multiple test scenarios, prefer parametrization (see below) or create multiple test functions with case suffixes.

### Exclude `__main__` Blocks from Tests

**IMPORTANT**: Do NOT write tests for `if __name__ == "__main__":` blocks.

These blocks are:
1. Excluded from coverage by default (configured in `pyproject.toml` via `exclude_lines`)
2. Entry points that simply call other methods which should already be tested
3. Difficult to test properly without hacky approaches like `exec(compile(...))`

**FORBIDDEN**:
```python
class TestMainBlock:
    """Tests for the __main__ block execution."""

    def test_main_runs(self) -> None:
        # FORBIDDEN: Don't test __main__ blocks
        exec(compile('if __name__ == "__main__": ...', "<string>", "exec"), ...)
```

**Why this matters**:
- The `__main__` block typically just calls `ClassName.run()` which should already have tests
- Testing it requires hacky approaches that are fragile and hard to maintain
- Coverage tools are configured to exclude these lines, so testing them adds no value
- The effort is better spent on testing the actual logic in the methods being called

## Mock Usage

### Use `side_effect` for Return Values

**MANDATORY**: When configuring mock return values, use `side_effect` instead of `return_value`. This is a strict requirement and must never be violated. For call chains, only the final call in the chain must use `side_effect` (for example: `mock.return_value.get.return_value.add.side_effect = [...]`).

**Correct**:
```python
@patch('module.api_client')
def test_fetch_data(mock_client):
    mock_client.return_value.get.side_effect = [{"status": "success"}]
```

**Incorrect - FORBIDDEN**:
```python
@patch('module.api_client')
def test_fetch_data(mock_client):
    mock_client.return_value.get.return_value = {"status": "success"}  # NEVER use return_value for the final call
```

**For complex return objects** (like HTTP responses), use `SimpleNamespace` instead of `MagicMock`:

**CRITICAL**: When a mock returns an object with attributes or methods, use `SimpleNamespace` NOT `MagicMock`. This avoids the need to verify `mock_calls` on the returned object.

**CORRECT - Use SimpleNamespace for response objects**:
```python
from types import SimpleNamespace

@patch('module.requests.post')
def test_api_call(mock_post):
    # Use SimpleNamespace - no need to verify mock_calls on response
    mock_post.side_effect = [
        SimpleNamespace(
            status_code=200,
            text="response text",
            json=lambda: {"data": "value"}  # Lambda for methods that return values
        )
    ]

    tested = ApiClient()
    result = tested.call_api()

    expected = {"data": "value"}
    assert result == expected

    # Only need to verify mock_post, NOT the response object
    exp_post_calls = [call("https://api.example.com")]
    assert mock_post.mock_calls == exp_post_calls
```

**FORBIDDEN - Using MagicMock for response objects**:
```python
@patch('module.requests.post')
def test_api_call(mock_post):
    # FORBIDDEN: Using MagicMock for response requires mock_calls verification
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = [{"data": "value"}]
    mock_post.side_effect = [mock_response]

    result = tested.call_api()

    # If you use MagicMock, you MUST verify its mock_calls - easy to forget!
    exp_response_calls = [call.json()]
    assert mock_response.mock_calls == exp_response_calls  # Often forgotten!
```

**Why SimpleNamespace is preferred**:
- No `mock_calls` verification needed - it's just a data container
- Simpler test code with less boilerplate
- No risk of forgetting to verify mock interactions
- Lambdas work for methods: `json=lambda: {...}`, `read=lambda: b"data"`

### Use `capsys` Instead of Mocking `print`

**CRITICAL**: When testing code that uses `print()`, use pytest's built-in `capsys` fixture instead of mocking `print`.

**FORBIDDEN - Mocking print**:
```python
@patch("module.print")
def test_output(mock_print):
    tested = MyClass()
    tested.display_message()

    # Complex extraction of print calls - error prone!
    print_calls = [c[0][0] for c in mock_print.call_args_list if c[0]]
    assert "Expected message" in print_calls

    # Must also verify mock_calls - easy to forget!
    exp_print_calls = [call("Expected message")]
    assert mock_print.mock_calls == exp_print_calls
```

**CORRECT - Using capsys fixture**:
```python
def test_output(self, capsys) -> None:
    tested = MyClass()
    tested.display_message()

    captured = capsys.readouterr()

    assert "Expected message" in captured.out
    # Or for exact match:
    expected = "Expected message\n"
    assert captured.out == expected
```

**Why capsys is preferred**:
- Built-in pytest fixture - no imports or patches needed
- Simpler assertion syntax - just check `captured.out` or `captured.err`
- No mock_calls verification required
- Works with any code that writes to stdout/stderr
- Captures actual output, not mock interactions
- Less boilerplate and setup code

**capsys usage patterns**:
```python
def test_stdout(self, capsys) -> None:
    print("Hello")
    captured = capsys.readouterr()
    assert captured.out == "Hello\n"

def test_stderr(self, capsys) -> None:
    import sys
    print("Error", file=sys.stderr)
    captured = capsys.readouterr()
    assert captured.err == "Error\n"

def test_multiple_prints(self, capsys) -> None:
    print("Line 1")
    print("Line 2")
    captured = capsys.readouterr()
    assert "Line 1" in captured.out
    assert "Line 2" in captured.out
```

### Verify All Mocks with `mock_calls`

**MANDATORY**: After each test, ALL mock objects must be verified through the `mock_calls` property. This includes:
- The main patched mock (e.g., `mock_db`)
- Any `MagicMock()` objects you create (e.g., `mock_response`)
- Any `.return_value` mock instances (e.g., `mock_db_class.return_value`)

**CRITICAL - Parametrized Tests Are NOT Exempt**:
Parametrized tests MUST verify all mocks just like regular tests. If a test has mock parameters, each mock MUST have a corresponding `assert mock.mock_calls == exp_*` statement.

**FORBIDDEN - Parametrized test without mock verification**:
```python
@pytest.mark.parametrize("input_val,expected", [...])
@patch("module.api")
def test_fetch(mock_api, input_val, expected):
    mock_api.get.side_effect = [{"data": input_val}]
    tested = Fetcher()
    result = tested.fetch(input_val)
    assert result == expected
    # FORBIDDEN: mock_api is NEVER verified with mock_calls!
```

**CORRECT - Parametrized test with mock verification**:
```python
@pytest.mark.parametrize("input_val,expected", [...])
@patch("module.api")
def test_fetch(mock_api, input_val, expected):
    mock_api.get.side_effect = [{"data": input_val}]
    tested = Fetcher()
    result = tested.fetch(input_val)
    expected_result = expected
    assert result == expected_result

    exp_api_calls = [call.get(input_val)]  # MUST verify mock
    assert mock_api.mock_calls == exp_api_calls
```

**When to avoid parametrization with mocks**:
If mock verification differs significantly between test cases, use separate non-parametrized tests instead of trying to parametrize with complex mock verification logic.

**CRITICAL**: Always verify at the **mock object level**, NOT at individual method level:
- **CORRECT**: `assert mock_response.mock_calls == exp_calls` (object level)
- **FORBIDDEN**: `assert mock_response.read.mock_calls == exp_calls` (method level)

**CRITICAL**: Use single assertion with hard-coded values:
- **CORRECT**: `assert mock.mock_calls == exp_calls` (single assertion)
- **FORBIDDEN**: `assert len(mock.mock_calls) == 3` then checking individual items
- **FORBIDDEN**: Using variables in expected values: `call(f"URL: {tested_url}")`
- **CORRECT**: Use hard-coded literals: `call("URL: http://example.com")`

**Correct verification**:

Using `SimpleNamespace`:
```python
@patch('module.requests.get')
def test_fetch_data(mock_get):
    # Create mock response object
    mock_get.side_effect = [SimpleNamespace(status_code=200, json=lambda :{"data": "value"})]

    tested = APIClient()
    result = tested.fetch_data("http://api.example.com/data")

    expected = {"data": "value"}
    assert result == expected

    # CRITICAL: Verify with single assertion and HARD-CODED values
    exp_get_calls = [call("http://api.example.com/data")]
    assert mock_get.mock_calls == exp_get_calls
```

Using embedded mocks:
```python
@patch('module.requests.get')
def test_fetch_data(mock_get):
    # Create mock response object
    mock_response = MagicMock()
    mock_response.json.side_effect = [{"data": "value"}]
    mock_get.side_effect = [mock_response]

    tested = APIClient()
    result = tested.fetch_data("http://api.example.com/data")

    expected = {"data": "value"}
    assert result == expected

    # CRITICAL: Verify with single assertion and HARD-CODED values
    exp_get_calls = [call("http://api.example.com/data")]
    assert mock_get.mock_calls == exp_get_calls

    # CRITICAL: Verify response mock at OBJECT level with hard-coded values
    exp_response_calls = [call.json()]
    assert mock_response.mock_calls == exp_response_calls  # Single assertion!
```

**Common mistakes**:

1. **Forgetting to verify mock objects**:
```python
# WRONG - mock_response is not verified!
@patch('module.requests.get')
def test_fetch_data(mock_get):
    mock_response = MagicMock()
    mock_response.json.side_effect = [{"data": "value"}]
    mock_get.side_effect = [mock_response]

    result = tested.fetch_data("url")

    # FORBIDDEN: Only verifying mock_get, missing mock_response!
    assert mock_get.mock_calls == [call("url")]
```

2. **Verifying at wrong level**:
```python
# WRONG - verifying individual methods instead of object!
@patch('module.urlopen')
def test_fetch(mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.side_effect = [b"data"]
    mock_urlopen.side_effect = [mock_response]

    result = fetch("url")

    # FORBIDDEN: Verifying at method level!
    assert mock_response.read.mock_calls == [call()]  # WRONG LEVEL

    # CORRECT: Verify at object level
    exp_response_calls = [call.read()]
    assert mock_response.mock_calls == exp_response_calls  # Object level!
```

3. **Checking length and using variables**:
```python
# WRONG - checking length then individual calls with variables!
@patch('builtins.print')
def test_process(mock_print):
    tested_url = "http://example.com"
    process(tested_url)

    # FORBIDDEN: Checking length and individual items
    assert len(mock_print.mock_calls) == 2
    assert mock_print.mock_calls[0] == call(f"Processing: {tested_url}")
    assert mock_print.mock_calls[1] == call("Done")

    # CORRECT: Single assertion with hard-coded values
    exp_print_calls = [
        call("Processing: http://example.com"),  # Hard-coded!
        call("Done")
    ]
    assert mock_print.mock_calls == exp_print_calls
```

### Forbidden Mock Assertions

**NEVER USE** these assertion helper methods:
- `mock.assert_called()`
- `mock.assert_called_once()`
- `mock.assert_called_with(...)`
- `mock.assert_called_once_with(...)`
- `mock.assert_not_called()`
- `mock.assert_any_call(...)`
- `mock.assert_has_calls(...)`
- `mock.call_count`
- `mock.call_args`
- `mock.call_args_list`

**NEVER verify at method or attribute level**:
- `mock_response.read.mock_calls` (FORBIDDEN - method level)
- `mock_response.read.return_value.decode.mock_calls` (FORBIDDEN - nested attribute level)

**NEVER check length or index mock_calls**:
- `assert len(mock.mock_calls) == 3` (FORBIDDEN - checking length)
- `assert mock.mock_calls[0] == call(...)` (FORBIDDEN - indexing)
- `assert call(...) == mock.mock_calls[1]` (FORBIDDEN - indexing with reversed order)

**NEVER use variables in expected values**:
- `call(f"URL: {tested_url}")` (FORBIDDEN - using variable)
- `call(tested_value)` (FORBIDDEN - using variable)
- Always use hard-coded literals: `call("URL: http://example.com")` (CORRECT)

**ALWAYS use**:
- `mock.mock_calls` property at the **object level** for verification
- Pattern: `assert mock_object.mock_calls == exp_calls` (single assertion)
- Hard-coded literal values in all expected calls

For comprehensive mock patterns and examples, see `references/mock-patterns.md`.

## Multiple Scenarios

When testing multiple scenarios for the same method, use these approaches in order of preference:

### 1. Parametrize (Preferred)

Use `@pytest.mark.parametrize` with `pytest.param` to define each scenario:

```python
@pytest.mark.parametrize("input_value,expected", [
    pytest.param(5, 10, id="positive"),
    pytest.param(-5, 0, id="negative"),
    pytest.param(0, 5, id="zero"),
])
def test_add_five(input_value, expected):
    tested = Calculator()
    result = tested.add_five(input_value)
    assert result == expected
```

Benefits:
- Compact representation
- Clear scenario identification
- Easy to add new cases
- Better test output with `id` parameter

### 2. Loop Within Test

For simple scenarios with similar setup:

```python
def test_validate_email():
    tested = Validator()

    test_cases = [
        ("user@example.com", True),
        ("invalid.email", False),
        ("@example.com", False),
    ]

    for email, expected in test_cases:
        result = tested.validate_email(email)
        assert result == expected
```

### 3. Multiple Test Functions

For complex scenarios requiring different setup or mocks:

```python
def test_process_data__valid_input():
    # Complex setup for valid input
    pass

def test_process_data__invalid_format():
    # Different setup for invalid format
    pass

def test_process_data__network_error():
    # Mock network error scenario
    pass
```

For detailed parametrization patterns, see `references/parametrize-examples.md`.

## Mock Scenarios

### When to Use Mocks

Use mocks for:

1. **External systems**: Database queries, HTTP requests, file I/O
2. **Non-deterministic behavior**: `datetime.now()`, `random.random()`, `uuid.uuid4()`
3. **Complex setup**: When creating the real scenario would be overly complicated
4. **Internal class dependencies**: When a method depends on other methods of the same class, mock those methods to avoid test duplication

**Example with internal method dependency:**
```python
class DataProcessor:
    def validate(self, data):
        # Complex validation logic tested separately
        ...

    def process(self, data):
        if not self.validate(data):
            raise ValueError("Invalid data")
        # Processing logic
        return transformed_data

# GOOD - Mock validate() to focus on process() logic only
@patch.object(DataProcessor, "validate")
def test_process(mock_validate):
    mock_validate.side_effect = [True]

    tested = DataProcessor()
    result = tested.process({"key": "value"})

    expected = {"key": "transformed"}
    assert result == expected

    exp_validate_calls = [call({"key": "value"})]
    assert mock_validate.mock_calls == exp_validate_calls

# BAD - Testing validate() behavior again inside process() tests
def test_process__duplicates_validation_tests():
    tested = DataProcessor()
    # This test ends up re-testing validate() logic
    result = tested.process({"key": "value"})
    ...
```

**Example with datetime**:
```python
@patch('module.datetime')
def test_create_timestamp(mock_datetime):
    mock_datetime.now.side_effect = [datetime(2024, 1, 1, 12, 0, 0)]

    tested = TimestampGenerator()
    result = tested.create_timestamp()

    expected = "2024-01-01 12:00:00"
    assert result == expected

    exp_calls = [call.now()]
    assert mock_datetime.mock_calls == exp_calls
```

### When NOT to Use Mocks

**Prefer real instances over mocks for simple data objects.** Mocks should isolate code from external dependencies, not replace simple data structures.

**Use real instances when:**

1. **Simple data containers**: NamedTuples, dataclasses, TypedDicts, or plain classes that only hold data
2. **No side effects**: Objects that don't perform I/O, network calls, or modify external state
3. **Trivial construction**: When creating a real instance requires no more effort than configuring a mock and checking its calls

**IMPORTANT for NamedTuples and Dataclasses**:
- NEVER mock NamedTuple classes or instances. NamedTuples are immutable data containers with no side effects - always use real instances created with keyword arguments.
- NEVER mock dataclass classes or instances. Dataclasses are data containers - always use real instances created with keyword arguments. Only mock external dependencies or internal methods when testing other methods on the same class.

**Example - Prefer real instance:**
```python
from hook_information import HookInformation

# GOOD - HookInformation is a simple NamedTuple, use real instance
def test_session_directory():
    hook_info = HookInformation(
        session_id="test123",
        exit_reason="user_exit",
        transcript_path=Path("/path/to/transcript.jsonl"),
        workspace_dir=Path("/home/user/project"),
        working_directory=Path("/home/user/project/subdir"),
    )

    result = UserInputsLogger.session_directory(hook_info)

    expected = Path("/home/user/project/.artifacts/user_inputs")
    assert result == expected
```

**Example - Avoid unnecessary mocks:**
```python
# BAD - Using Mock for a simple data object adds indirection without benefit
def test_session_directory():
    mock_hook_info = Mock()
    mock_hook_info.workspace_dir = Path("/home/user/project")

    result = UserInputsLogger.session_directory(mock_hook_info)
    # ...
```

**Why prefer real instances:**
- **Type safety**: Real objects catch attribute typos and type errors at test time
- **Better documentation**: Tests using real objects show the actual interface requirements
- **Detect breaking changes**: Mocks can hide breaking changes (e.g., renamed attributes still "work" on mocks)
- **Simpler tests**: No need to configure mock attributes when a real instance is just as easy to create

**Rule of thumb**: If the object is a data container with no behavior to mock (no methods that perform I/O, no side effects), use a real instance.

## Running Tests

Tests must pass these commands without errors:

### Run All Tests
```bash
uv run pytest tests/
```

### Run with Coverage
```bash
uv run pytest -v tests/ --cov=.
```

Coverage must reach 100% for all source files.

### Run Specific Test File
```bash
uv run pytest tests/utils/test_parser.py -v
```

## Complete Examples

### Regular Classes

See `examples/complete-test-file.py` for a full working example that demonstrates:
- Proper test file structure with inheritance testing
- Naming conventions for all scenarios
- Mock usage with `side_effect` and `mock_calls`
- Parametrization for multiple scenarios
- 100% coverage of source file

### NamedTuple Classes

See `examples/namedtuple-test-file.py` for a full working example that demonstrates:
- NamedTuple structure verification with `is_namedtuple()` helper
- Testing NamedTuple methods and immutability
- Creating test instances with keyword arguments
- Parametrization for NamedTuple scenarios
- 100% coverage of NamedTuple source file

### Dataclass Classes

See `examples/dataclass-test-file.py` for a full working example that demonstrates:
- Dataclass structure verification with `is_dataclass()` helper
- Testing dataclass methods and mutability
- Testing default values and default_factory fields
- Mocking internal methods to avoid test duplication
- Creating test instances with keyword arguments
- Parametrization for dataclass scenarios
- 100% coverage of dataclass source file

## Additional Resources

### Reference Files

For detailed guidance on specific topics:
- **`references/naming-conventions.md`** - Comprehensive naming examples for all scenarios
- **`references/mock-patterns.md`** - Mock patterns with `side_effect` and `mock_calls` verification
- **`references/parametrize-examples.md`** - Advanced parametrization techniques

### Example Files

Working examples demonstrating guidelines:
- **`examples/conftest.py`** - Example conftest.py with `is_namedtuple()` and `is_dataclass()` helper functions
- **`examples/complete-test-file.py`** - Complete test file with source code showing all patterns for regular classes
- **`examples/namedtuple-test-file.py`** - Complete test file demonstrating NamedTuple testing patterns
- **`examples/dataclass-test-file.py`** - Complete test file demonstrating dataclass testing patterns

## Quick Reference

**Test structure**:
- For classes with inheritance: First test must be `test_inheritance()` verifying `issubclass(DerivedClass, BaseClass)`
- For NamedTuple classes: First test must be `test_class()` using `is_namedtuple(tested, fields)` helper (add helper to `tests/conftest.py`)
- For dataclass classes: First test must be `test_class()` using `is_dataclass(tested, fields)` helper with string type values (add helper to `tests/conftest.py`)

**Test naming**: `test_method_name` or `test_method_name__case`

**Variable naming** (MANDATORY - use these exact names):
- `tested` - the class or instance being tested (assign FIRST, call methods on it)
- `result` - the return value from the method under test (NEVER use `output`, `ret`, `actual`)
- `expected` - the expected value for single assertions (NEVER inline in assert)
- `exp_*` - expected values for multiple assertions (NEVER use `expected_*` prefix)

**Assertions**:
- Use `is` for singletons: `assert result is True`, `assert result is None`
- Use `==` for everything else: `assert result == "value"`

**Mock setup**: Always use `side_effect` - `mock.method.side_effect = [return_value]`

**Mock return objects**: Use `SimpleNamespace` NOT `MagicMock` for return objects (like HTTP responses). Use lambdas for methods: `SimpleNamespace(status_code=200, json=lambda: {"data": "value"})`

**Capturing print output**: Use pytest's `capsys` fixture - NEVER mock `print`. Pattern: `captured = capsys.readouterr()` then `assert "message" in captured.out`

**Mock scope**: Mock external systems, I/O, non-deterministic behavior, and internal class method dependencies. Use real instances for simple data objects (NamedTuples, dataclasses). For dataclasses, you may mock internal methods when testing other methods to avoid duplication.

**Mock verification**: Verify ALL mock objects at object level with single assertion and hard-coded values
- Main patched mocks must be verified
- Created MagicMock() objects must be verified
- .return_value instances must be verified
- CRITICAL: Parametrized tests MUST verify mocks too - they are NOT exempt!
- Pattern: `assert mock_obj.mock_calls == exp_calls` (single assertion)
- NEVER verify at method level: `assert mock_obj.method.mock_calls == exp_calls`
- NEVER check length: `assert len(mock.mock_calls) == 3`
- NEVER index: `assert mock.mock_calls[0] == call(...)`
- NEVER use variables in expected values: `call(f"URL: {url_var}")`
- ALWAYS use hard-coded literals: `call("URL: http://example.com")`

**Parametrize**: `@pytest.mark.parametrize("arg,expected", [pytest.param(..., id="case")])`

**Coverage**: `uv run pytest tests/ --cov=. -v` must show 100%

**Excluded from tests**: `if __name__ == "__main__":` blocks - do NOT write tests for these (excluded from coverage)

**Critical Rules**:
1. ALWAYS start with `test_inheritance()` as the first test when testing a class that inherits from a base class, OR `test_class()` using `is_namedtuple()` helper for NamedTuple classes, OR `test_class()` using `is_dataclass()` helper for dataclass classes
2. ALWAYS assign the class or instance to a `tested` variable FIRST, then call methods on `tested` - NEVER call methods directly on the class name
3. ALWAYS store return values in a variable named `result` - NEVER use `output`, `ret`, `actual`, `response`, etc.
4. ALWAYS store expected values in a variable named `expected` - NEVER inline expected values in assertions
5. ALWAYS use `exp_*` prefix for multiple expected values (e.g., `exp_calls`) - NEVER use `expected_*` prefix
6. NEVER use `return_value` to set what a mock returns - always use `side_effect`
7. ALWAYS verify ALL mock objects with `mock_calls` in EVERY test - missing verification is forbidden
8. Parametrized tests are NOT exempt - every mock MUST be verified with `mock_calls` even in parametrized tests
9. ALWAYS verify at OBJECT level (`mock.mock_calls`), NEVER at method level (`mock.method.mock_calls`)
10. ALWAYS use single assertion format: `assert mock.mock_calls == exp_calls`
11. NEVER check length or index: `assert len(mock.mock_calls) == 3` or `mock.mock_calls[0]`
12. ALWAYS use hard-coded literal values in expected calls - NEVER use variables
13. NEVER use assert helpers like `assert_called_with()` - only use `mock_calls`
14. ALWAYS use `is` for True/False/None comparisons - never use `==` for singletons
15. PREFER real instances over mocks for simple data objects (NamedTuples, dataclasses, TypedDicts)
16. USE `SimpleNamespace` NOT `MagicMock` for return objects (HTTP responses, etc.) - avoids forgetting mock_calls verification
17. USE pytest's `capsys` fixture to capture print output - NEVER mock `print`
18. NEVER write tests for `if __name__ == "__main__":` blocks - they are excluded from coverage

Apply these guidelines consistently to create maintainable, comprehensive test suites that ensure code reliability and prevent regressions.
