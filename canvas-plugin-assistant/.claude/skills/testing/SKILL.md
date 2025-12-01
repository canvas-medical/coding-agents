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

## After Tests Are Complete

**Do NOT stop after writing tests.** Once tests pass with adequate coverage:

1. Tell the user tests are complete and coverage target is met
2. **Immediately offer to deploy for UAT:**

> "Tests are passing with X% coverage. The next step is to deploy the plugin to a Canvas instance for user acceptance testing. Ready to deploy?"

3. Use the `/deploy` command to guide deployment and log monitoring

**Always drive toward the next step.** The workflow is: Implement → Test → Deploy → UAT
