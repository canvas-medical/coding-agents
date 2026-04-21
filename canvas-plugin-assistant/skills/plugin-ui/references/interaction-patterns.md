# Interaction Patterns

Keyboard navigation, focus management, ARIA attributes, and behavioral rules for interactive elements. Clinical environment guidelines for touch targets, confirmations, and patient safety. For visual specification rules (hierarchy, density, truncation, date formatting), see [DESIGN.md](../DESIGN.md). When-to-use guidance is in component-usage.md (loaded at Step 3).

## Interaction Behavior

### Tab Keyboard Navigation

- Left and Right arrow keys move focus between tab items within the tab menu.
- Home jumps to the first tab. End jumps to the last tab.
- Enter or Space activates the focused tab and shows its panel.
- Tab items use `role="tab"`, the container uses `role="tablist"`, and panels use `role="tabpanel"`.
- Active tab has `aria-selected="true"`. Inactive tabs have `aria-selected="false"`.
- Each tab has `aria-controls` pointing to its panel ID. Each panel has `aria-labelledby` pointing to its tab ID.

### Combobox and Select Keyboard Navigation

- Click, Enter, or Space on the trigger opens the dropdown.
- Escape closes the dropdown and returns focus to the trigger.
- Up and Down arrow keys open the dropdown if closed. When open, they move the highlight through options.
- Enter selects the currently highlighted option and closes the dropdown.
- Type-ahead: typing a letter jumps to the first option starting with that letter. Typing multiple letters in quick succession narrows the match.
- Home and End keys jump to the first and last option when the dropdown is open.
- Tab closes the dropdown (selecting the highlighted option if any) and moves focus to the next focusable element.
- Clicking outside the dropdown closes it without selecting.

### Dropdown and Menu Behavior

- Clicking outside the dropdown or menu closes it.
- Dropdown menus must not exceed the viewport. If the menu would overflow below the trigger, flip it to open above. If it would overflow on the right, align it to the right edge of the trigger.
- Long option lists should scroll within the dropdown rather than growing the dropdown beyond the viewport.
- Menu items that perform actions use `role="menuitem"`. Menu items that toggle state use `role="menuitemcheckbox"` or `role="menuitemradio"`.

### Focus Management

- When a modal opens, move focus to the first focusable element inside (usually the close button or the first form input).
- When a modal closes, return focus to the element that triggered it. Never leave focus in an undefined state.
- Focus must be trapped inside open modals. Tab cycles through focusable elements within the modal and never escapes to the page behind it.
- When content loads dynamically (fetch, AJAX), focus should not jump unpredictably. If new content replaces the current view entirely, move focus to the top of the new content. If content is appended (like loading more list items), keep focus where it was.
- When a banner or notification appears, it should not steal focus. Use `aria-live` to announce it to screen readers without disrupting the user's current position.

### Toggle and Submit Prohibition

This is the most common UX mistake in generated plugin UI. It must be prevented. (Summary in SKILL.md Key Rules.)

- Toggles must never appear on a screen that has a Save or Submit button. This is a hard rule with no exceptions.
- If a form collects settings that are saved together, every control must be a checkbox, radio button, or input. Never a toggle.
- If a setting should take effect immediately, use a standalone toggle with no submit button anywhere on the screen. Provide instant visual feedback (an inline banner or confirmation).
- Mixed patterns on the same screen (some toggles for instant effect, some checkboxes for deferred submission) confuse users about what is saved and what is not. Pick one model per screen and apply it consistently.

### ARIA Essentials

These are the minimum ARIA attributes for common plugin UI elements. Do not over-apply ARIA. Use semantic HTML first (a `<button>` element does not need `role="button"`).

- **Buttons that toggle state** need `aria-pressed="true"` or `aria-pressed="false"`. Buttons that expand/collapse content need `aria-expanded="true"` or `aria-expanded="false"`.
- **Form inputs** need associated `<label>` elements using `for`/`id` pairing. If a visible label is not feasible, use `aria-label` on the input.
- **Error messages** need `aria-live="polite"` on the container so screen readers announce validation errors as they appear.
- **Loading spinners** need `aria-label="Loading"` and `role="status"`.
- **Tables** need `<caption>` or `aria-label` on the `<table>` element describing the table's purpose.
- **Toggle switches** need `role="switch"` and `aria-checked="true"` or `aria-checked="false"`.
- **Comboboxes** need `role="combobox"` on the input, `aria-expanded` to indicate dropdown state, `aria-controls` pointing to the listbox ID, and `aria-activedescendant` pointing to the currently highlighted option.
- **Required fields** need `aria-required="true"` (or use the HTML `required` attribute).
- **Disabled elements** should use the `disabled` attribute on native HTML elements. For custom elements, use `aria-disabled="true"` and remove click handlers.
- Do not use `aria-label` as a substitute for visible text. It is for screen readers when visible text is not feasible. If you can show the text, show it.

### Scrollable Containers

- Scrollable regions need `tabindex="0"` so keyboard users can scroll them with arrow keys.
- Scrollable regions need an accessible name via `aria-label` or `aria-labelledby` so screen readers can identify them.

### Form Submission

- Pressing Enter in a single-line text input should submit the form when there is only one input and one submit action on the screen.
- In multi-field forms, Enter should not submit. Only the explicit submit button triggers submission.
- The submit button must be reachable by tabbing from the last form field.
- Tab order must follow the visual layout: top to bottom, left to right for side-by-side fields.
- After a successful submission, move focus to the success message or back to the top of the form. Do not leave focus on the disabled submit button.

## Clinical Environment

These rules are driven by the clinical environment. Clinicians work under time pressure, use tablets at the bedside, deal with long medical terminology, and make decisions where errors have real-world patient consequences.

### Accessibility and Touch Targets

- Minimum touch target size is `44px` by `44px` for all interactive elements (buttons, checkboxes, toggles, links, table row actions). Clinicians use tablets at the bedside and rolling cart touchscreens.
- Clickable areas can be visually smaller than 44px as long as the hit area (padding included) meets the minimum.
- All color pairings must meet WCAG AA contrast ratio (4.5:1 for normal text, 3:1 for large text). Green `#22BA45` on white and white on green both pass. Muted text `#767676` on white passes at 4.6:1.
- Never rely on color alone to convey meaning. Pair color with text, icons, or patterns. A red badge should also have a label like "Critical" or an icon.

### Confirmation Hierarchy

For the confirmation hierarchy (no confirmation, soft undo, hard dialog, destructive typed input), see component-usage.md Confirmation Hierarchy.

### Patient Context Safety

- When a plugin displays patient-specific data, the patient's identity must be visible on the screen. In a right chart pane, the chart on the left provides this context. In a modal or standalone page, the plugin must show the patient's name and at least one identifier (date of birth or MRN) near the top. See [surface-selection.md](surface-selection.md) for which surfaces require a patient context header.
- Never display clinical data from one patient in a context where the user might believe they are looking at a different patient.

## Sortable List Keyboard

Focus a `canvas-sortable-item` handle with Tab.

- `ArrowUp` and `ArrowDown` reorder within the current list. Each keypress fires `reorder` and `change`, and announces position N of M in the list label.
- `ArrowLeft` and `ArrowRight` move the item into the previous or next list in the same group. Only active when the list has a `group` attribute and a compatible sibling list exists. Each keypress fires `move` and `change`, and announces source and destination labels.

Sibling resolution walks all compatible lists by screen position left to right, not by strict DOM sibling order. A list placed anywhere in the document that shares the group can be reached by ArrowRight.

## Sortable List Cross List Cancel

`beforemove`, `beforereorder`, and `beforechange` are cancelable. Calling `e.preventDefault()` in a handler snaps the item back to its source position and suppresses the success events. Always pair a cancel with visible user feedback, a toast or inline message. A silent cancel reads as a visual glitch to the user.

## Sortable List ARIA

A shared polite live region announces every move. Label lists explicitly so announcements read naturally.

- Give each participating list an `aria-labelledby` pointing at its column heading, or an `aria-label` with the column name. Without a label, the announcer falls back to the list's `id`, then to the generic word "list".
- Within list moves announce "Moved item to position N of M in <label>.".
- Cross list moves announce "Moved item from <source label> to <destination label>, position N of M.".
