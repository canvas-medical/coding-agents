# Changelog

## 4.31.3

### Fixed

- `references/web-components.md` authoritative count corrected from 49 tag names to 50. The `canvas-accordion-actions` element added in 4.31.0 took the registered tag count to 50, but the header line was never updated, so the count that other files point to as authoritative understated the system by one tag. The component count stays 30 because `canvas-accordion-actions` is a subcomponent of the accordion rather than a standalone component. Verified by counting the `CanvasUI.register('canvas-...')` calls in `assets/canvas-plugin-ui.js`, which total 50. Documentation only, no component output change.

## 4.31.2

### Fixed

- `canvas-progress` active sweep no longer animates `width`, which forced a layout and a paint on every frame and burned CPU for as long as an active bar was on screen. The `progress-active` keyframe now animates `transform: scaleX` from 0 to 1 with `transform-origin: left`, so the same left to right sweep composites on the GPU. The `.bar::after` overlay keeps its full size and is scaled rather than grown. No visible change to the animation at default sizes.
- `canvas-progress` now respects `prefers-reduced-motion: reduce`. The active sweep was the only animation in the design system with no reduced motion gate. Under reduced motion the `.bar::after` overlay is set to `display: none` and `animation: none`, leaving a plain determinate bar, matching the static affordance `canvas-loader` already shows. See `references/web-components.md` canvas-progress Active animation.

### Changed

- `examples/showcase.html` `.component-section` wrappers gain `content-visibility: auto` with `contain-intrinsic-size: auto 600px`, so the browser skips rendering sections scrolled offscreen and the page's many infinite CSS animations (the eleven `canvas-loader` spinners and the active progress bar) only run while their section is on screen. This cuts idle CPU on the long showcase page. The a11y scanner forces the sections back to fully rendered for the duration of a run by toggling an `a11y-scanning` class on the document element, since the whole page scan steps the scroll container through the page and relies on offscreen content painting as it scrolls into view, so scan coverage is unchanged.

## 4.31.1

### Fixed

- `canvas-calendar` no longer fires the `aria-required-children` violation. The outer `.layout` container carried `role="grid"` while holding only the navigation, the weekday header, the day grid, and the picked list, so it claimed to be a grid yet owned no rows. The role is removed, leaving the real grid on the inner `.days` element, which already has its `role="row"` wrappers, `role="gridcell"` buttons, and grid `aria-label`. The weekday header is now decorative, marked `aria-hidden="true"` with its `role="row"` and per-cell `role="columnheader"` removed, since each day cell's `aria-label` already names the full weekday, so no information is lost and `aria-required-parent` does not regress. The now unused `_dayFullNames` helper is removed. The change is markup and ARIA only, the calendar renders identically. Verified on the showcase axe scan, `aria-required-children` dropped from 16 affected nodes to zero with passing rule count unchanged. See `references/web-components.md` canvas-calendar ARIA.

## 4.31.0

### Added

- `canvas-accordion-actions`, a new element that holds interactive header controls beside the trigger button instead of inside it. The element registers from the same file as the rest of the accordion. `canvas-accordion-item` now renders a header row with the trigger `<button>` and a sibling actions container. The button keeps `flex: 1` so the whole left region stays the click target, and the actions container pins to the far right, vertically centered, with its children at natural size. The actions container stays hidden and adds no spacing when an item has no `canvas-accordion-actions`. Place a `canvas-toggle`, `canvas-checkbox`, `canvas-radio`, or `canvas-button` in the actions slot. Because the controls render outside the button, their clicks never toggle the panel and screen readers can reach them. This clears the `nested-interactive` violation that fired whenever an interactive control sat inside `canvas-accordion-title`. See `references/web-components.md` canvas-accordion and the showcase accordion section.

### Changed

- `canvas-accordion-title` is now for non-interactive content only, text and an optional `canvas-badge`. The title sizes to its content and aligns to the start, so a badge sits right beside the label rather than being pushed to the far right with a `flex: 1` span. Interactive controls move to the new `canvas-accordion-actions` slot.
- `canvas-accordion-item` no longer inspects the event path to suppress toggling when a click comes from an interactive child. The `isFromInteractiveChild` filter and its selector list are removed. Suppression is no longer needed because interactive controls live outside the trigger button in the actions slot. Behavior change for any consumer that placed an interactive control directly inside `canvas-accordion-title`. That control now both fires the `nested-interactive` violation and toggles the panel on click. Move such controls into `canvas-accordion-actions`. Documented as an anti-pattern in `references/anti-patterns.md` Interactive Control in Accordion Title.

## 4.30.2

### Fixed

- `canvas-radio` no longer reserves trailing space when it has no `label`. The `.label-text` span always carried an `8px` left padding, so a label-less radio rendered the dot with an empty gap to its right. A `.label-text:empty` rule now drops the padding to `0` when the label is empty, leaving a radio with a visible label unchanged.

## 4.30.1

### Fixed

- `canvas-modal` now scrolls from the top with its `2rem` overlay padding intact when the modal is taller than the viewport. Previously a tall modal centered the dialog in the fixed `.scroll` overlay, and the part above the center point was clipped and could not be reached by scrolling, so the header sat flush against the top edge with no breathing room. Two changes fix it. The overlay uses `align-items: safe center` and the `margin: auto` is removed from `.modal`, so the dialog still centers when it fits but falls back to top alignment when it overflows. And `open()` focuses the first control with `preventScroll: true` then resets `scroll.scrollTop` to `0`, because focusing the dialog otherwise scrolled the focused element into view and consumed the top padding on open. Short modals still center vertically. The showcase Modal section gains a Medium, long content, scrolls example so the behavior can be reviewed in a browser.

## 4.30.0

### Added

- `canvas-input` gains a `format="phone"` attribute that masks a North American phone number as the user types. The display fills in progressively, `000`, then `(000) 000`, then `(000) 000-0000`, and the field accepts at most 10 digits, matching the home-app patient phone field in `PhoneNumber.tsx`. The mask exists only for display. The `value` property and the form value both return the raw digits, so typing `(555) 123-4567` yields `el.value === "5551234567"`, which is what a backend expects. The setter accepts either raw digits or a formatted string and normalizes to the mask. A new `_raw` field backs the value, and the phone helpers (`_phoneFormat`, `_phoneParse`, `_caretAfterDigit`, `_applyPhoneMask`, `_assignValue`) live on the component. The caret is preserved by digit position during edits so inserting a digit mid-number does not jump the cursor. The component does not validate the phone itself. Validation stays with the consumer through the `error` attribute, consistent with every other input in the system. When `format` is absent the input behaves exactly as before. Pair the attribute with `type="tel"` for the numeric mobile keypad. See `references/web-components.md` canvas-input Phone formatting and the `component-samples/phone.html` sample.
- Documentation for phone validation patterns. `references/patterns.md` gains a Phone Field with Validation copy-paste template. `references/component-usage.md` Feedback and Status now explains why validation runs on the `change` event (blur) rather than per keystroke, and states that `canvas-input` never validates itself so the rule and message live in the consumer. `references/anti-patterns.md` gains a Hand-Rolled Phone Mask entry. `references/validation-checklist.md` Phase 2 gains a Text Inputs block. The showcase Input section gains a phone formatting card with a live raw-value readout and a blur-validation example, and the realistic form gains a phone field so the submitted `FormData` shows raw digits.
## 4.29.4

### Fixed

- `canvas-accordion-item` mirrors the content id onto the shadow `slot[name="content"]`. The shadow trigger button has carried `aria-controls` pointing at the content id since the original disclosure pattern landed, but the id lived only on the slotted `canvas-accordion-content` element in light DOM. axe resolves IDREFs from the source element's shadow scope, so `button.getRootNode().getElementById` could not see the light DOM id and `aria-valid-attr-value` fired on every open item. The shadow template now also sets `id` on the content slot, and `_assignSlots` keeps that slot id in sync with the resolved `this._contentId` whenever the slotted content carries its own id. The button's `aria-controls` now resolves inside its own shadow scope, the rule clears at all 10 nodes, the APG accordion disclosure pattern stays intact, and screen readers continue to follow `aria-controls` through the flatten algorithm to the slotted content in light DOM.

## 4.29.3

### Fixed

- `canvas-accordion-item` moves the title id from the shadow trigger button to the slotted `canvas-accordion-title` in light DOM. The shadow `.title` button now carries `aria-labelledby` pointing at that light DOM id instead of carrying the id directly. `canvas-accordion-content` continues to carry `aria-labelledby` pointing at the same id. Because the id now lives in light DOM, `axe.getElementById` resolves it and the `aria-valid-attr-value` violation that previously fired on every open accordion item clears. No visible markup change, no CSS change, the slotted title still renders inside the trigger button exactly as before.
- `canvas-calendar` shadow `.layout` wrapper gains `role="grid"`. The `.day-names` row with `role="row"` now has a grid ancestor, which satisfies `aria-required-parent` without moving day-names into the `.days` grid or wrapping it in a new element. The existing `role="grid"` on `.days` is kept, axe walks ancestors for context-role checks so nested grids do not regress. No visible markup change, no CSS change, the calendar renders identically.

## 4.29.2

### Changed

- Reverted visible markup and CSS in three areas to match the state on `main` before the a11y branch landed, while keeping every invisible a11y improvement (aria attributes, AriaProxy host hygiene, dropdown accessible name resolution, sidebar and content tabindex defaults, filter-bar role default, tabs aria-label injection). `canvas-accordion-item` shadow DOM returns to a single `.title` button with the chevron and the `slot[name="title"]` inside the same button. The accordion focus ring returns to the row-wide `outline-offset: -2px` style. `canvas-calendar` shadow DOM puts `.day-names` back above the `.body` grid as a sibling rather than nested inside `.days`, the `_renderGrid()` method returns to `innerHTML = ''`, and the `.cell.outside` color returns to `rgba(0, 0, 0, 0.45)`. The `--palette-text-muted` token returns to `#767676`. The three `--canvas-calendar-*-bg` overrides added at the `:root` block are removed. The `references/web-components.md` accordion accessibility paragraph reverts to describe the restored `aria-controls` and `role="region"` wiring. Note that this re-opens `aria-required-parent` on calendar day-names, `color-contrast` on muted text and on outside-month and selected calendar chips, and `nested-interactive` on accordions that slot interactive controls into the title. See `.artifacts/journal/projects/canvas-plugin-tools/fix/canvas-ui-a11y/009-execution-scope-decision.md` for the full classification.

## 4.29.1

### Fixed

- `canvas-combobox` and `canvas-dropdown` now scroll the pre-selected item to the center of the list when the menu opens. Previously the list always opened at the top regardless of which item was selected. Each component gains a `_scrollToSelected()` method that fires inside a `requestAnimationFrame` after the menu is visible. It uses `getBoundingClientRect` to measure the selected item's position relative to the `.menu` scroll container, then sets `menu.scrollTop` directly so only the list scrolls and no outer viewport or ancestor is affected. The browser clamps to valid scroll bounds naturally when the item is near the top or bottom of the list.

## 4.29.0

### Added

- Shared accessibility helpers near the top of `assets/canvas-plugin-ui.js` reused by every component touched in Sessions 1 through 4. `cuid` generates per element unique ids so duplicate `id="err"` collisions on multiple instances of `canvas-input` and `canvas-textarea` no longer occur. `reduceMotion` is a runtime `matchMedia` helper for `prefers-reduced-motion: reduce`, used by `canvas-loader` to swap the spinning arc for a static affordance. `trapFocus` is a shadow DOM aware focus trap that descends `composedPath` and open shadow roots, used by `canvas-modal` so Tab and Shift Tab cycle inside the modal even when the focusable target lives in another component's shadow root. `AriaProxy` is a class mixin that mirrors `required`, `aria-invalid`, `disabled`, `aria-describedby`, `aria-labelledby`, `aria-controls`, `aria-expanded`, and `aria-activedescendant` from the host onto the inner control returned by `_ariaProxyTarget`. `SR_STATUS_CSS` is a visually hidden CSS template that components concatenate into their shadow style block to render screen reader only severity words. `PREFERS_REDUCED_MOTION_CSS` is a shadow style block that gates animation duration, iteration count, transition duration, and scroll behavior under `prefers-reduced-motion: reduce`. The helpers are scoped to the IIFE so they do not leak onto `window`.
- `examples/a11y-harness.html` is a manual axe core verification fixture loaded from the unpkg CDN. The page mounts the showcase component variants, runs `axe.run` against the document, and writes violations into a `<pre>` block. No build step, no test runner. Covers the manual axe pass at the end of every a11y session.
- `evals/evals.json` extends from 18 cases to 29 cases. Evals 19 through 22 cover Session 0 invariants such as helper presence, harness markup, and no duplicate ids after render. Evals 23 through 27 cover Session 3 invariants such as the table role tree, the tabs roving tabindex, and the accordion native button trigger. Evals 28 and 29 cover Session 4 invariants such as banner role split by variant, badge severity word, chip named dismiss, progress indeterminate handling, and button AriaProxy mirroring.
- Session 1 form widgets adopt `AriaProxy`. `canvas-input`, `canvas-textarea`, `canvas-checkbox`, `canvas-radio`, `canvas-date-input`, and `canvas-toggle` mirror the host `required`, `aria-invalid`, `disabled`, `aria-describedby`, `aria-labelledby`, `aria-controls`, `aria-expanded`, and `aria-activedescendant` attributes onto the inner `<input>`, `<textarea>`, or composite control. Error spans use `cuid` ids so `aria-describedby` always points at a unique target. Labels use `cuid` ids and the inner control points `aria-labelledby` at the label id so screen readers announce the label even when the visible label lives in shadow DOM. `canvas-radio` was rebuilt as a real composite. The radios now carry `role="radio"` inside a `role="radiogroup"` host with arrow key roving tabindex, mirroring the `focusGrid` template `canvas-calendar` uses. `canvas-date-input` wires `aria-controls` from the trigger combobox to the popover id and moves focus into the inner calendar grid via `focusGrid` on open.
- Session 2 selection widgets and overlays wire real `aria-activedescendant` references. `canvas-dropdown`, `canvas-combobox`, `canvas-multi-select`, and `canvas-menu-button` generate option ids via `cuid` so the trigger always points at a real element id rather than a literal `opt-N` token. `canvas-multi-select` no longer hides selected options via `display: none`, the listbox keeps every option in the tree, and the chip row sits inside the trigger so screen readers can traverse the full option set. `canvas-menu-button` carries `role="menu"` on the popup, `role="menuitem"` on each option, and mirrors `aria-haspopup="menu"` and `aria-expanded` onto a slotted trigger automatically. `canvas-popover` accepts `aria-labelledby` on the surface and restores focus to the trigger on close. `canvas-modal` wires `aria-labelledby` from the dialog to its `canvas-modal-header`, sets `inert` on the background while open, runs the Session 0 `trapFocus` helper so Tab and Shift Tab cycle inside the modal, closes on Escape, and restores focus to the previously focused element. `canvas-tooltip` now shows on focus as well as hover, links the trigger via `aria-describedby`, and disconnects its `MutationObserver` on `disconnectedCallback` to fix the stacking listener leak. `canvas-modal-content` and `canvas-modal-footer` carry an accessible name on the scroll region and footer group respectively.
- Session 3 table, tabs, and accordion synthesize native semantics. `canvas-table` wraps every row group, row, and cell in a wrapper carrying `role="rowgroup"`, `role="row"`, `role="columnheader"`, or `role="cell"`. The wrappers use `display: contents` so the existing visual layout, padding, and row state colors keep rendering through. Sortable headers expose `aria-sort` of `ascending`, `descending`, or `none`. `canvas-tabs` carries `role="tablist"` with arrow key roving tabindex, Home and End jumps, `aria-controls` from each tab to its panel, and `aria-labelledby` from each panel back to its tab. `canvas-accordion-item` replaces the `div role="button"` trigger with a native `<button>`, the button toggles `aria-expanded` and points `aria-controls` at the content id. `canvas-accordion-content` ties its `role="region"` to the trigger via `aria-labelledby`. `canvas-accordion` accepts an optional `aria-label` that mirrors onto the group container.
- Session 4 status surfaces close out color only state issues and reduced motion gaps. `canvas-banner` splits role by variant, `info` and `success` render `role="status"`, `error` and `warning` render `role="alert"`. The dismiss button carries `aria-controls` pointing at the banner header id and an `aria-label` that names what it dismisses. `canvas-badge` renders a visually hidden severity word inside the badge so screen readers announce `Active` or `Denied` rather than relying on the colored swatch alone. `canvas-chip` ships a dismiss `aria-label` that names the chip such as `Remove Cardiology`, the chip becomes focusable when actionable, and the Delete and Backspace keys fire the dismiss event. `canvas-loader` wires `aria-live="polite"`, `aria-busy="true"`, and gates the spinning arc animation under `reduceMotion` so the spinner becomes a static affordance for users who request reduced motion. `canvas-progress` carries `role="progressbar"`, `aria-valuemin="0"`, `aria-valuemax="100"`, and emits `aria-valuenow` only when the value is determinate. `canvas-sortable-item` and `canvas-sortable-list` carry an `aria-label` on the drag handle that names the item and enforce a list label via `aria-label` or `aria-labelledby`. `canvas-button` adopts `AriaProxy` so `aria-label`, `aria-pressed`, `aria-expanded`, `aria-controls`, and `aria-disabled` mirror onto the inner `<button>`. Focusable disabled buttons use `aria-disabled` rather than the native `disabled` attribute so screen readers can still announce the disabled affordance. `canvas-scroll-area` carries `role="region"` and `tabindex="0"` when `vertical` or `horizontal` is set and requires `aria-label` or `aria-labelledby`. `canvas-sidebar` defaults to `role="complementary"` and `canvas-content` defaults to `role="main"`, both accept an optional `aria-label` for the multi region case.
- `references/interaction-patterns.md` gains an Accessibility Helpers section that documents `cuid`, `reduceMotion`, `trapFocus`, `AriaProxy`, `SR_STATUS_CSS`, and `PREFERS_REDUCED_MOTION_CSS` as central, reusable primitives. Each helper is paired with the canvas component pattern that consumes it so future component work cites the primitives rather than reinventing them.
- `references/web-components.md` updates the per family Keyboard and ARIA notes for every component touched in Sessions 1 through 4. Each section now documents the AriaProxy mirror set, the `cuid` id pattern, the activedescendant or roving tabindex contract, the focus trap and inert background pattern on `canvas-modal`, the aria-labelledby API on `canvas-popover`, the role split by variant on `canvas-banner`, the screen reader severity text on `canvas-badge`, and the named dismiss label on `canvas-chip`.

## 4.24.0

### Added

- `canvas-calendar` gains a visually hidden `role="status" aria-live="polite"` region that announces state changes to screen reader users. Month changes (navigation buttons, PageUp / PageDown, arrow keys crossing a month boundary) announce the new month and year. Single selection announces the full selected date. Range selection announces "Start date <date> selected. Pick an end date." after the first click and "Range <start> to <end> selected." after the second. Multi-select announces "Added <date>. N dates selected." or "Removed <date>. N dates selected." Granular adds announce the unit ("Added week of <date>." or "Added work week of <date>."). Picked list clear announces "All dates cleared."
- `canvas-calendar` cells carry full date `aria-label` of the form `"Wednesday, June 15, 2026"` followed in order by `, today`, range role (`, start of range` / `, end of range` / `, in range`), `, selected`, `, unavailable`. Replaces the previous behavior where the day number was the only accessible name, leaving screen reader users without weekday or month context.
- `canvas-calendar` day-name `role="columnheader"` cells gain an `aria-label` with the full weekday name (`Sunday`, `Monday`, etc) so screen readers no longer pronounce the visible two-letter abbreviation.
- `canvas-calendar` body grid renders six `role="row"` wrappers around the seven cells of each week, satisfying the ARIA grid contract. Rows use `display: contents` so the existing CSS grid layout and tokens (`--canvas-calendar-cell-size`, `--canvas-calendar-cell-gap`) keep driving visuals.
- `canvas-calendar` exposes a `focusGrid()` public method that moves focus into the active cell. Intended for host components that wrap the calendar in a popover (e.g. `canvas-date-input`) so panel open can transfer focus into the grid without reaching across shadow boundaries by hand.
- `canvas-calendar` today cells render a 4px dot below the day number in the today token color so today is identifiable without relying on a hairline border alone, which cannot meet 3:1 non-text contrast at 1px width.
- `canvas-calendar` shadow CSS adds a `@media (prefers-reduced-motion: reduce)` block that removes cell, nav button, picked-row, and picked-remove transitions for users who request reduced motion.
- `canvas-calendar` cell decoration spans (rendered via the `dayContent` function) carry `aria-hidden="true"` by default so screen readers no longer concatenate the day number with the decoration text. Consumers can opt out by returning an Element with `data-aria="expose"` set, in which case the calendar omits `aria-hidden` and the consumer takes responsibility for accessible context.
- `canvas-calendar` picked list remove button announces the full date including weekday and year (`Remove Wednesday, June 15, 2026`) regardless of whether the visible label abbreviates them.

### Changed

- `canvas-calendar` grid `aria-label` is now `"Calendar, <Month> <Year>"` instead of just `<Month> <Year>` so the grid is named as a calendar to screen readers.
- `canvas-calendar` body grid container no longer carries `tabindex="0"`. The roving tabindex on the active cell is the single Tab stop, eliminating a confusing double Tab stop where focus first landed on the grid container with no visible focus ring before reaching the active cell.
- `canvas-calendar` month label no longer carries `role="heading" aria-level="2"`. The new live region covers the screen reader announcement need without polluting the document outline of forms or pages that host the calendar.
- `canvas-calendar` disabled cells now stay reachable through arrow key navigation. Focus is preserved at `min` and `max` boundaries instead of falling back silently to a different cell. Enter and Space silently no-op on disabled cells, click is still suppressed by `pointer-events: none`. Disabled cells continue to expose `aria-disabled="true"`.
- `canvas-calendar` today-selected cells use a near-black green foreground (`#0A2A12` token default) instead of white to pass WCAG 1.4.3 contrast minimum (4.5:1) against the green background, and add an outer ring in the today color to reinforce today identity. Previous white on green failed at 2.95:1.
- `canvas-calendar` outside-month cell text alpha raised from 0.3 to 0.45 in the `--canvas-calendar-outside-month-color` token default so the text passes WCAG 1.4.3 (4.6:1 on white) instead of failing at 2.43:1.
- `references/web-components.md` `canvas-calendar` section rewrites Keyboard and ARIA subsections and adds Live region, Today indicator, Reduced motion, Public API, and `dayContent` accessibility subsections that document the new contracts.

## 4.23.0

### Added

- `references/web-components.md` documents `canvas-date-input` and `canvas-calendar` as full sections under Components. Both components shipped in earlier releases (canvas-calendar in 4.20.0, canvas-date-input in 4.21.0) without entries in this file. Each new section covers usage, attributes, properties, events, form participation, keyboard, ARIA, and the file pointer, matching the depth of every other component section. The header count is updated from 28 components / 47 tag names to 30 components / 49 tag names. The Components table of contents adds links for both.
- `references/component-usage.md` adds a `Date Inputs` decision section right after `Text Inputs vs Textareas`. Three way pick. `canvas-date-input` for single date entries inside a form (default for clinical date fields), `canvas-input type="date"` for date range pairs in filter bars and for the temporal types `canvas-date-input` does not cover (time, datetime-local, month, week), and `canvas-calendar` directly when the calendar is the focal interaction. Cross references DESIGN.md for the `MMM D, YYYY` display format rule.

### Changed

- `references/component-usage.md` Text Inputs vs Textareas native input prohibition now names `canvas-date-input` as the replacement for single date fields and limits `canvas-input` to non date temporal types and the other input types.
- `references/component-usage.md` Inline Form Rows date guidance now distinguishes the filter bar date range case (keep `canvas-input type="date"`) from the single date in form case (use `canvas-date-input`), with a pointer to the new Date Inputs section.
- `references/anti-patterns.md` Native Input Use Fix line now lists `canvas-date-input` as the first replacement for single date fields and `canvas-input` for everything else, with a pointer to component-usage.md Date Inputs.
- `references/patterns.md` Filter Bar narrative explains why the template stays on `canvas-input type="date"` for date ranges and notes that single date entries inside content forms use `canvas-date-input`.
- `README.md` component set sentence adds `date-input` and `calendar` to the inline list.

## 4.22.0

### Added

- `canvas-dropdown`, `canvas-combobox`, and `canvas-multi-select` gain a loading contract for the case where options are fetched on first open or mid session. New `loading` boolean attribute and new `loading-label` string attribute (default `Loading options`). While `loading` is set the trigger swaps the value, the input row, or the chip row plus input row for an inline spinner and the loading label, the cursor goes to `progress`, `aria-busy="true"` is set on the trigger, and the panel will not open. A click on the trigger queues an internal pending open, a second click toggles it off. When `loading` flips to false the component re-reads `<canvas-option>` light DOM children, re-renders, and opens the panel only if a click was queued. Setting `loading` to true while the panel is already open captures the queued open, so the click then fetch flow opens automatically when data lands. The component dispatches a `loading-cancel` event (bubbles and composes through shadow DOM) when the user disengages while a click was queued, with `event.detail.reason` of `outside`, `escape`, `blur`, or `toggle`. Blur is deferred by a microtask so an outside click reports `outside` rather than being preempted by `blur`, tab away still reports `blur`. The component does not abort fetches itself, the consumer listens for the event and aborts its own request.
- `examples/showcase.html` adds a Loading state (dynamic options) sample card under the Dropdown, Combobox, and Multi-Select sections. Each card has one shared `canvas-input` for fetch duration in milliseconds plus two component instances side by side. The left instance ignores `loading-cancel` so the simulated request keeps running, the right instance listens for `loading-cancel` and clears the timeout, mimicking `AbortController.abort`, then resets the loading attribute. Clicking the component itself triggers the fetch, no separate buttons.

### Changed

- `references/web-components.md` documents the loading contract on `canvas-dropdown` with a full Loading state subsection plus the new `loading` and `loading-label` rows in Attributes and the new `loading-cancel` row in Events. `canvas-combobox` and `canvas-multi-select` get the same table additions and short Loading state pointers back to `canvas-dropdown`. The combobox pointer notes that the editable input row is replaced with the spinner row so filtering as the user types is suppressed during loading. The multi-select pointer notes that selected chips remain visible inside the trigger while only the input row swaps for the spinner row.
- `references/component-usage.md` Loading States adds a bullet directing authors to set `loading` on `canvas-dropdown`, `canvas-combobox`, and `canvas-multi-select` whose options are fetched on first open or mid session, and to listen for `loading-cancel` to abort the in flight request.
- `references/anti-patterns.md` broadens the existing Open Trigger Without Panel Content entry with a second detection signal and matching fix. The entry now covers both hand rolled clones that hide the panel when results are zero and real components mounted with zero `<canvas-option>` children whose options are populated by a fetch with no `loading` attribute toggled around the call.
- `references/validation-checklist.md` Phase 2 Dropdowns and Comboboxes adds a binary check for the loading attribute when options are fetched on first open or mid session.

## 4.21.3

### Fixed

- `canvas-combobox`, `canvas-dropdown`, `canvas-multi-select`, `canvas-menu-button`, and the `canvas-calendar` picked-list now use `overscroll-behavior: none` on their internal scroll containers. Pre 4.21.3 the combobox and multi-select used `overscroll-behavior: contain`, which only blocks scroll chaining to the parent. The container itself still rubber-banded on macOS trackpad scroll, so when the list reached the bottom and the user kept scrolling the items translated up and a gap appeared between the last item and the menu's bottom border. Since the elastic bounce on macOS effectively translates the scroll-clip layer, that gap revealed page content sitting below the menu in z-index. The dropdown and menu-button menus had no overscroll rule at all and chained scroll into the page on top of the same bounce. Switching to `none` blocks both scroll chaining and the elastic bounce affordance, so the menu items stay welded to the container bounds and no page content is ever visible behind the open menu.

## 4.21.2

### Fixed

- `canvas-date-input` inner `canvas-calendar` is now capped at `max-width: 255px` inside the welded panel. With the calendar fluid the inner cells could scale up past picker proportions when the trigger input was wide. Capping the calendar at 255px keeps day cells, hover ring, and selection pill at consistent size while the panel still tracks the trigger width below that cap and pads the right side of the calendar when the trigger is wider. The panel keeps the welded combobox style from 4.21.1, no popover detachment.

## 4.21.1

### Fixed

- `canvas-date-input` no longer flattens the day cell, today outline, and selected day corners inside the open panel. Pre 4.21.1 the panel CSS set `--canvas-calendar-radius: 0` on the inner calendar to flatten the calendar's outer rounded container so it would not fight the panel's corners. That same token also drives the cell `border-radius` and the nav button `border-radius`, so zeroing it incorrectly squared off today's green outline and the selected day's blue pill. From 4.21.1 the override is removed. The outer calendar container does not need radius zeroing because the calendar's own outer border is already suppressed via `--canvas-calendar-border-width: 0` and the calendar background matches the panel background, so no visible outer corner exists. The selected day, today outline, and nav buttons now render with the standard 4px radius.
- `canvas-date-input` panel sizing now matches `canvas-combobox` and `canvas-dropdown` verbatim. Pre 4.21.1 the host `.field` was `display: inline-block` with no width, the input had no explicit width, and the panel was positioned with only `left: 0`, so the panel collapsed to the calendar's intrinsic width while the input collapsed to the user agent default and neither tracked the other. The result was a panel that under hung the input on the right and a panel top divider whose corners did not blend cleanly into the blue active border. From 4.21.1 the host is `display: block`, `.field` is `position: relative; width: 100%`, the input is `width: 100%`, and the panel uses `top: calc(100% - 1px); left: 0; right: 0` with `border-top: none` so the input's transparent open bottom border seams directly into the panel's left and right blue borders. The flip variant mirrors the pattern with `bottom: calc(100% - 1px)` and `border-bottom: none`. The dedicated gray top divider is removed, the visual separation between the input row and the calendar grid is now produced the same way `canvas-combobox` produces it, by the open input's transparent edge.

### Changed

- `canvas-date-input` inner `canvas-calendar` is now rendered with the `fluid` attribute. Pre 4.21.1 the inner calendar rendered at its intrinsic size (seven 32px cells plus padding), forcing the panel to that width regardless of the trigger width. From 4.21.1 the inner calendar's grid is `repeat(7, 1fr)` and cells are `aspect-ratio: 1`, so the calendar fills the panel width that the input width dictates. Cells, day name row, and nav buttons scale proportionally with the input width. The previous `--canvas-calendar-cell-size` override is no longer needed because fluid mode does not read that token, the panel width is now determined by the trigger.

## 4.21.0

### Added

- `canvas-date-input` is a new component that wraps `canvas-calendar` in a combobox style floating panel. The closed state is a read only text input styled identically to `canvas-dropdown` and `canvas-combobox`, with the same border, padding, focus ring, and caret arrow. The open state expands into a panel that shares the blue active border on the left, right, and bottom, with a thin gray divider as the top edge between the input row and the calendar grid. The calendar inside is full chrome `canvas-calendar` with its own border, gray header, and outer radius suppressed via CSS custom properties so the panel border is the only visible chrome. The component flips upward when there is no room below the input, mirroring `canvas-combobox`. Form associated, the form value is the ISO date string. Forwards `min`, `max`, `disabled-dates`, `week-start`, `size` to the inner calendar. Supports `label`, `placeholder`, `error`, `disabled`, `required`, `name`. Display format is `MMM D, YYYY` (e.g. May 4, 2026). Pattern for any single date entry that needs to feel native alongside other Canvas inputs in the same form row.
- `examples/showcase.html` adds a Date input dropdown sample under the calendar section with three side by side fields, default value, empty placeholder, and bounded min and max with `week-start="monday"`.

## 4.20.0

### Added

- `canvas-calendar` adds the `multi-add-exclusive` boolean attribute on top of `selection-mode="multiple"` and `multi-add-granularity`. When set, the click set replaces the current selection rather than merging with it. Clicking any day in a fully selected set clears the selection. Combined with `multi-add-granularity="workweek"` or `"week"` this produces single workweek or single week selection where switching weeks deselects the prior week and selects the new one. Pattern for shift assignment where exactly one workweek is current, weekly schedule pickers, and reporting filters that scope to a single week.

### Changed

- `examples/showcase.html` consolidates the four prior multi selection samples into two grouped cards, each demonstrating the optional `picked-list` variants in one place. Sample 11 now shows three layouts of `selection-mode="multiple"` side by side, default (no list), `picked-list="right"`, and `picked-list="below"`. Sample 12 shows three granularity variants side by side, plain workweek, week with picked list right, and exclusive workweek with picked list below. Easier to scan the calendar surface options when grouped, and clearer that the picked list is a layout choice independent of selection behavior.

## 4.19.0

### Added

- `canvas-calendar` adds the `multi-add-granularity` attribute to the multi selection mode. Default value `day` keeps existing behavior, one click toggles one date. Value `workweek` expands one click to the Monday through Friday of that week. Value `week` expands one click to all seven days of that week, respecting the `week-start` attribute so the expansion starts on the same weekday as the day-name row. Set toggle semantics, click on any day in a fully selected set removes the set, click on any day in a partially selected or empty set adds every day not yet selected. Disabled dates inside the expanded set are skipped without aborting the rest, so a workweek with one disabled holiday still adds the other four days. The `change` event detail now includes a `granularity` field when the value last changed via a granularity click. Pattern for shift planning, weekly availability blocks, and recurring clinical protocols where the host should not have to compute week boundaries from a single date.
- `examples/showcase.html` adds two calendar samples. Sample 13 demonstrates `multi-add-granularity="workweek"` with `picked-list="right"`. Sample 14 demonstrates `multi-add-granularity="week"` with `week-start="monday"` and `picked-list="below"`.

## 4.18.2

### Fixed

- `canvas-calendar` picked-list rows now extend full bleed inside the row scroll viewport. Pre 4.18.2 each `.picked-row` carried `border-radius: var(--canvas-calendar-radius)` and the `.picked-rows` scroll container carried left and bottom padding, so the row hover and selected highlight stopped short of the picked-list right edge and rendered as a rounded pill. From 4.18.2 the row has no border-radius and the rows container has no padding, so the hover and selected highlight reaches every edge of the row band, matching how rows render in Canvas list surfaces. The below variant default for `--canvas-calendar-picked-list-max-height-below` adjusts from `9.21428572rem` to `8.92857143rem` to preserve the four full rows plus half of the fifth row signal now that the rows container contributes no top padding to the viewport.

## 4.18.1

### Fixed

- `canvas-calendar` picked-list now isolates scroll to the row list only. Pre 4.18.1 the whole `.picked-list` was the scroll container, so the count and Clear all header scrolled away with the rows and rubber-band overscroll on macOS displaced the entire surface, including the calendar grid in the below variant. From 4.18.1 `.picked-list` is a flex column with no overflow, the header is a static `flex: 0 0 auto` row at the top, and a new `.picked-rows` child carries `overflow-y: auto` and `overscroll-behavior: contain`. The header and the calendar above it now stay set in stone during scroll. The variable `--canvas-calendar-picked-list-max-height-below` now applies to `.picked-rows` and its default is `9.21428572rem`, sized so the below variant displays exactly four full row heights plus the top half of the fifth row (signals there is more to scroll).
- `canvas-calendar` nav buttons now sit at equal distance from the calendar top and right edges. Pre 4.18.1 the `.nav` row had `2px` top padding and `6px` bottom padding, while `.header` had zero vertical padding, so the prev and next buttons sat 2px from the top while the right edge was offset by the header's horizontal padding. From 4.18.1 `.nav` has zero padding on all four sides and `.header` carries `var(--canvas-calendar-padding)` on the top and the sides (with zero on the bottom), giving identical insets at the top and the right. A new `.day-names` rule sets `margin-top: var(--canvas-calendar-padding)` so the day-name row keeps a clear gap from the nav buttons now that the nav itself has no padding.

## 4.18.0

### Changed

- `references/component-usage.md` Feedback and Status now states the banner discipline directly. Banners are reserved for unexpected outcomes, errors, warnings, and risk surfaces. Expected outcomes (successful save, confirm, create) communicate via UI state change, modal close, form reset, row append, badge flip. The pre 4.18.0 line that asked for a `variant="success"` banner after every save contradicted the Banner Variant Guide below it and is removed.

### Added

- `references/writing-style.md` adds a Banner copy voice section with two rules. No protocol noise (HTTP status codes, exception class names, raw backend field identifiers, null and undefined tokens) in banner text. Name the entity in plain language using the value the user supplied, wrapped in `<b>` so the eye lands on the term. Five paired avoid and prefer examples.
- `references/anti-patterns.md` adds two entries. Banner For Expected Success (detection, why, fix, rule home, validation check) and Technical Error Code in Banner Copy (same shape).
- `references/validation-checklist.md` Phase 3 Writing Style adds checks 13 and 14, banner reserved for the unexpected and banner copy in human voice with no protocol noise.
- `evals/evals.json` adds eval id 18 covering a coverage lookup form. Failure paths render an error banner that names the user supplied member ID wrapped in `<b>` and contains no status code, exception class name, backend field identifier, or null token. Success path renders no banner because the form reset and the new row are the confirmation.

## 4.17.0

### Fixed

- `canvas-tab-panel` no longer clips descendant focus rings, box shadows, or popover surfaces against its inner edge. The panel previously rendered a `.panel-inner` wrapper with `overflow: auto`, which made the wrapper a scroll container and clipped any descendant ink that paints outside its content box. A `canvas-button` flush against the panel edge had its 2px focus ring with 2px outset sliced off on every keyboard focus. The wrapper is removed, the slot now sits directly under the host, and overflow defaults to visible.

### Changed

- `canvas-tab-panel` is no longer a scroll container. Pre 4.17.0 the panel silently scrolled when its content exceeded its box. From 4.17.0 the panel content flows naturally and is allowed to paint outside the panel. When a panel needs to scroll, wrap its content in `canvas-scroll-area vertical` with an explicit `max-height` and `aria-label`, the same migration pattern applied to `canvas-card-body` in 4.0.0.
- `references/web-components.md` canvas-tabs section now documents the panel overflow contract and points to canvas-scroll-area for the scrolling-panel pattern.
- `references/component-usage.md` Scroll Areas adds the canvas-tab-panel migration bullet alongside the canvas-card-body bullet.
- `references/anti-patterns.md` adds Tab Panel Reliance on Implicit Scroll covering detection, why, and the canvas-scroll-area fix.
- `references/validation-checklist.md` Tabs section adds a binary check for raw `overflow: auto` on a panel or on a div inside a panel.
- `examples/showcase.html` Tabs section adds a Scrollable content sample showing the opt-in scroll pattern for `canvas-tab-panel`. A long encounter list is wrapped in `canvas-scroll-area vertical` with an explicit `max-height` and `aria-label` so the content stays bounded while the panel itself flows naturally.
- `examples/showcase.html` Accordion section adds a parallel Scrollable content sample showing the same pattern applied inside `canvas-accordion-content`.

### Migration

- Plugin authors with tab panels whose content fits inside the panel. No action required.
- Plugin authors with tab panels whose content was overflowing and silently scrolling. Wrap the panel content in `<canvas-scroll-area vertical aria-label="..." style="max-height: ...">` to restore scrolling. Content will visibly overflow the panel box on first reload otherwise.

## 4.16.2

### Fixed

- `canvas-dropdown`, `canvas-combobox`, and `canvas-multi-select` menu options no longer overflow the menu horizontally when the trigger parent is narrower than the option text. The `.option` rule in all three shadow DOMs now sets `white-space: nowrap`, `overflow: hidden`, and `text-overflow: ellipsis`, matching the truncation behavior the trigger already applies to the selected label. Each option li also carries a native `title` attribute equal to the option label, so hovering a truncated option reveals the full text via the browser's default tooltip on desktop. No new API surface, no new attribute, pure visual upgrade that plugins pick up on the next asset load.

### Changed

- Added a "Narrow container, option text truncates" sample to `examples/showcase.html` under Dropdown (narrow sort picker, provider dropdown) and a matching sample under Combobox (narrow medication search, provider search). Each sample frames the behavior as a layout signal, the author should widen the container when the ellipsis appears, the component does not attempt to resize itself.

## 4.16.1

### Changed

- Extended the Global CSS Reset Detection guidance in `references/setup.md` and the matching anti-pattern in `references/anti-patterns.md` to call out `body { -webkit-font-smoothing: antialiased }` as a frequent bare body offender. The property switches Chrome and Safari from subpixel to grayscale rendering and visibly thins Lato 700 strokes, so plugin text looked lighter than the Canvas home app. No new rule home, no new validation check, the existing Phase 0 "No global CSS reset" continues to cover it.

## 4.16.0

### Added

- "Modal With Duplicate Dismiss Paths" entry in `references/anti-patterns.md`. Detects modals that render both `dismissable` on `canvas-modal-header` and a Cancel, Close, or Dismiss button in `canvas-modal-footer`. The two paths are redundant and force the user to choose between equivalent controls.
- Modals section in `references/validation-checklist.md` Phase 2 with a binary check for the duplicate dismiss path.

### Changed

- `references/component-usage.md` Modal Patterns Header dismiss button guidance now states the prohibition explicitly. Previously the line said the X was "not needed" when Cancel and Confirm were present, which read as a soft suggestion. The updated wording instructs to pick one dismiss path and points to the new anti-pattern and validation check.

## 4.15.0

### Added

- `empty-state` attribute on `canvas-dropdown`, `canvas-combobox`, and `canvas-multi-select`. Overrides the default empty copy with plain text. Default values are "No options" for `canvas-dropdown` and "No results" for the two filtered components.
- `slot="empty"` on the same three components. Consumers can project rich HTML (headings, links, inline buttons) as the empty state body. When both `empty-state` and a slotted child are present, the attribute wins.
- Empty state sections in `references/web-components.md` for all three components, covering the override paths and the default copy.
- "Open Trigger Without Panel Content" entry in `references/anti-patterns.md` documenting the visual state versus panel state desync that the three components now prevent by contract.
- Phase 2 validation checks for empty-state override coverage and attribute vs slot conflict.
- "Menu components" subsection in `references/component-usage.md` Empty States, pointing to the component-level behavior and its anti-pattern.
- Component sample at `{project-root}/../.artifacts/sources/plugins/canvas-plugin-ui/component-samples/menu-empty-states.html` demonstrating default, attribute, and slot override for each of the three components.

### Fixed

- `canvas-combobox` rendering an open trigger above an empty menu when opened with zero `<canvas-option>` children. The open visual state now always pairs with visible panel content.
- `canvas-dropdown` had no empty state at all. Opening it with zero options produced an empty menu rectangle with no copy. Now shows the empty row with override paths.

### Changed

- `canvas-combobox` `_showAll` no longer touches the empty row. Empty row visibility is computed by a new `_checkEmpty` method that `_openMenu` and `_filter` both call. Single source of truth for the empty state, no desync possible.

## 4.14.0

### Added

- `references/setup.md`. New home for plugin HTML boilerplate, the three head tags, SimpleAPI routes with `StaffSessionAuthMixin`, Content Security Policy requirements, the static file prerequisite check, global CSS reset detection, and the `CanvasUI.utils` host communication bridge. Extracted from `web-components.md` Loading Components section and `SKILL.md` Design System Prerequisite.
- `references/refactor-safety.md`. New home for the four-part JavaScript dependency scan protocol (dependency scan, risk classification, migration declarations, risk summary). Extracted verbatim from `workflow.md` Refactor Safety section.
- `references/patterns.md`. New home for copy-paste multi-component templates. Covers the four typed empty state variants (first use, user cleared, filter no results, load error), the patient context header markup, the filter bar markup (card + inline-row + optional footer), the sortable list minimum height token usage, and the loading/empty/error state machine. Extracted from `DESIGN.md` Patterns Without Components and `component-usage.md` markup examples.
- `references/anti-patterns.md`. New home for common mistakes with consistent shape (name, detection, why, fix, rule home, validation check). Covers card imitations, native input and details use, mixed size tier rows, missed inline row and scroll area swaps, silent card body overflow, forbidden popup nesting, action menu built as a dropdown, anchored surface built as a modal, empty state during loading, filter without escape, generic empty copy, AI puffery, and global CSS reset override. Extracted and reorganized from `workflow.md` Common Mistakes.

### Changed

- Restructured the skill so each reference file answers exactly one question. Rule ownership map documented in `CLAUDE.md`. Every rule now lives in exactly one file with other files using one-line pointers. Generated output is unchanged, only the routing between reference files is reorganized.
- `SKILL.md`. Removed "Key Rules to Never Forget" block (rules restated content that lives in the reference files). Replaced with a three-link pointer to `component-usage.md`, `interaction-patterns.md`, and `anti-patterns.md`. Kept the escalation ladder and customization boundaries since they are unique to `SKILL.md`. The reference file table now names the one question each file answers.
- `DESIGN.md`. Narrowed to visual language only. Removed Menu Button Visual Spec and Popover Visual Spec (moved to `web-components.md` canvas-menu-button and canvas-popover sections). Removed Patterns Without Components (moved to `patterns.md`).
- `references/web-components.md`. Absorbed the Menu Button visual spec and Popover visual spec from `DESIGN.md` into the respective component sections. Added keyboard and ARIA detail to canvas-tabs, canvas-dropdown, canvas-combobox, canvas-menu-button, canvas-popover, and canvas-sortable-list. Removed the full Loading Components section (moved to `setup.md`) and replaced with a pointer. Stated the authoritative component count (28 components, 47 tag names) in the header, other files point here.
- `references/workflow.md`. Added a Step 0 Verify Setup row pointing at `setup.md`. Trimmed Refactor Safety (now in `refactor-safety.md`) and Common Mistakes (now in `anti-patterns.md`) to pointer lines. Step 4 now also loads `patterns.md` for multi-component templates.
- `references/interaction-patterns.md`. Narrowed to cross-cutting interaction rules only. Removed Tab, Combobox, Menu Button, Popover, and Sortable List per-component sections (those details now live with each component in `web-components.md`). Kept focus management, toggle and submit prohibition, ARIA essentials table, scrollable containers, form submission, touch targets, and patient context safety.
- `references/component-usage.md`. Narrowed to decision rules only. The minimal filter bar example moved to `patterns.md` Filter Bar. The Loading, empty, error state machine moved to `patterns.md`. Header paragraph updated to name the new file split.
- `references/validation-checklist.md`. Converted to binary form. Every check now has a pass or fail condition and a one-line pointer to its rule home, no inline rule restatement. Writing Style check block reduced from narrative to a numbered list. Cross references added to `anti-patterns.md` entries where a check has a named anti-pattern.
- `README.md`. Trimmed the three-tag loading description (duplicated in `setup.md`) and the reference file table (duplicated in `SKILL.md`). Kept the good-prompt examples and the iterating guidance which are unique to `README.md`.
- `CLAUDE.md`. File Consistency Matrix rewritten to include rows for `setup.md`, `refactor-safety.md`, `patterns.md`, and `anti-patterns.md`. Added a Rule Ownership table naming which file owns which rule type.

### Migration

- Plugin authors. No action required. Generated output is unchanged, the same rules apply, only the location of the rules inside the skill changed.
- Skill maintainers. When adding a new component, follow the updated matrix in `CLAUDE.md`. The component section in `web-components.md` now carries keyboard, ARIA, and visual spec details, not just API. The `component-usage.md` entry carries decision rules only. Common mistakes go in `anti-patterns.md`, not in `workflow.md`.

## 4.13.0

### Added

- `references/writing-style.md` with rules for every user facing string the skill generates. Banned punctuation (em dash, en dash, curly quotes, smart apostrophes), sentence case headings, banned assistant tone and didactic disclaimers, vocabulary to avoid (puffery clusters, inflation of significance, weasel wording, participle commentary, promotional stems), structural patterns to avoid (negative parallelism, rule of three padding, elegant variation, exhaustive tooltips, section summaries), and a clinical vocabulary carve out table covering vital, critical, significant, active, chronic, acute, pivotal, present, presenting, underlying, and key. Canvas domain terms (encounter, problem list, chief complaint, medication, allergy, prescription) listed as always safe.
- Writing Style check block in `references/validation-checklist.md` Phase 3. Twelve checks covering punctuation, case, disclaimers, assistant tone, knowledge cutoff phrases, emoji, puffery, inflation of significance, weasel wording, negative parallelism, and the clinical carve out lookup.
- Cross link from `references/component-usage.md` Empty States Voice subsection to `references/writing-style.md` for prose beyond empty states.
- Routing reference to `references/writing-style.md` in `references/workflow.md` step 4 (Build or refactor HTML) so copy rules load alongside component selection. Common Mistakes bullet for AI puffery in generated strings points at the clinical carve out.
- Key Rule in `SKILL.md` naming `references/writing-style.md` and summarizing the banned patterns plus the clinical carve out principle.

## 4.12.0

### Removed

- `persistent` attribute on `canvas-popover`. The attribute claimed to block dismissal by outside click and Escape, but the surrounding page stayed interactive so users could still walk away from a "blocking" popover by clicking any non trigger control, opening another popover, or focusing another input. The modal feeling was never real. Content that truly needs commitment belongs in `canvas-modal`, which has a backdrop and a focus trap and actually blocks the user.
- `trap-focus` attribute on `canvas-popover`. Same reasoning. Cycling Tab inside a surface that the user can click out of freely is inconsistent. Focus trap belongs to `canvas-modal`.
- Persistent confirmation micro dialog demo in `examples/showcase.html` and the matching section in the `canvas-popover` component sample. Destructive confirmations should use `canvas-modal`.

### Changed

- Popover is now documented as non modal by contract. Outside click and Escape always dismiss, Tab escapes to the next document tab stop. Reference docs, validation checks, and the overlay family decision rule updated to point confirmations and blocking flows at `canvas-modal`.

### Migration

- Any plugin using `<canvas-popover persistent>` or `<canvas-popover trap-focus>` should replace the popover with a `canvas-modal`. The body content transfers largely unchanged, the trigger becomes a button whose click handler calls `modal.open()`.

## 4.11.0

### Added

- `pointer` boolean attribute on `canvas-popover`. Renders a 14 px speech balloon arrow on the side of the surface that faces the trigger, matching the `canvas-tooltip` artwork. The arrow tracks the trigger center even when the surface clamps against a viewport edge, and flips side with the surface under auto placement. Use for icon only triggers, inline contextual disclosures, and small surfaces that float free of their trigger where the anchor would otherwise be ambiguous. Pointer does not change keyboard, ARIA, or dismissal behavior, it is a visual affordance only. When `pointer` is set the component adopts the tooltip distance recipe (10 px gap, 8 px viewport margin), otherwise the tighter popover recipe (6 px gap, 4 px viewport margin) stays in effect.
- `size="auto"` option on `canvas-popover`. Caps at `calc(100vw - 16px)` and lets the surface grow to its content width for wide tables, long labels, or content whose width is known only at runtime. Existing `sm` 280 px, `md` 360 px, `lg` 480 px defaults are unchanged.
- Overlay family decision table in `references/component-usage.md` mapping trigger and content shape to `canvas-tooltip`, `canvas-popover` without `pointer`, `canvas-popover` with `pointer`, `canvas-menu-button`, and `canvas-modal`. Replaces the scattered cross references between the tooltip and popover sections.
- Pointer subsection in `references/component-usage.md` Popover section with when to set and when to skip rules. Content sizing and escalation subsection caps the popover body at one logical group with up to four focused controls and names the escalation to `canvas-modal` when the task outgrows the popover.
- Icon only pointer filter form example in `references/web-components.md` showing the canonical filter trigger plus form pattern on `canvas-popover` with `pointer`.
- Shared anchored callout constants `ANCHOR_GAP` 10, `ANCHOR_EDGE` 8, `ANCHOR_ARROW_SIZE` 14, `ANCHOR_ARROW_DEPTH` 7, `ANCHOR_ARROW_HALF` 7, `ANCHOR_ARROW_CORNER_INSET` 6 hoisted to module scope in `canvas-plugin-ui.js`. `canvas-tooltip._calcPosition` now reads these constants instead of inline literals. `canvas-popover` pointer math consumes the same constants so tooltip and pointer popover distance and arrow geometry stay locked together.
- Pointer affordance, pointer at viewport edge, pointer with auto flip, and size auto demos in the `canvas-popover` component sample.

### Changed

- Border gray alignment across four components. Container chrome now uses `#d4d4d5` across the board. Form indicators use `rgba(34, 36, 38, 0.15)` resting, `rgba(34, 36, 38, 0.35)` hover.
- `canvas-popover .surface` no longer sets `overflow-y: auto`. The surface is not an internal scroll container. When content may exceed the direction aware `max-height`, wrap the body in `canvas-scroll-area vertical`. Same contract as `canvas-card-body`. Removes the ancestor overflow clip that was cutting off `canvas-dropdown` and `canvas-combobox` menus rendered inside a popover.
  - `canvas-card .card` outer border from `rgba(34, 36, 38, 0.15)` to `#d4d4d5`.
  - `canvas-popover .surface` border from `rgba(34, 36, 38, 0.15)` to `#d4d4d5`. Applies to both pointerless and pointer popovers so the surface edge matches `canvas-tooltip`.
  - `canvas-checkbox .box` resting border from `#d4d4d5` to `rgba(34, 36, 38, 0.15)`. Hover, checked, and focus borders unchanged.
  - `canvas-radio .dot` resting border from `#d4d4d5` to `rgba(34, 36, 38, 0.15)`. Hover, checked, and focus borders unchanged.

## 4.10.0

### Added

- New component `canvas-popover` for click triggered anchored content containers. Covers filter forms, column pickers, legends, preference sheets, bulk action panels, and confirmation micro dialogs. Uses `role="dialog"` with `aria-modal="false"`, trigger carries `aria-haspopup="dialog"` and `aria-expanded`. Not form associated. Component count in `SKILL.md` goes from 26 to 27.
- Slotted trigger via `slot="trigger"`. Default slot carries arbitrary HTML content. No composite sub elements in v1, authors wire their own header or action row inside the body.
- Attributes. `open` boolean reflected, `label` string required for `aria-label` on the dialog surface, `size` `sm` 280 px, `md` 360 px, or `lg` 480 px, `align` `start` or `end` with auto flip, `direction` `down` or `up` with content aware auto flip, `persistent` disables outside click and Escape dismissal, `trap-focus` cycles focus within the body, `dismiss-on-scroll` closes on any scroll instead of tracking. `persistent` and `trap-focus` are orthogonal, combine them for a micro dialog.
- Events. `open` and `close` for lifecycle, `cancel` for outside click and Escape dismissal when not persistent. Methods `open()` and `close()` for imperative control.
- Content aware placement. Direction defaults to `down` when content fits below the trigger, flips to whichever side has more room when content does not fit below. After the direction is chosen, `max-height` caps at the available space in that direction and the surface becomes scrollable when content exceeds the cap. Alignment defaults to `start` and flips to `end` when the start edge would clip. Explicit `direction` or `align` disable the corresponding axis auto flip.
- Top layer rendering. Surface uses `position: fixed` so it escapes ancestor `overflow: hidden` and appears above normal stacking contexts. `z-index: 2000`. Positioned continuously on scroll and resize so the surface follows the trigger. When the trigger leaves the viewport the surface visually hides while preserving `open` state, when the trigger scrolls back the surface reappears.
- Sizing. `size` attribute maps to `max-width` with an effective cap of `min(size default or override, calc(100vw - 8px))` so the popover shrinks below the configured size when the viewport is narrower. `max-height` is `min(--canvas-popover-max-height override, calc(100vh - 8px), available direction space)` with no hard default cap so tall content uses the viewport. Long unbreakable tokens break via `overflow-wrap: anywhere` so horizontal scroll rarely appears.
- Popover section in `references/web-components.md` covering attributes, slots, events, methods, keyboard, ARIA, placement, scroll behavior, and sizing tokens.
- Popover section in `references/component-usage.md` naming the use cases (filter forms, column pickers, legends, bulk action panels, micro confirmation dialogs) and non uses (action menus, form field selection, tooltips, full page overlays) plus attribute, trigger, and content rules.
- Popover Keyboard and Focus, Popover Placement and Scroll, and Popover ARIA sections in `references/interaction-patterns.md`.
- Popovers check block in `references/validation-checklist.md` Phase 2. Eight checks covering dialog role content, required label, slotted trigger with accessible name, lifecycle handler, persistent restraint, trap focus paired with a close control, no nested popovers, and placement override restraint.
- Popover Visual Spec section in `DESIGN.md` with surface, size, height, placement, scroll behavior, focus, and ARIA values.
- Key Rules entry in `SKILL.md` stating that anchored content surfaces are popovers, not modals.
- Showcase additions in `examples/showcase.html`. New Popover nav link between Multi-Select and Progress. Six demo cards covering filter form, column picker, persistent confirmation micro dialog, size variants including a `--canvas-popover-max-width` override, auto-flip placement, and tall content adapting to available space with directional height capping.
- `canvas-popover` added to the `INTERACTIVE_SELECTOR` used by `canvas-accordion-title` click handling and to the focusable descendants query used by `canvas-modal` focus trap.

### Changed

- Shared placement helper `computeAutoPlacement` extracted into module scope. `canvas-menu-button` now calls the shared helper instead of inlining the flip math. `canvas-popover` uses the same helper for the align decision and adds content aware direction picking on top. Pure refactor for menu button, no observable change.
- Common Mistake entry in `references/workflow.md` added for anchored content surface built as a modal, pointing at `canvas-popover`.

## 4.9.0

### Added

- New component `canvas-menu-button` for action menus (plus buttons, row kebabs, overflow menus). Implements the WAI ARIA Menu Button pattern with `role="menu"` and `role="menuitem"` children rather than overloading `canvas-dropdown`. Not form associated, no `name` or `value`, each option activation dispatches a `select` event with `detail.value` and `detail.label`. Children are `canvas-option` elements, the shared option element already used by `canvas-dropdown`, `canvas-combobox`, and `canvas-multi-select`. The 26 component count in `SKILL.md` reflects the addition.
- Slotted trigger via `slot="trigger"`. Default trigger (when no trigger is slotted) renders a ghost Actions button with a caret. Slotted triggers are typically a `canvas-button` with an icon for plus and kebab patterns. The default trigger owns `aria-haspopup="menu"` and toggles `aria-expanded` automatically, slotted triggers only need `aria-label` when icon only.
- Section dividers via `<hr>` children. A plain HTML `<hr>` between `canvas-option` children renders a section separator using the same color as the outer menu border, with small vertical spacing. Dividers expose `role="separator"` and are skipped by keyboard navigation.
- Auto-flip placement. On open the component measures the trigger rect against the viewport and flips the menu to `up` when the menu would clip below, or to `end` alignment when it would clip the right edge. Explicit `direction="down"`, `direction="up"`, `align="start"`, or `align="end"` attributes pin the corresponding axis and disable auto flipping on that axis only.
- Dimension rules. `min-width: 180px`, `max-width: 320px` with text wrapping at the cap, `max-height: 16.02857143rem` with scroll. Option padding and font match `canvas-dropdown` for visual parity.
- Menu Button section in `references/web-components.md` covering attributes, slots, events, keyboard, ARIA, placement, and dimensions.
- Menu Button section in `references/component-usage.md` naming the use cases (plus button, row action menu, overflow menu, sectioned actions) and non uses (value selection, arbitrary popover content, navigation, two or fewer actions). Dropdown vs Combobox vs Native Select section now explicitly calls out that actions belong in `canvas-menu-button`, not `canvas-dropdown`.
- Menu Button Keyboard Navigation, Focus Return, and ARIA sections in `references/interaction-patterns.md` documenting the Enter and Space open without highlight contract, ArrowDown and ArrowUp open with highlighted first or last, wrap behavior, Home and End, select returns focus to the trigger, Escape and Tab close, outside click close.
- Menu Buttons check block in `references/validation-checklist.md` Phase 2. Eight checks covering action role intent, trigger accessibility, select listener presence, row alignment, absence of form participation attributes, divider usage, minimum option count, and placement override restraint. Dropdowns and Comboboxes block gains a second check that flags `canvas-dropdown` whose children read like actions and points at the replacement.
- Menu Button Visual Spec section in `DESIGN.md` with trigger, menu container, option, divider, and placement values.
- Key Rules entry in `SKILL.md` stating that action menus are not dropdowns and naming the two behavioral differences (form association, event shape).
- Showcase additions in `examples/showcase.html`. New Menu Button nav link between Loader and Modal. Eight demo cards covering default trigger, plus icon, kebab row action, disabled option, disabled menu button, section dividers, width and height extremes (exercises min-width, max-width wrapping, and max-height scrolling in one menu), auto-flip placement, and explicit direction override.
- `canvas-menu-button` added to the `INTERACTIVE_SELECTOR` used by `canvas-accordion-title` click handling and to the focusable descendants query used by `canvas-modal` focus trap, so menu buttons nested inside titles and modals behave correctly.

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

- `canvas-loader`. Loading spinner matching the Canvas home-app. Four sizes (mini, small, default, large), inline and centered positioning modes, inverted mode for dark backgrounds, and optional text label. Arc color is #767676 (gray), not blue.

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
- `canvas-badge`. 13 named colors, 4 sizes (mini, tiny, small, large), basic (outlined) and circular variants.
- `canvas-chip`. Dismissible tag sharing the badge color palette. Fires a `dismiss` event on X click.
- `canvas-input`. Text input and textarea with integrated label, error state, and form participation via ElementInternals.
- `canvas-radio`. Locked radio matching the Canvas home-app. Grouped by shared `name` attribute. ElementInternals for form data.
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
- `assets/typography.css`. Heading and paragraph styles matching the Canvas home-app. Loads Lato via `@import`.
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
- Badge system (13 solid colors, basic bordered variant, size tiers)
- Banner (4 semantic variants, toast removed)

### Components changed
- Accordion corrected from Canvas source inspection (borderless basic variant, h3 headers, 7px padding, 34.58px natural height)
- Validation checklist rewritten as five-phase sequential protocol

## 1.0.0 (2026-03-25)

Initial release. Core design system with buttons, forms, checkboxes, radios, toggles, cards, tables, tabs, accordions, dropdowns, comboboxes, tooltips, dividers, skeletons, spinners, badges, banners, empty states, confirmation dialogs, patient context header.
