# Eval Case Index

**DO NOT READ THIS FILE DURING EVAL RUNS - IT WOULD BIAS RESULTS**

This file documents what each eval case tests. CPA is denied read access to this file.

## case_001

**Category:** Security
**Command:** `/security-review-cpa`
**Tests:** Hardcoded secret detection
**Vulnerability:** JWT token hardcoded directly in source code instead of using secrets
**Expected Finding:** HIGH severity - Secrets Declaration category

## case_002

**Category:** Security
**Command:** `/security-review-cpa`
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
