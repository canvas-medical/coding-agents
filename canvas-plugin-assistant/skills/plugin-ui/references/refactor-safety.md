# Refactor Safety

Protocol for refactoring existing plugin HTML that contains JavaScript. Applies only when the file contains `<script>` tags or inline event attributes. Skip entirely for HTML without JavaScript. Complete all four parts before modifying any markup.

## Part A. JavaScript Dependency Scan

Read every `<script>` block and inline event attribute. Extract every DOM access point.

- `getElementById`
- `querySelector` and `querySelectorAll`
- `getElementsByClassName` and `getElementsByTagName`
- Inline handlers (`onclick`, `onchange`, `onsubmit`, and similar)
- `dataset` reads
- `closest`, `parentElement`, `parentNode`, and sibling traversals
- `FormData` and `form.elements` references
- Child selectors that reach into elements being replaced by `<canvas-*>` components

Flag any selector targeting children of an element that will become a web component. Those children move behind a Shadow DOM boundary after migration, so selectors like `querySelector('#wrapper input')` or `closest('.field').querySelector('select')` stop matching.

Produce a dependency inventory pairing each DOM anchor with what the JavaScript does through it.

## Part B. Risk Classification

Classify each proposed change against the dependency inventory.

**Cosmetic.** The change does not touch any element in the inventory. A token swap, a spacing fix. Proceed without asking.

**Structural, clear migration.** The change replaces an element in the inventory and the replacement provides equivalent hooks. Declare the migration before modifying. Example. Replacing `<select id="provider-filter">` with `<canvas-dropdown id="provider-filter">` requires updating the change handler to use the component's `change` event and read from `element.value`.

**Structural, unclear migration.** The change replaces an element in the inventory and the agent cannot confirm the replacement preserves all behaviors. Stop and surface to the user.

## Part C. Migration Declarations

For every structural change, write a one-line declaration before making the change.

Format. `MIGRATION: {old element} used by {function name} for {purpose}. New target: {new element}. JS update: {what changes}.`

## Part D. Risk Summary

Before modifying any markup, present all proposed changes grouped by risk tier.

**Group 1, proceed (cosmetic).** Changes that do not touch any element in the dependency inventory. List each change in one line. Example. "Token swap on `#header` background color" or "Replace `div.badge` with `<canvas-badge>` (no JS references)".

**Group 2, clear migration (will update JS alongside markup).** Changes that replace elements in the inventory where the replacement provides equivalent hooks. Include the migration declaration for each. Example. "Replace `<select id="status">` with `<canvas-dropdown id="status">`. MIGRATION: `select#status` used by `updateFilters()` for reading selected value. New target: `canvas-dropdown#status`. JS update: replace `selectedIndex` with `.value` comparison."

**Group 3, needs your input (unclear migration).** Changes where the agent cannot confirm behavior preservation. Describe what breaks and what the options are. Example. "`querySelector('.field input')` in `validateForm()` reaches the inner input of `#patient-name`. After migration to `<canvas-input>`, that selector will not cross the Shadow DOM boundary. Options: change selector to target the custom element directly, or keep the native input."

Wait for user approval before modifying markup. The user may approve all groups at once, approve groups 1 and 2 while discussing group 3, or ask to skip specific changes.
