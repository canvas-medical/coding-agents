# UI Workflow

This file sequences the agent through the right reference files for each phase of UI work. A plugin can have multiple views (a chart pane, a modal, a settings page). Steps 2 through 5 run independently for each view.

## Routing Table

| Step | Task | Reference file | What the agent does |
|---|---|---|---|
| 1 | Inventory views | None | List every distinct screen the plugin has or needs. For each view, note what data it shows, what actions the user can take, and whether a patient chart must be open. If HTML exists, read the templates. If building from scratch, derive views from the requirements. This produces the view list that later steps iterate over. |
| 2 | Surface selection (per view) | [surface-selection.md](surface-selection.md) | For existing views, check whether the current surface fits. If a different surface is a better match, soft propose it with reasoning. Do not change without user approval. For new views, walk through the triggers, surfaces, and pairings sections and pick the combination. If two options are close, present both with tradeoffs and let the user pick. |
| 3 | Component selection (per view) | [component-usage.md](component-usage.md) | For existing views, audit component choices against the rules. Flag raw HTML where a web component exists. Flag hard rule violations (toggle with submit, wrong button color). For new views, choose components based on the data and actions from step 1. Use web components for every available element, falling back to raw HTML only for patterns listed in the "Patterns Without Components" section of web-components.md. |
| 4 | Build or refactor HTML (per view) | [web-components.md](web-components.md), [component-usage.md](component-usage.md), [DESIGN.md](DESIGN.md) | Start from the Plugin HTML Boilerplate in web-components.md. Build with `<canvas-*>` components. Use DESIGN.md for token selection when writing custom CSS. Cross-check every tag name against the 24 registered components. Cross-check every attribute against the documented API. If the existing HTML has JavaScript, complete the Refactor Safety protocol below before modifying any markup. |
| 5 | Clinical UX and interaction patterns (per view) | [interaction-patterns.md](interaction-patterns.md), [DESIGN.md](DESIGN.md) | Verify touch targets meet 44px minimum. Use DESIGN.md for visual hierarchy, information density, truncation rules, and date formatting. Confirmation hierarchy matches action severity. Patient identity visible on standalone pages and modals showing patient data. Keyboard navigation works. ARIA attributes present per interaction-patterns.md minimums. Focus management correct for modals and dynamic content. Right chart pane bottom clearance applied. |
| 6 | Validate | [validation-checklist.md](validation-checklist.md) | Run the six-phase validation protocol. Each phase must pass completely before the next begins. Reread the generated HTML as a string before starting. Fix violations within each phase and rerun until clean. Only present the result after all six phases produce zero violations. |

## Refactor Safety

This protocol applies only when existing HTML contains `<script>` tags or inline event attributes. Skip it entirely for HTML without JavaScript. Complete all four parts before modifying any markup.

**Part A. JavaScript Dependency Scan.** Read every `<script>` block and inline event attribute. Extract every DOM access point (getElementById, querySelector, getElementsByClassName, inline handlers, dataset reads, closest/parent/sibling traversals, FormData/form.elements references, child selectors that reach into elements being replaced by `<canvas-*>` components). Flag any selector targeting children of an element that will become a web component, because those children move behind a Shadow DOM boundary after migration (e.g., `querySelector('#wrapper input')` or `closest('.field').querySelector('select')`). Produce a dependency inventory pairing each DOM anchor with what the JavaScript does through it.

**Part B. Risk Classification.** Classify each proposed change against the dependency inventory.

*Cosmetic.* The change does not touch any element in the inventory. A token swap, a spacing fix. Proceed without asking.

*Structural, clear migration.* The change replaces an element in the inventory, and the replacement provides equivalent hooks. Declare the migration before modifying. Example: replacing `<select id="provider-filter">` with `<canvas-dropdown id="provider-filter">` requires updating the change handler to use the component's `change` event and read from `element.value`.

*Structural, unclear migration.* The change replaces an element in the inventory, and the agent cannot confirm the replacement preserves all behaviors. Stop and surface to the user.

**Part C. Migration Declarations.** For every structural change, write a one-line declaration before making the change.

Format: `MIGRATION: {old element} used by {function name} for {purpose}. New target: {new element}. JS update: {what changes}.`

**Part D. Risk Summary.** Before modifying any markup, present all proposed changes grouped by risk tier.

*Group 1, proceed (cosmetic).* Changes that do not touch any element in the dependency inventory. List each change in one line. Example: "Token swap on `#header` background color" or "Replace `div.badge` with `<canvas-badge>` (no JS references)."

*Group 2, clear migration (will update JS alongside markup).* Changes that replace elements in the inventory where the replacement provides equivalent hooks. Include the migration declaration for each. Example: "Replace `<select id="status">` with `<canvas-dropdown id="status">`. MIGRATION: `select#status` used by `updateFilters()` for reading selected value. New target: `canvas-dropdown#status`. JS update: replace `selectedIndex` with `.value` comparison."

*Group 3, needs your input (unclear migration).* Changes where the agent cannot confirm behavior preservation. Describe what breaks and what the options are. Example: "`querySelector('.field input')` in `validateForm()` reaches the inner input of `#patient-name`. After migration to `<canvas-input>`, that selector will not cross the Shadow DOM boundary. Options: change selector to target the custom element directly, or keep the native input."

Wait for user approval before modifying markup. The user may approve all groups at once, approve groups 1 and 2 while discussing group 3, or ask to skip specific changes.
