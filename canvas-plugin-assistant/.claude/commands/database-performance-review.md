# Database Performance Review

Review Canvas plugin for database query performance issues, focusing on N+1 queries and ORM optimization.

## Instructions

Run through each check, document findings, generate a report, and offer to fix issues.

### 1. Check for Data Model Queries

Identify if the plugin queries Canvas data models:

```bash
grep -rn "\.objects\." --include="*.py" .
```

**If no queries found:** Mark as N/A and skip to report generation.

**If queries exist:** Continue with detailed analysis.

---

### 2. Invoke Database Performance Skill

Invoke the **database-performance** skill to analyze query patterns.

The skill will check for:
- **N+1 query patterns**: Queries executed inside loops
- **Missing `select_related()`**: Foreign key access without prefetching
- **Missing `prefetch_related()`**: Reverse relation or many-to-many access without prefetching
- **Unbounded queries**: `.all()` or `.filter()` without limits
- **Inefficient filtering**: Filtering in Python instead of database

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

---

### 4. Generate Performance Report

Create timestamp for report:
```python
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
```

Save report to `../.cpa-workflow-artifacts/db-performance-review-{timestamp}.md`:

```markdown
# Database Performance Review: {plugin_name}

**Generated:** {timestamp}
**Reviewer:** Claude Code (CPA)

## Summary

| Category | Status | Issues |
|----------|--------|--------|
| N+1 Query Patterns | ✅ Pass / ⚠️ X issues / N/A | ... |
| select_related Usage | ✅ Pass / ⚠️ X issues / N/A | ... |
| prefetch_related Usage | ✅ Pass / ⚠️ X issues / N/A | ... |
| Query Bounds | ✅ Pass / ⚠️ X issues / N/A | ... |

## Detailed Findings

### N+1 Query Patterns

[List any queries executed inside loops with file:line references]

### select_related Opportunities

[List foreign key accesses that should use select_related]

### prefetch_related Opportunities

[List reverse relation accesses that should use prefetch_related]

### Unbounded Queries

[List queries without limits that could return large result sets]

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

**If user chooses to fix:**
1. Fix N+1 patterns first (highest impact)
2. Add `select_related()` for foreign key access
3. Add `prefetch_related()` for reverse relations
4. Add query limits where appropriate
5. Re-run the full analysis (steps 1-4) and save a new timestamped report showing resolved status

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

This command can be run standalone or is called by `/wrap-up`:

```
/check-setup              →  Verify environment tools
/new-plugin               →  Create plugin from requirements
/deploy                   →  Deploy to Canvas instance for UAT
/coverage                 →  Check test coverage (aim for 90%), save report
/security-review          →  Comprehensive security audit
/database-performance-review  →  Database query optimization  ← YOU ARE HERE
/wrap-up                  →  Final checklist before delivery
```

After performance review passes, continue to `/wrap-up` for remaining checks.
