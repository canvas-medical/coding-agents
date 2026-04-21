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
  version: "4.8.0"
  author: Vicert
allowed-tools: Read, Grep, Glob
---

# Canvas Plugin UI Design System

Complete design system for Canvas plugin user interfaces. All rules are derived from the Canvas home-app front-end to ensure plugins look native alongside the main application.

## Workflow

**Read [references/workflow.md](references/workflow.md) before starting any UI work.** It defines the step by step process for building new plugin UI and improving existing plugin UI. The workflow handles both cases through decision points at each step.

The workflow references the files below at the appropriate steps. Do not read all references up front. Load each one when the workflow step calls for it.

### Reference Files

- [references/workflow.md](references/workflow.md) — Routing table for each phase of UI work, refactor safety protocol
- [DESIGN.md](DESIGN.md) — Visual specification. Color palette, typography, spacing, shape, token system, text pairing, density, truncation, dates, patterns without components
- [references/web-components.md](references/web-components.md) — Component APIs (attributes, events, CSS custom properties, slots), loading modes
- [assets/canvas-plugin-ui.css](assets/canvas-plugin-ui.css) — Combined tokens and typography, the single source of truth for all CSS variables and type styles
- [assets/canvas-plugin-ui.js](assets/canvas-plugin-ui.js) — All 25 web components bundled into a single script
- [assets/head.html](assets/head.html) — Copy-paste snippet with the three tags needed in the plugin HTML head
- [references/component-usage.md](references/component-usage.md) — Decision rules for when to use which component, banner and modal patterns, button color discipline
- [references/surface-selection.md](references/surface-selection.md) — When to use left nav, right pane, modal, note buttons, bento grid
- [references/interaction-patterns.md](references/interaction-patterns.md) — Keyboard nav, focus management, ARIA, toggle-submit prohibition, touch targets, patient safety
- [references/validation-checklist.md](references/validation-checklist.md) — Post-generation checklist, run after every UI change

## How Styles and Components Load in Canvas Plugins

The design system loads as three tags in the plugin's HTML head. A Google Fonts `<link>` for Lato, a `<link rel="stylesheet">` for `canvas-plugin-ui.css`, and a `<script src="...">` for `canvas-plugin-ui.js`. These files are served through SimpleAPI routes and all pages rendered into the shell inherit them. See the Loading Components section and Plugin HTML Boilerplate in [references/web-components.md](references/web-components.md) for details.

## Design System Prerequisite

When working inside a Canvas plugin directory that uses `<canvas-*>` web components, check if the plugin's `static/` directory contains `canvas-plugin-ui.js` and `canvas-plugin-ui.css`. If either file is missing, stop and tell the user to copy them from the skill's `assets/` directory into the plugin's static directory and set up the serving routes before proceeding with any `<canvas-*>` markup.

## Key Rules to Never Forget

- Green is rare. Only for clinical state transitions that affect the patient record or leave the system (sign/lock note, send message to patient, submit referral, confirm fax, check in patient). Blue is the default for all standard actions (save, done, next, edit, add). Most screens have blue buttons only.
- Never combine toggle switches with a Save or Submit button. Toggles mean instant effect. If a form has any save or submit action, every boolean control must be a checkbox. This is the single most common UI mistake in generated plugin code.
- Plugin-specific CSS values come from tokens. No hardcoded hex, px, font-family, or border-radius in plugin CSS. Components handle their own internal styles.
- Minimum touch target is 44px by 44px. Clinicians use tablets at the bedside.
- Use absolute dates ("Mar 24, 2026") for clinical data. Never relative ("2 days ago").
- Spacing grid: 4, 8, 12, 16, 20, 24 px (see [design.md](DESIGN.md) Spacing Scale for usage context).
- Right chart pane plugins (`RIGHT_CHART_PANE` and `RIGHT_CHART_PANE_LARGE`) must have `padding-bottom: 120px` to clear the Pylon Chat widget. See [surface-selection.md](references/surface-selection.md) for details. This does not apply to other surfaces.
- On colored backgrounds, text must be white and bold. On gray backgrounds, only dark text (see [design.md](DESIGN.md) Text and Background Pairing).
- All 25 components have documented APIs in [references/web-components.md](references/web-components.md). Check the API before using any component. Do not write raw HTML for elements that have a web component. This includes `<input>`, which is always `canvas-input`, `<select>`, which is always `canvas-dropdown` or `canvas-combobox`, and `<details>` with `<summary>`, which is always `canvas-accordion` with `canvas-accordion-item`, `canvas-accordion-title`, and `canvas-accordion-content`.
- Form elements sharing a visual row must render at the same height. The `size` attribute is not a universal height tier across components. Do not mix `size="sm"` and default in the same row. See Same Row Height Cohesion in [references/component-usage.md](references/component-usage.md).
- When refactoring existing plugin HTML that contains JavaScript, scan all script blocks and inline event handlers before changing markup. If JavaScript references an element being changed (by id, class, data attribute, or tag type), that element is structurally bound. Update the JavaScript at the same time as the markup, or surface the migration to the user when the path is unclear. Read the refactor safety steps in [references/workflow.md](references/workflow.md) before modifying structurally bound elements.
- Watch for global CSS resets in the plugin style tag. Universal selector rules (`* { margin: 0; padding: 0; box-sizing: border-box; }`), unscoped `html` or `body` rules that set typography, linked reset libraries (normalize.css, reset.css, sanitize.css, modern-normalize.css), and Tailwind Preflight all override canvas web component styles. Padding on the `canvas-accordion` family (which is light DOM) gets stripped directly. Typography inherits across the Shadow DOM boundary and replaces Lato inside every component. Host box sizing shifts on every `<canvas-*>` element. When a plugin ships with a reset, flag it and offer to remove or scope it before proceeding with component work. See Global CSS Resets in [references/workflow.md](references/workflow.md) Common Mistakes.
- Empty, loading, and error are three states, not one. Render `canvas-loader` during fetch, the typed empty pattern only after fetch resolves with zero rows, and `canvas-banner variant="error"` on failure. Empty states are typed by cause (first use, user cleared, filter no results). A filter bar that can produce zero results must pair with a Clear filters action in the filter no results empty state. See Empty States in [references/component-usage.md](references/component-usage.md) and [DESIGN.md](DESIGN.md) Empty State.

## Visual Specification

For the complete color palette, token tables, typography, spacing, shape, and all visual rules, see [DESIGN.md](DESIGN.md).

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
- Spacing between elements. Follow the spacing grid (4, 8, 12, 16, 20, 24px) but pick the value that fits the density of the view.
- Button text content.
- Number of options in a dropdown or combobox.
