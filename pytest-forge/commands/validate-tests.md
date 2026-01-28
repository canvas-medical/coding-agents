---
name: validate-tests
description: Validate pytest test files for compliance with guidelines and coverage requirements
argument-hint: "<test_path>"
allowed-tools: ["Read", "Grep", "Bash", "Glob", "Task"]
---

# Validate Pytest Tests

Check existing pytest test files for compliance with strict testing guidelines and measure code coverage.

## Objective

Analyze test file(s) to verify:
- Naming conventions (tests, variables)
- Mock usage patterns (side_effect, mock_calls)
- Test ordering matches source code
- Parametrization usage
- Coverage requirements (100% target)

Provide detailed report of violations and suggestions for improvements.

## Prerequisites

Before validating:
1. Ensure pytest and pytest-cov are installed
2. Load the **pytest-guidelines** skill for reference

## Input Validation

### Check Argument

The command requires one argument: path to test file or directory.

If no argument provided:
```
Error: Test path required.

Usage: /pytest:validate-tests <test_path>

Examples:
  /pytest:validate-tests tests/utils/test_parser.py
  /pytest:validate-tests tests/
```

### Validate Path

Check that the provided path:
- Exists and is readable
- Is either a `.py` file or a directory
- For file: must start with `test_` prefix
- For directory: should contain test files

If invalid:
```
Error: Invalid test path: <path>

Test files must:
- Start with test_ prefix
- Be in tests/ directory
- Have .py extension
```

## Implementation Steps

### 1. Validate Type Annotations (MANDATORY PRE-CHECK)

**CRITICAL**: Before proceeding with test validation, verify that the source code has complete type annotations. This step is mandatory and cannot be skipped.

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

Cannot validate tests for <test_file> - source file <source_file> has missing type annotations.

The following functions/methods have incomplete type annotations:

  <class_name>.<method_name>:
    - Parameter '<param_name>' is missing type annotation
    - Return type is missing

  <function_name>:
    - Parameter '<param_name>' is missing type annotation

Please add type annotations to all parameters and return values in the source file before validating tests.

Example of properly typed code:
    def process(self, data: list[str], validate: bool = True) -> dict[str, int]:
        ...

After adding type annotations, run this command again.
```

**Only proceed to the next step if ALL functions/methods have complete type annotations.**

### 2. Determine Scope

**If path is a file**:
- Validate single test file
- Find corresponding source file

**If path is a directory**:
- Find all test files recursively: `tests/**/test_*.py`
- Validate each file separately
- Provide aggregate report

### 2. Find Test Files

Use Glob to find test files:

```bash
# For directory
find <directory> -name "test_*.py" -type f
```

Or use Glob tool:
```
pattern: **/test_*.py
path: <directory>
```

### 3. Delegate to Focused Validation Agents (IN PARALLEL)

**CRITICAL**: Use multiple focused validation agents running IN PARALLEL to ensure thorough validation. Each agent checks ONE specific aspect deeply.

For each test file, spawn ALL of these agents simultaneously using Task tool:

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

**Why parallel agents are critical**:
- Each agent focuses deeply on ONE rule category
- No rule is overlooked because the agent is "context-limited"
- Violations are found exhaustively, not partially
- Faster execution through parallelism

**After all agents complete**:
- Collect all violations from all agents
- Deduplicate if needed
- Categorize by severity
- Generate unified report

### 4. Run Coverage Analysis

For each test file, run coverage check:

```bash
uv run pytest <test_file_path> --cov=<source_file_or_module> --cov-report=term-missing -v
```

**Parse coverage output**:
- Extract coverage percentage
- Identify missing lines
- Note untested code paths

### 5. Check Test Execution

Run the tests to ensure they pass:

```bash
uv run pytest <test_file_path> -v
```

**Check for**:
- Test failures
- Errors or exceptions
- Warnings

### 6. Aggregate Results

If validating multiple files:
- Collect violations from all files
- Calculate aggregate coverage
- Identify common issues
- Prioritize critical violations

## Validation Report Format

Provide structured report:

```
=== Pytest Test Validation Report ===

File: <test_file_path>
Source: <source_file_path>
Tests: N functions
Coverage: X%

NAMING CONVENTIONS: [✅ Pass | ⚠️ Issues | ❌ Fail]
  ✅ Test function naming correct

VARIABLE NAMING: [✅ Pass | ⚠️ Issues | ❌ Fail]
  ❌ tests/test_parser.py:52 - Calling Parser.parse() directly without `tested` variable
  ❌ tests/test_parser.py:67 - Using 'output' instead of 'result' for return value
  ❌ tests/test_parser.py:89 - Inlining expected value in assertion instead of using 'expected' variable
  ❌ tests/test_parser.py:95 - Using 'expected_calls' instead of 'exp_calls'
  ✅ tests/test_parser.py:78 - Correctly uses `tested`, `result`, `expected`

MOCK USAGE: [✅ Pass | ⚠️ Issues | ❌ Fail]
  ❌ tests/test_parser.py:19 - Using MagicMock for response object - use SimpleNamespace instead
  ❌ tests/test_parser.py:35 - Mocking print with @patch("module.print") - use capsys fixture instead
  ❌ tests/test_parser.py:37 - Mock 'mock_environ' not verified with mock_calls (parametrized test)
  ❌ tests/test_parser.py:37 - Mock 'mock_path_cls' not verified with mock_calls (parametrized test)
  ❌ tests/test_parser.py:67 - Using return_value instead of side_effect
  ❌ tests/test_parser.py:72 - Using forbidden mock.assert_called_with()
  ✅ tests/test_parser.py:95 - All mocks properly verified with mock_calls

TEST ORDERING: [✅ Pass | ⚠️ Issues | ❌ Fail]
  ⚠️ Test order doesn't match source file
     Expected order: test_add, test_subtract, test_multiply
     Actual order: test_multiply, test_add, test_subtract

FORBIDDEN PATTERNS: [✅ Pass | ⚠️ Issues | ❌ Fail]
  ❌ tests/test_parser.py:459 - TestMainBlock class tests `__main__` block (should be deleted)
  ✅ No forbidden patterns found

PARAMETRIZATION: [✅ Pass | ⚠️ Issues | ❌ Fail]
  ✅ Uses @pytest.mark.parametrize appropriately
  ⚠️ tests/test_parser.py:89 - Missing id parameter in pytest.param
  ⚠️ tests/test_parser.py:92 - ID 'test1' not descriptive (use 'valid_input')

COVERAGE: [✅ Pass | ⚠️ Issues | ❌ Fail]
  ❌ Coverage: 85% (target: 100%)
  Missing lines in <source_file>:
    - Lines 45-48: Error handling path not tested
    - Line 67: Edge case with empty input not tested

TEST EXECUTION: [✅ Pass | ⚠️ Issues | ❌ Fail]
  ✅ All tests pass
  ✅ No warnings

---

SUMMARY:
  Critical Issues: 2
  Warnings: 4
  Coverage: 85% (needs +15%)

PRIORITY FIXES:
  1. [CRITICAL] Replace return_value with side_effect (test_parser.py:67)
  2. [CRITICAL] Replace assert_called_with() with mock_calls check (test_parser.py:72)
  3. [HIGH] Add tests for missing lines 45-48
  4. [MEDIUM] Reorder tests to match source file
  5. [LOW] Add descriptive IDs to parametrize decorators

RECOMMENDATION:
  Run /pytest:improve-tests tests/test_parser.py to automatically fix issues.
```

## Multi-File Report

When validating a directory:

```
=== Pytest Test Validation Report ===

Directory: tests/
Test files: N files
Total tests: M functions
Aggregate coverage: X%

FILES ANALYZED:
  ✅ tests/utils/test_parser.py - 100% coverage, no issues
  ⚠️  tests/utils/test_validator.py - 85% coverage, 3 warnings
  ❌ tests/models/test_user.py - 70% coverage, 2 critical issues

COMMON ISSUES:
  - 5 files using return_value instead of side_effect
  - 3 files using forbidden assert_called_with()
  - 2 files with test ordering issues

OVERALL ASSESSMENT:
  Critical Issues: 5
  Warnings: 12
  Average Coverage: 85%

TOP PRIORITY:
  1. Fix critical mock issues in test_user.py
  2. Improve coverage in test_validator.py and test_user.py
  3. Standardize naming conventions across all files

NEXT STEPS:
  1. Fix critical issues first
  2. Run /pytest:improve-tests on files with < 100% coverage
  3. Re-validate after fixes: /pytest:validate-tests tests/
```

## Success Criteria

Validation is successful when:
- ✅ All naming conventions followed
- ✅ All mock usage follows guidelines
- ✅ Test order matches source code
- ✅ Parametrization used appropriately
- ✅ 100% code coverage achieved
- ✅ All tests pass

## Error Handling

### Test File Not Found

```
Error: Test file not found: <path>

Possible causes:
- File doesn't exist
- Path is incorrect
- File not in tests/ directory

Generate tests first: /pytest:generate-tests <source_file>
```

### Source File Cannot Be Determined

If test file exists but source file can't be found:
```
Warning: Cannot determine source file for <test_file>

Test ordering and coverage checks will be limited.
Provide source file path manually if needed.
```

### Coverage Command Fails

If coverage analysis fails:
```
Error: Coverage analysis failed

Possible causes:
- pytest-cov not installed (run /pytest:setup)
- Source file not found
- Import errors in tests

Error output:
<error message>
```

### No Tests Found

If path contains no test files:
```
Warning: No test files found in <path>

Expected: files matching test_*.py pattern

Generate tests: /pytest:generate-tests <source_file>
```

## Output Formats

### Concise Mode (Default)

Show summary with critical issues only.

### Detailed Mode

Show all violations with context and recommendations.

### JSON Mode (Optional)

Provide structured JSON for programmatic use:

```json
{
  "file": "tests/test_parser.py",
  "coverage": 85,
  "issues": [
    {
      "severity": "critical",
      "category": "mock_usage",
      "line": 67,
      "message": "Using return_value instead of side_effect",
      "fix": "Change mock.return_value = X to mock.side_effect = [X]"
    }
  ]
}
```

## Related Commands

After validation:
- **improve-tests**: Automatically fix issues and improve coverage
- **generate-tests**: Re-generate tests for uncovered code

## Notes for Claude

- **FIRST: Validate type annotations** - This is mandatory and must happen BEFORE any test validation. If any parameter or return type is missing annotations in the source file, STOP and report the issue. Do NOT proceed with test validation.
- **Always load pytest-guidelines skill** for reference during validation
- **CRITICAL: Use ALL 6 focused validation agents IN PARALLEL** - This ensures thorough validation
  - validate-variable-names
  - validate-mock-objects
  - validate-mock-verification
  - validate-pytest-fixtures
  - validate-forbidden-patterns
  - validate-test-structure
- **Spawn all agents in a SINGLE message** with multiple Task tool calls for true parallelism
- **Provide file:line references** for all violations
- **Prioritize issues**: Critical → High → Medium → Low
- **Be specific** in recommendations
- **Run coverage analysis** even if other checks pass
- **Don't just report problems** - suggest concrete fixes
- **For directories**, summarize common patterns across files
- **If tests fail**, that's a critical issue - report prominently
- **Cross-reference guidelines** when explaining violations

## Example Usage

```
User: /pytest:validate-tests tests/utils/test_parser.py

Claude:
1. Loads pytest-guidelines skill
2. Reads test file
3. Finds source file: src/utils/parser.py
4. Validates type annotations in source file
5. Spawns 6 focused validation agents IN PARALLEL (single message, 6 Task calls):
   - validate-variable-names → finds 3 violations
   - validate-mock-objects → finds 5 violations (MagicMock used as response)
   - validate-mock-verification → finds 2 unverified mocks
   - validate-pytest-fixtures → finds 0 violations
   - validate-forbidden-patterns → finds 1 violation (return_value)
   - validate-test-structure → finds 0 violations
6. Collects and aggregates all violations
7. Runs coverage: 85%
8. Runs tests: all pass
9. Generates detailed report with ALL violations found
10. Suggests running improve-tests command
```

## Integration with Guidelines

This command enforces all pytest-guidelines:
- **Naming**: test_method, test_method__case
- **Variables** (MANDATORY - use these exact names):
  - `tested`: assign class/instance FIRST, call methods on it
  - `result`: store return values (NEVER use `output`, `ret`, `actual`)
  - `expected`: store expected values (NEVER inline in assertions)
  - `exp_*`: prefix for multiple expected values (NEVER use `expected_*`)
- **Mocks**: side_effect, mock_calls only
  - Use `SimpleNamespace` NOT `MagicMock` for return objects (HTTP responses)
  - Use `capsys` fixture to capture print output - NEVER mock `print`
  - CRITICAL: ALL mocks must be verified with `mock_calls` in EVERY test including parametrized tests
- **Order**: Match source file method order
- **Parametrize**: pytest.param with id
  - Parametrized tests MUST verify mocks - if verification differs per case, use separate tests instead
- **Coverage**: 100% target
- **Forbidden**: assert_called_with() and similar methods
- **Excluded**: `if __name__ == "__main__":` blocks - flag tests for these as violations to be deleted
