# Interaction Patterns

Cross-cutting interaction rules that apply across components. Focus management for modals, the toggle and submit prohibition, shared ARIA essentials, scrollable container contract, form submission behavior, touch targets, and patient context safety. Per-component keyboard, focus return, and ARIA contracts live with each component in [web-components.md](web-components.md). When-to-use rules live in [component-usage.md](component-usage.md). Visual specification rules (hierarchy, density, truncation, date formatting) live in [DESIGN.md](../DESIGN.md).

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
