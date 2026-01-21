# Pytest Test Helper

A Claude Code plugin for generating and validating pytest unit tests following strict guidelines to achieve 100% code coverage.

## Features

- **Automated Test Generation**: Generate comprehensive unit tests from Python source files
- **Intelligent Merging**: Add tests to existing files while maintaining guideline compliance
- **Test Validation**: Check tests against custom guidelines and coverage requirements
- **Test Improvement**: Analyze and enhance existing tests
- **Project Setup**: Configure pytest and coverage tools with proper settings
- **Auto-Configuration Check**: Automatically detects unconfigured projects and prompts setup at session start

## Installation

### Prerequisites

- Claude Code CLI
- Python 3.8+
- `uv` package manager

### Install Plugin

```bash
# Copy to your Claude plugins directory
cp -r pytest-forge ~/.claude/plugins/

# Or use with --plugin-dir flag
cc --plugin-dir /path/to/pytest-forge
```

## Usage

> **💡 Auto-Configuration Check**
> When you start a Claude Code session in a Python project, the plugin automatically checks if pytest is configured. If not, Claude will ask if you'd like to run the setup command to configure pytest.

### 1. Setup Project

Configure pytest and coverage tools for your project:

```bash
/pytest:setup
```

This command will:
- Verify `uv` is installed
- Add `pytest` and `pytest-cov` dependencies
- Configure pytest and coverage in `pyproject.toml`
- Set 100% coverage threshold
- Create `tests/` directory

### 2. Generate Tests

Generate tests for a Python source file:

```bash
/pytest:generate-tests src/utils/parser.py
```

This creates `tests/utils/test_parser.py` with:
- One test per method/function
- Proper naming conventions
- Mock usage with side_effect and mock_calls
- Tests ordered by method appearance in source
- 100% coverage goal

### 3. Validate Tests

Check existing tests for guideline compliance:

```bash
# Validate single file
/pytest:validate-tests tests/utils/test_parser.py

# Validate entire test suite
/pytest:validate-tests tests/
```

Reports:
- Naming convention violations
- Mock usage issues
- Coverage gaps
- Guideline compliance

### 4. Improve Tests

Analyze and enhance existing tests:

```bash
/pytest:improve-tests tests/utils/test_parser.py
```

Suggests and applies:
- Refactoring to follow guidelines
- Additional test cases for edge cases
- Better parametrization
- Improved mock usage

## Testing Guidelines

This plugin enforces strict testing guidelines:

### Naming Conventions

- One test per method: `test_method_name`
- Include underscore prefix: `test__private_method`
- Multiple cases: `test_method_name__case_description`
- Tests ordered by method appearance in source code

### Variable Naming

- Tested object: `tested`
- Result checked: `result`
- Expected value: `expected`
- Multiple expected values: `exp_calls`, `exp_result`, etc.

### Mock Usage

- Use `side_effect` instead of `return_value`
- Verify ALL mocks with `mock_calls` property
- **FORBIDDEN**: `assert_called()`, `assert_called_with()`, etc.

Example:
```python
@patch('module.external_api')
def test_fetch_data(mock_api):
    mock_api.method.side_effect = [{"data": "value"}]

    tested = MyClass()
    result = tested.fetch_data()

    expected = {"data": "value"}
    assert result == expected

    exp_calls = [call.method()]
    assert mock_api.mock_calls == exp_calls
```

### Multiple Scenarios

Preference order:
1. `@pytest.mark.parametrize` with `pytest.param`
2. Loop within test function
3. Multiple `test_function__case` functions

### Coverage

- 100% code coverage required
- Run: `uv run pytest tests/ --cov=. -v`
- All code paths must be tested

## Commands Reference

| Command | Description | Arguments |
|---------|-------------|-----------|
| `/pytest:setup` | Configure project for pytest | None |
| `/pytest:generate-tests` | Generate tests for source file | `<source_file>` |
| `/pytest:validate-tests` | Validate test compliance | `<test_path>` |
| `/pytest:improve-tests` | Analyze and improve tests | `<test_file>` |

## Agents

The plugin includes specialized agents for test generation and validation:

### Test Generation
- **test-generator**: Analyzes source code and generates comprehensive tests

### Validation Sub-agents (run in parallel)
- **validate-variable-names**: Checks `tested`, `result`, `expected`, `exp_*` variable usage
- **validate-mock-objects**: Ensures SimpleNamespace is used instead of MagicMock for response objects
- **validate-mock-verification**: Verifies all mocks have `mock_calls` assertions
- **validate-pytest-fixtures**: Checks proper use of pytest fixtures (e.g., `capsys` instead of mocking print)
- **validate-forbidden-patterns**: Detects `assert_called_with()`, `return_value`, and other forbidden patterns
- **validate-test-structure**: Validates test naming, ordering, and structure

These agents are invoked by commands to ensure thorough and consistent test quality.

## Hooks

The plugin uses hooks to enhance workflow automation:

### SessionStart Hook

Automatically runs when a Claude Code session starts. Checks if:
1. The current directory is a Python project (has `.py` files, `pyproject.toml`, etc.)
2. Pytest is configured (looks for `pytest.ini`, `pyproject.toml` with pytest config, etc.)

If it's a Python project without pytest configuration, Claude will receive a system message prompting to offer setup assistance.

**Detection criteria:**
- **Python project**: Presence of `.py` files, `pyproject.toml`, `setup.py`, `requirements.txt`, or `Pipfile`
- **Pytest configured**: Presence of `pytest.ini`, pytest section in `pyproject.toml` or `setup.cfg`, or pytest in dependencies

**Note:** Hook runs at session start only. Restart Claude Code after running `/pytest:setup` for the hook to recognize the new configuration.

## Contributing

Issues and suggestions welcome at [repository URL].

## License

MIT
