"""
Complete Test File Example

This file demonstrates all pytest guidelines in practice, including:
- Proper test/source file structure
- Naming conventions (test functions, variables)
- Mock usage with side_effect and mock_calls
- Parametrization with pytest.param
- Test ordering matching source code
- 100% coverage

Source File: calculator.py
Test File: test_calculator.py
"""

# =============================================================================
# SOURCE FILE (calculator.py)
# =============================================================================
"""
from datetime import datetime
from typing import List
from computer import Computer


class Calculator(Computer):
    def __init__(self, name: str = "default"):
        self.name = name
        self.history: List[str] = []

    def add(self, a: float, b: float) -> float:
        result = a + b
        self._log_operation(f"add({a}, {b}) = {result}")
        return result

    def subtract(self, a: float, b: float) -> float:
        result = a - b
        self._log_operation(f"subtract({a}, {b}) = {result}")
        return result

    def multiply(self, a: float, b: float) -> float:
        result = a * b
        self._log_operation(f"multiply({a}, {b}) = {result}")
        return result

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self._log_operation(f"divide({a}, {b}) = {result}")
        return result

    def power(self, base: float, exponent: float) -> float:
        result = base ** exponent
        return result

    def get_history(self) -> List[str]:
        return self.history.copy()

    def clear_history(self) -> None:
        self.history.clear()

    def _log_operation(self, message: str) -> None:
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.history.append(log_entry)

    def _validate(self, value: float) -> bool:
        return value is not None and isinstance(value, (int, float))
"""

# =============================================================================
# TEST FILE (test_calculator.py)
# =============================================================================
from unittest.mock import patch, call

import pytest
from calculator import Calculator, Computer


# =============================================================================
# TEST FUNCTIONS - Ordered by appearance in source file
# =============================================================================

def test_inheritance():
    assert issubclass(Calculator, Computer)


def test___init__():
    """Test Calculator initialization with the default name"""
    tested = Calculator()

    exp_name = "default"
    exp_history = []

    assert tested.name == exp_name
    assert tested.history == exp_history


def test___init____custom_name():
    """Test Calculator initialization with a custom name"""
    tested = Calculator(name="scientific")

    exp_name = "scientific"
    exp_history = []

    assert tested.name == exp_name
    assert tested.history == exp_history


# Test: add
def test_add():
    """Test addition"""
    tested = Calculator()

    with patch.object(tested, '_log_operation') as mock_log:
        result = tested.add(5, 3)

    expected = 8
    assert result == expected

    # Verify _log_operation was called
    exp_calls = [call("add(5, 3) = 8")]
    assert mock_log.mock_calls == exp_calls


@pytest.mark.parametrize(("a", "b", "expected", "exp_calls"), [
    pytest.param(5, 3, 8, [call('add(5, 3) = 8')], id="positive_numbers"),
    pytest.param(-5, -3, -8, [call('add(-5, -3) = -8')], id="negative_numbers"),
    pytest.param(0, 0, 0, [call('add(0, 0) = 0')], id="zeros"),
    pytest.param(1.5, 2.5, 4.0, [call('add(1.5, 2.5) = 4.0')], id="floats"),
])
def test_add__parametrized(a, b, expected, exp_calls):
    """Test addition with multiple scenarios"""
    tested = Calculator()

    with patch.object(tested, '_log_operation') as mock_log:
        result = tested.add(a, b)

    assert result == expected

    # Verify _log_operation exact message with expected values hardcoded
    assert mock_log.mock_calls == exp_calls


# Test: subtract
def test_subtract():
    """Test subtraction"""
    tested = Calculator()

    with patch.object(tested, '_log_operation') as mock_log:
        result = tested.subtract(10, 4)

    expected = 6
    assert result == expected

    # Verify _log_operation was called
    exp_calls = [call("subtract(10, 4) = 6")]
    assert mock_log.mock_calls == exp_calls


# Test: multiply
def test_multiply():
    """Test multiplication"""
    tested = Calculator()

    with patch.object(tested, '_log_operation') as mock_log:
        result = tested.multiply(4, 5)

    expected = 20
    assert result == expected

    # Verify _log_operation was called
    exp_calls = [call("multiply(4, 5) = 20")]
    assert mock_log.mock_calls == exp_calls


# Test: divide
def test_divide():
    """Test division with valid divisor"""
    tested = Calculator()

    with patch.object(tested, '_log_operation') as mock_log:
        result = tested.divide(10, 2)

    expected = 5.0
    assert result == expected

    # Verify _log_operation was called
    exp_calls = [call("divide(10, 2) = 5.0")]
    assert mock_log.mock_calls == exp_calls


def test_divide__zero_divisor():
    """Test division by zero raises ValueError"""
    tested = Calculator()

    with pytest.raises(ValueError, match="Cannot divide by zero"):
        tested.divide(10, 0)


# Test: power
def test_power():
    """Test exponentiation"""
    tested = Calculator()
    result = tested.power(2, 3)

    expected = 8
    assert result == expected


@pytest.mark.parametrize(("base", "exponent", "expected"), [
    pytest.param(2, 3, 8, id="positive_exponent"),
    pytest.param(5, 0, 1, id="zero_exponent"),
    pytest.param(2, -1, 0.5, id="negative_exponent"),
])
def test_power__parametrized(base, exponent, expected):
    """Test power with multiple scenarios"""
    tested = Calculator()
    result = tested.power(base, exponent)

    assert result == expected


# Test: get_history
def test_get_history():
    """Test retrieving operation history"""
    tested = Calculator()

    with patch.object(tested, '_log_operation') as mock_log:
        tested.add(5, 3)
        tested.subtract(10, 2)

    # Verify operations were logged
    exp_log_calls = [
        call("add(5, 3) = 8"),
        call("subtract(10, 2) = 8")
    ]
    assert mock_log.mock_calls == exp_log_calls

    # Since we mocked _log_operation, history will be empty
    # To properly test get_history, we need to test it without mocking
    tested2 = Calculator()
    tested2.history = ["op1", "op2"]
    result = tested2.get_history()

    expected = ["op1", "op2"]
    assert result == expected
    # Verify it returns a copy, not the original list
    assert result is not tested2.history


def test_get_history__empty():
    """Test retrieving empty history"""
    tested = Calculator()

    result = tested.get_history()

    expected = []
    assert result == expected


# Test: clear_history
def test_clear_history():
    """Test clearing operation history"""
    tested = Calculator()

    tested.history = ["op1", "op2"]
    tested.clear_history()

    result = tested.get_history()

    expected = []
    assert result == expected


# Test: _log_operation (private method)
@patch('calculator.datetime')
def test__log_operation(mock_datetime):
    """Test logging operation to history"""
    mock_datetime.now.return_value.isoformat.side_effect = ["2024-01-01T12:00:00"]

    tested = Calculator()
    tested._log_operation("test operation")

    exp_history = ["[2024-01-01T12:00:00] test operation"]
    assert tested.history == exp_history

    exp_calls = [call.now(), call.now().isoformat()]
    assert mock_datetime.mock_calls == exp_calls


# Test: _validate (private method)
@pytest.mark.parametrize(("value", "expected"), [
    pytest.param(5, True, id="valid_int"),
    pytest.param(5.5, True, id="valid_float"),
    pytest.param(None, False, id="none_value"),
    pytest.param("5", False, id="string_value"),
])
def test__validate(value, expected):
    """Test value validation"""
    tested = Calculator()
    result = tested._validate(value)

    # Use 'is' for boolean singleton comparisons
    assert result is expected

# =============================================================================
# KEY TAKEAWAYS FROM THIS EXAMPLE
# =============================================================================
"""
1. NAMING CONVENTIONS:
   - Test file: test_calculator.py (mirrors calculator.py)
   - Test functions: test_<method> or test_<method>__<case>
   - Private methods: test__log_operation (underscore included)
   - Variables: tested, result, expected, exp_*

2. TEST ORDERING:
   - Tests appear in same order as methods in source file
   - __init__, add, subtract, multiply, divide, power, get_history, clear_history, _log_operation, _validate

3. MOCK USAGE:
   - ALWAYS use side_effect for all return values (NEVER use return_value to set returns)
   - For complex return objects, create MagicMock() and return via side_effect
   - Example: mock_get.side_effect = [mock_response] (not mock_get.return_value = mock_response)
   - CRITICAL: Verify ALL mock objects with mock_calls property:
     * Main patched mocks (mock_datetime, mock_get, etc.)
     * Created MagicMock() objects (mock_response, mock_now, etc.)
     * .return_value instances (mock_db_class.return_value)
   - CRITICAL: ALWAYS verify at OBJECT level:
     * CORRECT: assert mock_response.mock_calls == exp_calls
     * FORBIDDEN: assert mock_response.read.mock_calls == exp_calls (method level)
   - CRITICAL: Use SINGLE assertion with HARD-CODED values:
     * CORRECT: assert mock.mock_calls == [call("http://example.com")]
     * FORBIDDEN: assert len(mock.mock_calls) == 1 (checking length)
     * FORBIDDEN: assert mock.mock_calls[0] == call(url_var) (indexing + variable)
     * ALWAYS use hard-coded literals, NEVER use variables in expected calls
   - If you create a mock object, you MUST verify its calls at object level
   - Never use assert_called_with() or similar helpers
   - Define exp_calls before assertion

4. PARAMETRIZATION:
   - Use @pytest.mark.parametrize for multiple scenarios
   - CRITICAL: First parameter must be a TUPLE: ("a", "b", "expected")
   - FORBIDDEN: Using string: "a,b,expected"
   - Use pytest.param() with id parameter
   - Descriptive IDs: "positive_numbers", "zero_divisor"

5. EXPECTED VALUES:
   - CRITICAL: Expected values must ALWAYS be hardcoded literals
   - ✅ CORRECT: expected = 8, exp_calls = [call("add(5, 3) = 8")]
   - ❌ FORBIDDEN: expected = a + b (computed)
   - ❌ FORBIDDEN: exp_calls = [call(f"add({a}, {b}) = {result}")] (dynamic in assertions)
   - Exception: In parametrized tests, you may construct expected values from parameters

6. VARIABLE NAMING:
   - tested: The Calculator instance
   - result: Return value from method
   - expected: Expected single value
   - exp_calls, exp_history: Multiple expected values with exp_ prefix

7. ASSERTION STYLE:
   - Use 'is' for singleton comparisons: True, False, None
   - Example: assert result is True (not assert result == True)
   - Use '==' for all other comparisons: strings, numbers, lists, dicts

8. MULTIPLE TEST CASES:
   - Prefer parametrize: test_add__parametrized
   - Alternative: Multiple functions: test_divide, test_divide__zero_divisor
   - Keep parametrization focused and simple

9. EXCEPTIONS:
   - Use pytest.raises() with match parameter
   - Still verify mock_calls if mocks are involved

10. COVERAGE:
   - Every method has at least one test
   - Edge cases covered (zero divisor, empty history, None values)
   - Private methods tested
   - Achieves 100% code coverage

11. MOCKING STRATEGY:
   - Mock at the RIGHT LEVEL for the method being tested:
     * When testing PUBLIC methods (add, subtract, etc.): Mock the PRIVATE methods they call (_log_operation)
     * When testing PRIVATE methods (_log_operation): Mock their external dependencies (datetime)
   - ARCHITECTURE: Test one layer at a time, mock the layer below
   - ✅ CORRECT: test_add mocks _log_operation, test__log_operation mocks datetime
   - ❌ WRONG: test_add mocks datetime directly (skips the _log_operation layer)
   - Use patch.object(tested, '_log_operation') for private method mocking
   - Mock external dependencies: datetime, file operations, HTTP requests
   - Don't mock the class being tested
   - Always verify EVERY mock object you create:
     * If you create mock_now = MagicMock(), you must assert mock_now.mock_calls
     * If you create mock_response = MagicMock(), you must assert mock_response.mock_calls
     * Missing verification of any mock object is a critical error

12. CONSISTENCY:
    - All tests follow same structure
    - Same naming patterns throughout
    - Predictable and maintainable
"""
