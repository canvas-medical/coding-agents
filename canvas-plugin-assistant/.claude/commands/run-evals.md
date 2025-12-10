# Run Evals

Execute eval cases to verify that security and database performance review commands correctly detect known issues.

## Instructions

### 1. Discover Eval Cases

```bash
echo "=== Discovering eval cases ==="
find .claude/evals -name "expected.json" | while read f; do
  eval_dir=$(dirname "$f")
  eval_name=$(basename "$eval_dir")
  category=$(basename $(dirname "$eval_dir"))
  echo "Found: $category / $eval_name"
done
```

### 2. Run Each Eval

For each eval case discovered:

#### Step 2a: Read Expected Outcomes

Read the `expected.json` file to understand:
- `review_command`: Which review to run (`security-review-cpa` or `database-performance-review`)
- `expected_findings`: What issues must be detected
- `expected_verdict`: Overall expected result

#### Step 2b: Navigate to Eval Case

```bash
cd .claude/evals/{category}/{eval_name}
```

#### Step 2c: Run the Appropriate Review

**For security evals (`review_command: "security-review-cpa"`):**
- Check for SimpleAPI/WebSocket endpoints and authentication
- Check for FHIR API client usage and token security
- Check manifest scope alignment
- Check secrets declaration and hardcoded tokens

**For database evals (`review_command: "database-performance-review"`):**
- Check for `.objects.` queries
- Look for N+1 patterns (queries in loops)
- Check for missing select_related/prefetch_related

Generate a review report and save it to the eval case directory as `review-output.md`.

#### Step 2d: Compare Results

Use the comparison script to evaluate whether the review detected the expected findings:

```bash
python .claude/scripts/compare_review_results.py \
  --report .claude/evals/{category}/{eval_name}/review-output.md \
  --expected .claude/evals/{category}/{eval_name}/expected.json
```

The script will:
1. Read the generated review report
2. Read the expected findings from expected.json
3. Use Anthropic API to determine if each expected finding was detected
4. Return a JSON result with pass/fail for each finding

#### Step 2e: Return to Base

```bash
cd -
```

### 3. Generate Eval Results Report

Create `../.cpa-workflow-artifacts/eval-results-{timestamp}.md`:

```markdown
# CPA Eval Results

**Run at:** {timestamp}
**Total evals:** {count}
**Passed:** {pass_count}
**Failed:** {fail_count}

## Summary

| Eval | Category | Command | Expected | Detected | Status |
|------|----------|---------|----------|----------|--------|
| hardcoded-secret | security | security-review-cpa | 1 HIGH | ? | ? |
| patient-scope-mismatch | security | security-review-cpa | 2 HIGH | ? | ? |
| n-plus-one-query | database | database-performance-review | 2 issues | ? | ? |

## Detailed Results

### {eval_name}

**Status:** PASS / FAIL

**Expected findings:**
- [ ] {severity}: {description}

**Review excerpt:**
> {relevant section from review output}

**Analysis:**
{explanation of what was or wasn't detected}
```

### 4. Report Final Status

**If all pass:**
```
============================================
EVAL SUITE PASSED
All {count} eval cases detected expected issues.
============================================
```

**If any fail:**
```
============================================
EVAL SUITE FAILED
{fail_count} of {total_count} eval cases did not detect all expected issues.

Failed evals:
- {eval_name}: {reason}

See detailed results at:
../.cpa-workflow-artifacts/eval-results-{timestamp}.md
============================================
```

## Available Eval Cases

### Security Evals

| Eval | Tests | Expected Finding |
|------|-------|------------------|
| hardcoded-secret | Hardcoded JWT token | HIGH: Token in source code |
| patient-scope-mismatch | Admin token in patient app | HIGH: Scope mismatch |

### Database Evals

| Eval | Tests | Expected Finding |
|------|-------|------------------|
| n-plus-one-query | Query inside loop | HIGH: N+1, MEDIUM: select_related |

## Adding New Evals

See `.claude/evals/README.md` for instructions on creating new eval cases.
