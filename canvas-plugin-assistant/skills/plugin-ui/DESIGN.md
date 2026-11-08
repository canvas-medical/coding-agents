# Visual Specification

Visual rules for the Canvas plugin design system. This file is the single source of truth for colors, typography, spacing, shape, token architecture, and visual treatment rules. Component APIs, per-component keyboard, ARIA, and visual internals are in [references/web-components.md](references/web-components.md). Cross-cutting interaction rules (focus, toggle-submit, touch targets) are in [references/interaction-patterns.md](references/interaction-patterns.md). Copy-paste templates that span components are in [references/patterns.md](references/patterns.md). This file loads at workflow Step 4 (building HTML) and Step 5 (clinical UX visual checks).

## Visual Theme

The Canvas home-app aesthetic is clinical and dense, not decorative. Screens prioritize information density and scannability over whitespace and visual flair. Plugins must match this tone. A plugin that looks like a marketing landing page will feel wrong next to the home-app.

## Where the Values Come From

Every value and rule below is a default. When the person building the plugin asks for something different, follow the request. See Defaults, Not Mandates in [SKILL.md](SKILL.md).


The home-app renders stock Semantic UI 2.4.0 (`home-app/app/static/css/semantic.min.css` in canvas-medical/canvas) with a few Canvas overrides in `home-app/static/scripts/themes/theme.ts` and `home-app/static/styles/`. Every token in `assets/canvas-plugin-ui.css` is marked with its source.

- **Anchored values** match the home-app exactly: Lato, text sizes, the palette hues, corner radius, border color, control padding, and the active tab treatment. These are what make a plugin read as part of Canvas. Keep them unless the person asks for something else.
- **Open values** are deliberate improvements over the home-app: the 4px spacing grid, a visible keyboard focus ring, darker button fills so white text passes contrast, consistent control heights, and short transitions. These may be tuned as long as the page still flows with the Canvas UI around it.

## Color Palette and Roles

This palette is the default. Do not reach for teal, olive, violet, pink, yellow, or cyan on your own. AI models add these for visual variety, and the Canvas palette does not include them. A color the person asks for, such as a customer's brand color, is fine.

Green is rare. In the home-app, green buttons commit something: lock a note, send a fax, collect or post a payment. Plugins follow the same rule. Use green only for clinical state transitions that affect the patient record or leave the system (sign or lock a note, send a message to a patient, submit a referral, confirm a fax, check in a patient) and for taking a payment. Blue is the default for all standard actions. Most screens have blue buttons only.

| Color | Hex | Role |
|---|---|---|
| Blue | `#2185d0` | Links, selected states, info badges, the Canvas brand blue |
| Blue button fill | `#1a69a4` | `canvas-button` default. Canvas blue darkened so white text passes 4.5:1 |
| Green | `#21ba45` | Success badges, progress |
| Green button fill | `#16802e` | `canvas-button variant="success"`. Canvas green darkened so white text passes 4.5:1 |
| Red | `#db2828` | Destructive actions, error badges |
| Orange | `#f2711c` | Warnings, due-soon and stale indicators |
| Purple | `#a333c8` | Rare category badges only |
| Neutral | `#e0e1e2` | Ghost buttons (cancel, dismiss) |
| White | `#ffffff` | Plugin page background (default), card surfaces, input backgrounds |
| Light Gray | `#f5f5f5` | Sidebars, opt-in page canvas for peer `canvas-card` collections |
| Border | `rgba(34,36,38,.15)` | Borders, dividers |
| Dark Text | `rgba(0,0,0,.87)` | Primary text |
| Muted Text | `#767676` | Secondary text (only on white backgrounds) |
| Error text and fill | `#9f3a38` on `#fff6f6`, border `#e0b4b4` | Field errors, error banners |

## Typography

Lato is the typeface. Plugin iframes do not inherit the parent page's fonts, so the Google Fonts `<link>` tag in head.html is required. `canvas-plugin-ui.css` sets Lato on the page body, so plain text outside components never falls back to a serif font.

| Property | Value |
|---|---|
| Font family | `Lato, "Helvetica Neue", Arial, Helvetica, sans-serif` |
| Root font size | `16px` (home-app `app.scss`), so `rem` values match the home-app |
| Body text | `14px` (Semantic `body`) |
| Form controls | `1rem` (16px), matching Semantic `.ui.form` |
| Form labels | `.92857143em` of the control size, weight `700` |
| Buttons | `1rem` (16px), weight `700` |
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
| Border-radius | `.28571429rem` | All rounded elements. Canvas baseline default. |
| Border width | `1px` | Default for inputs, cards, dividers |
| Border color | `rgba(34, 36, 38, 0.15)` | The `--color-border` token |
| Focus ring | `2px solid #85b7d9` | The `--focus-ring` token. Open value: Semantic only recolors the border |
| Focus ring offset | `1px` | The `--focus-ring-offset` token |
| Input focus border | `#85b7d9` | Semantic `.ui.input>input:focus` |
| Shadow | `0 1px 2px 0 rgba(34, 36, 38, 0.15)` | The `--shadow` token, Semantic `.ui.segment` |
| Transition fast | `100ms` | Hover and color transitions, Semantic `.1s ease` |
| Transition base | `200ms` | Layout and visibility transitions |

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
| `--palette-blue` | `#2185d0` | Selected states, blue badges, links, calendar today |
| `--palette-green` | `#21ba45` | Green badges, green chips, progress |
| `--palette-red` | `#db2828` | Danger buttons, red badges |
| `--palette-orange` | `#f2711c` | Warning banners, orange badges |
| `--palette-purple` | `#a333c8` | Purple badges |
| `--palette-grey` | `#767676` | Grey badges, muted text |
| `--palette-black` | `#1b1c1d` | Black badges |
| `--palette-white` | `#ffffff` | Surfaces, backgrounds |

Button fills have their own tokens (`--canvas-button-primary-bg` `#1a69a4`, `--canvas-button-success-bg` `#16802e`, and their hover and pressed shades) so the darker contrast-safe fills do not change badges, links, or selected states.

**Semantic aliases.** Named by role. Resolve through the palette. Changing one shifts every component that uses that role without affecting other uses of the same color.

| Token | Resolves to | Role |
|---|---|---|
| `--color-primary` | `--palette-blue` | Standard actions and selected states (save, edit, add) |
| `--color-success` | `--palette-green` | Clinical state transitions (sign, lock, send) and payments |
| `--color-danger` | `--palette-red` | Destructive actions (delete, remove) |
| `--color-warning` | `--palette-orange` | Warnings |
| `--color-text` | `--palette-text` | Primary body text |
| `--color-text-active` | `--palette-text-active` | Hovered or active text |
| `--color-text-muted` | `--palette-text-muted` | Secondary text on white backgrounds |
| `--color-bg` | `--palette-bg` | Opt-in page canvas for peer card collections. Not the default plugin background. |
| `--color-border` | `--palette-border` | Borders, dividers |
| `--color-surface` | `--palette-white` | Card and input backgrounds |

**Shared properties.** Typography, spacing, shape, and transitions used by multiple components.

| Token | Default | Used by |
|---|---|---|
| `--font-family` | `Lato, "Helvetica Neue", Arial, Helvetica, sans-serif` | All components with text |
| `--font-size-base` | `14px` | Page body text |
| `--font-size-control` | `1rem` | Inputs, textareas, dropdowns, comboboxes, multi-selects, date inputs |
| `--font-weight-bold` | `700` | Buttons, labels, headings |
| `--radius` | `.28571429rem` | Buttons, inputs, cards, badges, dropdowns |
| `--space-mini` | `4px` | Tight inline gaps |
| `--space-tiny` | `8px` | Button icon gaps, compact spacing |
| `--space-small` | `12px` | Form field spacing |
| `--space-medium` | `16px` | Section padding |
| `--space-large` | `20px` | Major section gaps |
| `--space-huge` | `24px` | Page padding |
| `--transition-fast` | `100ms` | Hover and color transitions |
| `--transition-base` | `200ms` | Layout and visibility transitions |
| `--focus-ring` | `2px solid #85b7d9` | Focus outline on interactive elements |
| `--focus-ring-offset` | `1px` | Focus outline offset |

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

## Plugin Background

Plugin pages use a white background by default. This matches the Canvas home-app, which leaves the body unstyled so the browser's white surface shows through. Single cards, forms, prose pages, pages with accordions, and pages with tables all sit on white. A single `canvas-card` on a white page still reads as elevated through its own border and shadow.

The one exception is a page whose entire purpose is a peer `canvas-card` collection laid out as a masonry, grid, or gallery. In that case, set the page background to `--color-bg` (light gray) so the gaps between cards do the visual grouping. This is not an everyday layout. If the page is not explicitly a card collection, stay on white.

```css
body {
  background: var(--palette-white);
}

.card-gallery-page {
  background: var(--color-bg);
}
```

## Text and Background Pairing

Follow these by default. They keep text readable.

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
- In data display views, keep content at the 14px body size. Larger sizes are for headings, buttons, and form controls only.

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
| Red | Denied, error, critical, overdue |
| Blue | Submitted, pending, pending review, scheduled, in progress |
| Grey | Done, draft, inactive |
| Orange | Warning, needs attention, due soon, stale |
| Purple | A plugin-specific category that none of the above fit |

## Button Spacing

Adjacent buttons in Canvas have a `.25em` (about 4px) gap between them. This is a layout concern, not a component concern. The component does not add outer spacing. Use whatever CSS achieves the correct visual result.

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

## Component Visual Specs

Per-component locked styling (trigger dimensions, menu container styling, option padding, surface border and shadow, pointer artwork, border gray alignment) lives with the component API in [references/web-components.md](references/web-components.md). See the Visual spec subsections under `canvas-menu-button` and `canvas-popover`.

## Patterns Without Components

Copy-paste templates for empty states, patient context header, filter bar, and sortable list minimum height live in [references/patterns.md](references/patterns.md).

## Do's and Don'ts

**Do.**
- Use `var(--token)` references for all CSS values in plugin-specific styles. The only allowed raw values are `0`, `none`, `auto`, `100%`, position values, and z-index integers.
- Follow the spacing grid (4, 8, 12, 16, 20, 24 px).
- Use absolute dates in clinical contexts ("Mar 24, 2026").
- Exhaust component options before writing novel HTML (see Escalation Ladder in SKILL.md).
- Use font-weight 700 and dark text for primary information, regular weight and muted text for secondary.

**Don't.**
- Add teal, olive, violet, pink, yellow, cyan, or any other color outside the palette unless the person asks for it. These are common AI-generation defaults.
- Change an anchored value (font, text sizes, palette hues, radius, border color, control padding) on your own initiative. Change it when the person asks.
- Use `box-shadow` to simulate borders. Use actual `border` properties.
- Set `outline: none` on focusable elements without providing an alternative focus indicator.
- Use custom scrollbar styling in plugin CSS. Let the browser handle scrollbars natively.
- Use CSS media queries based on viewport width for plugin content. Plugin iframes do not respond to viewport breakpoints. Design for the known surface width.
- Add whitespace for aesthetics in data-dense clinical screens. Every pixel of vertical space costs scrolling.
- Use relative dates ("2 days ago") in clinical documentation contexts.
