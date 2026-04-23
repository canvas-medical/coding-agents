# Component Usage

These rules describe when to use each component. Per-component API and keyboard behavior live in [web-components.md](web-components.md). Cross-cutting interaction rules (focus management, toggle-submit prohibition, touch targets, ARIA essentials) live in [interaction-patterns.md](interaction-patterns.md). Copy-paste markup templates live in [patterns.md](patterns.md).

## Tabs

- Use tabs when a single view has multiple content panels that the user switches between without leaving the page. The content under each tab should be related but distinct enough that showing it all at once would be overwhelming.
- Do not use tabs to navigate between different pages or routes. Tabs switch content panels within the same view. For page-level navigation, use the left nav or route links.
- Keep tab labels short (one to three words). If a tab has a count indicator, show it as a badge next to the label.
- If there are only two options and they represent a binary choice (on/off, yes/no, enabled/disabled), use a toggle or radio instead of tabs.
- If there are more than 6 tabs, consider whether the information architecture needs rethinking. Too many tabs force horizontal scrolling or wrapping, both of which hurt usability.
- The first tab should be the most commonly needed content. Do not default to a less important tab.
- In narrow containers like the right chart pane, tabs still work but keep labels very short to avoid wrapping.
- When the user picks between 2 to 4 ways to view the same data (list vs grid, day vs week vs month, active vs archived), use tabs. Canvas does not use segmented controls or toggle button groups for this purpose. Tabs are the standard pattern for mutually exclusive view modes. The button group component (`canvas-button-group`) is for grouping related actions, not for selection.

## Accordion vs Tabs

- Use an **accordion** when sections are independent and the user may only need one or two at a time. Good for long forms with many sections (demographics, contacts, consents), settings pages, and FAQ-style content. Multiple sections can be open simultaneously.
- Use **tabs** when the user is switching between parallel views of the same data and only one view makes sense at a time. Good for content categories (coverages, claims, authorizations) where the sections are mutually exclusive.
- Use the **basic accordion** (transparent, borderless) as a bare content divider on a page. It sits directly in the content area without a card wrapper, matching the Canvas patient profile edit page. Do not wrap the basic accordion inside a card.
- Use the **styled accordion** (white background, shadow, borders between items) when the accordion needs to be a standalone elevated container on a gray background.
- The accordion title row has a fixed layout. The caret arrow is always first and never moves. To the left of the row (between the caret and any right-aligned content) you may place text, badges, or custom elements. Never a toggle or checkbox on the left side. To the right of the row (inside `.accordion-actions` with `margin-left: auto`) you may place badges, text, toggles, or checkboxes. When a toggle or checkbox is present on the right, it is always the outermost right element. Badges and text sit to its left. Badges can also be placed next to the title text on the left (omit `flex-grow` on the title span) for a tighter grouping.
- Buttons, toggles, checkboxes, radios, dropdowns, inputs, and other interactive elements can be placed directly inside `canvas-accordion-title`. Clicks and keyboard activations on those children run the child's own handler and do not toggle the surrounding accordion item. Authors do not need to add `event.stopPropagation` on buttons or other interactive descendants of the title slot.
- The default title height is ~34.58px. Do not add `min-height` or extra padding to accordion titles. If a larger trigger height is needed, the user must explicitly request it. When toggles or checkboxes sit in the actions area, they naturally expand the row through their own height.
- **Do not use native `<details>` or `<summary>` elements.** Use `canvas-accordion` with `canvas-accordion-item`, `canvas-accordion-title`, and `canvas-accordion-content`. The component renders its own chevron, handles ARIA and keyboard, and respects Canvas visual tokens. Any native `<details>` or `<summary>` in an existing template is a migration target. This rule is parallel to the native `<select>` prohibition in Dropdown vs Combobox vs Native Select and the native `<input>` prohibition in Text Inputs vs Textareas.
- A custom accordion pattern is acceptable only when the trigger needs a multi column layout that cannot fit the `canvas-accordion-title` slot, for example a medication group row with a drug name, sig line, code badges, fill count badge, and add button. In that narrow case, keep the custom header but match the Canvas visual tokens. Do not use native `<details>` even as the outer container for a custom header.
- Accordions carry no horizontal padding of their own. A top level `canvas-accordion` sits flush with the edges of its container the same way a raw `<h2>`, `<p>`, or `canvas-button` would. The container is responsible for horizontal inset. Wrap the accordion in a `canvas-card`, place it inside a section that already pads its children, or apply padding at the page shell level. Do not add inline padding on the accordion itself.
- Nested accordions indent automatically. A `canvas-accordion-item` placed inside another accordion's `canvas-accordion-content` picks up left padding of `--space-small` via a global rule in `canvas-plugin-ui.css`. Depth compounds through the cascade, each deeper level adds one `--space-small` step on the left. Do not hand roll per depth `padding-left` rules. To change the step size globally set `--canvas-accordion-nested-indent` on an ancestor, to remove the nested indent on one accordion set `--canvas-accordion-nested-indent: 0` on that element.

## Checkboxes vs Toggle Switches

- Use a `canvas-toggle` for settings that take effect immediately (enable/disable a feature, show/hide a section). The user expects the change to apply as soon as they flip the toggle.
- Use a `canvas-checkbox` for selections that are part of a form and only take effect when the user submits. Also use checkboxes when the user can select multiple items from a list.
- The toggle-submit prohibition forbids combining toggles with save or submit actions in the same UI segment. See [interaction-patterns.md](interaction-patterns.md) Toggle and Submit Prohibition for the full behavioral rule.

## Text Inputs vs Textareas

- Use `canvas-input` for single-line values like names, emails, phone numbers, dates, and short identifiers.
- Use `canvas-textarea` for multi-line content like notes, descriptions, comments, and free-form text.
- Always include a visible label above the input. Do not rely on placeholder text as the only label. Placeholders disappear once the user starts typing, leaving a filled form with no visible field names.
- Use placeholder text to show an example value or format hint, not to describe the field's purpose.
- **Do not use native `<input>` elements.** Use `canvas-input` for every input type including text, email, password, number, tel, url, date, datetime-local, month, week, and time. The `canvas-input` component styles the native date and time pickers through the same border, radius, padding, and font as other inputs. Using a raw `<input>` produces output that does not match Canvas even when CSS tokens are applied by hand. This rule is parallel to the native `<select>` prohibition in Dropdown vs Combobox vs Native Select.

## Textarea Variants

Five common patterns for `canvas-textarea`, each suited to a different context.

- **Fixed-height field.** Use a fixed `rows` value when the expected content length is known. Clinical notes (`rows="6"`), descriptions (`rows="4"`), short comments (`rows="2"`). The user can manually resize unless `no-resize` is set.
- **Single-line expandable.** Use `auto-resize rows="1"` for a field that starts matching the height of a `canvas-input` and grows as the user types. Good for inline comments, quick notes, and any field where one line is usually enough but more space is occasionally needed.
- **Capped expandable.** Use `auto-resize rows="1" max-rows="6"` when growth should stop at a reasonable point and scroll beyond it. This prevents the field from pushing the rest of the page out of view.
- **Chat input.** Use `auto-resize rows="1" max-rows="4"` paired with a send button in a grid layout (`grid-template-columns: 1fr auto; align-items: end`). The field starts at one line, grows to four, then scrolls. The button stays at the bottom as the field grows.
- **Character-limited field.** Add `maxlength="200"` (or any limit) to show a live counter below the field. Works with any of the patterns above. Use for override reasons, rejection notes, and any field with a backend length constraint.

## Dropdown vs Combobox vs Native Select

- Use a **`canvas-dropdown`** as the default for picking from a fixed list of options. Matches the selection dropdown used throughout the Canvas home-app. The custom dropdown has a white menu, subtle gray on selected items, and connected border-radius between trigger and menu.
- Use a **`canvas-combobox`** when the list is long or the option text is long and the user benefits from typing to filter (provider search, appointment selection, diagnosis lookup, medication search). Visually identical to the dropdown but the input is editable.
- **Do not use native `<select>` elements.** Native selects render with OS-level styling that does not match the Canvas home-app on any platform. The dropdown menu appearance (colors, fonts, selected item highlight) is controlled by the operating system and cannot be styled. Always use `canvas-dropdown` or `canvas-combobox` instead.
- Use **radio buttons** when there are 2 to 3 mutually exclusive options and you want all choices visible at once without requiring a click to open.
- Never use a dropdown for yes/no or on/off choices. Use a toggle or checkbox instead.
- **Never use `canvas-dropdown` for actions.** A dropdown is for selecting a value that is part of form state. For action triggers such as "Edit, Duplicate, Delete" row menus, plus buttons that open "Add X, Add Y, Add Z" lists, or overflow kebab menus, use `canvas-menu-button`. See Menu Button below. Misusing `canvas-dropdown` here breaks screen readers (wrong ARIA role), exposes unused form props (`name`, `value`), and confuses the visual convention (field styled trigger where a button is expected).

## Menu Button

Use `canvas-menu-button` when a button opens a small list of actions, not a selection of values. The WAI ARIA pattern is "Menu Button", the element exposes `role="menu"` with `role="menuitem"` children, and each option fires a `select` event carrying `value` and `label` rather than contributing to a form.

When to use.

- **Plus button with a list of things to add.** "Add note", "Add task", "Add diagnosis" triggered from a single plus icon that opens a menu below. Common in list headers where multiple creation flows share one entry point.
- **Row action menu (kebab or ellipsis).** Edit, Duplicate, Archive, Delete on table rows, list rows, and card headers. Pair with `align="end"` so the menu opens toward the row's right edge.
- **Overflow menu.** When a toolbar has more actions than fit, collapse the tail into a kebab trigger that opens a menu of the remaining actions.
- **Split actions by category with section dividers.** Place `<hr>` between `canvas-option` children to group related actions, for example "Edit, Duplicate" in one section and "Archive, Delete" in the next.

When not to use.

- **Selecting a value that lives in form state.** Use `canvas-dropdown`, `canvas-combobox`, or `canvas-multi-select` instead. The menu button emits discrete actions, not a settable value.
- **More than one interactive control in the popover.** If the popover needs checkboxes, date inputs, or any form beyond a list of actions (filter panels, preference sheets, legends), `canvas-menu-button` is the wrong primitive. Use `canvas-popover` instead, it is the generic anchored container for arbitrary content.
- **Navigation between pages or routes.** A link or tab bar covers this. A menu button dispatches in-page actions.
- **Two actions or fewer.** Render them as side by side `canvas-button` elements instead of hiding them behind a menu. The menu button earns its place once there are three or more peers.

Trigger rules.

- The default trigger (when no `slot="trigger"` child is provided) is a ghost button reading "Actions" with a caret. Use this for generic overflow menus.
- Slot a `canvas-button` when the trigger is an icon button, a primary add button, or anything beyond the generic default. Keep the slotted trigger at `variant="ghost"` and `size="sm"` for toolbar and row contexts. Primary (green) or secondary (blue) triggers are reserved for the plus button that represents the single primary creation affordance on the page.
- Icon only triggers must carry `aria-label`. The default ghost trigger already wires `aria-haspopup="menu"` and `aria-expanded` automatically, slotted custom triggers inherit these contracts from the component, the only gap you fill is the accessible name.

Placement rules.

- Leave `direction` and `align` unset for the default auto placement. The component measures viewport space on open and flips up or right aligns only when the menu would clip.
- Set `direction="up"` or `direction="down"` only when the auto decision is wrong for a known layout constraint, for example a menu button pinned to a fixed bottom toolbar where the menu must always open upward regardless of viewport state.
- Set `align="end"` on row action menus (kebab menus in the right cell of a table row) so the menu hugs the row's right edge instead of extending past it.

Option rules.

- Each `canvas-option` carries a `value` attribute that identifies the action in the `select` event. Keep values short and stable (`edit`, `duplicate`, `archive`, `delete`). Treat them as action identifiers, not human strings.
- Option text is the verb ("Edit") or verb plus object ("Mark as completed"). Avoid compound labels that read like a sentence. Long labels force wrapping and slow scanning.
- Disable individual options with the `disabled` attribute when the action is contextually unavailable. Do not hide options conditionally if their availability changes frequently, the shifting menu length confuses muscle memory. Hide only when the option is structurally impossible in the current flow.
- Place destructive actions (Delete, Remove, Revoke) last. Separate with a `<hr>` divider from non destructive actions above.

## Overlay family

Pick the right overlay before picking attributes. Rows in the table below map the interaction model and content shape to a component.

| Trigger and content | Component |
|---|---|
| Hover or focus, short non interactive text | `canvas-tooltip` |
| Click, three or more action items anchored to a toolbar button | `canvas-menu-button` |
| Click, arbitrary interactive content, surface tethered by width or edge alignment | `canvas-popover` without `pointer` |
| Click, arbitrary interactive content, surface floats free of the trigger or the anchor is ambiguous | `canvas-popover` with `pointer` |
| Click, full task that needs a backdrop, centered focus, and true modality | `canvas-modal` |

Tooltip and popover share the same speech balloon artwork and the same trigger to surface distance, but they carry different ARIA contracts. Tooltip is `role="tooltip"` with hover and focus triggers. Popover is `role="dialog"` with click triggers, explicit open state, and optional focus trap. Do not simulate a tooltip with a popover just to get the arrow, and do not stuff interactive content into a tooltip.

## Popover

Use `canvas-popover` when a button opens an anchored container with arbitrary content. It is the generic complement to `canvas-menu-button`, which is reserved for action menus. The ARIA contract is `role="dialog"` with `aria-modal="false"`, and the trigger carries `aria-haspopup="dialog"` plus `aria-expanded`.

When to use.

- **Filter forms.** Icon triggers that open a short form for narrowing a list, for example the note filter on the patient chart header or a table column filter. Icon only triggers are ambiguous on their own, set `pointer` to tether the surface to the trigger.
- **Column pickers.** Toolbar buttons that open a checkbox list for toggling table column visibility.
- **Legends and preference sheets.** Small explanatory panels anchored to an info icon or a settings button. Short body content, often a paragraph plus a key.
- **Bulk action panels.** Panels anchored to a selection summary with multiple controls (assign to, tag, change status) beyond what a menu button can represent.

When not to use.

- **Action menus.** Use `canvas-menu-button`. The options there map to `role="menuitem"` and the trigger is not carrying a dialog contract.
- **Form field selection.** Use `canvas-dropdown`, `canvas-combobox`, or `canvas-multi-select`. Those participate in form state and emit `change`.
- **Tooltips.** Short descriptive text on hover belongs in `canvas-tooltip`. Popovers are for click triggered interactive surfaces. If you want the speech balloon arrow on a click triggered callout, use `canvas-popover` with `pointer`.
- **Full page overlays and confirmations.** Use `canvas-modal` when the content needs centered focus, a backdrop, and true modality. Destructive confirmations, blocking flows, and anything the user must respond to before continuing belong in a modal. Popovers are non blocking, a user can always dismiss by clicking outside or pressing Escape.

Attribute rules.

- Always set `label`. It is required because `role="dialog"` needs an accessible name and the v1 popover has no composite header element to derive it from.
- Leave `direction` and `align` unset for the default auto placement. Direction picks the side with more room when content does not fit below. Alignment flips to end when the start edge would clip. Set explicitly only when a known layout constraint forces a side.
- Pick `size` based on the content. `sm` 280 px for short legends and compact checkbox lists. `md` 360 px for filter forms. `lg` 480 px for denser column pickers and bulk action panels. `auto` grows the surface to its content width up to the viewport, use for wide tables, long labels, or data whose width is known only at runtime. Override with `--canvas-popover-max-width` when the content has a known ideal width.
- Leave `dismiss-on-scroll` off by default. The popover follows the trigger on scroll and hides when the trigger leaves the viewport. Set `dismiss-on-scroll` only when any scroll should close the popover, for example a filter panel that becomes stale when the user scrolls the underlying table.

Pointer.

- Set `pointer` when the anchor is ambiguous, for example an ellipsis in a row of icon buttons, an inline disclosure anchored to a chip or table cell, or a small floating surface next to a cluster of peers. The speech balloon arrow is what tells the user which control opened the surface.
- Leave `pointer` off when the surface is visually tethered by width or edge alignment, for example a filter panel flush under a full width toolbar button, a column picker aligned to a table header, or a large preference sheet where a small arrow looks vestigial.
- The pointer does not change keyboard, ARIA, or dismissal behavior. It is a visual affordance only.

Content sizing and escalation.

- Keep the body to one logical group and up to four focused controls. Inputs, checkboxes, and date pickers count together. A date range made of two inputs bound to one label counts as one control. Action rows at the end do not count.
- Beyond that the popover stops reading as a quick action and starts reading as a form. Escalate to `canvas-modal`. Signals that you have crossed the line include more than four controls, multiple logical groups, side by side columns, or a scroll area inside the popover that appears outside edge cases.
- The popover is not a scroll container. When content may exceed the direction aware `max-height`, wrap the body in `canvas-scroll-area vertical` with an explicit `max-height` and an `aria-label`. Same contract as `canvas-card-body`. Never place `canvas-dropdown`, `canvas-combobox`, or `canvas-multi-select` directly inside the scroll area, their menu surfaces will clip. Place those outside the scroll area or restructure the content so the scroll is further in.

Trigger rules.

- Slot a `canvas-button` as the trigger. Ghost variant is the default for toolbar and row contexts. Primary or secondary triggers are reserved for the page's main popover opener, for example the chart filter icon.
- Icon only triggers must carry `aria-label`. The component wires `aria-haspopup="dialog"` and toggles `aria-expanded` on the slotted trigger automatically.

Content rules.

- Keep the popover focused on a single task. Filter form, not filter plus sort plus export.
- Wrap content in a flex column when stacking multiple controls so they do not flow side by side.
- Action rows sit at the end of the body as a flex row aligned to the end, ghost Cancel then primary action button.

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

## Cards and Content Containers

- Use `canvas-card` as the default elevated content container on a gray page background. White surface, soft border, standard shadow. Good for summary panels, detail views, note blocks, and any grouping that needs visual separation from the page.
- **The four property signature is the primary card imitation detector.** Any element combining background, border, border-radius, and box-shadow on itself is a `canvas-card` imitation, regardless of class name. When a CSS rule or inline style puts those four properties on one element, stop and use `canvas-card` instead. The component handles all four automatically and stays aligned with Canvas visual updates.
- **Class names are secondary signals.** Names historically used for card styling include `card`, `panel`, `box`, `tile`, `container`, `filters`, `filter-bar`, `toolbar`, `section`, `wrapper`, `wrap`, `header`. Flag these when they appear with the four property signature. Do not restrict the detector to a fixed class name list. Exception, class names where a word refers to something unrelated, for example `card-number-input` is a payment input, not a card container.
- **Adjacent region pattern.** Two adjacent containers where one has `border-top: none` and visually connects to another through a shared `border-radius` are always a multi region card. Replace the pair with `canvas-card` containing `canvas-card-body` for the upper region and `canvas-card-footer` for the lower region, or stacked `canvas-card-body` elements when the second region is still content.
- Use `canvas-card-body` for padded content regions inside the card. Stack multiple `canvas-card-body` elements for sections that need internal dividers (history, assessment, plan). Adjacent bodies get a border between them automatically.
- Use `canvas-card-footer` for gray action rows at the bottom of a card. Place primary and ghost buttons here. Do not create a raw div with a gray background under the card body.
- Add the `raised` attribute when a card needs to pop against similar surfaces, such as a selected card in a list or the card hosting the primary action on the page.
- Use `no-padding` on `canvas-card-body` only when content needs edge to edge treatment, such as a full width table or image.
- For unstyled flat grouping with no border or shadow, do not use `canvas-card`. Use a plain div with spacing tokens. The card is for elevated surfaces, not semantic grouping.
- `canvas-card-body` is not a scroll container. Setting `max-height` on the body does not activate scrolling in 4.0.0 and later. Wrap scrollable content in a `canvas-scroll-area`. See the Scroll Areas section below.

## Table Behavior in Narrow Containers

Plugins render in different surface widths. A full page plugin has room for wide tables. A right chart pane plugin is roughly 25% to 40% of the viewport. Tables need to handle both cases.

- **Prefer fewer columns in narrow surfaces.** Before reaching for horizontal scroll, ask whether every column is necessary. Drop low-value columns (IDs, secondary dates, metadata) and show them in a detail view or tooltip instead.
- **Use horizontal scroll when columns cannot be reduced.** Wrap the table in `<canvas-scroll-area horizontal>` and set `min-width` on the table. The container scrolls horizontally while the page stays fixed. This is better than squishing columns into unreadable widths.
- **Use compact padding in narrow surfaces.** The `.table-compact` modifier tightens padding without changing font size, giving each column more room.
- **Combine compact and scroll for dense data.** A claims table with 6 columns in a sidebar can use `.table-compact` inside `<canvas-scroll-area horizontal>` with a `min-width` that ensures each column has enough room.
- **Do not hide columns with CSS media queries.** The plugin iframe width does not correspond to viewport breakpoints. A right chart pane can be 400px wide on a 1920px monitor. Media queries based on viewport width will not trigger correctly. Instead, design the table for the surface it will render in.

## Inline Form Rows

A horizontal row of form elements sharing a visual row. The primitive for filter bars, inline edits, search bars, and toolbar forms. Use `canvas-inline-row` as the container. The component encapsulates the flex layout, gap, bottom alignment, wrap behavior, and per child flex sizing so the erroneous state (elements overflowing the card, truncation, mismatched heights) is unreachable.

Rules that apply to every inline form row.

- Wrap the row in `canvas-inline-row`. The component handles `display: flex`, `gap`, `align-items: flex-end`, `flex-wrap: wrap`, and the per child flex rules that let inputs grow while buttons keep natural width.
- Use default size on every form element in the row. No `size="sm"` anywhere. See Same Row Height Cohesion for why mixing sizes breaks alignment.
- Label every form element through the component `label` prop. Do not mix component labels with external `<label for>` tags. The component label ships with the correct spacing and semantics.
- Use `canvas-input` for every input including `type="date"`, `type="time"`, and `type="number"`. Never use native `<input>` tags. See the native input prohibition in Text Inputs vs Textareas.
- Use `canvas-dropdown` for fixed option lists, `canvas-combobox` for searchable long lists, `canvas-multi-select` for multi pick rows.

Use cases. Each extends the primitive with ingredients specific to that pattern.

- **Filter bar above a table.** Wrap the `canvas-inline-row` inside a `canvas-card-body`. If the table has bulk actions, add a second `canvas-card-body no-padding` for the table and a `canvas-card-footer` for the selection count on the left and action buttons on the right. Use `canvas-input type="date"` for date range fields.
- **Inline edit form.** Sits inside an existing `canvas-card-body` on a detail view. The row ends with a primary Save button and a ghost Cancel button. No card wrapper around the row itself.
- **Search bar.** Row with a text input plus a search button, optionally with filter dropdowns. No card wrapper. Lives in a page header region or toolbar area.
- **Action bar.** Context text or selection count on the left, one or two action buttons on the right. Use a plain div with flex when the action bar stands alone. When the action bar is attached to a card below a table, use `canvas-card-footer` instead.

The copy-paste filter bar markup lives in [patterns.md](patterns.md) Filter Bar.

Narrow surfaces. `canvas-inline-row` wraps automatically when the row cannot fit. Every growing child (input, dropdown, combobox, multi-select, textarea) keeps at least 160 px width before wrapping. Override the minimum with `style="--canvas-inline-row-item-min: 140px"` on the row for compact contexts that must stay on one line.

When not to use `canvas-inline-row`. Horizontal scrollers such as chip strips (use `canvas-scroll-area horizontal`), tab bars (use `canvas-tabs`), vertical stacks (use a plain flex column or block flow), right aligned action clusters inside a card footer (use `canvas-card-footer` directly with a plain div using `justify-content: space-between`), or single element rows (render the element directly). See `web-components.md` canvas-inline-row for the full reference.

## Scroll Areas

Use `canvas-scroll-area` whenever content needs to scroll inside a bounded region. The component is direction agnostic and opts into scrolling through the `vertical` and `horizontal` attributes. Without either attribute the component is a transparent block that grows to content.

- Use `vertical` for long lists, activity logs, and constrained content columns. Set `max-height` via inline style.
- Use `horizontal` for wide tables that should scroll sideways without scrolling the page. Set `min-width` on the inner content so the container has something to scroll to.
- Use both attributes together when content is wide and tall (for example a dense data grid). Set `max-height` and `max-width` on the scroll area.
- Always provide `aria-label` or `aria-labelledby` that names what is scrolling. The component auto applies `tabindex="0"` when a direction is set so keyboard users can focus the region, and the label is what a screen reader announces.
- Do not add `overflow-y: auto` or `overflow-x: auto` on plugin level divs. If a raw div needs to scroll, replace it with a `canvas-scroll-area`. The component is the single canonical way to opt into scrolling.
- Do not place `canvas-dropdown`, `canvas-combobox`, or `canvas-multi-select` inside a `canvas-scroll-area[vertical]`. The menu surface of these components gets clipped by the scroll area's overflow. Place them outside the scroll area, or restructure the layout so the scroll is further out. Tooltips are exempt because they hide on scroll. This restriction is lifted in a later release when popup components move to the browser top layer.
- For scrolling inside a `canvas-card-body`, put the scroll area inside the body. The body no longer scrolls on its own. See the canvas-scroll-area section in [web-components.md](web-components.md) for the migration pattern.

## Buttons

Follow the button color rules in SKILL.md. A screen should have at most one green button. When in doubt, use blue.

- **Button sizing.** Three layout patterns determine the size tier.
  - **Input-paired buttons** (button in the same row as an input, forming a visual unit like "Add" next to a text field). Match the input height. Standard inputs are ~43px, so use base `canvas-button`. If the form uses compact inputs, use `size="sm"`. Never use `size="xs"` for input-paired buttons because the height mismatch looks broken.
  - **Floating utility buttons** (button near a field but not height-paired, like "+ Insert Field" above a textarea or "Clear" on a filter tag). Use `size="xs"`. These should not compete visually with the content they support.
  - **Table row buttons** ("Retry", "Edit", "View" in table cells). Use `size="sm"` for standard tables. Use `size="xs"` for compact tables. If the action is a simple text link (like "Remove" in a data row), a ghost text link may work better than a button. The goal is that the button does not inflate the row height. Table action buttons should be their natural width and right-aligned in the cell using the `cell-actions` class. Never stretch buttons to fill the cell width. When buttons in the same column vary in text length ("Edit" vs "Reschedule"), each button keeps its own width.
- Place the main action on the right side of a button group. Place cancel or back on the left.
- Use `variant="ghost"` for actions that are available but not encouraged (reset, clear filters, cancel).
- Destructive actions always require a confirmation step. Never put a `variant="danger"` button directly next to the main action button. Either move it to a separate section, use `variant="ghost"` to visually downplay it, or add a confirmation dialog.
- If the action navigates the user away from the current screen, make that clear. Use a link or indicate the destination. Never silently redirect after a button click.

## Same Row Height Cohesion

Form elements sharing a visual row must render at the same height. This covers `canvas-input`, `canvas-dropdown`, `canvas-combobox`, `canvas-multi-select`, and `canvas-button` when placed side by side in a filter bar, inline form, or action cluster.

- The `size` attribute is not a universal height tier across components. `canvas-button[size="sm"]` renders at 36 px min-height. `canvas-dropdown[size="sm"]` only reduces the trigger font size and inherits default padding, so it renders shorter than the button. Matching the `size` attribute does not guarantee matching rendered height.
- Do not mix `size="sm"` and default in the same row. Pick one tier for the whole row.
- The safe baseline for filter bars and inline forms is default size on every element in the row. This produces matching heights by construction.
- Reserve `size="sm"` for rows where every element is a button, for example a table action cluster with two or three ghost buttons in a cell.
- If a row must use `sm` and includes a dropdown, combobox, or input, verify rendered heights in a browser and align them through the component `min-height` CSS custom property. Do not ship untested size mixes.

See Form Element Height Cohesion below for the custom height case where the user has asked for a non default size on any element in the row.

## Form Element Height Cohesion

When the user requests a custom height on any form element (text input, `canvas-dropdown`, `canvas-combobox`, button) in a specific context (a card, a sidebar section, a modal form, a toolbar row), match the height of all sibling form elements in that same group. If a text input is made shorter to fit a compact sidebar, the dropdown next to it and the button beside it should shrink to the same height. This applies to elements that are visually grouped, on the same row or in the same form section. It does not mean changing the default dimensions globally across the whole plugin. The default sizes stay the same everywhere else. Only the local group of elements should be cohesive.

See Same Row Height Cohesion above for the baseline rule that applies to every row regardless of custom height.

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

## Confirmation Hierarchy

Not all consequential actions are destructive. Clinical workflows include actions that are irreversible or have real-world impact without being "delete" operations. Use this hierarchy to decide when confirmation is needed.

- **No confirmation needed.** Saving a draft, toggling a UI preference, filtering a list, expanding or collapsing a section. These are low-risk and easily reversible.
- **Soft confirmation (undo banner).** Closing a care gap flag, dismissing an alert, marking a task complete. Show an inline banner with an undo option for 5 seconds. The action takes effect immediately but can be reversed.
- **Hard confirmation (dialog).** Sending a message to a patient, submitting a referral, signing a note, overriding a clinical alert. These leave the plugin's scope and affect external systems or the patient record. Show a confirmation dialog that names the specific action and its consequence.
- **Destructive confirmation (dialog with typed input).** Deleting patient-facing data, removing a medication, canceling an order. Show a confirmation dialog that requires the user to type "delete" or the item name before proceeding.

## Badges

- Use **mini** (`size="mini"`) as the default size for all status indicators in tables, cards, lists, and accordion titles. This is the size Canvas uses most frequently.
- Use **tiny** or **small** only when the badge needs to be more prominent, like a standalone tag or a primary visual element.
- Use the **solid color** variants (`canvas-badge` with a color attribute like `green`, `red`, etc.) for status display. White text on a colored background. Matches the status labels used throughout the Canvas home-app.
- Use the **basic** variant (add the `basic` attribute) for de-emphasized or neutral statuses like "Inactive", "Self-pay", or "Draft" where a solid color would be too visually heavy.
- Use the **circular** variant (add the `circular` attribute) for notification counts. Short content renders as a circle, longer content stretches into a pill.
- Match colors to semantic meaning consistently. See [DESIGN.md](../DESIGN.md) Badge Color Semantics for the full mapping.
- Follow the palette closure rule in [DESIGN.md](../DESIGN.md) Color Palette and Roles when choosing badge colors.

## Chips

- A chip is a badge the user can dismiss. Same visual base, same colors, same sizes. Use chips when the user can remove the item. Use badges when the item is read-only.
- Use chips for **filter bars** where the user removes active filters by clicking the dismiss button. Pair with a "Clear all" ghost button at the end.
- Use chips for **tag inputs** where the user adds and removes tags. Place chips above or beside the text input. New chips are created via JS when the user types and presses enter.
- Use chips for **multi-select display** where selected items from a dropdown or combobox are shown as removable chips.
- The dismiss button uses an SVG X icon (8x8, stroke-linecap round) that inherits the chip text color. Do not use the `&times;` HTML entity as it does not center correctly across font sizes.
- Include a single dismiss event listener on a parent container using event delegation, not individual handlers on each chip.
- When a chip is dismissed, remove it from the DOM. Update any backing data state (filter list, selected values, tag array) in the same handler.

## Empty States

Empty is not one pattern. The cause of the emptiness drives both the copy and the available action, and picking the wrong type produces a dead end for the user. Every list, table, or data section that can render zero rows needs a typed empty state, never a blank container.

### Types

Four types cover every plugin surface. Agents pick one based on why the container is empty right now.

- **First use.** The user has never added data here. The section will eventually fill through this plugin's own flows. Copy explains what lives here once populated. Primary action is the first add flow, for example "Add first medication".
- **User cleared.** Data existed, the user removed it all (bulk delete, archive, dismiss). Copy confirms the cleared state. Primary action is the add flow, secondary ghost action may restore if the plugin keeps a restore affordance.
- **Filter no results.** Underlying data exists, the current filter or search term excludes everything. Copy names that filters are active. Primary action is a ghost "Clear filters" button, secondary is guidance to adjust the filter.
- **Load error.** A fetch failed. Do not reuse the centered empty pattern. Render a `canvas-banner` with `variant="error"` and a retry affordance so the user can tell a failed load from a true empty. See Error Banners for variant rules.

### Content hierarchy

Every empty state follows the same three part order. Omit the third part only when the user cannot take an action from this surface.

1. A heading that names what is missing ("No medications recorded", "No results match your filters").
2. One line of supporting text that explains why or what to expect next.
3. One primary action button when the user can do something about it. A secondary ghost button is optional.

One line only empty states are acceptable inside tight containers like card bodies narrower than 300 pixels. Everywhere else, use the full hierarchy.

### Voice

- **Be specific.** Name the domain object, not "data" or "results". "No medications recorded" reads as clinical. "No data found" reads as a bug.
- **Be action oriented.** Button labels start with a verb tied to the task, "Add first medication", "Clear filters", "Invite team member". No "Click here", no "Learn more".
- **Be educational on first use, blunt on filter no results.** First use is the one moment where explaining what lives here pays off. Filter no results needs the escape, not a lesson.
- **For prose beyond empty states**, see [writing-style.md](writing-style.md) for the full copy rules and the clinical vocabulary carve out.

### Clinical nuance

- **Distinguish recorded from not recorded.** A blank list does not mean the patient has no allergies, it means nothing is recorded. Prefer "No allergies recorded" over "No allergies". The difference matters clinically.
- **Do not assert clinical meaning the data does not support.** Copy stays factual about what the plugin knows. Leave clinical interpretation to the user.

### Loading, empty, error state machine

For the four-state gating rules (loading, populated, empty, error), see [patterns.md](patterns.md) Loading, Empty, Error State Machine.

### Accessibility

- Use a semantic heading element inside the empty container (`<h3>` or the appropriate level for the surrounding page) so screen readers announce the state transition.
- For filter no results that replaces previously rendered rows, wrap the results region in `aria-live="polite"` so the change is announced without stealing focus.
- Keep the primary action reachable with one Tab from the surrounding filter bar or page header. Do not trap focus inside a decorative empty container.

See [patterns.md](patterns.md) Empty State for markup per type, and [anti-patterns.md](anti-patterns.md) Filter Without Escape and Empty State During Loading for the common pitfalls.

## Progress Indicators

- Use `canvas-progress` for any percentage visualization. Campaign completion, outreach tracking, match scores, goal attainment.
- Color is set by the consumer, not by the component. The component does not automatically change color based on the value. If the design needs red below 30% and green above 80%, set the color attribute from JavaScript based on the value.
- Use **default size** for standalone progress bars where the bar is the primary content. Use **small** for lists and compact layouts where progress sits alongside other data. Use **tiny** for inline indicators like search match scores.
- The `label` attribute shows the percentage inside the bar. Hide it at tiny size (the component does this automatically) and in contexts where an external label already shows the number.

## Dividers

- Use `canvas-divider` to visually separate content sections. A plain divider with no text renders a horizontal rule with 1rem vertical margin above and below.
- The horizontal-with-text variant is the most common divider in Canvas. Campaign lists, availability cards, change request cards, and diagnosis tables all use centered text between lines. Default to this variant when separating labeled content groups.
- Use the `fitted` attribute when the divider sits between tightly packed items and no extra spacing is needed (e.g., between condition detail rows or inside a table cell).
- Use `canvas-divider` with text content to create a labeled section break. The text sits centered between two lines. Good for separating groups of results ("Or"), toggling section visibility ("Hide closed campaigns"), or labeling time boundaries.
- Use the `hidden` attribute for invisible spacing in print layouts or contexts where vertical separation is needed without a visible line.
- Do not use `canvas-divider` to separate items inside a list or table. Use borders on the list items or table rows instead. The divider is for separating distinct content groups, not individual rows.

## Loading States

- Use `canvas-loader` for all loading states in plugins. It supports full-page overlay, inline section loading, and compact indicators.
- If a specific section is loading while the rest of the page is ready, show the loader only in that section rather than blocking the whole screen.
- Do not leave the screen blank during loads.
- There is no skeleton component. Skeleton placeholders require layout-specific shapes (line widths, column counts, card dimensions) that vary per view. An AI agent generating plugins cannot guarantee that a skeleton preview will match the actual content layout, which creates visual inconsistency when the real content arrives. Use `canvas-loader` instead.

## Form Layout

- Stack form fields vertically with `12px` between them. Do not place unrelated fields side by side unless they are logically paired (first name and last name, city and state).
- Group related fields under a shared heading or within a card. If a form is long enough to scroll, it must have grouping.
- Place the submit button below the last field, separated by `16px`. Align it to the left or stretch it full width in narrow containers.
- Don't use modals for complex forms. If a form has more than 3 or 4 fields, it should be a page or a panel section, not a modal. Modals are for confirmations, single-field edits, and quick selections.

## Read-Only vs Editable Content

- When mixing display and edit on the same screen, make it visually obvious which parts are interactive. Read-only values use plain text. Editable values sit inside input fields with visible borders.
- Keep action placement consistent. If the save button is bottom-right on one screen, it should be bottom-right on every screen in the same plugin.

## Sidebar Width Awareness

- Plugins in `RIGHT_CHART_PANE` are narrow (roughly 25% to 40% of the viewport). Avoid horizontal layouts, multi-column forms, and wide tables in sidebar plugins. Stack everything vertically. See [surface-selection.md](surface-selection.md) for all surface options and their constraints.
- Full-page plugins (`PAGE`) have more room and can use multi-column layouts where appropriate.

## Tooltips

- Use tooltips for supplementary information the user does not need to see unless they hover. Ambiguous icon labels, truncated text expansion, disabled state explanations.
- Do not add tooltips when the element is already clear by itself. A button labeled "Save", a close X, a trash icon, a back arrow, and a search magnifier do not need tooltips. Adding them clutters the UI without helping the user.
- Icon-only buttons need a tooltip when the icon alone does not make the action obvious. A gear, lightning bolt, clipboard, or any domain-specific icon needs a tooltip to explain the action. Universal icons (close, delete, back, search) are exempt from the tooltip but still need `aria-label` for screen readers.
- Truncated table cells should have a tooltip with the full text. When a cell uses `text-overflow: ellipsis`, the tooltip shows the complete value on hover.
- Disabled elements should explain why they are disabled. Use an inverted tooltip with a delay to tell the user what condition must change before the element becomes active.
- Do not put essential information in tooltips. If the user must see it to complete a task, it should be visible text, not hidden behind a hover.
- Do not use tooltips as error messages or validation feedback. Errors should be visible inline via `canvas-input` error state or `canvas-banner`. Tooltips are hidden until hover and can be missed entirely.
- Do not use tooltips for touch-only contexts. Tablets do not have hover. If the plugin runs in a right chart pane where clinicians may use a tablet, ensure all information is accessible without hover.
- Do not add tooltips to elements inside a scrollable area the user drags or swipes. The scroll listener hides tooltips immediately, so they will flash and disappear.
- Keep tooltip text short. One line, two at most. If you need a paragraph or interactive content, use `canvas-popover` with `pointer` instead, it shares the tooltip's speech balloon artwork but supports click triggers and arbitrary content.
- Use the inverted (dark) variant for disabled state explanations and secondary hints. Use the default (light) variant for primary content like truncated text expansion.
- Add `data-canvas-tooltip-delay="1000"` for disabled state explanations so the tooltip does not flash when the user moves past the element quickly.
- When a table row has multiple icon-only action buttons (edit, delete, view), each needs its own tooltip. Place them with enough gap that tooltips do not overlap when hovering adjacent buttons quickly.

## Sortable List and Cross List Drag and Drop

- Use `canvas-sortable-list` for any list the user can reorder. Do not hand roll drag and drop or use a third party library. The component owns pointer handling, FLIP animation, auto scroll during drag, keyboard reorder, and ARIA announcements.
- Give two or more lists the same `group` value when items need to move between them. Kanban columns, archive flows, inbox and done buckets, and template palettes are the main fits. Same string on every participating list, case sensitive.
- Leave items as plain `canvas-sortable-item`. Content goes in the default slot. No extra attributes per item are required for cross list to work.
- When a list must stay stationary and only receive from another source, set `accept` with the source group name and omit `group` on the receiver.
- When the source is a palette of reusable templates, set `pull="clone"` on the palette. Items drop as copies into the target and the original stays in the palette.
- Prefer a plain Move to X button in a menu when there are only two lists and moves are rare. Cross list drag is heavier visually than a button. Reserve it for flows where spatial arrangement of columns carries meaning, such as a kanban board or a schedule editor.
- Do not wrap a sortable list in anything that intercepts pointer events. The handle must receive `pointerdown` through to the component.

## Single Drop vs Bulk Changes

- **Single drop.** Fire an API call on every `move` or `reorder` event. Use when lists are short and the backend is fast. Revert the last move from a catch block if the request fails.
- **Bulk.** Accumulate `change` events in a `Map` keyed by item id. Save flushes as one payload, either on a Save button or after a debounced timer. Use when lists are long, the backend exposes a bulk endpoint, or the user wants to arrange several cards before committing. The Map collapses repeated moves of the same item so only the latest position ships.
- Validation that cannot be expressed on the client but must not let the user visually commit belongs in a `beforemove` or `beforereorder` handler that calls `preventDefault()`. Always pair a cancel with a toast or inline message explaining why the move was refused.

## Anti-Patterns

For visual anti-patterns (off-palette colors, box-shadow borders, custom scrollbars, CSS media queries), see [DESIGN.md](../DESIGN.md) Do's and Don'ts.
