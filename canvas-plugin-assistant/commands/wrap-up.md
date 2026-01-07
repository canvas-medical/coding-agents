# Wrap Up Plugin

Final checklist before calling a plugin "done" for this version.

## Instructions

Run through each checklist item, report findings, and give a clear verdict.

### 0. Project Structure Validation

**Before any other checks, verify the plugin has the correct folder structure.**

```bash
# Get current directory name (should be container folder)
CONTAINER=$(basename "$PWD")
# Convert to snake_case for inner folder name
INNER=$(echo "$CONTAINER" | tr '-' '_')

echo "Checking project structure..."
echo "Container: $CONTAINER"
echo "Expected inner folder: $INNER"

ERRORS=0

# Check 1: Inner folder exists
if [ -d "$INNER" ]; then
    echo "OK: Inner folder '$INNER' exists"
else
    echo "ERROR: Inner folder '$INNER' not found"
    ERRORS=$((ERRORS + 1))
fi

# Check 2: CANVAS_MANIFEST.json is inside inner folder
if [ -f "$INNER/CANVAS_MANIFEST.json" ]; then
    echo "OK: CANVAS_MANIFEST.json in correct location"
elif [ -f "CANVAS_MANIFEST.json" ]; then
    echo "ERROR: CANVAS_MANIFEST.json at container level - should be inside $INNER/"
    ERRORS=$((ERRORS + 1))
else
    echo "ERROR: CANVAS_MANIFEST.json not found"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: tests/ at container level
if [ -d "tests" ]; then
    echo "OK: tests/ at container level"
elif [ -d "$INNER/tests" ]; then
    echo "ERROR: tests/ inside inner folder - should be at container level"
    ERRORS=$((ERRORS + 1))
else
    echo "WARNING: No tests/ directory found"
fi

# Check 4: pyproject.toml at container level
if [ -f "pyproject.toml" ]; then
    echo "OK: pyproject.toml at container level"
else
    echo "WARNING: pyproject.toml not found"
fi

# Check 5: No duplicate CANVAS_MANIFEST.json
if [ -f "CANVAS_MANIFEST.json" ] && [ -f "$INNER/CANVAS_MANIFEST.json" ]; then
    echo "ERROR: CANVAS_MANIFEST.json in BOTH locations - remove container level copy"
    ERRORS=$((ERRORS + 1))
fi

echo ""
if [ $ERRORS -gt 0 ]; then
    echo "STRUCTURE VALIDATION FAILED: $ERRORS error(s)"
else
    echo "Structure validation passed."
fi
```

**If structure validation fails:**
- Report all errors to the user
- Offer to fix each issue (move files to correct locations)
- Do NOT proceed with other checks until structure is correct

**Common fixes:**

| Issue | Fix |
|-------|-----|
| CANVAS_MANIFEST.json at container level | `mv CANVAS_MANIFEST.json $INNER/` |
| tests/ inside inner folder | `mv $INNER/tests ./` |
| No inner folder | Re-run `canvas init` or restructure manually |

---

### 1. Security Review

Run the comprehensive security review command:

```
/security-review
```

This covers:
- **Plugin API Server Security** - SimpleAPI/WebSocket authentication and authorization
- **FHIR API Client Security** - Token scopes, patient-scoped tokens, token storage
- **Application Scope** - Manifest scope alignment with token usage
- **Secrets Declaration** - All tokens properly declared

The command saves a timestamped report to `../.cpa-workflow-artifacts/` and offers to fix any issues found.

### 2. Database Performance Review

Check if the plugin queries Canvas data models:

```bash
grep -rn "\.objects\." --include="*.py" .
```

**If data queries exist:**
- Invoke the **database-performance** skill
- Look for N+1 query patterns (queries inside loops)
- Check for missing `select_related()` on foreign key access
- Check for missing `prefetch_related()` on reverse relations
- Report any performance issues found

**If no data queries:** Mark database performance as N/A.

### 3. Type checking

```bash
uv run mypy --config-file=mypy.ini .
```

**If errors exist:** Flag this as a blocker.

### 4. Test Coverage

Run coverage check:

```bash
uv run pytest --cov=. --cov-report=term-missing --cov-branch
```

**If coverage < 90%:**
- Tell the user coverage needs improvement
- Offer to run `/coverage` to address gaps

**If coverage ≥ 90%:** Mark tests as passing.

**If no tests exist:** Flag this as a blocker.

### 5. Debug Log Cleanup

Check for debug logging statements that were added during UAT troubleshooting:

```bash
grep -rn "\[DEBUG\]\|# DEBUG\|# TODO\|print(" --include="*.py" .
```

Also look for excessive logging that should be removed:

```bash
grep -rn "log\.\(info\|debug\|warning\)" --include="*.py" . | head -30
```

**Review each log statement:**
- Remove any `[DEBUG]` prefixed logs - these were for troubleshooting
- Remove `print()` statements - use logger instead or remove entirely
- Keep meaningful operational logs (errors, important business events)
- Remove verbose logs that dump full objects or contexts

**Good logs to keep:**
```python
log.info(f"Alert created for patient {patient_id}")
log.warning(f"Missing required field: {field_name}")
```

**Logs to remove:**
```python
log.info(f"[DEBUG] Full event context: {self.event.context}")  # Too verbose
log.info(f"[DEBUG] Entering compute()")  # Only useful during debugging
print(f"vitals: {vitals}")  # Should use logger, and too verbose
```

### 6. Dead Code Removal

Identify and remove unused code:

**Step 1: Trace from manifest declarations**

Read `CANVAS_MANIFEST.json` and verify every declared component exists and is used:
- Each `protocols` entry should have a corresponding file that's actually needed
- Each `commands` entry should reference code that exists
- Each `applications` entry should reference code that exists
- Each `content` entry should be used

Remove any declarations for code that no longer exists, and remove code that isn't declared in the manifest.

**Step 2: Check for unused imports**

```bash
grep -rn "^from\|^import" --include="*.py" .
```

Review each file for imports that aren't used in the code.

**Step 3: Check for unused functions and variables**

Look for:
- Functions defined but never called
- Variables assigned but never read
- Commented-out code blocks (delete them, git has history)
- Placeholder/scaffolding code from `canvas init` that wasn't needed

**Step 4: Remove dead tests**

Check that all test files test code that still exists:
- If a handler was removed, remove its tests
- If a function was renamed, update or remove old tests
- Remove `test_models.py` if it's just scaffolding

**Common dead code from scaffolding:**
- `protocols/my_protocol.py` - default placeholder if you renamed your protocol
- `test_models.py` - often unused scaffolding
- Unused effect imports (e.g., `AddTask` if you only use `AddBannerAlert`)
- Empty or stub methods that were never implemented

**Remove dead code rather than commenting it out.** Git history preserves old code if needed.

### 7. README Review

Read the plugin's README.md and verify:

**Must have:**
- [ ] Plugin name and brief description
- [ ] What events/triggers the plugin responds to
- [ ] What effects/actions the plugin produces
- [ ] Any configuration requirements
- [ ] Any external dependencies or integrations

**Must NOT have:**
- [ ] Outdated information (old handler names, removed features)
- [ ] TODOs or placeholder text
- [ ] Overly verbose explanations (keep it succinct)
- [ ] Internal implementation details users don't need

**Should match:**
- [ ] Handler list matches actual code
- [ ] Event types match CANVAS_MANIFEST.json
- [ ] Any environment variables mentioned are accurate

Update the README if issues are found.

### 8. License Check

Check for any license file or license mentions:

```bash
ls -la LICENSE* license* 2>/dev/null
grep -i "license\|MIT\|BSD\|Apache\|GPL" README.md 2>/dev/null
```

**⚠️ IMPORTANT: Plugins built for specific customers should NOT have open source licenses.**

If a LICENSE file exists or the README mentions a license (MIT, BSD, Apache, GPL, etc.), ask the user:

```json
{
  "questions": [
    {
      "question": "I found a license file or license mention. Is this plugin intended for open source distribution?",
      "header": "License check",
      "options": [
        {"label": "Yes, open source", "description": "This is a public/community plugin"},
        {"label": "No, remove it", "description": "This is a customer-specific plugin, remove the license"}
      ],
      "multiSelect": false
    }
  ]
}
```

If user says to remove it, delete the LICENSE file and remove any license section from the README.

### 9. Final Verdict

After all checks, present a summary:

```markdown
## Wrap-Up Summary

| Check | Status | Notes |
|-------|--------|-------|
| Project Structure | ✅ Pass / ❌ Errors | ... |
| Plugin API Security | ✅ Pass / ⚠️ Issues / N/A | ... |
| FHIR Client Security | ✅ Pass / ⚠️ Issues / N/A | ... |
| DB Performance | ✅ Pass / ⚠️ N+1 Issues / N/A | ... |
| Type checking | ✅ Pass / ❌ Errors | ... |
| Coverage | ✅ 92% / ❌ 78% | ... |
| Debug Logs | ✅ Clean / ⚠️ Removed X logs | ... |
| Dead Code | ✅ Clean / ⚠️ Removed X items | ... |
| README | ✅ Current / ⚠️ Updated | ... |
| License | ✅ None / ⚠️ Removed / ✅ Intentional | ... |

### Verdict

**✅ Ready to ship** - You can call it done for this version.

OR

**❌ Changes needed:**
1. Fix security issue in `/api/webhook.py` - missing auth check
2. Run `/coverage` to improve test coverage to 90%
3. Update README to remove reference to deleted handler
```

Use AskUserQuestion if any issues were found:

```json
{
  "questions": [
    {
      "question": "I found issues that should be addressed. How would you like to proceed?",
      "header": "Next steps",
      "options": [
        {"label": "Fix all issues", "description": "I'll address each issue now"},
        {"label": "Ship anyway", "description": "Accept current state, ship this version"},
        {"label": "Review details", "description": "Show me more about each issue"}
      ],
      "multiSelect": false
    }
  ]
}
```

### 10. Export Session History

**Save a record of this development session for future reference.**

Export the session history using Python:

```python
import json
from pathlib import Path

history_file = Path.home() / ".claude" / "history.jsonl"
lines = history_file.read_text().strip().split("\n")
last_entry = json.loads(lines[-1])
session_id = last_entry.get("sessionId")

display_texts = []
for line in lines:
    entry = json.loads(line)
    if entry.get("sessionId") == session_id:
        display = entry.get("display")
        if display:
            display_texts.append(display)

output_dir = Path("../.cpa-workflow-artifacts")
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / f"claude-history-{session_id}.txt"
output_file.write_text("\n".join(display_texts))
print(f"Exported {len(display_texts)} messages to {output_file}")
```

This creates `../.cpa-workflow-artifacts/claude-history-{sessionId}.txt` (one level above the plugin directory) containing all messages from this session.

### 11. Final Git Commit and Push

**After all checks pass (or issues are resolved), commit and push the final state.**

```bash
git add -A .
git commit -m "complete {plugin_name} v{version} wrap-up"
git push
```

**CRITICAL:** Always use `git add -A .` (with the trailing `.`) to scope changes to the current directory only. Never use `git add --all` or `git add -A` without a path - those commands stage changes across the entire repository, which can accidentally commit files outside the plugin directory.

Use concise declarative voice for commit messages:
- "complete vitals-alert v0.1.0 wrap-up"
- "finalize plugin, remove debug logs"
- "complete wrap-up, update README"

## CPA Workflow

This command is the **final step** in the Canvas Plugin Assistant workflow:

```
/check-setup      →  Verify environment tools (uv, unbuffer)
/new-plugin       →  Create plugin from requirements
/deploy           →  Deploy to Canvas instance for UAT
/coverage         →  Check test coverage (aim for 90%)
/security-review  →  Comprehensive security audit
/wrap-up          →  Final checklist before delivery  ← YOU ARE HERE
```

After wrap-up passes, the plugin is ready to ship!
