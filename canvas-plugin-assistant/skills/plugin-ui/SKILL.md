---
name: canvas-plugin-ui
description: >
  Canvas plugin UI design system. Generates and refactors plugin HTML and
  inline CSS to match the Canvas home-app. Outputs complete HTML pages with
  tokens, web components, and validated markup. When refactoring
  existing HTML that has JavaScript, scans all DOM dependencies and flags
  structural changes that could break functionality before modifying markup.
  Triggers: plugin pages, forms, tables, buttons, tabs, dropdowns, banners,
  toasts, badges, chips, toggles, checkboxes, modals, cards, accordions,
  comboboxes, styling, look and feel, visual bugs, HTMLResponse content,
  plugin view creation or audit, UI that does not match Canvas. Also triggers
  when the user mentions toasts, notifications, or floating alerts because
  Canvas does not use those patterns.
compatibility: Designed for Claude Code. Targets Canvas plugin SDK with HTMLResponse delivery.
metadata:
  version: "4.14.0"
  author: Vicert
allowed-tools: Read, Grep, Glob
---

# Canvas Plugin UI Design System

Complete design system for Canvas plugin user interfaces. All rules are derived from the Canvas home-app front-end to ensure plugins look native alongside the main application.

## Workflow

**Read [references/workflow.md](references/workflow.md) before starting any UI work.** It defines the step by step process for building new plugin UI and improving existing plugin UI. The workflow handles both cases through decision points at each step.

The workflow references the files below at the appropriate steps. Do not read all references up front. Load each one when the workflow step calls for it.

## Reference Files

Each reference file answers exactly one question. Load on demand during the workflow.

| File | Question it answers |
|---|---|
| [references/setup.md](references/setup.md) | How to serve and load the design system |
| [references/workflow.md](references/workflow.md) | What are the ordered agent steps |
| [references/surface-selection.md](references/surface-selection.md) | Where does the plugin render |
| [references/component-usage.md](references/component-usage.md) | When to pick one component over another |
| [references/web-components.md](references/web-components.md) | How does each component work (API, keyboard, ARIA, visual spec) |
| [DESIGN.md](DESIGN.md) | What is the visual language (tokens, palette, typography, spacing, shape) |
| [references/patterns.md](references/patterns.md) | Copy-paste templates that span components |
| [references/interaction-patterns.md](references/interaction-patterns.md) | What cross-cutting interaction rules apply |
| [references/writing-style.md](references/writing-style.md) | How to write UI copy |
| [references/anti-patterns.md](references/anti-patterns.md) | Common mistakes with detection and fix |
| [references/refactor-safety.md](references/refactor-safety.md) | How to refactor existing HTML with JavaScript |
| [references/validation-checklist.md](references/validation-checklist.md) | Binary pass or fail scans after generation |

Bundled assets. [assets/canvas-plugin-ui.css](assets/canvas-plugin-ui.css) is the single source for all CSS variables and type styles. [assets/canvas-plugin-ui.js](assets/canvas-plugin-ui.js) bundles every web component. [assets/head.html](assets/head.html) is the copy-paste snippet with the three tags needed in the plugin HTML head.

## Cross-Cutting Rules

Do not restate rules in this file. The canonical homes live in the reference files above. Before building or refactoring, load these three at step 3 (component selection) and use them together.

- [component-usage.md](references/component-usage.md) for decision rules (button color discipline, same row height cohesion, card imitation detection, empty state types, confirmation hierarchy).
- [interaction-patterns.md](references/interaction-patterns.md) for behavioral rules (toggle and submit prohibition, focus management, 44 px touch targets, ARIA essentials, patient context safety).
- [anti-patterns.md](references/anti-patterns.md) for the patterns agents commonly miss (card imitations, native element use, mixed size tiers, action menu as dropdown, anchored surface as modal, empty during loading, AI puffery).

## Escalation Ladder

When building plugin UI, exhaust each level before moving to the next.

1. **Use existing components.** Compose `<canvas-*>` elements. No friction.
2. **Customize through attributes and slots.** Set variant, size, color, slot content. No friction.
3. **Override through CSS custom properties.** Set `--canvas-{component}-{property}` tokens. Light friction, confirm the override is necessary.
4. **Build novel HTML/CSS using [DESIGN.md](DESIGN.md) tokens.** For layouts no component covers. Significant friction, exhaust component options first.

## Customization Boundaries

Every form element has properties split into three tiers. This determines what the agent can adjust and what stays fixed.

**Locked. Never change unless the user explicitly overrides.**
- Checkbox: entire appearance is fixed. Shape, size, white background, dark checkmark, border color, border-radius, checked/unchecked states. The canvas-checkbox component handles checked state internally.
- Radio: entire appearance is fixed. Circle shape, dot centering, dot color, border color, border-radius 500rem, checked/unchecked states. The canvas-radio component handles checked state internally.
- Toggle: track colors (blue active, gray inactive), track shape, thumb shape and color. Never use green for the active track.
- Shape and border rules (radius, border styles, focus border) are defined in [DESIGN.md](DESIGN.md) Shape section. They are locked.
- Label-to-input relationship: label above input, spacing `.28571429rem`. Toggle label inline.
- Button colors: green only for clinical state transitions, blue for standard actions, gray (`variant="ghost"`) for cancel and neutral actions, red for destructive. Disabled is `opacity: 0.45` on any variant via the `disabled` attribute.

**Flexible with resistance. Keep defaults unless the user is direct and specific.**
- Height and vertical padding on text inputs, dropdowns, comboboxes. Default comes from `--input-padding`. Only change if the user says something like "make the inputs shorter" or "compact form."
- Button height and padding. Default comes from `--btn-padding`. Only change if the user explicitly asks.
- Button width. Buttons are naturally content-sized. Only stretch or fix width if the user insists.
- Font size on inputs and buttons. Default is `1em` for inputs, `1rem` for buttons. Only change if the user specifies a size.
- When any of these change in a local context, apply the Form Element Height Cohesion rule: match all sibling form elements in the same group.

**Free. Adjust to fit the layout and context.**
- Width of text inputs, dropdowns, comboboxes. These are naturally fluid and size to their container. The agent picks appropriate widths for the layout.
- Placeholder text content and whether to include it.
- Whether a label is present (labels are recommended but optional for space-constrained layouts like table filters).
- Spacing between elements. Follow the spacing grid (4, 8, 12, 16, 20, 24 px) but pick the value that fits the density of the view.
- Button text content.
- Number of options in a dropdown or combobox.
