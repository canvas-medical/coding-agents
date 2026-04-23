# Anti-Patterns

Common mistakes agents make when generating or refactoring plugin UI. Each entry has a consistent shape. Detection, why it is wrong, fix, rule home, and validation check. Scan for each during workflow Step 3 (component selection). List any matches in the `refactor-safety.md` Part D risk summary so the user sees the full swap plan before work begins.

## Card Imitations

**Detection.** Any element combining background, border, border-radius, and box-shadow on itself, regardless of class name. The four property signature is the primary detector. Class names historically used include `card`, `panel`, `box`, `tile`, `container`, `filters`, `filter-bar`, `toolbar`, `section`, `wrapper`, `wrap`, `header`. Adjacent regions joined with `border-top: none` and a shared radius are a multi region card.

**Why.** The component handles all four properties automatically and stays aligned with Canvas visual updates. Hand rolled card styling drifts from Canvas the moment the design system updates any of the four properties.

**Fix.** Replace with `<canvas-card><canvas-card-body>...</canvas-card-body></canvas-card>` and remove the local class CSS rule. For multi region cards use `canvas-card-body` plus `canvas-card-footer`, or stacked `canvas-card-body` elements when the second region is still content.

**Exception.** Class names where the word refers to something unrelated, for example `card-number-input` is a payment field, not a card container.

**Rule home.** `component-usage.md` Cards and Content Containers.
**Validation check.** `validation-checklist.md` Phase 2, Cards.

## Native Input Use

**Detection.** Raw `<input type="date">`, `<input type="text">`, `<input type="number">`, or any other native input tag.

**Why.** Native inputs render with OS-level styling that does not match Canvas. Applying tokens by hand produces inconsistent output across browsers and platforms.

**Fix.** Replace with `canvas-input` using the appropriate `type` attribute. The component styles native date and time pickers through the same border, radius, padding, and font as other inputs.

**Rule home.** `component-usage.md` Text Inputs vs Textareas.
**Validation check.** `validation-checklist.md` Phase 1, no native replacements.

## Native Details and Summary Use

**Detection.** Any `<details>` or `<summary>` element in the template.

**Why.** Native `<details>` renders with browser default chevrons, spacing, and ARIA that do not match Canvas. The component handles chevron, ARIA, and keyboard behavior correctly.

**Fix.** Replace with `<canvas-accordion>` wrapping one or more `<canvas-accordion-item>`, each containing a `<canvas-accordion-title>` and a `<canvas-accordion-content>`.

**Exception.** A custom header row whose trigger content does not fit the accordion title slot, for example a medication group row with name, sig, badges, and actions. That exception still rules out native `<details>` as the outer container.

**Rule home.** `component-usage.md` Accordion vs Tabs.
**Validation check.** `validation-checklist.md` Phase 2, Accordions.

## Mixed Size Tier in One Row

**Detection.** A dropdown at `size="sm"` next to a default size input or button, or any combination of `sm` and default form elements side by side.

**Why.** Matching the `size` attribute across components does not produce matching rendered heights. `canvas-button[size="sm"]` has a 36 px `min-height` while `canvas-dropdown[size="sm"]` only reduces the trigger font size.

**Fix.** Use default size across the row, or use `sm` only when every element in the row is a button.

**Rule home.** `component-usage.md` Same Row Height Cohesion.
**Validation check.** `validation-checklist.md` Phase 2, Inline Form Rows.

## Missed Inline Row Swaps

**Detection.** A `div` with `display: flex` containing two or more form elements (input, dropdown, combobox, multi select, textarea, button).

**Why.** Hand rolled flex rows drift from the Canvas per-child sizing rules. Buttons stretch, inputs shrink, wrap behavior breaks in narrow surfaces.

**Fix.** Replace the container with `<canvas-inline-row>` and delete the local flex, gap, alignment, and wrap CSS. The component handles flex sizing per child type, so buttons keep natural width while inputs share available space and wrap in narrow surfaces.

**Rule home.** `component-usage.md` Inline Form Rows.
**Validation check.** `validation-checklist.md` Phase 2, Inline Form Rows.

## Missed Scroll Area Swaps

**Detection.** Raw inline `overflow-y: auto`, `overflow-x: auto`, or `overflow: auto` on plugin level divs. The pre 4.0.0 `.table-scroll` wrapper for wide tables.

**Why.** Raw overflow divs miss the ARIA contract (keyboard focus, screen reader label) that `canvas-scroll-area` wires in automatically.

**Fix.** Replace with `<canvas-scroll-area>` using `vertical`, `horizontal`, or both as appropriate.

**Exception.** Internal scrolling inside the dropdown, combobox, and multi-select menus is intentional and must stay untouched.

**Rule home.** `component-usage.md` Scroll Areas.
**Validation check.** `validation-checklist.md` Phase 2, Scroll Areas.

## Silent Card Body Overflow Reliance

**Detection.** Setting `max-height` on `canvas-card-body` expecting scrolling to activate.

**Why.** The body is not a scroll container in 4.0.0 and later. A `max-height` value on `canvas-card-body` silently clips content instead of scrolling.

**Fix.** Wrap the content in a `canvas-scroll-area vertical` inside the body.

**Rule home.** `component-usage.md` Scroll Areas.
**Validation check.** `validation-checklist.md` Phase 2, Cards.

## Forbidden Popup Nesting in a Vertical Scroll Area

**Detection.** `canvas-dropdown`, `canvas-combobox`, or `canvas-multi-select` placed inside a `canvas-scroll-area[vertical]`.

**Why.** The menu gets clipped by the scroll area's overflow. Tooltips are exempt because they hide on scroll.

**Fix.** Restructure so the popup component is outside the scroll area. This restriction lifts in a later release when popup components move to the browser top layer.

**Rule home.** `component-usage.md` Scroll Areas.
**Validation check.** `validation-checklist.md` Phase 2, Scroll Areas.

## Action Menu Built as a Dropdown

**Detection.** Using `canvas-dropdown` for a trigger that opens a list of verbs (Edit, Duplicate, Delete, Add X) and wiring behavior on the `change` event.

**Why.** The dropdown is a form field with `role="listbox"`, `role="option"`, and form association. Screen readers announce it as a selection, the `name` and `value` props are exposed but unused, and the user sees a field styled trigger where a button belongs.

**Fix.** Replace with `canvas-menu-button`, slot a `canvas-button` as the trigger, and listen for `select` events with `detail.value`.

**Rule home.** `component-usage.md` Menu Button.
**Validation check.** `validation-checklist.md` Phase 2, Menu Buttons.

## Anchored Content Surface Built as a Modal

**Detection.** Using `canvas-modal` for a click triggered surface that should stay attached to a specific trigger (filter icon, column picker button, legend icon, bulk action panel).

**Why.** The modal is a full screen overlay with a dimmed backdrop, wrong weight for a local disclosure. The surface has no anchor relationship to the trigger.

**Fix.** Replace with `canvas-popover`. Slot the trigger, set `label`, pick a `size`, set `pointer` if the anchor is ambiguous. Popover is non blocking, outside click and Escape always dismiss. Destructive confirmations and blocking flows stay on `canvas-modal`.

**Rule home.** `component-usage.md` Popover.
**Validation check.** `validation-checklist.md` Phase 2, Popovers.

## Empty State During Loading

**Detection.** An empty state that renders in the loading window before data arrives.

**Why.** Reads as a broken fetch to the user. A surface that swaps directly from empty to populated without a loading state reads as flicker.

**Fix.** Gate the empty pattern behind fetch resolution. Render `canvas-loader` during the fetch, and mount the empty pattern only after rows is known to be zero.

**Rule home.** `component-usage.md` Empty States and `patterns.md` Loading, Empty, Error State Machine.
**Validation check.** `validation-checklist.md` Phase 3, Empty States.

## Filter Without Escape

**Detection.** A filter bar or search input above a list or table that can produce zero results, with no Clear filters action inside the filter no results empty state.

**Why.** A user cannot tell a dead surface from a filter dead end without the reset button.

**Fix.** Pair the filter with a Clear filters action inside the filter no results empty state. See the filter no results markup in `patterns.md` Empty State.

**Rule home.** `component-usage.md` Empty States.
**Validation check.** `validation-checklist.md` Phase 3, Empty States.

## Generic Empty Copy

**Detection.** "No data", "No results found", or "Empty" as the only empty state copy.

**Why.** The type of empty (first use, user cleared, filter no results) is unrecoverable from generic copy, which means the action button cannot match the situation either.

**Fix.** Name the domain object ("No medications recorded") and the cause, then offer the action that fits the type.

**Rule home.** `component-usage.md` Empty States Voice.
**Validation check.** `validation-checklist.md` Phase 3, Empty States.

## AI Puffery in Generated Strings

**Detection.** Em dashes, title case headings, puffery clusters (vibrant, boasts, serves as, stands as), didactic disclaimers (It is important to note, Please be aware), collaborative assistant tone (Let me help you), and participle commentary (empowering, ensuring, fostering).

**Why.** These patterns are AI writing fingerprints and bad UI writing independently. They leak into generated plugin copy and make the UI read as machine written.

**Fix.** Apply `writing-style.md` rules to every user facing string. The clinical vocabulary carve out in `writing-style.md` covers legitimate uses of flagged words like vital, critical, significant, active, and acute so "vital signs" and "active medications" survive while "vital role" and "active participation" do not.

**Rule home.** `writing-style.md`.
**Validation check.** `validation-checklist.md` Phase 3, Writing Style.

## Global CSS Reset Overriding Component Styles

**Detection.** Any universal selector rule (`* { margin: 0; padding: 0; box-sizing: border-box; }` or similar), bare `html`, `body`, `button`, `input`, `a` rules without a plugin scope class, linked reset libraries (`normalize.css`, `reset.css`, `sanitize.css`, `modern-normalize.css`), or Tailwind Preflight in the plugin head.

**Why.** Three things break. Light DOM components in the `canvas-accordion` family lose their intended padding and margins because universal rules match them directly. Typography (`font-family`, `line-height`, `color`) inherits across the Shadow DOM boundary and replaces Lato inside every component. The custom element host itself picks up the reset's box sizing and margin, shifting layout on every `<canvas-*>` tag.

**Fix.** When scanning an existing plugin for refactor, flag any reset pattern and offer to remove it or scope it to a plugin root class before touching canvas markup. The Google Fonts Lato link must stay, do not suppress `font-family` on `html` or `body`.

**Rule home.** `setup.md` Global CSS Reset Detection.
**Validation check.** Surface in `refactor-safety.md` Part D risk summary before any component work.
