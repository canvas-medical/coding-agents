---
name: canvas-platform
description: Canvas native-feature reference. Use whenever an answer depends on what Canvas already does without a plugin — feasibility ("can Canvas do X, and how?"), config-first alternatives (a setting, role, template, or protocol instead of code), out-of-the-box workflows and UI behavior, adjacent native capabilities worth suggesting, mapping a clinical term to a native feature, the native/configuration side of compliance (EPCS, billing, consent) and integrations (FHIR, pharmacy, labs), debugging something that may be expected native behavior, plain "how does Canvas do X?" education, and avoiding building something Canvas already ships. Not for SDK build questions (events, effects, data models, handlers, manifest, CLI) — that is canvas-sdk. The bundled docs are the source of truth; do not answer from memory.
---

# Canvas Native-Feature Reference

This skill is the reference for **what Canvas already does natively — without a plugin**. It bundles a two-tier native-feature reference drawn from the Canvas Help Center: a grep-able index plus a full-body corpus.

## What This Skill Answers

Use this skill whenever the answer depends — even in passing — on Canvas's shipped, no-code behavior. Concretely:

- **Feasibility routing** — "can Canvas do X?" Check here first for a native path, then hand off to `canvas-sdk` for the build path if there isn't one.
- **Config-first alternatives** — the ask may be a setting, role, permission, template, questionnaire, or protocol rather than code.
- **Platform behavior claims** — how a workflow, default, or screen behaves out of the box, before any customization.
- **Adjacent native capability** — Canvas also ships Y, which the user probably wants to know about even though they didn't ask.
- **Concept and terminology mapping** — a clinical or operational term ("recall", "superbill", "care gap") that maps onto a named Canvas feature.
- **Compliance surfaces** — the native handling and configuration side of EPCS, billing, and consent.
- **Integration cooperation** — the native behavior and configuration side of FHIR, pharmacy, lab, and partner integrations.
- **Debugging** — whether the behavior someone is calling a bug is in fact documented native behavior.
- **Non-build education** — "how does Canvas do X?" asked with no intention of building anything.
- **Redundancy avoidance** — a native feature already covers the ask, so the plugin shouldn't be built.

This applies to a one-line conversational question just as much as to plugin-building work. Redundancy avoidance is the last item on that list, not the point of the skill.

**Not this skill — use `canvas-sdk` instead** for anything about what you can *build*: event types and contexts, effect types and payloads, SDK data models and their field/import names, handler types, `CANVAS_MANIFEST.json` structure, the Canvas CLI, surface/handler terminology, `sdk_version` and deprecations, and build patterns. If a question has both a native side and a build side, answer the native side from here and the build side from `canvas-sdk`.

## Grounding Rule — Read Before Answering

**Never describe Canvas's native behavior from memory** — not whether a capability exists, not how a workflow behaves by default, not where a setting lives — **and never propose to build a capability before checking whether Canvas already ships it.** The Help Center changes independently of any code, and the model's prior about Canvas's native surface is frequently wrong or out of date.

Before stating anything about what Canvas natively does, how it behaves by default, or how it is configured — or before scaffolding a plugin for a capability — run the **two-tier lookup**:

1. **Grep `canvas_platform_index.txt`** (the index, in this skill's directory) for the capability's keywords. The index is title/heading-only, so a keyword returns clean candidate articles — each a `- [Title](url)` bullet with its `## Subsection` outline indented beneath it — not dozens of noisy body hits.
2. **Read that one article's body** from `canvas_platform_context.txt` by grepping its `----- BEGIN PAGE <url>` block, then locate the relevant `## Subsection`.
3. Base the answer on what that body actually says.
4. **Cite the article as a markdown link: `[Article Title](https://help.canvasmedical.com/articles/...)`.** Copy it verbatim from the index — the index bullets are already in exactly this form (`- [Fax Migration & Event History](https://help.canvasmedical.com/articles/4882014801-fax-migration-event-history)`), so reuse the bullet's text and URL rather than composing your own. Never emit a bare `----- BEGIN PAGE` line or a naked URL as the citation.

This applies to a one-line conversational question just as much as to plugin-building work. If a question is even partially about a Canvas native capability and you have not yet consulted this skill in the current conversation, consult it first, then answer.

## Claim Discipline — Hedge Coverage, Assert Facts

Two different kinds of statement can come out of this skill, and they carry different confidence.

**Assert what the article says.** If you read it here, state it plainly and cite the article. "Canvas logs every fax event with a status and timestamp — [Fax Migration & Event History](...)." Hedging a plainly-cited fact makes a grounded answer read as a guess and wastes the lookup.

**Hedge whether it covers *their* need.** Any claim of the form "Canvas already handles this, so don't build it" is a coverage claim about a requirement you have only partly heard, and it should stay a pointer:

> "Canvas **may** cover this — see `[Article Title](<article-url>)`; confirm whether it covers your specific need before we build."

A native feature often covers only part of a request — native Appointment Reminders send a single org-wide reminder, so a flat "don't build, Canvas does this" would be wrong for a use case needing per-provider or multi-touch reminders. A wrong "Canvas already handles this" poisons trust worse than over-building: it steers the user away from something they actually need.

The rule in one line: **facts from the corpus are asserted and cited; conclusions about sufficiency are offered and confirmed.**

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
3. **Cite the article as a `[Article Title](url)` markdown link**, copied verbatim from the index bullet for the page whose section you used — not a bare `BEGIN PAGE` line or naked URL.

**NEVER attempt to curl or download either file — both are already bundled here.**

## Related Skills

Route by what the *answer* is about:

- **`canvas-platform` (this skill) — native / no-code.** "Is there a shipped feature, setting, or admin workflow that does X **without a plugin**?" Source: the bundled Help Center corpus.
- **`canvas-sdk` — build / model.** "Can I build or model X with the SDK, and how?" Events, effects, data models, handlers, manifest. Source: the bundled docs-site corpus. Use it to scaffold once this skill has established that nothing native covers the need — or alongside this skill when the answer has both a native and a build half.
- **Omniplug MCP tools — instance state and plugin inventory.** "What plugins does this customer already have, what does each one do, and where does its UI land?" Use `get_customer_plugins` (name, version, manifest description, match status), `describe_plugin` (manifest, README, match status, file listing — it falls back to the reference index, so it also answers "what does this Canvas-managed plugin we don't have do?"), `get_plugin_placement` (scope, menu position, menu order, panel visibility from the live instance database), and `list_reference_plugins` (what exists to install, with install and divergence counts). These answer questions about *one instance's state*, which is not Canvas's native surface and not the SDK.
- **`instance-analyze`** — the local-dev path to the same instance picture, via the Canvas admin portal. It needs a root password from a local `~/.canvas/credentials.ini`, so it is for a developer working against an instance directly, not for Studio sessions.