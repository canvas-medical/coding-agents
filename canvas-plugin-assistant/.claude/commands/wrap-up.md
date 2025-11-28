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

### 2. Test Coverage

Run coverage check:

```bash
uv run pytest --cov=. --cov-report=term-missing
```

**If coverage < 90%:**
- Tell the user coverage needs improvement
- Offer to run `/coverage` to address gaps

**If coverage ≥ 90%:** Mark tests as passing.

**If no tests exist:** Flag this as a blocker.

### 3. README Review

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

### 4. License Check

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

### 5. Final Verdict

After all checks, present a summary:

```markdown
## Wrap-Up Summary

| Check | Status | Notes |
|-------|--------|-------|
| Security | ✅ Pass / ⚠️ Issues / N/A | ... |
| Coverage | ✅ 92% / ❌ 78% | ... |
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
