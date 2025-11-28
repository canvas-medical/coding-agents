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

## Documentation

Reference the `testing_context.txt` file in this skill directory for:
- Mocking patterns for Canvas SDK
- Test structure guidelines
- Coverage checking procedures
- Common test scenarios
