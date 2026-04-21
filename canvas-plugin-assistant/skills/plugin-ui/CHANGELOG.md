# Changelog

## 4.8.0

### Added

- Empty State taxonomy in `references/component-usage.md`. Four types cover every plugin surface, first use (never had data), user cleared (data removed), filter no results (filter excludes everything), and load error (fetch failed, use `canvas-banner variant="error"` not the centered empty pattern). Picks the right type by cause rather than treating empty as one pattern.
- Content hierarchy rule. Heading plus one line of supporting text plus one primary action button, with the action omitted only when the user cannot act. Single line empty states are acceptable only inside containers narrower than 300 pixels.
- Voice rules. Name the domain object, not "data" or "results". Button labels start with a verb tied to the task. Educational on first use, blunt on filter no results.
- Clinical nuance rule. Distinguish recorded from not recorded. "No allergies recorded" passes, "No allergies" fails on an allergies surface because the blank state carries clinical weight that the copy must not erase.
- Loading, empty, error state machine. Four states (loading, populated, empty, error) with strict ordering. `canvas-loader` covers fetch in flight, the typed empty pattern mounts only after fetch resolves with zero rows, `canvas-banner variant="error"` covers failure. Prevents the common bug of an empty state flashing during the loading window.
- Accessibility guidance. Semantic heading inside the empty container so screen readers announce the state transition. `aria-live="polite"` wrap for filter empty regions that replace previously rendered rows.
- Four snippet variants in `DESIGN.md` Empty State section, one per type. First use with a primary add action. User cleared with a restore secondary. Filter no results with a Clear filters ghost button. Load error as a `canvas-banner` to show by contrast what not to reuse for failures.
- Placement rule in `DESIGN.md` Empty State. Center vertically and horizontally in short containers (card bodies, sidebar panels under 400 pixels). Top align with `--space-huge` padding in tall containers (full page regions, modal bodies) so the block sits where the eye lands.
- Empty States check block in `references/validation-checklist.md` Phase 3. Eight checks covering handler presence, typed empty, filter escape, loading gate, error contrast, content hierarchy, clinical distinction, and accessibility.
- Three Common Mistakes entries in `references/workflow.md`, empty state during loading, filter without escape, and generic empty copy. Each points at the state machine and the typed empty taxonomy.
- Key Rules entry in `SKILL.md` naming the three state machine and the Clear filters requirement for filter bars.
- Eval scenario 14 in `evals/evals.json` testing the filter no results escape. Exercises the typed empty copy, the Clear filters ghost button, and the heading element requirement for screen reader announcement.

## 4.7.0

### Added

- `data-drop-eligible` attribute on `canvas-sortable-list`. Every sibling list that can receive from the active drag source carries the attribute for the full duration of the drag. The source list itself does not. Styled by default with a thin outline matching `canvas-input`'s focus border via `var(--canvas-input-focus-border, #85b7d9)` and the input's `border-radius` via `var(--canvas-input-radius, var(--radius, .28571429rem))`. Uses `outline` rather than `border` so no layout shift occurs when the attribute flips on. Gives the user an immediate visual map of where the item can land before they commit, without coloring the source column or tinting any list.

## 4.6.0

### Added

- Cross list drag and drop on `canvas-sortable-list`. Lists that share a `group` value exchange items via pointer drag or keyboard. No new custom element, existing markup keeps working unchanged. When the attribute is omitted the component behaves exactly as it did in 4.5.x.
- `group` attribute on `canvas-sortable-list`. Same string value on two or more lists makes them compatible peers. Case sensitive string comparison.
- `accept` attribute on `canvas-sortable-list`. Comma separated group names the list will receive from. Defaults to the list's own group. Enables one way flows like an archive bucket that pulls from several sources without sending.
- `pull` attribute on `canvas-sortable-list`. Values `move` (default) or `clone`. A `clone` source leaves the original in place and drops a copy into the target, which supports template palettes and widget pickers.
- `disabled` attribute on `canvas-sortable-list`. Freezes the list so items cannot be dragged out and drops are refused. Applied statically or toggled at runtime.
- New events on `canvas-sortable-list`. `move` fires after a cross list commit with `{ item, fromList, toList, oldIndex, newIndex }`. `change` fires for every committed move with the same detail plus `type` equal to `reorder` or `move`. Cancelable pre commit twins `beforereorder`, `beforemove`, and `beforechange` snap the item back when `preventDefault()` is called, which enables permission gates and column capacity rules without visually accepting an unacceptable drop.
- `list.items` property getter. Returns the live array of `canvas-sortable-item` children in current DOM order. Rebuilds from the DOM on each read, no cached state. Consumers who prefer a snapshot to a delta stream read this in a Save handler.
- Keyboard cross list navigation on `canvas-sortable-item`. `ArrowLeft` and `ArrowRight` on a focused handle move the item into the previous or next list in the same group. Active only when the list has a `group` attribute and a compatible sibling exists. Sibling resolution goes by on screen position left to right.
- Shared ARIA live region. Within list reorders announce "Moved item to position N of M in <list label>." and cross list moves announce "Moved item from <source label> to <destination label>, position N of M." List labels resolve from `aria-labelledby`, then `aria-label`, then the list `id`, then the generic word "list".
- `data-drop-active` attribute on `canvas-sortable-list`. Toggled by the component while a cross list drag hovers this list. No default visual is applied. Consumers who want a column highlight can write their own `canvas-sortable-list[data-drop-active]` rule. The default cross list affordance is the placeholder insertion bar alone.
- `--canvas-sortable-min-height` CSS custom property. Default `calc(var(--space-medium) * 2)`. Ensures empty receiving lists remain reachable as drop targets.
- `.canvas-sortable-placeholder` class on the placeholder element created during a drag. Holds the insertion gap so items can animate into place via FLIP. No default color indicator, consumers can add one via their own rule on the class if desired.
- Four sample cards in `examples/showcase.html` under Sortable List. `Cross list kanban with shared group` shows three columns sharing `group="tickets"`. `Template palette with pull clone` shows a palette feeding a form builder without losing source items. `Bulk flow with accumulator and Save button` shows a Map keyed by item id collecting `change` events and flushing on Save. `Permission gate with beforemove` shows a locked column rejecting drops with a logged explanation.
- Cross List Drag and Drop and Single Drop vs Bulk Changes decision rules in `references/component-usage.md`. Spells out when to reach for cross list vs a plain Move to X button, and when to choose single drop writes vs bulk accumulation.
- Sortable List Keyboard, Sortable List Cross List Cancel, and Sortable List ARIA sections in `references/interaction-patterns.md`.
- Sortable Lists check block in `references/validation-checklist.md` Phase 2.
- Sortable List Dropzone, Sortable List Placeholder Bar, and Sortable List Minimum Height specs in `DESIGN.md`.

## 4.5.1

### Fixed

- `canvas-accordion-item` no longer toggles when the user clicks or keyboard activates an interactive descendant of `canvas-accordion-title`. The trigger handler now inspects `e.composedPath` and skips `toggle()` when any element along the path up to the shadow DOM `.title` node matches a native interactive element (`button`, `a[href]`, `input`, `select`, `textarea`), an ARIA role of button, switch, checkbox, radio, link, menuitem, tab, or option, or a canvas interactive component (`canvas-button`, `canvas-toggle`, `canvas-checkbox`, `canvas-radio`, `canvas-dropdown`, `canvas-combobox`, `canvas-multi-select`, `canvas-input`, `canvas-date-input`, `canvas-textarea`). The same filter runs on the keydown handler, so Enter and Space on a focused child button or toggle no longer trip the accordion. Plugin authors no longer need to add `event.stopPropagation` on interactive children of the title slot. Added a `With buttons in title` sample card in `examples/showcase.html` between the existing `With toggles in title` and `Multiple sections open` cards to exercise the behavior.

## 4.5.0

### Added

- `--canvas-accordion-nested-indent` CSS custom property. Controls the left padding applied to any `canvas-accordion-item` that sits inside another accordion's `canvas-accordion-content`. Default resolves through `var(--canvas-accordion-nested-indent, var(--space-small, 12px))` so the component inherits `--space-small` and falls back to 12 pixels when both layers are stripped. Has no effect on top level items. Set to `0` on an ancestor to disable the nested indent under that subtree, set to a larger value to deepen the hierarchy step.
- Global CSS rule `canvas-accordion-content canvas-accordion-item` in `canvas-plugin-ui.css` that applies the nested indent. Depth compounds automatically because every nested content holds its own nested items, level two steps in by one `--space-small` from level one, level three by two, and so on, without any per depth authoring.
- `Nested accordions (automatic indent)` sample card in `examples/showcase.html` between `Multiple sections open` and `Toggle event`. Demonstrates the three level cascade with no inline padding rules in the markup.
- `Container Padding Responsibility` section in `DESIGN.md`. Codifies the design system rule that horizontal inset is a container concern, not a component concern. Headings, paragraphs, buttons, accordions, and every other top level element sit flush with their parent's content box and rely on the container to supply outer padding. Nesting indent is documented as the separate concern with the nested accordion rule as the canonical example.
- Nested accordion guidance in `references/component-usage.md` Accordion vs Tabs section. Two bullets, one on container padding responsibility (wrap in a `canvas-card` or place inside a section that pads its children), one on the automatic nested indent and how to tune it with `--canvas-accordion-nested-indent`.
- Nesting documentation and Tokens table in `references/web-components.md` canvas-accordion entry. Replaces the prior "Locked component" line and adds explicit coverage of the container padding assumption.

## 4.4.0

### Added

- `canvas-sortable-list` auto scrolls its nearest scrollable ancestor while an item is being dragged toward the top or bottom edge. On `pointerdown` the component walks up from the list to find the first ancestor with `overflow-y` equal to `auto` or `scroll` whose `scrollHeight` exceeds its `clientHeight`, falling back to the document scroller when none qualify. While a drag is active, a 48 pixel edge hotspot (clamped to one third of the ancestor height for short panes) drives a `requestAnimationFrame` loop that increments `scrollTop` by up to 12 pixels per frame, ramped linearly by how deep the cursor sits inside the hotspot. The loop also re runs the placeholder and ghost position logic each tick so the list responds to items sliding under a stationary cursor. Scrolling stops on `pointerup`, when the cursor leaves the hotspot, or when the scroller hits its min or max. Hovering near an edge without an active drag has no effect. Vertical only. No new attributes, events, or slots. Added a dedicated `Auto scroll in a scrollable container` sample card in `examples/showcase.html` with 12 items in a 220 pixel pane so the behavior is exercisable.

## 4.3.4

### Fixed

- `canvas-input` date and datetime height parity with `canvas-dropdown`. The 4.3.1 reset on `::-webkit-datetime-edit` eliminated the 2 pixel gap but left a 0.57 pixel residual because Chromium's `::-webkit-calendar-picker-indicator` has `padding: 2px` on every side, giving the icon a `1em + 4px` outer box that slightly exceeds the declared `line-height: 1.21428571em`. The taller indicator dragged the flex row up by the difference. Added a shadow CSS reset that zeroes the padding on `::-webkit-calendar-picker-indicator` so the indicator sits within the text line box. Date, datetime-local, week, and month inputs now match the dropdown height to the pixel.

## 4.3.3

### Fixed

- `canvas-tooltip` arrow decoupling and viewport edge margin. The tooltip box now reserves an 8 pixel margin from every viewport edge, up from 4 pixels. When the box shifts inward to honor that margin, the arrow no longer follows the box center. Instead the arrow slides inside the tooltip box to keep its tip over the trigger's center axis (horizontal axis for top and bottom tooltips, vertical axis for left and right tooltips). The arrow is clamped to stay at least 6 pixels inside each tooltip corner so it never bleeds into the rounded border. Applies to all four orientations.

## 4.3.2

### Fixed

- `canvas-dropdown` arrow indicator now matches `canvas-combobox` and `canvas-multi-select`. Dropdown previously rendered a sharp CSS triangle using border tricks with fill `rgba(0, 0, 0, 0.8)`. Combobox and multi-select render a rounded chevron SVG with fill `#575757`. The three components sit side by side in the same rows and the inconsistent indicator was visible at a glance. Replaced the dropdown's CSS triangle with the combobox SVG and matched the `.arrow` CSS to the 8 by 5 pixel box the other two use.

## 4.3.1

### Fixed

- `canvas-input` height consistency across `type` values. Added a shadow CSS reset that zeroes `padding` on `::-webkit-datetime-edit` and `::-webkit-datetime-edit-fields-wrapper` inside the internal `input`. Without the reset, Chromium and WebKit render `type="date"`, `type="time"`, `type="datetime-local"`, `type="month"`, and `type="week"` 2px taller than `type="text"` because the datetime edit pseudo carries a 1px top and 1px bottom padding inside the content box. Date and time inputs now match the height of text inputs, `canvas-dropdown`, and `canvas-combobox` in the same row. Firefox ignores the WebKit pseudos and is unaffected.

## 4.3.0

### Added

- Warning about global CSS resets overriding canvas web component styles. Added one line in `SKILL.md` Key Rules. Added one bullet in `references/workflow.md` Common Mistakes covering universal selector rules, bare `html`/`body`/form element type selectors, linked reset libraries (normalize.css, reset.css, sanitize.css, modern-normalize.css), and Tailwind Preflight. Three failure modes are named, light DOM components losing their padding and margins, typography inheritance crossing the Shadow DOM boundary, and host box sizing shifts on every `<canvas-*>` element. Scope is advisory, flag and offer to fix, not a blocking prohibition. No validation check, no eval case.

## 4.2.0

### Added

- Native `<details>` and `<summary>` prohibition. Added in `SKILL.md` Key Rules alongside the existing `<input>` and `<select>` rule. Added as a two bullet block in `references/component-usage.md` Accordion vs Tabs section, one bullet for the prohibition and one bullet for the narrow exception when a custom trigger needs a multi column layout that cannot fit the `canvas-accordion-title` slot. Extended `references/validation-checklist.md` Phase 1 check 3 `No native replacements` to include `<details>` and `<summary>`. Added a second check under Phase 2 Accordions section that scans for any remaining native `<details>` or `<summary>` after refactor. Added a new `Native details and summary use` bullet in `references/workflow.md` Common Mistakes parallel to `Native input use`. Added one eval case covering the refactor scenario.

## 4.1.0

### New component

- `canvas-inline-row`. Layout primitive for a horizontal row of form elements. Encapsulates `display: flex`, `gap`, `align-items: flex-end`, `flex-wrap: wrap`, and per child flex sizing so the row contains itself inside `canvas-card-body` without overflow and wraps cleanly in narrow surfaces. Growing children (canvas-input, canvas-dropdown, canvas-combobox, canvas-multi-select, canvas-textarea) share available space with a 160 px minimum before wrapping. Natural width children (canvas-button, canvas-checkbox, canvas-radio, canvas-toggle) keep their content width. Consumers override per instance with `inline-role="grow"` or `inline-role="natural"`. Component tokens, `--canvas-inline-row-gap` (default `--space-small` then `12px`) and `--canvas-inline-row-item-min` (default `160px`). Component count is now 25.

### Added

- `Same Row Height Cohesion` section in `references/component-usage.md`. Form elements sharing a visual row must render at the same height. The `size` attribute is not a universal height tier across components. `canvas-button[size="sm"]` has a 36 px `min-height`, `canvas-dropdown[size="sm"]` only reduces the trigger font size and inherits default padding. The safe baseline for filter bars and inline forms is default size on every element in the row. Reserve `sm` for rows where every element is a button.
- `Inline Form Rows` section in `references/component-usage.md`. Centers on `canvas-inline-row` as the container. Lists use cases that extend the primitive, filter bar above a table, inline edit form, search bar, action bar. Filter bar use case covers the `canvas-card` wrapper, the optional `canvas-card-footer` for bulk action rows, and `canvas-input type="date"` for date range fields.
- Native `<input>` prohibition in `references/component-usage.md` Text Inputs vs Textareas section. Parallel to the existing native `<select>` prohibition. Covers all input types including text, email, password, number, tel, url, date, datetime-local, month, week, and time. Use `canvas-input` with the appropriate `type` attribute.
- Adjacent region card pattern in `references/component-usage.md` Cards and Content Containers. Two adjacent containers where one has `border-top: none` and connects visually to another through a shared `border-radius` are a multi region card. Replace the pair with `canvas-card` plus `canvas-card-body` plus `canvas-card-footer`.
- `Native input use`, `Mixed size tier in one row`, and `Missed inline row swaps` entries in `references/workflow.md` Common Mistakes. Feeds Refactor Safety Part D risk summary so the user sees the full swap plan before work begins.
- `Inline Form Rows (canvas-inline-row)` subsection in `references/validation-checklist.md` Phase 2. Four checks cover raw flex rows of form elements, mixed size tiers in one row, native inputs inside an inline row, and the filter bar card plus inline row plus footer structure.
- `canvas-inline-row` added to the Phase 1 tag allowlist in `references/validation-checklist.md`.
- `canvas-inline-row` section in `references/web-components.md` with API reference, child flex behavior table, per instance override recipe, component tokens, and when not to use.
- Filter Bar (with table and action footer) sample card in `examples/showcase.html` under the Form section, updated to use `canvas-inline-row`. Demonstrates filter row in `canvas-card-body`, table in `canvas-card-body no-padding`, selection count plus bulk action buttons in `canvas-card-footer`.
- `canvas-inline-row (primitive)` sample card in `examples/showcase.html` under the Form section. Demonstrates the component at standard width and in a 360 px wrap test container.
- Two entries in SKILL.md Key Rules to Never Forget. One extends the no raw HTML for components rule to explicitly name `<input>` and `<select>`. One names the same row height cohesion rule with a pointer to component-usage.md.

### Changed

- `Cards and Content Containers` section in `references/component-usage.md` rewritten. Promotes the four property signature (background, border, border-radius, box-shadow on one element) to the primary card imitation detector. Class names become secondary signals with an expanded list covering `container`, `filters`, `filter-bar`, `toolbar`, `section`, `wrapper`, `wrap`, `header`. Adds the adjacent region pattern as a new bullet.
- `Missed card imitations` bullet in `references/workflow.md` Common Mistakes rewritten to match the new detector model.
- `canvas-button` size rules in `references/web-components.md` updated. `sm` is reserved for card headers and table row actions where every element in the row is a button. For toolbars and inline form rows that include dropdowns, comboboxes, or inputs, use default size on every element in the row.
- `canvas-dropdown` size rules in `references/web-components.md` updated. Default is the baseline for forms, modals, filter bars, search bars, and inline edit rows. `sm` is only for compact contexts where every other element in the row is also `sm`. Removed the previous guidance to match button size attribute, which did not produce matching rendered heights.
- `canvas-input` section in `references/web-components.md` opens with an explicit native input prohibition above the Usage block. Lists every supported type.
- `Form Element Height Cohesion` section in `references/component-usage.md` cross links to Same Row Height Cohesion.
- Component count updated from 24 to 25 in `SKILL.md`, `README.md`, and `references/web-components.md`. Tag count updated from 43 to 44.
- `examples/showcase.html` `.row` helper class gains `flex-wrap: wrap`. Reference inline row samples using the raw flex pattern continue to work correctly in narrow viewports.

## 4.0.0

### Breaking

- `canvas-card-body` no longer applies `overflow-y: auto`. Cards that set `max-height` on the body to activate scrolling stop scrolling in 4.0.0. Wrap the body content in the new `canvas-scroll-area` component to restore scrolling. Migration recipe in `references/web-components.md` canvas-scroll-area section.
- `canvas-card` outer container no longer applies `overflow: hidden`. Corner clipping of slotted body and footer backgrounds is now handled by applying the card border-radius (minus 1px for the border) to the first and last slotted child via `::slotted(...:first-child)` and `::slotted(...:last-child)`. This makes the card transparent to popup children, so a `canvas-dropdown` or `canvas-combobox` menu inside a card can extend past the card edge without being clipped.
- The `.table-scroll` helper pattern for wide tables is replaced by `<canvas-scroll-area horizontal>`. Plugins that used a raw `.table-scroll` div migrate to the component.

### Added

- New `canvas-scroll-area` component. Declarative, opt in scroll container with `vertical` and `horizontal` boolean attributes. Auto applies `tabindex="0"` when a direction attribute is present and no consumer `tabindex` is already set. Shadow DOM wrapper around a single slot. Consumers set dimensions via `style=` or external CSS.
- `Cards and Content Containers` section in `references/component-usage.md` with the decision rule for when to use `canvas-card` versus a flat div. Flags raw card wrappers with class names `card`, `panel`, `box`, `tile` as refactor targets. Flags raw divs combining background, border, border-radius, and box-shadow as refactor targets.
- `Scroll Areas` section in `references/component-usage.md` covering direction selection, the accessibility label requirement, and the restriction on placing `canvas-dropdown`, `canvas-combobox`, and `canvas-multi-select` inside a vertical scroll area (lifted in 4.1.0 after the Popover API migration). Tooltip is exempt because it hides on scroll.
- `Cards and Content Containers (canvas-card)` subsection in `references/validation-checklist.md` Phase 2. Six checks cover raw card wrappers, style signature imitations, footer component usage, component owned padding, stacked body usage for multi section cards, and the removed card body scroll reliance.
- `Scroll Areas (canvas-scroll-area)` subsection in `references/validation-checklist.md` Phase 2. Five checks cover raw overflow on plugin level divs, explicit direction attribute, accessibility label, forbidden popup nesting, and the legacy `.table-scroll` migration.
- `Common Mistakes` section in `references/workflow.md`. Covers missed card imitations, missed scroll area swaps, silent card body overflow reliance, and forbidden popup nesting. Feeds the Refactor Safety Part D risk summary so the user sees the full swap plan.
- `canvas-scroll-area` section in `references/web-components.md` with full API reference, usage examples, accessibility notes, clipping caveat, and the card body migration pattern.
- `canvas-scroll-area` added to the Phase 1 tag allowlist in `references/validation-checklist.md`.
- Cross reference from the `canvas-card` section in `references/web-components.md` back to the new `Cards and Content Containers` section in `component-usage.md`.

### Changed

- `canvas-card` section in `references/web-components.md` updated. The old `Scrollable body` paragraph is gone. New `Rendering` and `Scrolling` paragraphs describe the 4.0.0 behavior.
- `Table Behavior in Narrow Containers` in `references/component-usage.md` replaces the `.table-scroll` wrapper pattern with `<canvas-scroll-area horizontal>`.
- `Phase 6 check 3 Token usage` in `references/validation-checklist.md` extended to flag combined background, border, border-radius, and shadow on one element as a possible card imitation.
- `examples/showcase.html` Scrollable body demo updated to use the `canvas-scroll-area` wrapper pattern.

## 3.2.0

### Changed

- Refactor Safety Part D rewritten from a structural-only pre-listing to a three-tier risk summary (cosmetic, clear migration, unclear migration). The agent now presents all proposed changes grouped by risk before modifying any markup. The user sees the full scope and approves before work begins.
- Refactor Safety Part A expanded to scan for child selectors targeting elements inside nodes being replaced by web components. These children move behind a Shadow DOM boundary after migration and existing selectors will not reach them.

## 3.1.0

### Added

- DESIGN.md at the skill root as the visual specification layer. Single source of truth for colors, typography, spacing, shape, token system, text-background pairing, visual hierarchy, information density, truncation, dates, badge color semantics, button spacing, patterns without components, and consolidated do's and don'ts.

### Changed

- Extracted visual specification content from web-components.md (token system, fallback chain, button spacing, patterns without components), component-usage.md (text-background pairing, badge color semantics, visual anti-patterns), interaction-patterns.md (visual hierarchy, information density, long text truncation, date formatting), and SKILL.md (color palette, spacing, shape rules). Each donor file now cross-references DESIGN.md.
- Updated workflow.md routing table Steps 4 and 5 to include DESIGN.md as a reference.
- Updated validation-checklist.md attributions to point to DESIGN.md for visual rules.
- Updated CLAUDE.md maintenance workflow with design spec checks and file consistency matrix column.
- Updated SKILL.md escalation ladder Level 4 to reference DESIGN.md for token selection.

## 3.0.1

### Fixed

- All 12 eval assertions referenced old file names (tokens.css, typography.css, canvas-components.js). Updated to canvas-plugin-ui.css and canvas-plugin-ui.js.
- SKILL.md restructured to lead with the workflow pointer so Claude reads the execution sequence before rules. Color palette and customization boundaries moved after key rules.
- Stale escalation ladder cross-reference to web-components.md removed (section was deleted in 3.0.0).
- btn-default CSS class name in customization boundaries replaced with variant="ghost" web component attribute.
- Duplicate toggle-submit prohibition removed from SKILL.md customization boundaries (canonical location is Key Rules).
- Toggle-submit rule deduplicated across component-usage.md and interaction-patterns.md with cross-references to the canonical statement in SKILL.md.
- Duplicate keyboard efficiency section removed from interaction-patterns.md Clinical Environment (already covered by Form Submission section).
- Validation checklist cross-references hardened. Every "see SKILL.md" or "see interaction-patterns.md" check now includes the rule criterion inline. Duplicate select check (Phase 1 and Phase 2) and duplicate table aria-label check (Phase 2 and Phase 5) removed.
- Confirmation hierarchy moved from interaction-patterns.md to component-usage.md where it belongs as "when to use which pattern" guidance.
- README.md design rules section expanded with a one-sentence summary before the SKILL.md redirect.
- CLAUDE.md journal directory section clarified with guidance on identifying the active issue directory.

## 3.0.0

### Breaking

- Asset pipeline restructured. The 24 individual component files in assets/components/, the two CSS files (tokens.css, typography.css), and the bundle script (scripts/bundle.sh) are replaced by three files. assets/canvas-plugin-ui.js (all components and utilities), assets/canvas-plugin-ui.css (tokens and typography merged), assets/head.html (canonical head snippet).
- All components wrapped in a single IIFE under the CanvasUI namespace on window. CanvasUI.register(tag, cls) replaces per-file customElements.define with double registration guards.
- Google Fonts @import removed from CSS. Lato now loads via a link tag in the head snippet. Plugins must include the Google Fonts link tag.
- Bundle script removed. Claude copies canvas-plugin-ui.js and canvas-plugin-ui.css directly to the plugin static directory during setup.
- Plugin HTML boilerplate changed from two link tags and one script tag to three tags (Google Fonts link, CSS link, JS script).
- SimpleAPI routes reduced from three (tokens.css, typography.css, canvas-components.js) to two (canvas-plugin-ui.css, canvas-plugin-ui.js).

### Added

- CanvasUI.utils.dismissModal() and CanvasUI.utils.resizeModal(width, height) for host communication on DEFAULT_MODAL and NOTE surfaces. MessageChannel handshake (INIT_CHANNEL) handled automatically.
- canvas-option defined once as a shared element instead of duplicated across canvas-dropdown, canvas-combobox, and canvas-multi-select.
- assets/head.html as the canonical reference for the three tags every plugin includes in its head.
- Host Communication section added to surface-selection.md documenting CanvasUI.utils.

### Changed

- All documentation updated. SKILL.md, README.md, CLAUDE.md, web-components.md, validation-checklist.md, workflow.md, surface-selection.md, CHANGELOG.md.
- Component count remains 24 (22 files, 44 tag names). No components added or removed.
- Version bumped to 3.0.0 in SKILL.md frontmatter.

## 2.2.0

### Added

- `canvas-button-group`. Layout wrapper that joins canvas-button children into a connected unit. Uses ::slotted to override border-radius on first, middle, and last children. Fluid attribute for full-width equal distribution.
- `canvas-textarea`. Dedicated multi-line text area replacing the multiline attribute on canvas-input. Auto-resize via grid overlay, max-rows to cap growth and scroll, maxlength with live character counter, no-resize option. Shares visual tokens with canvas-input.
- `canvas-tooltip`. Infrastructure component placed once in the body. Activates a global tooltip system via data-canvas-tooltip attributes on any element. Direct mouseenter/mouseleave listeners per element, MutationObserver for dynamic elements, SVG arrows per direction, scroll listener hides tooltip immediately, viewport edge flipping.

### Changed

- `canvas-loader` rewritten. Positioning modes changed from inline/centered/inverted to inline/overlay/fullscreen. Overlay and fullscreen modes include a backdrop with light (default), dark, or none options. Spinner colors auto-invert on dark backdrop. Flex centering replaces absolute centering.
- `canvas-input` multiline attribute removed. Use `canvas-textarea` instead.
- Component count updated from 19 to 22 in SKILL.md, README.md, workflow.md, and validation-checklist.md.
- component-usage.md updated with tabs as the view mode switching pattern, textarea variants section, and tooltip best practices.
- bundle.sh gained a --create flag that runs mkdir -p on the target directory if it does not exist.

## 2.1.0

### Added

- `canvas-loader`. Loading spinner matching the Semantic UI Loader used in Canvas. Four sizes (mini, small, default, large), inline and centered positioning modes, inverted mode for dark backgrounds, and optional text label. Arc color is #767676 (gray) matching the Canvas home-app, not blue.

### Changed

- Component count updated from 18 to 19 in SKILL.md and README.md.
- Loading Spinner removed from the Patterns Without Components section of web-components.md since canvas-loader replaces it.
- component-usage.md loading states guidance updated to reference canvas-loader.
- canvas-loader added to the valid tag name list in validation-checklist.md.

## 2.0.0

Web components migration. The design system moves from CSS class patterns with inlined base.css to 18 native Custom Elements with Shadow DOM scoped styles. This is a breaking change. Plugins built with the old class system need to be migrated to web component elements.

### Added

**Web components.** 18 self-contained Custom Elements, each with Shadow DOM scoped styles, double registration guard, and three-layer CSS custom property fallback chain (component token, global token, hardcoded default).

- `canvas-button`. Four color variants (primary/green, secondary/blue, ghost/gray, danger/red), three sizes (base, sm, xs), form submission via ElementInternals.
- `canvas-badge`. 13 Semantic UI colors, 4 sizes (mini, tiny, small, large), basic (outlined) and circular variants.
- `canvas-chip`. Dismissible tag sharing the badge color palette. Fires a `dismiss` event on X click.
- `canvas-input`. Text input and textarea with integrated label, error state, and form participation via ElementInternals.
- `canvas-radio`. Locked radio matching Canvas Semantic UI. Grouped by shared `name` attribute. ElementInternals for form data.
- `canvas-checkbox`. Locked checkbox. White box with dark checkmark, no colored fill. ElementInternals for form data.
- `canvas-toggle`. Locked toggle switch. Blue active track (#0D71BC, not green). No form participation because toggles mean instant effect.
- `canvas-banner`. Four semantic variants (error, warning, success, info). Dismissible option. Slotted content for rich messages.
- `canvas-card`. Three elements (canvas-card, canvas-card-body, canvas-card-footer). Raised variant, no-padding option for edge-to-edge content.
- `canvas-dropdown`. Non-searchable select with keyboard navigation. Uses `canvas-option` children for options. ElementInternals for form data. Default and sm sizes.
- `canvas-combobox`. Searchable dropdown with type-ahead filtering and viewport flip. Shares `canvas-option`. ElementInternals.
- `canvas-multi-select`. Multi-value combobox with chip rendering, inline checkbox indicators, backspace to remove. Shares `canvas-option`. ElementInternals.
- `canvas-tabs`. Four elements (canvas-tabs, canvas-tab, canvas-tab-label, canvas-tab-panel). Bold-shift prevention, badge support, overflow fade masks.
- `canvas-accordion`. Four elements (canvas-accordion, canvas-accordion-item, canvas-accordion-title, canvas-accordion-content). Chevron animation, nested interactive elements in title without triggering expand/collapse.
- `canvas-modal`. Four elements (canvas-modal, canvas-modal-header, canvas-modal-content, canvas-modal-footer). Three sizes (small, medium, full), focus trapping, persistent mode, two-layer backdrop.
- `canvas-table`. Five elements (canvas-table, canvas-table-head, canvas-table-body, canvas-table-row, canvas-table-cell). Compact, celled, selectable, sticky, striped modifiers. Row state colors (positive, warning, negative, active).
- `canvas-sortable-list`. Two elements (canvas-sortable-list, canvas-sortable-item). Pointer event drag with FLIP animation, keyboard reorder via ArrowUp/ArrowDown.
- `canvas-sidebar-layout`. Three elements (canvas-sidebar-layout, canvas-sidebar, canvas-content). Three width variants (default 260px, narrow 210px, wide 400px), fullscreen mode.

**Infrastructure.**

- `assets/tokens.css`. Shared token file with raw palette, semantic aliases, spacing, shape, and transition tokens.
- `assets/typography.css`. Heading and paragraph styles matching Canvas Semantic UI. Loads Lato via `@import`.
- `canvas-option`. Shared marker element registered once, used by dropdown, combobox, and multi-select.
- `scripts/bundle.sh`. Concatenates all component JS into `canvas-components.js` and copies `tokens.css` and `typography.css` to a target plugin static directory.
- `examples/showcase.html`. Demonstration page with all 18 components and multiple variants.

**Skill guidance.**

- Escalation ladder in web-components.md and SKILL.md. Four friction levels for how agents approach UI work (use components, customize via attributes, override via CSS custom properties, build novel HTML as last resort).
- Plugin HTML boilerplate in web-components.md for the standard `<head>` structure linking tokens.css, typography.css, and canvas-components.js.
- Patterns Without Components section in web-components.md for tooltip, divider, empty state, spinner, and patient context header.
- Banner variant guide in component-usage.md with usage rules for error, warning, success, and info variants.
- Modal patterns in component-usage.md with size selection, dismiss behavior, and confirmation pattern.
- Text-background pairing rules and anti-patterns in component-usage.md.

### Changed

- web-components.md expanded from 10 to 18 component API entries.
- component-usage.md updated from CSS class references to web component element names. UX rules merged from interface-rules.md.
- workflow.md rewritten. Steps 3 and 4 target web component selection and building instead of base.css pasting.
- validation-checklist.md rewritten. All six phases updated for web components. Reduced from 254 lines to ~110 lines because components handle most of what was previously checked manually.
- SKILL.md updated to remove CSS class approach, add escalation ladder, update key rules, and update reference file list.
- evals.json assertions updated from CSS class patterns to web component elements.
- Toggle-submit prohibition scoped to UI segments (form, card, modal, accordion section) rather than the entire page. A toggle in one independent segment can coexist with a save button in a separate segment.
- Phase 0 of validation checklist now verifies bundled asset files exist in the plugin's static directory before checking HTML references.

### Removed

- `references/components-markup.md`. All patterns replaced by web components or moved to the Patterns Without Components section.
- `references/components-interactive.md`. All JS implementations replaced by web components.
- `references/interface-rules.md`. CSS specifications now internal to components. UX rules extracted to component-usage.md.
- `assets/base.css`. CSS class component library replaced by web components.
- `assets/tokens-legacy.css`. Old token file with component-specific variables replaced by tokens.css.

## 1.3.3 (2026-03-27)

### Components changed
- Toggle: click target moved from button to `.toggle-wrap` wrapper. Button gets `pointer-events: none`, wrapper gets `user-select: none`. Hover on `.toggle-wrap:hover .toggle`. Three markup variants documented (label right, label left, standalone). `toggleSwitch(wrap)` function replaces inline onclick.
- Tabs: two-layer bold-shift prevention CSS added to base.css (was documented in interface-rules but never implemented). `.tab-item` gets `position: relative`, `color: transparent`, `font-weight: bold`. `.tab-label` absolutely positioned with visible text. Reserve badge hidden via `.tab-item > .tab-badge { visibility: hidden }`.

## 1.3.2 (2026-03-27)

### Skill infrastructure
- Added CLAUDE.md with mandatory modification protocol, semver rules, file consistency matrix, pre-change questions, and patterns to flag

## 1.3.1 (2026-03-27)

### Components changed
- Toggle: inactive track corrected to `#F4F4F4`, hover to `#DEDEDE`, active to `#0D71BC` from Canvas source inspection. Removed track background transition so hover is instant in both directions. Thumb slide animation kept on `::after` only.

## 1.3.0 (2026-03-27)

### Refactor safety
- JavaScript dependency scan in workflow Step 4: traces all DOM access points (getElementById, querySelector, inline handlers, dataset reads, form name references) before modifying existing HTML
- Risk classification: cosmetic changes proceed freely, structural changes with clear migration require declarations, structural changes with unclear migration stop and surface to the user
- Migration declaration format for audit trail and forced pre-planning of JS updates
- Risk-based pre-listing trigger replaces the old "more than 3 violations" count-based rule
- New validation Phase 4 (Functional Preservation): verifies getElementById targets, querySelector targets, inline handler targets, form name contracts, data attribute contracts, and function count integrity after refactoring
- Validation checklist expanded from five phases to six (Functional Preservation inserted after UX Patterns)
- New eval case testing refactor safety with JavaScript-bound tabs and native select replacement

### Skill infrastructure
- README restructured around iterative usage (new plugin, existing overhaul, iterating)
- SKILL.md trigger description tightened, mentions refactor safety and skill output

## 1.2.0 (2026-03-27)

### Components added
- Multi-select combobox with chip selections, inline checkboxes, search filtering
- Segment card replacing the old flat card (body segments, gray footer, raised variant)
- Modal with two-layer backdrop (fixed backdrop + scrollable overlay), three sizes (small, medium, full), stretch modifiers (full-width, full-height)
- Dismissible banner variant with X button

### Components changed
- Buttons: removed `btn-ghost` and `btn-disabled`. Added `btn-default` (gray, for cancel/neutral). Disabled is now `opacity: 0.45` via the `disabled` attribute on any variant
- Tabs: two-layer structure for bold-shift prevention. Invisible bold text reserves width, visible label overlays with absolute positioning
- Chips: sized to match SUI `.ui.label` (background #e8e8e8, inset box-shadow border, asymmetric padding). Dismiss icon upgraded to 10x10 stroke-width 2
- Tables: aligned to Canvas patient list pattern (white header, no outer border, border-collapse collapse, 2px header border). Added `.table-scroll` for horizontal scrolling
- Banners: documented real Canvas distribution (error/warning dominant, success almost never used). Added placement and spacing rules

### Skill infrastructure
- Lato font loading added to HTML boilerplate (plugins render in iframes that do not inherit parent stylesheets)
- Interactive component reference loading made mandatory in SKILL.md key rules and workflow common mistakes
- SKILL.md trigger description expanded with more component keywords and anti-pattern triggers
- README rewritten with realistic usage prompts for two scenarios (new plugin, existing overhaul)
- Validation checklist updated for all new components and patterns
- Iframe width guidance: CSS media queries do not work in plugin iframes, design for known surface width

## 1.1.0 (2026-03-26)

### Components added
- Chip component (dismissible badge variant)
- Badge system aligned to Semantic UI Label (13 solid colors, basic bordered variant, size tiers)
- Banner aligned to Semantic UI Message (4 semantic variants, toast removed)

### Components changed
- Accordion corrected from Canvas source inspection (borderless basic variant, h3 headers, 7px padding, 34.58px natural height)
- Validation checklist rewritten as five-phase sequential protocol

## 1.0.0 (2026-03-25)

Initial release. Core design system with buttons, forms, checkboxes, radios, toggles, cards, tables, tabs, accordions, dropdowns, comboboxes, tooltips, dividers, skeletons, spinners, badges, banners, empty states, confirmation dialogs, patient context header.
