---
name: setup
description: Configure pytest and coverage tools for the project with 100% coverage threshold
argument-hint: ""
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob"]
---

# Setup Pytest Environment

Configure the current project for pytest testing with coverage tracking and 100% coverage requirement.

## Objective

Set up pytest and pytest-cov dependencies, configure pytest and coverage settings in `pyproject.toml`, create test directory structure, and verify the setup works correctly.

## Prerequisites Check

First, verify that `uv` package manager is installed:

```bash
uv --version
```

If `uv` is not installed, inform the user that `uv` is required and provide installation instructions:
- Visit: https://docs.astral.sh/uv/getting-started/installation/
- Or run: `curl -LsSf https://astral.sh/uv/install.sh | sh`

Do NOT proceed if `uv` is not installed.

## Implementation Steps

Execute these steps in order:

### 1. Check Project Structure

Verify the project has a `pyproject.toml` file. If not present, ask the user if they want to create one:

```bash
ls pyproject.toml
```

If missing and user agrees, create a minimal `pyproject.toml`:

```toml
[project]
name = "project-name"
version = "0.1.0"
dependencies = []

[project.optional-dependencies]
dev = []
```

### 2. Add Pytest Dependencies

Add pytest and pytest-cov as development dependencies:

```bash
uv add --dev pytest pytest-cov
```

This command:
- Adds pytest and pytest-cov to `[project.optional-dependencies.dev]` section
- Updates or creates `uv.lock` file
- Installs the dependencies

### 3. Configure Pytest

Add or update pytest configuration in `pyproject.toml`. Use the Edit or Write tool to add this section:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --strict-markers"
```

### 4. Configure Coverage

Add or update coverage configuration in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["."]
branch = true
omit = [
    "tests/*",
    "**/__pycache__/*",
    "**/.*",
    "**/venv/*",
    "**/env/*"
]

[tool.coverage.report]
fail_under = 100
show_missing = true
skip_covered = false
precision = 2
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

**Key settings**:
- `fail_under = 100`: Requires 100% code coverage
- `show_missing = true`: Shows which lines aren't covered
- `source = ["."]`: Measures coverage for all project code
- `omit = ["tests/*"]`: Excludes test files from coverage

### 5. Create Test Directory

Create the `tests/` directory if it doesn't exist:

```bash
mkdir -p tests
```

Create an empty `tests/__init__.py` file to make it a package:

```bash
touch tests/__init__.py
```

### 6. Verify Setup

Run pytest to verify the configuration works:

```bash
uv run pytest --version
```

This should display the pytest version, confirming installation.

Try running tests (will find no tests yet, which is expected):

```bash
uv run pytest tests/ -v
```

Expected output: `collected 0 items` (this is correct for a new setup)

### 7. Test Coverage Command

Verify coverage works:

```bash
uv run pytest tests/ --cov=. --cov-report=term-missing
```

This should run without errors (0 tests, 0 coverage is expected initially).

## Success Criteria

Setup is successful when:
- ✅ `uv` is installed and working
- ✅ `pytest` and `pytest-cov` are added to dev dependencies
- ✅ `pyproject.toml` contains pytest and coverage configuration
- ✅ `tests/` directory exists with `__init__.py`
- ✅ `uv run pytest --version` executes without error
- ✅ `uv run pytest tests/` executes without error

## Output to User

After successful setup, provide this summary:

```
✅ Pytest environment configured successfully!

Setup complete:
- pytest and pytest-cov installed
- Configuration added to pyproject.toml
- Test directory created: tests/
- Coverage threshold set to 100%

Next steps:
1. Generate tests for your source files:
   /pytest:generate-tests <source_file>

2. Run tests:
   uv run pytest tests/ -v

3. Check coverage:
   uv run pytest tests/ --cov=. -v

The project is now ready for test-driven development!
```

## Error Handling

### `uv` Not Found

If `uv` is not installed:
```
❌ Error: 'uv' package manager not found.

Please install uv first:
https://docs.astral.sh/uv/getting-started/installation/

Or run: curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Permission Errors

If permission errors occur when creating directories or files:
- Inform the user about the permission issue
- Suggest running with appropriate permissions
- Provide the exact command that failed

### Existing Configuration Conflicts

If `pyproject.toml` already has pytest or coverage configuration:
- Read the existing configuration
- Ask user if they want to merge or replace
- Preserve user's existing settings unless they conflict with guidelines

## Related Skills

For detailed testing guidelines after setup:
- Reference the **pytest-guidelines** skill for comprehensive testing standards
- Run `/pytest:generate-tests <file>` to create tests following the guidelines

## Notes for Claude

- This command modifies `pyproject.toml` - always read it first before making changes
- Use Edit tool to update existing sections, Write tool only for new files
- The 100% coverage requirement is strict - don't suggest lowering it
- Verify each step completes successfully before proceeding
- If any step fails, stop and report the error clearly
- Don't create example test files - that's what generate-tests command does
