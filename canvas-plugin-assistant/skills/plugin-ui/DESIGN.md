# Visual Specification

Visual rules for the Canvas plugin design system. This file is the single source of truth for colors, typography, spacing, shape, token architecture, and visual treatment rules. Component APIs are in web-components.md. Behavioral rules are in interaction-patterns.md. This file loads at workflow Step 4 (building HTML) and Step 5 (clinical UX visual checks).

## Visual Theme

The Canvas home-app inherits from Semantic UI. The aesthetic is clinical and dense, not decorative. Screens prioritize information density and scannability over whitespace and visual flair. Plugins must match this tone. A plugin that looks like a marketing landing page will feel wrong next to the home-app.

## Color Palette and Roles

This palette is closed. Never use purple, teal, pink, or cyan. AI models reach for these to add visual variety. The Canvas palette does not include them.

Green is rare. Only for clinical state transitions that affect the patient record or leave the system (sign/lock note, send message to patient, submit referral, confirm fax, check in patient). Blue is the default for all standard actions. Most screens have blue buttons only.

| Token | Hex | Role |
|---|---|---|
| Green | `#22BA45` | Primary actions (clinical state transitions), success |
| Blue | `#2185D0` | Secondary actions, links, focus rings, info badges |
| White | `#FFFFFF` | Backgrounds, card surfaces, input backgrounds |
| Light Gray | `#F5F5F5` | Page backgrounds, disabled inputs |
| Mid Gray | `#E9E9E9` | Borders, dividers, inactive toggles |
| Red | `#BD0B00` | Destructive actions only, errors |
| Orange | `#ED4A0B` | Warnings, stale indicators |
| Brown | `#935330` | Reserved, almost never used |
| Dark Text | `rgba(0,0,0,0.87)` | Primary text |
| Muted Text | `#767676` | Secondary text (only on white backgrounds) |

## Typography

Lato is the typeface. Plugin iframes do not inherit the parent page's fonts, so the Google Fonts `<link>` tag in head.html is required.

| Property | Value |
|---|---|
| Font family | `lato, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` |
| Base font size | `16px` |
| Label font size | `.92857143em` |
| Bold weight | `700` |
| Base line height | `1.4285em` |

### Heading Scale

All headings use weight 700 and line height 1.28571429em. Margin is calc(2rem - .14285714em) top and 1rem bottom. First-child headings have zero top margin. Last-child headings have zero bottom margin.

| Level | Size |
|---|---|
| h1 | `2rem` |
| h2 | `1.71428571rem` |
| h3 | `1.28571429rem` |
| h4 | `1.07142857rem` |
| h5 | `1rem` |

### Paragraphs

Margin is 0 0 1em. First-child paragraphs have zero top margin. Last-child paragraphs have zero bottom margin. Line height is 1.4285em.

## Spacing Scale

All spacing follows a 4px grid. Use the token names in plugin CSS, not raw pixel values.

| Token | Value | Usage |
|---|---|---|
| `--space-mini` | `4px` | Tight inline gaps, button icon spacing |
| `--space-tiny` | `8px` | Data display row spacing, compact layouts |
| `--space-small` | `12px` | Form field gaps, nested accordion indent step |
| `--space-medium` | `16px` | Section padding, form section gaps |
| `--space-large` | `20px` | Major section separations |
| `--space-huge` | `24px` | Page padding, empty state containers |

## Container Padding Responsibility

Horizontal inset is a container concern, not a component concern. A plugin component must not carry intrinsic left or right padding that offsets its own box from its parent's inner edge. Every built in element and every canvas component follows this rule.

- Headings and paragraphs. `h1` through `h5` and `<p>` ship with `padding: 0` in `canvas-plugin-ui.css`. Horizontal space around text comes from the parent that holds the text.
- Buttons, inputs, and interactive controls. Intrinsic padding lives inside the control (between the border and the text), never outside it. Outer spacing from the container edge is the container's job.
- Accordions, cards, tables, sortable lists, and every other structural component. Same rule. The component sits flush with its parent's content box.

Containers supply the inset. A `canvas-card` has internal padding. A `canvas-sidebar-layout` content pane has internal padding. A plugin page shell applies its own padding at the top of the document tree. When a component looks like it is touching the viewport edge, the fix is to add padding to the container, never to the component.

Nesting indent is a separate concern from container padding. When a component needs to show hierarchy at different depths, for example nested accordions, apply a left step via a scoped rule that only matches nested instances. The top level instance still carries no intrinsic padding. See the `canvas-accordion-content canvas-accordion-item` rule in `canvas-plugin-ui.css` for the canonical pattern, it uses `--canvas-accordion-nested-indent` with a `--space-small` fallback.

## Shape

| Property | Value | Notes |
|---|---|---|
| Border-radius | `.28571429rem` | All rounded elements. From Semantic UI. Never change. |
| Border width | `1px` | Default for inputs, cards, dividers |
| Border color | `rgba(34, 36, 38, 0.15)` | The `--color-border` token |
| Focus ring | `2px solid #2185D0` | The `--focus-ring` token |
| Focus ring offset | `2px` | The `--focus-ring-offset` token |
| Input focus border | `#96c8da` | Component-specific, not a global token |
| Shadow | `0 1px 2px 0 rgba(34, 36, 38, 0.15)` | The `--shadow` token |
| Transition fast | `200ms` | Hover and color transitions |
| Transition base | `250ms` | Layout and visibility transitions |

## Token System

The component system uses CSS custom properties organized in three layers. Each layer can override the one below it. The browser resolves the first defined value and stops.

```
component token  →  global token  →  hardcoded default
 most specific       shared            fallback
```

### Layer 1. Hardcoded defaults

Every value the component needs is hardcoded as the innermost fallback. If the page defines nothing, the component renders with the correct Canvas design system appearance. This is what makes components self sufficient.

### Layer 2. Global tokens

Shared properties that apply across all components. These are defined in `assets/canvas-plugin-ui.css` but can also be set by the plugin author in a `:root` block or on any ancestor element.

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

## Text and Background Pairing

These rules are mandatory with no exceptions.

- **On white (`#FFFFFF`) backgrounds.** Both dark text and muted gray text are allowed. This is the only background where gray text may appear.
- **On light gray and mid gray backgrounds.** Only dark text. Never place gray text on a gray background.
- **On colored backgrounds** (green, blue, red, orange, brown). Text must be white and bold.

## Visual Hierarchy and Scanning

Clinicians scan, they do not read. The most critical piece of information on any screen must be identifiable within one second.

- In a medication list, the drug name and dose are primary. The prescriber and date are secondary.
- In a lab result, the value and its abnormal/normal status are primary. The collection time and ordering provider are secondary.
- In a patient list, the patient name and chief concern are primary. The appointment time and status are secondary.
- Use font-weight `700` and dark text (`rgba(0,0,0,0.87)`) for primary information. Use regular weight and muted text (`#767676`) for secondary information. This creates a two-level hierarchy without needing different font sizes.

## Information Density

- Distinguish between form views and data display views. Forms use the standard spacing scale (12px between fields, 16px section gaps). Data display views (medication lists, lab results, visit histories) can use tighter spacing (8px between rows, 12px section gaps) to show more information without scrolling.
- Clinicians want to see as much relevant information at a glance as possible. Do not add whitespace for aesthetics in data-dense screens. Every pixel of vertical space costs scrolling.
- In data display views, use the 14px font size for all content. Reserve 16px for headings only.

## Long Text and Truncation

Medical terminology produces long strings. Drug names, diagnosis descriptions, allergy lists, and procedure names regularly exceed available width.

- In tables and lists, truncate with ellipsis after one line. Show the full text in a tooltip on hover.
- In cards and detail views, wrap the full text. Do not truncate content the user came to read.
- In badges and pills, truncate with ellipsis and set a max-width. Keep the badge readable but compact.
- Never truncate patient names, medication doses, or allergy information in contexts where the truncated version could cause a clinical misidentification.

## Date and Time Display

- Use absolute dates for clinical documentation. "Mar 24, 2026" not "2 days ago." Relative dates create ambiguity in medical records.
- Include time when it matters clinically (medication administration, vital signs, lab draws). Format as "Mar 24, 2026 2:30 PM."
- For timestamps in non-clinical contexts like audit logs, last-edited indicators, and sync status, relative time is acceptable ("5 minutes ago", "yesterday").
- Never display dates in MM/DD/YYYY numeric format. Use the three-letter month abbreviation to avoid ambiguity.

## Badge Color Semantics

Match colors to semantic meaning consistently across the plugin.

| Color | Meaning |
|---|---|
| Green | Accepted, active, completed successfully |
| Red | Denied, error, critical |
| Blue | Submitted, pending, in progress |
| Grey | Done, draft, inactive |
| Yellow | Pending review, needs attention |
| Orange | Warning, preferred tags, stale |
| Teal | Scheduled |

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

## Patterns Without Components

These patterns do not have web components yet. Use them as raw HTML/CSS when needed. All CSS values must come from design tokens.

### Empty State

Empty state is typed by cause. Four markup variants cover the full taxonomy. See Empty States in `references/component-usage.md` for the rules that pick which one to use.

Placement. Center vertically and horizontally inside short containers (card bodies, sidebar panels under 400 pixels tall). Top align with `--space-huge` padding inside tall containers (full page regions, modal bodies) so the block sits where the eye lands rather than floating in the middle.

First use. User has never added data here.

```html
<div style="padding: var(--space-huge); text-align: center">
  <h3 style="margin: 0 0 var(--space-small); font-weight: 700">No medications recorded</h3>
  <p style="margin: 0 0 var(--space-medium); color: var(--color-text-muted, #767676)">Track this patient's active medications here.</p>
  <canvas-button>Add first medication</canvas-button>
</div>
```

User cleared. Data existed, the user removed it all.

```html
<div style="padding: var(--space-huge); text-align: center">
  <h3 style="margin: 0 0 var(--space-small); font-weight: 700">Medication list cleared</h3>
  <p style="margin: 0 0 var(--space-medium); color: var(--color-text-muted, #767676)">All medications were removed. Add a new entry or restore the previous list.</p>
  <canvas-button style="margin-right: var(--space-small)">Add medication</canvas-button>
  <canvas-button variant="ghost">Restore previous</canvas-button>
</div>
```

Filter no results. Underlying data exists, the current filter excludes everything. Render inside the same container that holds the filtered list or table.

```html
<div style="padding: var(--space-huge); text-align: center">
  <h3 style="margin: 0 0 var(--space-small); font-weight: 700">No results match your filters</h3>
  <p style="margin: 0 0 var(--space-medium); color: var(--color-text-muted, #767676)">Try widening the date range or removing a tag.</p>
  <canvas-button variant="ghost">Clear filters</canvas-button>
</div>
```

Load error. Fetch failed. Do not reuse the centered empty pattern. Use `canvas-banner` so the user can tell a failed load from a true empty.

```html
<canvas-banner variant="error">
  <span slot="title">Could not load medications</span>
  <span slot="description">Check your connection and try again.</span>
  <canvas-button slot="action" variant="ghost">Retry</canvas-button>
</canvas-banner>
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

### Sortable List Minimum Height

Empty receiving lists need a minimum drop target.

- Token. `--canvas-sortable-min-height`. Default `calc(var(--space-medium) * 2)`.
- Applied via `:host`. Ensures an empty column still catches a drop.

## Do's and Don'ts

**Do.**
- Use `var(--token)` references for all CSS values in plugin-specific styles. The only allowed raw values are `0`, `none`, `auto`, `100%`, position values, and z-index integers.
- Follow the spacing grid (4, 8, 12, 16, 20, 24 px).
- Use absolute dates in clinical contexts ("Mar 24, 2026").
- Exhaust component options before writing novel HTML (see Escalation Ladder in SKILL.md).
- Use font-weight 700 and dark text for primary information, regular weight and muted text for secondary.

**Don't.**
- Use purple, teal, cyan, pink, or any color outside the palette. These are common AI-generation defaults.
- Use `box-shadow` to simulate borders. Use actual `border` properties.
- Set `outline: none` on focusable elements without providing an alternative focus indicator.
- Use custom scrollbar styling in plugin CSS. Let the browser handle scrollbars natively.
- Use CSS media queries based on viewport width for plugin content. Plugin iframes do not respond to viewport breakpoints. Design for the known surface width.
- Add whitespace for aesthetics in data-dense clinical screens. Every pixel of vertical space costs scrolling.
- Use relative dates ("2 days ago") in clinical documentation contexts.
