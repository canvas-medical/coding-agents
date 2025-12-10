# Run Evals

Execute eval cases to verify that security and database performance review commands correctly detect known issues.

## Instructions

### 1. Discover Eval Cases

```bash
echo "=== Discovering eval cases ==="
find .claude/evals -name "expected.json" -type f | while read f; do
  eval_dir=$(dirname "$f")
  eval_name=$(basename "$eval_dir")
  echo "Found: $eval_name"
done
```

### 2. Run Each Eval

For each eval case discovered (e.g., case_001, case_002, case_003):

**CRITICAL: DO NOT read expected.json or case_index.md - that would invalidate the eval by biasing your review.**

#### Step 2a: Navigate to Eval Case

```bash
cd .claude/evals/{eval_name}
```

#### Step 2b: Run BOTH Review Commands

**IMPORTANT: You MUST use the SlashCommand tool to invoke the review commands.**

Run both reviews on each eval case - the comparison script will determine which findings are relevant:

```
Use the SlashCommand tool with command: "/security-review-cpa"
```

Save the security review output to `../.cpa-workflow-artifacts/{eval_name}-security-review.md`.

```
Use the SlashCommand tool with command: "/database-performance-review"
```

Save the database review output to `../.cpa-workflow-artifacts/{eval_name}-database-review.md`.

#### Step 2c: Compare Results

Use the comparison script to evaluate whether the reviews detected the expected findings:

```bash
uv run --with requests python .claude/scripts/compare_review_results.py \
  --security-report ../.cpa-workflow-artifacts/{eval_name}-security-review.md \
  --database-report ../.cpa-workflow-artifacts/{eval_name}-database-review.md \
  --expected .claude/evals/{eval_name}/expected.json
```

The script will:
1. Read the generated review reports
2. Read the expected findings from expected.json
3. Use Anthropic API to determine if each expected finding was detected
4. Return a JSON result with pass/fail for each finding

#### Step 2d: Return to Base

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

| Eval | Expected Findings | Detected | Status |
|------|-------------------|----------|--------|
| case_001 | 1 | ? | ? |
| case_002 | 2 | ? | ? |
| case_003 | 2 | ? | ? |

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

## Adding New Evals

See `.claude/evals/README.md` for instructions on creating new eval cases.

Eval case names should be sequential (case_004, case_005, etc.) to avoid revealing what they test.
Update `.claude/evals/case_index.md` with the new case's category and purpose (CPA cannot read this file).
