# Web Components

Reference for the Canvas plugin web component system. Covers how components load, how the token system works, and the API for each component. Read this before writing any plugin that uses `<canvas-*>` elements.

## Loading Components

Components work with zero external dependencies. No tokens.css, no base.css, no linked stylesheets. Every visual default is hardcoded inside the component. External token files are optional overrides.

There are two loading modes depending on how the plugin is structured.

### Inline mode

For simple single-page plugins or demos, paste the component JS file contents directly into a `<script>` tag before any markup that uses the component. Every file has a double registration guard so pasting the same component twice is safe.

```html
<script>
  /* contents of canvas-button.js */
</script>

<canvas-button>Save</canvas-button>
```

### Plugin mode

For plugins that use SimpleAPI routing, the design system ships as three static files served through dedicated API routes.

#### Bundling

The bundle script at `scripts/bundle.sh` concatenates all component JS files into a single `canvas-components.js` and copies `tokens.css` and `typography.css` alongside it into the target directory.

```bash
./scripts/bundle.sh /path/to/plugin/package/static/
```

This produces three files in the target `static/` directory.

- `canvas-components.js` contains all web components with their registration guards
- `tokens.css` contains the shared palette, semantic aliases, spacing, shape, and transition tokens
- `typography.css` contains heading and paragraph styles matching Canvas Semantic UI, including a Google Fonts `@import` for Lato

Plugin iframes are isolated from the parent Canvas app and do not inherit its fonts. The `@import` in `typography.css` is the only font loading mechanism needed. Do not add separate Google Fonts `<link>` tags in the HTML.

#### Serving

Each file needs a SimpleAPI GET route that reads it via `render_to_string` and returns it with the correct content type. The plugin sandbox does not allow `os`, `pathlib`, or `open()` for file access. Use `render_to_string("static/filename")` for all file reads.

The SimpleAPI class serving these routes must inherit from `StaffSessionAuthMixin`. Plugin pages load inside an authenticated Canvas iframe that passes a staff session cookie. Without the mixin, asset routes return a credentials error instead of the file contents, and the page renders with no styling or components.

```python
@api.get("/tokens.css")
def tokens_css(self) -> list[Response]:
    return [
        Response(
            render_to_string("static/tokens.css").encode(),
            status_code=HTTPStatus.OK,
            content_type="text/css",
        )
    ]

@api.get("/typography.css")
def typography_css(self) -> list[Response]:
    return [
        Response(
            render_to_string("static/typography.css").encode(),
            status_code=HTTPStatus.OK,
            content_type="text/css",
        )
    ]

@api.get("/canvas-components.js")
def components_js(self) -> list[Response]:
    return [
        Response(
            render_to_string("static/canvas-components.js").encode(),
            status_code=HTTPStatus.OK,
            content_type="application/javascript",
        )
    ]
```

#### Loading in the HTML shell

The plugin's index template includes all three files in the `<head>`. Replace `{plugin_name}` with the `name` field from `CANVAS_MANIFEST.json` (uses underscores) and `{prefix}` with the SimpleAPI PREFIX value (without the leading slash).

```html
<link rel="stylesheet" href="/plugin-io/api/{plugin_name}/{prefix}/tokens.css">
<link rel="stylesheet" href="/plugin-io/api/{plugin_name}/{prefix}/typography.css">
<script src="/plugin-io/api/{plugin_name}/{prefix}/canvas-components.js"></script>
```

No other font or stylesheet links are needed. Every `<canvas-*>` element works anywhere in the page body without additional script tags.

### Plugin HTML Boilerplate

Start every plugin HTML page from this shell. Replace `{plugin_name}` with the name from CANVAS_MANIFEST.json and `{prefix}` with the SimpleAPI PREFIX value.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="/plugin-io/api/{plugin_name}/{prefix}/tokens.css">
  <link rel="stylesheet" href="/plugin-io/api/{plugin_name}/{prefix}/typography.css">
  <script src="/plugin-io/api/{plugin_name}/{prefix}/canvas-components.js"></script>
  <style>
    /* Plugin-specific CSS only. Use var(--token) for all values. */
  </style>
</head>
<body>
  <!-- Plugin content using <canvas-*> elements -->
</body>
</html>
```

For right chart pane plugins, add `padding-bottom: 120px` to the body or outermost scrollable container to clear the Pylon Chat widget.

## Token System

The component system uses CSS custom properties organized in three layers. Each layer can override the one below it. The browser resolves the first defined value and stops.

```
component token  →  global token  →  hardcoded default
 most specific       shared            fallback
```

### Layer 1. Hardcoded defaults

Every value the component needs is hardcoded as the innermost fallback. If the page defines nothing, the component renders with the correct Canvas design system appearance. This is what makes components self sufficient.

### Layer 2. Global tokens

Shared properties that apply across all components. These are defined in `assets/tokens.css` but can also be set by the plugin author in a `:root` block or on any ancestor element.

**Raw palette.** Named by color. Changing one shifts every component that uses that color.

| Token | Default | Affects |
|---|---|---|
| `--palette-green` | `#22BA45` | Primary buttons, green badges, green chips |
| `--palette-blue` | `#2185D0` | Secondary buttons, blue badges, focus rings |
| `--palette-red` | `#BD0B00` | Danger buttons, red badges, error states |
| `--palette-orange` | `#ED4A0B` | Warning banners, orange badges |
| `--palette-yellow` | `#fbbd08` | Yellow badges |
| `--palette-olive` | `#b5cc18` | Olive badges |
| `--palette-teal` | `#00b5ad` | Teal badges |
| `--palette-violet` | `#6435c9` | Violet badges |
| `--palette-purple` | `#a333c8` | Purple badges |
| `--palette-pink` | `#e03997` | Pink badges |
| `--palette-brown` | `#935330` | Brown badges |
| `--palette-grey` | `#767676` | Grey badges, muted text |
| `--palette-black` | `#1b1c1d` | Black badges |
| `--palette-white` | `#FFFFFF` | Surfaces, backgrounds |

**Semantic aliases.** Named by role. Resolve through the palette. Changing one shifts every component that uses that role without affecting other uses of the same color.

| Token | Resolves to | Role |
|---|---|---|
| `--color-primary` | `--palette-green` | Clinical state transitions (sign, lock, send) |
| `--color-secondary` | `--palette-blue` | Standard actions (save, edit, add) |
| `--color-danger` | `--palette-red` | Destructive actions (delete, remove) |
| `--color-warning` | `--palette-orange` | Warnings |
| `--color-text` | `--palette-text` | Primary body text |
| `--color-text-active` | `--palette-text-active` | Hovered or active text |
| `--color-text-muted` | `--palette-text-muted` | Secondary text on white backgrounds |
| `--color-bg` | `--palette-bg` | Page backgrounds |
| `--color-border` | `--palette-border` | Borders, dividers |
| `--color-surface` | `--palette-white` | Card and input backgrounds |

**Shared properties.** Typography, spacing, shape, and transitions used by multiple components.

| Token | Default | Used by |
|---|---|---|
| `--font-family` | `lato, -apple-system, ...` | All components with text |
| `--font-weight-bold` | `700` | Buttons, labels, headings |
| `--radius` | `.28571429rem` | Buttons, inputs, cards, badges, dropdowns |
| `--space-mini` | `4px` | Tight inline gaps |
| `--space-tiny` | `8px` | Button icon gaps, compact spacing |
| `--space-small` | `12px` | Form field spacing |
| `--space-medium` | `16px` | Section padding |
| `--space-large` | `20px` | Major section gaps |
| `--space-huge` | `24px` | Page padding |
| `--transition-fast` | `200ms` | Hover and color transitions |
| `--transition-base` | `250ms` | Layout and visibility transitions |
| `--focus-ring` | `2px solid #2185D0` | Focus outline on interactive elements |
| `--focus-ring-offset` | `2px` | Focus outline offset |

### Layer 3. Component tokens

Prefixed with `--canvas-{component}-`. Override a single component type or a single instance without affecting anything else. These are checked first in the fallback chain so they always win.

Set on a container to affect all instances of that component inside it, or inline on a single element to affect only that one.

```html
<!-- one button -->
<canvas-button style="--canvas-button-radius: 999px">Pill</canvas-button>

<!-- all buttons in this section -->
<div style="--canvas-button-radius: 999px">
  <canvas-button>Pill A</canvas-button>
  <canvas-button>Pill B</canvas-button>
</div>
```

## How Fallbacks Resolve

An example with `border-radius` on a button.

```css
border-radius: var(--canvas-button-radius, var(--radius, .28571429rem));
```

The browser checks in order.

1. Is `--canvas-button-radius` defined? If yes, use it. Done.
2. Is `--radius` defined? If yes, use it. Done.
3. Use `.28571429rem`.

This means.

- Setting `--radius: 0` in `:root` makes all components square (buttons, inputs, cards, badges).
- Setting `--canvas-button-radius: 0` on one element makes only that button square.
- Setting nothing gives every component the Canvas default radius.

The same logic applies to every property in every component.

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

## Button Spacing

Adjacent buttons in Canvas have a `.25em` (4px at 16px base) gap between them. This is a layout concern, not a component concern. The component does not add outer spacing. Use whatever CSS achieves the correct visual result.

```html
<!-- flex with gap -->
<div style="display: flex; gap: .25em">
  <canvas-button variant="ghost">Cancel</canvas-button>
  <canvas-button>Save</canvas-button>
</div>

<!-- margin -->
<canvas-button variant="ghost">Cancel</canvas-button>
<canvas-button style="margin-left: .25em">Save</canvas-button>
```

For button groups where one side is flush left and the other flush right (cancel on left, save on right), use `justify-content: space-between` on the container. The `.25em` gap only applies when buttons sit next to each other.

```html
<div style="display: flex; justify-content: space-between">
  <canvas-button variant="ghost">Cancel</canvas-button>
  <canvas-button>Save</canvas-button>
</div>
```

---

## Components

## Escalation Ladder

When building plugin UI, the agent should exhaust each level before moving to the next. Each level adds friction.

**Level 1. Use existing components.** Compose `<canvas-*>` elements together. No friction, no approval needed. This handles the vast majority of plugin UI.

**Level 2. Customize through attributes and slots.** Set variant, size, color, and other attributes. Place content in slots. Still no friction.

**Level 3. Override through CSS custom properties.** Set `--canvas-{component}-{property}` tokens to adjust a single component or `--{global-token}` to adjust all components. Light friction. The agent should confirm the override is necessary and not achievable through attributes.

**Level 4. Build novel HTML/CSS using tokens.css.** For layouts and patterns that no component covers. Use `var(--space-*)`, `var(--color-*)`, `var(--radius)`, and other tokens from tokens.css. Significant friction. The agent should exhaust component options first and push back before going custom. All custom CSS values must come from tokens.

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
- **sm** for card headers, toolbars, and table row actions.
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

**File.** `assets/components/canvas-button.js`

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

**File.** `assets/components/canvas-badge.js`

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

**File.** `assets/components/canvas-chip.js`

### canvas-input

A text input or textarea with integrated label, error state, and native form participation via `ElementInternals`. Renders either an `<input>` or `<textarea>` inside Shadow DOM depending on the `multiline` attribute.

**Usage**

```html
<canvas-input label="Patient Name" placeholder="e.g. Jane Smith"></canvas-input>
<canvas-input label="Email" type="email" placeholder="patient@example.com"></canvas-input>
<canvas-input label="Date of Birth" type="date"></canvas-input>
<canvas-input label="Notes" multiline rows="4" placeholder="Enter clinical notes"></canvas-input>
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
| `multiline` | boolean | false (renders textarea when set) |
| `rows` | number | 4 |
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
  <canvas-input label="Reason" name="reason" multiline rows="3"></canvas-input>
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
  <canvas-input label="Notes" multiline rows="3"></canvas-input>
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
| `--canvas-input-textarea-min-height` | Textarea minimum height | `80px` |
| `--canvas-input-error-text` | Error text and label color | `#9f3a38` |
| `--canvas-input-error-bg` | Error input background | `#fff6f6` |
| `--canvas-input-error-border` | Error border and placeholder color | `#e0b4b4` |

**File.** `assets/components/canvas-input.js`

### canvas-radio

A locked radio button matching the Canvas Semantic UI radio. No visual customization. Grouped by shared `name` attribute. Selecting one radio deselects siblings with the same name.

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

**File.** `assets/components/canvas-radio.js`

### canvas-checkbox

A locked checkbox matching the Canvas Semantic UI checkbox. White box with a dark checkmark, no colored fill. Toggles between checked and unchecked on click.

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

**File.** `assets/components/canvas-checkbox.js`

### canvas-toggle

A locked toggle switch matching the Canvas Semantic UI toggle. Blue active track (#0D71BC, not green), white thumb with gradient and shadow, slide animation. Toggles mean instant effect and must never appear on a screen with a Save or Submit button. If a form has submit, use checkboxes instead.

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

**File.** `assets/components/canvas-toggle.js`

### canvas-banner

An inline message banner matching the Canvas Semantic UI message. Four semantic variants for communicating status. Never floating. Canvas does not use toasts, snackbars, or auto-dismissing notifications anywhere. The border is rendered via `box-shadow: inset`, not a CSS border.

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

**Locked component.** No visual customization tokens. The four variant colors are fixed to match Canvas Semantic UI. The neutral default (no variant) uses gray.

**File.** `assets/components/canvas-banner.js`

### canvas-card

A segment card matching the Canvas Semantic UI segments pattern. White surface with border, border-radius, and box-shadow. Supports multiple body sections separated by borders, and an optional gray footer for actions and metadata. Used for notes, stacked content blocks, and detail panels.

Three custom elements are registered from a single file: `canvas-card` (outer container), `canvas-card-body` (body sections), and `canvas-card-footer` (gray footer area).

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

**Typography dependency.** Headings (h4, h3, etc.) inside card body sections need `typography.css` loaded on the page for correct margin behavior. Without it, browser default heading margins add unwanted space at the top of card bodies. The `:first-child { margin-top: 0 }` rule in typography.css handles this.

**File.** `assets/components/canvas-card.js`

### canvas-dropdown

A non-searchable select dropdown matching the Canvas Semantic UI selection dropdown. Click to open a menu, arrow keys to navigate, Enter to select. For searchable dropdowns, use `canvas-combobox` instead.

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

- **default** (no size attribute) for forms, modals, and any standalone data entry. This is the standard dropdown seen in patient forms, coverage modals, appointment creation, and anywhere the dropdown is the primary interaction on screen. Trigger text renders at 16px.
- **sm** for compact contexts where the dropdown is secondary to the main content. Sidebars, toolbars, filter bars, card headers, and settings panels where space is tight and the dropdown sits alongside other compact controls. Trigger text renders at 12px. The menu items always stay at 16px regardless of trigger size.

When a dropdown appears next to buttons, match the button size. If the buttons are `size="sm"`, the dropdown should also be `size="sm"`. When a dropdown appears inside a card footer or toolbar alongside small buttons, use `sm`. When it is the main form element on a page or modal, use default.

```html
<!-- default for forms and modals -->
<canvas-dropdown label="Coverage Type" name="coverage" placeholder="Select type">
  <canvas-option value="commercial">Commercial</canvas-option>
  <canvas-option value="medicare">Medicare</canvas-option>
</canvas-dropdown>

<!-- sm for sidebars, toolbars, filter bars -->
<canvas-dropdown label="Location" size="sm" placeholder="Select location">
  <canvas-option value="sf">Canvas Clinic SF</canvas-option>
  <canvas-option value="oak">Canvas Clinic Oakland</canvas-option>
</canvas-dropdown>
```

**Keyboard navigation.** Arrow up/down to navigate options, Enter or Space to select, Escape to close, Home/End to jump, Tab to select and move focus. Disabled options are skipped.

**Locked component.** No visual customization tokens. Border, focus border (#96c8da), shadow, item hover, and item selected styling are fixed to match Canvas Semantic UI.

**File.** `assets/components/canvas-dropdown.js`

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

**Keyboard navigation.** Arrow up/down to navigate, Enter to select, Escape to restore previous value and close, Home/End to jump, Tab to select and move focus. Disabled options are skipped.

**Locked component.** No visual customization tokens. Border, focus border (#96c8da), shadow, item hover, and item selected styling are fixed to match Canvas Semantic UI.

**File.** `assets/components/canvas-combobox.js`

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

**File.** `assets/components/canvas-multi-select.js`

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

**Keyboard navigation.** ArrowLeft/ArrowRight cycle through tabs. Home/End jump to first/last. Focus follows selection.

**Initial selection.** The first tab with the `active` attribute becomes selected on mount. If no tab has `active`, the first tab is selected.

**Component tokens**

| Token | What it controls | Default |
|---|---|---|
| `--tab-bar-height` | Height of the tab bar | `45.41px` |
| `--tab-label-max-width` | Maximum label width before truncation | `160px` |
| `--tab-label-min-width` | Minimum label width | `60px` |

**File.** `assets/components/canvas-tabs.js`

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

**Actions in title.** Place interactive elements (toggles, checkboxes, badges) directly inside `canvas-accordion-title`. The component handles click propagation so that clicking a toggle or checkbox does not trigger expand/collapse. When mixing text and interactive elements, use flex utilities on the title content.

```html
<canvas-accordion-title>
  <span style="flex: 1">Notifications</span>
  <canvas-toggle label="" checked></canvas-toggle>
</canvas-accordion-title>
```

**Multiple open.** Multiple items can be open simultaneously. There is no exclusive mode.

**Keyboard.** Enter or Space on a focused title toggles that item. Focus is managed via `tabindex="0"` on the title element.

**Accessibility.** Title has `role="button"` and `aria-expanded`. Content has `role="region"`.

**Locked component.** No visual customization tokens beyond `--font-family`.

**File.** `assets/components/canvas-accordion.js`

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

**File.** `assets/components/canvas-modal.js`

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

**File.** `assets/components/canvas-table.js`

### canvas-sortable-list

A drag-to-reorder list with FLIP animation and keyboard support. Registers two elements from one file. `canvas-sortable-list` is the container and `canvas-sortable-item` wraps each draggable item.

Each item renders a drag handle (grip icon) automatically. Drag the handle to reorder. The list uses pointer events for drag and FLIP animation for smooth transitions.

**Usage**

```html
<canvas-sortable-list>
  <canvas-sortable-item>
    <span>First item</span>
  </canvas-sortable-item>
  <canvas-sortable-item>
    <span>Second item</span>
  </canvas-sortable-item>
  <canvas-sortable-item>
    <span>Third item</span>
  </canvas-sortable-item>
</canvas-sortable-list>
```

**Events**

| Event | When | Detail |
|---|---|---|
| `reorder` | When an item is moved to a new position (drag or keyboard). Bubbles and composes. | `{ oldIndex: number, newIndex: number, item: HTMLElement }` |

**Slot.** `canvas-sortable-item` has a default slot for content. The drag handle is rendered inside Shadow DOM and cannot be replaced.

**Drag behavior.** Pointer down on the handle starts a drag. The dragged item becomes a fixed overlay following the cursor. A placeholder holds space at the original position. As the cursor moves past item midpoints, the placeholder shifts and other items animate into place via FLIP transforms (200ms ease). On pointer up, the item is inserted at the placeholder position. A `reorder` event fires only if the position actually changed.

**Keyboard reorder.** Focus the drag handle with Tab, then press ArrowUp or ArrowDown to move the item. Each keypress moves the item one position and fires a `reorder` event.

**FLIP animation.** Items animate from old to new position using `transform: translateY()` with a 200ms ease transition. The animation is smooth and prevents visual jumping during reorder.

**Component tokens**

| Token | What it controls | Default |
|---|---|---|
| `--radius` | Border radius on drag overlay and handle hover | `.28571429rem` |

**File.** `assets/components/canvas-sortable-list.js`

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

**File.** `assets/components/canvas-sidebar-layout.js`

## Patterns Without Components

These patterns do not have web components yet. Use them as raw HTML/CSS when needed. All CSS values must come from tokens.css.

### Tooltip

Uses the `data-tooltip` attribute on any element. The tooltip appears above the element on hover with a scale-in animation. No JavaScript needed.

```html
<canvas-button data-tooltip="Edit this record" size="sm" variant="ghost">Edit</canvas-button>
```

Truncated text in a table cell.

```html
<canvas-table-cell style="max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap"
  data-tooltip="Metformin Hydrochloride Extended-Release 500mg">
  Metformin Hydrochloride Extended-Release 500mg
</canvas-table-cell>
```

Tooltip styles must be included in plugin-specific CSS. See the tooltip CSS spec in tokens.css comments or the showcase page for the full implementation.

### Divider

A horizontal rule for separating content sections.

```html
<div style="border-top: 1px solid var(--color-border); margin: var(--space-medium) 0"></div>
```

### Empty State

```html
<div style="padding: var(--space-huge); text-align: center; color: var(--color-text-muted, #767676)">
  <p>No medications found</p>
  <canvas-button size="sm" style="margin-top: var(--space-small)">Add Medication</canvas-button>
</div>
```

### Loading Spinner

```html
<div role="status" aria-label="Loading" style="
  width: 32px; height: 32px; margin: var(--space-huge) auto;
  border: 3px solid var(--color-border, #E9E9E9);
  border-top-color: var(--color-secondary, #2185D0);
  border-radius: 50%; animation: spin 0.8s linear infinite;
"></div>
<style>
@keyframes spin { to { transform: rotate(360deg); } }
</style>
```

### Patient Context Header

Use in modals or standalone pages where the patient chart is not visible.

```html
<div style="display: flex; align-items: center; gap: var(--space-small);
  padding-bottom: var(--space-small); border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-medium)">
  <span style="font-weight: 700">Jane Smith</span>
  <span style="color: var(--color-text-muted, #767676); font-size: .92857143em">DOB: Mar 15, 1985</span>
  <span style="color: var(--color-text-muted, #767676); font-size: .92857143em">MRN: 12345</span>
</div>
```
