---
name: plugin-api-server-security
description: Security review for plugin API endpoints (SimpleAPI, WebSocket) - authentication and authorization when your plugin is the SERVER
---

# Plugin API Server Security Skill

This skill provides security review guidelines for Canvas plugins that expose API endpoints. Use it to audit SimpleAPI and WebSocket handlers for proper authentication and authorization when your **plugin is the SERVER** receiving requests.

## When to Use This Skill

Use this skill when:
- A plugin has any SimpleAPI or WebSocket handlers
- Reviewing authentication implementation
- Checking SessionCredential usage for patient/staff authorization
- Auditing endpoints for security vulnerabilities

## Best Practice: Use Authentication Mixins

**Always prefer the built-in authentication mixins over manual `authenticate()` implementations.**

The Canvas SDK provides mixins that handle authentication correctly:

- `StaffSessionMixin` - For staff-only endpoints
- `PatientSessionMixin` - For patient-only endpoints
- `APIKeyAuthMixin` - For API key authentication

These mixins are documented at: `handlers-simple-api-http/#staff-session`

Using mixins:
- Reduces boilerplate code
- Ensures consistent, correct authentication
- Is easier to audit during security review
- Avoids common authentication mistakes

**During security review, flag any manual `authenticate()` implementations and recommend using the appropriate mixin instead.**

## Security Checklist

Reference the `security_context.txt` file for detailed security patterns and common vulnerabilities.
