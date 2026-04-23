# Canvas Plugin UI Skill

Design system for Canvas plugin interfaces. Ensures plugins look native alongside the Canvas home-app. All visual values verified against the live application.

The skill activates automatically when the task involves plugin HTML or CSS. You can also invoke it explicitly with `/canvas-plugin-ui`.

## What You Get

The skill produces complete HTML pages ready to serve from a Canvas plugin. All UI is built from native web components with Shadow DOM scoped styles. Plugin-specific CSS goes in a `<style>` tag using token references. For the full loading pattern and SimpleAPI routes, see [references/setup.md](references/setup.md).

Canvas ships a closed component set covering button, button-group, badge, chip, input, textarea, radio, checkbox, toggle, banner, card, inline-row, dropdown, combobox, multi-select, menu-button, popover, tabs, accordion, modal, table, sortable-list, sidebar-layout, scroll-area, loader, progress, tooltip, and divider. The authoritative component list lives in [references/web-components.md](references/web-components.md).

## Getting Good Results

### New plugin views

Describe what the view shows and what actions the user can take. Name the surface if you know it (right chart pane, full page, modal). See [surface-selection.md](references/surface-selection.md) for the full list of triggers and surfaces. List the components you expect (table, form, dropdown, tabs). The skill picks the rest.

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

When the HTML has JavaScript, mention the plugin's key behaviors. The skill scans all JS dependencies before touching markup, but knowing what matters most helps it prioritize. Describe what the interactive elements do, what triggers API calls, and what state management exists. Note that migrating from class-based HTML patterns to web component elements is a structural change that triggers the protocol in [references/refactor-safety.md](references/refactor-safety.md).

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
# First pass, full audit
Apply the Canvas design system to the HTML templates in this plugin.
Audit all views and fix anything that doesn't match Canvas.

# Second pass, fix specific issues you notice
The badge colors on the campaign status table don't feel right.
Pending should be blue, not yellow. Also the action buttons in the
table rows are too wide.

# Third pass, polish
The form spacing feels loose. Tighten up the gap between form groups
and make the filter bar more compact.
```

Each follow-up invocation loads the same design system context, so the skill stays consistent across iterations.

## Design Rules

The skill enforces a closed color palette, button color discipline (green is rare, blue is default), a toggle-submit prohibition, token-only CSS values, and 44 px minimum touch targets. For the reference file map and the customization boundaries, see [SKILL.md](SKILL.md).

## Info

*This skill was developed and contributed by [Vicert](https://vicert.com).*
*engineering@vicert.com*
