---
name: canvas-platform
description: Canvas native-feature and UI-placement reference. Use whenever a question or plan touches whether Canvas already does something natively ("can we set up appointment reminders?", "does Canvas handle X out of the box?") before proposing to build a plugin, and whenever you need to know where a plugin's UI lands (app drawer, panel, provider menu, note tabs, chart sections) or in what order. The bundled docs are the source of truth; do not answer from memory.
---

# Canvas Platform Reference

This skill grounds two kinds of answer that the model's prior gets wrong: **what Canvas already does natively** (so we don't rebuild a shipped feature) and **where a plugin's UI lands and in what order**. It bundles a two-tier native-feature reference (a grep-able index + a full-body corpus) and a static placement model.

## Grounding Rule — Read Before Answering

**Never answer "does Canvas do X natively" from memory, and never propose to build a capability before checking whether Canvas already ships it.** The Help Center changes independently of any code, and the model's prior about Canvas's native surface is frequently wrong or out of date.

Before stating that Canvas does or does not natively support a capability — or before scaffolding a plugin for one — run the **two-tier lookup**:

1. **Grep `canvas_platform_index.txt`** (the index, in this skill's directory) for the capability's keywords. The index is title/heading-only, so a keyword returns clean candidate articles — each a `- [Title](url)` bullet with its `## Subsection` outline indented beneath it — not dozens of noisy body hits.
2. **Read that one article's body** from `canvas_platform_context.txt` by grepping its `----- BEGIN PAGE <url>` block, then locate the relevant `## Subsection`.
3. Base the answer on what that body actually says.
4. **Cite the `----- BEGIN PAGE https://help.canvasmedical.com/...` URL** whose section you used, so the answer is verifiable rather than asserted.

This applies to a one-line conversational question just as much as to plugin-building work. If a question is even partially about a Canvas native capability and you have not yet consulted this skill in the current conversation, consult it first, then answer.

## Pointer Discipline

Surface every native-feature match as a **pointer**, never as settled coverage:

> "Canvas **may** do X — see `<article-url>`; confirm it covers your specific need before we build."

Do **not** say "Canvas already handles this" as a closed conclusion. A native feature often covers only part of a request — for example, native Appointment Reminders send a single org-wide reminder, so a flat "don't build, Canvas does this" would be wrong for a use case needing per-provider or multi-touch reminders. A wrong "Canvas already handles this" poisons trust worse than over-building: it steers the user away from something they actually need. Point them at the article and let the confirmation happen against their real requirement.

## Usage

**IMPORTANT**: Both reference files are bundled with this skill. **DO NOT download, curl, or fetch remote files** — the index and corpus already exist locally in the same directory as this SKILL.md.

Note the path to this SKILL.md file, then read the two `.txt` files from that same directory:

```
/some/path/skills/canvas-platform/canvas_platform_index.txt     ← grep this FIRST (discovery)
/some/path/skills/canvas-platform/canvas_platform_context.txt    ← read ONE article's body from here (by URL)
```

The retrieval order matters:

1. **Grep the index first, never the corpus, for discovery.** Grepping the corpus directly for a topic word is the anti-pattern this skill replaces — a word like `appointment` matches dozens of article bodies and buries the answer. The index maps a keyword to a small set of candidate articles and their subsections.
2. **Then read only the matched article's `----- BEGIN PAGE <url>` block** from the corpus. Read one entry at a time, by URL — do not read or grep the whole corpus for a topic word.
3. **Cite the `BEGIN PAGE` URL** whose section you used.

**NEVER attempt to curl or download either file — both are already bundled here.**

## Placement Model — Where a Plugin's UI Lands

This section is static and hand-authored (it is not in the corpus). Use it to answer "where will this app show up, and in what order" and to choose an order value that lands an app between two existing neighbors.

### Applications — `CANVAS_MANIFEST.json` → `components.applications[]`

Each application entry declares its placement through these fields:

- **`scope`** — where the app appears. Values:
  - `global` — app drawer, everywhere (not tied to a patient).
  - `patient_specific` — app drawer within a patient chart.
  - `provider_menu_item` — a button on the provider's menu.
  - `portal_menu_item` — a button on the patient portal menu.
  - `full_chart` — a full-chart tab, alongside the built-in "Chart" and "Profile" tabs.
  - `provider_companion_global` / `provider_companion_patient_specific` / `provider_companion_note_specific` — Provider Companion surfaces.
- **`menu_position`** — coarse placement within the menu (e.g. `"top"`). Applies **only to the provider menu**.
- **`menu_order`** — integer-like ordering within the menu (e.g. `100`, `200`). Lower renders first.
- **`show_in_panel`** — boolean. When `true`, the app shows alongside the other panel buttons instead of inside the app drawer, raising its visibility.
- **`panel_priority`** — integer ordering **within the panel** when `show_in_panel` is `true` (e.g. `100`, `200`). Lower renders first.

### Render / sort rule

Apps in the same surface render by **`menu_order` ascending** (`panel_priority` ascending for panel buttons). The ordering is nullable: an entry with **no order value sorts to the top** (NULLs first), and **ties fall back to install order**. So an app with `menu_order` unset outranks every app that sets one.

**Choosing a `menu_order` to land between neighbors:** pick any value strictly between the two neighbors' orders. Given apps at `90`, `100`, and `150`, they render in that order; to land a new app between `100` and `150`, give it any value in `(100, 150)` — e.g. `120`. To force an app to the very top of the surface, leave its order unset (NULLs sort first) rather than guessing a smaller number than every existing app.

### ActionButton and NoteApplication — placement is in the handler, not the manifest

Some surfaces are placed by **class attributes on the handler**, not by `applications[]`:

- **`ActionButton`** — `BUTTON_LOCATION` picks the surface (`NOTE_HEADER`, `NOTE_FOOTER`, `CHART_SUMMARY_VITALS_SECTION`, `CHART_SUMMARY_ALLERGIES_SECTION`, …); `PRIORITY` (integer) orders buttons within that location, ascending, lower first, default `0`.
- **`NoteApplication`** tabs — `PRIORITY` (integer) orders tabs within the note, ascending, lower first, default `0`.

When asked where one of these lands, read `BUTTON_LOCATION` / `PRIORITY` off the handler class — the manifest `applications[]` fields above do not govern them.

## Related Skills

- **canvas-sdk** — what you can *build*: SDK classes, handlers, events, effects, data models, manifest structure. Use it to scaffold the plugin once this skill confirms Canvas doesn't already cover the need.
- The boundary: **`canvas-sdk` = what you can build; `canvas-platform` = what Canvas already does natively + where the UI lands.** Check `canvas-platform` before building; use `canvas-sdk` to build.
