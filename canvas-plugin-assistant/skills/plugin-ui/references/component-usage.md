# Component Usage

These rules describe when to use each component and how interactions should behave. Keyboard and accessibility behavior is in interaction-patterns.md (loaded at Step 5).

## Tabs

- Use tabs when a single view has multiple content panels that the user switches between without leaving the page. The content under each tab should be related but distinct enough that showing it all at once would be overwhelming.
- Do not use tabs to navigate between different pages or routes. Tabs switch content panels within the same view. For page-level navigation, use the left nav or route links.
- Keep tab labels short (one to three words). If a tab has a count indicator, show it as a badge next to the label.
- If there are only two options and they represent a binary choice (on/off, yes/no, enabled/disabled), use a toggle or radio instead of tabs.
- If there are more than 6 tabs, consider whether the information architecture needs rethinking. Too many tabs force horizontal scrolling or wrapping, both of which hurt usability.
- The first tab should be the most commonly needed content. Do not default to a less important tab.
- In narrow containers like the right chart pane, tabs still work but keep labels very short to avoid wrapping.

## Accordion vs Tabs

- Use an **accordion** when sections are independent and the user may only need one or two at a time. Good for long forms with many sections (demographics, contacts, consents), settings pages, and FAQ-style content. Multiple sections can be open simultaneously.
- Use **tabs** when the user is switching between parallel views of the same data and only one view makes sense at a time. Good for content categories (coverages, claims, authorizations) where the sections are mutually exclusive.
- Use the **basic accordion** (transparent, borderless) as a bare content divider on a page. It sits directly in the content area without a card wrapper, matching the Canvas patient profile edit page. Do not wrap the basic accordion inside a card.
- Use the **styled accordion** (white background, shadow, borders between items) when the accordion needs to be a standalone elevated container on a gray background.
- The accordion title row has a fixed layout. The caret arrow is always first and never moves. To the left of the row (between the caret and any right-aligned content) you may place text, badges, or custom elements. Never a toggle or checkbox on the left side. To the right of the row (inside `.accordion-actions` with `margin-left: auto`) you may place badges, text, toggles, or checkboxes. When a toggle or checkbox is present on the right, it is always the outermost right element. Badges and text sit to its left. Badges can also be placed next to the title text on the left (omit `flex-grow` on the title span) for a tighter grouping.
- The default title height is ~34.58px. Do not add `min-height` or extra padding to accordion titles. If a larger trigger height is needed, the user must explicitly request it. When toggles or checkboxes sit in the actions area, they naturally expand the row through their own height.

## Checkboxes vs Toggle Switches

- Use a `canvas-toggle` for settings that take effect immediately (enable/disable a feature, show/hide a section). The user expects the change to apply as soon as they flip the toggle.
- Use a `canvas-checkbox` for selections that are part of a form and only take effect when the user submits. Also use checkboxes when the user can select multiple items from a list.
- Never mix toggles and checkboxes in the same form for the same type of choice.
- Never combine toggle switches with a Save or Submit button. If the screen has a submit step, every control must be a checkbox, radio, or input. Never a toggle. Toggles imply instant effect and a submit button contradicts that.
- If a setting should take effect immediately, use a standalone `canvas-toggle` with no submit button. Provide instant visual feedback (inline banner or confirmation).
- Mixed patterns (some toggles, some checkboxes on the same screen) confuse users about what's saved and what isn't. Pick one model per screen.

## Text Inputs vs Textareas

- Use a text input for single-line values like names, emails, phone numbers, dates, and short identifiers.
- Use a textarea for multi-line content like notes, descriptions, comments, and free-form text.
- Always include a visible label above the input. Do not rely on placeholder text as the only label. Placeholders disappear once the user starts typing, leaving a filled form with no visible field names.
- Use placeholder text to show an example value or format hint, not to describe the field's purpose.

## Dropdown vs Combobox vs Native Select

- Use a **`canvas-dropdown`** as the default for picking from a fixed list of options. This matches the Semantic UI selection dropdown used throughout the Canvas home-app. The custom dropdown has a white menu, subtle gray on selected items, and connected border-radius between trigger and menu.
- Use a **`canvas-combobox`** when the list is long or the option text is long and the user benefits from typing to filter (provider search, appointment selection, diagnosis lookup, medication search). Visually identical to the dropdown but the input is editable.
- **Do not use native `<select>` elements.** Native selects render with OS-level styling that does not match the Canvas home-app on any platform. The dropdown menu appearance (colors, fonts, selected item highlight) is controlled by the operating system and cannot be styled. Always use `canvas-dropdown` or `canvas-combobox` instead.
- Use **radio buttons** when there are 2 to 3 mutually exclusive options and you want all choices visible at once without requiring a click to open.
- Never use a dropdown for yes/no or on/off choices. Use a toggle or checkbox instead.

## Multi-Select

When the user needs to pick multiple values from a set.

- **Fewer than 8 options.** Use a **checkbox group** (standard `canvas-checkbox` elements). All options visible, no dropdown, no search. Appointment types, status filters, day-of-week selection.
- **8 or more options.** Use a **`canvas-multi-select`** (see web-components.md). Search to filter, inline checkboxes in each option, selected items rendered as dismissible chips inside the trigger area. Providers, locations, diagnosis codes, insurance plans.
- **Never use a native `<select multiple>`.** It is unusable on touch devices, has no search, and cannot be styled to match Canvas.
- If the set is dynamic or very large (hundreds of items), still use `canvas-multi-select`. The search input makes large sets manageable.

## Tables vs Card Lists

- Use a table when displaying structured data with consistent columns across all rows (patient lists, lab results, medication schedules).
- Use a card list when each item has variable content, needs its own actions, or benefits from visual grouping (summary cards, task cards, protocol overviews).
- If a table would have only one meaningful column, use a simple list instead.

## Table Behavior in Narrow Containers

Plugins render in different surface widths. A full page plugin has room for wide tables. A right chart pane plugin is roughly 25% to 40% of the viewport. Tables need to handle both cases.

- **Prefer fewer columns in narrow surfaces.** Before reaching for horizontal scroll, ask whether every column is necessary. Drop low-value columns (IDs, secondary dates, metadata) and show them in a detail view or tooltip instead.
- **Use horizontal scroll when columns cannot be reduced.** Wrap the table in `.table-scroll` and set `min-width` on the table. The container scrolls horizontally while the page stays fixed. This is better than squishing columns into unreadable widths.
- **Use compact padding in narrow surfaces.** The `.table-compact` modifier tightens padding without changing font size, giving each column more room.
- **Combine compact and scroll for dense data.** A claims table with 6 columns in a sidebar can use `.table-compact` inside `.table-scroll` with a `min-width` that ensures each column has enough room.
- **Do not hide columns with CSS media queries.** The plugin iframe width does not correspond to viewport breakpoints. A right chart pane can be 400px wide on a 1920px monitor. Media queries based on viewport width will not trigger correctly. Instead, design the table for the surface it will render in.

## Buttons

Green is rare. Blue is the default. Most plugin screens will have blue buttons only.

- **Green** is only for clinical state transitions and confirmations that affect the patient record or leave the system. Sign/lock a note, send a message to a patient, submit a referral, confirm a fax, check in a patient. If the action doesn't change the patient record or leave the plugin's scope, it should not be green.
- **Blue** is for all standard actions. Save, done, next, add, update, edit, adjust, refill, stop, back, return, skip. Form submissions are blue. Multi-step modal footers are blue.
- A screen should have at most one green button. If you're not sure whether an action qualifies for green, use blue.
- **Button sizing.** Three layout patterns determine the size tier.
  - **Input-paired buttons** (button in the same row as an input, forming a visual unit like "Add" next to a text field). Match the input height. Standard inputs are ~43px, so use base `canvas-button`. If the form uses compact inputs, use `size="sm"`. Never use `size="xs"` for input-paired buttons because the height mismatch looks broken.
  - **Floating utility buttons** (button near a field but not height-paired, like "+ Insert Field" above a textarea or "Clear" on a filter tag). Use `size="xs"`. These should not compete visually with the content they support.
  - **Table row buttons** ("Retry", "Edit", "View" in table cells). Use `size="sm"` for standard tables. Use `size="xs"` for compact tables. If the action is a simple text link (like "Remove" in a data row), a ghost text link may work better than a button. The goal is that the button does not inflate the row height. Table action buttons should be their natural width and right-aligned in the cell using the `cell-actions` class. Never stretch buttons to fill the cell width. When buttons in the same column vary in text length ("Edit" vs "Reschedule"), each button keeps its own width.
- Place the main action on the right side of a button group. Place cancel or back on the left.
- Use `variant="ghost"` for actions that are available but not encouraged (reset, clear filters, cancel).
- Destructive actions always require a confirmation step. Never put a `variant="danger"` button directly next to the main action button. Either move it to a separate section, use `variant="ghost"` to visually downplay it, or add a confirmation dialog.
- If the action navigates the user away from the current screen, make that clear. Use a link or indicate the destination. Never silently redirect after a button click.

## Form Element Height Cohesion

When the user requests a custom height on any form element (text input, `canvas-dropdown`, `canvas-combobox`, button) in a specific context (a card, a sidebar section, a modal form, a toolbar row), match the height of all sibling form elements in that same group. If a text input is made shorter to fit a compact sidebar, the dropdown next to it and the button beside it should shrink to the same height. This applies to elements that are visually grouped, on the same row or in the same form section. It does not mean changing the default dimensions globally across the whole plugin. The default sizes stay the same everywhere else. Only the local group of elements should be cohesive.

## Feedback and Status

- Use inline validation messages directly below the field that has the error. Do not show all errors in a single banner at the top.
- Use an inline banner for success feedback after a save or submit. Show a `canvas-banner` with `variant="success"` at the top of the form or content area. Never silently succeed. Canvas does not use floating toast notifications. All feedback is inline.
- Use a banner at the top of the content area for warnings or informational messages that apply to the whole screen.
- Disable the submit button until all required fields are filled. Show inline validation errors when the user leaves a field, not only after they hit submit.

## Banner Variant Guide

Canvas uses error and warning banners extensively. Success and info banners are extremely rare.

- **`variant="error"`** for API failures, server errors, and validation errors that block form submission. Place directly above the form or action that failed. If individual field validation is sufficient (red field borders and error text on canvas-input), do not add a banner on top.
- **`variant="warning"`** for situations where the user can proceed but should be aware of a risk. Potential duplicate patient, coverage about to expire, data that looks unusual.
- **`variant="success"`** is almost never needed. Use only when the user stays on the same page after an action and the UI does not visually change to reflect the outcome. If the modal closes, the form resets, or a row appears, that IS the confirmation.
- **`variant="info"`** for neutral context the user might not know. First-time usage hints, links to documentation. Use very sparingly.

Do not show a success banner after every save. Do not show multiple banners stacked. If an action produces several errors, put them in a single error banner with a list inside. Never use floating toasts, snackbars, or auto-dismissing notifications.

## Modal Patterns

**Size selection.** Use `size="small"` for confirmations and short questions (fewer than 3 fields). Use `size="medium"` for form dialogs (4 or more fields). Use `size="full"` for complex views needing maximum space.

**Dismiss behavior.** By default, Escape and backdrop click close the modal. Add `persistent` when the user must explicitly choose an action (destructive confirmations, required data entry).

**Header dismiss button.** Add `dismissable` on `canvas-modal-header` only when the header is present and the user has no other visible dismiss path. Most confirmation modals have Cancel and Confirm buttons, so no X button is needed.

**Confirmation pattern for destructive actions.**

```html
<canvas-modal id="delete-modal" size="small" persistent>
  <canvas-modal-header>Delete Record</canvas-modal-header>
  <canvas-modal-content>
    <p>This action cannot be undone. Are you sure?</p>
  </canvas-modal-content>
  <canvas-modal-footer>
    <canvas-button variant="ghost" onclick="document.getElementById('delete-modal').dismiss()">Cancel</canvas-button>
    <canvas-button variant="danger">Delete</canvas-button>
  </canvas-modal-footer>
</canvas-modal>
```

## Badges

- Use **mini** (`size="mini"`) as the default size for all status indicators in tables, cards, lists, and accordion titles. This is the size Canvas uses most frequently.
- Use **tiny** or **small** only when the badge needs to be more prominent, like a standalone tag or a primary visual element.
- Use the **solid color** variants (`canvas-badge` with a color attribute like `green`, `red`, etc.) for status display. White text on a colored background. This matches the Semantic UI Label used throughout the Canvas home-app.
- Use the **basic** variant (add the `basic` attribute) for de-emphasized or neutral statuses like "Inactive", "Self-pay", or "Draft" where a solid color would be too visually heavy.
- Use the **circular** variant (add the `circular` attribute) for notification counts. Short content renders as a circle, longer content stretches into a pill.
- Match colors to semantic meaning consistently. Green for accepted or active, red for denied or error, blue for submitted or pending, grey for done or draft, yellow for pending review, orange for warnings or preferred tags, teal for scheduled.
- Do not use violet, purple, or pink for clinical statuses. Reserve those for non-clinical tags where a distinct color is needed to differentiate from the clinical palette.

## Chips

- A chip is a badge the user can dismiss. Same visual base, same colors, same sizes. Use chips when the user can remove the item. Use badges when the item is read-only.
- Use chips for **filter bars** where the user removes active filters by clicking the dismiss button. Pair with a "Clear all" ghost button at the end.
- Use chips for **tag inputs** where the user adds and removes tags. Place chips above or beside the text input. New chips are created via JS when the user types and presses enter.
- Use chips for **multi-select display** where selected items from a dropdown or combobox are shown as removable chips.
- The dismiss button uses an SVG X icon (8x8, stroke-linecap round) that inherits the chip text color. Do not use the `&times;` HTML entity as it does not center correctly across font sizes.
- Include a single dismiss event listener on a parent container using event delegation, not individual handlers on each chip.
- When a chip is dismissed, remove it from the DOM. Update any backing data state (filter list, selected values, tag array) in the same handler.

## Empty States

- When a list, table, or section has no data, show a short message explaining why and what the user can do next. Do not leave blank space with no explanation.
- Use muted text (`#767676`) for empty state messages. Center them vertically and horizontally in the container.

## Loading States

- Use a **skeleton** when the page layout is known (you know there will be a table with 3 columns, a card with a title and body, a list of items). Skeletons preview the expected structure and feel faster to the user.
- Use a **spinner** when the layout is unknown, the entire view is loading, or the loading area is too small for meaningful skeleton shapes.
- If a specific section is loading while the rest of the page is ready, show the loading indicator only in that section rather than blocking the whole screen.
- Do not leave the screen blank during loads.

## Form Layout

- Stack form fields vertically with `12px` between them. Do not place unrelated fields side by side unless they are logically paired (first name and last name, city and state).
- Group related fields under a shared heading or within a card. If a form is long enough to scroll, it must have grouping.
- Place the submit button below the last field, separated by `16px`. Align it to the left or stretch it full width in narrow containers.
- Don't use modals for complex forms. If a form has more than 3 or 4 fields, it should be a page or a panel section, not a modal. Modals are for confirmations, single-field edits, and quick selections.

## Read-Only vs Editable Content

- When mixing display and edit on the same screen, make it visually obvious which parts are interactive. Read-only values use plain text. Editable values sit inside input fields with visible borders.
- Keep action placement consistent. If the save button is bottom-right on one screen, it should be bottom-right on every screen in the same plugin.

## Sidebar Width Awareness

- Plugins in `RIGHT_CHART_PANE` are narrow (roughly 25% to 40% of the viewport). Avoid horizontal layouts, multi-column forms, and wide tables in sidebar plugins. Stack everything vertically.
- Full-page plugins (`TargetType.PAGE`) have more room and can use multi-column layouts where appropriate.

## Text and Background Pairing

These rules are mandatory with no exceptions.

- **On white (`#FFFFFF`) backgrounds.** Both dark text and muted gray text are allowed. This is the only background where gray text may appear.
- **On light gray and mid gray backgrounds.** Only dark text. Never place gray text on a gray background.
- **On colored backgrounds** (green, blue, red, orange, brown). Text must be white and bold.

## Anti-Patterns

- Never use purple, teal, pink, cyan, or other colors outside the palette. These are common AI-generation defaults.
- Never use `box-shadow` to simulate borders. Use actual `border` properties.
- Never set `outline: none` on focusable elements without providing an alternative focus indicator.
- Never use custom scrollbar styling in plugin CSS. Let the browser handle scrollbars natively.
- Never use CSS media queries based on viewport width for plugin content. Plugin iframes do not respond to viewport breakpoints. Design for the known surface width.
