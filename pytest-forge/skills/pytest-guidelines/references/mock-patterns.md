# Mock Patterns - Comprehensive Guide

This reference provides detailed patterns for using mocks in pytest tests, emphasizing `side_effect` for return values and `mock_calls` for verification.

## Core Mock Principles

### Always Use `side_effect` for Return Values

**MANDATORY**: Use `side_effect` instead of `return_value` for all mock return values, even for single returns.

**Rationale**:
- Consistent pattern across all mocks
- Supports sequential return values naturally
- Makes mock behavior explicit
- Better represents the mock as a sequence of interactions
- Prevents confusion about mock behavior

**FORBIDDEN**: Never use `mock.return_value = value` or `mock_obj.method.return_value = value` to set return values.

**Exception**: Using `.return_value` to access a mock instance is acceptable ONLY when you need to configure the instance that a mocked class constructor returns:
```python
@patch('module.Database')
def test_example(mock_db_class):
    mock_db = mock_db_class.return_value  # OK: Getting instance mock
    mock_db.connect.side_effect = [None]  # Use side_effect to set returns
```

### Always Verify with `mock_calls`

**MANDATORY**: After every test involving mocks, verify ALL mock interactions using the `mock_calls` property.

**Critical Rule**: If you create a mock object (using `MagicMock()`, `mock.return_value`, etc.), you MUST verify its calls. This includes:
- The main patched mock (e.g., `mock_urlopen`)
- Any `MagicMock()` objects you create (e.g., `mock_response`)
- Any `.return_value` mock instances (e.g., `mock_db_class.return_value`)

**Verification Level**: ALWAYS verify at the **mock object level**, not individual method level:
- **CORRECT**: `assert mock_response.mock_calls == exp_calls`
- **FORBIDDEN**: `assert mock_response.read.mock_calls == exp_calls` (verifying individual method)
- **FORBIDDEN**: `assert mock_response.read.return_value.decode.mock_calls == exp_calls` (verifying nested attribute)

**Rationale**:
- Ensures complete verification of mock usage
- Catches unexpected or missing method calls
- Prevents partial verification that might miss issues
- Creates comprehensive test coverage
- Verifying at object level captures ALL interactions

**Pattern**: For each mock object created, define its expected calls and verify:
```python
# Verify at the mock OBJECT level
exp_main_calls = [call(...)]
assert mock_main.mock_calls == exp_main_calls

# Verify all methods on the mock object
exp_response_calls = [call.method1(), call.method2()]
assert mock_response.mock_calls == exp_response_calls
```

**Verification Format**:
- **CORRECT**: `assert mock.mock_calls == exp_calls` (single assertion with list comparison)
- **FORBIDDEN**: Checking length then individual calls:
  ```python
  # WRONG - do not check length and individual items
  assert len(mock.mock_calls) == 3
  assert mock.mock_calls[0] == call(...)
  assert mock.mock_calls[1] == call(...)
  ```

**Hard-Coded Values Required**:
- ALWAYS use hard-coded literal values in expected calls
- **FORBIDDEN**: Using variables in expected values
  ```python
  # WRONG - using variables
  tested_url = "http://example.com"
  exp_calls = [call(f"URL: {tested_url}")]  # Don't use variable

  # CORRECT - hard-coded values
  exp_calls = [call("URL: http://example.com")]  # Use literal
  ```

### Forbidden Assertion Methods

**NEVER USE** these mock assertion helpers:
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

**NEVER verify at method or nested attribute level**:
- `mock_response.read.mock_calls` (FORBIDDEN - verifying individual method)
- `mock_response.read.return_value.decode.mock_calls` (FORBIDDEN - verifying nested attribute)
- `mock_obj.method.mock_calls` (FORBIDDEN - always verify at object level)

**ONLY use `mock_calls` at object level for all verification**:
- `assert mock_object.mock_calls == exp_calls` (CORRECT - object level verification)

## Basic Mock Patterns

### Simple Function Mock

**Pattern**: Mock a function with a single return value.

```python
from unittest.mock import patch, call

@patch('module.external_function')
def test_call_external(mock_func):
    mock_func.side_effect = ["return_value"]

    tested = MyClass()
    result = tested.call_external()

    expected = "return_value"
    assert result == expected

    exp_calls = [call()]
    assert mock_func.mock_calls == exp_calls
```

### Function with Arguments

**Pattern**: Mock a function that receives arguments.

```python
@patch('module.api_call')
def test_fetch_data(mock_api):
    mock_api.side_effect = [{"data": "value"}]

    tested = DataFetcher()
    result = tested.fetch_data("user123")

    expected = {"data": "value"}
    assert result == expected

    exp_calls = [call("user123")]
    assert mock_api.mock_calls == exp_calls
```

### Multiple Return Values

**Pattern**: Mock sequential calls with different return values.

```python
@patch('module.api_call')
def test_retry_logic(mock_api):
    # First call fails, second succeeds
    mock_api.side_effect = [
        Exception("Network error"),
        {"status": "success"}
    ]

    tested = RetryableClient()
    result = tested.fetch_with_retry()

    expected = {"status": "success"}
    assert result == expected

    exp_calls = [call(), call()]
    assert mock_api.mock_calls == exp_calls
```

## Method Mocks

### Mocking Object Methods

**Pattern**: Mock methods on an object.

```python
@patch('module.Database')
def test_save_user(mock_db_class):
    mock_db = mock_db_class.return_value
    mock_db.connect.side_effect = [None]
    mock_db.insert.side_effect = [42]
    mock_db.close.side_effect = [None]

    tested = UserService()
    result = tested.save_user({"name": "John"})

    expected = 42
    assert result == expected

    # Verify the class constructor was called
    exp_class_calls = [call()]
    assert mock_db_class.mock_calls == exp_class_calls

    # Verify the instance methods were called
    exp_db_calls = [
        call.connect(),
        call.insert({"name": "John"}),
        call.close()
    ]
    assert mock_db.mock_calls == exp_db_calls
```

### Chained Method Calls

**Pattern**: Mock fluent interfaces or chained calls.

```python
@patch('module.QueryBuilder')
def test_build_query(mock_builder_class):
    mock_builder = mock_builder_class.return_value
    mock_builder.select.side_effect = [mock_builder]
    mock_builder.where.side_effect = [mock_builder]
    mock_builder.execute.side_effect = [[{"id": 1}, {"id": 2}]]

    tested = DataService()
    result = tested.get_users()

    expected = [{"id": 1}, {"id": 2}]
    assert result == expected

    # Verify constructor was called
    exp_class_calls = [call()]
    assert mock_builder_class.mock_calls == exp_class_calls

    # Verify instance methods were called
    exp_builder_calls = [
        call.select("*"),
        call.where("active", True),
        call.execute()
    ]
    assert mock_builder.mock_calls == exp_builder_calls
```

## Multiple Mocks

### Multiple Patches

**Pattern**: Mock multiple dependencies in a single test.

```python
@patch('module.datetime')
@patch('module.database')
@patch('module.api_client')
def test_create_record(mock_api, mock_db, mock_datetime):
    # Note: Patches are applied bottom-to-top
    mock_datetime.now.side_effect = [datetime(2024, 1, 1, 12, 0)]
    mock_api.fetch.side_effect = [{"external_id": "abc123"}]
    mock_db.insert.side_effect = [42]

    tested = RecordService()
    result = tested.create_record("John")

    expected = 42
    assert result == expected

    exp_datetime_calls = [call.now()]
    exp_api_calls = [call.fetch("John")]
    exp_db_calls = [call.insert({
        "name": "John",
        "external_id": "abc123",
        "timestamp": datetime(2024, 1, 1, 12, 0)
    })]

    assert mock_datetime.mock_calls == exp_datetime_calls
    assert mock_api.mock_calls == exp_api_calls
    assert mock_db.mock_calls == exp_db_calls
```

### Nested Mock Calls

**Pattern**: Mock nested attribute access and method calls.

```python
@patch('module.client')
def test_api_request(mock_client):
    mock_client.api.v1.users.get.side_effect = [{"id": 123}]

    tested = APIWrapper()
    result = tested.get_user(123)

    expected = {"id": 123}
    assert result == expected

    exp_calls = [call.api.v1.users.get(123)]
    assert mock_client.mock_calls == exp_calls
```

## Common Scenarios

### Mocking datetime

**Pattern**: Mock datetime.now() or other datetime operations.

```python
from datetime import datetime
from unittest.mock import patch, call

@patch('module.datetime')
def test_timestamp_creation(mock_datetime):
    mock_datetime.now.side_effect = [datetime(2024, 1, 1, 15, 30, 0)]
    mock_datetime.strftime.side_effect = ["2024-01-01 15:30:00"]

    tested = TimestampService()
    result = tested.create_timestamp()

    expected = "2024-01-01 15:30:00"
    assert result == expected

    exp_calls = [call.now()]
    assert mock_datetime.mock_calls == exp_calls
```

### Mocking Random Values

**Pattern**: Mock random number generation for deterministic tests.

```python
@patch('module.random')
def test_generate_id(mock_random):
    mock_random.randint.side_effect = [42]

    tested = IDGenerator()
    result = tested.generate_id()

    expected = 42
    assert result == expected

    exp_calls = [call.randint(1, 100)]
    assert mock_random.mock_calls == exp_calls
```

### Mocking File Operations

**Pattern**: Mock file reading/writing.

```python
@patch('module.open')
def test_read_config(mock_open):
    mock_file = mock_open.return_value.__enter__.return_value
    mock_file.read.side_effect = ['{"setting": "value"}']

    tested = ConfigReader()
    result = tested.read_config("config.json")

    expected = {"setting": "value"}
    assert result == expected

    exp_calls = [
        call("config.json", "r"),
        call().__enter__(),
        call().__enter__().read(),
        call().__exit__(None, None, None)
    ]
    assert mock_open.mock_calls == exp_calls
```

### Mocking Database Queries

**Pattern**: Mock database connections and queries.

```python
@patch('module.psycopg2.connect')
def test_query_users(mock_connect):
    mock_conn = mock_connect.return_value
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.fetchall.side_effect = [[
        (1, "Alice"),
        (2, "Bob")
    ]]

    tested = UserRepository()
    result = tested.get_all_users()

    expected = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
    assert result == expected

    # Verify connect was called
    exp_connect_calls = [call()]
    assert mock_connect.mock_calls == exp_connect_calls

    # Verify connection methods were called
    exp_conn_calls = [
        call.cursor(),
        call.close()
    ]
    assert mock_conn.mock_calls == exp_conn_calls

    # Verify cursor methods were called
    exp_cursor_calls = [
        call.execute("SELECT id, name FROM users"),
        call.fetchall(),
        call.close()
    ]
    assert mock_cursor.mock_calls == exp_cursor_calls
```

### Mocking HTTP Requests

**Pattern**: Mock HTTP client libraries. **CRITICAL**: Always verify both the request mock AND the response mock.

```python
from unittest.mock import patch, call, MagicMock

@patch('module.requests.get')
def test_fetch_api_data(mock_get):
    # Create a mock response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = [{"data": "value"}]

    # Use side_effect to return the mock response
    mock_get.side_effect = [mock_response]

    tested = APIClient()
    result = tested.fetch_data("https://api.example.com/data")

    expected = {"data": "value"}
    assert result == expected

    # CRITICAL: Verify the request function was called
    exp_get_calls = [call("https://api.example.com/data")]
    assert mock_get.mock_calls == exp_get_calls

    # CRITICAL: Verify the response methods were called
    exp_response_calls = [call.json()]
    assert mock_response.mock_calls == exp_response_calls
```

### Mocking Environment Variables

**Pattern**: Mock os.environ or os.getenv.

```python
@patch('module.os.getenv')
def test_load_env_config(mock_getenv):
    mock_getenv.side_effect = ["production", "db.example.com", "5432"]

    tested = ConfigLoader()
    result = tested.load_config()

    expected = {
        "environment": "production",
        "db_host": "db.example.com",
        "db_port": "5432"
    }
    assert result == expected

    exp_calls = [
        call("ENVIRONMENT"),
        call("DB_HOST"),
        call("DB_PORT")
    ]
    assert mock_getenv.mock_calls == exp_calls
```

## Exception Handling

### Mocking Exceptions

**Pattern**: Mock functions that raise exceptions.

```python
@patch('module.api_call')
def test_handle_network_error(mock_api):
    mock_api.side_effect = [ConnectionError("Network unreachable")]

    tested = ResilientClient()

    with pytest.raises(ConnectionError):
        tested.fetch_data()

    exp_calls = [call()]
    assert mock_api.mock_calls == exp_calls
```

### Retry with Exception

**Pattern**: Test retry logic with exceptions and eventual success.

```python
@patch('module.unreliable_service')
def test_retry_until_success(mock_service):
    mock_service.call.side_effect = [
        TimeoutError("Timeout"),
        TimeoutError("Timeout"),
        {"status": "success"}
    ]

    tested = RetryService()
    result = tested.call_with_retry(max_retries=3)

    expected = {"status": "success"}
    assert result == expected

    exp_calls = [call.call(), call.call(), call.call()]
    assert mock_service.mock_calls == exp_calls
```

## Advanced Patterns

### Conditional Mocking

**Pattern**: Different return values based on arguments.

```python
@patch('module.cache')
def test_cache_lookup(mock_cache):
    def cache_side_effect(key):
        if key == "user:1":
            return {"name": "Alice"}
        elif key == "user:2":
            return {"name": "Bob"}
        return None

    mock_cache.get.side_effect = cache_side_effect

    tested = CacheService()
    result1 = tested.get_user(1)
    result2 = tested.get_user(2)

    exp_result1 = {"name": "Alice"}
    exp_result2 = {"name": "Bob"}

    assert result1 == exp_result1
    assert result2 == exp_result2

    exp_calls = [call.get("user:1"), call.get("user:2")]
    assert mock_cache.mock_calls == exp_calls
```

### Stateful Mocks

**Pattern**: Mock objects that maintain state across calls.

```python
@patch('module.Counter')
def test_counter_increment(mock_counter_class):
    mock_counter = mock_counter_class.return_value

    # Simulate stateful behavior
    counter_value = [0]

    def increment_side_effect():
        counter_value[0] += 1
        return counter_value[0]

    mock_counter.increment.side_effect = increment_side_effect
    mock_counter.value.side_effect = lambda: counter_value[0]

    tested = CounterService()
    result1 = tested.increment()
    result2 = tested.increment()
    result3 = tested.get_value()

    assert result1 == 1
    assert result2 == 2
    assert result3 == 2

    exp_calls = [
        call.increment(),
        call.increment(),
        call.value()
    ]
    assert mock_counter.mock_calls == exp_calls
```

### Partial Mocking

**Pattern**: Mock only specific methods of an object, use real implementations for others.

```python
from unittest.mock import patch, call, MagicMock

def test_partial_mock():
    tested = DataProcessor()

    # Mock only the _fetch_data method
    with patch.object(tested, '_fetch_data') as mock_fetch:
        mock_fetch.side_effect = [{"raw": "data"}]

        # The process() method uses real implementation
        # but _fetch_data is mocked
        result = tested.process()

        expected = {"processed": "data"}
        assert result == expected

        exp_calls = [call()]
        assert mock_fetch.mock_calls == exp_calls
```

## Verifying No Calls

**Pattern**: Verify a mock was never called.

```python
@patch('module.expensive_operation')
@patch('module.cache')
def test_cache_hit(mock_cache, mock_expensive):
    mock_cache.get.side_effect = [{"cached": "data"}]

    tested = OptimizedService()
    result = tested.get_data("key")

    expected = {"cached": "data"}
    assert result == expected

    exp_cache_calls = [call.get("key")]
    exp_expensive_calls = []  # Should not be called

    assert mock_cache.mock_calls == exp_cache_calls
    assert mock_expensive.mock_calls == exp_expensive_calls  # Verify empty
```

## Complete Example

**Source code**:
```python
# services/user_service.py
import requests
from datetime import datetime

class UserService:
    def create_user(self, name, email):
        # Validate email via external API
        validation = requests.post(
            "https://api.validator.com/email",
            json={"email": email}
        )

        if not validation.json()["valid"]:
            raise ValueError("Invalid email")

        # Create user record with timestamp
        user = {
            "name": name,
            "email": email,
            "created_at": datetime.now().isoformat()
        }

        # Save to database
        response = requests.post(
            "https://api.db.com/users",
            json=user
        )

        return response.json()["id"]
```

**Test code**:
```python
# tests/services/test_user_service.py
from unittest.mock import patch, call, MagicMock
from datetime import datetime
import pytest

from services.user_service import UserService

@patch('services.user_service.datetime')
@patch('services.user_service.requests')
def test_create_user(mock_requests, mock_datetime):
    # Setup datetime mock
    mock_now = MagicMock()
    mock_now.isoformat.side_effect = ["2024-01-01T12:00:00"]
    mock_datetime.now.side_effect = [mock_now]

    # Setup validation response
    mock_validation_response = MagicMock()
    mock_validation_response.json.side_effect = [{"valid": True}]

    # Setup creation response
    mock_creation_response = MagicMock()
    mock_creation_response.json.side_effect = [{"id": 123}]

    # Configure requests.post to return different responses
    mock_requests.post.side_effect = [
        mock_validation_response,
        mock_creation_response
    ]

    tested = UserService()
    result = tested.create_user("John Doe", "john@example.com")

    expected = 123
    assert result == expected

    # Verify datetime mock calls
    exp_datetime_calls = [call.now()]
    assert mock_datetime.mock_calls == exp_datetime_calls

    # Verify the datetime.now() mock calls
    exp_now_calls = [call.isoformat()]
    assert mock_now.mock_calls == exp_now_calls

    # Verify requests.post calls
    exp_requests_calls = [
        call.post(
            "https://api.validator.com/email",
            json={"email": "john@example.com"}
        ),
        call.post(
            "https://api.db.com/users",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "created_at": "2024-01-01T12:00:00"
            }
        )
    ]
    assert mock_requests.mock_calls == exp_requests_calls

    # Verify validation response mock calls
    exp_validation_calls = [call.json()]
    assert mock_validation_response.mock_calls == exp_validation_calls

    # Verify creation response mock calls
    exp_creation_calls = [call.json()]
    assert mock_creation_response.mock_calls == exp_creation_calls
```

## Anti-Patterns (FORBIDDEN)

These patterns are **STRICTLY FORBIDDEN** and must never appear in generated tests:

### ❌ Using `return_value` to Set Return Values

**WRONG**:
```python
@patch('module.urlopen')
def test_fetch(mock_urlopen):
    mock_urlopen.return_value = response_data  # FORBIDDEN!
```

**CORRECT**:
```python
@patch('module.urlopen')
def test_fetch(mock_urlopen):
    mock_urlopen.side_effect = [response_data]  # Always use side_effect
```

### ❌ Using `return_value` on Methods

**WRONG**:
```python
@patch('module.api_client')
def test_call(mock_client):
    mock_client.get.return_value = {"data": "value"}  # FORBIDDEN!
```

**CORRECT**:
```python
@patch('module.api_client')
def test_call(mock_client):
    mock_client.get.side_effect = [{"data": "value"}]  # Always use side_effect
```

### ❌ Using Mock Assert Helpers

**WRONG**:
```python
mock_func.assert_called_once()  # FORBIDDEN!
mock_func.assert_called_with(arg)  # FORBIDDEN!
assert mock_func.call_count == 1  # FORBIDDEN!
```

**CORRECT**:
```python
exp_calls = [call(arg)]
assert mock_func.mock_calls == exp_calls  # Always use mock_calls
```

### ❌ Not Verifying All Mock Objects

**WRONG** - Missing verification of mock_response:
```python
@patch('module.urlopen')
def test_fetch(mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.side_effect = [b"data"]
    mock_urlopen.side_effect = [mock_response]

    result = fetch_content("https://example.com")

    # FORBIDDEN: Only verifying mock_urlopen, forgetting mock_response!
    exp_urlopen_calls = [call("https://example.com")]
    assert mock_urlopen.mock_calls == exp_urlopen_calls
```

**CORRECT** - Verify ALL mock objects:
```python
@patch('module.urlopen')
def test_fetch(mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.side_effect = [b"data"]
    mock_urlopen.side_effect = [mock_response]

    result = fetch_content("https://example.com")

    # Verify the main mock
    exp_urlopen_calls = [call("https://example.com")]
    assert mock_urlopen.mock_calls == exp_urlopen_calls

    # CRITICAL: Also verify the response mock
    exp_response_calls = [call.read()]
    assert mock_response.mock_calls == exp_response_calls
```

### ❌ Verifying Individual Methods Instead of Mock Object

**WRONG** - Verifying at method level:
```python
@patch('module.urlopen')
def test_fetch(mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.side_effect = [b"data"]
    mock_urlopen.side_effect = [mock_response]

    result = fetch_content("https://example.com")

    # FORBIDDEN: Verifying individual method, not the object!
    exp_read_calls = [call()]
    assert mock_response.read.mock_calls == exp_read_calls  # WRONG LEVEL

    # FORBIDDEN: Verifying nested attributes!
    assert mock_response.read.return_value.decode.mock_calls == []  # WRONG LEVEL
```

**CORRECT** - Verify at object level:
```python
@patch('module.urlopen')
def test_fetch(mock_urlopen):
    mock_response = MagicMock()
    mock_response.read.side_effect = [b"data"]
    mock_urlopen.side_effect = [mock_response]

    result = fetch_content("https://example.com")

    # Verify urlopen was called
    exp_urlopen_calls = [call("https://example.com")]
    assert mock_urlopen.mock_calls == exp_urlopen_calls

    # CORRECT: Verify at the mock_response OBJECT level
    exp_response_calls = [call.read()]
    assert mock_response.mock_calls == exp_response_calls  # Object level!
```

### ❌ Checking Length and Individual Calls

**WRONG** - Checking length then individual items:
```python
@patch('builtins.print')
def test_print_messages(mock_print):
    tested_url = "http://example.com"
    tested_file = "output.txt"

    process_url(tested_url, tested_file)

    # FORBIDDEN: Checking length and individual calls
    assert len(mock_print.mock_calls) == 3
    assert call(f"URL: {tested_url}") == mock_print.mock_calls[0]  # Wrong format
    assert call(f"File: {tested_file}") == mock_print.mock_calls[1]  # Using variables
    assert call("Done") == mock_print.mock_calls[2]
```

**CORRECT** - Single assertion with hard-coded values:
```python
@patch('builtins.print')
def test_print_messages(mock_print):
    process_url("http://example.com", "output.txt")

    # CORRECT: Single assertion with hard-coded literal values
    exp_print_calls = [
        call("URL: http://example.com"),
        call("File: output.txt"),
        call("Done")
    ]
    assert mock_print.mock_calls == exp_print_calls
```

## Summary

**Use `side_effect` for returns**: Always use `side_effect` even for single values - NEVER use `return_value` to set what a mock returns

**Verify ALL mocks with `mock_calls`**:
- EVERY mock object must be verified: patched mocks, `MagicMock()` objects, `.return_value` instances
- ALWAYS verify at the **mock object level**: `assert mock_object.mock_calls == exp_calls`
- NEVER verify individual methods: `assert mock_object.method.mock_calls == exp_calls` (FORBIDDEN)
- NEVER verify nested attributes: `assert mock.method.return_value.attr.mock_calls == exp_calls` (FORBIDDEN)
- NEVER use assert helpers like `assert_called_with()`

**Verification format rules**:
- Use single assertion: `assert mock.mock_calls == exp_calls`
- NEVER check length then individual items: `assert len(mock.mock_calls) == 3` (FORBIDDEN)
- NEVER index mock_calls: `assert mock.mock_calls[0] == call(...)` (FORBIDDEN)

**Hard-coded values required**:
- ALWAYS use hard-coded literal values in expected calls
- NEVER use variables in expected values: `call(f"URL: {tested_url}")` (FORBIDDEN)
- Use literals directly: `call("URL: http://example.com")` (CORRECT)

**Critical verification rule**: Verify at object level with single assertion and hard-coded values:
```python
# Create it
mock_response = MagicMock()
# Configure it
mock_response.json.side_effect = [{"data": "value"}]
# Use it
mock_get.side_effect = [mock_response]

# VERIFY IT AT OBJECT LEVEL WITH HARD-CODED VALUES (MANDATORY)
exp_response_calls = [call.json()]  # Hard-coded method name
assert mock_response.mock_calls == exp_response_calls  # Single assertion!

# FORBIDDEN patterns
# assert len(mock_response.mock_calls) == 1  # Don't check length
# assert mock_response.mock_calls[0] == call.json()  # Don't index
# assert mock_response.json.mock_calls == [call()]  # Wrong level
```

**Mock external systems**: Database, HTTP, file I/O, datetime, random

**Verify completely**: Check every mock interaction, verify empty lists for unused mocks

**Use descriptive names**: `exp_calls`, `exp_api_calls`, `exp_db_calls`, `exp_response_calls`

**Create mock objects explicitly**: Use `MagicMock()` for complex return objects, then return them via `side_effect`

Following these mock patterns ensures comprehensive test coverage and reliable verification of external dependencies.
