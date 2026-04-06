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
  version: "2.0.0"
  author: vicert
allowed-tools: Read, Grep, Glob
---

# Canvas Plugin UI Design System

Complete design system for Canvas plugin user interfaces. All rules are derived from the Canvas home-app front-end to ensure plugins look native alongside the main application.

## Color Palette Quick Reference

This palette is closed. Never use purple, teal, pink, or cyan.

| Token | Hex | Role |
|---|---|---|
| Green | `#22BA45` | Primary actions (save, submit, confirm), success |
| Blue | `#2185D0` | Secondary actions, links, focus rings, info badges |
| White | `#FFFFFF` | Backgrounds, card surfaces, input backgrounds |
| Light Gray | `#F5F5F5` | Page backgrounds, disabled inputs |
| Mid Gray | `#E9E9E9` | Borders, dividers, inactive toggles |
| Red | `#BD0B00` | Destructive actions only, errors |
| Orange | `#ED4A0B` | Warnings, stale indicators |
| Brown | `#935330` | Reserved, almost never used |
| Dark Text | `rgba(0,0,0,0.87)` | Primary text |
| Muted Text | `#767676` | Secondary text (only on white backgrounds) |

## Key Rules to Never Forget

- Green is rare. Only for clinical state transitions that affect the patient record or leave the system (sign/lock note, send message to patient, submit referral, confirm fax, check in patient). Blue is the default for all standard actions (save, done, next, edit, add). Most screens have blue buttons only.
- Never combine toggle switches with a Save or Submit button. Toggles mean instant effect. If a form has any save or submit action, every boolean control must be a checkbox. This is the single most common UI mistake in generated plugin code.
- Plugin-specific CSS values come from tokens. No hardcoded hex, px, font-family, or border-radius in plugin CSS. Components handle their own internal styles.
- Minimum touch target is 44px by 44px. Clinicians use tablets at the bedside.
- Use absolute dates ("Mar 24, 2026") for clinical data. Never relative ("2 days ago").
- Spacing grid: 4, 8, 12, 16, 20, 24 px.
- Right chart pane plugins must have `padding-bottom: 120px` to clear the Pylon Chat widget.
- On colored backgrounds, text must be white and bold. On gray backgrounds, only dark text.
- All 18 components have documented APIs in [references/web-components.md](references/web-components.md). Check the API before using any component. Do not write raw HTML for elements that have a web component.
- When refactoring existing plugin HTML that contains JavaScript, scan all script blocks and inline event handlers before changing markup. If JavaScript references an element being changed (by id, class, data attribute, or tag type), that element is structurally bound. Update the JavaScript at the same time as the markup, or surface the migration to the user when the path is unclear. Read the refactor safety steps in [references/workflow.md](references/workflow.md) before modifying structurally bound elements.

## Customization Boundaries

Every form element has properties split into three tiers. This determines what the agent can adjust and what stays fixed.

**Locked. Never change unless the user explicitly overrides.**
- Checkbox: entire appearance is fixed. Shape, size, white background, dark checkmark, border color, border-radius, checked/unchecked states. The canvas-checkbox component handles checked state internally.
- Radio: entire appearance is fixed. Circle shape, dot centering, dot color, border color, border-radius 500rem, checked/unchecked states. The canvas-radio component handles checked state internally.
- Toggle: track colors (blue active, gray inactive), track shape, thumb shape and color. Never use green for the active track.
- Border-radius: `.28571429rem` on all rounded elements (inputs, buttons, cards, dropdowns, badges). Never use a different radius.
- Border styles and colors on inputs, dropdowns, comboboxes: gray default border, blue `#96c8da` focus border. These do not change.
- Label-to-input relationship: label above input, spacing `.28571429rem`. Toggle label inline.
- Toggle-to-submit prohibition: toggles never appear on a screen with a submit button.
- Button colors: green only for clinical state transitions, blue for standard actions, gray (`btn-default`) for cancel and neutral actions, red for destructive. Disabled is `opacity: 0.45` on any variant via the `disabled` attribute.

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

## How Styles and Components Load in Canvas Plugins

Components and tokens are served as external files through SimpleAPI routes. The plugin's HTML shell links `tokens.css` and `typography.css` via `<link rel="stylesheet">` and `canvas-components.js` via `<script src="...">`. All pages rendered into that shell inherit both. See the Loading Components section and Plugin HTML Boilerplate in [references/web-components.md](references/web-components.md) for details.

## Escalation Ladder

When building plugin UI, exhaust each level before moving to the next.

1. **Use existing components.** Compose `<canvas-*>` elements. No friction.
2. **Customize through attributes and slots.** Set variant, size, color, slot content. No friction.
3. **Override through CSS custom properties.** Set `--canvas-{component}-{property}` tokens. Light friction, confirm the override is necessary.
4. **Build novel HTML/CSS using tokens.css.** For layouts no component covers. Significant friction, exhaust component options first.

Full details in [references/web-components.md](references/web-components.md).

## Design System Prerequisite

When working inside a Canvas plugin directory that uses `<canvas-*>` web components, check if the plugin's `static/` directory contains `canvas-components.js`, `tokens.css`, and `typography.css`. If any file is missing, stop and tell the user to run the bundle script (`scripts/bundle.sh`) targeting the plugin's static directory and set up the serving routes before proceeding with any `<canvas-*>` markup.

## Workflow

**Read [references/workflow.md](references/workflow.md) before starting any UI work.** It defines the step by step process for building new plugin UI and improving existing plugin UI. The workflow handles both cases through decision points at each step.

The workflow references the files below at the appropriate steps. Do not read all references up front. Load each one when the workflow step calls for it.

## Reference Files

- [references/workflow.md](references/workflow.md) — Step by step process, hard rules vs soft proposals, decision points
- [references/web-components.md](references/web-components.md) — Component APIs (attributes, events, CSS custom properties, slots), token system, escalation ladder, loading modes, orphan patterns
- [assets/tokens.css](assets/tokens.css) — `:root` CSS variables, the single source of truth for all token values
- [assets/typography.css](assets/typography.css) — Heading and paragraph styles, Lato font loading
- [references/component-usage.md](references/component-usage.md) — Decision rules for when to use which component, banner and modal patterns, button color discipline
- [references/surface-selection.md](references/surface-selection.md) — When to use left nav, right pane, modal, note buttons, bento grid
- [references/clinical-ux.md](references/clinical-ux.md) — Touch targets, info density, scanning, confirmation hierarchy, dates, patient safety
- [references/interaction-patterns.md](references/interaction-patterns.md) — Keyboard nav, focus management, ARIA, toggle-submit prohibition
- [references/validation-checklist.md](references/validation-checklist.md) — Post-generation checklist, run after every UI change
