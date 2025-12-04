# Wrap Up Plugin

Final checklist before calling a plugin "done" for this version.

## Instructions

Run through each checklist item, report findings, and give a clear verdict.

### 1. Security Review

Check if the plugin has any SimpleAPI or WebSocket handlers:

```bash
grep -r "SimpleAPI\|WebSocket" --include="*.py" .
```

**If handlers exist:**
- Invoke the **api-security** skill
- Review all API handlers for authentication and authorization
- Report any security issues found

**If no handlers:** Mark security as N/A.

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

### 3. Test Coverage

Run coverage check:

```bash
uv run pytest --cov=. --cov-report=term-missing
```

**If coverage < 90%:**
- Tell the user coverage needs improvement
- Offer to run `/coverage` to address gaps

**If coverage ≥ 90%:** Mark tests as passing.

**If no tests exist:** Flag this as a blocker.

### 4. Debug Log Cleanup

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

### 5. README Review

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

### 6. License Check

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

### 7. Final Verdict

After all checks, present a summary:

```markdown
## Wrap-Up Summary

| Check | Status | Notes |
|-------|--------|-------|
| Security | ✅ Pass / ⚠️ Issues / N/A | ... |
| DB Performance | ✅ Pass / ⚠️ N+1 Issues / N/A | ... |
| Coverage | ✅ 92% / ❌ 78% | ... |
| Debug Logs | ✅ Clean / ⚠️ Removed X logs | ... |
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

### 8. Export Session History

**Save a record of this development session for future reference.**

Run the history export script:

```bash
python .claude/scripts/export-session-history.py
```

This creates `.claude/artifacts/claude-history-{sessionId}.txt` containing all messages from this session. The file is overwritten on each run, so there's one complete file per session.

### 9. Final Git Commit and Push

**After all checks pass (or issues are resolved), commit and push the final state.**

```bash
git add .
git commit -m "complete {plugin_name} v{version} wrap-up"
git push
```

Use concise declarative voice for commit messages:
- "complete vitals-alert v0.1.0 wrap-up"
- "finalize plugin, remove debug logs"
- "complete wrap-up, update README"

## CPA Workflow

This command is the **final step** in the Canvas Plugin Assistant workflow:

```
/check-setup     →  Verify environment tools (uv, unbuffer)
/new-plugin      →  Create plugin from requirements
/deploy          →  Deploy to Canvas instance for UAT
/coverage        →  Check test coverage (aim for 90%)
/wrap-up         →  Final checklist before delivery  ← YOU ARE HERE
```

After wrap-up passes, the plugin is ready to ship!
