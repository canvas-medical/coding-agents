---
name: database-performance-review
description: Review Canvas plugin for database query performance issues, focusing on N+1 queries and ORM optimization.
---

# Database Performance Review

Review Canvas plugin for database query performance issues, focusing on N+1 queries and ORM optimization.

## Instructions

**Execution standard:** Run Python scripts and Python-based tooling with `uv run ...` (for scripts, `uv run python <script>.py ...`). Do not invoke bare `python` or `pip`.

### Step 1: Validate Environment

```bash
uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_cpa_environment.py" --require-plugin-dir
```

**If the script exits with an error:** STOP and show the user the error message. Do NOT proceed.

**If validation passes:** Continue with the steps below.

```bash
cd "$CPA_PLUGIN_DIR"
```

Run through each check, document findings, generate a report, and offer to fix issues.

### Step 2: Check for Data Model Queries

Identify if the plugin queries Canvas data models:

```bash
grep -rn "\.objects\." --include="*.py" .
```

**If no queries found:** Mark as N/A and skip to report generation.

**If queries exist:** Continue with detailed analysis.

---

### 2. Invoke Database Performance Skill

Invoke the **database-performance** skill to analyze data-access patterns across **all four failure modes** — not just N+1.

**Measure before you fix.** Query count is only one axis. Before proposing changes, identify the hot path (which endpoint/handler and how often it runs), then estimate **rows × row width per request** (memory) and **writes/effects per trigger** (amplification). Confirm the fix addresses the actual bottleneck — an oversized effect batch or a non-converging import is algorithmic and scaling workers/memory will not fix it.

The skill will check for:

*Read count (N+1):*
- **N+1 query patterns**: Queries executed inside loops
- **Missing `select_related()`**: Foreign key access without prefetching
- **Missing `prefetch_related()`**: Reverse relation or many-to-many access without prefetching
- **Inefficient filtering**: Filtering in Python instead of database

*Over-hydration / memory:*
- **Large text/JSON blob columns loaded but unused**: `Note._body` and other `*_body`/`*_json`/`*_data`/`payload`/`content`/document fields can dwarf the rest of the row → `.defer(...)` them, or `.only(...)`/`.values(...)` the small fields you use. Often the single biggest per-row cost.
- **`select_related` used only for an id**: joining a large relation (e.g. `note`) whose only downstream use is `.dbid`/`.id` → read the `<fk>_id` column instead
- **Full-instance hydration on hot list endpoints**: use `.values()`/`.only()` projections
- **Large queryset materialization / missing `.iterator()`**: `list()` wrapping or bare `.all()` iteration over large tables
- **Cache/state accumulator**: a resumable or cron-driven job that stores all results-so-far in one cache entry or in-process list (read → concat → re-serialize each call) → persist only the cursor/metadata (`offset`, `total`, `complete`), process each page in place
- **Unlocked serializer contract**: no `FIELDS` frozenset + test, so the card can silently regrow

*Write amplification:*
- **Redundant writes**: `.update()`/`.save()` in sync/webhook/reconcile paths with no content-hash change guard
- **Unbounded reconcile**: "delete all + recreate all" not scoped to the changed window/day
- **Non-converging / non-idempotent imports**: can re-create an already-imported record

*Canvas execution limits:*
- **Custom-data PK**: `Count("id")`/`order_by("id")` on a custom-data (SDK) model → use `dbid`
- **Effect-batch ceiling**: a handler emitting effects proportional to an unbounded queryset → chunk via queue + cron (one batch must stay under the 64 MB gRPC limit)

---

### 3. Manual Query Pattern Checks

Additionally, search for common anti-patterns:

**N+1 Queries (queries in loops):**
```bash
grep -rn "for.*in.*:" --include="*.py" . -A 5 | grep -E "\.objects\.|\.get\(|\.filter\("
```

**Missing select_related:**
```bash
grep -rn "\.patient\.\|\.provider\.\|\.encounter\.\|\.organization\." --include="*.py" .
```

Cross-reference with queries to see if `select_related()` is used.

**Missing prefetch_related:**
```bash
grep -rn "_set\.\|\.all()\|related_name" --include="*.py" .
```

**Large queryset materialization (list wrapping):**
```bash
grep -rn "list(.*\.objects\." --include="*.py" .
```

**Missing .iterator() on large table scans:**
```bash
grep -rn "\.objects\.all()" --include="*.py" . | grep -v "\.iterator("
```

**Missing .only() on broad queries:**
```bash
grep -rn "\.objects\.all()\|\.objects\.filter(" --include="*.py" . | grep -v "\.only("
```

Cross-reference `.only()` hits with actual field usage to confirm unnecessary columns are being fetched.

**Over-hydration — large text/JSON blob columns loaded without .defer()/.only():**
```bash
grep -rn "_body\|_json\|_html\|_data\|payload\|\.content" --include="*.py" .
```

For each model that has a large blob column (notably `Note._body`), check whether the query paths that fetch that model actually read the blob. If not, flag it — the query should `.defer("_body", ...)`, `.only(...)` the small fields, or `.values(...)` when only scalars are needed. A blob column loaded across hundreds/thousands of rows is a memory blowout even at a perfect query count. Also check `select_related`/`prefetch_related` that pull a relation whose rows carry a blob column.

**Cache/state accumulator (memory grows with total items, not per batch):**
```bash
grep -rn "cache.get\|cache.set\|json.loads\|json.dumps" --include="*.py" .
```

Look for a resumable/cron job that reads a cache blob, concatenates new items onto a stored list, and re-serializes the whole thing each call (e.g. `state["entries"] = state.get("entries", []) + new_rows`). That accumulates unbounded state and holds 2–3 copies at peak. Flag it — the job should persist only the cursor/metadata and process each page in place.

**Over-hydration — select_related used only for an id:**
```bash
grep -rn "select_related(" --include="*.py" .
```

For each hit, check the downstream use of the joined relation. If the only access is `.dbid`/`.id` (e.g. `appt.note.dbid`), flag it — read the `<fk>_id` column (`appt.note_id`) instead so the large related row is never hydrated.

**Custom-data PK — `id` used where the PK is `dbid`:**
```bash
grep -rn 'Count("id")\|order_by("id")\|values("id")\|F("id")' --include="*.py" .
```

For custom-data (SDK) models, `"id"` raises `FieldError` (PK is `dbid`). Cross-reference against models defined with the SDK base.

**Write amplification — writes in sync/webhook/reconcile paths:**
```bash
grep -rn "\.update(\|\.save(\|\.delete(" --include="*.py" .
```

In inbound/webhook/sync/reconcile code, flag writes that run unconditionally on every delivery. Look for a content-hash / change guard before the write; flag "delete all + recreate all" that isn't bounded to the changed window.

**Effect-batch ceiling — effects proportional to an unbounded queryset:**
```bash
grep -rn "for.*in.*\.objects" --include="*.py" . -A 8 | grep -E "\.apply\(|effects\.append|effects \+=|return effects"
```

Flag handlers that build an effect list by looping over all providers/patients/appointments and return it in one batch — chunk via queue + cron instead.

**Tests that mock the ORM (hide field/query errors):**
```bash
grep -rn "patch(.*objects\|Mock().*objects\|MagicMock" --include="*.py" ./tests 2>/dev/null
```

A query/field change covered only by a mocked queryset is not real coverage — the mock never resolves field names, so `Count("id")`-style bugs pass in CI.

---

### 4. Generate Performance Report

Get the workspace directory:
```bash
WORKSPACE_DIR=$(uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/get_plugin_dir.py")
```

Save report to `$WORKSPACE_DIR/.cpa-workflow-artifacts/db-performance-review.md`, overwriting any previous run:

```markdown
# Database Performance Review: {plugin_name}

**Generated:** {timestamp}
**Reviewer:** Claude Code (CPA)

## Summary

| Axis | Category | Status | Issues |
|------|----------|--------|--------|
| Read count | N+1 Query Patterns | ✅ Pass / ⚠️ X issues / N/A | ... |
| Read count | select_related / prefetch_related Usage | ✅ Pass / ⚠️ X issues / N/A | ... |
| Memory | Over-hydration (blob columns loaded / select_related for id only) | ✅ Pass / ⚠️ X issues / N/A | ... |
| Memory | Large queryset materialization / .iterator() / .only() | ✅ Pass / ⚠️ X issues / N/A | ... |
| Memory | Cache/state accumulator (cursor-only, no growing blob) | ✅ Pass / ⚠️ X issues / N/A | ... |
| Memory | Serializer contract locked | ✅ Pass / ⚠️ X issues / N/A | ... |
| Write | Redundant writes / content-hash guard | ✅ Pass / ⚠️ X issues / N/A | ... |
| Write | Bounded reconcile / idempotent sync | ✅ Pass / ⚠️ X issues / N/A | ... |
| Exec limit | Custom-data PK (dbid vs id) | ✅ Pass / ⚠️ X issues / N/A | ... |
| Exec limit | Effect-batch ceiling (queue+cron chunking) | ✅ Pass / ⚠️ X issues / N/A | ... |

## Detailed Findings

### N+1 Query Patterns

[List any queries executed inside loops with file:line references]

### select_related Opportunities

[List foreign key accesses that should use select_related]

### prefetch_related Opportunities

[List reverse relation accesses that should use prefetch_related]

### Unbounded Queries

[List queries without limits that could return large result sets]

### Large Queryset Materialization

[List instances of list() wrapping large querysets that should use .iterator()]

### Missing .iterator()

[List large table iterations (Patient, Note, Appointment, etc.) without .iterator(chunk_size=N)]

### Missing .only()

[List broad queries fetching all columns where only a few fields are used]

## Recommendations

| Priority | Issue | Location | Recommendation |
|----------|-------|----------|----------------|
| HIGH | N+1 query in loop | file:line | Move query outside loop or use prefetch |
| MEDIUM | Missing select_related | file:line | Add select_related('field') |
| LOW | ... | file:line | ... |

## Verdict

**✅ PASS** - No performance issues found

OR

**⚠️ ISSUES FOUND** - X issues require attention
```

Tell the user the report path.

---

### 5. Offer to Fix Issues

If issues were found, use AskUserQuestion:

```json
{
  "questions": [
    {
      "question": "Database performance review found issues. How would you like to proceed?",
      "header": "Performance fixes",
      "options": [
        {"label": "Fix all issues", "description": "Implement recommended optimizations now"},
        {"label": "Fix critical only", "description": "Only fix N+1 and HIGH priority issues"},
        {"label": "Review only", "description": "I'll review and fix manually"}
      ],
      "multiSelect": false
    }
  ]
}
```

**If the user chooses to fix:**
1. Fix N+1 patterns first (the highest impact)
2. Replace `list()` wrapping with `.iterator(chunk_size=100)` on large querysets
3. Add `.iterator(chunk_size=100)` to unbounded `.all()` iterations on large tables
4. Add `select_related()` for foreign key access
5. Add `prefetch_related()` for reverse relations
6. Add `.only()` to narrow column selection where few fields are used
7. Add query limits where appropriate
8. Re-run the full analysis (steps 1-4) and save a new timestamped report showing resolved status

---

## Example Fixes

### N+1 Query Pattern

**Before (N+1):**
```python
patients = Patient.objects.filter(active=True)
for patient in patients:
    # This executes a query for each patient!
    provider = patient.primary_provider
    log.info(f"Patient {patient.id} has provider {provider.name}")
```

**After (optimized):**
```python
patients = Patient.objects.filter(active=True).select_related('primary_provider')
for patient in patients:
    # No additional query - provider already loaded
    provider = patient.primary_provider
    log.info(f"Patient {patient.id} has provider {provider.name}")
```

### Reverse Relation Access

**Before (N+1):**
```python
encounters = Encounter.objects.filter(date=today)
for encounter in encounters:
    # This executes a query for each encounter!
    for diagnosis in encounter.diagnosis_set.all():
        process_diagnosis(diagnosis)
```

**After (optimized):**
```python
encounters = Encounter.objects.filter(date=today).prefetch_related('diagnosis_set')
for encounter in encounters:
    # No additional query - diagnoses already loaded
    for diagnosis in encounter.diagnosis_set.all():
        process_diagnosis(diagnosis)
```

---

## CPA Workflow

This command can be run standalone or is called by `/cpa:wrap-up`:

```
/cpa:check-setup              →  Verify environment tools
/cpa:new-plugin               →  Create plugin from requirements
/cpa:deploy                   →  Deploy to Canvas instance for UAT
/cpa:coverage                 →  Check test coverage (aim for 90%), save report
/cpa:security-review          →  Comprehensive security audit
/cpa:database-performance-review  →  Database query optimization  ← YOU ARE HERE
/cpa:wrap-up                  →  Final checklist before delivery
```

After a successful performance review, guide the user to the next step in the workflow.
