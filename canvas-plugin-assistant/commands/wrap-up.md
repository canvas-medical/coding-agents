# Wrap Up Plugin

Final checklist before calling a plugin "done" for this version.

## Instructions

### Step 1: Validate Environment

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_cpa_environment.py" --require-plugin-dir
```

**If the script exits with an error:** STOP and show the user the error message. Do NOT proceed.

**If validation passes:** Continue with the steps below.

```bash
cd "$CPA_PLUGIN_DIR"
```

Run through each checklist item, report findings, and give a clear verdict.

### Step 2: Project Structure Validation

**Before any other checks, verify the plugin has the correct folder structure.**

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify_plugin_structure.py {plugin_name}
```

**If structure validation fails:**
- Report all errors to the user
- Offer to fix each issue (move files to correct locations)
- Do NOT proceed with other checks until the structure is correct

**Common fixes:**

Determine the inner folder name:
```bash
CONTAINER=$(basename "$PWD")
INNER=$(echo "$CONTAINER" | tr '-' '_')
```

| Issue | Fix |
|-------|-----|
| CANVAS_MANIFEST.json at container level | `mv CANVAS_MANIFEST.json $INNER/` |
| tests/ inside inner folder | `mv $INNER/tests ./` |
| No inner folder | Re-run `canvas init` or restructure manually |

---

### 1. Security Review

Run the comprehensive security review command:

```
/cpa:security-review
```

This covers:
- **Plugin API Server Security** - SimpleAPI/WebSocket authentication and authorization
- **FHIR API Client Security** - Token scopes, patient-scoped tokens, token storage
- **Application Scope** - Manifest scope alignment with token usage
- **Secrets Declaration** - All tokens properly declared

The command saves a timestamped report to `.cpa-workflow-artifacts/` and offers to fix any issues found.

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
- Offer to run `/cpa:coverage` to address gaps

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

### 8. Application Icon Check

**If the plugin has an Application component, verify it has an icon.**

Check CANVAS_MANIFEST.json for applications:

```bash
INNER=$(basename "$PWD" | tr '-' '_')
grep -A 10 '"applications"' "$INNER/CANVAS_MANIFEST.json" 2>/dev/null
```

**If applications exist:**

For each application entry, verify:
- [ ] The `icon` field is present
- [ ] The icon file exists in the inner plugin directory
- [ ] The icon is a PNG file (48x48 recommended)
- [ ] The filename matches what's in the manifest

Check icon files:
```bash
INNER=$(basename "$PWD" | tr '-' '_')
ls -lh "$INNER"/assets/*.png 2>/dev/null || echo "No PNG icons found"
```

**If Application exists but no icon:**
- Offer to create an icon using the icon-generation skill
- Invoke `Skill(skill="icon-generation")` to generate an appropriate icon
- Update the manifest with the icon filename

**If no applications:** Mark as N/A.

### 9. License Check

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

If the user says to remove it, delete the LICENSE file and remove any license section from the README.

### 10. Final Verdict

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
| Application Icon | ✅ Present / ⚠️ Created / N/A | ... |
| License | ✅ None / ⚠️ Removed / ✅ Intentional | ... |

### Verdict

**✅ Ready to ship** - You can call it done for this version.

OR

**❌ Changes needed:**
1. Fix the security issue in `/api/webhook.py` - missing auth check
2. Run `/cpa:coverage` to improve test coverage to 90%
3. Update README to remove reference to deleted handler
```

**Save the wrap-up report:**

Create a timestamp and save the report:

```bash
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
REPORT_FILE="$CPA_PLUGIN_DIR/.cpa-workflow-artifacts/wrap-up-report-$TIMESTAMP.md"

# Create the report (replace {plugin_name} with actual plugin name)
cat > "$REPORT_FILE" <<'REPORT_END'
# Wrap-Up Report: {plugin_name}

**Generated:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Reviewer:** Claude Code (CPA)

## Wrap-Up Summary

| Check | Status | Notes |
|-------|--------|-------|
| Project Structure | {status} | {notes} |
| Plugin API Security | {status} | {notes} |
| FHIR Client Security | {status} | {notes} |
| DB Performance | {status} | {notes} |
| Type checking | {status} | {notes} |
| Coverage | {status} | {notes} |
| Debug Logs | {status} | {notes} |
| Dead Code | {status} | {notes} |
| README | {status} | {notes} |
| Application Icon | {status} | {notes} |
| License | {status} | {notes} |

## Verdict

{verdict_text}

REPORT_END

echo "Wrap-up report saved: $REPORT_FILE"
```

Replace the placeholders with actual results from each check.

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

### 11. Wrap-Up Complete

**After all checks pass (or issues are resolved), the plugin is ready.**

The plugin changes will be automatically committed and pushed when you exit this Claude Code session (via a SessionEnd hook that detects the wrap-up report).

## CPA Workflow

This command is the **final step** in the Canvas Plugin Assistant workflow:

```
/cpa:check-setup      →  Verify environment tools (uv, unbuffer)
/cpa:new-plugin       →  Create plugin from requirements
/cpa:deploy           →  Deploy to Canvas instance for UAT
/cpa:coverage         →  Check test coverage (aim for 90%)
/cpa:security-review  →  Comprehensive security audit
/cpa:database-performance-review  →  Database query optimization
/cpa:wrap-up          →  Final checklist before delivery  ← YOU ARE HERE
```

After wrap-up passes, the plugin is ready to ship!
