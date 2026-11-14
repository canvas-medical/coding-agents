# Eval Case Index

**DO NOT READ THIS FILE DURING EVAL RUNS - IT WOULD BIAS RESULTS**

This file documents what each eval case tests. CPA is denied read access to this file.

## case_001

**Category:** Security
**Command:** `/security-review`
**Tests:** Hardcoded secret detection
**Vulnerability:** JWT token hardcoded directly in source code instead of using secrets
**Expected Finding:** HIGH severity - Secrets Declaration category

## case_002

**Category:** Security
**Command:** `/security-review`
**Tests:** Patient scope mismatch
**Vulnerability:** Patient-facing application (portal_menu_item scope) using admin-scoped FHIR token instead of patient-scoped token
**Expected Findings:**
- HIGH severity - Application Scope (portal_menu_item requires patient-scoped token)
- HIGH severity - FHIR Client Security (patient-facing app should not use admin/global token)

## case_003

**Category:** Database Performance
**Command:** `/database-performance-review`
**Tests:** N+1 query patterns
**Vulnerability:** Database queries inside loops, FK access without select_related
**Expected Findings:**
- HIGH severity - N+1 Query Patterns (query inside loop)
- MEDIUM severity - Missing select_related (FK access without prefetch)

## case_004

**Category:** Security
**Command:** `/security-review`
**Tests:** Untrusted HTML rendered raw
**Vulnerability:** Staff-facing conversation view renders patient message content (`Message.content`) with `|safe` (stored XSS)
**Expected Finding:** HIGH severity - Template and HTML Output Safety (use `|sanitize_html`)

## case_005

**Category:** Security
**Command:** `/security-review`
**Tests:** JSON printed into a script tag
**Vulnerability:** Observation data passed as a `json.dumps` string and rendered with `|safe` inside `<script>`; `</script>` in any value breaks out of the tag
**Expected Finding:** HIGH severity - Template and HTML Output Safety (use `json_script`)

## case_006

**Category:** Security
**Command:** `/security-review`
**Tests:** Secret sent to the browser
**Vulnerability:** `self.secrets["FORMULARY_API_KEY"]` placed in template context and used from inline JavaScript to call the external API directly
**Expected Finding:** HIGH severity - Template and HTML Output Safety (proxy the call through a SimpleAPI route)

## case_007

**Category:** Security
**Command:** `/security-review`
**Tests:** HTML built in Python
**Vulnerability:** Error page built with an f-string that puts the external API's `response.text` into an `HTMLResponse`
**Expected Finding:** HIGH severity - Template and HTML Output Safety (template + `render_to_string`)

## case_008

**Category:** Security
**Command:** `/security-review`
**Tests:** JavaScript DOM write
**Vulnerability:** Page script appends `${m.body}` (fetched `Message.content`) to `innerHTML`
**Expected Finding:** HIGH severity - Template and HTML Output Safety (`createElement` + `textContent`)

## case_009

**Category:** Security
**Command:** `/security-review`
**Tests:** Data inside an `on*=` attribute
**Vulnerability:** Patient-search picker renders `'{{ r.name }}'` inside `onclick="pickPatient(...)"`
**Expected Finding:** HIGH severity - Template and HTML Output Safety (`data-` attribute or `escapejs`)
**Must not flag:** `innerHTML` set to the plugin's own server-rendered partial

## case_010

**Category:** Security
**Command:** `/security-review`
**Tests:** URL from data in `href`
**Vulnerability:** Citation URLs regex-parsed from a summarization API's text rendered as `href="{{ c.citation_url }}"` with no scheme check
**Expected Finding:** HIGH severity - Template and HTML Output Safety (check for `https://`/`http://` in Python)

## case_011

**Category:** Security
**Command:** `/security-review`
**Tests:** `self.secrets.get()` returned in a `JSONResponse`; publishable key exemption
**Vulnerability:** `self.secrets.get("ELIGIBILITY_API_SECRET")` returned to the browser and used as a bearer token from page JavaScript
**Expected Finding:** HIGH severity - Template and HTML Output Safety (proxy the call through a SimpleAPI route)
**Must not flag:** the Stripe publishable key returned for Stripe.js

## case_012

**Category:** Security
**Command:** `/security-review`
**Tests:** `|safe` inside a nested `{% include %}`
**Vulnerability:** `templates/partials/message_card.html` renders `{{ body|safe }}`, where `body` is `Message.content` passed through two includes
**Expected Finding:** HIGH severity - Template and HTML Output Safety (use `|sanitize_html`)

## case_013

**Category:** Security
**Command:** `/security-review`
**Tests:** Constant `|safe` beside data `|safe`
**Vulnerability:** `{{ condition.notes|safe }}` renders free-text notes raw, next to a constant `{{ icon|safe }}`
**Expected Finding:** exactly one HIGH severity - Template and HTML Output Safety (the notes)
**Must not flag:** `{{ icon|safe }}` on the module-level SVG constant

## case_014

**Category:** Security
**Command:** `/security-review`
**Tests:** `{% autoescape off %}` around JSON in a script tag
**Vulnerability:** `json.dumps` of condition notes printed inside `<script>` within `{% autoescape off %}`
**Expected Finding:** HIGH severity - Template and HTML Output Safety (use `json_script`)
