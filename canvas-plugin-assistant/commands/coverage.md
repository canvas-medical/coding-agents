# Test Coverage Report

Run tests with coverage and offer to improve if below 90%.

## Instructions

### Step 1: Validate Environment

```bash
uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_cpa_environment.py" --require-plugin-dir
```

**If the script exits with an error:** STOP and show the user the error message. Do NOT proceed.

**If validation passes:** Continue with the steps below.

```bash
cd "$CPA_PLUGIN_DIR"
```

### Step 2: Run pytest with coverage

```bash
uv run pytest --cov=. --cov-report=term-missing
```

2. **Parse the output** and extract:
   - Overall coverage percentage
   - Per-file coverage
   - Missing line numbers

3. **Generate Coverage Report**

Create a timestamp and get a workspace directory:
```bash
WORKSPACE_DIR=$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/get_plugin_dir.py")
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
```

Save report to `$WORKSPACE_DIR/.cpa-workflow-artifacts/coverage-report-$TIMESTAMP.md`:

```markdown
## Coverage Report

**Generated:** {timestamp}
**Reviewer:** Claude Code (CPA)

## Summary

**Overall:** {overall}%
**Target:** 90%
**Status:** {status}

| File | Coverage | Missing |
|------|----------|---------|
| ... | ...% | lines |

## Verdict

**✅ PASS** - Coverage meets 90% target

OR

**⚠️ NEEDS IMPROVEMENT** - Coverage below 90% target
```

Tell the user the report path.

4. **If coverage < 90%:**

Use AskUserQuestion:

```json
{
  "questions": [
    {
      "question": "Coverage is below 90%. Would you like me to write additional tests?",
      "header": "Improve coverage",
      "options": [
        {"label": "Yes", "description": "Write tests for uncovered lines"},
        {"label": "No", "description": "Coverage is acceptable for now"},
        {"label": "Show details", "description": "Show which lines need coverage"}
      ],
      "multiSelect": false
    }
  ]
}
```

5. **If the user says yes:**
   - Invoke the **testing skill**
   - Read the files with missing coverage
   - Write tests for uncovered lines
   - Re-run coverage to verify improvement

## Quick Report

If the user just wants a quick summary, show:

```
Coverage: 87% (target: 90%)
Files needing attention:
  - protocols/handler.py: 82% (lines 34-38, 67)
  - api/routes.py: 91% (line 23)
```

## CPA Workflow

This command is **step 4** in the Canvas Plugin Assistant workflow:

```
/cpa:check-setup      →  Verify environment tools (uv, unbuffer)
/cpa:new-plugin       →  Create plugin from requirements
/cpa:deploy           →  Deploy to Canvas instance for UAT
/cpa:coverage         →  Check test coverage (aim for 90%), save report  ← YOU ARE HERE
/cpa:security-review  →  Comprehensive security audit
/cpa:database-performance-review  →  Database query optimization
/cpa:wrap-up          →  Final checklist before delivery
```

After achieving 90% coverage, guide the user to the next step of the workflow.
