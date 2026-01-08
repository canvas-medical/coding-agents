---
name: fhir-api-client-security
description: Security review for plugins acting as FHIR API clients - token management, scope validation, and patient-scoped authorization
---

# FHIR API Client Security Skill

This skill provides security review guidelines for Canvas plugins that act as FHIR API clients. Use it to audit token management, scope usage, and patient-scoped authorization when your plugin calls Canvas FHIR APIs or external FHIR endpoints.

## When to Use This Skill

Use this skill when:
- Plugin uses `Http()` to call FHIR APIs
- Plugin uses Canvas SDK data models (`Patient.objects`, etc.)
- Plugin implements SMART on FHIR integration
- Plugin has patient-facing features that access FHIR data
- Reviewing OAuth token scope declarations

## Key Security Concerns

1. **Token Scope** - Request minimum necessary scopes (least privilege)
2. **Patient-Scoped Tokens** - Patient-facing apps MUST scope tokens to the specific patient
3. **Token Storage** - Tokens in secrets, never hardcoded
4. **Token Leakage** - Never log tokens or include in error messages

## Security Checklist

Reference the `fhir_client_context.txt` file for detailed patterns including:
- OAuth authentication methods
- FHIR scope format and common scopes
- Patient-scoped token requirements
- Token storage best practices
- Common vulnerabilities and detection
