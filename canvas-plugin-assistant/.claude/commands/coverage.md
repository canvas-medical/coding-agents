# Test Coverage Report

Run tests with coverage and offer to improve if below 90%.

## Instructions

1. **Run pytest with coverage:**

```bash
uv run pytest --cov=. --cov-report=term-missing
```

2. **Parse the output** and extract:
   - Overall coverage percentage
   - Per-file coverage
   - Missing line numbers

3. **Report findings** in this format:

```markdown
## Coverage Report

**Overall:** X%
**Target:** 90%
**Status:** PASS / NEEDS IMPROVEMENT

| File | Coverage | Missing |
|------|----------|---------|
| ... | ...% | lines |
```

4. **Save report to workflow artifacts:**

```python
from pathlib import Path
from datetime import datetime

output_dir = Path("../.cpa-workflow-artifacts")
output_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
report_file = output_dir / f"coverage-report-{timestamp}.md"

report_content = """## Coverage Report

**Overall:** {overall}%
**Target:** 90%
**Status:** {status}
**Generated:** {timestamp}

| File | Coverage | Missing |
|------|----------|---------|
{file_rows}
"""

report_file.write_text(report_content)
print(f"Report saved to {report_file}")
```

5. **If coverage < 90%:**

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

6. **If user says yes:**
   - Invoke the **testing skill**
   - Read the files with missing coverage
   - Write tests for uncovered lines
   - Re-run coverage to verify improvement

## Quick Report

If user just wants a quick summary, show:

```
Coverage: 87% (target: 90%)
Files needing attention:
  - protocols/handler.py: 82% (lines 34-38, 67)
  - api/routes.py: 91% (line 23)
```

## CPA Workflow

This command is **step 4** in the Canvas Plugin Assistant workflow:

```
/check-setup      →  Verify environment tools (uv, unbuffer)
/new-plugin       →  Create plugin from requirements
/deploy           →  Deploy to Canvas instance for UAT
/coverage         →  Check test coverage (aim for 90%), save report  ← YOU ARE HERE
/security-review-cpa  →  Comprehensive security audit
/wrap-up          →  Final checklist before delivery
```

After achieving 90% coverage, guide the user to `/wrap-up` for final checks before delivery.
