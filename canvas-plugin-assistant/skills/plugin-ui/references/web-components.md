# Web Components

Reference for the Canvas plugin web component system. The system registers 28 components spanning 47 tag names (the count that includes shared children like `canvas-option` and subcomponents like `canvas-card-body`, `canvas-tab-panel`, `canvas-modal-header`). Authoritative count for the skill. Other files point here rather than stating a number. This file covers how components load and the API, keyboard, ARIA, and visual spec for each component. For the token system, palette, typography, spacing, shape, pairing, and hierarchy rules, see [DESIGN.md](../DESIGN.md). For setup and serving, see [setup.md](setup.md).

## Contents

[Layout](#layout) | [Components](#components)

**Components.** [canvas-button](#canvas-button) | [canvas-button-group](#canvas-button-group) | [canvas-badge](#canvas-badge) | [canvas-chip](#canvas-chip) | [canvas-input](#canvas-input) | [canvas-textarea](#canvas-textarea) | [canvas-radio](#canvas-radio) | [canvas-checkbox](#canvas-checkbox) | [canvas-toggle](#canvas-toggle) | [canvas-banner](#canvas-banner) | [canvas-card](#canvas-card) | [canvas-inline-row](#canvas-inline-row) | [canvas-scroll-area](#canvas-scroll-area) | [canvas-dropdown](#canvas-dropdown) | [canvas-combobox](#canvas-combobox) | [canvas-multi-select](#canvas-multi-select) | [canvas-menu-button](#canvas-menu-button) | [canvas-popover](#canvas-popover) | [canvas-tabs](#canvas-tabs) | [canvas-accordion](#canvas-accordion) | [canvas-modal](#canvas-modal) | [canvas-table](#canvas-table) | [canvas-sortable-list](#canvas-sortable-list) | [canvas-sidebar-layout](#canvas-sidebar-layout) | [canvas-loader](#canvas-loader) | [canvas-progress](#canvas-progress) | [canvas-tooltip](#canvas-tooltip) | [canvas-divider](#canvas-divider)

## Loading Components

All setup and serving instructions (SimpleAPI routes, `StaffSessionAuthMixin`, CSP requirements, the three head tags, the HTML boilerplate, `CanvasUI.utils` host communication bridge) live in [setup.md](setup.md). Read `setup.md` before authoring any `<canvas-*>` markup.

## Layout

Components are custom HTML elements. Standard CSS layout properties work directly on the element with no special API.

```html
<!-- full width -->
<canvas-button style="width: 100%">Save</canvas-button>

<!-- fixed dimensions -->
<canvas-button style="width: 200px; height: 60px">Save</canvas-button>

<!-- flex participation -->
<div style="display: flex; gap: 12px">
  <canvas-button variant="ghost">Cancel</canvas-button>
  <canvas-button style="flex: 1">Save</canvas-button>
</div>

<!-- margin -->
<canvas-button style="margin-top: 16px">Save</canvas-button>
```

The internal button fills the host element (`width: 100%; height: 100%`), so sizing the custom element sizes the visible button.

## Components

### canvas-button

A button with four color variants, three sizes, and disabled state. Renders a native `<button>` inside Shadow DOM.

**Usage**

```html
<canvas-button>Save</canvas-button>
<canvas-button variant="primary">Sign and Lock</canvas-button>
<canvas-button variant="ghost">Cancel</canvas-button>
<canvas-button variant="danger">Delete</canvas-button>
<canvas-button size="sm">Edit</canvas-button>
<canvas-button variant="ghost" size="xs">Clear</canvas-button>
<canvas-button disabled>Unavailable</canvas-button>
<canvas-button type="submit">Submit Form</canvas-button>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `variant` | `primary`, `secondary`, `ghost`, `danger` | `secondary` |
| `size` | `sm`, `xs` | base |
| `disabled` | boolean | `false` |
| `type` | `button`, `submit` | `button` |

**Slot.** Default slot accepts any content (text, icons, mixed). Layout is `inline-flex` with a gap.

```html
<canvas-button>
  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
    <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  </svg>
  Add Patient
</canvas-button>
```

**Variant rules.** These match the existing Canvas design system rules and are not changed by the web component migration.

- **primary** (green) is for clinical state transitions that affect the patient record or leave the system. Sign/lock a note, send a message to a patient, submit a referral, confirm a fax, check in a patient. Most screens will not have a primary button.
- **secondary** (blue) is the default. Save, done, next, add, update, edit, adjust, refill, back.
- **ghost** (gray) is for cancel, dismiss, close, and other neutral actions. This is the gray `#e0e1e2` button, not a transparent style.
- **danger** (red) is for destructive actions. Always require confirmation.

**Size rules.**

- **base** for primary page actions (save, submit, confirm).
- **sm** for card headers and table row actions where every element in the row is a button. For toolbars and inline form rows that include dropdowns, comboboxes, or inputs, use default size on every element in the row. See Inline Form Rows and Same Row Height Cohesion in component-usage.md.
- **xs** for floating utility actions not paired with an input. Normal weight (400), no min-height.

**Form submission.** A button with `type="submit"` finds the closest `<form>` ancestor and calls `requestSubmit()` on click. The component crosses the shadow DOM boundary to find the form.

**Component tokens**

| Token | What it controls | Fallback chain |
|---|---|---|
| `--canvas-button-bg` | Secondary/default background | `--color-secondary` then `--palette-blue` then `#2185D0` |
| `--canvas-button-color` | Secondary/default text | `#fff` |
| `--canvas-button-primary-bg` | Primary variant background | `--color-primary` then `--palette-green` then `#22BA45` |
| `--canvas-button-primary-color` | Primary variant text | `#fff` |
| `--canvas-button-ghost-bg` | Ghost variant background | `#e0e1e2` |
| `--canvas-button-ghost-color` | Ghost variant text | `rgba(0, 0, 0, 0.6)` |
| `--canvas-button-ghost-hover-bg` | Ghost hover background | `#cacbcd` |
| `--canvas-button-ghost-hover-color` | Ghost hover text | `rgba(0, 0, 0, 0.8)` |
| `--canvas-button-danger-bg` | Danger variant background | `--color-danger` then `--palette-red` then `#BD0B00` |
| `--canvas-button-danger-color` | Danger variant text | `#fff` |
| `--canvas-button-padding` | Base size padding | `.67857143em 1.5em` |
| `--canvas-button-padding-sm` | Small size padding | `.58928571em 1.125em` |
| `--canvas-button-padding-xs` | Extra small size padding | `.5em .85714286em` |
| `--canvas-button-font-size` | Base font size | `1rem` |
| `--canvas-button-font-size-sm` | Small font size | `.92857143rem` |
| `--canvas-button-font-size-xs` | Extra small font size | `.78571429rem` |
| `--canvas-button-font-weight` | Font weight | `--font-weight-bold` then `700` |
| `--canvas-button-font-family` | Font family | `--font-family` then `lato, ...` |
| `--canvas-button-radius` | Border radius | `--radius` then `.28571429rem` |
| `--canvas-button-border` | Border | `1px solid transparent` |
| `--canvas-button-gap` | Gap between slot children | `--space-tiny` then `8px` |
| `--canvas-button-transition` | Transition duration | `--transition-fast` then `200ms` |
| `--canvas-button-focus-ring` | Focus outline | `--focus-ring` then `2px solid #2185D0` |
| `--canvas-button-focus-ring-offset` | Focus outline offset | `--focus-ring-offset` then `2px` |

**File.** `assets/canvas-plugin-ui.js`

### canvas-button-group

A layout wrapper that joins `canvas-button` children into a single connected unit. Removes inner border-radius so buttons sit flush with shared edges. Only the first and last buttons keep their outer radius.

**Usage**

```html
<canvas-button-group>
  <canvas-button>Edit</canvas-button>
  <canvas-button>Duplicate</canvas-button>
  <canvas-button variant="ghost">Delete</canvas-button>
</canvas-button-group>

<canvas-button-group>
  <canvas-button>Done</canvas-button>
  <canvas-button variant="ghost">Close</canvas-button>
</canvas-button-group>

<canvas-button-group fluid>
  <canvas-button>Back</canvas-button>
  <canvas-button>Today</canvas-button>
  <canvas-button>Next</canvas-button>
</canvas-button-group>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `fluid` | boolean | false (when set, stretches to full width with equal button sizing) |

**How it works.** The wrapper sets `--canvas-button-radius` on slotted children via `::slotted(canvas-button)` selectors. First child gets left-side radius, last child gets right-side radius, middle children get zero. The `canvas-button` component already reads its border-radius from this custom property, so no changes to the button are needed.

**Button sizing.** Each button controls its own variant, size, and disabled state. The group does not override these. In fluid mode, buttons get `flex: 1 0 auto` to distribute equally.

**Slot.** Default slot accepts `canvas-button` elements only. Other elements will not receive radius adjustments.

**ARIA.** The inner container has `role="group"`. Add `aria-label` on the group when the purpose is not obvious from context.

**Component tokens**

| Token | What it controls | Default |
|---|---|---|
| `--canvas-button-group-radius` | Outer edge border radius | `--radius` then `.28571429rem` |

**File.** `assets/canvas-plugin-ui.js`

### canvas-badge

A status indicator with 13 colors, 4 sizes, a basic (outlined) variant, and a circular variant. Renders a `<span>` inside Shadow DOM. No JavaScript behavior, purely visual.

**Usage**

```html
<canvas-badge color="green" size="mini">Active</canvas-badge>
<canvas-badge color="red" size="mini">Denied</canvas-badge>
<canvas-badge color="blue" basic>Submitted</canvas-badge>
<canvas-badge color="red" circular size="mini">3</canvas-badge>
<canvas-badge>Default</canvas-badge>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `color` | red, orange, yellow, olive, green, teal, blue, violet, purple, pink, brown, grey, black | none (gray) |
| `size` | mini, tiny, small, large | base |
| `basic` | boolean | false |
| `circular` | boolean | false |

**Slot.** Default slot for text content.

**Size rules.**

- **mini** is the preferred size for status indicators in tables, cards, and lists. Default to mini unless the context demands larger.
- **tiny** for slightly more prominent status display.
- **small** for standalone badges where mini is too compact.
- **base** (no size attribute) and **large** are rarely used.

**Color semantics.** Common mappings used in Canvas.

| Color | Used for |
|---|---|
| green | Active, accepted, complete |
| red | Denied, error, inactive |
| blue | Submitted, pending, in progress |
| grey | Draft, done, archived |
| yellow | Pending review |
| orange | Warnings, preferred tags |
| teal | Scheduled |

**Basic variant.** White background with colored border and text. Use for de-emphasized statuses like "Inactive" or "Self-pay."

**Circular variant.** For count indicators. Single digits render as circles, longer text stretches into a pill shape.

**Color tokens.** Badge colors use the raw palette layer directly, not the semantic layer. Changing `--palette-green` shifts green badges. Changing `--color-primary` does not affect badges.

**Component tokens**

| Token | What it controls | Fallback chain |
|---|---|---|
| `--canvas-badge-bg` | Default (no color) background | `#e8e8e8` |
| `--canvas-badge-color` | Default (no color) text | `rgba(0, 0, 0, 0.6)` |
| `--canvas-badge-{color}-bg` | Specific color background | `--palette-{color}` then hardcoded hex |
| `--canvas-badge-{color}-color` | Specific color text | `#fff` |
| `--canvas-badge-padding` | Padding | `.5833em .833em` |
| `--canvas-badge-font-size` | Base font size | `.85714286rem` |
| `--canvas-badge-font-size-mini` | Mini font size | `.64285714rem` |
| `--canvas-badge-font-size-tiny` | Tiny font size | `.71428571rem` |
| `--canvas-badge-font-size-small` | Small font size | `.78571429rem` |
| `--canvas-badge-font-size-large` | Large font size | `1rem` |
| `--canvas-badge-font-weight` | Font weight | `--font-weight-bold` then `700` |
| `--canvas-badge-font-family` | Font family | `--font-family` then `lato, ...` |
| `--canvas-badge-radius` | Border radius | `--radius` then `.28571429rem` |
| `--canvas-badge-border` | Border | `0 solid transparent` |

**File.** `assets/canvas-plugin-ui.js`

### canvas-chip

A dismissible tag element for filters, selections, and tags. Always shows an X dismiss button. For non-dismissible status indicators, use `<canvas-badge>` instead. Shares the same 13 color palette as badge via `--palette-*` tokens. Changing a palette color shifts both badges and chips of that color.

**Usage**

```html
<canvas-chip color="blue">Provider: Dr. Magee</canvas-chip>
<canvas-chip color="blue" size="small">Status: Active</canvas-chip>
<canvas-chip>Diabetes</canvas-chip>
<canvas-chip basic color="red">Inactive</canvas-chip>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `color` | red, orange, yellow, olive, green, teal, blue, violet, purple, pink, brown, grey, black | none (gray) |
| `size` | mini, tiny, small | base |
| `basic` | boolean | false |

**Slot.** Default slot for text content.

**Dismiss event.** Clicking the X button fires a `dismiss` CustomEvent that bubbles and crosses shadow DOM boundaries (`composed: true`). The component does not remove itself. The consumer handles removal.

```html
<div id="filters">
  <canvas-chip color="blue">Cardiology</canvas-chip>
  <canvas-chip color="blue">Dr. Magee</canvas-chip>
</div>

<script>
document.getElementById('filters').addEventListener('dismiss', function(e) {
  e.target.remove();
});
</script>
```

**Filter bar pattern.** Chips with a clear all button.

```html
<div style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center">
  <canvas-chip color="blue" size="small">Status: Active</canvas-chip>
  <canvas-chip color="blue" size="small">Provider: Dr. Magee</canvas-chip>
  <canvas-button variant="ghost" size="xs">Clear all</canvas-button>
</div>
```

**Dynamic chip creation.**

```html
<script>
var chip = document.createElement('canvas-chip');
chip.setAttribute('color', 'blue');
chip.textContent = 'New Filter';
container.appendChild(chip);
</script>
```

**Component tokens**

| Token | What it controls | Fallback chain |
|---|---|---|
| `--canvas-chip-bg` | Default (no color) background | `#e8e8e8` |
| `--canvas-chip-color` | Default (no color) text | `rgba(0, 0, 0, 0.6)` |
| `--canvas-chip-{color}-bg` | Specific color background | `--palette-{color}` then hardcoded hex |
| `--canvas-chip-{color}-color` | Specific color text | `#fff` |
| `--canvas-chip-padding` | Padding (asymmetric, see note) | `.5833em .708em .5833em .833em` |
| `--canvas-chip-font-size` | Base font size | `.85714286rem` |
| `--canvas-chip-font-size-mini` | Mini font size | `.64285714rem` |
| `--canvas-chip-font-size-tiny` | Tiny font size | `.71428571rem` |
| `--canvas-chip-font-size-small` | Small font size | `.78571429rem` |
| `--canvas-chip-font-weight` | Font weight | `--font-weight-bold` then `700` |
| `--canvas-chip-font-family` | Font family | `--font-family` then `lato, ...` |
| `--canvas-chip-radius` | Border radius | `--radius` then `.28571429rem` |
| `--canvas-chip-border` | Border | `0 solid transparent` |

**Asymmetric padding.** The right padding is 15% less than the left to optically balance the dismiss icon. The X button adds visual weight to the right side, so reduced padding compensates. When overriding `--canvas-chip-padding`, keep the right value about 15% smaller than the left (e.g., if left is `1em`, right should be about `.85em`).

**File.** `assets/canvas-plugin-ui.js`

### canvas-input

A single-line text input with integrated label, error state, and native form participation via `ElementInternals`. Renders an `<input>` inside Shadow DOM. For multi-line text, use `canvas-textarea`.

**Do not use native `<input>` elements.** `canvas-input` supports every input type including `text`, `email`, `password`, `number`, `tel`, `url`, `date`, `datetime-local`, `month`, `week`, and `time`. For date and time types the component styles the native picker through the same border, radius, padding, and font as other inputs. A raw `<input>` produces output that does not match Canvas even when CSS tokens are applied by hand. See the native input prohibition in `component-usage.md` Text Inputs vs Textareas.

**Usage**

```html
<canvas-input label="Patient Name" placeholder="e.g. Jane Smith"></canvas-input>
<canvas-input label="Email" type="email" placeholder="patient@example.com"></canvas-input>
<canvas-input label="Date of Birth" type="date"></canvas-input>
<canvas-input label="First Name" required error="Required"></canvas-input>
<canvas-input label="Patient ID" value="PAT-00421" disabled></canvas-input>
<canvas-input placeholder="No label, just placeholder"></canvas-input>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `label` | string | none (no label rendered) |
| `placeholder` | string | none |
| `type` | text, email, date, number, tel, url, password, etc. | text |
| `required` | boolean | false |
| `error` | string | none (shows error state when set, value becomes error message) |
| `disabled` | boolean | false |
| `value` | string | empty |
| `name` | string | none (form field name for ElementInternals) |

**Properties**

| Property | Type | Description |
|---|---|---|
| `value` | string | Get or set the current input value. Setting also updates the form value via ElementInternals. |
| `name` | string | The form field name (reads from attribute). |

**Events**

| Event | When |
|---|---|
| `input` | On every keystroke. Bubbles and composes through shadow DOM. |
| `change` | On blur after value changed. Bubbles and composes through shadow DOM. |

**Form participation.** The component uses `ElementInternals` with `formAssociated: true`. When placed inside a `<form>` with a `name` attribute, its value is automatically included in `FormData` on submission. No manual value extraction needed.

```html
<form id="intake" onsubmit="event.preventDefault(); console.log(new FormData(this));">
  <canvas-input label="First Name" name="first_name" required></canvas-input>
  <canvas-input label="Last Name" name="last_name" required></canvas-input>
  <canvas-textarea label="Reason" name="reason" rows="3"></canvas-textarea>
  <canvas-button type="submit">Submit</canvas-button>
</form>
```

**Error state.** Setting the `error` attribute activates the error visual treatment and shows the error message below the input. Removing the attribute clears it.

```html
<!-- show error -->
<canvas-input label="Email" error="Invalid email address"></canvas-input>

<!-- clear error via JS -->
document.querySelector('canvas-input').removeAttribute('error');
```

When in error state, the label turns red (`#9f3a38`), the input background turns pink (`#fff6f6`), the border turns pink (`#e0b4b4`), and the error text appears. The input gets `aria-invalid="true"` and `aria-describedby` linking to the error message.

**Spacing.** The component does not add outer margin. Vertical spacing between stacked inputs is handled by the consumer.

```html
<div style="display: flex; flex-direction: column; gap: 12px">
  <canvas-input label="First Name"></canvas-input>
  <canvas-input label="Last Name"></canvas-input>
  <canvas-textarea label="Notes" rows="3"></canvas-textarea>
</div>
```

**Component tokens**

| Token | What it controls | Fallback chain |
|---|---|---|
| `--canvas-input-padding` | Input/textarea padding | `.67857143em 1em` |
| `--canvas-input-font-size` | Input/textarea font size | `1em` |
| `--canvas-input-font-family` | Font family (label, input, error) | `--font-family` then `lato, ...` |
| `--canvas-input-line-height` | Input/textarea line height | `1.21428571em` |
| `--canvas-input-color` | Input text color | `--color-text` then `rgba(0, 0, 0, 0.87)` |
| `--canvas-input-bg` | Input background | `--color-surface` then `#FFFFFF` |
| `--canvas-input-border` | Input border | `1px solid rgba(34, 36, 38, 0.15)` |
| `--canvas-input-radius` | Border radius | `--radius` then `.28571429rem` |
| `--canvas-input-focus-border` | Focus border color | `#85b7d9` |
| `--canvas-input-placeholder` | Placeholder color | `rgba(191, 191, 191, 0.87)` |
| `--canvas-input-focus-placeholder` | Placeholder color on focus | `rgba(115, 115, 115, 0.87)` |
| `--canvas-input-disabled-bg` | Disabled background | `--color-bg` then `#F5F5F5` |
| `--canvas-input-label-font-size` | Label font size | `.92857143em` |
| `--canvas-input-label-font-weight` | Label font weight | `--font-weight-bold` then `700` |
| `--canvas-input-label-color` | Label color | `--color-text` then `rgba(0, 0, 0, 0.87)` |
| `--canvas-input-error-text` | Error text and label color | `#9f3a38` |
| `--canvas-input-error-bg` | Error input background | `#fff6f6` |
| `--canvas-input-error-border` | Error border and placeholder color | `#e0b4b4` |

**File.** `assets/canvas-plugin-ui.js`

### canvas-textarea

A multi-line text area with integrated label, error state, optional auto-resize, character counter, and native form participation via `ElementInternals`. Shares visual styling with `canvas-input` so both look cohesive in the same form.

**Usage**

```html
<canvas-textarea label="Notes" placeholder="Enter notes ..."></canvas-textarea>
<canvas-textarea label="Description" rows="6" placeholder="Describe the issue ..."></canvas-textarea>
<canvas-textarea label="Comment" auto-resize rows="1" placeholder="Add a comment ..."></canvas-textarea>
<canvas-textarea label="Message" auto-resize rows="1" max-rows="6" placeholder="Type a message ..."></canvas-textarea>
<canvas-textarea label="Reason" maxlength="200" placeholder="Override reason ..."></canvas-textarea>
<canvas-textarea label="Notes" error="This field is required"></canvas-textarea>
<canvas-textarea label="Notes" disabled value="Read-only content"></canvas-textarea>
<canvas-textarea label="Notes" no-resize placeholder="Fixed height area"></canvas-textarea>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `label` | string | none (no label rendered) |
| `placeholder` | string | none |
| `rows` | number | 4 (initial height in rows) |
| `max-rows` | number | none (caps auto-resize growth at this many rows, then scrolls) |
| `maxlength` | number | none (when set, shows character counter below) |
| `auto-resize` | boolean | false (grows with content using grid overlay) |
| `no-resize` | boolean | false (hides the drag-to-resize handle) |
| `required` | boolean | false |
| `error` | string | none (shows error state when set, value becomes error message) |
| `disabled` | boolean | false |
| `value` | string | empty |
| `name` | string | none (form field name for ElementInternals) |

**Properties**

| Property | Type | Description |
|---|---|---|
| `value` | string | Get or set the current textarea value. Setting also updates the form value via ElementInternals. |
| `name` | string | The form field name (reads from attribute). |

**Events**

| Event | When |
|---|---|
| `input` | On every keystroke. Bubbles and composes through shadow DOM. |
| `change` | On blur after value changed. Bubbles and composes through shadow DOM. |

**Auto-resize.** When `auto-resize` is set, the textarea grows with its content. Uses the same grid overlay technique Canvas uses in its command fields. A hidden pseudo-element mirrors the content and pushes the container height. The resize handle is automatically hidden in this mode. Combine with `rows="1"` for a single-line starting height that matches `canvas-input`. Add `max-rows` to cap the growth and scroll beyond that point.

**Chat input pattern.** For a message input that starts at one line, grows as the user types, and caps at a reasonable height.

```html
<canvas-textarea auto-resize rows="1" max-rows="6" placeholder="Type a message ..."></canvas-textarea>
```

**max-rows.** Only applies when `auto-resize` is set. The component measures the textarea's line-height and padding at render time and calculates a pixel max-height from the row count. Once content exceeds max-rows, the textarea stops growing and scrolls internally. For container-level height capping (e.g. filling a flex panel), use CSS on the host element instead.

**Character counter.** When `maxlength` is set, a counter appears below the textarea showing the current length against the limit (e.g. "42 / 200"). The counter turns red and bold when the limit is reached.

**Form participation.** Same as `canvas-input`. Uses `ElementInternals` with `formAssociated: true`. When placed inside a `<form>` with a `name` attribute, its value is automatically included in `FormData`.

```html
<form id="intake" onsubmit="event.preventDefault(); console.log(new FormData(this));">
  <canvas-input label="First Name" name="first_name" required></canvas-input>
  <canvas-textarea label="Reason" name="reason" rows="3" required></canvas-textarea>
  <canvas-button type="submit">Submit</canvas-button>
</form>
```

**Error state.** Same visual treatment as `canvas-input`. Red label, pink background, pink border, error message below.

**Spacing.** The component does not add outer margin. Use the consumer layout for spacing between fields.

**Component tokens**

| Token | What it controls | Fallback chain |
|---|---|---|
| `--canvas-textarea-padding` | Textarea padding | `--canvas-input-padding` then `.67857143em 1em` |
| `--canvas-textarea-font-size` | Textarea font size | `--canvas-input-font-size` then `1em` |
| `--canvas-textarea-font-family` | Font family (label, textarea, error) | `--font-family` then `lato, ...` |
| `--canvas-textarea-line-height` | Textarea line height | `--canvas-input-line-height` then `1.21428571em` |
| `--canvas-textarea-color` | Textarea text color | `--color-text` then `rgba(0, 0, 0, 0.87)` |
| `--canvas-textarea-bg` | Textarea background | `--color-surface` then `#FFFFFF` |
| `--canvas-textarea-border` | Textarea border | `--canvas-input-border` then `1px solid rgba(34, 36, 38, 0.15)` |
| `--canvas-textarea-radius` | Border radius | `--canvas-input-radius` then `--radius` then `.28571429rem` |
| `--canvas-textarea-focus-border` | Focus border color | `--canvas-input-focus-border` then `#85b7d9` |
| `--canvas-textarea-placeholder` | Placeholder color | `--canvas-input-placeholder` then `rgba(191, 191, 191, 0.87)` |
| `--canvas-textarea-disabled-bg` | Disabled background | `--canvas-input-disabled-bg` then `--color-bg` then `#F5F5F5` |
| `--canvas-textarea-label-font-size` | Label font size | `--canvas-input-label-font-size` then `.92857143em` |
| `--canvas-textarea-label-color` | Label color | `--color-text` then `rgba(0, 0, 0, 0.87)` |
| `--canvas-textarea-error-text` | Error text and label color | `--canvas-input-error-text` then `#9f3a38` |
| `--canvas-textarea-error-bg` | Error background | `--canvas-input-error-bg` then `#fff6f6` |
| `--canvas-textarea-error-border` | Error border color | `--canvas-input-error-border` then `#e0b4b4` |
| `--canvas-textarea-counter-color` | Counter text color | `--color-text-muted` then `#767676` |

**File.** `assets/canvas-plugin-ui.js`

### canvas-radio

A locked radio button matching the Canvas home-app. No visual customization. Grouped by shared `name` attribute. Selecting one radio deselects siblings with the same name.

**Usage**

```html
<canvas-radio name="duration" label="15 min" value="15"></canvas-radio>
<canvas-radio name="duration" label="30 min" value="30"></canvas-radio>
<canvas-radio name="duration" label="60 min" value="60" checked></canvas-radio>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `name` | string | none (required for grouping and form data) |
| `label` | string | none |
| `value` | string | empty |
| `checked` | boolean | false |
| `disabled` | boolean | false |

**Properties**

| Property | Type | Description |
|---|---|---|
| `checked` | boolean | Get or set checked state. Setting updates the attribute and unchecks siblings. |
| `value` | string | The radio value (reads from attribute). |
| `name` | string | The group name (reads from attribute). |

**Events**

| Event | When |
|---|---|
| `change` | When the radio is selected. Bubbles and composes through shadow DOM. |

**Grouping.** Radios with the same `name` attribute form a group. Selecting one unchecks the others. Place them under the same parent element.

**Form participation.** Uses `ElementInternals` with `formAssociated: true`. The checked radio's value is included in `FormData`.

**Layouts.** Vertical and horizontal groups are handled by the consumer via flex layout.

```html
<!-- Vertical -->
<div style="display: flex; flex-direction: column">
  <canvas-radio name="type" label="Appointment" value="appointment"></canvas-radio>
  <canvas-radio name="type" label="Home visit" value="home-visit"></canvas-radio>
</div>

<!-- Horizontal -->
<div style="display: flex; gap: 16px">
  <canvas-radio name="dur" label="15 min" value="15"></canvas-radio>
  <canvas-radio name="dur" label="30 min" value="30" checked></canvas-radio>
  <canvas-radio name="dur" label="60 min" value="60"></canvas-radio>
</div>
```

**Touch targets.** Override min-height and min-width for tablet use via `--canvas-radio-min-height` and `--canvas-radio-min-width`. Defaults to `auto` (content sized).

**Vertical spacing.** Stacked radios need `gap: 4px` on the container. The component does not add outer margin.

**Locked component.** No visual customization tokens beyond touch targets. Focus border uses `#85b7d9` matching canvas-input for consistency across form elements.

**File.** `assets/canvas-plugin-ui.js`

### canvas-checkbox

A locked checkbox matching the Canvas home-app. White box with a dark checkmark, no colored fill. Toggles between checked and unchecked on click.

**Usage**

```html
<canvas-checkbox label="I agree to the terms"></canvas-checkbox>
<canvas-checkbox label="Send updates" checked></canvas-checkbox>
<canvas-checkbox label="Locked option" checked disabled></canvas-checkbox>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `label` | string | none |
| `checked` | boolean | false |
| `disabled` | boolean | false |
| `name` | string | none (form field name) |
| `value` | string | "on" |

**Properties**

| Property | Type | Description |
|---|---|---|
| `checked` | boolean | Get or set checked state. Setting updates the attribute. |
| `value` | string | The checkbox value (reads from attribute, defaults to "on"). |
| `name` | string | The form field name (reads from attribute). |

**Events**

| Event | When |
|---|---|
| `change` | When the checkbox is toggled. Bubbles and composes through shadow DOM. |

**Form participation.** Uses `ElementInternals` with `formAssociated: true`. When checked, the value is included in `FormData`. When unchecked, the field is omitted (standard checkbox behavior).

**Checkbox group.** Multiple checkboxes allow independent selection. No mutual exclusion. Use the same `name` for grouping in form data.

```html
<div style="display: flex; flex-direction: column; align-items: flex-start">
  <canvas-checkbox name="type" label="Appointment" value="appointment" checked></canvas-checkbox>
  <canvas-checkbox name="type" label="Home visit" value="home-visit"></canvas-checkbox>
  <canvas-checkbox name="type" label="Phone call" value="phone-call"></canvas-checkbox>
</div>
```

**Full width rows.** Set `width: 100%` for clickable rows that span the container. Without it, the checkbox is content sized.

```html
<canvas-checkbox label="Enable notifications" style="width: 100%"></canvas-checkbox>
```

**Touch targets.** Override min-height and min-width for tablet use via `--canvas-checkbox-min-height` and `--canvas-checkbox-min-width`. Defaults to `auto` (content sized).

```html
<!-- 44px touch target for tablet -->
<div style="--canvas-checkbox-min-height: 44px">
  <canvas-checkbox label="Enable notifications"></canvas-checkbox>
</div>
```

**Vertical spacing.** Stacked checkboxes need `gap: 4px` on the container. The component does not add outer margin.

**Locked component.** No visual customization tokens beyond touch targets. Focus border uses `#85b7d9` matching canvas-input and canvas-radio.

**File.** `assets/canvas-plugin-ui.js`

### canvas-toggle

A locked toggle switch matching the Canvas home-app. Blue active track (#0D71BC, not green), white thumb with gradient and shadow, slide animation. Toggles mean instant effect and must never appear on a screen with a Save or Submit button. If a form has submit, use checkboxes instead.

**Usage**

```html
<canvas-toggle label="Enable dark mode"></canvas-toggle>
<canvas-toggle label="Notifications" checked></canvas-toggle>
<canvas-toggle label="SMS alerts" label-position="start" checked></canvas-toggle>
<canvas-toggle label="Locked setting" checked disabled></canvas-toggle>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `label` | string | none |
| `checked` | boolean | false |
| `disabled` | boolean | false |
| `label-position` | start, end | end (label after toggle) |

**Properties**

| Property | Type | Description |
|---|---|---|
| `checked` | boolean | Get or set checked state. Setting updates the attribute. |

**Events**

| Event | When |
|---|---|
| `change` | When the toggle is flipped. Bubbles and composes through shadow DOM. |

**No form participation.** Toggles represent instant actions, not form data. There is no `name` or `value` attribute. Do not use inside forms that have a submit button.

**Label position.** Default is `end` (label after toggle). Set `label-position="start"` for label before toggle, commonly used in settings lists.

**Settings list pattern.** Full width rows with label on the left and toggle on the right.

```html
<div style="display: flex; flex-direction: column">
  <canvas-toggle label="Email notifications" label-position="start" style="width: 100%; justify-content: space-between;" checked></canvas-toggle>
  <canvas-toggle label="Push notifications" label-position="start" style="width: 100%; justify-content: space-between;"></canvas-toggle>
</div>
```

**Touch targets.** Override via `--canvas-toggle-min-height` and `--canvas-toggle-min-width`. Defaults to `auto`.

**Vertical spacing.** Stacked toggles need `gap: 4px` on the container.

**Locked component.** No visual customization tokens beyond touch targets. Active track is always blue #0D71BC. Focus border uses `#85b7d9`.

**File.** `assets/canvas-plugin-ui.js`

### canvas-banner

An inline message banner matching the Canvas home-app. Four variants for communicating status. Never floating. Canvas does not use toasts, snackbars, or auto-dismissing notifications anywhere. The border is rendered via `box-shadow: inset`, not a CSS border.

**Usage rules.** Canvas uses error and warning banners extensively. Success and info banners are extremely rare in the home-app. Success is communicated through UI state changes (modal closes, form resets, row appears) rather than green banners. Use `error` for API failures and validation errors that block submission (not when field-level errors are sufficient). Use `warning` when the user can proceed but should know about a risk. Use `success` only in the rare case where the user stays on the same page and nothing else changes. Use `info` very sparingly. Never stack multiple banners. If an action produces several errors, use a single banner with a list inside.

**Usage**

```html
<canvas-banner variant="warning" header="Potential duplicate patient">
  <p>It looks like this patient might already exist in Canvas.</p>
</canvas-banner>

<canvas-banner variant="error" header="Invalid credentials."></canvas-banner>

<canvas-banner variant="success">Your remittance has been successfully submitted.</canvas-banner>

<canvas-banner variant="info" dismissible header="New lab results">
  <p>Lab results from Mar 20, 2026 are ready for review.</p>
</canvas-banner>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `variant` | `warning`, `error`, `success`, `info` | none (neutral gray) |
| `header` | string | none (no header rendered) |
| `dismissible` | boolean | false |

**Slot.** Default slot accepts any content including text, paragraphs, lists, and other web components like buttons and checkboxes.

```html
<canvas-banner variant="warning" header="Potential duplicate patient">
  <p>A patient with this name already exists.</p>
  <div style="margin-top: 8px; display: flex; gap: .25em">
    <canvas-button size="sm" variant="ghost">Review match</canvas-button>
    <canvas-button size="sm">Continue anyway</canvas-button>
  </div>
</canvas-banner>
```

**Events**

| Event | When |
|---|---|
| `dismiss` | When the dismiss button is clicked. Bubbles and composes through shadow DOM. |

The component does not remove itself on dismiss. The consumer handles removal.

```html
<script>
document.addEventListener('dismiss', function(e) {
  if (e.target.tagName === 'CANVAS-BANNER') {
    e.target.remove();
  }
});
</script>
```

**Content patterns.**

Header with body (most common for detailed messages).
```html
<canvas-banner variant="error" header="Coverage verification failed">
  <p>The following errors were returned by the payer.</p>
  <ul>
    <li>Patient not found in payer system</li>
    <li>Member ID does not match records</li>
  </ul>
</canvas-banner>
```

Header only (short status messages).
```html
<canvas-banner variant="warning" header="This patient has an active drug interaction alert."></canvas-banner>
```

Body only (simple inline messages).
```html
<canvas-banner variant="info">Lab results are pending review.</canvas-banner>
```

**Spacing.** The component does not add outer margin. Vertical spacing between stacked banners is handled by the consumer.

**Locked component.** No visual customization tokens. The four variant colors are fixed to match the Canvas home-app. The neutral default (no variant) uses gray.

**File.** `assets/canvas-plugin-ui.js`

### canvas-card

A segment card matching the Canvas home-app. White surface with border, border-radius, and box-shadow. The card is always 100% width of its parent container. Supports multiple body sections separated by borders, and an optional gray footer for actions and metadata. Used for notes, stacked content blocks, and detail panels. For the decision rule on when to reach for this component rather than a raw div, see [component-usage.md](component-usage.md) Cards and Content Containers.

Three custom elements are registered from a single file: `canvas-card` (outer container), `canvas-card-body` (body sections), and `canvas-card-footer` (gray footer area).

**Rendering.** The card does not apply `overflow: hidden`. Corner clipping of slotted body and footer backgrounds is handled by applying the card's border-radius (minus 1px for the border width) to the first and last slotted child via `::slotted(...:first-child)` and `::slotted(...:last-child)` rules. Because the card is not a clipping boundary, a popup child (for example a `canvas-dropdown` menu) can extend past the card's edge without being cut off. The body also does not apply `overflow-y: auto`, so content grows to fit naturally.

**Scrolling.** For a card body that should scroll, wrap the content in a `canvas-scroll-area` and set a `max-height` on the scroll area. Setting `max-height` on `canvas-card-body` directly has no effect because the body is not a scroll container. See the canvas-scroll-area section below for the migration pattern.

**Usage**

```html
<canvas-card>
  <canvas-card-body>
    <h4>Patient Summary</h4>
    <p style="margin-top: 8px">Content here</p>
  </canvas-card-body>
</canvas-card>

<canvas-card raised>
  <canvas-card-body>
    <h4>Office Visit</h4>
    <p>Reviewed medications.</p>
  </canvas-card-body>
  <canvas-card-footer>
    <canvas-button variant="primary" size="sm">Sign</canvas-button>
    <canvas-button variant="ghost" size="sm">Delete</canvas-button>
  </canvas-card-footer>
</canvas-card>
```

**Attributes (canvas-card)**

| Attribute | Values | Default |
|---|---|---|
| `raised` | boolean | false (stronger shadow when set) |

**Attributes (canvas-card-body and canvas-card-footer)**

| Attribute | Values | Default |
|---|---|---|
| `no-padding` | boolean | false (removes 1em padding when set) |

**Multiple body segments.** Adjacent `canvas-card-body` elements get a border between them automatically.

```html
<canvas-card raised>
  <canvas-card-body>
    <h4>History of Present Illness</h4>
    <p style="margin-top: 8px">Patient presents with worsening shortness of breath.</p>
  </canvas-card-body>
  <canvas-card-body>
    <h4>Assessment</h4>
    <p style="margin-top: 8px">COPD, stable.</p>
  </canvas-card-body>
  <canvas-card-footer>
    <canvas-button variant="primary" size="sm">Sign</canvas-button>
  </canvas-card-footer>
</canvas-card>
```

**No padding.** Use `no-padding` on body or footer for edge-to-edge content like tables.

```html
<canvas-card>
  <canvas-card-body no-padding>
    <table style="width: 100%">...</table>
  </canvas-card-body>
</canvas-card>
```

**Spacing.** The component does not add outer margin. Vertical spacing between stacked cards is handled by the consumer.

**Component tokens**

| Token | What it controls | Fallback chain |
|---|---|---|
| `--canvas-card-shadow` | Box shadow | `0 1px 2px 0 rgba(34, 36, 38, 0.15)` (default) or `0 2px 4px 0 rgba(34, 36, 38, 0.12), 0 2px 10px 0 rgba(34, 36, 38, 0.15)` (raised) |

The shadow token can be used for hover effects or to remove the shadow entirely.

```html
<!-- no shadow -->
<canvas-card style="--canvas-card-shadow: none">...</canvas-card>

<!-- hover elevation via JS -->
<canvas-card raised
  onmouseenter="this.style.setProperty('--canvas-card-shadow','0 4px 12px 0 rgba(34,36,38,0.2)')"
  onmouseleave="this.style.removeProperty('--canvas-card-shadow')">
  ...
</canvas-card>
```

**Typography dependency.** Headings (h4, h3, etc.) inside card body sections need `canvas-plugin-ui.css` loaded on the page for correct margin behavior. Without it, browser default heading margins add unwanted space at the top of card bodies. The `:first-child { margin-top: 0 }` rule in the stylesheet handles this.

**File.** `assets/canvas-plugin-ui.js`

### canvas-inline-row

A layout primitive for a horizontal row of form elements. Defaults to a flex container with `gap` between children, bottom alignment of children, and automatic wrap onto a new line when the row cannot fit. Growing children (inputs, dropdowns, comboboxes, multi selects, textareas) share available space with a minimum basis of 160 px. Natural width children (buttons, checkboxes, radios, toggles) keep their content width.

Use for filter bars, inline edit forms, search bars, toolbar forms, and any row of form elements sharing a visual line. See [component-usage.md](component-usage.md) Inline Form Rows for the full pattern description and use cases.

**Usage**

```html
<canvas-inline-row>
  <canvas-input label="From" type="date"></canvas-input>
  <canvas-input label="To" type="date"></canvas-input>
  <canvas-dropdown label="Provider">
    <canvas-option value="" selected>All Providers</canvas-option>
    <canvas-option value="1">Dr. Alvarez</canvas-option>
  </canvas-dropdown>
  <canvas-button>Load Appointments</canvas-button>
</canvas-inline-row>
```

**Attributes.** None.

**Children and flex behavior.** The component applies flex sizing rules to its slotted children based on component type.

| Behavior | Canvas components | Flex rule |
|---|---|---|
| Grow | `canvas-input`, `canvas-dropdown`, `canvas-combobox`, `canvas-multi-select`, `canvas-textarea` | `flex: 1 0 var(--canvas-inline-row-item-min, 160px)`. Items share available space, respect a 160 px minimum, wrap instead of shrinking below the minimum. |
| Natural | `canvas-button`, `canvas-checkbox`, `canvas-radio`, `canvas-toggle` | `flex: 0 0 auto`. Items take content width, never grow, never shrink. |
| Opt in | Any child with `inline-role="grow"` or `inline-role="natural"` | Overrides the default based on the attribute value. Useful for per instance tweaks or for external components that are not in the Canvas bundle. |

**Per instance override.** Set `inline-role` on any child to override its default sizing.

```html
<!-- Force a fixed width input, e.g. a zip code field -->
<canvas-inline-row>
  <canvas-input label="Street" placeholder="Address"></canvas-input>
  <canvas-input label="Zip" inline-role="natural" style="width: 120px"></canvas-input>
</canvas-inline-row>

<!-- Force a stretched button -->
<canvas-inline-row>
  <canvas-input label="Search" placeholder="Patient name"></canvas-input>
  <canvas-button inline-role="grow">Search</canvas-button>
</canvas-inline-row>
```

**Narrow surfaces.** The component wraps automatically via `flex-wrap: wrap`. In a 360 px container, a four element row wraps onto two or three lines. Every element keeps at least 160 px width.

**Component tokens**

| Token | What it controls | Fallback chain |
|---|---|---|
| `--canvas-inline-row-gap` | Gap between children | `--space-small` then `12px` |
| `--canvas-inline-row-item-min` | Minimum width for growing children | `160px` |

```html
<!-- Wider gap, e.g. in a page header toolbar -->
<canvas-inline-row style="--canvas-inline-row-gap: 20px">
  ...
</canvas-inline-row>

<!-- Tighter minimum for a compact filter bar that must stay on one line -->
<canvas-inline-row style="--canvas-inline-row-item-min: 140px">
  ...
</canvas-inline-row>
```

**When not to use.** Do not use `canvas-inline-row` for horizontal scrollers like chip strips (use `canvas-scroll-area horizontal`), tab bars (use `canvas-tabs`), vertical stacks (use a plain flex column or block flow), right aligned action clusters inside a card footer (use `canvas-card-footer` directly with `justify-content: space-between` on a plain div inside), or single element rows (render the element directly). Full guidance in [component-usage.md](component-usage.md) Inline Form Rows.

**File.** `assets/canvas-plugin-ui.js`

### canvas-scroll-area

A declarative, opt in scroll container. Use it anywhere content needs to scroll. Common cases include replacing raw wide table wrappers, adding a scroll region inside a card body, and constraining long lists or log panels to a fixed height. The component has no visual styling of its own, it is a structural wrapper.

**Opt in direction.** Scrolling is off by default. Add the `vertical` attribute for vertical scroll, the `horizontal` attribute for horizontal scroll, or both for a two axis scroll area. Without either attribute, the component is a transparent block that grows to content.

**Usage**

```html
<canvas-scroll-area vertical aria-label="Activity log" style="max-height: 320px">
  long list or log content
</canvas-scroll-area>

<canvas-scroll-area horizontal aria-label="Wide data table" style="max-width: 100%">
  <table style="min-width: 1200px">...</table>
</canvas-scroll-area>

<canvas-scroll-area vertical horizontal aria-label="Wide and tall grid" style="max-height: 400px; max-width: 100%">
  <table style="min-width: 1400px">...</table>
</canvas-scroll-area>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `vertical` | boolean | off. When set, the component enables `overflow-y: auto`. |
| `horizontal` | boolean | off. When set, the component enables `overflow-x: auto`. |

**Dimensions.** Consumers set `max-height`, `max-width`, or any other CSS length via `style=` or an external stylesheet. The component does not accept size attributes. This keeps the API minimal and lets consumers use any CSS length.

**Accessibility.** When either `vertical` or `horizontal` is present and the element has no consumer supplied `tabindex`, the component sets `tabindex="0"` so keyboard users can focus the region and scroll with arrow keys. Always provide `aria-label` or `aria-labelledby` describing what is scrolling. Consumer supplied `tabindex` is never overridden.

**Clipping caveat.** A scroll area is itself a clipping boundary. Popups placed inside a vertical scroll area (such as a `canvas-dropdown` or `canvas-combobox` menu) get clipped by the scroll area even when the outer card or modal does not clip. Current usage rule, do not place `canvas-dropdown`, `canvas-combobox`, or `canvas-multi-select` inside a `canvas-scroll-area[vertical]`. Tooltips are exempt because they hide on scroll. The restriction is lifted in a later release when popup components move to the browser top layer.

**Migration from canvas-card-body scrolling.** Before 4.0.0, setting `max-height` on `canvas-card-body` activated body scrolling. That pattern is removed. Wrap the content in a scroll area instead.

```html
<!-- before 4.0.0 -->
<canvas-card-body style="max-height: 360px">
  long content
</canvas-card-body>

<!-- 4.0.0 and later -->
<canvas-card-body>
  <canvas-scroll-area vertical style="max-height: 336px">
    long content
  </canvas-scroll-area>
</canvas-card-body>
```

The scroll area `max-height` is smaller than the old body `max-height` to account for the body's 1em top and bottom padding. If the card body does not need its own padding around the scroll region, add `no-padding` on the body and move padding to the scroll area.

**Replaces the table-scroll helper.** The pre 4.0.0 `.table-scroll` div wrapper for wide tables is replaced by `<canvas-scroll-area horizontal>` wrapping the table.

**File.** `assets/canvas-plugin-ui.js`

### canvas-dropdown

A non-searchable select dropdown matching the Canvas home-app. Click to open a menu, arrow keys to navigate, Enter to select. For searchable dropdowns, use `canvas-combobox` instead.

**Usage**

```html
<canvas-dropdown label="Status" name="status" placeholder="Select status">
  <canvas-option value="active">Active</canvas-option>
  <canvas-option value="inactive">Inactive</canvas-option>
  <canvas-option value="pending">Pending Review</canvas-option>
</canvas-dropdown>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `label` | string | none (no label rendered) |
| `placeholder` | string | none |
| `name` | string | none (form field name) |
| `value` | string | none |
| `size` | `sm` | base |
| `disabled` | boolean | false |
| `required` | boolean | false |
| `error` | string | none (shows error state when set) |

**Options via `<canvas-option>` children.** The component reads `<canvas-option>` elements from its light DOM on connect. Each option has a `value` attribute and optional `label` attribute (used for trigger display text, falls back to textContent). Pre-select with the `selected` attribute. Disable with `disabled`.

```html
<canvas-dropdown label="Coverage" name="coverage">
  <canvas-option value="commercial">Commercial</canvas-option>
  <canvas-option value="medicare" selected>Medicare</canvas-option>
  <canvas-option value="medicaid">Medicaid</canvas-option>
  <canvas-option value="self-pay" disabled>Self-pay (unavailable)</canvas-option>
</canvas-dropdown>
```

**Rich content options.** `<canvas-option>` accepts any HTML content. Use the `label` attribute to set what appears in the trigger when selected, since the trigger shows plain text only.

```html
<canvas-dropdown label="Patient Status" placeholder="Select status">
  <canvas-option value="active" label="Active">
    <canvas-badge color="green" size="mini">Active</canvas-badge> Currently enrolled
  </canvas-option>
  <canvas-option value="inactive" label="Inactive">
    <canvas-badge color="red" size="mini">Inactive</canvas-badge> No recent visits
  </canvas-option>
</canvas-dropdown>
```

**Properties**

| Property | Type | Description |
|---|---|---|
| `value` | string | Get or set the selected value. |
| `name` | string | The form field name (reads from attribute). |

**Events**

| Event | When |
|---|---|
| `change` | When a new option is selected. Bubbles and composes through shadow DOM. |

**Form participation.** Uses `ElementInternals` with `formAssociated: true`. The selected value is included in FormData.

**Size rules.**

- **default** (no size attribute) for forms, modals, filter bars, search bars, inline edit rows, and any standalone data entry. This is the standard dropdown seen in patient forms, coverage modals, appointment creation, and anywhere the dropdown is the primary interaction on screen. Trigger text renders at 16px.
- **sm** for compact contexts where the dropdown is secondary to the main content and every other element in the row is also `sm`. Narrow sidebars and settings panels where the dropdown sits alongside `sm` buttons. Trigger text renders at 12px. The menu items always stay at 16px regardless of trigger size.

When a dropdown shares a row with inputs, buttons, or other dropdowns, follow the Same Row Height Cohesion rule in component-usage.md. Matching the `size` attribute across components does not produce matching rendered heights. `canvas-button[size="sm"]` has a 36 px `min-height` while `canvas-dropdown[size="sm"]` only reduces the trigger font size. The safe baseline is default size on every element in the row. For the full filter bar pattern see Inline Form Rows in component-usage.md.

```html
<!-- default for forms and modals -->
<canvas-dropdown label="Coverage Type" name="coverage" placeholder="Select type">
  <canvas-option value="commercial">Commercial</canvas-option>
  <canvas-option value="medicare">Medicare</canvas-option>
</canvas-dropdown>

<!-- sm only in rows where every element is also sm. See component-usage.md Same Row Height Cohesion. -->
<canvas-dropdown label="Location" size="sm" placeholder="Select location">
  <canvas-option value="sf">Canvas Clinic SF</canvas-option>
  <canvas-option value="oak">Canvas Clinic Oakland</canvas-option>
</canvas-dropdown>
```

**Keyboard navigation.** Click, Enter, or Space on the trigger opens the dropdown. ArrowUp and ArrowDown open the dropdown when closed and move the highlight through options when open. Enter selects the currently highlighted option and closes. Type-ahead, typing a letter jumps to the first option starting with that letter, typing multiple letters in quick succession narrows the match. Home and End jump to first and last when open. Tab closes the dropdown (selecting the highlighted option if any) and moves focus to the next focusable element. Escape closes without selecting and returns focus to the trigger. Clicking outside closes without selecting. Disabled options are skipped.

**Menu behavior.** The dropdown menu must not exceed the viewport. If the menu would overflow below the trigger, it flips to open above. If it would overflow on the right, it aligns to the right edge of the trigger. Long option lists scroll within the menu rather than growing the menu beyond the viewport.

**Locked component.** No visual customization tokens. Border, focus border (#96c8da), shadow, item hover, and item selected styling are fixed to match the Canvas home-app.

**File.** `assets/canvas-plugin-ui.js`

### canvas-combobox

A searchable dropdown with type-ahead filtering, keyboard navigation, and viewport flip. Visually identical to `canvas-dropdown` but the input is editable for filtering. Use when the list is long or option text is long and the user benefits from typing to narrow results (provider search, diagnosis lookup, medication search). For fixed lists where search is not needed, use `canvas-dropdown` instead.

**Usage**

```html
<canvas-combobox label="Diagnosis" name="diagnosis" placeholder="Search diagnoses">
  <canvas-option value="e11.9">Type 2 diabetes mellitus without complications</canvas-option>
  <canvas-option value="i10">Essential hypertension</canvas-option>
  <canvas-option value="j06.9">Acute upper respiratory infection</canvas-option>
  <canvas-option value="z00.00">Encounter for general adult medical exam</canvas-option>
</canvas-combobox>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `label` | string | none (no label rendered) |
| `placeholder` | string | none |
| `name` | string | none (form field name) |
| `value` | string | none |
| `disabled` | boolean | false |
| `required` | boolean | false |
| `error` | string | none (shows error state when set) |

**Options via `<canvas-option>` children.** Same as `canvas-dropdown`. Each option has a `value` attribute and optional `label` attribute (falls back to textContent). Pre-select with `selected`. Disable with `disabled`. HTML content inside options is preserved in the menu.

**Properties**

| Property | Type | Description |
|---|---|---|
| `value` | string | Get or set the selected value. |
| `name` | string | The form field name (reads from attribute). |

**Events**

| Event | When |
|---|---|
| `change` | When a new option is selected. Bubbles and composes through shadow DOM. |

**Form participation.** Uses `ElementInternals` with `formAssociated: true`. The selected value is included in FormData.

**Type-ahead filtering.** Typing in the input filters options by case-insensitive substring match. A "No results" message appears when no options match. Filtering clears on selection or Escape.

**Viewport flip.** If the menu would overflow below the viewport, it flips to open above the input. Border radius adjusts automatically.

**Error state.** Same visual treatment as `canvas-input`. Setting the `error` attribute shows a red label, pink input background, pink border, and error message below the input.

**Keyboard navigation.** Click, Enter, or Space on the input opens the dropdown. ArrowUp and ArrowDown navigate through filtered options, Enter selects the highlighted option and closes, Escape restores the previous value and closes, Home and End jump to first and last, Tab selects the highlighted option and moves focus to the next element. Disabled options are skipped. Clicking outside closes without selecting.

**ARIA.** The input carries `role="combobox"`, `aria-expanded` reflecting dropdown state, `aria-controls` pointing to the listbox id, and `aria-activedescendant` pointing to the currently highlighted option.

**Menu behavior.** Same contract as `canvas-dropdown`. The menu must not exceed the viewport. If it would overflow below the input, it flips to open above. Long filtered lists scroll within the menu rather than growing beyond the viewport.

**Locked component.** No visual customization tokens. Border, focus border (#96c8da), shadow, item hover, and item selected styling are fixed to match the Canvas home-app.

**File.** `assets/canvas-plugin-ui.js`

### canvas-multi-select

A multi-value combobox with chip rendering, inline checkbox indicators, and search filtering. Selected items appear as dismissible chips in the trigger area. The menu stays open after each selection. Use when the user needs to pick multiple values from a set of 8 or more items (providers, locations, diagnosis codes, insurance plans). For fewer than 8 options, use a checkbox group instead.

**Usage**

```html
<canvas-multi-select label="Providers" name="providers" placeholder="Search providers">
  <canvas-option value="magee">Steven Magee MD</canvas-option>
  <canvas-option value="chen">Lisa Chen DO</canvas-option>
  <canvas-option value="patel" selected>Raj Patel MD</canvas-option>
</canvas-multi-select>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `label` | string | none (no label rendered) |
| `placeholder` | string | none |
| `name` | string | none (form field name) |
| `disabled` | boolean | false |
| `required` | boolean | false |
| `error` | string | none (shows error state when set) |

**Options via `<canvas-option>` children.** Same element as dropdown and combobox. Pre-select with `selected` attribute. Disable with `disabled`. Selected options are hidden from the menu and shown as chips in the trigger.

**Properties**

| Property | Type | Description |
|---|---|---|
| `value` | array | Get or set the selected values. Getter returns a shallow copy. Setter accepts an array. |
| `name` | string | The form field name (reads from attribute). |

**Events**

| Event | When |
|---|---|
| `change` | When an option is selected or deselected. Bubbles and composes through shadow DOM. |

**Form participation.** Uses `ElementInternals` with `formAssociated: true`. Each selected value is appended as a separate FormData entry under the same name.

**Chip behavior.** Selected values render as chips with dismiss buttons in the trigger area. Clicking the X on a chip deselects that value. Chips have `aria-label="Remove [label]"` for accessibility.

**Keyboard navigation.** Same as combobox plus Backspace on an empty input deselects the last selected value. Arrow keys navigate visible options. Enter toggles the highlighted option. Escape closes the menu.

**Viewport flip.** Same as combobox. Menu flips above if it would overflow the viewport.

**Error state.** Same visual treatment as canvas-input and canvas-combobox.

**Locked component.** No visual customization tokens.

**File.** `assets/canvas-plugin-ui.js`

### canvas-menu-button

A button that opens a list of actions below. Implements the WAI ARIA "Menu Button" pattern with `role="menu"` and `role="menuitem"` children. Not form associated. Use for action triggers such as plus buttons, kebab row menus, and overflow action lists. Do not use for value selection, that is `canvas-dropdown`. Do not use for arbitrary popover content such as filter forms or legends, use `canvas-popover` for that.

**Usage**

```html
<canvas-menu-button>
  <canvas-option value="edit">Edit</canvas-option>
  <canvas-option value="duplicate">Duplicate</canvas-option>
  <hr>
  <canvas-option value="delete">Delete</canvas-option>
</canvas-menu-button>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `disabled` | boolean | false |
| `direction` | `down`, `up` | auto, down when space allows, else up |
| `align` | `start`, `end` | auto, start when space allows, else end |

When `direction` or `align` is set explicitly, the corresponding axis is pinned and does not auto flip. Leaving both unset enables auto placement in both axes.

**Options via `<canvas-option>` children.** Each option has a `value` attribute and optional `label` attribute (falls back to textContent). Disable with `disabled`. HTML content inside options is preserved in the menu. Content can include icons or badges alongside text.

**Section dividers via `<hr>` children.** Insert an `<hr>` element between `<canvas-option>` children to render a section separator. The divider uses the same color as the outer menu border and has small vertical spacing. Dividers are not focusable and are skipped during keyboard navigation.

**Slotted trigger.** By default, the component renders a ghost "Actions" button with a caret. To use a custom trigger such as an icon button, slot an element with `slot="trigger"`.

```html
<canvas-menu-button>
  <canvas-button slot="trigger" variant="ghost" size="sm" aria-label="Add">
    <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
      <path d="M5 0h2v5h5v2H7v5H5V7H0V5h5z"/>
    </svg>
  </canvas-button>
  <canvas-option value="user">User</canvas-option>
  <canvas-option value="item">Item</canvas-option>
  <canvas-option value="picture">Picture</canvas-option>
</canvas-menu-button>
```

Icon only triggers must carry their own `aria-label`. The default ghost trigger sets `aria-haspopup="menu"` and toggles `aria-expanded` automatically.

**Events**

| Event | When |
|---|---|
| `select` | When an option is activated by click, Enter, or Space. `event.detail` carries `value` and `label`. Bubbles and composes through shadow DOM. |
| `open` | When the menu opens. No detail. |
| `close` | When the menu closes. No detail. |

**No form participation.** `canvas-menu-button` is not form associated. It does not carry a `name` or `value` and does not contribute to FormData. Each option action is a discrete event, not a form value.

**Keyboard navigation.** On the trigger, Enter or Space opens the menu through native button activation without a pre highlighted item. ArrowDown opens and highlights the first option. ArrowUp opens and highlights the last option. Inside the menu, ArrowUp and ArrowDown navigate with wrap, Home and End jump to first and last. Enter or Space activate the highlighted option, dispatch the `select` event with `detail.value` and `detail.label`, close the menu, and return focus to the trigger. Escape closes the menu and returns focus to the trigger without firing a select. Tab closes the menu and lets focus move to the next tab stop in the document. Outside click closes the menu without firing select, same as Escape. Disabled options are skipped during highlight navigation and cannot be activated. Section dividers (`<hr>` children) are not in the focus cycle.

**Focus return.** After a `select` event fires, the component calls `focus()` on the trigger. For the default trigger, this puts focus on the internal Actions button. For a slotted `canvas-button` trigger, focus lands on the slotted element's host, which forwards to the inner button via `delegatesFocus`. This focus return matches the Menu Button pattern and prevents focus from becoming orphaned on the closed menu. Code that listens for `select` should not call `focus()` on unrelated elements during that handler, the return is automatic.

**ARIA.** Trigger, `aria-haspopup="menu"` and `aria-expanded="true"` or `aria-expanded="false"` are set automatically on the default trigger. Slotted triggers inherit this through the component, authors only supply `aria-label` when the trigger is icon only. Menu container, `role="menu"` and `tabindex="-1"` so it is reachable by programmatic focus but not part of the tab order. Option, `role="menuitem"` and `aria-disabled="true"` when the `disabled` attribute is set on the `canvas-option`. Divider, `role="separator"` on the `<li>` rendered for each `<hr>` child.

**Auto placement.** On open, the component measures the trigger position and the menu dimensions against the viewport. If the menu would clip the viewport bottom and more room exists above, `direction` computes to up, and `data-placement-direction="up"` is set on the inner root. If the menu would clip the viewport right and room exists to the left, `align` computes to end, and `data-placement-align="end"` is set. Explicit `direction` or `align` attributes disable auto flipping on the matching axis.

**Dimensions.** Menu `min-width` 180 px, `max-width` 320 px with text wrapping at the cap, `max-height` 16.02857143 rem with vertical scroll. The trigger sizes to its content.

**Locked component.** No visual customization tokens. Trigger, menu, option, and divider styling are fixed to match the Canvas dropdown menu. Customize the trigger through a slotted `canvas-button` variant instead.

**Visual spec.**

*Default trigger.* When no `slot="trigger"` child is provided, the component renders a ghost button.

- Background, `#e0e1e2`. Hover, `#cacbcd`.
- Text color, `rgba(0, 0, 0, 0.6)`. Hover, `rgba(0, 0, 0, 0.8)`.
- Padding, `.67857143em 1.5em`. Font size, `1rem`. Font weight, `700`. Line height, `1.21428571em`.
- Border, `1px solid transparent`. Radius, `var(--radius, .28571429rem)`.
- Caret, 8 px wide by 5 px tall SVG, inherits `currentColor`.
- Focus, `var(--focus-ring, 2px solid #2185D0)` outline with 2 px offset.

*Menu container.*

- Background, `var(--color-surface, #FFFFFF)`.
- Border, `1px solid rgba(34, 36, 38, 0.15)`. Radius, `var(--radius, .28571429rem)`.
- Shadow, `0 2px 4px 0 rgba(34, 36, 38, 0.12), 0 2px 10px 0 rgba(34, 36, 38, 0.15)`.
- Offset from trigger, 2 px margin on the open axis.
- Width, `min-width: 180px`, `max-width: 320px`. Text wraps at the cap.
- Height, `max-height: 16.02857143rem` with `overflow-y: auto`. Scroll bar rendered by the browser, no custom scrollbar styling.
- Z index, `100`.
- Padding, `0`. Options sit flush against the top and bottom menu edges.

*Option.*

- Padding, `.78571429rem 1.14285714rem`. Font size, `1rem`. Line height, `1.0625rem`.
- Default color, `var(--color-text, rgba(0, 0, 0, 0.87))`.
- Hover and highlighted, background `rgba(0, 0, 0, 0.05)`, color `rgba(0, 0, 0, 0.95)`.
- Disabled, color `#767676`, cursor `not-allowed`, background transparent on hover.
- No per option border.

*Section divider.*

- Rendered for each `<hr>` child inside the default slot.
- Border top, `1px solid rgba(34, 36, 38, 0.15)`, same as the outer menu border.
- Height, `0`. Margin, `.28571429rem 0`. Padding, `0`.
- Role, `separator`. Not focusable, skipped by keyboard navigation.

**File.** `assets/canvas-plugin-ui.js`

### canvas-popover

A click triggered anchored container for arbitrary content. Covers filter forms, column pickers, legends, preference sheets, bulk action panels, and micro confirmation dialogs. Uses `role="dialog"` with `aria-modal="false"` by default. Not form associated. Use when content is arbitrary and not a list of selectable options. For action menus use `canvas-menu-button`. For a single value selection use `canvas-dropdown`. For full overlay modals use `canvas-modal`.

**Usage**

```html
<canvas-popover label="Filter notes">
  <canvas-button slot="trigger" variant="ghost" size="sm">Filter</canvas-button>
  <div>
    <p>Filter notes</p>
    <canvas-dropdown label="Type" placeholder="Any type">
      <canvas-option value="office">Office visit</canvas-option>
      <canvas-option value="phone">Phone call</canvas-option>
    </canvas-dropdown>
  </div>
</canvas-popover>
```

**Icon only trigger with pointer and form**

The icon only trigger filter form pattern maps to `canvas-popover` with `pointer`. The arrow tethers the surface to the small trigger so the user sees which control opened the form.

```html
<canvas-popover pointer label="Filter notes">
  <canvas-button slot="trigger" variant="ghost" size="sm" aria-label="Filter notes">
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
      <path d="M0 1h14v2L9 8v5l-4-2V8L0 3z"/>
    </svg>
  </canvas-button>
  <div style="display: flex; flex-direction: column; gap: 12px">
    <p style="margin: 0; font-weight: 700">Filter notes</p>
    <canvas-dropdown label="Type" placeholder="Any type">
      <canvas-option value="office">Office visit</canvas-option>
      <canvas-option value="phone">Phone call</canvas-option>
    </canvas-dropdown>
    <canvas-input label="Author" placeholder="Any author"></canvas-input>
    <div style="display: flex; gap: 8px">
      <canvas-input label="From" type="date" style="flex:1"></canvas-input>
      <canvas-input label="To" type="date" style="flex:1"></canvas-input>
    </div>
    <div style="display: flex; justify-content: flex-end; gap: 8px; margin-top: 4px">
      <canvas-button variant="ghost" size="sm">Clear</canvas-button>
      <canvas-button variant="primary" size="sm">Apply</canvas-button>
    </div>
  </div>
</canvas-popover>
```

Three controls (Type, Author, date range) plus an action row. Date range counts as one control because the two inputs share a label. Clear plus Apply closes with the ghost then primary convention.

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `open` | boolean, reflected | false |
| `label` | string, required | none (sets surface `aria-label`) |
| `size` | `sm`, `md`, `lg`, `auto` | `md` |
| `direction` | `down`, `up` | auto, picks the side with more room when content does not fit below |
| `align` | `start`, `end` | auto, start when space allows, else end |
| `pointer` | boolean | false (no visual tether to the trigger) |
| `dismiss-on-scroll` | boolean | false (scroll moves the popover with the trigger by default) |

The `label` attribute is required because `role="dialog"` needs an accessible name. The size attribute sets a `max-width` default, `sm` 280 px, `md` 360 px, `lg` 480 px, and the surface shrinks below that cap when the viewport is narrower. `size="auto"` caps at the viewport width minus 16 px and lets the surface grow to its content width for wide tables, long labels, or content whose width is known only at runtime. `pointer` renders a 14 px speech balloon arrow on the side of the surface that faces the trigger, matching the `canvas-tooltip` artwork. The arrow tracks the trigger center even when the surface clamps to a viewport edge, and flips side with the surface under auto placement. Distance between the trigger and the surface uses the tooltip recipe (10 px gap, 8 px viewport margin) when `pointer` is set, and the tighter popover recipe (6 px gap, 4 px viewport margin) when it is not.

Popover is not modal. Outside click and Escape always dismiss. When the content needs to block the user until they respond, for example a destructive confirmation, use `canvas-modal` instead.

**Slots**

- `trigger`, the anchor element. The component automatically sets `aria-haspopup="dialog"` and `aria-expanded` on the slotted trigger when open state changes.
- default, arbitrary HTML content for the popover body.

**Events**

| Event | When |
|---|---|
| `open` | When the popover opens. No detail. |
| `close` | When the popover closes, whether by attribute removal, outside click, Escape, or a `close()` method call. |
| `cancel` | When the popover is dismissed by outside click or Escape, before `close`. Does not fire when the author removes `open` programmatically. |

**Methods**

- `open()`, adds the `open` attribute.
- `close()`, removes the `open` attribute.

**Keyboard navigation.** On the trigger, Enter or Space opens the popover through native button activation. Focus moves to the first focusable element inside the popover, or to the surface itself when the body has no focusable content, so Escape and screen reader announcements still work. Escape closes the popover, returns focus to the trigger, and dispatches a `cancel` event before the `close` event. Tab escapes the popover to the next document tab stop, no focus trap. Content that needs modality and focus trap belongs in `canvas-modal`. Outside click closes the popover and dispatches `cancel`.

**ARIA.** Trigger, `aria-haspopup="dialog"` and `aria-expanded="true"` or `aria-expanded="false"` are wired automatically on the slotted trigger element when open state changes. Icon only triggers must supply `aria-label` themselves. Surface, `role="dialog"`, `aria-modal="false"`, `aria-label` set from the component's `label` attribute. Without `label` the dialog has no accessible name, which is why the attribute is required.

**Placement.** On open, the component measures the trigger rectangle and the popover content against the viewport. Direction defaults to `down` when the content fits below the trigger. When it does not fit below, direction picks the side with more room. After the direction is chosen, `max-height` caps at the available space in that direction and the surface becomes scrollable when content exceeds the cap. Alignment defaults to `start` and flips to `end` when the start edge would clip the viewport. Explicit `direction` or `align` disable the corresponding axis auto flip. The surface is rendered with `position: fixed` so it escapes ancestor `overflow: hidden` and appears above normal stacking contexts.

**Scroll behavior.** By default the popover follows its trigger on scroll, repositioning continuously. When the trigger leaves the viewport, the surface is visually hidden without closing (via `visibility: hidden`). When the trigger scrolls back into view, the surface reappears. Set `dismiss-on-scroll` to close the popover on any scroll instead.

**Sizing.**

| Token or attribute | What it controls | Default |
|---|---|---|
| `size="sm"` | Max width | 280 px |
| `size="md"` | Max width | 360 px |
| `size="lg"` | Max width | 480 px |
| `size="auto"` | Max width | viewport minus 16 px, surface grows with content up to that cap |
| `--canvas-popover-max-width` | Override for max width | size attribute default |
| `--canvas-popover-max-height` | Author cap for max height | viewport minus 8 px (effectively unbounded) |

The surface uses `overflow-wrap: anywhere` so long unbreakable tokens such as IRIs or IDs break rather than produce horizontal scroll. The surface itself is not a scroll container. When body content may exceed the direction aware `max-height`, wrap it in `canvas-scroll-area vertical` with an explicit `max-height` and `aria-label`. Same contract as `canvas-card-body`. This keeps the popover free of ancestor overflow clipping that would otherwise cut off descendant `canvas-dropdown` or `canvas-combobox` menus.

**Visual spec.**

*Surface.*

- Background, `var(--color-surface, #FFFFFF)`.
- Border, `1px solid #d4d4d5`. Radius, `var(--radius, .28571429rem)`. Matches `canvas-tooltip` and `canvas-card` so anchored surfaces share one container gray.
- Shadow, `0 2px 4px 0 rgba(34, 36, 38, 0.12), 0 2px 10px 0 rgba(34, 36, 38, 0.15)`, same as the `canvas-menu-button` menu.
- Padding, `1em 1.14285714em`. The surface holds arbitrary content, padding belongs to the container not the options.
- Text, font size `1rem`, line height `1.4285714`, color `var(--color-text, rgba(0, 0, 0, 0.87))`.
- Positioning, `position: fixed` with inline top and left values set by the component. Z index, `2000`.
- Offset from trigger, 6 px gutter without `pointer`, 10 px gutter with `pointer` (matches `canvas-tooltip`).
- Overflow, none. Long unbreakable tokens are broken by `overflow-wrap: anywhere`.

*Height.*

- No hard default cap. The effective `max-height` is `min(--canvas-popover-max-height override, calc(100vh - 8px), available space in chosen direction)`.
- When content fits below the trigger, direction is down. When content does not fit below, direction is whichever of up or down has more room. After the direction is chosen, `max-height` caps at that side's available space.
- Scroll inside the surface is automatic when content exceeds the cap.

*Pointer artwork.*

- 14 px by 7 px SVG triangle, rotated 45 degrees equivalent via path geometry. Border color `#d4d4d5`, fill `var(--color-surface, #FFFFFF)` on the overlay cover.
- Layering, grey arrow sits behind the surface so only the protruding tip shows in the border color. White cover sits above the surface and masks the 1 px surface border at the 14 px joint so the arrow reads as continuous with the surface body. Same technique as the tooltip.
- Offset, 5 px of the 7 px arrow protrudes outside the surface, 2 px overlaps behind the surface so the cover has a surface to paint on.
- Position, arrow tracks the trigger center even when the surface edge clamps inward from the viewport. Clamp inside the surface keeps the arrow 6 px from each corner so it cannot slide into the border radius.
- Flip, when auto placement flips direction from down to up, the arrow moves from the surface top edge to the surface bottom edge and the SVG inverts so the tip still points at the trigger.
- Distance, when `pointer` is set the surface sits 10 px from the trigger with 8 px of viewport margin. Without `pointer`, 6 px gap and 4 px margin.

*Border gray alignment.*

Anchored surfaces and containers share one gray. Form indicators share a second gray that darkens on hover.

- `#d4d4d5` on container chrome, `canvas-tooltip`, `canvas-popover` surface, `canvas-card` outer border.
- `rgba(34, 36, 38, 0.15)` on form controls and form indicators, `canvas-input`, `canvas-dropdown`, `canvas-combobox`, `canvas-textarea`, `canvas-multi-select`, `canvas-checkbox` resting, `canvas-radio` resting. Darkens to `rgba(34, 36, 38, 0.35)` on hover, to `#85b7d9` on focus.

Do not introduce a third gray without mapping it into one of these two categories.

**File.** `assets/canvas-plugin-ui.js`

### canvas-tabs

A tabbed interface with automatic panel switching, bold-shift prevention, badge support, and keyboard navigation. Registers four elements from one file. `canvas-tabs` is the controller, `canvas-tab` is the tab button, `canvas-tab-label` is the text wrapper inside a tab, and `canvas-tab-panel` is the content area.

**Usage**

```html
<canvas-tabs>
  <canvas-tab for="panel-coverages" active>
    <canvas-tab-label>Coverages</canvas-tab-label>
  </canvas-tab>
  <canvas-tab for="panel-claims" badge="2">
    <canvas-tab-label>Outstanding Claims</canvas-tab-label>
  </canvas-tab>
  <canvas-tab for="panel-auths">
    <canvas-tab-label>Authorizations</canvas-tab-label>
  </canvas-tab>

  <canvas-tab-panel id="panel-coverages">
    <!-- Coverages content -->
  </canvas-tab-panel>
  <canvas-tab-panel id="panel-claims">
    <!-- Claims content -->
  </canvas-tab-panel>
  <canvas-tab-panel id="panel-auths">
    <!-- Authorizations content -->
  </canvas-tab-panel>
</canvas-tabs>
```

**Attributes (canvas-tab)**

| Attribute | Values | Default |
|---|---|---|
| `for` | string (panel ID) | none (required, maps to panel) |
| `badge` | string | none (no badge rendered) |
| `active` | boolean | false (first tab with `active` becomes selected) |

**Attributes (canvas-tab-panel)**

| Attribute | Values | Default |
|---|---|---|
| `id` | string | none (required, matched by tab `for` attribute) |

**Events**

| Event | When | Detail |
|---|---|---|
| `tab-change` | When the active tab changes. Bubbles and composes. | `{ index: number, panel: string }` |

**Panel visibility.** Only one panel is visible at a time. Inactive panels get the `hidden` attribute. Active panels get the `visible` attribute for CSS targeting.

**Bold-shift prevention.** The component handles this internally. Tab buttons reserve width for the bold (700) state so sibling tabs do not shift when the active tab changes weight.

**Badge support.** Set the `badge` attribute on a `canvas-tab` to show a count indicator next to the label.

**Trailing content.** Elements placed after `canvas-tab-label` inside a `canvas-tab` are rendered after the label text. Use for icons or custom indicators.

**Label truncation.** Long labels are truncated with ellipsis. A `title` tooltip shows the full text on hover.

**Overflow fade.** When tabs overflow horizontally, CSS mask gradients fade the edges to indicate scrollable content.

**Keyboard navigation.** Left and Right arrow keys move focus between tab items within the tab menu. Home jumps to the first tab, End jumps to the last tab. Enter or Space activates the focused tab and shows its panel. Focus follows selection.

**ARIA.** Tab items use `role="tab"`, the container uses `role="tablist"`, and panels use `role="tabpanel"`. Active tab has `aria-selected="true"`, inactive tabs have `aria-selected="false"`. Each tab has `aria-controls` pointing to its panel ID. Each panel has `aria-labelledby` pointing to its tab ID.

**Initial selection.** The first tab with the `active` attribute becomes selected on mount. If no tab has `active`, the first tab is selected.

**Component tokens**

| Token | What it controls | Default |
|---|---|---|
| `--tab-bar-height` | Height of the tab bar | `45.41px` |
| `--tab-label-max-width` | Maximum label width before truncation | `160px` |
| `--tab-label-min-width` | Minimum label width | `60px` |

**File.** `assets/canvas-plugin-ui.js`

### canvas-accordion

A collapsible section container with chevron animation, ARIA, and keyboard support. Registers four elements from one file. `canvas-accordion` is the outer container (no Shadow DOM), `canvas-accordion-item` wraps each section, `canvas-accordion-title` holds the clickable header, and `canvas-accordion-content` holds the collapsible body.

**Usage**

```html
<canvas-accordion>
  <canvas-accordion-item open>
    <canvas-accordion-title>Patient Demographics</canvas-accordion-title>
    <canvas-accordion-content>
      <!-- Demographics form -->
    </canvas-accordion-content>
  </canvas-accordion-item>
  <canvas-accordion-item>
    <canvas-accordion-title>Contacts</canvas-accordion-title>
    <canvas-accordion-content>
      <!-- Contacts content -->
    </canvas-accordion-content>
  </canvas-accordion-item>
</canvas-accordion>
```

**Attributes (canvas-accordion-item)**

| Attribute | Values | Default |
|---|---|---|
| `open` | boolean | false (collapsed on mount) |

**Properties (canvas-accordion-item)**

| Property | Type | Description |
|---|---|---|
| `open` | boolean | Get or set expanded state. Setting triggers expand/collapse. |

**Methods (canvas-accordion-item)**

| Method | Description |
|---|---|
| `toggle()` | Toggles between expanded and collapsed. |

**Events**

| Event | When | Detail |
|---|---|---|
| `toggle` | When an item expands or collapses. Bubbles and composes. | `{ open: boolean }` |

**Title content.** The default slot on `canvas-accordion-title` accepts any content. Text, badges, buttons, toggles, and checkboxes can all be placed inside. The chevron icon is rendered automatically by the component and always appears first.

**Actions in title.** Place interactive elements directly inside `canvas-accordion-title`. The accordion inspects the event path on its trigger handlers and skips expand or collapse when a click or keyboard activation originates from an interactive descendant. The filter covers `canvas-button`, `canvas-toggle`, `canvas-checkbox`, `canvas-radio`, `canvas-dropdown`, `canvas-combobox`, `canvas-multi-select`, `canvas-input`, `canvas-date-input`, `canvas-textarea`, plain HTML `button`, `a[href]`, `input`, `select`, `textarea`, and any element carrying an ARIA role of button, switch, checkbox, radio, link, menuitem, tab, or option. Plugin authors do not need to add `event.stopPropagation` on interactive children. When mixing text and interactive elements, use flex utilities on the title content.

```html
<canvas-accordion-title>
  <span style="flex: 1">Notifications</span>
  <canvas-toggle label="" checked></canvas-toggle>
</canvas-accordion-title>
```

**Multiple open.** Multiple items can be open simultaneously. There is no exclusive mode.

**Keyboard.** Enter or Space on a focused title toggles that item. Focus is managed via `tabindex="0"` on the title element.

**Accessibility.** Title has `role="button"` and `aria-expanded`. Content has `role="region"`.

**Container padding.** `canvas-accordion` and `canvas-accordion-item` carry no horizontal padding of their own. Top level accordions sit flush with the edges of their container and rely on the container to supply horizontal inset, the same way `h1` through `h5`, `<p>`, and `canvas-button` rely on their parent. This matches the `padding: 0` rule applied to heading elements in `canvas-plugin-ui.css` and keeps the accordion from double padding when it lives inside a `canvas-card`, a `sample-card`, or any shell that already pads its children. See DESIGN.md Container Padding Responsibility for the full rule.

**Nested indent.** When a `canvas-accordion-item` sits inside another accordion's `canvas-accordion-content`, a global CSS rule in `canvas-plugin-ui.css` applies left padding of `--canvas-accordion-nested-indent` so the hierarchy is visible. The rule only matches nested items, not top level ones. Depth compounds naturally because each nested content holds its own nested items, so level two steps in by one `--space-small` from level one, level three by two `--space-small` from level one, and so on.

**Tokens**

| Token | What it controls | Default |
|---|---|---|
| `--canvas-accordion-nested-indent` | Left padding applied to any `canvas-accordion-item` placed inside another accordion's content. Has no effect on top level items. | `var(--space-small, 12px)` |
| `--font-family` | Title font family. | Inherits from the global font stack. |

**File.** `assets/canvas-plugin-ui.js`

### canvas-modal

An overlay dialog with backdrop, focus trapping, and three size variants. Registers four elements from one file. `canvas-modal` is the outer container with backdrop and scroll layer, `canvas-modal-header` is the optional title bar, `canvas-modal-content` is the padded body area, and `canvas-modal-footer` is the gray actions area.

The modal does not render on page load. Call `modal.open()` to show it and `modal.dismiss()` to hide it. Escape and backdrop click dismiss by default unless the `persistent` attribute is set.

**Usage**

```html
<canvas-modal id="confirm-dialog" size="small">
  <canvas-modal-header dismissable>Confirm Deletion</canvas-modal-header>
  <canvas-modal-content>
    <p>Are you sure you want to delete this record? This action cannot be undone.</p>
  </canvas-modal-content>
  <canvas-modal-footer>
    <canvas-button variant="ghost" onclick="document.getElementById('confirm-dialog').dismiss()">Cancel</canvas-button>
    <canvas-button variant="danger">Delete</canvas-button>
  </canvas-modal-footer>
</canvas-modal>

<canvas-button onclick="document.getElementById('confirm-dialog').open()">Delete Record</canvas-button>
```

**Attributes (canvas-modal)**

| Attribute | Values | Default |
|---|---|---|
| `size` | `small`, `medium`, `full` | `medium` |
| `persistent` | boolean | false (when set, Escape and backdrop click are disabled) |

**Attributes (canvas-modal-header)**

| Attribute | Values | Default |
|---|---|---|
| `dismissable` | boolean | false (when set, shows a close X button) |

**Attributes (canvas-modal-content)**

| Attribute | Values | Default |
|---|---|---|
| `flush` | boolean | false (when set, removes default 1.5rem padding) |

**Properties (canvas-modal)**

| Property | Type | Description |
|---|---|---|
| `isOpen` | boolean | Read-only. Returns whether the modal is currently visible. |

**Methods (canvas-modal)**

| Method | Description |
|---|---|
| `open()` | Shows the modal, traps focus, fires `open` event. |
| `dismiss()` | Hides the modal, restores focus, fires `dismiss` event. |

**Events**

| Event | When |
|---|---|
| `open` | When the modal opens. Bubbles and composes. |
| `dismiss` | When the modal closes. Bubbles and composes. |

**Size rules.**
- **small** (35rem). Confirmations, destructive actions, clinical confirmations, simple notifications. Use when the modal has no form fields or fewer than 3 fields.
- **medium** (52.5rem). Form dialogs, data entry, edit screens. Use when the modal has 4 or more form fields or needs multi-column rows.
- **full** (calc(100vw - 6rem) width, min-height calc(100vh - 6rem)). Complex views needing maximum space. Document viewers, scheduling interfaces, data import screens.

**Focus management.** On open, focus moves to the first focusable element. On dismiss, focus returns to the element that triggered the modal. Tab/Shift+Tab cycle within the modal. The component knows about canvas-button, canvas-input, canvas-dropdown, canvas-combobox, and canvas-multi-select for focus trapping.

**Backdrop.** Two-layer backdrop prevents overscroll bounce. The dark overlay is fixed at z-index 1000. The scroll layer sits at z-index 1001 with `overflow-y: auto`. Background scroll is disabled while the modal is open.

**No inner elements required.** All children (header, content, footer) are optional. Content placed directly in the modal renders in the modal box without wrappers.

**Flush content.** Use the `flush` attribute on `canvas-modal-content` for edge-to-edge content like tables.

```html
<canvas-modal-content flush>
  <canvas-table>...</canvas-table>
</canvas-modal-content>
```

**Locked component.** No visual customization tokens. Box shadow, backdrop color, header/footer styling are all fixed.

**File.** `assets/canvas-plugin-ui.js`

### canvas-table

A data table with modifier attributes for compact, celled, selectable, sticky, and striped variants. Registers five elements from one file. `canvas-table` is the outer container (renders as CSS table), `canvas-table-head` is the header group, `canvas-table-body` is the body group, `canvas-table-row` is a row, and `canvas-table-cell` is a cell (renders as header or body cell depending on context).

**Usage**

```html
<canvas-table aria-label="Active medications">
  <canvas-table-head>
    <canvas-table-row>
      <canvas-table-cell>Medication</canvas-table-cell>
      <canvas-table-cell>Dose</canvas-table-cell>
      <canvas-table-cell>Status</canvas-table-cell>
    </canvas-table-row>
  </canvas-table-head>
  <canvas-table-body>
    <canvas-table-row>
      <canvas-table-cell bold>Metformin</canvas-table-cell>
      <canvas-table-cell>500 mg</canvas-table-cell>
      <canvas-table-cell><canvas-badge color="green" size="mini">Active</canvas-badge></canvas-table-cell>
    </canvas-table-row>
  </canvas-table-body>
</canvas-table>
```

**Attributes (canvas-table)**

| Attribute | Values | Default |
|---|---|---|
| `compact` | boolean | false (tighter padding, same font size) |
| `celled` | boolean | false (visible borders between all cells) |
| `selectable` | boolean | false (pointer cursor, hover highlight on rows) |
| `sticky` | boolean | false (sticky header row) |
| `striped` | boolean | false (alternating row backgrounds) |

**Attributes (canvas-table-row)**

| Attribute | Values | Default |
|---|---|---|
| `positive` | boolean | false (green tint for normal/success) |
| `warning` | boolean | false (yellow tint for borderline/pending) |
| `negative` | boolean | false (red tint for abnormal/error) |
| `active` | boolean | false (gray highlight for selected row) |

**Attributes (canvas-table-cell)**

| Attribute | Values | Default |
|---|---|---|
| `actions` | boolean | false (right-aligned, no-wrap, narrow width for action buttons) |
| `bold` | boolean | false (font-weight 700) |
| `colspan` | boolean | false (cell spans full row width, hides siblings) |
| `width` | string | none (explicit width, e.g. "200px") |

Combine modifier attributes on the same `canvas-table` element as needed.

```html
<canvas-table compact celled sticky selectable aria-label="Claims">
  ...
</canvas-table>
```

**Row state colors.** Add `positive`, `warning`, or `negative` to individual rows for clinical status indication (lab results, claim outcomes). States are mutually exclusive with priority order: positive, warning, negative, active.

**Inline actions.** Use the `actions` attribute on the last cell in a row to right-align action buttons and prevent wrapping.

```html
<canvas-table-row>
  <canvas-table-cell bold>Annual Wellness Visit</canvas-table-cell>
  <canvas-table-cell>Mar 15, 2026</canvas-table-cell>
  <canvas-table-cell actions>
    <canvas-button variant="ghost" size="sm">View</canvas-button>
    <canvas-button size="sm">Edit</canvas-button>
  </canvas-table-cell>
</canvas-table-row>
```

**Component tokens**

| Token | What it controls | Default |
|---|---|---|
| `--canvas-table-cell-padding` | Body cell padding | `0.5rem 1rem` (compact: `0.35rem 0.7rem`) |
| `--canvas-table-header-padding` | Header cell padding | `0.5rem 1rem` (compact: `0.5rem 0.7rem`) |
| `--canvas-table-header-bg` | Header background | `#FFFFFF` |
| `--canvas-table-border` | Row and cell border color | `rgba(34, 36, 38, 0.1)` |
| `--canvas-table-stripe-bg` | Striped row background | `rgba(0, 0, 50, 0.02)` |
| `--canvas-table-row-positive-bg` | Positive row background | `#fcfff5` |
| `--canvas-table-row-positive-text` | Positive row text | `#2c662d` |
| `--canvas-table-row-warning-bg` | Warning row background | `#fffaf3` |
| `--canvas-table-row-warning-text` | Warning row text | `#573a08` |
| `--canvas-table-row-negative-bg` | Negative row background | `#fff6f6` |
| `--canvas-table-row-negative-text` | Negative row text | `#9f3a38` |
| `--canvas-table-row-active-bg` | Active/selected row background | `#e0e0e0` |

**File.** `assets/canvas-plugin-ui.js`

### canvas-sortable-list

A drag to reorder list with FLIP animation, keyboard support, auto scroll during drag, and optional cross list moves. Registers two elements from one file. `canvas-sortable-list` is the container and `canvas-sortable-item` wraps each draggable item.

Each item renders a drag handle automatically. Drag the handle to reorder within the list, or to move the item into another list in the same group.

**Usage**

```html
<canvas-sortable-list>
  <canvas-sortable-item>First item</canvas-sortable-item>
  <canvas-sortable-item>Second item</canvas-sortable-item>
  <canvas-sortable-item>Third item</canvas-sortable-item>
</canvas-sortable-list>
```

**Cross list usage.** Give two or more lists the same `group` value. Items can be dragged between them and the matching keyboard bindings become active.

```html
<canvas-sortable-list group="tickets" id="backlog">
  <canvas-sortable-item data-id="t-1">Update coverage form</canvas-sortable-item>
  <canvas-sortable-item data-id="t-2">Fix date picker</canvas-sortable-item>
</canvas-sortable-list>

<canvas-sortable-list group="tickets" id="done">
  <canvas-sortable-item data-id="t-3">Chart note signed</canvas-sortable-item>
</canvas-sortable-list>
```

**Attributes on `canvas-sortable-list`**

| Attribute | Values | Default | Purpose |
|---|---|---|---|
| `group` | string | none | Lists sharing a group value exchange items. Omitted means the list is isolated, identical to single list behavior. |
| `accept` | comma separated group names | the list's own group | Extra groups this list will receive from without being a member. Useful for one way flows like an archive bucket. |
| `pull` | `move`, `clone` | `move` | `clone` leaves the original in place and drops a copy into the target list. Enables template palettes. |
| `disabled` | boolean | false | Items cannot be dragged out, list cannot receive drops. |

**Events**

All events bubble and compose, so one listener at a common ancestor catches every change on the page.

| Event | When | Detail | Cancelable |
|---|---|---|---|
| `reorder` | After a within list move commits | `{ item, oldIndex, newIndex, list }` | no |
| `move` | After a cross list move commits | `{ item, fromList, toList, oldIndex, newIndex }` | no |
| `change` | After any move commits | same as the one that fired, plus `type` equal to `reorder` or `move` | no |
| `beforereorder`, `beforemove`, `beforechange` | Before the drop lands | same as their twin | yes, `preventDefault()` snaps the item back |

The `change` event is a single listener path when you do not care to distinguish within list from cross list. Use `beforemove` and `beforereorder` for permission gates and column capacity rules. Always pair a cancel with visible user feedback.

**Property getter**

`list.items` returns the live array of `canvas-sortable-item` children in current DOM order. Rebuilds from the DOM on each read, no cached state.

**Slot.** `canvas-sortable-item` has a default slot for content. The drag handle is rendered inside Shadow DOM and cannot be replaced.

**Drag behavior.** Pointer down on the handle starts a drag. The dragged item becomes a fixed overlay following the cursor. A placeholder holds space at the current target position. As the cursor moves past item midpoints, the placeholder shifts and other items animate into place via FLIP transforms (200ms ease). On pointer up, the item is inserted at the placeholder position and the matching `reorder` or `move` event fires, followed by `change`.

**Cross list drop indication.** The placeholder holds an empty gap at the insertion point and items animate into place via FLIP. No color indicator is applied by default. The list currently under the cursor carries a `data-drop-active` attribute that consumers can style on their own for a column highlight or insertion bar if desired.

**Auto scroll during drag.** When the list is inside a scrollable ancestor, dragging an item toward the top or bottom edge of that ancestor makes the ancestor auto scroll. The component resolves the nearest element with `overflow-y` of `auto` or `scroll` at drag start, falling back to the document scroller. A 48 pixel edge hotspot drives a `requestAnimationFrame` loop at up to 12 pixels per frame, ramped by cursor proximity. Stops on pointer up, when the cursor leaves the hotspot, or when the scroller hits its boundary.

**Keyboard.** Focus the drag handle with Tab.

- `ArrowUp` and `ArrowDown` reorder within the current list. Each keypress fires `reorder` and `change`, and announces position N of M in the list label.
- `ArrowLeft` and `ArrowRight` move the item into the previous or next list in the same group. Each keypress fires `move` and `change`, and announces source and destination labels. Active only when the list has a `group` attribute and a compatible sibling list exists. Sibling resolution walks all compatible lists by screen position left to right, not by strict DOM sibling order.

**Cross list cancel.** `beforemove`, `beforereorder`, and `beforechange` are cancelable. Calling `e.preventDefault()` in a handler snaps the item back to its source position and suppresses the success events. Always pair a cancel with visible user feedback, a toast or inline message. A silent cancel reads as a visual glitch to the user.

**ARIA.** A shared polite live region announces every move. Label lists explicitly so announcements read naturally. Give each participating list an `aria-labelledby` pointing at its column heading, or an `aria-label` with the column name. Without a label, the announcer falls back to the list's `id`, then to the generic word "list". Within list moves announce "Moved item to position N of M in `<label>`.". Cross list moves announce "Moved item from `<source label>` to `<destination label>`, position N of M.".

**Single drop vs bulk changes.** For small lists and fast backends, fire an API call on every `move` or `reorder`. For larger boards, accumulate `change` events in a `Map` keyed by id and flush on Save or after a debounced timer. The Map collapses repeated moves of the same item so only the final position ships in one payload.

**FLIP animation.** Items animate from old to new position using `transform: translateY()` with a 200ms ease transition.

**Empty list drop target.** An empty list in a cross list group still accepts drops. A default `min-height` via `--canvas-sortable-min-height` keeps the target reachable.

**Component tokens**

| Token | What it controls | Default |
|---|---|---|
| `--radius` | Border radius on drag overlay and handle hover | `.28571429rem` |
| `--canvas-sortable-min-height` | Minimum height so empty lists stay reachable as drop targets | `calc(var(--space-medium) * 2)` |

**File.** `assets/canvas-plugin-ui.js`

### canvas-sidebar-layout

A two-column layout with a fixed-width sidebar and flexible content area. Registers three elements from one file. `canvas-sidebar-layout` is the flex row container, `canvas-sidebar` is the fixed-width left column, and `canvas-content` is the flexible right column.

**Usage**

```html
<canvas-sidebar-layout style="--canvas-sidebar-layout-height: 100vh">
  <canvas-sidebar>
    <nav>
      <!-- Navigation items -->
    </nav>
  </canvas-sidebar>
  <canvas-content>
    <!-- Main content -->
  </canvas-content>
</canvas-sidebar-layout>
```

**Attributes (canvas-sidebar-layout)**

| Attribute | Values | Default |
|---|---|---|
| `fullscreen` | boolean | false (when set, layout fills the viewport with fixed positioning) |

**Attributes (canvas-sidebar)**

| Attribute | Values | Default |
|---|---|---|
| `variant` | `default`, `narrow`, `wide` | `default` |

**Sidebar widths.**
- **default** (260px). Standard sidebar for navigation and settings.
- **narrow** (210px). Compact sidebar for space-constrained layouts.
- **wide** (400px). Expanded sidebar for content-heavy navigation.

**Slots.** All three elements have default slots accepting any content.

**Overflow.** Both sidebar and content areas scroll vertically independently. The sidebar has custom webkit scrollbar styling (8px, semi-transparent thumb).

**Fullscreen mode.** The `fullscreen` attribute applies `position: fixed; inset: 0` to fill the entire viewport.

**Component tokens**

| Token | What it controls | Default |
|---|---|---|
| `--canvas-sidebar-layout-height` | Layout height | `auto` |
| `--canvas-sidebar-width` | Sidebar width (overrides variant) | `260px` |
| `--canvas-sidebar-bg` | Sidebar background | `#f5f5f5` |
| `--canvas-sidebar-padding` | Sidebar padding | `0` |
| `--canvas-content-bg` | Content area background | `#fff` |
| `--canvas-content-padding` | Content area padding | `0` |

**File.** `assets/canvas-plugin-ui.js`

### canvas-loader

A loading spinner matching the Canvas home-app. Renders a spinning circular border with a gray track and a colored arc. Uses a flex container for centering with three positioning modes.

**Usage**

```html
<!-- Inline (default, normal document flow) -->
<canvas-loader></canvas-loader>
<canvas-loader size="large"></canvas-loader>
<canvas-loader size="large" centered text="Loading ..."></canvas-loader>

<!-- Overlay (fills relative parent, light backdrop by default) -->
<canvas-loader mode="overlay" size="large"></canvas-loader>
<canvas-loader mode="overlay" backdrop="dark" size="large" text="Refreshing ..."></canvas-loader>
<canvas-loader mode="overlay" backdrop="none" size="large"></canvas-loader>

<!-- Fullscreen (fills viewport, light backdrop by default) -->
<canvas-loader mode="fullscreen" size="large"></canvas-loader>
<canvas-loader mode="fullscreen" backdrop="dark" size="large" text="Please wait ..."></canvas-loader>

<!-- Inverted (for dark backgrounds, works with any mode) -->
<canvas-loader inverted size="large"></canvas-loader>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `size` | `mini`, `small`, (default), `large` | default (2.28rem) |
| `mode` | (default), `overlay`, `fullscreen` | default (inline block) |
| `centered` | boolean | false (centers inline loader horizontally) |
| `inverted` | boolean | false (light spinner and text for dark backgrounds) |
| `backdrop` | `light`, `dark`, `none` | `light` for overlay/fullscreen, ignored in inline |
| `text` | string | none (label below the spinner) |
| `aria-label` | string | `"Loading"` |

**Positioning modes.** The component is always a flex container that centers the spinner. The mode attribute controls how that container is sized and positioned.

- **Inline (default).** Normal document flow. The container is a block element. Use `centered` to horizontally center it. No backdrop.
- **Overlay.** `position: absolute; inset: 0`. Fills the nearest relatively positioned parent. The parent must have `position: relative`. Includes a light semi-transparent backdrop by default.
- **Fullscreen.** `position: fixed; inset: 0`. Fills the entire viewport. Includes a light semi-transparent backdrop by default.

**Backdrop.** Overlay and fullscreen modes show a light backdrop (`rgba(255, 255, 255, 0.85)`) by default. Set `backdrop="dark"` for a dark backdrop (`rgba(0, 0, 0, 0.5)`) which automatically inverts the spinner and text colors. Set `backdrop="none"` to remove the backdrop. The backdrop attribute is ignored in inline mode.

**Sizes.** Mini (1rem), small (1.71rem), default (2.28rem), large (3.42rem). Canvas most commonly uses `size="large"`.

**Text label.** The `text` attribute renders a label below the spinner. Font size scales with the size attribute. Use "Loading ..." for consistency with Canvas patterns.

**Inverted mode.** For use on dark or colored backgrounds. Switches the track to rgba(255, 255, 255, 0.15) and the arc to white. The dark backdrop automatically inverts colors without needing the `inverted` attribute.

**Events.** None.

**Component tokens**

| Token | What it controls | Default |
|---|---|---|
| `--canvas-loader-size` | Spinner width and height | `2.28571429rem` |
| `--canvas-loader-size-mini` | Mini spinner dimensions | `1rem` |
| `--canvas-loader-size-small` | Small spinner dimensions | `1.71428571rem` |
| `--canvas-loader-size-large` | Large spinner dimensions | `3.42857143rem` |
| `--canvas-loader-border-width` | Track and arc border width | `.2em` |
| `--canvas-loader-track-color` | Track circle color | `rgba(0, 0, 0, 0.1)` |
| `--canvas-loader-arc-color` | Spinning arc color | `#767676` |
| `--canvas-loader-track-color-inverted` | Track color on dark backgrounds | `rgba(255, 255, 255, 0.15)` |
| `--canvas-loader-arc-color-inverted` | Arc color on dark backgrounds | `#fff` |
| `--canvas-loader-backdrop` | Light backdrop color | `rgba(255, 255, 255, 0.85)` |
| `--canvas-loader-backdrop-dark` | Dark backdrop color | `rgba(0, 0, 0, 0.5)` |
| `--canvas-loader-text-color` | Label text color | `rgba(0, 0, 0, 0.87)` |
| `--canvas-loader-text-color-inverted` | Label text color on dark backgrounds | `rgba(255, 255, 255, 0.9)` |
| `--canvas-loader-text-gap` | Space between spinner and label | `.78571429rem` |
| `--canvas-loader-font-family` | Label font family | inherited from --font-family |
| `--canvas-loader-font-size` | Label font size | `1em` |
| `--canvas-loader-z-index` | Z-index for overlay and fullscreen | `1000` |
| `--canvas-loader-min-height` | Min height for inline container | `auto` |

**File.** `assets/canvas-plugin-ui.js`

### canvas-progress

A horizontal fill bar matching the Canvas home-app. Shows completion percentages, match scores, and campaign tracking. The bar fills from left to right based on the value attribute.

**Usage**

```html
<canvas-progress value="65" label></canvas-progress>

<canvas-progress value="88" color="green" size="small"></canvas-progress>

<canvas-progress value="40" active label></canvas-progress>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `value` | 0 to 100 (number) | 0 |
| `color` | `blue`, `grey`, `green`, `red`, `orange` | `blue` |
| `size` | `tiny`, `small`, (default) | default |
| `active` | boolean | false (pulsing animation when set) |
| `label` | boolean | false (shows percentage text inside bar when set) |

**Sizes.** Default (1.75em bar height) for standalone progress indicators. Small (1em) for campaign lists and compact layouts. Tiny (0.5em) for inline match scores. The label is automatically hidden at tiny size because the bar is too short for text.

**Colors.** Blue is the default and matches active campaign progress in Canvas. Grey for inactive or selected states. Green for match scores and success indicators. Red and orange for error and warning contexts. The color is always set by the consumer. The component does not change color based on the percentage value.

**Active animation.** The `active` attribute adds a pulsing white sweep animation across the bar, matching the Canvas home-app active progress animation.

**ARIA.** The bar element has `role="progressbar"`, `aria-valuenow`, `aria-valuemin="0"`, and `aria-valuemax="100"`.

**Component tokens**

| Token | What it controls | Fallback chain |
|---|---|---|
| `--canvas-progress-track` | Track background | `rgba(0, 0, 0, 0.1)` |
| `--canvas-progress-bar` | Bar fill color | color attribute value |

**File.** `assets/canvas-plugin-ui.js`

### canvas-tooltip

An infrastructure component that activates a global tooltip system. Place it once in the body. It renders nothing visible. On hover over any element with a `data-canvas-tooltip` attribute, it shows a positioned tooltip with an arrow pointing at the trigger. This is different from UI components. It is placed once per page and activates behavior via data attributes on other elements.

**Usage**

```html
<!-- Place once in the body -->
<canvas-tooltip></canvas-tooltip>

<!-- Add data-canvas-tooltip to any element -->
<canvas-button data-canvas-tooltip="Edit this record" size="sm" variant="ghost">Edit</canvas-button>
<canvas-button data-canvas-tooltip="Previous day" data-canvas-tooltip-position="bottom">←</canvas-button>
<canvas-badge data-canvas-tooltip="Coverage verified" data-canvas-tooltip-inverted>Active</canvas-badge>

<!-- Truncated text -->
<canvas-table-cell style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap"
  data-canvas-tooltip="Metformin Hydrochloride Extended-Release 500mg">
  Metformin Hydrochloride Extended-Release 500mg
</canvas-table-cell>

<!-- Delayed tooltip for disabled state explanation -->
<canvas-toggle data-canvas-tooltip="Disabled by admin policy" data-canvas-tooltip-inverted data-canvas-tooltip-delay="1000" disabled label="Auto-save"></canvas-toggle>
```

**Trigger attributes (on any element)**

| Attribute | Values | Default |
|---|---|---|
| `data-canvas-tooltip` | string | required (tooltip text) |
| `data-canvas-tooltip-position` | `top`, `bottom`, `left`, `right` | `top` |
| `data-canvas-tooltip-inverted` | boolean | false (dark background with white text) |
| `data-canvas-tooltip-delay` | number (ms) | 0 |

**How it works.** On connect, the component queries all `[data-canvas-tooltip]` elements and attaches `mouseenter`/`mouseleave` listeners to each one. A MutationObserver watches for dynamically added elements. On hover, it reads the text and attributes, positions a shared floating div relative to the trigger, and shows it. On leave, hides it. Only one tooltip is visible at a time.

**Viewport flipping.** If the tooltip would overflow the viewport edge on the requested side, it flips to the opposite side automatically.

**Visual treatment.** Matches the Canvas home-app tooltip. White background, 1px solid #d4d4d5 border, .28571429rem border-radius, drop shadow, .71428571em arrow rotated 45deg. Inverted variant uses #1b1c1d background with white text and no border/shadow.

**Infrastructure component.** Unlike UI components, `canvas-tooltip` is placed once per page, not per element. It does not render visible content. The double registration guard prevents issues if it appears multiple times. The `connectedCallback` creates the shared tooltip div and attaches listeners. The `disconnectedCallback` cleans up both.

**File.** `assets/canvas-plugin-ui.js`

### canvas-divider

A horizontal rule matching the Canvas home-app. Separates content sections with a visible line or acts as an invisible spacer. When text content is placed inside, it renders a centered label with lines extending to each side.

**Usage**

```html
<canvas-divider></canvas-divider>

<canvas-divider fitted></canvas-divider>

<canvas-divider>Or</canvas-divider>

<canvas-divider hidden></canvas-divider>
```

**Attributes**

| Attribute | Values | Default |
|---|---|---|
| `fitted` | boolean | false (removes vertical margin when set) |
| `hidden` | boolean | false (invisible line, spacing only) |

**Slot.** Default slot accepts text content. When text is present, the divider switches from a plain horizontal rule to the text-between-lines layout where the label sits centered between two lines. When the slot is empty, it renders a standard `<hr>`.

**Fitted.** Removes the default 1rem vertical margin. Use between tightly packed items where no extra spacing is wanted.

**Hidden.** Makes the line invisible while preserving the vertical space from margin. Used for spacing in print layouts or between sections where a visible line would be too heavy.

**ARIA.** The divider has `role="separator"`. When text is present, screen readers announce the text content.

**Component tokens**

| Token | What it controls | Fallback chain |
|---|---|---|
| `--canvas-divider-margin` | Vertical margin | `1rem 0` |
| `--canvas-divider-border` | Line color | `var(--color-border, rgba(34, 36, 38, 0.15))` |
| `--canvas-divider-color` | Text color | `var(--color-text, rgba(0, 0, 0, 0.85))` |
| `--canvas-divider-font-size` | Text label size | `0.85714286rem` |

**File.** `assets/canvas-plugin-ui.js`

