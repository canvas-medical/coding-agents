# Visual Specification

Visual rules for the Canvas plugin design system. This file is the single source of truth for colors, typography, spacing, shape, token architecture, and visual treatment rules. Component APIs are in web-components.md. Behavioral rules are in interaction-patterns.md. This file loads at workflow Step 4 (building HTML) and Step 5 (clinical UX visual checks).

## Visual Theme

The Canvas home-app aesthetic is clinical and dense, not decorative. Screens prioritize information density and scannability over whitespace and visual flair. Plugins must match this tone. A plugin that looks like a marketing landing page will feel wrong next to the home-app.

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
| Border-radius | `.28571429rem` | All rounded elements. Canvas baseline, never change. |
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

## Menu Button Visual Spec

`canvas-menu-button` is a locked component with no customization tokens. Visual parity with the Canvas dropdown menu is maintained by fixing the following values inside the component's scoped styles.

### Default trigger

When no `slot="trigger"` child is provided, the component renders a ghost button.

- Background, `#e0e1e2`. Hover, `#cacbcd`.
- Text color, `rgba(0, 0, 0, 0.6)`. Hover, `rgba(0, 0, 0, 0.8)`.
- Padding, `.67857143em 1.5em`. Font size, `1rem`. Font weight, `700`. Line height, `1.21428571em`.
- Border, `1px solid transparent`. Radius, `var(--radius, .28571429rem)`.
- Caret, 8 px wide by 5 px tall SVG, inherits `currentColor`.
- Focus, `var(--focus-ring, 2px solid #2185D0)` outline with 2 px offset.

### Menu container

- Background, `var(--color-surface, #FFFFFF)`.
- Border, `1px solid rgba(34, 36, 38, 0.15)`. Radius, `var(--radius, .28571429rem)`.
- Shadow, `0 2px 4px 0 rgba(34, 36, 38, 0.12), 0 2px 10px 0 rgba(34, 36, 38, 0.15)`.
- Offset from trigger, 2 px margin on the open axis.
- Width, `min-width: 180px`, `max-width: 320px`. Text wraps at the cap.
- Height, `max-height: 16.02857143rem` with `overflow-y: auto`. Scroll bar rendered by the browser, no custom scrollbar styling.
- Z index, `100`.
- Padding, `0`. Options sit flush against the top and bottom menu edges.

### Option

- Padding, `.78571429rem 1.14285714rem`. Font size, `1rem`. Line height, `1.0625rem`.
- Default color, `var(--color-text, rgba(0, 0, 0, 0.87))`.
- Hover and highlighted, background `rgba(0, 0, 0, 0.05)`, color `rgba(0, 0, 0, 0.95)`.
- Disabled, color `#767676`, cursor `not-allowed`, background transparent on hover.
- No per option border.

### Section divider

- Rendered for each `<hr>` child inside the default slot.
- Border top, `1px solid rgba(34, 36, 38, 0.15)`, same as the outer menu border.
- Height, `0`. Margin, `.28571429rem 0`. Padding, `0`.
- Role, `separator`. Not focusable, skipped by keyboard navigation.

### Placement

- Default, auto. Component measures trigger rect against the viewport on open and sets `data-placement-direction="up"` or `data-placement-align="end"` on the inner root when the menu would clip.
- `direction="down"` and `direction="up"` pin the vertical axis and disable auto flip on that axis.
- `align="start"` and `align="end"` pin the horizontal axis and disable auto flip on that axis.

## Popover Visual Spec

`canvas-popover` is an anchored content container for arbitrary HTML. It complements `canvas-menu-button` by covering anchored content that is not an action menu or a value selection, for example filter forms, column pickers, legends, and micro confirmation dialogs.

### Surface

- Background, `var(--color-surface, #FFFFFF)`.
- Border, `1px solid #d4d4d5`. Radius, `var(--radius, .28571429rem)`. Matches `canvas-tooltip` and `canvas-card` so anchored surfaces share one container gray.
- Shadow, `0 2px 4px 0 rgba(34, 36, 38, 0.12), 0 2px 10px 0 rgba(34, 36, 38, 0.15)`, same as the menu button menu and the Canvas dropdown menu.
- Padding, `1em 1.14285714em`. The surface holds arbitrary content, padding belongs to the container not the options.
- Text, font size `1rem`, line height `1.4285714`, color `var(--color-text, rgba(0, 0, 0, 0.87))`.
- Positioning, `position: fixed` with inline top and left values set by the component. Rendered above ancestor stacking contexts and outside ancestor `overflow: hidden`. Z index, `2000`.
- Offset from trigger, 6 px gutter without `pointer`, 10 px gutter with `pointer` (matches `canvas-tooltip`).
- Overflow, none. The surface is not a scroll container, `canvas-scroll-area` wraps the body when content may exceed `max-height`. Long unbreakable tokens are broken by `overflow-wrap: anywhere`.

### Size

The `size` attribute sets `max-width`.

- `sm`, 280 px.
- `md` default, 360 px.
- `lg`, 480 px.
- `auto`, `calc(100vw - 16px)`. Surface grows to content width up to the viewport cap. Use for wide tables, long labels, or content whose width is known only at runtime.
- Override via `--canvas-popover-max-width` when the content has a known ideal width.
- Effective cap, `min(size default or override, calc(100vw - 8px))` for fixed sizes, `calc(100vw - 16px)` for `auto`. The popover shrinks below the configured size when the viewport is narrower.

### Height

- No hard default cap. The effective `max-height` is `min(--canvas-popover-max-height override, calc(100vh - 8px), available space in chosen direction)`.
- When content fits below the trigger, direction is down. When content does not fit below, direction is whichever of up or down has more room. After the direction is chosen, `max-height` caps at that side's available space.
- Scroll inside the surface is automatic when content exceeds the cap.

### Placement

- Default, auto. Component measures trigger rect and content against the viewport on open and picks direction plus alignment.
- Direction, down by default. Flips to up when content does not fit below and up has more room.
- Alignment, start by default. Flips to end when the start edge would clip the viewport right.
- Explicit `direction` and `align` attributes pin the corresponding axis.

### Scroll behavior

- The popover follows the trigger on scroll and resize, repositioning continuously while visible.
- When the trigger leaves the viewport, the surface visually hides via `visibility: hidden` without closing. When the trigger scrolls back, the surface reappears.
- `dismiss-on-scroll` opts into closing on any scroll.

### Focus

- Focus moves into the surface on open, to the first focusable descendant or to the surface itself.
- Escape closes the popover, returns focus to the trigger, and dispatches `cancel`.
- Tab escapes the popover to the next document tab stop. Popover does not trap focus. Content that needs modality and focus trap belongs in `canvas-modal`.

### ARIA

- Surface, `role="dialog"`, `aria-modal="false"`, `aria-label` from the `label` attribute.
- Trigger, `aria-haspopup="dialog"` and `aria-expanded`, wired by the component.

### Pointer

The `pointer` boolean attribute renders a speech balloon arrow on the side of the surface that faces the trigger. Same artwork as `canvas-tooltip`.

- Artwork, 14 px by 7 px SVG triangle, rotated 45 degrees equivalent via path geometry. Border color `#d4d4d5`, fill `var(--color-surface, #FFFFFF)` on the overlay cover.
- Layering, grey arrow sits behind the surface so only the protruding tip shows in the border color. White cover sits above the surface and masks the 1 px surface border at the 14 px joint so the arrow reads as continuous with the surface body. Same technique as the tooltip.
- Offset, 5 px of the 7 px arrow protrudes outside the surface, 2 px overlaps behind the surface so the cover has a surface to paint on.
- Position, arrow tracks the trigger center even when the surface edge clamps inward from the viewport. Clamp inside the surface keeps the arrow 6 px from each corner so it cannot slide into the border radius.
- Flip, when auto placement flips direction from down to up, the arrow moves from the surface top edge to the surface bottom edge and the SVG inverts so the tip still points at the trigger.
- Distance, when `pointer` is set the surface sits 10 px from the trigger with 8 px of viewport margin. Without `pointer`, 6 px gap and 4 px margin.

### Border gray alignment

Anchored surfaces and containers share one gray. Form indicators share a second gray that darkens on hover.

- `#d4d4d5` on container chrome, `canvas-tooltip`, `canvas-popover` surface, `canvas-card` outer border.
- `rgba(34, 36, 38, 0.15)` on form controls and form indicators, `canvas-input`, `canvas-dropdown`, `canvas-combobox`, `canvas-textarea`, `canvas-multi-select`, `canvas-checkbox` resting, `canvas-radio` resting. Darkens to `rgba(34, 36, 38, 0.35)` on hover, to `#85b7d9` on focus.

Do not introduce a third gray without mapping it into one of these two categories.

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
