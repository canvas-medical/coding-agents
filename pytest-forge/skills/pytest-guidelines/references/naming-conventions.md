# Naming Conventions - Detailed Examples

This reference provides comprehensive examples of naming conventions for pytest test files following the strict guidelines.

## Critical Rule: Hard-Coded Values in Expected Results

**MANDATORY**: All expected values must be hard-coded literals, never variables.

This applies to:
- Expected return values: `expected = "http://example.com"` (not `expected = tested_url`)
- Expected mock calls: `call("http://example.com")` (not `call(f"{url_var}")`)
- Expected outputs: `exp_result = [1, 2, 3]` (not `exp_result = input_list.copy()`)

**Rationale**:
- Tests must be self-contained and readable
- Expected values should be obvious from reading the test
- Prevents accidental coupling between test inputs and expectations
- Makes test failures easier to understand

## Test File Naming

### Directory Structure Mirroring

Always mirror the source directory structure in `tests/`:

```
Source Structure:
src/
├── utils/
│   ├── parser.py
│   └── validator.py
├── models/
│   ├── user.py
│   └── product.py
└── services/
    └── api_client.py

Test Structure:
tests/
├── utils/
│   ├── test_parser.py
│   └── test_validator.py
├── models/
│   ├── test_user.py
│   └── test_product.py
└── services/
    └── test_api_client.py
```

### File Name Format

- Prefix with `test_`
- Match the source file name exactly (except for test_ prefix)
- Use lowercase with underscores (snake_case)

**Examples**:
```
parser.py → test_parser.py
APIClient.py → test_APIClient.py (preserve capitalization)
data_processor.py → test_data_processor.py
```

## Test Function Naming

### Basic Pattern: One Test Per Method

Format: `test_<method_name>`

**Source code**:
```python
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
```

**Test code**:
```python
def test_add():
    tested = Calculator()
    result = tested.add(2, 3)
    expected = 5
    assert result == expected

def test_subtract():
    tested = Calculator()
    result = tested.subtract(5, 3)
    expected = 2
    assert result == expected
```

### Private Methods: Include Underscore Prefix

Format: `test_<_method_name>` (include the leading underscore)

**Source code**:
```python
class Validator:
    def _check_format(self, value):
        return len(value) > 0

    def __internal_validate(self, value):
        return value is not None
```

**Test code**:
```python
def test__check_format():
    tested = Validator()
    result = tested._check_format("test")
    expected = True
    assert result is expected  # Use 'is' for boolean singletons

def test___internal_validate():
    tested = Validator()
    result = tested.__internal_validate("value")
    expected = True
    assert result is expected  # Use 'is' for boolean singletons
```

Note: Double underscores in method names become double underscores in test names.

### Multiple Test Cases: Add Case Description

Format: `test_<method_name>__<case_description>`

The double underscore `__` separates the method name from the case description.

**Example 1: Different input types**:
```python
def test_format_name__first_last():
    tested = Formatter()
    result = tested.format_name("john", "doe")
    expected = "John Doe"
    assert result == expected

def test_format_name__single_name():
    tested = Formatter()
    result = tested.format_name("john", "")
    expected = "John"
    assert result == expected

def test_format_name__empty_input():
    tested = Formatter()
    result = tested.format_name("", "")
    expected = ""
    assert result == expected
```

**Example 2: Success and failure cases**:
```python
def test_validate_email__valid_format():
    tested = Validator()
    result = tested.validate_email("user@example.com")
    expected = True
    assert result is expected  # Use 'is' for boolean singletons

def test_validate_email__invalid_format():
    tested = Validator()
    result = tested.validate_email("invalid.email")
    expected = False
    assert result is expected  # Use 'is' for boolean singletons

def test_validate_email__missing_domain():
    tested = Validator()
    result = tested.validate_email("user@")
    expected = False
    assert result is expected  # Use 'is' for boolean singletons
```

**Example 3: Exception scenarios**:
```python
def test_parse_json__valid_json():
    tested = Parser()
    result = tested.parse_json('{"key": "value"}')
    expected = {"key": "value"}
    assert result == expected

def test_parse_json__invalid_json():
    tested = Parser()
    with pytest.raises(ValueError):
        tested.parse_json('invalid json')

def test_parse_json__empty_string():
    tested = Parser()
    with pytest.raises(ValueError):
        tested.parse_json('')
```

### Case Description Guidelines

Case descriptions should be:
- Lowercase with underscores (snake_case)
- Descriptive of the scenario
- Concise (2-4 words typically)

**Good case descriptions**:
- `__valid_input`
- `__empty_list`
- `__network_error`
- `__missing_parameter`
- `__negative_value`

**Avoid**:
- `__test_1` (not descriptive)
- `__thisTestChecksWhenTheInputIsEmpty` (too verbose, wrong case)
- `__ValidInput` (wrong case - should be lowercase)

## Variable Naming

### Standard Variable Names

Use these consistently across all tests:

#### `tested`
The object, instance, or module being tested.

```python
def test_calculate():
    tested = Calculator()  # Instance being tested
    result = tested.calculate(5)
    expected = 10
    assert result == expected

def test_format_string():
    tested = StringFormatter()  # Object being tested
    result = tested.format("hello")
    expected = "HELLO"
    assert result == expected
```

#### `result`
The value returned from the method under test.

```python
def test_get_user():
    tested = UserService()
    result = tested.get_user(123)  # Return value stored as 'result'
    expected = {"id": 123, "name": "John"}
    assert result == expected
```

#### `expected`
The expected value for single assertions.

```python
def test_add():
    tested = Calculator()
    result = tested.add(2, 3)
    expected = 5  # Single expected value
    assert result == expected
```

#### `exp_*`
Multiple expected values, prefixed with `exp_`.

**Example with multiple expectations**:
```python
@patch('module.api')
def test_process_data(mock_api):
    mock_api.fetch.side_effect = [{"data": "value"}]

    tested = DataProcessor()
    result = tested.process_data()

    exp_result = {"data": "value"}  # Expected result
    exp_calls = [call.fetch()]       # Expected mock calls

    assert result == exp_result
    assert mock_api.mock_calls == exp_calls
```

**Common `exp_*` variable names**:
- `exp_calls` - Expected mock calls
- `exp_output` - Expected output value
- `exp_status` - Expected status code
- `exp_message` - Expected error message
- `exp_count` - Expected count or length
- `exp_items` - Expected list items

### Variable Naming Examples

**Example 1: Simple test with standard names**:
```python
def test_multiply():
    tested = Calculator()
    result = tested.multiply(4, 5)
    expected = 20
    assert result == expected
```

**Example 2: Test with multiple expectations**:
```python
@patch('module.database')
def test_save_record(mock_db):
    mock_db.insert.side_effect = [42]

    tested = RecordService()
    result = tested.save_record({"name": "test"})

    exp_id = 42
    exp_calls = [call.insert({"name": "test"})]

    assert result == exp_id
    assert mock_db.mock_calls == exp_calls
```

**Example 3: Test with complex expectations**:
```python
@patch('module.datetime')
@patch('module.api_client')
def test_create_report(mock_api, mock_datetime):
    mock_datetime.now.side_effect = [datetime(2024, 1, 1)]
    mock_api.fetch_data.side_effect = [[1, 2, 3]]

    tested = ReportGenerator()
    result = tested.create_report()

    exp_timestamp = "2024-01-01"
    exp_data = [1, 2, 3]
    exp_api_calls = [call.fetch_data()]
    exp_datetime_calls = [call.now()]

    assert result["timestamp"] == exp_timestamp
    assert result["data"] == exp_data
    assert mock_api.mock_calls == exp_api_calls
    assert mock_datetime.mock_calls == exp_datetime_calls
```

## Method Ordering

Tests must appear in the same order as methods in the source file.

**Source file**:
```python
class UserService:
    def __init__(self):
        pass

    def create_user(self, name):
        return self._validate(name)

    def update_user(self, id, name):
        return self._validate(name)

    def delete_user(self, id):
        return self._remove(id)

    def _validate(self, name):
        return len(name) > 0

    def _remove(self, id):
        return True
```

**Test file** (correct order):
```python
def test_create_user():
    pass

def test_update_user():
    pass

def test_delete_user():
    pass

def test__validate():
    pass

def test__remove():
    pass
```

**Test file** (incorrect order - DO NOT DO THIS):
```python
def test_delete_user():  # Wrong: out of order
    pass

def test_create_user():  # Wrong: out of order
    pass

def test__validate():    # Wrong: should come after all public methods
    pass
```

### Ordering Rules

1. Tests follow the order of method definitions in source file
2. Constructor (`__init__`) typically doesn't need a test unless it has logic
3. Public methods first, then private methods (in order of appearance)
4. If source has multiple test cases (`test_method__case1`, `test_method__case2`), keep them together

## Class-Based Test Organization

When testing classes with many methods, maintain clear organization:

**Source**:
```python
class DataProcessor:
    def load_data(self, path):
        pass

    def process_data(self, data):
        pass

    def save_data(self, data, path):
        pass

    def _validate_path(self, path):
        pass

    def _validate_data(self, data):
        pass
```

**Tests**:
```python
# Load data tests
def test_load_data__valid_path():
    pass

def test_load_data__invalid_path():
    pass

# Process data tests
def test_process_data__valid_data():
    pass

def test_process_data__empty_data():
    pass

# Save data tests
def test_save_data():
    pass

# Private method tests
def test__validate_path():
    pass

def test__validate_data():
    pass
```

Use comments to separate logical groups while maintaining source order.

## Module-Level Function Tests

For modules with functions (not classes):

**Source `utils.py`**:
```python
def format_name(first, last):
    pass

def validate_email(email):
    pass

def parse_date(date_string):
    pass
```

**Tests `test_utils.py`**:
```python
def test_format_name():
    result = format_name("john", "doe")
    expected = "John Doe"
    assert result == expected

def test_validate_email():
    result = validate_email("user@example.com")
    expected = True
    assert result is expected  # Use 'is' for boolean singletons

def test_parse_date():
    result = parse_date("2024-01-01")
    expected = datetime(2024, 1, 1)
    assert result == expected
```

No `tested` variable needed for module functions—call directly.

## Property and Staticmethod Tests

**Source**:
```python
class User:
    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @staticmethod
    def validate_name(name):
        return len(name) > 0
```

**Tests**:
```python
def test_full_name():
    tested = User("John", "Doe")
    result = tested.full_name  # Property access
    expected = "John Doe"
    assert result == expected

def test_validate_name():
    result = User.validate_name("John")  # Static method call
    expected = True
    assert result is expected  # Use 'is' for boolean singletons
```

## Assertion Style

### Use `is` for Singleton Comparisons

**Rule**: Always use `is` (not `==`) when comparing to `True`, `False`, or `None`.

**Rationale**:
- These are singletons in Python
- `is` checks identity, which is correct for singletons
- Recommended by PEP 8
- More semantically correct

**Correct Examples**:
```python
def test_is_valid():
    tested = Validator()
    result = tested.is_valid("data")
    expected = True
    assert result is expected  # Correct: use 'is' for True

def test_is_empty():
    tested = Checker()
    result = tested.is_empty([])
    expected = False
    assert result is expected  # Correct: use 'is' for False

def test_get_optional():
    tested = Service()
    result = tested.get_optional("key")
    expected = None
    assert result is expected  # Correct: use 'is' for None
```

**Incorrect Examples** (DO NOT USE):
```python
def test_is_valid():
    tested = Validator()
    result = tested.is_valid("data")
    expected = True
    assert result == expected  # WRONG: should use 'is' not '=='
```

### Use `==` for All Other Comparisons

For strings, numbers, lists, dicts, and objects, use `==`:

```python
def test_format_name():
    tested = Formatter()
    result = tested.format_name("john")
    expected = "John"
    assert result == expected  # Correct: use '==' for strings

def test_calculate():
    tested = Calculator()
    result = tested.add(2, 3)
    expected = 5
    assert result == expected  # Correct: use '==' for numbers

def test_get_items():
    tested = DataService()
    result = tested.get_items()
    expected = [1, 2, 3]
    assert result == expected  # Correct: use '==' for lists
```

## Summary

**File naming**: `test_<source_file>.py` in mirrored directory structure

**Function naming**: `test_<method>` or `test_<method>__<case>`

**Variable naming**: `tested`, `result`, `expected`, `exp_*`

**Assertion style**: Use `is` for True/False/None, `==` for everything else

**Ordering**: Tests match source file method order

**Consistency**: Use these conventions universally across all test files

Following these naming conventions creates predictable, maintainable test suites that are easy to navigate and understand.
