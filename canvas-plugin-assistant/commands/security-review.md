# Security Review

Comprehensive security audit for Canvas plugins covering both server-side API security and client-side FHIR API security.

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

Run through each security category, document findings, generate a report, and offer to fix issues.

### Step 2: Plugin API Server Security

Check if the plugin exposes any API endpoints:

```bash
grep -rn "SimpleAPI\|WebSocket\|SimpleAPIRoute" --include="*.py" .
```

**If endpoints exist:**
- Invoke the **plugin-api-server-security** skill
- Review all handlers for:
  - `authenticate()` method present
  - Proper credential validation (SessionCredentials, APIKeyCredentials, etc.)
  - Patient data access authorization
  - Use of `compare_digest()` for API keys
- Document findings with file:line references

**If no endpoints:** Mark as N/A

---

### 2. FHIR API Client Security

Check if the plugin calls FHIR APIs or uses Http():

```bash
grep -rn "Http()\|\.objects\.\|Authorization.*Bearer\|/api/" --include="*.py" .
```

**If FHIR client usage exists:**
- Invoke the **fhir-api-client-security** skill
- Check for:
  - Token storage (must be in the secrets, not hardcoded)
  - Token scope (minimum necessary)
  - Patient-scoped tokens for patient-facing apps
  - Token leakage in logs
- Document findings with the file:line references

**If no FHIR client usage:** Mark as N/A

---

### 3. Application Scope Review

Check the manifest for application scope:

```bash
grep -n "scope" */CANVAS_MANIFEST.json 2>/dev/null || grep -n "scope" CANVAS_MANIFEST.json 2>/dev/null
```

**Validate scope alignment:**

| Manifest `scope` | Token Requirement |
|------------------|-------------------|
| `patient_specific` | Must use patient-scoped token or verify patient context |
| `portal_menu_item` | MUST use patient-scoped token (patient is the user) |
| `global` | Broader token acceptable, validate access appropriately |
| `provider_menu_item` | Staff token acceptable |

**Check for mismatches:**
- Patient-facing apps using admin/global tokens (HIGH risk)
- Global apps accessing patient data without authorization

---

### 4. Secrets Declaration Review

Check that all tokens/keys are declared in the manifest:

```bash
grep -n "secrets" */CANVAS_MANIFEST.json 2>/dev/null || grep -n "secrets" CANVAS_MANIFEST.json 2>/dev/null
grep -rn "self\.secrets\[" --include="*.py" .
```

**Verify:**
- Every `self.secrets['X']` usage has 'X' declared in manifest
- No hardcoded tokens (grep for long base64-like strings)

```bash
grep -rn "eyJ\|['\"][A-Za-z0-9_-]\{30,\}['\"]" --include="*.py" .
```

---

### 5. Generate Security Report

Create a timestamp and get a workspace directory:
```bash
WORKSPACE_DIR=$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/get_plugin_dir.py")
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
```


Save report to `$WORKSPACE_DIR/.cpa-workflow-artifacts/security-review-$TIMESTAMP.md`:

```markdown
# Security Review Report: {plugin_name}

**Generated:** {timestamp}
**Reviewer:** Claude Code (CPA)

## Summary

| Category | Status | Issues |
|----------|--------|--------|
| Plugin API Server Security | ✅ Pass / ⚠️ X issues / N/A | ... |
| FHIR API Client Security | ✅ Pass / ⚠️ X issues / N/A | ... |
| Application Scope | ✅ Pass / ⚠️ X issues / N/A | ... |
| Secrets Declaration | ✅ Pass / ⚠️ X issues / N/A | ... |

## Detailed Findings

### Plugin API Server Security

[Findings from plugin-api-server-security skill review]

### FHIR API Client Security

[Findings from fhir-api-client-security skill review]

### Application Scope

[Scope alignment validation findings]

### Secrets Declaration

[Secrets audit findings]

## Recommendations

| Priority | Issue | Location | Recommendation |
|----------|-------|----------|----------------|
| HIGH | ... | file:line | ... |
| MEDIUM | ... | file:line | ... |
| LOW | ... | file:line | ... |

## Verdict

**✅ PASS** - No security issues found

OR

**⚠️ ISSUES FOUND** - X issues require attention (Y HIGH, Z MEDIUM)
```

Tell the user the report path.

---

### 6. Offer to Fix Issues

If issues were found, use AskUserQuestion:

```json
{
  "questions": [
    {
      "question": "Security review found issues. How would you like to proceed?",
      "header": "Security fixes",
      "options": [
        {"label": "Fix all issues", "description": "Implement recommended fixes now"},
        {"label": "Fix critical only", "description": "Only fix HIGH priority issues"},
        {"label": "Review only", "description": "I'll review and fix manually"}
      ],
      "multiSelect": false
    }
  ]
}
```

**If the user chooses to fix:**
1. Implement fixes in priority order (HIGH first)
2. For missing authentication: add `authenticate()` method with appropriate validation
3. For token issues: move to secrets, add validation
4. For scope issues: recommend manifest changes or token scoping
5. After fixes, re-run the security checks to confirm resolution
6. Update the report with "RESOLVED" status

---

## CPA Workflow

This command can be run standalone or is called by `/cpa:wrap-up`:

```
/cpa:check-setup     →  Verify environment tools
/cpa:new-plugin      →  Create plugin from requirements
/cpa:deploy          →  Deploy to Canvas instance for UAT
/cpa:coverage        →  Check test coverage (aim for 90%)
/cpa:security-review →  Comprehensive security audit  ← YOU ARE HERE
/cpa:database-performance-review  →  Database query optimization
/cpa:wrap-up         →  Final checklist before delivery
```

After the security review passes, guide the user to the next step in the workflow.
