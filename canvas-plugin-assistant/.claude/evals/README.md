# CPA Eval Cases

This directory contains eval cases for testing the CPA review commands (`/security-review-cpa` and `/database-performance-review`).

## Structure

Each eval case is a mini plugin with a known issue that the review commands should detect. **Case names are intentionally non-descriptive to avoid biasing the review.**

```
evals/
├── case_001/
│   ├── CANVAS_MANIFEST.json
│   ├── protocols/handler.py (or api/portal.py)
│   └── expected.json
├── case_002/
│   └── ...
├── case_003/
│   └── ...
├── case_index.md              # Describes each case (CPA cannot read this)
└── README.md
```

## expected.json Format

```json
{
  "eval_name": "case_001",
  "description": "Brief description of what this tests",
  "expected_findings": [
    {
      "category": "Category name",
      "severity": "HIGH",
      "description": "What should be detected",
      "must_detect": true
    }
  ],
  "expected_verdict": "ISSUES FOUND"
}
```

### Fields

- `eval_name`: Case identifier (case_001, case_002, etc.)
- `description`: What vulnerability/issue this eval tests
- `expected_findings`: Array of issues the review MUST detect
  - `category`: Report section where finding should appear
  - `severity`: HIGH, MEDIUM, or LOW
  - `description`: What the finding should describe
  - `must_detect`: If true, test fails if not detected
- `expected_verdict`: Expected overall result ("PASS", "ISSUES FOUND", or "N/A")

## Running Evals

Use the `/run-evals` command to execute all eval cases and generate a results report.

**IMPORTANT:** The eval runner does NOT read expected.json or case_index.md before running reviews - this ensures blind evaluation. Both `/security-review-cpa` and `/database-performance-review` are run on each case, and the comparison script determines which findings are relevant.

Only the comparison script (run after the reviews complete) reads expected.json to evaluate results.

## Adding New Eval Cases

1. Determine the next case number (e.g., case_004)
2. Create directory: `.claude/evals/case_004/`
3. Add minimal plugin files demonstrating the issue:
   - `CANVAS_MANIFEST.json` with neutral name/description
   - Handler/API files as needed
4. Create `expected.json` with expected findings
5. Update `case_index.md` with the case's category and purpose (human reference only)
6. Run `/run-evals` to verify detection

**DO NOT use descriptive case names** - this would bias the reviews. Use sequential case_00N naming only.
