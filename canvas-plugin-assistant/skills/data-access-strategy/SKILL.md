---
name: data-access-strategy
description: Decide how a Canvas plugin reads and writes data - SDK vs FHIR API, and existing Canvas data models vs Custom Data. Use whenever a plugin needs to read or write clinical/operational data, before writing the spec or any data-access code.
---

# Data Access Strategy

This skill decides **how** a Canvas plugin touches data. There are two questions, and the plugin spec must answer both with a recorded rationale:

1. **SDK or FHIR API?** — for every read and every write the plugin performs.
2. **Existing Canvas data models or Custom Data?** — for everything the plugin needs to persist.

The defaults are the same on both axes: **stay inside the SDK and reuse what Canvas already models.** Escalate to FHIR or to Custom Data only when the default genuinely can't do the job, and write down why.

## When to Use This Skill

Invoke this skill **before writing the spec**, as soon as you know what data the plugin reads or writes. Also use it when:

- Mapping requirements to a `Data Requirements` / `Data Access Strategy` spec section
- About to write a data-model query, an Effect, or a FHIR call
- Reviewing a plugin and questioning whether a FHIR call or a CustomModel was the right call

## Decision 1: SDK vs FHIR API

**Default to the SDK. Use FHIR only when the SDK cannot accomplish the task.**

Why the SDK is the default:

- Runs in-process, no network round-trip, no token to manage or leak.
- No OAuth scopes to request, store, or scope to a patient.
- Reads come straight from the data module (Django ORM over read-only views); writes go through Effects, which Canvas validates and applies.
- Less code, fewer failure modes, nothing to rotate.

### Reads

- **SDK first.** If the data you need is exposed in the data module (`canvas_sdk.v1.data`), read it there. This covers the large majority of clinical and operational models.
- **FHIR only if** the data you need is **not** exposed in the SDK data module, or you need a FHIR-shaped resource bundle (e.g. an external integration expects FHIR JSON).

### Writes

The SDK data models are **read-only**. Mutations happen one of two ways, and the only question is whether an Effect exists for the write you need:

- **SDK Effects** — if there is an Effect for the change you want (e.g. `AddBannerAlert`, `AddTask`, command effects, chart writes), use it. This is the default for writes. Effects are **not** tied to event handlers: a `BaseHandler` returns them from `compute()`, a `CronTask` returns them from `execute()` (`-> list[Effect]`), and a `SimpleAPI` route returns them from its method (`-> list[Response | Effect]`). So a scheduled job or an API endpoint can write via Effects just like an event handler.
- **FHIR API** — use it to create or update data when there is **no Effect** for the write you need. (A handful of effects are contextual to the in-flight command — e.g. `*__PRE_COMMIT` overrides — and only make sense from the handler responding to that event; those are command overrides, not general data writes.)

### Quick reference

| Situation | Use |
|-----------|-----|
| Read a model exposed in `canvas_sdk.v1.data` | **SDK data module** |
| Read data not exposed in the SDK | **FHIR** |
| Write and an Effect exists for it | **SDK Effect** (works from `BaseHandler`, `CronTask`, or `SimpleAPI`) |
| Write with no matching Effect | **FHIR** |
| Plugin is itself a FHIR-shaped integration with an external system | **FHIR** |

When in doubt, check the **canvas-sdk** skill for whether a data model or Effect exists before reaching for FHIR. Most "we need FHIR" instincts are covered by an existing model or Effect.

### If you choose FHIR

Reads/writes via FHIR carry security obligations the SDK does not. Invoke the **fhir-api-client-security** skill and confirm:

- token stored in a secret, never hardcoded
- patient-facing flows use a patient-scoped token
- minimum-necessary scopes requested

## Decision 2: Existing Data Models vs Custom Data

**Default to existing Canvas data models. Add Custom Data only when no Canvas model represents the data.**

- **Use existing models** (via the SDK data module / Effects, or FHIR) whenever the data is a clinical or operational concept Canvas already knows about — patients, conditions, medications, tasks, appointments, notes, etc. Do not shadow a Canvas concept with your own table.
- **Use Custom Data** (`CustomModel` / `AttributeHub`) only for data that genuinely has **no home in Canvas**:
  - plugin-specific configuration or state
  - mappings to an external system's identifiers
  - bookkeeping the plugin needs that Canvas does not model

Anti-pattern: storing a copy of patient/clinical data in a CustomModel "for convenience." Reference the Canvas record instead. If you do introduce any `CustomModel` or `AttributeHub`, invoke the **custom-data-patterns** skill before writing the model definitions.

## Record the Rationale in the Spec

Every plugin spec must include a **Data Access Strategy** section that states the choices and *why*, so a reviewer can see the reasoning without reading the code. Keep it short — one line per decision:

```markdown
## Data Access Strategy

- **Reads**: SDK data module (`Patient`, `Observation`) — both exposed in `canvas_sdk.v1.data`.
- **Writes**: SDK Effect `AddBannerAlert` — fires in response to `VITALS_COMMAND__POST_COMMIT`, effect exists.
- **FHIR used**: No — SDK covers all reads and writes.
- **Custom Data**: No — all data maps to existing Canvas models.
```

When the plugin *does* escalate, the rationale must say what the SDK couldn't do:

```markdown
## Data Access Strategy

- **Reads**: SDK data module for patient + appointments.
- **Writes**: FHIR `DocumentReference` POST — no SDK Effect exists for creating documents.
- **FHIR used**: Yes, write only, for document creation; patient-scoped token, stored in secret.
- **Custom Data**: Yes — `ExternalSyncRecord` CustomModel maps Canvas appointments to the partner system's booking IDs (no Canvas model for this). custom-data-patterns skill applied.
```

## Related Skills

- **canvas-sdk**: confirm whether a data model or Effect exists before choosing FHIR (preferred path).
- **fhir-api-client-development**: how to call FHIR once you've decided the SDK can't do it.
- **fhir-api-client-security**: required security review whenever FHIR is used.
- **custom-data-patterns**: required whenever a CustomModel or AttributeHub is introduced.
