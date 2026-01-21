# Parametrize Examples - Advanced Techniques

This reference provides comprehensive guidance on using `@pytest.mark.parametrize` for testing multiple scenarios efficiently.

## Why Parametrize?

Parametrization is the preferred approach for testing multiple scenarios of the same method because it:

- **Reduces duplication**: Write test logic once, apply to multiple cases
- **Improves maintainability**: Add new test cases by adding parameters, not duplicating code
- **Better test output**: Each parameter set shows as a separate test in output
- **Clear identification**: Use `id` parameter to name each scenario

## Basic Parametrization

### Simple Parameters

**Pattern**: Test a function with multiple input/output pairs.

```python
import pytest

@pytest.mark.parametrize("input_value,expected", [
    pytest.param(5, 10, id="positive"),
    pytest.param(0, 5, id="zero"),
    pytest.param(-5, 0, id="negative"),
])
def test_add_five(input_value, expected):
    tested = Calculator()
    result = tested.add_five(input_value)
    assert result == expected
```

**Test output**:
```
test_calculator.py::test_add_five[positive] PASSED
test_calculator.py::test_add_five[zero] PASSED
test_calculator.py::test_add_five[negative] PASSED
```

### Multiple Parameters

**Pattern**: Test with multiple independent parameters.

```python
@pytest.mark.parametrize("first_name,last_name,expected", [
    pytest.param("John", "Doe", "John Doe", id="full_name"),
    pytest.param("Jane", "", "Jane", id="first_only"),
    pytest.param("", "Smith", "Smith", id="last_only"),
    pytest.param("", "", "", id="empty"),
])
def test_format_name(first_name, last_name, expected):
    tested = NameFormatter()
    result = tested.format_name(first_name, last_name)
    assert result == expected
```

## Using pytest.param

### Why Use pytest.param

Always use `pytest.param()` instead of plain tuples for clearer test identification.

**Good** (with pytest.param and id):
```python
@pytest.mark.parametrize("value,expected", [
    pytest.param(10, True, id="valid"),
    pytest.param(-1, False, id="negative"),
])
def test_validate(value, expected):
    pass
```

**Acceptable** (without pytest.param, pytest generates IDs):
```python
@pytest.mark.parametrize("value,expected", [
    (10, True),
    (-1, False),
])
def test_validate(value, expected):
    pass
```

**Output comparison**:
```
# With id:
test_file.py::test_validate[valid] PASSED
test_file.py::test_validate[negative] PASSED

# Without id:
test_file.py::test_validate[10-True] PASSED
test_file.py::test_validate[-1-False] PASSED
```

The `id` parameter makes test output more readable.

### ID Naming Conventions

Use descriptive, lowercase IDs with underscores:

**Good IDs**:
- `"valid_input"`
- `"empty_list"`
- `"network_error"`
- `"missing_key"`
- `"negative_value"`

**Avoid**:
- `"test1"` - Not descriptive
- `"ValidInput"` - Should be lowercase
- `"test-valid-input"` - Use underscores, not hyphens

## Complex Parameters

### Testing Exceptions

**Pattern**: Parametrize tests that expect exceptions.

```python
@pytest.mark.parametrize("input_value,exception,message", [
    pytest.param("", ValueError, "Empty input", id="empty"),
    pytest.param("invalid", ValueError, "Invalid format", id="invalid_format"),
    pytest.param(None, TypeError, "None not allowed", id="none_value"),
])
def test_parse_errors(input_value, exception, message):
    tested = Parser()
    with pytest.raises(exception, match=message):
        tested.parse(input_value)
```

### Dictionary Parameters

**Pattern**: Use dictionaries for complex test data.

```python
@pytest.mark.parametrize("user_data,expected_id", [
    pytest.param(
        {"name": "Alice", "email": "alice@example.com"},
        123,
        id="valid_user"
    ),
    pytest.param(
        {"name": "Bob", "email": "bob@example.com", "age": 30},
        124,
        id="user_with_age"
    ),
])
def test_create_user(user_data, expected_id):
    tested = UserService()
    result = tested.create_user(user_data)
    assert result == expected_id
```

### List Parameters

**Pattern**: Test functions that process lists.

```python
@pytest.mark.parametrize("items,expected", [
    pytest.param([1, 2, 3], 6, id="positive_numbers"),
    pytest.param([−1, -2, -3], -6, id="negative_numbers"),
    pytest.param([], 0, id="empty_list"),
    pytest.param([0, 0, 0], 0, id="all_zeros"),
])
def test_sum_items(items, expected):
    tested = Calculator()
    result = tested.sum_items(items)
    assert result == expected
```

## Parametrizing with Mocks

### Mocking in Parametrized Tests

**Pattern**: Use mocks within parametrized tests.

```python
from unittest.mock import patch, call

@pytest.mark.parametrize("api_response,expected", [
    pytest.param({"status": "success"}, True, id="success"),
    pytest.param({"status": "error"}, False, id="error"),
    pytest.param({}, False, id="empty_response"),
])
@patch('module.api_client')
def test_check_status(mock_api, api_response, expected):
    mock_api.get_status.side_effect = [api_response]

    tested = StatusChecker()
    result = tested.check_status()

    assert result == expected

    exp_calls = [call.get_status()]
    assert mock_api.mock_calls == exp_calls
```

### Different Mock Behaviors

**Pattern**: Parametrize different mock responses.

```python
@pytest.mark.parametrize("side_effect,expected,exp_retry_count", [
    pytest.param(
        [{"data": "value"}],
        {"data": "value"},
        1,
        id="success_first_try"
    ),
    pytest.param(
        [TimeoutError(), {"data": "value"}],
        {"data": "value"},
        2,
        id="success_after_retry"
    ),
    pytest.param(
        [TimeoutError(), TimeoutError(), TimeoutError()],
        None,
        3,
        id="all_retries_failed"
    ),
])
@patch('module.api')
def test_retry_logic(mock_api, side_effect, expected, exp_retry_count):
    mock_api.fetch.side_effect = side_effect

    tested = RetryClient()
    result = tested.fetch_with_retry()

    assert result == expected

    exp_calls = [call.fetch()] * exp_retry_count
    assert mock_api.mock_calls == exp_calls
```

## Multiple Parametrize Decorators

### Cartesian Product

**Pattern**: Test all combinations of parameters.

```python
@pytest.mark.parametrize("operator", [
    pytest.param("+", id="addition"),
    pytest.param("-", id="subtraction"),
])
@pytest.mark.parametrize("a,b", [
    pytest.param(5, 3, id="positive"),
    pytest.param(-5, -3, id="negative"),
    pytest.param(0, 0, id="zeros"),
])
def test_calculator_operations(operator, a, b):
    tested = Calculator()
    result = tested.calculate(a, operator, b)

    if operator == "+":
        expected = a + b
    else:
        expected = a - b

    assert result == expected
```

This creates 6 tests (2 operators × 3 value pairs):
```
test_calculator.py::test_calculator_operations[addition-positive] PASSED
test_calculator.py::test_calculator_operations[addition-negative] PASSED
test_calculator.py::test_calculator_operations[addition-zeros] PASSED
test_calculator.py::test_calculator_operations[subtraction-positive] PASSED
test_calculator.py::test_calculator_operations[subtraction-negative] PASSED
test_calculator.py::test_calculator_operations[subtraction-zeros] PASSED
```

## Indirect Parametrization

### Parametrizing Fixtures

**Pattern**: Use `indirect=True` to parametrize fixtures.

```python
@pytest.fixture
def database(request):
    db_type = request.param
    if db_type == "sqlite":
        return SQLiteDatabase()
    elif db_type == "postgres":
        return PostgresDatabase()

@pytest.mark.parametrize("database", [
    pytest.param("sqlite", id="sqlite_db"),
    pytest.param("postgres", id="postgres_db"),
], indirect=True)
def test_save_record(database):
    tested = RecordService(database)
    result = tested.save_record({"name": "test"})
    assert result is not None
```

## Skipping Parameters

### Conditional Skipping

**Pattern**: Skip specific parameter combinations.

```python
import sys

@pytest.mark.parametrize("os_type,expected", [
    pytest.param("linux", "/tmp", id="linux"),
    pytest.param("darwin", "/tmp", id="macos"),
    pytest.param(
        "windows",
        "C:\\Temp",
        marks=pytest.mark.skipif(
            sys.platform != "win32",
            reason="Windows-only test"
        ),
        id="windows"
    ),
])
def test_temp_directory(os_type, expected):
    tested = FileSystem()
    result = tested.get_temp_dir(os_type)
    assert result == expected
```

## Real-World Examples

### Email Validation

```python
@pytest.mark.parametrize("email,expected", [
    pytest.param("user@example.com", True, id="valid_standard"),
    pytest.param("user.name@example.com", True, id="valid_with_dot"),
    pytest.param("user+tag@example.co.uk", True, id="valid_with_plus"),
    pytest.param("invalid.email", False, id="missing_at"),
    pytest.param("@example.com", False, id="missing_local"),
    pytest.param("user@", False, id="missing_domain"),
    pytest.param("", False, id="empty"),
])
def test_validate_email(email, expected):
    tested = Validator()
    result = tested.validate_email(email)
    assert result == expected
```

### Date Parsing

```python
from datetime import datetime

@pytest.mark.parametrize("date_string,expected", [
    pytest.param(
        "2024-01-15",
        datetime(2024, 1, 15),
        id="iso_format"
    ),
    pytest.param(
        "01/15/2024",
        datetime(2024, 1, 15),
        id="us_format"
    ),
    pytest.param(
        "15-01-2024",
        datetime(2024, 1, 15),
        id="eu_format"
    ),
])
def test_parse_date(date_string, expected):
    tested = DateParser()
    result = tested.parse_date(date_string)
    assert result == expected

@pytest.mark.parametrize("invalid_date", [
    pytest.param("invalid", id="not_a_date"),
    pytest.param("2024-13-01", id="invalid_month"),
    pytest.param("2024-01-32", id="invalid_day"),
])
def test_parse_date_errors(invalid_date):
    tested = DateParser()
    with pytest.raises(ValueError):
        tested.parse_date(invalid_date)
```

### API Response Handling

```python
@pytest.mark.parametrize("status_code,response_data,expected", [
    pytest.param(
        200,
        {"data": "value"},
        {"data": "value"},
        id="success_200"
    ),
    pytest.param(
        201,
        {"id": 123},
        {"id": 123},
        id="created_201"
    ),
    pytest.param(
        404,
        {"error": "Not found"},
        None,
        id="not_found_404"
    ),
    pytest.param(
        500,
        {"error": "Server error"},
        None,
        id="server_error_500"
    ),
])
@patch('module.requests.get')
def test_api_response_handling(mock_get, status_code, response_data, expected):
    mock_response = mock_get.return_value
    mock_response.status_code = status_code
    mock_response.json.side_effect = [response_data]

    tested = APIClient()
    result = tested.fetch_data("https://api.example.com/data")

    assert result == expected

    exp_calls = [call("https://api.example.com/data")]
    assert mock_get.mock_calls == exp_calls
```

### File Processing

```python
@pytest.mark.parametrize("file_content,expected_lines,expected_word_count", [
    pytest.param(
        "Hello world\nSecond line",
        2,
        3,
        id="two_lines"
    ),
    pytest.param(
        "Single line",
        1,
        2,
        id="single_line"
    ),
    pytest.param(
        "",
        0,
        0,
        id="empty_file"
    ),
    pytest.param(
        "One\nTwo\nThree\nFour",
        4,
        4,
        id="multiple_lines"
    ),
])
@patch('module.open')
def test_process_file(mock_open, file_content, expected_lines, expected_word_count):
    mock_file = mock_open.return_value.__enter__.return_value
    mock_file.read.side_effect = [file_content]

    tested = FileProcessor()
    result = tested.process_file("test.txt")

    exp_lines = expected_lines
    exp_words = expected_word_count

    assert result["lines"] == exp_lines
    assert result["words"] == exp_words

    exp_calls = [
        call("test.txt", "r"),
        call().__enter__(),
        call().__enter__().read(),
        call().__exit__(None, None, None)
    ]
    assert mock_open.mock_calls == exp_calls
```

## When NOT to Use Parametrize

### Complex Setup Differences

If test scenarios require significantly different setup, use separate test functions:

**Don't do this** (complex conditional logic):
```python
@pytest.mark.parametrize("scenario,setup_type,mock_config", [
    pytest.param("simple", "basic", {...}, id="simple"),
    pytest.param("complex", "advanced", {...}, id="complex"),
])
def test_process(scenario, setup_type, mock_config):
    if scenario == "simple":
        # 20 lines of setup
    elif scenario == "complex":
        # 30 lines of different setup
    # Test logic
```

**Do this instead** (separate functions):
```python
def test_process__simple():
    # Simple setup
    # Test logic

def test_process__complex():
    # Complex setup
    # Test logic
```

### Different Assertions

If scenarios need different assertions, use separate functions:

**Don't do this**:
```python
@pytest.mark.parametrize("input,check_type", [
    pytest.param(5, "positive", id="positive"),
    pytest.param(0, "zero", id="zero"),
])
def test_validate(input, check_type):
    result = validate(input)
    if check_type == "positive":
        assert result > 0
    elif check_type == "zero":
        assert result == 0
```

**Do this instead**:
```python
def test_validate__positive():
    result = validate(5)
    assert result > 0

def test_validate__zero():
    result = validate(0)
    assert result == 0
```

## Parametrization Best Practices

### Clear IDs

Always provide descriptive `id` parameters:

```python
@pytest.mark.parametrize("value,expected", [
    pytest.param(10, 100, id="ten"),
    pytest.param(5, 25, id="five"),
    pytest.param(0, 0, id="zero"),
])
```

### Limit Scope

Keep parametrized tests focused on single functionality:

**Good** (focused):
```python
@pytest.mark.parametrize("x,expected", [
    pytest.param(2, 4, id="two"),
    pytest.param(3, 9, id="three"),
])
def test_square(x, expected):
    result = square(x)
    assert result == expected
```

**Avoid** (too broad):
```python
@pytest.mark.parametrize("operation,x,y,expected", [
    pytest.param("add", 2, 3, 5, id="add"),
    pytest.param("multiply", 2, 3, 6, id="multiply"),
    # Better as separate test functions
])
```

### Order Parameters Logically

Put inputs before expected outputs:

**Good**:
```python
@pytest.mark.parametrize("input_value,expected_result", [...])
```

**Avoid**:
```python
@pytest.mark.parametrize("expected_result,input_value", [...])
```

## Summary

**Use pytest.param**: Always use `pytest.param()` with `id` parameter

**Descriptive IDs**: Use lowercase with underscores (`"valid_input"`)

**Inputs before outputs**: Order parameters logically

**Prefer parametrize**: First choice for multiple scenarios

**Use separate functions**: When setup or assertions differ significantly

**Test combinations**: Use multiple decorators for cartesian products

**Mock within parametrize**: Combine with mocks for comprehensive testing

**Focus scope**: Keep parametrized tests focused on single functionality

Parametrization is the preferred approach for testing multiple scenarios efficiently while maintaining clear, maintainable test code.
