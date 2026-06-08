---
name: canvas-sdk
description: Canvas SDK reference and documentation access for Canvas platform capabilities, API usage, implementation patterns, and testing
---

# Canvas SDK Reference

This skill provides comprehensive documentation for the Canvas Medical SDK, enabling development of Canvas plugins.

## When to Use This Skill

Use this skill when you need information about:
- Canvas SDK classes, methods, and APIs
- Event types and their context structures
- Effect types and their payloads
- Data models (Patient, Condition, Medication, etc.)
- Handler types (BaseHandler, SimpleAPI, Application, CronTask)
- Canvas CLI commands
- Plugin manifest structure

## Terminology / Aliases

Users describe Canvas surfaces with different names. Map them to SDK classes before
deciding which handler to scaffold:

- **"Note Application", "NoteApplication", "Charting app", "Charting application", "note tab", "tab inside a note"** → an embedded application scoped to a note. Implement with `NoteApplication` (subclass of `EmbeddedApplication`, with `SCOPE = ApplicationScope.NOTE` preset). Located in `canvas_sdk.handlers.application`.
- **"Embedded app", "embedded application"** → `EmbeddedApplication` directly. Use this when the scope is something other than note, or when the user wants to set `SCOPE` explicitly.
- **"Full chart app", "chart tab"** → an `Application` registered with `"scope": "full_chart"` in `CANVAS_MANIFEST.json` (appears alongside the default "Chart" and "Profile" tabs).
- **"App drawer application"** → a plain `Application` launched from the app drawer.

When a user says "Charting app" or "NoteApplication", do not ask them to clarify — assume they mean a note-scoped embedded application (`NoteApplication`) unless they describe behavior that doesn't fit (e.g. "appears at the top of the chart" → full_chart scope).

### Note Application templates: always auto-resize

Every HTML template rendered by a `NoteApplication` must wire up the Canvas `RESIZE` message pattern so the iframe grows to fit its content instead of showing its own scrollbar inside the note. Apply this by default — do not ask the user to confirm. Only omit it if the user explicitly says they want a fixed-height iframe with its own scroll.

The canonical pattern (full snippet in `coding_agent_context.txt`, under "Auto-resizing the Note Application iframe"):
- `html, body { overflow: hidden; margin: 0; padding: 0; }`
- Listen for `INIT_CHANNEL` → grab the `MessagePort`
- Post `{ type: 'RESIZE', height: document.body.offsetHeight }` on connect and on every `ResizeObserver` tick

### Custom chart summary sections: always ask about real-time

When building a custom patient chart summary section (`PatientChartSummaryCustomSectionHandler`), **ask the user whether the section needs real-time updates** before scaffolding. If yes, implement it with a `WebSocketAPI` + `Broadcast` from a `BaseHandler` listening for the relevant Canvas events.

**The WebSocket channel name MUST include the patient id** (e.g. `chart-summary-{plugin_name}-{patient_id}`). Never broadcast on a global channel — it leaks updates across patient charts and causes every connected client to re-render on every event. Full pattern + example in `coding_agent_context.txt`, under "Real-Time Updates for Custom Sections".

### WebSockets must survive blue/green deploys

This applies to **any** plugin WebSocket — custom chart summary sections, real-time note-restriction updates (`NoteRestrictionsUpdatedEffect`), companion-app surfaces, anything built on `WebSocketAPI` + `Broadcast`. Canvas runs blue/green deploys during the working day, so a live socket is closed mid-session and the client reconnects onto a freshly booted process. Build every WebSocket client to survive that gap:

- **Push is a hint, pull is the truth.** `Broadcast` is fire-and-forget and ephemeral — anything sent while the socket was down is gone, and the plugin process keeps no durable state across a restart (module globals reset every deploy). Treat the socket as a "something changed" nudge and re-fetch the authoritative snapshot from your `SimpleAPI` endpoint to learn *what*.
- **Re-fetch on every (re)connect, not just initial load.** Wire the snapshot fetch to the socket's `open` event so the initial load and every reconnect run identical reconciliation — anything missed during the gap is picked up immediately.
- **Reconnect with exponential backoff + jitter + a cap, never a fixed delay.** A deploy drops every client at the same instant, so a fixed delay is a thundering herd against the single container that just booted. Also reconnect immediately on the browser `online` event.
- **Make mutating `POST`s idempotent.** A cutover can drop the response to an in-flight mutation, and the client cannot tell "never applied" from "applied, response lost," so it retries. Re-check current state server-side and no-op if the desired state already holds rather than blindly emitting a second effect.

Full worked client code (backoff/jitter, `online` handling, half-open heartbeat, idempotent mutations) is in the `companion-app-patterns` skill's `companion_app_patterns_context.txt`, under "Surviving deploys & reconnection" — the pattern is identical for any WebSocket surface, not just companion apps.

## Key Documentation Sections

### Handlers
- **BaseHandler**: Event-driven handlers responding to Canvas events
- **SimpleAPI**: HTTP endpoints and WebSocket handlers
- **Application**: UI applications launched from the app drawer
- **EmbeddedApplication / NoteApplication**: Embedded UI shown inside the chart or note (see Terminology above)
- **CronTask**: Scheduled task execution
- **ActionButton**: UI buttons in notes and patient headers

### Events
- Record lifecycle events (patient, appointment, lab results)
- Command lifecycle events (prescribe, diagnose, assess, etc.)
- Search result events for customizing dropdowns

### Effects
- AddBannerAlert: Display alerts in patient timeline
- AddTask: Create tasks for staff
- LaunchModalEffect: Open modals/panels
- Patient metadata effects
- Billing effects

### Data Models
- Patient, Appointment, LabOrder, Medication
- Condition, AllergyIntolerance, Observation
- Note, Task, Staff, Team

### Third-Party Libraries
- AWS S3
- LLM:
  - Anthropic Claude, 
  - OpenAI ChatGPT, 
  - Google Gemini
- Twilio
- SendGrid
- Extend.ai


## Usage

**IMPORTANT**: The full SDK documentation is bundled with this skill. **DO NOT download, curl, or fetch remote files.**

The context file `coding_agent_context.txt` is located **in the same directory as this SKILL.md file**.

When you read this skill, note the path to this SKILL.md file, then read `coding_agent_context.txt` from that same directory.

For example, if this SKILL.md is at:
```
/some/path/skills/canvas-sdk/SKILL.md
```

Then read:
```
/some/path/skills/canvas-sdk/coding_agent_context.txt
```

To use this skill:
1. **Read `coding_agent_context.txt` from this skill's directory** - it already exists locally
2. Search the file for specific class names, event types, or effect types
3. Use the documentation to understand Canvas SDK capabilities

The context file contains ~20000 lines of comprehensive SDK documentation including all handlers, events, effects, and data models.

**NEVER attempt to curl or download coding_agent_context.txt - it is already bundled here.**
