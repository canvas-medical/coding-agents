# Canvas Plugin UI Skill

Design system for Canvas plugin interfaces. Ensures plugins look native alongside the Canvas home-app. All visual values verified against the live application.

The skill activates automatically when the task involves plugin HTML or CSS. You can also invoke it explicitly with `/canvas-plugin-ui`.

## What You Get

The skill produces complete HTML pages ready to serve from a Canvas plugin. The design system loads as three external files (tokens.css, typography.css, canvas-components.js) served through SimpleAPI routes, and all UI is built from native web components with Shadow DOM scoped styles. Plugin-specific CSS goes in a `<style>` tag using token references.

18 components are available. Button, badge, chip, input, radio, checkbox, toggle, banner, card, dropdown, combobox, multi-select, tabs, accordion, modal, table, sortable-list, sidebar-layout.

## Getting Good Results

### New plugin views

Describe what the view shows and what actions the user can take. Name the surface if you know it (right chart pane, left sidebar page, modal). List the components you expect (table, form, dropdown, tabs). The skill picks the rest.

```
Build a right chart pane plugin that shows the patient's active medications
in a table with dose, frequency, and status columns. Include a search input
to filter by medication name and a button to add a new medication.
```

For multi-view plugins, describe each view. The skill runs its workflow independently for each one.

```
This plugin has three views. A left sidebar nav page that lists all
campaigns in a table with status badges. A settings page with a form
for notification preferences using checkboxes and a dropdown for
default provider. A detail page that shows campaign metrics and a
multi-select combobox for filtering by location.
```

### Existing plugin overhaul

Point at the existing plugin HTML and ask for a design system audit. The skill reads the current markup, identifies deviations from Canvas, and fixes them.

When the HTML has JavaScript, mention the plugin's key behaviors. The skill scans all JS dependencies before touching markup, but knowing what matters most helps it prioritize. Describe what the interactive elements do, what triggers API calls, and what state management exists. Note that migrating from class-based HTML patterns to web component elements is a structural change that triggers the refactor safety protocol in workflow.md.

```
Apply the Canvas design system to the campaign management plugin. It has
tabs that switch between campaign and history views, a provider dropdown
that triggers an API filter on change, and toggle controls in the settings
tab that save immediately. Preserve all existing behavior.
```

For a targeted fix on a specific view or component.

```
The settings page in this plugin uses toasts for feedback and toggles
in a form with a save button. Fix this to match Canvas patterns.
```

### Iterating

The first pass handles the bulk of the work. Follow up with targeted requests to refine.

```
# First pass — full audit
Apply the Canvas design system to the HTML templates in this plugin.
Audit all views and fix anything that doesn't match Canvas.

# Second pass — fix specific issues you notice
The badge colors on the campaign status table don't feel right.
Pending should be blue, not yellow. Also the action buttons in the
table rows are too wide.

# Third pass — polish
The form spacing feels loose. Tighten up the gap between form groups
and make the filter bar more compact.
```

Each follow-up invocation loads the same design system context, so the skill stays consistent across iterations.

## Key Design Decisions

These are the rules that matter most and that AI agents violate most often.

**Buttons.** Green is rare, only for clinical state transitions (sign note, send message to patient). Blue is the default for all standard actions. Gray for cancel and neutral actions.

**Toggles vs checkboxes.** Toggles mean instant effect with no save button in the same UI segment. If there is a save or submit action in the same form, card, or section, every boolean must be a checkbox.

**Banners, not toasts.** Canvas uses inline banner components. No floating toasts, no snackbars, no auto-dismissing notifications anywhere. Error and warning banners are the primary feedback mechanism. Success banners are almost never used because Canvas communicates success through UI state changes (modal closes, form resets, row appears).

**Refactoring preserves JavaScript.** When applying the design system to existing plugin HTML, the skill scans all script blocks and inline event handlers before changing markup. Elements referenced by JavaScript are structurally bound. The skill updates the JavaScript at the same time as the markup, or stops and asks the user when the migration path is unclear. Migrating from class-based patterns to web component elements is a structural change covered by the refactor safety protocol in workflow.md.

**Font loading.** Typography.css handles Lato loading via `@import`. No manual Google Fonts link needed. Plugin iframes do not inherit the parent page's fonts.

**Design system loads as linked files.** The design system ships as three files served through SimpleAPI routes. `tokens.css` and `typography.css` are linked in the `<head>`, and `canvas-components.js` is loaded via a `<script>` tag. Plugin-specific CSS goes in a `<style>` tag using `var(--token)` references. No inlined base classes.

**Right chart pane clearance.** Plugins in the right chart pane need `padding-bottom: 120px` because the Pylon Chat widget overlaps the bottom-right corner.

**Palette is closed.** No purple, teal, cyan, pink. AI models reach for these to add variety. The Canvas palette does not include them.

**Escalation ladder.** The skill exhausts each level before moving to the next.

1. Use existing `<canvas-*>` components.
2. Customize through attributes and slots.
3. Override through CSS custom properties when attributes are not enough.
4. Build novel HTML/CSS with token references only as a last resort.

See [web-components.md](references/web-components.md) for the full ladder.

## Info

*This skill was developed and contributed by [Vicert](https://vicert.com).*

## Reference Files

Each reference file is self-contained and readable on its own. The agent loads them on demand during the workflow.

`SKILL.md` is the entry point. It loads automatically and the agent follows the workflow in `references/workflow.md`, loading reference files on demand at each step.

| File | Purpose |
|---|---|
| `assets/tokens.css` | CSS variables for colors, spacing, typography, borders, transitions |
| `assets/typography.css` | Heading and paragraph styles, Lato font loading |
| `references/web-components.md` | Component APIs, token system, escalation ladder, loading modes, orphan patterns |
| `references/workflow.md` | Build process with decision points for new vs existing UI |
| `references/component-usage.md` | When to use which component, banner and modal patterns, button color discipline |
| `references/surface-selection.md` | Decision sequence for where a view renders |
| `references/clinical-ux.md` | Touch targets, information density, date formatting, confirmation hierarchy |
| `references/interaction-patterns.md` | Keyboard navigation, focus management, ARIA, toggle-submit prohibition |
| `references/validation-checklist.md` | Six-phase post-generation validation protocol |
