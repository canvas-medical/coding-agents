# Interaction Patterns

Cross-cutting interaction rules that apply across components. Focus management for modals, the toggle and submit prohibition, shared ARIA essentials, scrollable container contract, form submission behavior, the accessibility helper primitives the component bundle ships, touch targets, and patient context safety. Per-component keyboard, focus return, and ARIA contracts live with each component in [web-components.md](web-components.md). When-to-use rules live in [component-usage.md](component-usage.md). Visual specification rules (hierarchy, density, truncation, date formatting) live in [DESIGN.md](../DESIGN.md).

## Focus Management

- When a modal opens, move focus to the first focusable element inside (usually the close button or the first form input).
- When a modal closes, return focus to the element that triggered it. Never leave focus in an undefined state.
- Focus must be trapped inside open modals. Tab cycles through focusable elements within the modal and never escapes to the page behind it.
- When content loads dynamically (fetch, AJAX), focus should not jump unpredictably. If new content replaces the current view entirely, move focus to the top of the new content. If content is appended (like loading more list items), keep focus where it was.
- When a banner or notification appears, it should not steal focus. Use `aria-live` to announce it to screen readers without disrupting the user's current position.

## Toggle and Submit Prohibition

This is the most common UX mistake in generated plugin UI. It must be prevented.

- Toggles must never appear on a screen that has a Save or Submit button. This is a hard rule with no exceptions.
- If a form collects settings that are saved together, every control must be a checkbox, radio button, or input. Never a toggle.
- If a setting should take effect immediately, use a standalone toggle with no submit button anywhere on the screen. Provide instant visual feedback (an inline banner or confirmation).
- Mixed patterns on the same screen (some toggles for instant effect, some checkboxes for deferred submission) confuse users about what is saved and what is not. Pick one model per screen and apply it consistently.

## ARIA Essentials

Minimum ARIA attributes for common plugin UI elements. Do not over-apply ARIA. Use semantic HTML first (a `<button>` element does not need `role="button"`). Per-component ARIA contracts (roles, states, wiring) live with each component in [web-components.md](web-components.md).

- **Buttons that toggle state** need `aria-pressed="true"` or `aria-pressed="false"`. Buttons that expand or collapse content need `aria-expanded="true"` or `aria-expanded="false"`.
- **Form inputs** need associated `<label>` elements using `for`/`id` pairing. If a visible label is not feasible, use `aria-label` on the input.
- **Error messages** need `aria-live="polite"` on the container so screen readers announce validation errors as they appear.
- **Loading spinners** need `aria-label="Loading"` and `role="status"`.
- **Tables** need `<caption>` or `aria-label` on the `<table>` element describing the table's purpose.
- **Toggle switches** need `role="switch"` and `aria-checked="true"` or `aria-checked="false"`.
- **Menu items** that perform actions use `role="menuitem"`. Menu items that toggle state use `role="menuitemcheckbox"` or `role="menuitemradio"`. `canvas-menu-button` wires `role="menuitem"` automatically, the other two roles are for hand rolled menus only.
- **Required fields** need `aria-required="true"` (or use the HTML `required` attribute).
- **Disabled elements** should use the `disabled` attribute on native HTML elements. For custom elements, use `aria-disabled="true"` and remove click handlers.
- Do not use `aria-label` as a substitute for visible text. It is for screen readers when visible text is not feasible. If you can show the text, show it.

## Scrollable Containers

- Scrollable regions need `tabindex="0"` so keyboard users can scroll them with arrow keys.
- Scrollable regions need an accessible name via `aria-label` or `aria-labelledby` so screen readers can identify them.
- `canvas-scroll-area` applies both automatically when a `vertical` or `horizontal` direction is set. See [web-components.md](web-components.md) canvas-scroll-area.

## Form Submission

- Pressing Enter in a single-line text input should submit the form when there is only one input and one submit action on the screen.
- In multi-field forms, Enter should not submit. Only the explicit submit button triggers submission.
- The submit button must be reachable by tabbing from the last form field.
- Tab order must follow the visual layout: top to bottom, left to right for side-by-side fields.
- After a successful submission, move focus to the success message or back to the top of the form. Do not leave focus on the disabled submit button.

## Accessibility Helpers

The skill ships six reusable accessibility primitives near the top of `assets/canvas-plugin-ui.js`. Component classes consume them so that ARIA contracts, focus management, motion preferences, and screen reader text follow the same pattern across the bundle. New components and forks should reach for these helpers before reinventing the contract.

### cuid

Per element unique id generator. Returns a string of the form `prefix_<timestamp>_<counter>` so two instances of the same component on the same page never collide on the same id. Use it wherever a component needs a stable id that an ARIA reference such as `aria-describedby`, `aria-labelledby`, or `aria-controls` can point to.

`canvas-input` is the canonical pattern. The component generates three ids on construction, one for the inner `<input>`, one for the visible label, and one for the error span. The `<label>` element's `for` attribute points at the input id, the input's `aria-labelledby` points at the label id, and the input's `aria-describedby` points at the error span id when the `error` attribute is set. Multiple `canvas-input` instances on the same form no longer collide on the literal id `err`, which was the duplicate id collision the audit caught.

```javascript
this._inputId = cuid('input');
this._labelId = cuid('label');
this._errorId = cuid('error');
```

### reduceMotion

Runtime `matchMedia('(prefers-reduced-motion: reduce)')` query. Returns true when the user has requested reduced motion at the OS level. Use it to swap an animation for a static affordance at component construction time when CSS `@media (prefers-reduced-motion: reduce)` cannot reach into shadow DOM keyframes.

`canvas-loader` is the canonical pattern. When `reduceMotion()` returns true, the spinner stops, the spinning arc renders as a static partial circle, and the `aria-label` text remains the only signal that work is in flight. When the helper returns false, the spinning animation runs as before. Pair this runtime check with the `PREFERS_REDUCED_MOTION_CSS` shadow style block for the CSS only path.

```javascript
if (reduceMotion()) {
  this._spinner.style.animationName = 'none';
}
```

### trapFocus

Shadow DOM aware focus trap. Takes a root element, returns a release function. The trap descends `composedPath` and open shadow roots when collecting tabbables, so it traps focus correctly even when the focusable target lives several shadow boundaries deep. The release function removes the listener and optionally restores focus to the element that was focused before the trap started.

`canvas-modal` is the canonical pattern. The component calls `trapFocus(this)` in `open()` and stores the release function. On `dismiss()`, the release function runs, focus returns to the trigger, and the listener is removed. Tab and Shift Tab cycle through the focusable elements inside the modal even when one of those targets lives inside a `canvas-input` or a `canvas-button` shadow root. Escape calls `dismiss()` so the same release path runs on keyboard close.

```javascript
open() {
  this._releaseFocusTrap = trapFocus(this);
}
dismiss() {
  if (this._releaseFocusTrap) this._releaseFocusTrap();
  this._releaseFocusTrap = null;
}
```

### AriaProxy

Class mixin that mirrors a configurable list of ARIA attributes from the host onto an inner control. The default attribute list is `required`, `aria-invalid`, `disabled`, `aria-describedby`, `aria-labelledby`, `aria-controls`, `aria-expanded`, and `aria-activedescendant`. Components extend the mixin via `class extends AriaProxy(HTMLElement)` and implement `_ariaProxyTarget()` which returns the inner element that should receive the mirrored attributes. The mixin also extends `observedAttributes` so the mirroring runs automatically inside `attributeChangedCallback`.

`canvas-input` is the canonical default attribute pattern. The component returns the inner shadow `<input>` from `_ariaProxyTarget()`. Setting `aria-describedby` on the host forwards it onto the inner input so screen readers announce the description when the input takes focus.

`canvas-button` is the canonical custom attribute list pattern. The component passes a custom list including `aria-label`, `aria-pressed`, `aria-expanded`, `aria-controls`, and `aria-disabled`. Disabled buttons use `aria-disabled="true"` rather than the native `disabled` attribute so the inner `<button>` stays in the focus order and screen readers can still announce the disabled affordance.

```javascript
class CanvasInput extends AriaProxy(HTMLElement) {
  _ariaProxyTarget() { return this._innerInput; }
}

class CanvasButton extends AriaProxy(HTMLElement, {
  attributes: ['aria-label', 'aria-pressed', 'aria-expanded', 'aria-controls', 'aria-disabled']
}) {
  _ariaProxyTarget() { return this._innerButton; }
}
```

### SR_STATUS_CSS

Visually hidden CSS template for screen reader only text. The template defines a `.sr-status` class that absolutely positions the element off screen with zero width and height, hidden overflow, and clipped rect, the standard pattern for visually hidden text that screen readers still read aloud. Components concatenate this template into their shadow style block and render text inside a `<span class="sr-status">` for any signal the visible UI conveys through color or icon alone.

`canvas-badge` is the canonical severity word pattern. The visible badge shows the colored swatch and the visible label such as `Active`. The component appends a `<span class="sr-status">` carrying the severity word such as `Active status` so screen reader users hear the severity alongside the badge label rather than only seeing the colored swatch. `canvas-loader` uses the same template for the loading status text the spinner conveys visually.

```javascript
this.shadowRoot.innerHTML = '<style>' + SR_STATUS_CSS + '</style>' +
  '<span class="sr-status">Active status</span>' +
  '<slot></slot>';
```

### PREFERS_REDUCED_MOTION_CSS

Shadow style block that gates animation duration, animation iteration count, transition duration, and scroll behavior under `prefers-reduced-motion: reduce`. The block uses the universal selector with the `::before` and `::after` pseudo elements so every animated descendant of the shadow root drops to a 0.01ms duration, single iteration, and instant scroll on reduced motion. Components concatenate this block into their shadow style block once, and every animated rule under that root respects the user's preference.

`canvas-loader` is the canonical pattern. The shadow style block carries the spinner keyframes plus `PREFERS_REDUCED_MOTION_CSS` so users who request reduced motion see the arc render once at its starting position rather than rotating. Pair this with the `reduceMotion` runtime helper for the path that needs to swap the affordance entirely rather than just stop the animation.

```javascript
this.shadowRoot.innerHTML = '<style>' +
  '@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }' +
  '.spinner { animation: spin 1s linear infinite; }' +
  PREFERS_REDUCED_MOTION_CSS +
'</style>' + ...;
```

## Clinical Environment

These rules are driven by the clinical environment. Clinicians work under time pressure, use tablets at the bedside, deal with long medical terminology, and make decisions where errors have real-world patient consequences.

### Accessibility and Touch Targets

- Minimum touch target size is `44px` by `44px` for all interactive elements (buttons, checkboxes, toggles, links, table row actions). Clinicians use tablets at the bedside and rolling cart touchscreens.
- Clickable areas can be visually smaller than 44 px as long as the hit area (padding included) meets the minimum.
- All color pairings must meet WCAG AA contrast ratio (4.5:1 for normal text, 3:1 for large text). Green `#22BA45` on white and white on green both pass. Muted text `#767676` on white passes at 4.6:1.
- Never rely on color alone to convey meaning. Pair color with text, icons, or patterns. A red badge should also have a label like "Critical" or an icon.

### Confirmation Hierarchy

For the confirmation hierarchy (no confirmation, soft undo, hard dialog, destructive typed input), see [component-usage.md](component-usage.md) Confirmation Hierarchy.

### Patient Context Safety

- When a plugin displays patient-specific data, the patient's identity must be visible on the screen. In a right chart pane, the chart on the left provides this context. In a modal or standalone page, the plugin must show the patient's name and at least one identifier (date of birth or MRN) near the top. See [surface-selection.md](surface-selection.md) for which surfaces require a patient context header. The copy-paste markup lives in [patterns.md](patterns.md).
- Never display clinical data from one patient in a context where the user might believe they are looking at a different patient.
