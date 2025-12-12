---
name: testing
description: Unit test authoring and coverage checking for Canvas plugins
---

# Testing Skill

This skill provides guidance for writing unit tests and checking coverage for Canvas plugins.

## When to Use This Skill

Use this skill when:
- Writing unit tests for plugin handlers
- Checking test coverage
- Mocking Canvas SDK components
- Setting up test fixtures

## Opinionated Testing Rules

**These rules are non-negotiable. Follow them exactly.**

### 1. Tests at Container Level, Mirroring Source Structure

**CRITICAL:** The `tests/` directory MUST be at the container level (parallel to the inner plugin folder), NOT inside the inner folder.

```
my-plugin-name/                       # Container folder (kebab-case)
├── pyproject.toml                    # Container level
├── tests/                            # Container level - NOT inside inner folder!
│   ├── conftest.py
│   ├── protocols/
│   │   ├── test_vitals_handler.py    # mirrors inner/protocols/vitals_handler.py
│   │   └── test_lab_handler.py       # mirrors inner/protocols/lab_handler.py
│   ├── api/
│   │   └── test_routes.py            # mirrors inner/api/routes.py
│   └── helpers/
│       └── test_utils.py             # mirrors inner/helpers/utils.py
└── my_plugin_name/                   # Inner folder (snake_case)
    ├── CANVAS_MANIFEST.json
    ├── README.md
    ├── protocols/
    │   ├── vitals_handler.py
    │   └── lab_handler.py
    ├── api/
    │   └── routes.py
    └── helpers/
        └── utils.py
```

**Key points:**
- `tests/` is a **sibling** to the inner plugin folder, not a child
- Test file structure mirrors the inner folder's source structure
- Test file name = `test_` + source file name

**WRONG structure (DO NOT DO THIS):**
```
my-plugin-name/
└── my_plugin_name/
    ├── protocols/
    │   └── handler.py
    └── tests/                        # WRONG - tests inside inner folder!
        └── test_handler.py
```

**If you find tests inside the inner folder, move them:**
```bash
mv my_plugin_name/tests ./tests
```

### 2. One Test File Per Source File

- Each source file gets exactly ONE test file
- Test file name = `test_` + source file name
- Example: `protocols/handler.py` → `tests/protocols/test_handler.py`

### 3. Use Mocks for Isolation

- Every external dependency MUST be mocked
- Tests must never make real API calls or database queries
- Use `unittest.mock.MagicMock` and `patch` for all mocking

### 4. Always Verify Mock Calls

**Every mock MUST have its calls verified.** Do not just mock and forget.

```python
# REQUIRED - verify mock was called correctly, with the right arguments, for all calls
with patch("canvas_sdk.v1.data.patient.Patient.objects") as mock_objects:
    mock_objects.get.return_value = mock_patient

    handler.compute()

    calls = [call.get(id="patient-123"), call.get(id="patient-456")]
    assert mock_objects.mock_calls == calls  # REQUIRED
```

### 5. Exclude Tests from Coverage

The `pyproject.toml` MUST exclude test files from coverage measurement:

```toml
[tool.coverage.run]
source = ["plugin_name"]
omit = ["tests/*", "*/tests/*"]

[tool.coverage.report]
omit = ["tests/*", "*/tests/*"]
```

## Quick Commands

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=plugin_name --cov-report=term-missing --cov-branch

# Run tests with HTML coverage report
uv run pytest --cov=plugin_name --cov-report=html
```

## Coverage Target

Aim for **90% coverage** on plugin code. If coverage is below 90%, offer to write additional tests.

## Test Data Approach

**Use manual mocking with MagicMock, NOT factory libraries.** Factories don't exist for Canvas plugins. Create test data directly in fixtures and customize per-test. See `testing_context.txt` for patterns.

## Documentation

Reference the `testing_context.txt` file in this skill directory for:
- Mocking patterns for Canvas SDK
- Test structure guidelines
- Coverage checking procedures
- Common test scenarios

## After Tests Are Complete

**Do NOT stop after writing tests.** Once tests pass with adequate coverage:

1. Tell the user tests are complete and coverage target is met
2. **Immediately offer to deploy for UAT:**

> "Tests are passing with X% coverage. The next step is to deploy the plugin to a Canvas instance for user acceptance testing. Ready to deploy?"

3. Use the `/deploy` command to guide deployment and log monitoring

**Always drive toward the next step.** The workflow is: Implement → Test → Deploy → UAT
