# Test Coverage Report

Run tests with coverage and offer to improve if below 90%.

## Instructions

### Working Directory Setup

**Before starting, navigate to the workspace and identify the plugin directory:**

```bash
workspace="$(python3 "/media/DATA/anthropic_plugins/coding-agents/canvas-plugin-assistant/scripts/get-workspace-dir.py")"
(cd "$workspace" && find . -maxdepth 1 -type d ! -name '.' ! -name '.*' | wc -l)
```

**If 0 subdirectories:**
- Report error: "This command can only work when a plugin has been created. Please run /cpa:new-plugin first."
- STOP - do not proceed

**If 1 subdirectory:**
- Automatically change to that directory
- Tell the user: "Working in plugin directory: {subdirectory_name}"

**If multiple subdirectories:**
- Use AskUserQuestion to ask which plugin directory to work on
- Change to that directory: `cd {selected_directory}`

---

1. **Run pytest with coverage:**

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
WORKSPACE_DIR=$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/get-workspace-dir.py")
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
