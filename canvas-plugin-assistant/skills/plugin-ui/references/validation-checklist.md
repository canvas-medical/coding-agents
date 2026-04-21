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

1. **Tag name check.** Every `<canvas-*>` element in the HTML matches one of the registered component names. Misspelled tags render as empty unknown elements. The valid names are: canvas-button, canvas-badge, canvas-chip, canvas-input, canvas-radio, canvas-checkbox, canvas-toggle, canvas-banner, canvas-card, canvas-card-body, canvas-card-footer, canvas-inline-row, canvas-dropdown, canvas-combobox, canvas-multi-select, canvas-option, canvas-tabs, canvas-tab, canvas-tab-label, canvas-tab-panel, canvas-accordion, canvas-accordion-item, canvas-accordion-title, canvas-accordion-content, canvas-modal, canvas-modal-header, canvas-modal-content, canvas-modal-footer, canvas-table, canvas-table-head, canvas-table-body, canvas-table-row, canvas-table-cell, canvas-sortable-list, canvas-sortable-item, canvas-sidebar-layout, canvas-sidebar, canvas-content, canvas-loader, canvas-button-group, canvas-textarea, canvas-tooltip, canvas-progress, canvas-divider, canvas-scroll-area.
2. **Attribute check.** Every attribute set on a `<canvas-*>` element is documented in web-components.md for that component. Unknown attributes are silently ignored.
3. **No native replacements.** No `<select>` elements anywhere. No `<input type="checkbox">` or `<input type="radio">` outside of a web component. No `<details>` or `<summary>` elements anywhere. Use canvas-dropdown, canvas-checkbox, canvas-radio, canvas-accordion.
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
2. No native `<details>` or `<summary>` elements remain in the markup. Every collapsible section uses `canvas-accordion` with `canvas-accordion-item`, `canvas-accordion-title`, and `canvas-accordion-content`. The only accepted exception is a custom header row whose trigger content does not fit the accordion title slot (for example a medication group row with name, sig, badges, and actions). That exception still does not permit native `<details>` as the outer container.

### Inline Form Rows (canvas-inline-row)

1. No raw flex rows of form elements. Scan the markup for a `div` or other plain element with inline style or class CSS that includes `display: flex` and contains two or more `canvas-input`, `canvas-dropdown`, `canvas-combobox`, `canvas-multi-select`, `canvas-textarea`, or `canvas-button` children. Replace the container with `<canvas-inline-row>`. Remove any `flex-wrap`, `align-items`, `gap`, or per child flex rules, the component handles them.
2. No mixed size tier in one row. Scan `<canvas-inline-row>` children for `size="sm"` attributes. Either every element in the row is a button at `sm`, or no element uses `size="sm"`. Mixed tiers produce visibly mismatched heights. See Same Row Height Cohesion in `component-usage.md`.
3. No native input inside an inline row. A `<canvas-inline-row>` containing a raw `<input>` or `<select>` fails this check. Replace with `canvas-input` or `canvas-dropdown`.
4. Filter bar pattern uses canvas-card plus canvas-inline-row. A filter row sitting above a table that is not wrapped in a `<canvas-card><canvas-card-body><canvas-inline-row>...</canvas-inline-row></canvas-card-body></canvas-card>` structure is a migration target. Bulk action rows under the table use `<canvas-card-footer>`.

### Cards and Content Containers (canvas-card)

1. No raw card wrappers. Scan the markup for any element with a class name matching `card`, `panel`, `box`, or `tile` that is used as a content container. Replace with `<canvas-card>` and `<canvas-card-body>`. Remove any local CSS rule targeting that class. Exception, class names where the word `card` refers to something unrelated such as `card-number-input`.
2. No style signature imitations. Scan the plugin `<style>` tag and inline `style=` attributes for any rule that combines a light background, a border, a border-radius, and a box-shadow on a single element. Replace with `<canvas-card>` unless the element is a modal body or popover which share some of these properties by design.
3. Footers use the component. Any gray action strip at the bottom of a card that contains buttons must be a `<canvas-card-footer>`. No raw div with a gray background for this role.
4. Card padding is component owned. No `padding` rule on elements that are direct children of `<canvas-card-body>` other than layout spacing between child elements. The body applies `1em` padding unless `no-padding` is set.
5. Multiple titled sections use stacked bodies. If a card shows two or more titled sections with internal dividers, use adjacent `<canvas-card-body>` elements rather than custom dividers or horizontal rules.
6. No `max-height` on `canvas-card-body` expecting scrolling. The body is not a scroll container in 4.0.0 and later. Use `<canvas-scroll-area vertical>` inside the body instead.

### Scroll Areas (canvas-scroll-area)

1. No raw overflow on plugin level divs. Scan the plugin `<style>` tag and inline `style=` attributes for `overflow-y: auto`, `overflow-x: auto`, or `overflow: auto` on any element that is not a web component. Each match is replaced with a `<canvas-scroll-area>` wrapper using the appropriate direction attribute.
2. Direction is explicit. Every `<canvas-scroll-area>` has at least one of `vertical` or `horizontal`. A scroll area without a direction is either a mistake or should be replaced with a plain div.
3. Every scrolling region is labeled. Every `<canvas-scroll-area>` with a direction attribute has either `aria-label` or `aria-labelledby`. Screen readers announce the region name when keyboard focus enters it.
4. No forbidden popup nesting. Scan for `<canvas-dropdown>`, `<canvas-combobox>`, or `<canvas-multi-select>` nested inside a `<canvas-scroll-area vertical>`. Each occurrence is a violation until the 4.1.0 Popover API migration. `<canvas-tooltip>` is allowed inside because it hides on scroll.
5. No legacy `.table-scroll` class. The pre 4.0.0 `.table-scroll` wrapper is replaced by `<canvas-scroll-area horizontal>`. Any remaining usage is a migration target.

### Sortable Lists (canvas-sortable-list)

1. **Component, not hand roll.** No plain `<div>` structures with `draggable` attributes, `HTML5 Drag and Drop API` event listeners, or third party drag libraries. Every reorderable list is a `canvas-sortable-list` with `canvas-sortable-item` children.
2. **Cross list group consistency.** When two or more lists need to exchange items, every participating list has a `group` attribute with the same value. Case sensitive. Mismatched groups silently prevent cross list moves.
3. **Receiver only semantics.** A list that should only receive (never send) uses `accept` with the source group name and omits `group`. A list that should hand out copies uses `pull="clone"` on the source.
4. **Event handler presence.** Where cross list is enabled, a `move` handler or a `change` handler exists on the receiving list, the source list, or a common ancestor. A `reorder` only handler misses cross list commits.
5. **Cancel pairing.** Any `beforemove` or `beforereorder` handler that calls `preventDefault()` also surfaces a visible message (toast, banner, inline text). A silent cancel reads as a broken drop.
6. **Labels for ARIA.** Each cross list participant has `aria-labelledby` pointing at its column heading, or `aria-label` with the column name. Without a label, the live region falls back to the list id.

## Phase 3. UX Patterns

Cross-component behavioral rules spanning the whole page.

1. **Button color audit.** Every `variant="primary"` button has text matching a clinical state transition (sign, lock, send, submit referral, confirm fax, check in). If not, change to default (blue). Defined in SKILL.md Key Rules.
2. **Form element height cohesion.** When canvas-input, canvas-dropdown, canvas-combobox, and canvas-button appear on the same row, they match sizes. Default pairs with default. `size="sm"` pairs with `size="sm"`.
3. **Date formatting.** All visible date strings in clinical contexts use absolute format ("Mar 24, 2026"). No relative dates ("2 days ago"). Defined in DESIGN.md Date and Time Display.

### Empty States

1. **Handler presence.** Every canvas-table-body, list container, or data section that can render zero rows has an empty state handler. Blank containers with no explanation fail this check.
2. **Typed empty.** The empty copy makes the type identifiable. One of first use, user cleared, filter no results, or load error. Generic "No data" fails this check. See Empty States in component-usage.md.
3. **Filter escape.** A filter bar or search input above a list or table that can produce zero results pairs with a Clear filters action inside the filter no results empty state. A filter with no reset affordance fails this check.
4. **Loading gate.** The empty pattern does not render during the loading window. canvas-loader covers that case. An empty state that renders before fetch resolves fails this check.
5. **Error contrast.** Fetch failure renders `canvas-banner variant="error"`, not the centered empty pattern. A failed load that reuses the empty pattern reads as a true empty and fails this check.
6. **Content hierarchy.** Empty copy includes a heading plus one line of supporting text. Single line empty states are acceptable only inside containers narrower than 300 pixels.
7. **Clinical distinction.** Clinical data empty states distinguish recorded from not recorded where the distinction is meaningful. "No allergies recorded" passes, "No allergies" fails on an allergies surface.
8. **Accessibility.** The empty container uses a semantic heading element. Filter empty regions that replace previously rendered rows wrap their results region in `aria-live="polite"`.

### Loading and Patient Context

1. **Loading presence.** If the plugin fetches data, a `canvas-loader` exists for the loading state. Defined in component-usage.md Loading States.
2. **Patient context.** If the plugin runs as a modal or standalone page and displays patient-specific data, the patient name and at least one identifier (DOB or MRN) must be visible near the top (see surface-selection.md Surfaces).

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
3. **Token usage.** All spacing, color, radius, and font values in plugin-specific CSS use `var(--token)` references. Defined in DESIGN.md Token System. Additionally, if any plugin CSS rule combines background, border, border-radius, and box-shadow on one element, verify that element is not a card imitation. Cards must use the `canvas-card` component, not inline card styling with tokens.

---

After all six phases pass with zero violations, the UI is validated.
