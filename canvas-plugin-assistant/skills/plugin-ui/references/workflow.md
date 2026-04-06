# UI Workflow

Follow these steps in order when building or improving plugin UI. Each step either always runs or has a decision point that adapts based on whether the UI already exists.

A plugin can have multiple views (a chart pane, a modal, a settings page). Steps 2 and 3 run independently for each view.

## Common Mistakes

These are the rules agents violate most because they contradict default instincts. Read this list before starting and keep it in mind throughout every step.

1. **Save buttons are blue, not green.** Use `<canvas-button>Save</canvas-button>` (default variant is secondary/blue). Green (`variant="primary"`) is only for clinical state transitions (sign note, send message to patient). Most plugin screens have zero green buttons.
2. **No toggles on any screen with a submit button.** If the form has a save or submit action, every boolean control must be `<canvas-checkbox>`. Toggles (`<canvas-toggle>`) mean instant effect. This is the single most common UI mistake in generated plugin code.
3. **No colors outside the palette.** No purple, teal, cyan, pink. AI models reach for these to add visual variety. The palette is closed.
4. **Use web components, not raw HTML.** Do not write `<button class="btn btn-secondary">` or `<div class="dropdown">`. Use `<canvas-button>` and `<canvas-dropdown>`. Every form element, badge, banner, card, table, tab, and accordion has a web component. Check web-components.md before writing raw HTML for any UI element.
5. **Plugin-specific CSS uses tokens.** Any custom CSS beyond component usage must reference `var(--token)` values from tokens.css. No hardcoded hex, px, font-family, or border-radius.
6. **Follow the escalation ladder.** Use components first. Customize through attributes. Override through CSS custom properties. Build novel HTML only as a last resort. See the escalation ladder in web-components.md.

## Hard Rules vs Soft Proposals

**Hard rules** are enforced automatically. The agent fixes violations without asking. Component rendering (colors, borders, padding, sizing, tokens), toggle and submit prohibition, accessibility minimums, right pane bottom padding, date formatting in clinical contexts.

**Soft proposals** are presented as suggestions with reasoning. The user decides. Surface choice, component type choice (table vs cards, select vs radios), layout alternatives, information density tradeoffs.

## Step 1. Inventory Views

Always runs. List every distinct screen the plugin has or needs. For each view, note what data it shows, what actions the user can take, and whether a patient chart needs to be open.

If the plugin already has HTML, read the existing templates and list the views found. If building from scratch, derive the views from the requirements.

This produces the view list that steps 2 through 5 iterate over.

## Step 2. Surface Selection (per view)

Reference: [surface-selection.md](surface-selection.md)

**If the view already exists.** Check which surface it targets. If the surface fits the view's purpose per the decision sequence in surface-selection.md, move on. If a different surface would be a better fit, soft propose the alternative with reasoning. Do not change the surface without user approval.

**If the view is new.** Walk through the decision sequence in surface-selection.md and pick the surface. If the requirements make the choice obvious, state it and move on. If two surfaces are close, present both with tradeoffs and let the user pick.

## Step 3. Component Selection (per view)

Reference: [component-usage.md](component-usage.md)

**If the view already exists.** Audit the component choices against the rules in component-usage.md. Check toggle vs checkbox, table vs cards, dropdown vs combobox. If the view uses raw HTML where a web component exists, flag it for migration. If the view violates the toggle-submit prohibition or another hard rule, flag it as a hard fix.

**If the view is new.** Choose components based on the data and actions identified in step 1. Follow the decision rules in component-usage.md. Use web components from web-components.md for every available element. Only fall back to raw HTML for patterns listed in the "Patterns Without Components" section of web-components.md (tooltip, divider, spinner, empty state, patient context header). Explain non-obvious choices briefly.

## Step 4. Build or Refactor HTML (per view)

References: [web-components.md](web-components.md), [component-usage.md](component-usage.md)

Always runs. This is where hard rules are enforced on component rendering.

1. Start from the Plugin HTML Boilerplate in web-components.md. The `<head>` links tokens.css, typography.css, and canvas-components.js. Plugin iframes do not inherit the parent page's fonts or components.
2. Build the view using `<canvas-*>` web components for every available element. Check the component API in web-components.md for attributes, events, and slots.
3. For patterns without a web component (tooltip, divider, spinner, empty state, patient context header), use the HTML snippets from the "Patterns Without Components" section of web-components.md. All CSS values must use `var(--token)` references from tokens.css.
4. Write plugin-specific CSS in the `<style>` tag only for layout or behavior the components do not cover. Use token references for all values.
5. **Cross-check elements.** For every `<canvas-*>` element used in the HTML, verify it is one of the 18 registered components. Misspelled tag names render as empty unknown elements with no error.
6. **Cross-check attributes.** For every attribute set on a `<canvas-*>` element, verify it is a documented attribute in web-components.md. Unknown attributes are silently ignored.

### Refactor Safety (existing HTML with JavaScript only)

Skip this block entirely if the existing HTML has no `<script>` tags and no inline event attributes. For HTML with JavaScript, complete all four parts before modifying any markup.

**Part A. JavaScript Dependency Scan.** Read every `<script>` block and inline event attribute. Extract every DOM access point (getElementById, querySelector, getElementsByClassName, inline handlers, dataset reads, closest/parent/sibling traversals, FormData/form.elements references). Produce a dependency inventory pairing each DOM anchor with what the JavaScript does through it.

**Part B. Risk Classification.** Classify each proposed change against the dependency inventory.

*Cosmetic.* The change does not touch any element in the inventory. A token swap, a spacing fix. Proceed without asking.

*Structural, clear migration.* The change replaces an element in the inventory, and the replacement provides equivalent hooks. Declare the migration before modifying. Example: replacing `<select id="provider-filter">` with `<canvas-dropdown id="provider-filter">` requires updating the change handler to use the component's `change` event and read from `element.value`.

*Structural, unclear migration.* The change replaces an element in the inventory, and the agent cannot confirm the replacement preserves all behaviors. Stop and surface to the user.

**Part C. Migration Declarations.** For every structural change, write a one-line declaration before making the change.

Format: `MIGRATION: {old element} used by {function name} for {purpose}. New target: {new element}. JS update: {what changes}.`

**Part D. Pre-modification listing.** If any structural changes exist, list all proposed changes with their migration declarations before modifying the markup. Cosmetic-only refactors do not require pre-listing regardless of how many violations exist.

## Step 5. Clinical UX and Interaction Patterns (per view)

References: [clinical-ux.md](clinical-ux.md), [interaction-patterns.md](interaction-patterns.md)

Always runs. Apply these rules to the HTML from step 4.

- Touch targets meet the 44px minimum.
- Dates use absolute format ("Mar 24, 2026") in clinical contexts.
- Confirmation hierarchy matches the action's severity.
- Information density fits the view type (form vs data display).
- Visual hierarchy uses weight and color to separate primary from secondary information.
- Patient identity visible on standalone pages and modals showing patient data. Use the Patient Context Header pattern from web-components.md.
- Keyboard navigation works (tab order, enter to submit, escape to close).
- ARIA attributes present per interaction-patterns.md minimums.
- Focus management correct for modals, dynamic content, banners.
- Right chart pane has `padding-bottom: 120px`.

## Step 6. Validate

Reference: [validation-checklist.md](validation-checklist.md)

Always runs. The validation checklist is a six-phase protocol. Each phase must pass completely before the next phase begins.

Before starting, reread the generated HTML as a string. Do not validate from what you remember writing. Read the actual output.

1. **Phase 1, CSS Foundation.** Verify the stylesheet infrastructure. Tokens from file, base classes from file, no hardcoded values, class cross-check, JS cross-check.
2. **Phase 2, Component Audit.** Inventory which component types are present. For each type, run its dedicated check block. Validate structure, classes, ARIA, and visual treatment.
3. **Phase 3, UX Patterns.** Cross-component behavioral rules. Toggle-submit prohibition, button color audit, table action alignment, form height cohesion, confirmation hierarchy, date formatting.
4. **Phase 4, Functional Preservation.** Only runs when refactoring existing HTML that contained JavaScript. Verify all JS DOM targets still resolve, all inline handler functions are defined, form name contracts survived, and no functions were dropped. Skip for newly generated HTML.
5. **Phase 5, Accessibility.** Touch targets, label association, ARIA attributes, color independence, right-pane clearance.
6. **Phase 6, Visual Polish.** Palette compliance, text-background pairing, border-radius, truncation, transitions, spacing grid.

Within each phase, fix violations as you find them, then rerun the phase from check 1. Only advance after a clean pass. Only present the result after all six phases produce zero violations.

If a violation requires a component or surface change that was already approved by the user in steps 2 or 3, do not re-ask. If a new issue surfaces that was not covered in earlier steps, flag it.
