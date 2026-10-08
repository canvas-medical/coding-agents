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
