---
name: icon-generation
description: Generate app icons — black rounded square with white symbol, 128x128 PNG
---

# Icon Generation Skill

Generate consistent, branded icons for Canvas SDK plugins and small applications. Every icon follows the same visual language: a black rounded square with a simple white symbol, on a transparent background.

## When to Use This Skill

- Creating a new plugin or app that needs an icon
- User requests an icon for an existing project
- Regenerating or updating an existing icon

## Design Specification

### Canvas & Background

- SVG with `viewBox="0 0 128 128"`
- Transparent background (no background rectangle)

### Rounded Square

- Black (`#000000`) filled rectangle
- Full bleed: `x="0" y="0"` with `width="128" height="128"`
- Corner radius `rx="24"`

### Layout & Safe Zone

- Icons must be visually centered around `(64, 64)`
- The `scale(3.5)` transform produces an **84x84** bounding box (66% canvas fill), within the recommended 60–80% range
- `translate(22,22)` centers the scaled icon on the 128x128 canvas
- Allow pointed shapes (triangles, arrows) or circular elements to slightly overshoot the safe zone to carry the same visual weight as blocky shapes

### Symbol

- White (`#FFFFFF`) only — stroke-based, matching Lucide's native style
- Stroke weight is controlled by the `<g>` wrapper: `stroke-width="2"` in the 24x24 coordinate space scales to **7px** at 3.5×
- Always use `stroke-linecap="round"` and `stroke-linejoin="round"`
- No gradients, no drop shadows, no color, no fills on icon shapes

### Optical Centering

- **Play/triangle icons:** Nudge 1–2px right (in the 24x24 space) to compensate for left-heavy visual weight
- **Circular icons:** Scale 102% to match the perceived size of rectangular icons
- **Top-heavy icons:** Nudge 1px down

## SVG Template

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="24" fill="#000000"/>
  <g transform="translate(22,22) scale(3.5)" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <!-- icon inner elements here (path, rect, circle, line, polyline) -->
  </g>
</svg>
```

The `<g>` wrapper handles all styling. Icon elements inside it need only their geometry attributes — strip any `fill`, `stroke`, `stroke-width`, `stroke-linecap`, and `stroke-linejoin` from the source SVG elements before inserting them.

## Icon Source: Lucide Library

**Always use professional icon library paths.** Never hand-draw SVG coordinates — library paths produce dramatically better results.

### Primary: Lucide Icons

Fetch the raw SVG from GitHub:

```
https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{name}.svg
```

1. Fetch the SVG using `WebFetch` or `curl`
2. Extract the inner elements (`<path>`, `<rect>`, `<circle>`, `<line>`, `<polyline>`) — discard the outer `<svg>` tag
3. Strip styling attributes from each element (`fill`, `stroke`, `stroke-width`, `stroke-linecap`, `stroke-linejoin`) — the `<g>` wrapper provides these
4. Place the cleaned elements inside the `<g>` wrapper in the template

### Fallback: Tabler Icons

If Lucide doesn't have a matching icon, try Tabler (5,000+ icons, same 24x24 format):

```
https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/{name}.svg
```

Same extraction and wrapping process.

### Last Resort: Hand-Draw

Only if neither library has a suitable icon, hand-draw in the **24x24 coordinate space** using the same `<g transform>` wrapper. This ensures consistent sizing and style.

### Choosing the Right Icon

- **Search Lucide first** at [lucide.dev](https://lucide.dev) — browse by name, tags, categories
- **Prefer concrete symbols** over abstract ones (`camera` > "media", `lock` > "security")
- **Pick the simplest variant** — `bell` not `bell-ring`, `video` not `video-off`
- **Search by metaphor**, not just literal name ("group therapy" → `users`, "telehealth" → `video` or `monitor`)

## Composing Compound Icons

When a single icon can't represent the concept, compose two:

- **Primary icon:** Place normally within the `<g>` wrapper
- **Badge icon:** 30–35% size, positioned in the bottom-right or top-right corner of the 24x24 space
- Maintain **4px+** separation between primary and badge elements (in 24x24 space)
- Maximum **2 concepts** per icon — more than that becomes unreadable
- Example concept: telehealth = `monitor` (primary) + `heart-pulse` (badge)

## Examples

All examples use Lucide icon paths wrapped in the `translate(22,22) scale(3.5)` template.

### Lock

Simple security icon — a rectangle (body) and a path (shackle). Two elements, immediately recognizable.

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="24" fill="#000000"/>
  <g transform="translate(22,22) scale(3.5)" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
  </g>
</svg>
```

### Bell

Organic curves — two paths forming the bell body and clapper. Shows how professional paths handle complex curves cleanly.

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="24" fill="#000000"/>
  <g transform="translate(22,22) scale(3.5)" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M10.268 21a2 2 0 0 0 3.464 0"/>
    <path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326"/>
  </g>
</svg>
```

### Bookmark

Minimal — a single path. Demonstrates the elegance of simplicity.

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="24" fill="#000000"/>
  <g transform="translate(22,22) scale(3.5)" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M17 3a2 2 0 0 1 2 2v15a1 1 0 0 1-1.496.868l-4.512-2.578a2 2 0 0 0-1.984 0l-4.512 2.578A1 1 0 0 1 5 20V5a2 2 0 0 1 2-2z"/>
  </g>
</svg>
```

## Quality Checklist

Before converting to PNG, verify:

1. **Thumbnail test** — Is the icon recognizable at 32px? If not, simplify.
2. **Element count** — Fewer than 6 distinct visual elements? If not, simplify.
3. **Optical centering** — Apply nudges for triangles, circles, or top-heavy shapes (see Optical Centering above).
4. **Stroke consistency** — All strokes should be the same weight (the `<g>` wrapper handles this automatically when using library paths).

## Workflow

1. **Infer the icon subject** from the plugin's name, purpose, or surrounding context. Do not ask the user what to draw — figure it out.
2. **Ask the user where to save** the PNG file. Always ask; never assume.
3. **Search Lucide** for a matching icon at [lucide.dev](https://lucide.dev) or by fetching from the GitHub URL pattern. If found, fetch the SVG, extract inner elements, strip styling attributes, and wrap in the template.
4. **If no Lucide match**, search Tabler Icons. Same fetch → extract → wrap process.
5. **If no library match**, hand-draw in the 24x24 coordinate space using the same `<g transform>` wrapper.
6. **Run the quality checklist** — thumbnail test, element count, optical centering, stroke consistency.
7. **Write the SVG to `/tmp`** as a temporary intermediate file (e.g. `/tmp/icon-name.svg`).
8. **Convert to 128x128 PNG** at the user's chosen location using `rsvg-convert`:
   ```bash
   rsvg-convert -w 128 -h 128 /tmp/icon-name.svg -o output.png
   ```
9. **Delete the temporary SVG** — `rm /tmp/icon-name.svg`. Only the PNG should remain.
10. **Report results** — provide the path to the PNG file.

## Conversion

The SVG is a temporary intermediate — write it to `/tmp`, convert to PNG, then delete it.

```bash
rsvg-convert -w 128 -h 128 /tmp/icon-name.svg -o output.png && rm /tmp/icon-name.svg
```

## Error Handling

If `rsvg-convert` is not available:
1. Keep the temporary SVG file in `/tmp` so the user can convert it manually
2. Inform the user that the PNG could not be generated
3. Suggest installing librsvg: `brew install librsvg`

## Automated Flow Context

When this skill is invoked from an **automated workflow** — specifically the **plugin-brainstorm agent** (during new plugin creation) or the **wrap-up command** (when generating a missing icon) — the following overrides apply:

- **Do NOT ask the user where to save.** Auto-save the PNG to `{plugin_name_snake}/assets/`.
- **Create the assets directory** if it doesn't exist: `mkdir -p {plugin_name_snake}/assets`
- **Update `CANVAS_MANIFEST.json`** with the icon path: `"icon": "assets/{icon-filename}.png"`
- **Skip workflow step 2** (ask user where to save) — the save location is predetermined.

This keeps the automated flows non-interactive while preserving the "ask where to save" behavior for manual `/cpa:create-icon` invocations.
