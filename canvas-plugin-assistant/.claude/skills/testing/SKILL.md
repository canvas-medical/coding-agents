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

### 1. Directory Structure Mirrors Source Code

The `tests/` directory structure MUST mirror the source code structure exactly:

```
plugin_name/
├── plugin_name/
│   ├── protocols/
│   │   ├── vitals_handler.py
│   │   └── lab_handler.py
│   ├── api/
│   │   └── routes.py
│   └── helpers/
│       └── utils.py
├── tests/
│   ├── protocols/
│   │   ├── test_vitals_handler.py    # mirrors vitals_handler.py
│   │   └── test_lab_handler.py       # mirrors lab_handler.py
│   ├── api/
│   │   └── test_routes.py            # mirrors routes.py
│   ├── helpers/
│   │   └── test_utils.py             # mirrors utils.py
│   └── conftest.py
└── pyproject.toml
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
# REQUIRED - verify mock was called correctly
with patch("canvas_sdk.v1.data.patient.Patient.objects") as mock_objects:
    mock_objects.get.return_value = mock_patient

    handler.compute()

    mock_objects.get.assert_called_once_with(id="patient-123")  # REQUIRED
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
uv run pytest --cov=plugin_name --cov-report=term-missing

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
