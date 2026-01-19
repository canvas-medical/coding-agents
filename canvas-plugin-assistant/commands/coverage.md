# Test Coverage Report

Run tests with coverage and offer to improve if below 90%.

## Prerequisites

This command requires:
- `CPA_RUNNING` must be set to 1
- `CPA_WORKSPACE_DIR` must be set
- `CPA_PLUGIN_DIR` must be set to an existing plugin directory

## Instructions

### Step 1: Check CPA_RUNNING

```bash
echo $CPA_RUNNING
```

**If CPA_RUNNING is not set to "1":**
- STOP and tell the user:
  ```
  ERROR: CPA_RUNNING is not set to 1.

  Please /exit and run:
  export CPA_RUNNING=1 && claude

  Then run this command again.
  ```

### Step 2: Check CPA_WORKSPACE_DIR

```bash
echo $CPA_WORKSPACE_DIR
```

**If CPA_WORKSPACE_DIR is not set:**
- STOP and tell the user:
  ```
  ERROR: CPA_WORKSPACE_DIR is not set.

  Please /exit, navigate to your workspace directory, and run:
  export CPA_WORKSPACE_DIR=$(pwd) && claude

  Then run this command again.
  ```

### Step 3: Check CPA_PLUGIN_DIR

```bash
echo $CPA_PLUGIN_DIR
```

**If CPA_PLUGIN_DIR is not set or empty:**
- STOP and tell the user:
  ```
  ERROR: CPA_PLUGIN_DIR is not set.

  This command requires an existing plugin. To work on a plugin:

  1. /exit
  2. Run: export CPA_PLUGIN_DIR=$CPA_WORKSPACE_DIR/[plugin-name]
  3. Run: claude

  To see available plugins, list subdirectories in your workspace.
  ```

**If CPA_PLUGIN_DIR is set:**
- Verify it's a subdirectory of CPA_WORKSPACE_DIR and exists:

```bash
if [[ "$CPA_PLUGIN_DIR" != "$CPA_WORKSPACE_DIR"/* ]]; then
  echo "ERROR: CPA_PLUGIN_DIR must be a subdirectory of CPA_WORKSPACE_DIR"
  echo "  CPA_PLUGIN_DIR: $CPA_PLUGIN_DIR"
  echo "  CPA_WORKSPACE_DIR: $CPA_WORKSPACE_DIR"
  exit 1
elif [ ! -d "$CPA_PLUGIN_DIR" ]; then
  echo "ERROR: CPA_PLUGIN_DIR points to non-existent directory: $CPA_PLUGIN_DIR"
  exit 1
else
  cd "$CPA_PLUGIN_DIR"
  echo "Working in plugin: $(basename "$CPA_PLUGIN_DIR")"
fi
```

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
