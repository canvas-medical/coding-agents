---
name: companion-app-patterns
description: Design, UI, data-access, and packaging conventions for Canvas provider companion applications (scopes `provider_companion_global`, `provider_companion_patient_specific`, `provider_companion_note_specific`). Use when building or reviewing a plugin whose manifest declares one of those scopes, or whose `Application.on_open` emits a `LaunchModalEffect` for the companion surface.
---

# Canvas Provider Companion Application Patterns

This skill captures conventions for building Canvas **provider companion** plugins — mobile-oriented modals launched from the provider companion harness. They read as small single-page apps rendered inside an iframe, served by a `SimpleAPI` handler.

## When to Use This Skill

Invoke this skill when you are:

- Creating a new plugin that declares `provider_companion_global`, `provider_companion_patient_specific`, or `provider_companion_note_specific` in its manifest.
- Reviewing or modifying a plugin whose `Application` subclass emits a `LaunchModalEffect` that points at a `SimpleAPI` endpoint served by the same plugin.
- Deciding where a piece of logic should live between the `Application`, the `SimpleAPI`, and the client-side `main.js`.
- Choosing between client-side render and server-round-trip for a new interaction.

It complements `plugin-patterns` (generic Canvas plugin patterns) and `testing` (mock-based test discipline) rather than replacing them.

## Quick Reference

Reference `companion_app_patterns_context.txt` in this skill directory for the full rule set with rationale and examples. High-level rules:

1. **Scope awareness.** Only read the event context keys your scope actually provides. Global apps get no `patient` or `note`; patient-specific gets `patient.id`; note-specific gets both.
2. **Mutations via effects, never `.save()`.** Writes flow through SDK effects (`UpdateTask`, `AddTaskComment`, etc.). The plugin sandbox disallows direct ORM writes.
3. **Server enforces permissions; client renders.** The task serializer sets `can_complete` / `can_assign_to_me`; the client gates button visibility on those flags, and the mutating endpoint re-verifies before emitting the effect.
4. **FK lookups by public UUID use `fk__id=<uuid>`.** `assignee_id` / `provider_id` target the integer `dbid` PK and will raise `ValueError: Field 'dbid' expected a number` if passed a UUID string.
5. **Timezone: client sends ISO, server parses ISO.** Client builds date-range boundaries from local `Date` objects and calls `.toISOString()`. Server parses with `datetime.fromisoformat` (supporting `Z`). Display uses `toLocaleTimeString` / `toLocaleDateString`.
6. **One HTML shell + `main.js` + `styles.css` per plugin.** Vanilla JS, no framework, no bundler. The shell is served by `@api.get("/")`; JS and CSS are served by sibling routes.
7. **Material-style card language.** 4px radius, layered `box-shadow` for elevation, consistent neutral/accent palette. Tap-to-expand cards get a visible, rotating chevron.
8. **Mobile-first scroll isolation.** `body` is a full-height flex column with `overflow: hidden`; only the content region scrolls so header/filter chrome stays pinned.
9. **Deep links break out of the iframe via `target="_top"`.** Navigating to another part of Canvas (e.g., a patient page) must replace the top frame; don't try to reproduce host chrome inside the modal.
10. **One plugin = one surface, one purpose.** Ship them self-contained: own `README.md` leading with end-user usage, own `LICENSE`, own 256×256 icon (SVG source + PNG), own tests at 100% coverage. Don't cross-reference sibling companion plugins — fork, don't import.

## Reference Implementations

Two companion-scope plugins demonstrate this skill end-to-end in [Medical-Software-Foundation/canvas](https://github.com/Medical-Software-Foundation/canvas):

- `extensions/provider_schedule_companion/` — the logged-in provider's schedule with day/week/month views (`provider_companion_global`).
- `extensions/provider_task_dashboard_companion/` — filterable task list with inline comment thread, assign-to-me, and mark-complete actions (`provider_companion_global`).

Both ship with detailed READMEs, 100% pytest coverage, and MIT licensing.
