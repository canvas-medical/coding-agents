---
name: security-review
description: Comprehensive security audit for Canvas plugins covering both server-side API security and client-side FHIR API security.
---

# Security Review

Comprehensive security audit for Canvas plugins covering both server-side API security and client-side FHIR API security.

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

Run through each security category, document findings, generate a report, and offer to fix issues.

### Step 2: Plugin API Server Security

Check if the plugin exposes any API endpoints:

```bash
grep -rn "SimpleAPI\|WebSocket\|SimpleAPIRoute" --include="*.py" .
```

Ignore all directories that are not part of the project, e.g. `.venv`, `.pytest_cache`... with `--exclude-dir`.


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

### 4. Variables Declaration Review

Check that all tokens/keys/configurable values are declared in the manifest's modern `variables` array:

```bash
grep -nE '"(variables|secrets)"' */CANVAS_MANIFEST.json 2>/dev/null || grep -nE '"(variables|secrets)"' CANVAS_MANIFEST.json 2>/dev/null
grep -rnE "self\.secrets(\[|\.get\()" --include="*.py" .
```

**Verify:**
- Every `self.secrets['X']` or `self.secrets.get('X')` usage has 'X' declared in the manifest's `variables` array (or, for unmigrated plugins, the deprecated `secrets` array — flag it; the modern form is required and the pre-deploy lint rejects legacy-only manifests).
- No hardcoded tokens (grep for long base64-like strings).

```bash
grep -rn "eyJ\|['\"][A-Za-z0-9_-]\{30,\}['\"]" --include="*.py" .
```

---

### 5. Template and HTML Output Safety

Check every template and every HTML/JavaScript the plugin sends to a browser (`render_to_string`, `HTMLResponse`, `LaunchModalEffect(content=...)`, widget/section `content`):

```bash
grep -rnE "\|\s*safe\b|autoescape off|mark_safe|format_html\(" --include="*.html" --include="*.py" --include="*.js" .
grep -rnE "self\.secrets(\[|\.get\()" --include="*.py" .
grep -rnE "<script" --include="*.html" .
grep -rnE "(HTMLResponse\(|\bcontent=)\s*f[\"']" --include="*.py" .
grep -rnE "f[\"'][^\"']*<[a-zA-Z/]" --include="*.py" .
grep -rnE "\.(innerHTML|outerHTML)\s*\+?=[^=]|insertAdjacentHTML\(|document\.write\(" --include="*.html" --include="*.js" --include="*.py" --include="*.jsx" --include="*.tsx" .
grep -rnE "on[a-z]+=\"[^\"]*\{\{|on[a-z]+='[^']*\{\{" --include="*.html" .
grep -rnE "(href|src)=[\"']\{\{" --include="*.html" .
```

A grep hit is where to look, not the finding: trace the value to its source before reporting it.

**If the plugin renders no HTML:** Mark as N/A

**Flag each of these as a HIGH finding, with file:line and the fix:**

| Pattern | Why it is a finding | Fix |
|---------|---------------------|-----|
| `{{ value\|safe }}`, `{% autoescape off %}`, or `mark_safe(...)` on data from patients, integrations, notes, messages, questionnaires, FHIR input, or any external API | Stored XSS: the data runs as script in the viewing staff member's session | Plain `{{ value }}` (or `\|linebreaksbr`) for text; `{{ value\|sanitize_html }}` / `canvas_sdk.utils.html.sanitize_html(value)` for HTML that must keep formatting |
| JSON printed into a `<script>` block, e.g. `const x = {{ data_json\|safe }};` or an f-string building `<script>` content | `json.dumps` does not escape `</script>`, so a value containing it closes the tag and injects HTML | Pass the Python object in the context and use `{{ data\|json_script:"element-id" }}`, read with `JSON.parse(document.getElementById("element-id").textContent)` |
| HTML built in Python (f-string, `.format()`, `%`, or `+`) from data and returned via `HTMLResponse`, `LaunchModalEffect(content=...)`, or widget content, including `str(e)` or `{e!r}` in an error page | No template, so nothing is escaped | Template + `render_to_string` with the data in the context, or `sanitize_html` for HTML that must keep formatting |
| `innerHTML`, `outerHTML`, `insertAdjacentHTML`, or `document.write` given a template literal or `+` with fetched or server data | Nothing escapes it, so markup in a value runs as script in the staff session | `textContent` / `createElement` + `textContent`; markup stays in templates |
| `{{ value }}` from data inside an `on*=` attribute (`onclick`, `onchange`, ...) without `escapejs` | Autoescape turns `'` into `&#x27;`, and the browser decodes it before running the handler, so a value like `x');alert(1);//` runs | A `data-` attribute read in the script, or `{{ value\|escapejs }}` |
| `href`/`src` set from data (an integration, an LLM, a patient, an external API) with no scheme check | A `javascript:` URL survives escaping and runs on click | Check in Python that the URL starts with `https://` or `http://` before it reaches the context |
| A `self.secrets[...]` or `self.secrets.get(...)` value (or anything derived from it, like an auth header) placed in template context, an `HTMLResponse`, a `JSONResponse`, inline JavaScript, or modal content | Anything sent to the browser is readable there, so the secret leaks to every user who opens the page | Keep the secret server-side: add a `SimpleAPIRoute` that calls the external API and returns only the data the page needs, and have the page `fetch()` that route |

To trace a secret, follow each `self.secrets[...]` and `self.secrets.get(...)` variable to where it is used; a secret that reaches a `render_to_string` context dict, a response body (`HTMLResponse`, `JSONResponse`, `Response`), or a string containing `<script` is a finding.

These are not findings; say why in the report so the reader can check it:
- `|safe` on a value the plugin fully controls (a constant, or HTML the plugin built only from escaped parts).
- HTML built in Python where every data value passes through `html.escape` (allowed in the sandbox) or `sanitize_html`, and no value lands in an `on*=` attribute or a `href`/`src`.
- `innerHTML` given only a constant string, or HTML the plugin's own server rendered from a template.
- A vendor key documented as publishable for browser use, such as a Stripe `pk_...` key or a Pay Theory public API key, rendered into the page on purpose.

---

### 6. Generate Security Report

Get the workspace directory:
```bash
WORKSPACE_DIR=$(uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/get_plugin_dir.py")
```

Save report to `$WORKSPACE_DIR/.cpa-workflow-artifacts/security-review.md`, overwriting any previous run:

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
| Template and HTML Output Safety | ✅ Pass / ⚠️ X issues / N/A | ... |

## Detailed Findings

### Plugin API Server Security

[Findings from plugin-api-server-security skill review]

### FHIR API Client Security

[Findings from fhir-api-client-security skill review]

### Application Scope

[Scope alignment validation findings]

### Secrets Declaration

[Secrets audit findings]

### Template and HTML Output Safety

[`|safe` / `autoescape off` / `mark_safe` on untrusted data, JSON in `<script>` blocks, HTML built in Python, JavaScript DOM writes, `on*=` attribute values, `href`/`src` from data, secrets reaching the browser]

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

### 7. Offer to Fix Issues

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
5. For template issues: replace `|safe` with `|sanitize_html` (or plain escaping), JSON-in-script with `json_script`, Python-built HTML with a template and `render_to_string`, `innerHTML` writes with `textContent`, handler values with a `data-` attribute or `escapejs`, data URLs with a server-side scheme check, and secrets in the browser with a `SimpleAPIRoute` proxy
6. After fixes, re-run the security checks to confirm resolution
7. Update the report with "RESOLVED" status

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
