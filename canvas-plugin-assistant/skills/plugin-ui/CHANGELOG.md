# Changelog

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
