---
name: generate-tests
description: Generate comprehensive pytest unit tests for a Python source file following strict guidelines
argument-hint: "<source_file>"
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Task"]
---

# Generate Pytest Tests

Generate comprehensive unit tests for a Python source file, following strict naming conventions, mock patterns, and aiming for 100% code coverage.

## Objective

Analyze a Python source file and generate or update its corresponding test file with:
- One test per method/function
- Proper naming conventions
- Comprehensive mock usage with `side_effect` and `mock_calls`
- Parametrization for multiple scenarios
- Tests ordered by method appearance in source
- 100% code coverage

## Prerequisites

Before generating tests:
1. Verify pytest is set up (if not, suggest running `/pytest:setup` first)
2. Ensure the source file exists and is readable
3. Load the **pytest-guidelines** skill for reference

## Input Validation

### Check Argument

The command requires one argument: the path to the Python source file.

If no argument provided:
```
Error: Source file path required.

Usage: /pytest:generate-tests <source_file>

Example: /pytest:generate-tests src/utils/parser.py
```

### Validate Source File

Check that the provided path:
- Exists and is readable
- Is a Python file (`.py` extension)
- Contains actual code (not empty)

If file doesn't exist:
```
Error: File not found: <path>

Please provide a valid Python source file path.
```

## Test File Path Determination

Calculate the test file path by mirroring the source directory structure in `tests/`:

**Examples**:
```
src/utils/parser.py → tests/utils/test_parser.py
app/models/user.py → tests/models/test_user.py
calculator.py → tests/test_calculator.py
```

**Rules**:
1. Mirror all directory structure under `tests/`
2. Prefix filename with `test_`
3. Maintain exact filename (including capitalization)

## Implementation Steps

### 1. Validate Type Annotations (MANDATORY PRE-CHECK)

**CRITICAL**: Before proceeding with test generation, verify that the source code has complete type annotations. This step is mandatory and cannot be skipped.

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

Cannot generate tests for <source_file> - missing type annotations.

The following functions/methods have incomplete type annotations:

  <class_name>.<method_name>:
    - Parameter '<param_name>' is missing type annotation
    - Return type is missing

  <function_name>:
    - Parameter '<param_name>' is missing type annotation

Please add type annotations to all parameters and return values before generating tests.

Example of properly typed code:
    def process(self, data: list[str], validate: bool = True) -> dict[str, int]:
        ...

After adding type annotations, run this command again.
```

**Only proceed to the next step if ALL functions/methods have complete type annotations.**

### 2. Read and Analyze Source File

Read the source file to understand:
- Classes defined
- Methods and functions (public and private)
- Method signatures and parameters
- Dependencies and imports
- External calls that need mocking

Use Grep or AST parsing to extract:
- All function/method names
- Method order of appearance
- Import statements
- External dependencies

### 2. Check for Existing Test File

Check if the test file already exists:

```bash
ls <test_file_path>
```

**If test file exists**:
- Read the existing test file
- Identify which methods already have tests
- Check if existing tests follow guidelines
- Plan to merge new tests and refactor non-compliant tests

**If test file doesn't exist**:
- Plan to create complete test file from scratch
- Create necessary directory structure

### 3. Delegate to Test-Generator Agent

Use the Task tool to invoke the **test-generator** agent with detailed instructions:

```
Generate comprehensive pytest tests for <source_file> following these requirements:

Source file: <source_file_path>
Test file: <test_file_path>
Existing tests: [Yes/No]

Requirements:
1. Create one test per method/function in source file
   - EXCEPTION: Do NOT create tests for `if __name__ == "__main__":` blocks (excluded from coverage)
2. Follow naming conventions:
   - test_<method_name> for single scenario
   - test_<method_name>__<case> for multiple scenarios
   - Include underscore prefix for private methods (test__private)
3. CRITICAL - Use mandatory variable names:
   - `tested`: ALWAYS assign the class or instance being tested to a `tested` variable FIRST
     - For class methods: `tested = ClassName` then `result = tested.method_name(...)`
     - For instance methods: `tested = ClassName()` then `result = tested.method_name(...)`
     - NEVER call methods directly on the class name without the `tested` variable
   - `result`: ALWAYS store return values in a variable named `result`
     - NEVER use `output`, `ret`, `actual`, `response`, or other names
   - `expected`: ALWAYS store expected values in a variable named `expected`
     - NEVER inline expected values in assertions
   - `exp_*`: Use `exp_` prefix for multiple expected values (e.g., `exp_calls`, `exp_output`)
     - NEVER use `expected_` prefix (too long)
4. Order tests to match source file method order
5. Use mocks for external dependencies:
   - side_effect for return values
   - Use `SimpleNamespace` NOT `MagicMock` for return objects (HTTP responses, etc.)
     - Example: `mock_post.side_effect = [SimpleNamespace(status_code=200, json=lambda: {"data": "value"})]`
     - Use lambdas for methods that return values
     - This avoids needing to verify mock_calls on the response object
   - Use pytest's `capsys` fixture to capture print output - NEVER mock `print`
     - Example: `captured = capsys.readouterr()` then `assert "message" in captured.out`
   - CRITICAL: Verify ALL mocks with mock_calls property in EVERY test
   - This includes parametrized tests - each mock MUST be verified even in parametrized tests
   - NEVER use assert_called_with() or similar
6. Use @pytest.mark.parametrize for multiple scenarios
   - IMPORTANT: Parametrized tests MUST still verify all mocks with mock_calls
   - If mock verification differs per parameter, use separate non-parametrized tests instead
7. Aim for 100% code coverage

[If existing tests]:
- Preserve existing compliant tests
- Add tests for uncovered methods
- Refactor non-compliant tests to follow guidelines
- Maintain source code method order

Generate the complete test file content.
```

The agent will:
- Analyze the source code structure
- Generate test functions for all methods
- Apply proper mocking patterns
- Use parametrization where appropriate
- Create comprehensive test coverage

### 4. Create Directory Structure

If test file doesn't exist, create necessary directories:

```bash
mkdir -p <test_directory_path>
```

### 5. Write or Update Test File

Based on agent output:

**If new file**:
- Use Write tool to create the test file
- Include proper imports
- Add module docstring
- Include all generated test functions

**If updating existing file**:
- Use Edit tool to add new tests
- Refactor non-compliant tests
- Maintain correct method order
- Preserve any custom fixtures or setup

### 6. Validate Generated Tests (PARALLEL AGENTS)

**CRITICAL**: Before running tests, validate that the generated test file follows all guidelines. Use 6 focused validation agents running IN PARALLEL to ensure thorough checking.

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

### 7. Verify Tests Run Successfully

Run the generated tests to ensure they work:

```bash
uv run pytest <test_file_path> -v
```

**If tests fail**:
- Read the error output
- Fix syntax errors or import issues
- Adjust mock configurations as needed
- Re-run until tests pass

### 8. Check Coverage

Run coverage analysis on the new tests:

```bash
uv run pytest <test_file_path> --cov=<source_file_without_extension> --cov-report=term-missing -v
```

Report coverage percentage and any missing lines.

**If coverage < 100%**:
- Identify uncovered lines
- Generate additional test cases
- Add tests for edge cases or error paths
- Re-run coverage check

## Success Output

After successful generation:

```
✅ Tests generated successfully!

Test file: <test_file_path>
Source file: <source_file_path>

Coverage: X%
Tests created: N test functions
- N new tests added
- M existing tests preserved
- K tests refactored

Test results:
<test output>

Next steps:
1. Review generated tests: <test_file_path>
2. Run tests: uv run pytest <test_file_path> -v
3. Check coverage: uv run pytest <test_file_path> --cov=<source> -v
4. Validate guidelines: /pytest:validate-tests <test_file_path>
```

If coverage is < 100%:

```
⚠️  Coverage: X% (target: 100%)

Missing coverage:
<list of uncovered lines>

Suggested actions:
1. Add tests for uncovered lines
2. Run /pytest:improve-tests <test_file_path> for suggestions
```

## Error Handling

### Import Errors

If tests have import errors:
- Check source file imports are correct
- Verify the test file uses correct import paths
- Adjust imports to match project structure

### Mock Configuration Errors

If mocks aren't configured correctly:
- Review external dependencies in source
- Check mock patches match actual import paths
- Ensure side_effect lists match call count

### Test Failures

If generated tests fail:
- Analyze failure messages
- Check method signatures match
- Verify mock return values are appropriate
- Adjust test logic as needed

## Edge Cases

### Empty Source File

If source file has no testable functions:
```
Warning: No testable functions found in <source_file>

The file may contain only:
- Constants
- Type definitions
- Empty classes

No tests generated.
```

### Source File with Only `__init__`

If a class only has `__init__` with no logic:
- Create minimal test for initialization if it sets attributes
- Skip if `__init__` is trivial (pass only)

### Async Functions

For async functions:
- Generate async test functions with `async def test_<name>`
- Use `@pytest.mark.asyncio` decorator
- Use `await` for async calls

### Class-Based Tests

For complex test scenarios, consider:
- Using pytest fixtures for shared setup
- Creating helper methods for common assertions
- Grouping related tests with clear comments

## Related Commands

After generating tests:
- **validate-tests**: Check guideline compliance
- **improve-tests**: Enhance test quality and coverage

## Notes for Claude

- **FIRST: Validate type annotations** - This is mandatory and must happen BEFORE any test generation. If any parameter or return type is missing annotations, STOP and report the issue. Do NOT proceed with test generation.
- **Always activate pytest-guidelines skill** before generating tests
- **Delegate heavy lifting to test-generator agent** - don't try to write all tests manually
- **CRITICAL: Run 6 validation agents IN PARALLEL after generation** - This step happens BEFORE running tests
  - validate-variable-names, validate-mock-objects, validate-mock-verification
  - validate-pytest-fixtures, validate-forbidden-patterns, validate-test-structure
  - Spawn all agents in a SINGLE message with multiple Task tool calls for true parallelism
  - Fix ALL violations before proceeding to run tests
- **Verify tests pass** before reporting success
- **Check coverage** and iterate if < 100%
- **Maintain source code method order** in test file
- **Read source file carefully** to identify all methods, including private ones
- **If existing tests exist**, be smart about merging - don't duplicate or delete good tests
- **Follow all naming conventions** strictly
- **Use mocks appropriately** - external dependencies only
- **Parametrize when appropriate** - multiple similar scenarios

## Example Usage

```
User: /pytest:generate-tests src/utils/calculator.py

Claude:
1. Reads src/utils/calculator.py
2. Validates type annotations on all methods
   - If missing: STOP and report which parameters/return types need annotations
   - If complete: proceed
3. Identifies methods: add, subtract, multiply, divide
4. Determines test path: tests/utils/test_calculator.py
5. Delegates to test-generator agent
6. Creates tests/utils/ directory
7. Writes tests/utils/test_calculator.py
8. Spawns 6 validation agents IN PARALLEL (single message, 6 Task calls):
   - validate-variable-names → checks tested, result, expected, exp_*
   - validate-mock-objects → checks SimpleNamespace vs MagicMock
   - validate-mock-verification → checks all mocks have mock_calls
   - validate-pytest-fixtures → checks capsys usage
   - validate-forbidden-patterns → checks return_value, assert_called_with, etc.
   - validate-test-structure → checks naming, ordering
9. Fixes any violations found by agents
10. Runs: uv run pytest tests/utils/test_calculator.py -v
11. Checks coverage: 100%
12. Reports success with summary
```

### Example: Type Validation Failure

```
User: /pytest:generate-tests canvas-plugin-assistant/scripts/session_end_orchestrator.py

Claude:
1. Reads session_end_orchestrator.py
2. Validates type annotations - FAILS

❌ Type Annotation Validation Failed

Cannot generate tests for session_end_orchestrator.py - missing type annotations.

The following functions/methods have incomplete type annotations:

  SessionEndOrchestrator.run:
    - Parameter 'hook_info' is missing type annotation

Please add type annotations to all parameters and return values before generating tests.

Example fix:
    @classmethod
    def run(cls, hook_info: HookInformation) -> None:
        ...

After adding type annotations, run this command again.
```

## Integration with Guidelines

This command implements the pytest-guidelines skill. Reference key guidelines:
- **Naming**: `test_method` or `test_method__case`
- **Variables** (MANDATORY - use these exact names):
  - `tested`: assign class/instance FIRST, call methods on it
  - `result`: store return values (NEVER use `output`, `ret`, `actual`)
  - `expected`: store expected values (NEVER inline in assertions)
  - `exp_*`: prefix for multiple expected values (NEVER use `expected_*`)
- **Mocks**: `side_effect`, `mock_calls` (never `assert_called_with`)
  - Use `SimpleNamespace` NOT `MagicMock` for return objects (HTTP responses)
  - Use `capsys` fixture to capture print output - NEVER mock `print`
  - CRITICAL: ALL mocks must be verified with `mock_calls` in EVERY test including parametrized tests
- **Parametrize**: `@pytest.mark.parametrize` with `pytest.param(id=...)`
  - Parametrized tests MUST verify mocks - if verification differs per case, use separate tests instead
- **Order**: Tests match source method order
- **Coverage**: 100% target
- **Excluded**: `if __name__ == "__main__":` blocks - do NOT generate tests for these
