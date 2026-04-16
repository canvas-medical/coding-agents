# Changelog

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
