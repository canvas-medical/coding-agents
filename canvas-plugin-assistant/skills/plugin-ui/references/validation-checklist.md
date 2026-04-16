# UI Validation Checklist

Six-phase validation protocol. Each phase must pass with zero violations before the next phase begins. Fix violations immediately as you find them. Do not batch fixes across phases.

## Execution Discipline

Before starting validation, reread the generated HTML as a string. Do not validate from what you remember writing. Read the actual output.

Every check is binary. The condition either holds in the generated HTML or it does not. There is no "mostly compliant." If a check fails, fix the HTML, then restart the current phase from check 1. Only advance to the next phase after a complete clean pass.

## Phase 0. Preconditions

Verify the plugin loads the design system correctly and bundled assets exist.

1. The plugin's `static/` directory contains `canvas-plugin-ui.js` and `canvas-plugin-ui.css`. If either file is missing, stop and tell the user to copy them from the skill's `assets/` directory into the plugin's static directory before proceeding.
2. Compare line counts of the plugin's static files against the skill source files (`assets/canvas-plugin-ui.js` and `assets/canvas-plugin-ui.css`). Run `wc -l` on each pair. If any counts differ, warn the user that the skill's source files may have been updated since the plugin's copies were placed. Offer to recopy. Do not recopy without user approval.
3. The `<head>` contains a Google Fonts `<link>` tag loading the Lato family, a `<link>` to `canvas-plugin-ui.css`, and a `<script>` to `canvas-plugin-ui.js`. All paths use the correct static prefix for the plugin.
4. The Google Fonts `<link>` tag is present. Plugin iframes do not inherit the parent page's fonts, so the font must be loaded explicitly via a link tag.
5. No `<style>` tag contains base component classes or `:root` variable blocks copied from the old system. Web components handle their own styles internally.

## Phase 1. Element Verification

Verify all web components are used correctly.

1. **Tag name check.** Every `<canvas-*>` element in the HTML matches one of the registered component names. Misspelled tags render as empty unknown elements. The valid names are: canvas-button, canvas-badge, canvas-chip, canvas-input, canvas-radio, canvas-checkbox, canvas-toggle, canvas-banner, canvas-card, canvas-card-body, canvas-card-footer, canvas-dropdown, canvas-combobox, canvas-multi-select, canvas-option, canvas-tabs, canvas-tab, canvas-tab-label, canvas-tab-panel, canvas-accordion, canvas-accordion-item, canvas-accordion-title, canvas-accordion-content, canvas-modal, canvas-modal-header, canvas-modal-content, canvas-modal-footer, canvas-table, canvas-table-head, canvas-table-body, canvas-table-row, canvas-table-cell, canvas-sortable-list, canvas-sortable-item, canvas-sidebar-layout, canvas-sidebar, canvas-content, canvas-loader, canvas-button-group, canvas-textarea, canvas-tooltip, canvas-progress, canvas-divider.
2. **Attribute check.** Every attribute set on a `<canvas-*>` element is documented in web-components.md for that component. Unknown attributes are silently ignored.
3. **No native replacements.** No `<select>` elements anywhere. No `<input type="checkbox">` or `<input type="radio">` outside of a web component. Use canvas-dropdown, canvas-checkbox, canvas-radio.
4. **Plugin-specific CSS uses tokens.** Scan the `<style>` tag for any CSS rules. All color, spacing, radius, font-family, and transition values must use `var(--token)` references. The only allowed raw values are `0`, `none`, `auto`, `100%`, position values, and `z-index` integers.

## Phase 2. Component Usage Audit

Inventory which component types are present. Run only the checks relevant to components found.

### Buttons (canvas-button)

1. Green (`variant="primary"`) only for clinical state transitions (sign/lock note, send to patient, submit referral, confirm fax, check in). All other actions are blue (default variant). If the button text is "Save", "Done", "Next", "Add", "Edit", or "Update", it must be blue. Defined in SKILL.md Key Rules.
2. At most one green button on the entire page.
3. Cancel, dismiss, close, and neutral actions use `variant="ghost"`.
4. Disabled buttons use the `disabled` attribute on the existing variant.
5. Button groups place the main action on the right, cancel on the left.

### Toggle and Checkbox

1. Scan each discrete UI segment (form, card, accordion section, modal) for both a `canvas-toggle` and a submit or save action (`type="submit"`, or button text containing Save, Submit, Done, Apply, Confirm). If both exist in the same segment, the check fails. Toggles in a separate, unrelated segment are allowed when their effect is independent and instant. When in doubt about segment boundaries, treat the nearest shared ancestor container as the boundary. Defined in SKILL.md Key Rules and interaction-patterns.md Toggle and Submit Prohibition.

### Dropdowns and Comboboxes

1. canvas-dropdown used for fixed lists. canvas-combobox used for searchable lists. canvas-multi-select used for multi-value selection with 8 or more options.

### Tables (canvas-table)

1. Table has `aria-label` attribute.
2. Action cells use the `actions` attribute on canvas-table-cell.
3. Variant matches data density. Standard data uses default. Claims, lab values, ledger breakdowns use `compact`.

### Tabs (canvas-tabs)

1. Each canvas-tab has a `for` attribute matching a canvas-tab-panel `id`.
2. Each canvas-tab contains a canvas-tab-label.

### Accordions (canvas-accordion)

1. Each canvas-accordion-item contains exactly one canvas-accordion-title and one canvas-accordion-content.

## Phase 3. UX Patterns

Cross-component behavioral rules spanning the whole page.

1. **Button color audit.** Every `variant="primary"` button has text matching a clinical state transition (sign, lock, send, submit referral, confirm fax, check in). If not, change to default (blue). Defined in SKILL.md Key Rules.
2. **Form element height cohesion.** When canvas-input, canvas-dropdown, canvas-combobox, and canvas-button appear on the same row, they match sizes. Default pairs with default. `size="sm"` pairs with `size="sm"`.
3. **Date formatting.** All visible date strings in clinical contexts use absolute format ("Mar 24, 2026"). No relative dates ("2 days ago"). Defined in DESIGN.md Date and Time Display.
4. **Empty states.** Every canvas-table-body, list container, or data section has an empty state handler.
5. **Loading states.** If the plugin fetches data, a loading indicator exists for the loading state.
6. **Patient context.** If the plugin runs as a modal or standalone page and displays patient-specific data, the patient name and at least one identifier (DOB or MRN) must be visible near the top (see surface-selection.md Surfaces).

## Phase 4. Functional Preservation

Only runs when refactoring existing HTML that contained JavaScript. Skip for newly generated HTML.

1. **Script block presence.** If the original HTML had `<script>` tags, the refactored HTML must have `<script>` tags.
2. **getElementById targets.** Every `getElementById('...')` call in JavaScript has a matching `id` in the HTML.
3. **querySelector targets.** Every `querySelector('...')` call matches at least one element.
4. **Inline handler targets.** Every inline event attribute calls a function defined in a `<script>` tag.
5. **Form name contracts.** If JavaScript reads form data through `name` attributes, those names still exist on equivalent elements or the submission code is updated.
6. **Data attribute contracts.** If JavaScript reads `dataset.*` on specific elements, those `data-*` attributes still exist.
7. **Function count integrity.** Every named function in the original scripts exists in the refactored scripts (unless explicitly marked for removal in a migration declaration).

## Phase 5. Accessibility

1. **Touch targets.** 44px minimum touch target on all interactive elements through element size or padding. Web components handle this for their own interactive areas. Defined in interaction-patterns.md Accessibility and Touch Targets.
2. **Label association.** Every canvas-input, canvas-dropdown, canvas-combobox, and canvas-multi-select has a `label` attribute or an external label.
3. **Color independence.** No information conveyed by color alone. Badges have text labels. Error states have text messages.
4. **Right pane clearance.** `padding-bottom: 120px` on the outermost scrollable container for RIGHT_CHART_PANE and RIGHT_CHART_PANE_LARGE surfaces. Does not apply to other surfaces. Defined in surface-selection.md Right Chart Pane.

## Phase 6. Visual Polish

1. **Palette compliance.** No purple, teal, pink, cyan, or other colors outside the closed palette. Search all plugin-specific CSS and inline styles for off-palette colors. Defined in DESIGN.md Color Palette and Roles.
2. **Text-background pairing.** On white backgrounds, dark and muted text allowed. On gray backgrounds, only dark text. On colored backgrounds, white bold text. Defined in DESIGN.md Text and Background Pairing.
3. **Token usage.** All spacing, color, radius, and font values in plugin-specific CSS use `var(--token)` references. Defined in DESIGN.md Token System.

---

After all six phases pass with zero violations, the UI is validated.
