# Setup

How to serve the design system from a Canvas plugin and load it into the HTML shell. Read before any other reference file when the plugin is new or the assets are missing.

## Prerequisite Check

When working inside a Canvas plugin directory that uses `<canvas-*>` web components, check that the plugin's `static/` directory contains both `canvas-plugin-ui.js` and `canvas-plugin-ui.css`. If either file is missing, stop and tell the user to copy them from the skill's `assets/` directory into the plugin's static directory and set up the serving routes before proceeding with any `<canvas-*>` markup.

Compare line counts of the plugin's static files against the skill source files (`assets/canvas-plugin-ui.js` and `assets/canvas-plugin-ui.css`). Run `wc -l` on each pair. If any counts differ, warn the user that the skill's source files may have been updated since the plugin's copies were placed. Offer to recopy. Do not recopy without user approval.

## Serving Through SimpleAPI

Each asset file needs a SimpleAPI GET route that reads it via `render_to_string` and returns it with the correct content type. The plugin sandbox does not allow `os`, `pathlib`, or `open()` for file access. Use `render_to_string("static/filename")` for all file reads.

The SimpleAPI class serving these routes must inherit from `StaffSessionAuthMixin`. Plugin pages load inside an authenticated Canvas iframe that passes a staff session cookie. Without the mixin, asset routes return a credentials error instead of the file contents, and the page renders with no styling or components.

If the plugin sets a custom `Content-Security-Policy` header, the policy must include `'self'` in `style-src` and `script-src`. Without it the browser silently blocks the design system CSS and JS files and the page renders unstyled. `'unsafe-inline'` alone is not enough because it only covers inline styles and scripts, not files loaded via `<link>` or `<script src>`.

```python
@api.get("/canvas-plugin-ui.css")
def plugin_ui_css(self) -> list[Response]:
    return [
        Response(
            render_to_string("static/canvas-plugin-ui.css").encode(),
            status_code=HTTPStatus.OK,
            content_type="text/css",
        )
    ]

@api.get("/canvas-plugin-ui.js")
def plugin_ui_js(self) -> list[Response]:
    return [
        Response(
            render_to_string("static/canvas-plugin-ui.js").encode(),
            status_code=HTTPStatus.OK,
            content_type="application/javascript",
        )
    ]
```

## Loading in the HTML Shell

The plugin's index template includes two asset files and a Google Fonts link in the `<head>`. Replace `{plugin_name}` with the `name` field from `CANVAS_MANIFEST.json` (uses underscores) and `{prefix}` with the SimpleAPI PREFIX value (without the leading slash).

```html
<link href="https://fonts.googleapis.com/css?family=Lato:400,700,400italic,700italic&subset=latin" rel="stylesheet">
<link rel="stylesheet" href="/plugin-io/api/{plugin_name}/{prefix}/canvas-plugin-ui.css">
<script src="/plugin-io/api/{plugin_name}/{prefix}/canvas-plugin-ui.js"></script>
```

The Google Fonts link tag is required. The CSS file does not use `@import` for font loading, so without this tag the Lato typeface will not render. Plugin iframes do not inherit the parent page's fonts. Every `<canvas-*>` element works anywhere in the page body without additional script tags.

A copy-paste snippet for these three tags lives at `assets/head.html`.

## Plugin HTML Boilerplate

Start every plugin HTML page from this shell. Replace `{plugin_name}` with the name from `CANVAS_MANIFEST.json` and `{prefix}` with the SimpleAPI PREFIX value.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css?family=Lato:400,700,400italic,700italic&subset=latin" rel="stylesheet">
  <link rel="stylesheet" href="/plugin-io/api/{plugin_name}/{prefix}/canvas-plugin-ui.css">
  <script src="/plugin-io/api/{plugin_name}/{prefix}/canvas-plugin-ui.js"></script>
  <style>
    /* Plugin-specific CSS only. Use var(--token) for all values. */
  </style>
</head>
<body>
  <!-- Plugin content using <canvas-*> elements -->
</body>
</html>
```

## Global CSS Reset Detection

Before touching any `<canvas-*>` markup in an existing plugin, scan the plugin style tag for CSS resets. Flag any of the following patterns and offer to remove or scope them before proceeding.

- Universal selector rules, `* { margin: 0; padding: 0; box-sizing: border-box; }` or similar
- Bare `html`, `body`, `button`, `input`, `a` rules without a plugin scope class
- Linked reset libraries, `normalize.css`, `reset.css`, `sanitize.css`, `modern-normalize.css`
- Tailwind Preflight in the plugin head

Three things break when a reset is present. Light DOM components in the `canvas-accordion` family lose their intended padding and margins because universal rules match them directly. Typography (`font-family`, `line-height`, `color`) inherits across the Shadow DOM boundary and replaces Lato inside every component. The custom element host itself picks up the reset's box sizing and margin, shifting layout on every `<canvas-*>` tag.

The Google Fonts Lato link must stay. Do not suppress `font-family` on `html` or `body`.

## Host Communication

The `canvas-plugin-ui.js` file registers a `CanvasUI.utils` object on the global `window`. This provides a host communication bridge that plugins use to send messages to the Canvas app through a MessageChannel. The MessageChannel handshake (`INIT_CHANNEL`) is handled automatically when the script loads. No setup code is needed.

`CanvasUI.utils.dismissModal()` sends a `CLOSE_MODAL` message to the host app via the MessageChannel. Use this in plugins rendered on `DEFAULT_MODAL` or `NOTE` surfaces that need to close themselves after completing an action.

```html
<canvas-button onclick="CanvasUI.utils.dismissModal()">Done</canvas-button>
```

`CanvasUI.utils.resizeModal(width, height)` sends a `RESIZE` message with optional width and height values. Use this to adjust the iframe dimensions when the plugin content changes size. Both width and height are optional, omitting a value leaves that dimension unchanged on the host side.

```js
CanvasUI.utils.resizeModal(800, 600);
CanvasUI.utils.resizeModal(null, 300);
```

Include this communication bridge only for `DEFAULT_MODAL` and `NOTE` surfaces. Plugins on `RIGHT_CHART_PANE`, `RIGHT_CHART_PANE_LARGE`, `PAGE`, or `NEW_WINDOW` surfaces do not use these commands.
