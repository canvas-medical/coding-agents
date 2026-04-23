# UI Validation Checklist

Six-phase binary validation. Each check is pass or fail against the generated HTML. No inline rule restatement, every check points to its rule home. Fix violations as you find them and restart the current phase from check 1. Only advance when the phase produces zero violations.

## Execution Discipline

Before starting, reread the generated HTML as a string. Do not validate from memory.

## Phase 0. Preconditions

Setup rules live in [setup.md](setup.md). Anti-pattern Global CSS Reset in [anti-patterns.md](anti-patterns.md).

1. **Static files present.** Plugin `static/` contains both `canvas-plugin-ui.js` and `canvas-plugin-ui.css`. If missing, stop and direct the user to [setup.md](setup.md).
2. **Asset line counts match skill source.** `wc -l` on plugin static files equals `wc -l` on skill `assets/`. On mismatch, warn and offer to recopy.
3. **Three head tags present.** Google Fonts Lato `<link>`, `canvas-plugin-ui.css` `<link>`, and `canvas-plugin-ui.js` `<script>`, all with the correct static prefix.
4. **Lato font link present.** Plugin iframes do not inherit parent page fonts.
5. **No legacy system residue.** No `<style>` tag contains base component classes or `:root` variable blocks copied from the pre 4.0.0 class system.
6. **No global CSS reset.** See [setup.md](setup.md) Global CSS Reset Detection and [anti-patterns.md](anti-patterns.md) Global CSS Reset Overriding Component Styles.

## Phase 1. Element Verification

Component API lives in [web-components.md](web-components.md).

1. **Tag name.** Every `<canvas-*>` tag resolves to a registered component. See the component list at the top of [web-components.md](web-components.md).
2. **Attributes.** Every attribute on a `<canvas-*>` element is documented in [web-components.md](web-components.md) for that component.
3. **No native replacements.** No `<select>`, no `<input type="checkbox">`, no `<input type="radio">`, no raw `<input>` of any type outside a component, no `<details>` or `<summary>`. See [anti-patterns.md](anti-patterns.md) Native Input Use and Native Details and Summary Use.
4. **Plugin CSS uses tokens.** All color, spacing, radius, font-family, and transition values in `<style>` use `var(--token)` references. Allowed raw values: `0`, `none`, `auto`, `100%`, position values, z-index integers. Token system lives in [DESIGN.md](../DESIGN.md) Token System.

## Phase 2. Component Usage Audit

Inventory which component types are present. Run only checks relevant to components found.

### Buttons

Rules in [component-usage.md](component-usage.md) Buttons.

1. `variant="primary"` reserved for clinical state transitions only.
2. At most one green button per page.
3. Cancel, dismiss, close, neutral use `variant="ghost"`.
4. Disabled uses the `disabled` attribute on the existing variant.
5. Button group places main action on the right, cancel on the left.

### Toggle and Checkbox

Rule in [interaction-patterns.md](interaction-patterns.md) Toggle and Submit Prohibition.

1. No `canvas-toggle` in the same UI segment as a submit or save action. Toggles in a separate unrelated segment are allowed when their effect is independent and instant.

### Dropdowns and Comboboxes

Decision rules in [component-usage.md](component-usage.md) Dropdown vs Combobox.

1. `canvas-dropdown` for fixed lists, `canvas-combobox` for searchable, `canvas-multi-select` for 8+ multi value.
2. No `canvas-dropdown` used for action lists. See [anti-patterns.md](anti-patterns.md) Action Menu Built as a Dropdown.

### Menu Buttons

Rules in [component-usage.md](component-usage.md) Menu Button. API in [web-components.md](web-components.md) canvas-menu-button.

1. Options are verbs (actions), not values.
2. Icon only slotted triggers carry `aria-label`.
3. Interactive menu button on the page has a `select` event listener.
4. Row kebab menus use `align="end"`.
5. No `name`, `value`, or `required` on `<canvas-menu-button>`.
6. Section separators use `<hr>` children, not custom markup.
7. Two or fewer enabled options is a review target, prefer side by side buttons.
8. Explicit `direction` or `align` has a documented layout reason.

### Popovers

Rules in [component-usage.md](component-usage.md) Popover. API in [web-components.md](web-components.md) canvas-popover.

1. Body is arbitrary content, not a list of action verbs. See [anti-patterns.md](anti-patterns.md) Action Menu Built as a Dropdown.
2. Non empty `label` attribute present.
3. `slot="trigger"` child present, icon only triggers carry `aria-label`.
4. Interactive popover has an `open`, `close`, or `cancel` listener, or controls `open` from another handler.
5. No nested popovers.
6. Explicit `direction` or `align` has a documented layout reason.
7. `pointer` only on ambiguous anchors, icon only triggers, or small surfaces floating free.
8. Body stays within one logical group and up to four focused controls. Five or more escalates to `canvas-modal`.
9. Never used for destructive confirmations or blocking flows. Those belong in `canvas-modal`. See [anti-patterns.md](anti-patterns.md) Anchored Content Surface Built as a Modal.

### Tables

1. Table has `aria-label`.
2. Action cells use the `actions` attribute on `canvas-table-cell`.
3. Variant matches density. `compact` for claims, lab values, ledger breakdowns.

### Tabs

1. Each `canvas-tab` has a `for` matching a `canvas-tab-panel` `id`.
2. Each `canvas-tab` contains a `canvas-tab-label`.

### Accordions

1. Each `canvas-accordion-item` has exactly one `canvas-accordion-title` and one `canvas-accordion-content`.
2. No native `<details>` or `<summary>`. See [anti-patterns.md](anti-patterns.md) Native Details and Summary Use.

### Inline Form Rows

Rules in [component-usage.md](component-usage.md) Inline Form Rows and Same Row Height Cohesion.

1. No raw flex rows of two or more form elements. See [anti-patterns.md](anti-patterns.md) Missed Inline Row Swaps.
2. No mixed size tier in one row. See [anti-patterns.md](anti-patterns.md) Mixed Size Tier in One Row.
3. No native input inside a `canvas-inline-row`.
4. Filter bar above a table uses `canvas-card` + `canvas-card-body` + `canvas-inline-row`. Template in [patterns.md](patterns.md) Filter Bar.

### Cards and Content Containers

Rules in [component-usage.md](component-usage.md) Cards.

1. No raw card wrappers. See [anti-patterns.md](anti-patterns.md) Card Imitations.
2. No four property signature (background + border + border-radius + box-shadow on one element) outside of modals and popovers.
3. Gray action strips at card bottom use `canvas-card-footer`.
4. No `padding` on direct children of `canvas-card-body` beyond layout spacing.
5. Multiple titled sections use stacked `canvas-card-body` elements.
6. No `max-height` on `canvas-card-body` expecting scroll. See [anti-patterns.md](anti-patterns.md) Silent Card Body Overflow Reliance.

### Scroll Areas

Rules in [component-usage.md](component-usage.md) Scroll Areas.

1. No raw `overflow-y`, `overflow-x`, or `overflow: auto` on plugin level divs. See [anti-patterns.md](anti-patterns.md) Missed Scroll Area Swaps.
2. Every `canvas-scroll-area` has at least one of `vertical` or `horizontal`.
3. Every scrolling region has `aria-label` or `aria-labelledby`.
4. No `canvas-dropdown`, `canvas-combobox`, or `canvas-multi-select` inside `canvas-scroll-area[vertical]`. See [anti-patterns.md](anti-patterns.md) Forbidden Popup Nesting in a Vertical Scroll Area.
5. No legacy `.table-scroll` class. Replaced by `canvas-scroll-area horizontal`.

### Sortable Lists

Rules in [component-usage.md](component-usage.md) Sortable List. API in [web-components.md](web-components.md) canvas-sortable-list.

1. No hand rolled drag with `draggable` or third party libraries. Every reorderable list uses the component.
2. Lists that exchange items share the same `group` value, case sensitive.
3. Receive only lists use `accept` and omit `group`. Template palettes use `pull="clone"`.
4. Cross list enabled requires a `move` or `change` handler on the receiver, source, or common ancestor.
5. `beforemove` or `beforereorder` that calls `preventDefault()` surfaces a visible message.
6. Each cross list participant has `aria-labelledby` or `aria-label`.

## Phase 3. UX Patterns

Cross component rules.

1. **Button color audit.** See [component-usage.md](component-usage.md) Buttons.
2. **Form element height cohesion.** See [component-usage.md](component-usage.md) Same Row Height Cohesion.
3. **Date formatting.** Absolute dates in clinical contexts. See [DESIGN.md](../DESIGN.md) Date and Time Display.

### Empty States

Rules in [component-usage.md](component-usage.md) Empty States. Templates in [patterns.md](patterns.md) Empty State. State machine in [patterns.md](patterns.md) Loading, Empty, Error State Machine.

1. Every zero-row data section has an empty state handler.
2. Empty copy identifies type (first use, user cleared, filter no results, load error). No generic "No data". See [anti-patterns.md](anti-patterns.md) Generic Empty Copy.
3. Filter with possible zero results pairs with Clear filters action. See [anti-patterns.md](anti-patterns.md) Filter Without Escape.
4. Empty pattern does not render during the loading window. See [anti-patterns.md](anti-patterns.md) Empty State During Loading.
5. Fetch failure renders `canvas-banner variant="error"`, not the centered empty pattern.
6. Empty copy includes heading plus one line. One line acceptable only under 300 px wide containers.
7. Clinical surfaces distinguish recorded from not recorded where meaningful.
8. Semantic heading inside empty container. Filter empty regions wrap results in `aria-live="polite"`.

### Writing Style

Rules in [writing-style.md](writing-style.md). Anti-pattern in [anti-patterns.md](anti-patterns.md) AI Puffery in Generated Strings.

Run on every user facing string.

1. No em dashes or en dashes (`—`, `–`).
2. No curly quotes or smart apostrophes (`"`, `"`, `'`, `'`).
3. Sentence case headings.
4. No didactic disclaimers (It is important to note, Please be aware, Note that).
5. No collaborative assistant tone (Let me help you, Together we will).
6. No knowledge cutoff disclaimers (As of my last update, training data).
7. No emoji as visual formatting.
8. No puffery vocabulary (vibrant, boasts, seamlessly, effortlessly, robust, powerful, comprehensive, intuitive, empowering, fostering). Clinical carve out applies.
9. No inflation of significance (serves as, stands as, plays a key role in).
10. No weasel wording (studies show, experts agree).
11. No negative parallelism (Not just X, but Y).
12. Clinical carve out honored. Check phrase context before flagging vital, critical, significant, active, acute, pivotal, present, presenting, underlying.

### Loading and Patient Context

1. Fetching plugin has a `canvas-loader` for the loading state. See [component-usage.md](component-usage.md) Loading States.
2. Modal or standalone page with patient data shows patient name and one identifier near the top. See [surface-selection.md](surface-selection.md) Surfaces and [patterns.md](patterns.md) Patient Context Header.

## Phase 4. Functional Preservation

Runs only when refactoring HTML that contained JavaScript. Protocol in [refactor-safety.md](refactor-safety.md).

1. Script blocks preserved when original had them.
2. Every `getElementById('...')` has a matching `id`.
3. Every `querySelector('...')` matches at least one element.
4. Every inline event attribute calls a function defined in a `<script>` tag.
5. Form `name` contracts preserved, or submission code updated.
6. Data attribute contracts preserved.
7. Every named function in the original scripts exists in the refactored scripts unless explicitly marked for removal in a migration declaration.

## Phase 5. Accessibility

Rules in [interaction-patterns.md](interaction-patterns.md).

1. 44 px minimum touch target on interactive elements via size or padding.
2. Every `canvas-input`, `canvas-dropdown`, `canvas-combobox`, `canvas-multi-select` has a `label` attribute or external label.
3. No information by color alone. Badges carry text labels. Error states carry text messages.
4. `padding-bottom: 120px` on the outermost scrollable container for `RIGHT_CHART_PANE` and `RIGHT_CHART_PANE_LARGE`. See [surface-selection.md](surface-selection.md) Right Chart Pane.

## Phase 6. Visual Polish

Rules in [DESIGN.md](../DESIGN.md).

1. Palette compliance. No off palette colors (purple, teal, pink, cyan). See [DESIGN.md](../DESIGN.md) Color Palette and Roles.
2. Text and background pairing. See [DESIGN.md](../DESIGN.md) Text and Background Pairing.
3. Token usage. All spacing, color, radius, font values in plugin CSS use `var(--token)` references. No raw card imitation (four property signature) outside modal and popover surfaces.

---

After all six phases pass with zero violations, the UI is validated.
