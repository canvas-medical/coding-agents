# CPA Eval Cases

This directory contains eval cases for testing the CPA review commands (`/security-review-cpa` and `/database-performance-review`).

## Structure

Each eval case is a mini plugin with a known issue that the review command should detect:

```
evals/
├── security/
│   ├── hardcoded-secret/
│   │   ├── hardcoded_secret/          # Inner folder (plugin structure)
│   │   │   ├── CANVAS_MANIFEST.json
│   │   │   └── protocols/handler.py
│   │   └── expected.json              # What the review should find
│   └── patient-scope-mismatch/
│       └── ...
└── database/
    └── n-plus-one-query/
        └── ...
```

## expected.json Format

```json
{
  "eval_name": "hardcoded-secret",
  "review_command": "security-review-cpa",
  "description": "Plugin with hardcoded API token in source code",
  "expected_findings": [
    {
      "category": "Secrets Declaration",
      "severity": "HIGH",
      "description": "Hardcoded JWT token should be detected",
      "must_detect": true
    }
  ],
  "expected_verdict": "ISSUES FOUND"
}
```

### Fields

- `eval_name`: Human-readable identifier
- `review_command`: Which command to run (`security-review-cpa` or `database-performance-review`)
- `description`: What vulnerability/issue this eval tests
- `expected_findings`: Array of issues the review MUST detect
  - `category`: Report section where finding should appear
  - `severity`: HIGH, MEDIUM, or LOW
  - `description`: What the finding should describe
  - `must_detect`: If true, test fails if not detected
- `expected_verdict`: Expected overall result ("PASS", "ISSUES FOUND", or "N/A")

## Running Evals

Use the `/run-evals` command to execute all eval cases and generate a results report.

## Adding New Eval Cases

1. Create a directory: `.claude/evals/{category}/{eval-name}/`
2. Create the inner plugin folder with snake_case name
3. Add minimal plugin files demonstrating the issue
4. Create `expected.json` with expected findings
5. Run `/run-evals` to verify detection
