---
name: canvas-sdk
description: Canvas SDK reference and documentation. Use whenever a question, claim, or piece of code touches Canvas SDK capabilities, API usage, implementation patterns, or testing — including quick conversational questions ("how do I ingest ADTs?", "what's the import for X?", "does Canvas support Y?"). The bundled docs are the source of truth; do not answer Canvas SDK questions from memory.
---

# Canvas SDK Reference

This skill provides comprehensive documentation for the Canvas Medical SDK, enabling development of Canvas plugins.

## Grounding Rule — Read Before Answering

**Never answer a Canvas SDK question from memory.** Canvas's SDK surface (effects, events, data models, handlers, manifest fields, import paths) is Canvas-specific and changes often; the model's prior is frequently wrong or out of date. Confidently-wrong answers about Canvas APIs are worse than no answer.

Before stating any specific class name, import path, effect/event name, field name, method, or supported value:
1. Read `coding_agent_context.txt` from this skill's directory (see Usage below) and `grep`/search it for the relevant term.
2. Base your answer on what the bundled docs actually say.
3. **Cite the source doc page URL** (the `----- BEGIN PAGE https://docs.canvasmedical.com/...` line that contains the content) so the user can verify it — the same way a high-quality grounded answer always links its source.

This applies to a one-line verbal question just as much as to code generation. If a question is even partially about an SDK capability and you have not yet consulted this skill in the current conversation, consult it first, then answer.

## When to Use This Skill

Use this skill whenever a question, claim, or piece of code involves — even in passing — any of:
- Canvas SDK classes, methods, and APIs
- Event types and their context structures
- Effect types and their payloads (e.g. creating external events / ADT ingestion, banner alerts, tasks)
- Data models (Patient, Condition, Medication, etc.)
- Handler types (BaseHandler, SimpleAPI, Application, CronTask)
- Canvas CLI commands
- Plugin manifest structure
- Whether Canvas "supports" some capability, and how it is modeled

This includes short conversational questions, not just plugin-building work. Examples that REQUIRE consulting this skill before answering: "how do I ingest ADTs?", "what's the import path for the external event effect?", "what fields does X take?", "does Canvas have a built-in HL7 parser?". Do not answer any of these from memory.

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
4. **Cite the source doc page URL** in your answer (the `----- BEGIN PAGE https://docs.canvasmedical.com/...` URL whose section you used), so the answer is verifiable and grounded rather than asserted from memory

The context file contains ~20000 lines of comprehensive SDK documentation including all handlers, events, effects, and data models.

**NEVER attempt to curl or download coding_agent_context.txt - it is already bundled here.**
