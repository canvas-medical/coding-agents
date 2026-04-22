---
name: product-review
description: Product-level review criteria for Canvas plugins — Designated Record Set alignment, placement, coded data capture, native primitives, alert fatigue, configurability, attribution, terminology, and ONC certified-criteria overlap. Use proactively while planning/writing plugin code, not just at review time.
---

# Product Review Skill

This skill provides the nine product-level tenets used to evaluate Canvas plugins. It surfaces product judgment calls (regulatory, placement, record-set alignment) that are distinct from the engineering concerns covered by `plugin-api-server-security`, `fhir-api-client-security`, and `database-performance`.

Use this skill **proactively** — apply the tenets while planning and writing code, not only in a dedicated review pass. The `/cpa:product-review` command is the end-to-end workflow (environment validation, report generation, next-step routing); this skill is the underlying rule set you can invoke inline.

## When to Use This Skill

Invoke this skill when:

- **Planning or brainstorming a plugin** — before any code is written, check whether the intended data model and placement align with the tenets (especially Tenets 1, 2, 4, 9).
- **About to create or modify a `CustomModel` / `AttributeHub`** — apply Tenet 1 (DRS) and Tenet 4 (native primitives) before deciding on custom storage.
- **Declaring an `Application` or configuring a manifest `scope`** — apply Tenet 2 (placement), including the mixed-scope and `provider_menu_item` vs. `global` distinctions.
- **Writing clinical concept matching** (conditions, medications, allergies, observations, specialties, facility types) — apply Tenet 3 (coded data capture).
- **Shipping defaults, thresholds, or catalogs** in plugin code or content — apply Tenet 6 (configurability) and Tenet 9 (CDS-lite).
- **Integrating with orders, prescriptions, TOC, immunization registries, CQMs, EHI export, patient VDT, or FHIR APIs** — apply Tenet 9 (ONC overlap).
- **Reviewing existing plugin code** before `/cpa:wrap-up` or as a spot-check.

## The Nine Tenets

Reference `product_review_context.txt` for each tenet in full — the rules, detection heuristics, and what to flag. Quick index:

1. **Designated Record Set / Clinical Data Model** — custom data must not restate DRS content (USCDI V3 + broader DRS: billing, care coordination, authorizations, external data incorporated into decisions). Psychotherapy notes are a special case — escalate.
2. **Placement** — manifest `scope` must match the feature's intent. `provider_menu_item` (settings-ish) vs. `global` (panel-level clinical activities) is distinct. Flag mixed-scope applications (one app doing patient-specific work *and* global CRUD / catalog management).
3. **Coded data capture** — clinical concepts matched and stored by codes (SNOMED, LOINC, RxNorm, ICD-10, CPT, CVX, NUCC, NCPDP, FDB), not by display strings.
4. **Native Canvas primitives** — Questionnaire, Task, Note, Goal, Command, CareTeamMembership, ServiceProvider, Organization, Location, Observation, PrescribeCommand, CustomCommand, Effect types. Parallel systems fragment the record.
5. **Alert fatigue** — interruptions must be justified, contextual, dismissible. Prefer passive surfacing over blocking UI.
6. **Configurability** — clinical thresholds, code lists, reference ranges, and default catalogs must be customer-overridable, not hardcoded in Python.
7. **Audit trail / attribution** — clinically-relevant writes must capture the actor. Server-derive `staff_id` from session; never trust a client-supplied identity. No shadow overrides that edit what's displayed without mutating the record of truth.
8. **Terminology consistency** — Canvas vocabulary (Patient, Staff, Note, Command, Effect, Protocol, Questionnaire, Task) in code; clinical vocabulary with code-system-named fields (`snomed_code`, `loinc_code`, not `dx_code` with unspecified system).
9. **ONC certified-criteria overlap** — cross-reference every plugin behavior against Canvas's §170.315 certifications. Augment-class overlaps are fine with documentation; **replace-class overlaps and EHI-transmission outside certified paths are HIGH**. Plugin-authored clinical guidance (dosing schedules, thresholds, decision rules shipped in code) is CDS-lite — needs provenance or move to customer-owned content.

## How to Apply

When invoking inline, run through the tenets **in the order listed**. Tenet 1 (DRS) and Tenet 9 (ONC) catch the highest-impact issues and often resolve earlier tenets as a side effect — e.g. moving a CustomModel into a native primitive (Tenet 4) frequently fixes the DRS gap (Tenet 1) and the placement mismatch (Tenet 2) at the same time.

Don't silently refactor for Tenets 1 or 9 — always confirm with the user. DRS migrations and ONC-overlap changes affect compliance posture and often require product/compliance sign-off. For Tenets 2, 3, 6, 7, 8 the fixes are usually mechanical (rename, move to config, switch to session-derived staff) and can be applied with light confirmation.

## Relationship to Other Skills and Commands

- `/cpa:product-review` — end-to-end workflow that applies these tenets, writes a timestamped report, and routes next steps. Use this as a gated step before `/cpa:wrap-up`.
- `plugin-patterns` — architectural patterns and best practices. Complementary — that skill tells you *how* to build, this one tells you *what* qualifies as a product-sound plugin.
- `custom-data-patterns` — anti-patterns in CustomModel / AttributeHub use. Overlaps with Tenet 1 and Tenet 4 here; that skill is more surgical on the custom-data specifics.
- `plugin-api-server-security` / `fhir-api-client-security` — engineering security concerns. This skill's Tenet 7 overlaps at the seam (session-derived identity) but focuses on attribution integrity; those skills focus on authentication / authorization correctness.
