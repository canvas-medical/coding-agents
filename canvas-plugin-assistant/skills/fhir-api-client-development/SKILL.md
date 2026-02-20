---
name: fhir-api-client-development
description: FHIR API reference and documentation for Canvas plugins that need to read or write data via FHIR endpoints
---

# FHIR API Client Development

This skill provides documentation for Canvas FHIR API endpoints, enabling plugin development when the Canvas SDK alone doesn't cover the needed data access or write operations.

## When to Use This Skill

Use this skill when:
- A plugin needs data only available via FHIR endpoints (not exposed in the SDK)
- A plugin needs to write data in a way only possible through FHIR
- Building integrations that interact with Canvas FHIR APIs
- You need to understand FHIR resource structures and endpoints available on Canvas

## Usage

**IMPORTANT**: The full FHIR documentation is bundled with this skill. **DO NOT download, curl, or fetch remote files.**

The context file `fhir_client_context.txt` is located **in the same directory as this SKILL.md file**.

When you read this skill, note the path to this SKILL.md file, then read `fhir_client_context.txt` from that same directory.

To use this skill:
1. **Read `fhir_client_context.txt` from this skill's directory** - it already exists locally
2. Search the file for specific FHIR resource types, endpoints, or operations
3. Use the documentation to understand available FHIR APIs and their usage

**NEVER attempt to curl or download fhir_client_context.txt - it is already bundled here.**

## Related Skills

- **canvas-sdk**: For SDK-based data access (preferred when available)
- **fhir-api-client-security**: For security review of FHIR API client code (token management, scope validation)
