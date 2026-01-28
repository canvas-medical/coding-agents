---
name: improve-tests
description: Analyze and enhance existing pytest tests for better quality, coverage, and guideline compliance
argument-hint: "<test_file>"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Task"]
---

# Improve Pytest Tests

Analyze existing test files, identify issues and gaps, and automatically refactor them to follow strict testing guidelines while improving coverage to 100%.

## Objective

Enhance test quality by:
1. Validating compliance with all guidelines
2. Identifying missing test coverage
3. Refactoring non-compliant tests
4. Adding tests for edge cases and error paths
5. Improving parametrization and mock usage
6. Achieving 100% code coverage

## Prerequisites

Before improving tests:
1. Ensure pytest and pytest-cov are installed
2. Test file must exist
3. Load the **pytest-guidelines** skill for reference

## Input Validation

### Check Argument

The command requires one argument: path to test file.

If no argument provided:
```
Error: Test file path required.

Usage: /pytest:improve-tests <test_file>

Example: /pytest:improve-tests tests/utils/test_parser.py
```

### Validate Test File

Check that the provided path:
- Exists and is readable
- Is a Python file (`.py` extension)
- Starts with `test_` prefix
- Contains actual test functions

If invalid:
```
Error: Invalid test file: <path>

Test file must:
- Exist and be readable
- Start with test_ prefix
- Contain test functions

Generate tests first: /pytest:generate-tests <source_file>
```

## Implementation Steps

### 1. Validate Type Annotations (MANDATORY PRE-CHECK)

**CRITICAL**: Before proceeding with test improvements, verify that the source code has complete type annotations. This step is mandatory and cannot be skipped.

**First, determine the source file** from the test file path:
```
tests/utils/test_parser.py → src/utils/parser.py (or similar)
```

**Check each function/method for**:
- Type annotations on ALL parameters (except `self` and `cls`)
- Return type annotation (including `-> None` for void functions)

**How to validate**:
1. Read the source file
2. Identify all function and method definitions
3. For each function/method, verify:
   - Every parameter has a type annotation
   - The return type is annotated

**If type annotations are missing, STOP and report**:
```
❌ Type Annotation Validation Failed

Cannot improve tests for <test_file> - source file <source_file> has missing type annotations.

The following functions/methods have incomplete type annotations:

  <class_name>.<method_name>:
    - Parameter '<param_name>' is missing type annotation
    - Return type is missing

  <function_name>:
    - Parameter '<param_name>' is missing type annotation

Please add type annotations to all parameters and return values in the source file before improving tests.

Example of properly typed code:
    def process(self, data: list[str], validate: bool = True) -> dict[str, int]:
        ...

After adding type annotations, run this command again.
```

**Only proceed to the next step if ALL functions/methods have complete type annotations.**

### 2. Run Initial Validation (PARALLEL AGENTS)

First, validate the test file to understand current state. Use 6 focused validation agents running IN PARALLEL to ensure thorough checking.

Spawn ALL of these agents simultaneously using Task tool in a SINGLE message:

#### Agent 1: validate-variable-names
```
Validate variable naming in test file: <test_file_path>

Check for:
- `tested` variable: must be used before method calls
- `result` variable: must store return values (not output, ret, actual)
- `expected` variable: must store expected values (not inlined)
- `exp_*` prefix: for multiple expected values (not expected_*)

Report ALL violations with file:line references.
```

#### Agent 2: validate-mock-objects
```
Validate mock object usage in test file: <test_file_path>

Check for:
- MagicMock used as return objects (should be SimpleNamespace)
- Look for: mock_response = MagicMock(), mock_request = MagicMock()
- Check if they have attributes set or are used in side_effect

Report ALL violations with file:line references.
```

#### Agent 3: validate-mock-verification
```
Validate mock verification in test file: <test_file_path>

Check that EVERY mock has mock_calls verification:
- All @patch mocks must have assert mock.mock_calls == exp_calls
- All MagicMock() objects must be verified
- Parametrized tests are NOT exempt

Report ALL unverified mocks with file:line references.
```

#### Agent 4: validate-pytest-fixtures
```
Validate pytest fixture usage in test file: <test_file_path>

Check for:
- Mocking print instead of using capsys fixture
- Look for: @patch("module.print"), mock_print parameter

Report ALL violations with file:line references.
```

#### Agent 5: validate-forbidden-patterns
```
Validate for forbidden patterns in test file: <test_file_path>

Check for:
- assert_called_with(), assert_called(), etc.
- return_value usage (should be side_effect)
- TestMainBlock or __main__ tests
- len(mock_calls), mock_calls[0] indexing
- @pytest.mark.parametrize("string" instead of tuple

Report ALL violations with file:line references.
```

#### Agent 6: validate-test-structure
```
Validate test structure in test file: <test_file_path>
Source file (if known): <source_file_path>

Check for:
- Test function naming: test_method or test_method__case
- Test class naming: TestClassName
- Test ordering matches source file
- Docstrings present

Report ALL violations with file:line references.
```

**After all agents complete**:
- Collect all violations from all agents
- Categorize by severity (critical, high, medium, low)
- Identify current coverage percentage
- Note missing lines/branches
- Identify improvement opportunities

### 3. Analyze Quality Issues

Categorize issues by type:

**Critical** (must fix):
- Using `return_value` instead of `side_effect`
- Using `MagicMock` for return objects (HTTP responses) instead of `SimpleNamespace`
  - Replace `mock_response = MagicMock()` with `SimpleNamespace(status_code=200, json=lambda: {...})`
  - Use lambdas for methods: `json=lambda: {"data": "value"}`
- Mocking `print` instead of using pytest's `capsys` fixture
  - Replace `@patch("module.print")` and `mock_print` with `capsys` fixture
  - Use `captured = capsys.readouterr()` then `assert "message" in captured.out`
- Using forbidden `assert_called_with()` methods
- Missing `mock_calls` verification for ANY mock (including in parametrized tests)
  - Every mock parameter MUST have a corresponding `assert mock.mock_calls == exp_*` statement
  - Parametrized tests are NOT exempt - they must verify mocks just like regular tests
- Tests for `if __name__ == "__main__":` blocks (should be DELETED, not fixed)
  - These blocks are excluded from coverage and should not be tested
  - Delete any TestMainBlock class or similar patterns
- Test functions without assertions
- Syntax errors or failing tests

**High** (should fix):
- Coverage < 100%
- Missing tests for methods
- Incorrect test ordering
- Variable naming violations:
  - Not using `tested` variable (calling methods directly on class name)
  - Not using `result` for return values (using `output`, `ret`, `actual`, etc.)
  - Not using `expected` for expected values (inlining in assertions)
  - Using `expected_*` prefix instead of `exp_*` for multiple expected values

**Medium** (improve):
- Multiple similar tests that could be parametrized
- Missing `id` parameter in `pytest.param`
- Non-descriptive test case IDs
- Redundant test logic

**Low** (nice to have):
- Better test documentation
- More descriptive variable names for `exp_*`
- Clearer test structure

### 4. Present Improvement Plan

Before making changes, show the user what will be done:

```
=== Test Improvement Plan ===

File: <test_file_path>
Current Coverage: X%
Issues Found: N critical, M high, K medium

PROPOSED CHANGES:

1. Fix Critical Issues:
   ✓ Line 45: Replace return_value with side_effect
   ✓ Line 67: Replace assert_called_with() with mock_calls check
   ✓ Line 89: Add missing mock_calls verification
   ✓ Line 459: DELETE TestMainBlock class (tests __main__ block - forbidden)

2. Improve Coverage (X% → 100%):
   ✓ Add test for error path in <method> (lines 102-105)
   ✓ Add test for edge case: empty input (line 78)
   ✓ Add test for edge case: None value (line 91)

3. Refactor for Guidelines:
   ✓ Reorder tests to match source file method order
   ✓ Fix variable naming violations:
     - Add `tested` variable where missing (assign class/instance before calling methods)
     - Rename return value variables to `result` (was: output, ret, actual)
     - Add `expected` variable where values are inlined in assertions
     - Rename `expected_*` to `exp_*` for multiple expected values
   ✓ Add descriptive IDs to parametrize decorators

4. Enhance Test Quality:
   ✓ Parametrize test_<method> (3 similar tests → 1 parametrized)
   ✓ Add missing test for private method _helper
   ✓ Improve error message assertions

Estimated changes: ~50 lines modified, ~30 lines added

Proceed with improvements? [Yes/No]
```

### 5. Apply Improvements (If User Confirms)

If user agrees, proceed with changes:

#### A. Fix Critical Mock Issues

Use Edit tool to fix each violation:

**Before**:
```python
@patch('module.api')
def test_fetch(mock_api):
    mock_api.get.return_value = {"data": "value"}
    result = fetch_data()
    mock_api.assert_called_once_with("url")
```

**After**:
```python
@patch('module.api')
def test_fetch(mock_api):
    mock_api.get.side_effect = [{"data": "value"}]

    tested = DataFetcher()
    result = tested.fetch_data()

    expected = {"data": "value"}
    assert result == expected

    exp_calls = [call.get("url")]
    assert mock_api.mock_calls == exp_calls
```

**Fix Missing `tested` Variable** (for class/static methods):

**Before**:
```python
@patch('module.sys')
def test_parse_arguments(mock_sys):
    mock_sys.argv = ["script.py", "/input.svg", "/output.png"]

    result = SvgToPngConverter.parse_arguments()  # WRONG: calling directly on class

    expected = ConversionInput(...)
    assert result == expected
```

**After**:
```python
@patch('module.sys')
def test_parse_arguments(mock_sys):
    tested = SvgToPngConverter  # CORRECT: assign class to tested variable
    mock_sys.argv = ["script.py", "/input.svg", "/output.png"]

    result = tested.parse_arguments()  # CORRECT: call on tested

    expected = ConversionInput(...)
    assert result == expected
```

**Fix MagicMock for Response Objects** (use SimpleNamespace instead):

**Before**:
```python
@patch('module.requests.post')
def test_call_api(mock_post):
    mock_response = MagicMock()  # WRONG: Using MagicMock for response
    mock_response.status_code = 200
    mock_response.json.side_effect = [{"data": "value"}]
    mock_post.side_effect = [mock_response]

    result = tested.call_api()

    # Must verify mock_response.mock_calls - easy to forget!
    exp_response_calls = [call.json()]
    assert mock_response.mock_calls == exp_response_calls
```

**After**:
```python
@patch('module.requests.post')
def test_call_api(mock_post):
    # CORRECT: Use SimpleNamespace - no mock_calls verification needed
    mock_post.side_effect = [
        SimpleNamespace(
            status_code=200,
            json=lambda: {"data": "value"}  # Lambda for methods
        )
    ]

    tested = ApiClient()
    result = tested.call_api()

    expected = {"data": "value"}
    assert result == expected

    # Only verify mock_post, NOT the response object
    exp_post_calls = [call("https://api.example.com")]
    assert mock_post.mock_calls == exp_post_calls
```

**Fix mock_print to use capsys fixture**:

**Before**:
```python
@patch("module.print")
@patch("module.Path")
def test_verify_structure(mock_path, mock_print):
    # ... setup mocks ...

    tested = verify_structure
    result = tested("my-plugin")

    # Complex extraction of print calls
    print_calls = [c[0][0] for c in mock_print.call_args_list if c[0]]
    assert "OK: Structure valid" in print_calls

    # Must also verify mock_print.mock_calls - easy to forget!
```

**After**:
```python
@patch("module.Path")
def test_verify_structure(mock_path, capsys):  # Use capsys fixture
    # ... setup mocks ...

    tested = verify_structure
    result = tested("my-plugin")

    # Simple assertion on captured output
    captured = capsys.readouterr()
    assert "OK: Structure valid" in captured.out

    # No mock_print verification needed!
    exp_path_calls = [call("my_plugin")]
    assert mock_path.mock_calls == exp_path_calls
```

#### B. Add Missing Tests

For each uncovered line/method:
- Identify what needs testing
- Generate appropriate test function
- Use proper naming convention
- Add mocks if needed
- Place in correct order

Delegate to **test-generator** agent for new test creation:
```
Generate tests for these uncovered scenarios in <source_file>:
- Lines 102-105: Error handling for invalid input
- Line 78: Edge case with empty string
- Line 91: Edge case with None value
- Method _helper: Private method not currently tested

Follow all pytest guidelines and integrate with existing tests.
```

#### C. Refactor for Compliance

**Fix `tested` Variable**:
```python
# Before - calling directly on class
result = Calculator.parse(data)

# After - assign to tested first
tested = Calculator
result = tested.parse(data)
```

**Fix `result` Variable**:
```python
# Before - using wrong name
output = tested.add(2, 3)
ret = tested.add(2, 3)
actual = tested.add(2, 3)

# After - use 'result'
result = tested.add(2, 3)
```

**Fix `expected` Variable**:
```python
# Before - inlined in assertion
assert result == 5

# After - use 'expected' variable
expected = 5
assert result == expected
```

**Fix `exp_*` Prefix**:
```python
# Before - using 'expected_' prefix
expected_calls = [call.get("url")]
assert mock_api.mock_calls == expected_calls

# After - use 'exp_' prefix
exp_calls = [call.get("url")]
assert mock_api.mock_calls == exp_calls
```

**Complete Variable Rename Example**:
```python
# Before
calc = Calculator()
output = calc.add(2, 3)
assert output == 5

# After
tested = Calculator()
result = tested.add(2, 3)
expected = 5
assert result == expected
```

**Reorder Tests**:
Rearrange test functions to match source file method order.

**Add Parametrization**:
```python
# Before (3 separate functions)
def test_validate__positive():
    assert validate(5) == True

def test_validate__zero():
    assert validate(0) == False

def test_validate__negative():
    assert validate(-5) == False

# After (parametrized)
@pytest.mark.parametrize("value,expected", [
    pytest.param(5, True, id="positive"),
    pytest.param(0, False, id="zero"),
    pytest.param(-5, False, id="negative"),
])
def test_validate(value, expected):
    tested = Validator()
    result = tested.validate(value)
    assert result == expected
```

#### D. Add Missing IDs

Add or improve `pytest.param` IDs:

```python
# Before
@pytest.mark.parametrize("x,y,expected", [
    (2, 3, 5),
    (0, 0, 0),
])

# After
@pytest.mark.parametrize("x,y,expected", [
    pytest.param(2, 3, 5, id="positive_numbers"),
    pytest.param(0, 0, 0, id="zeros"),
])
```

### 6. Validate Improvements (PARALLEL AGENTS)

**CRITICAL**: After making improvements, validate that the test file follows all guidelines before running tests. Use 6 focused validation agents running IN PARALLEL to ensure thorough checking.

Spawn ALL of these agents simultaneously using Task tool in a SINGLE message:

#### Agent 1: validate-variable-names
```
Validate variable naming in test file: <test_file_path>

Check for:
- `tested` variable: must be used before method calls
- `result` variable: must store return values (not output, ret, actual)
- `expected` variable: must store expected values (not inlined)
- `exp_*` prefix: for multiple expected values (not expected_*)

Report ALL violations with file:line references.
```

#### Agent 2: validate-mock-objects
```
Validate mock object usage in test file: <test_file_path>

Check for:
- MagicMock used as return objects (should be SimpleNamespace)
- Look for: mock_response = MagicMock(), mock_request = MagicMock()
- Check if they have attributes set or are used in side_effect

Report ALL violations with file:line references.
```

#### Agent 3: validate-mock-verification
```
Validate mock verification in test file: <test_file_path>

Check that EVERY mock has mock_calls verification:
- All @patch mocks must have assert mock.mock_calls == exp_calls
- All MagicMock() objects must be verified
- Parametrized tests are NOT exempt

Report ALL unverified mocks with file:line references.
```

#### Agent 4: validate-pytest-fixtures
```
Validate pytest fixture usage in test file: <test_file_path>

Check for:
- Mocking print instead of using capsys fixture
- Look for: @patch("module.print"), mock_print parameter

Report ALL violations with file:line references.
```

#### Agent 5: validate-forbidden-patterns
```
Validate for forbidden patterns in test file: <test_file_path>

Check for:
- assert_called_with(), assert_called(), etc.
- return_value usage (should be side_effect)
- TestMainBlock or __main__ tests
- len(mock_calls), mock_calls[0] indexing
- @pytest.mark.parametrize("string" instead of tuple

Report ALL violations with file:line references.
```

#### Agent 6: validate-test-structure
```
Validate test structure in test file: <test_file_path>
Source file: <source_file_path>

Check for:
- Test function naming: test_method or test_method__case
- Test class naming: TestClassName
- Test ordering matches source file
- Docstrings present

Report ALL violations with file:line references.
```

**After all agents complete**:
1. Collect all violations from all agents
2. If violations found:
   - Fix each violation in the test file
   - Re-run validation to confirm fixes
3. Only proceed to run tests when all validations pass

### 7. Run Tests

After validation passes, run the tests:

```bash
uv run pytest <test_file_path> -v
```

Ensure all tests still pass. If failures occur:
- Analyze error messages
- Fix issues
- Re-run tests

### 8. Check Coverage

```bash
uv run pytest <test_file_path> --cov=<source> --cov-report=term-missing -v
```

Verify coverage improved. If still < 100%:
- Identify remaining gaps
- Add more tests
- Re-check coverage

### 9. Generate Improvement Report

Provide detailed before/after summary:

```
=== Test Improvement Report ===

File: <test_file_path>
Status: ✅ Improved Successfully

BEFORE:
  Coverage: 75%
  Critical Issues: 3
  Warnings: 7
  Test Functions: 8

AFTER:
  Coverage: 100% ✅
  Critical Issues: 0 ✅
  Warnings: 0 ✅
  Test Functions: 12 (+4 new tests)

CHANGES APPLIED:

✅ Fixed Critical Issues:
  • Replaced 3 instances of return_value with side_effect
  • Replaced 4 instances of MagicMock response objects with SimpleNamespace
  • Replaced 8 instances of mock_print with capsys fixture
  • Replaced 2 instances of assert_called_with() with mock_calls
  • Added 3 missing mock_calls verifications
  • Deleted TestMainBlock class (tests for __main__ block are forbidden)

✅ Improved Coverage (75% → 100%):
  • Added test_process_data__empty_input for line 78
  • Added test_process_data__invalid_format for lines 102-105
  • Added test__helper for private method (lines 120-125)
  • Added test_validate__none_value for line 91

✅ Refactored for Guidelines:
  • Reordered 4 tests to match source file order
  • Fixed variable naming in 8 tests:
    - Added `tested` variable to 5 tests (was calling methods directly on class)
    - Renamed 'output'/'ret'/'actual' to 'result' in 4 tests
    - Added 'expected' variable in 6 tests (was inlining values in assertions)
    - Renamed 'expected_calls' to 'exp_calls' in 3 tests
  • Parametrized 3 similar tests into 1 function
  • Added descriptive IDs to 4 parametrize decorators

✅ Code Quality:
  • Lines modified: 48
  • Lines added: 35
  • Tests more maintainable and consistent

VERIFICATION:
  ✅ All tests pass (12/12)
  ✅ 100% code coverage achieved
  ✅ No guideline violations
  ✅ Ready for production

NEXT STEPS:
  1. Review changes: <test_file_path>
  2. Commit improved tests
  3. Apply same improvements to other test files if needed
```

## Edge Cases

### Tests Already Compliant

If tests already follow all guidelines and have 100% coverage:

```
✅ Tests Already Excellent!

File: <test_file_path>
Coverage: 100%
Guideline Compliance: 100%

No improvements needed. Your tests are well-written and comprehensive.

Optional enhancements:
- Add more edge case tests for robustness
- Add performance tests if applicable
- Document complex test scenarios
```

### Cannot Determine Source File

If source file can't be found:

```
Warning: Cannot determine source file for <test_file>

Limited improvements available:
- Fix mock usage issues
- Improve parametrization
- Fix naming conventions

Cannot improve:
- Test ordering (need source file)
- Coverage gaps (need source file)

Provide source file path if available.
```

### Tests Have Import Errors

If tests can't run due to import errors:

```
Error: Tests cannot run due to import errors

Error output:
<error message>

Fix import errors before improving tests:
1. Check source file imports
2. Verify test file import paths
3. Ensure dependencies installed

Run again after fixing imports.
```

## Interactive Mode

For complex improvements, use interactive mode:

1. Show improvement plan
2. Ask user which categories to fix:
   - [ ] Critical issues
   - [ ] Coverage gaps
   - [ ] Refactor for guidelines
   - [ ] Enhance quality

3. Apply selected improvements
4. Show results
5. Ask if further improvements needed

## Related Commands

- **validate-tests**: Check current state before improving
- **generate-tests**: Re-generate tests from scratch if needed

## Notes for Claude

- **FIRST: Validate type annotations** - This is mandatory and must happen BEFORE any test improvements. If any parameter or return type is missing annotations in the source file, STOP and report the issue. Do NOT proceed with test improvements.
- **Run 6 validation agents IN PARALLEL for initial validation** - This identifies current issues
  - validate-variable-names, validate-mock-objects, validate-mock-verification
  - validate-pytest-fixtures, validate-forbidden-patterns, validate-test-structure
  - Spawn all agents in a SINGLE message with multiple Task tool calls for true parallelism
- **Show improvement plan** before making changes
- **Get user confirmation** for significant refactoring
- **Delegate to test-generator agent** for creating new tests
- **Be incremental**: Fix critical issues first, then improve coverage
- **Preserve working tests**: Don't break existing good tests
- **Run 6 validation agents IN PARALLEL after improvements** - This verifies fixes before running tests
  - Same 6 agents as initial validation
  - Fix ALL violations before proceeding to run tests
- **Verify improvements**: Always run tests and coverage after validation passes
- **Explain changes**: Help user understand why each improvement matters
- **If coverage is still < 100%** after improvements, explain why and what's still missing

## Example Usage

```
User: /pytest:improve-tests tests/utils/test_parser.py

Claude:
1. Validates type annotations in source file
2. Spawns 6 validation agents IN PARALLEL for initial validation (single message, 6 Task calls):
   - validate-variable-names → finds 3 violations
   - validate-mock-objects → finds 2 MagicMock response objects
   - validate-mock-verification → finds 1 unverified mock
   - validate-pytest-fixtures → finds 0 violations
   - validate-forbidden-patterns → finds 1 return_value usage
   - validate-test-structure → finds 0 violations
3. Analyzes: 85% coverage, 2 critical issues, 4 warnings
4. Presents improvement plan
5. User confirms
6. Fixes critical mock issues
7. Delegates to test-generator agent for 3 new tests for uncovered lines
8. Refactors variable names
9. Reorders tests
10. Spawns 6 validation agents IN PARALLEL to verify fixes (single message, 6 Task calls)
11. Fixes any remaining violations found by agents
12. Runs tests: all pass
13. Checks coverage: 100%
14. Generates improvement report
```

## Integration with Guidelines

This command applies all pytest-guidelines:
- **Naming**: Enforces test_method, test_method__case
- **Variables** (MANDATORY - use these exact names):
  - `tested`: assign class/instance FIRST, call methods on it
  - `result`: store return values (NEVER use `output`, `ret`, `actual`)
  - `expected`: store expected values (NEVER inline in assertions)
  - `exp_*`: prefix for multiple expected values (NEVER use `expected_*`)
- **Mocks**: Fixes side_effect, mock_calls usage
  - Replace `MagicMock` for return objects with `SimpleNamespace`
  - Replace `mock_print` with pytest's `capsys` fixture
  - CRITICAL: ALL mocks must be verified with `mock_calls` in EVERY test including parametrized tests
- **Order**: Aligns tests with source file order
- **Parametrize**: Refactors similar tests
  - Parametrized tests MUST verify mocks - if verification differs per case, use separate tests instead
- **Coverage**: Adds tests to reach 100%
- **Quality**: Improves maintainability and clarity
- **Excluded**: `if __name__ == "__main__":` blocks - DELETE any tests for these (e.g., TestMainBlock)
