---
name: canvas-platform
description: Canvas native-feature reference. Use whenever a question or plan touches whether Canvas already does something natively ("can we set up appointment reminders?", "does Canvas handle X out of the box?"). The bundled docs are the source of truth; do not answer from memory.
---

# Canvas Native-Feature Reference

This skill helps determine **what Canvas already does natively**. It bundles a two-tier native-feature reference — a grep-able index plus a full-body corpus.

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

## Related Skills

- **canvas-sdk** — what you can *build*: SDK classes, handlers, events, effects, data models, manifest structure. Use it to scaffold the plugin once this skill confirms Canvas doesn't already cover the need.
- The boundary: **`canvas-sdk` = what you can build; `canvas-platform` = what Canvas already does natively.** Check `canvas-platform` before building; use `canvas-sdk` to build.
