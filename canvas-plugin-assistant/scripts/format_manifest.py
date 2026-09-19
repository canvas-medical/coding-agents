#!/usr/bin/env python3
"""Canonical formatter for CANVAS_MANIFEST.json.

Applies the Canvas manifest-style conventions that jsonschema validation does
not cover: a fixed key order (matching the manifest schema's property order), a
2-space indent, and a trailing newline. Stdlib-only on purpose — Studio's
deploy-time style gate shells out to this exact file so the ordering rule cannot
drift between the two repos, and a deploy-critical caller must not depend on a
resolver being healthy.

Usage: format_manifest.py <path-to-CANVAS_MANIFEST.json> [more paths...]

Exit codes:
  0  every file is valid (reformatted or already canonical)
  2  a file could not be read or parsed (left untouched; the caller decides)

Prints one line per file: "reformatted <path>" or "unchanged <path>".
"""

from __future__ import annotations

import json
import sys

# Top-level key order, matching the manifest schema property declaration order
# in canvas-plugins/canvas_cli/utils/validators/manifest_schema.py. Unknown keys
# are preserved and emitted after these, in their original order.
TOP_LEVEL_ORDER = [
    "sdk_version",
    "plugin_version",
    "name",
    "description",
    "variables",
    "secrets",
    "origins",
    "url_permissions",
    "components",
    "tags",
    "references",
    "license",
    "diagram",
    "readme",
    "custom_data",
]

# Sub-key order inside "components".
COMPONENTS_ORDER = [
    "commands",
    "protocols",
    "handlers",
    "content",
    "effects",
    "views",
    "applications",
    "questionnaires",
]

# Key order inside each entry of "variables".
VARIABLE_ORDER = ["name", "sensitive", "default"]


def _reorder(mapping: dict, order: list[str]) -> dict:
    """Return a new dict with known keys first (in `order`), then the rest as-is."""
    known = {key: mapping[key] for key in order if key in mapping}
    rest = {key: value for key, value in mapping.items() if key not in known}
    return {**known, **rest}


def canonicalize(manifest: dict) -> dict:
    """Return the manifest with its keys ordered by convention."""
    result = _reorder(manifest, TOP_LEVEL_ORDER)
    components = result.get("components")
    if isinstance(components, dict):
        result["components"] = _reorder(components, COMPONENTS_ORDER)
    variables = result.get("variables")
    if isinstance(variables, list):
        result["variables"] = [
            _reorder(entry, VARIABLE_ORDER) if isinstance(entry, dict) else entry
            for entry in variables
        ]
    return result


def format_file(path: str) -> bool | None:
    """Rewrite `path` in canonical form. Returns True if it changed, False if
    already canonical, None if it could not be read/parsed."""
    try:
        with open(path, encoding="utf-8") as handle:
            original = handle.read()
        manifest = json.loads(original)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"skipped {path}: {exc}", file=sys.stderr)
        return None
    if not isinstance(manifest, dict):
        print(f"skipped {path}: top level is not an object", file=sys.stderr)
        return None
    formatted = json.dumps(canonicalize(manifest), indent=2, ensure_ascii=False) + "\n"
    if formatted == original:
        return False
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(formatted)
    return True


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: format_manifest.py <CANVAS_MANIFEST.json> [...]", file=sys.stderr)
        return 2
    had_error = False
    for path in argv:
        changed = format_file(path)
        if changed is None:
            had_error = True
        else:
            print(f"{'reformatted' if changed else 'unchanged'} {path}")
    return 2 if had_error else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
