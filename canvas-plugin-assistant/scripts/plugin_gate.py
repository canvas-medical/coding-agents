#!/usr/bin/env python3
"""PreToolUse gate: run `canvas validate` before a plugin is committed, installed or deployed.

Off unless CPA_PLUGIN_GATE is `advise` (findings go back to Claude, nothing is
stopped) or `block` (a failure stops the tool call, and Claude sees why).
Stdlib only, so the hook never depends on a resolver being healthy.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from os import environ
from pathlib import Path

MODE_VARIABLE = "CPA_PLUGIN_GATE"
MODES = ("off", "advise", "block")
MANIFEST = "CANVAS_MANIFEST.json"
INSTALLER_TOOL_SUFFIX = "canvas_cmd_line__installer"
VALIDATE_TIMEOUT_SECONDS = 120
OUTPUT_LIMIT = 3500


def find_plugin_dir(start: Path) -> Path | None:
    """The plugin package at or above ``start``, else the only one directly inside it."""
    for directory in (start, *start.parents):
        if (directory / MANIFEST).is_file():
            return directory
    if not start.is_dir():
        return None
    children = [child for child in start.iterdir() if (child / MANIFEST).is_file()]
    return children[0] if len(children) == 1 else None


def target_dir(payload: dict) -> Path | None:
    """The plugin the gated tool call acts on, or None when it acts on no plugin."""
    cwd = Path(payload.get("cwd") or ".")
    tool_input = payload.get("tool_input") or {}
    if payload.get("tool_name", "").endswith(INSTALLER_TOOL_SUFFIX):
        install_cwd = Path(tool_input.get("cwd") or cwd)
        return find_plugin_dir(install_cwd / tool_input.get("plugin_name", ""))
    return find_plugin_dir(cwd)


def is_uv_project(plugin_dir: Path) -> bool:
    """Whether the nearest pyproject.toml declares a `[project]`, so `uv run` can run its canvas.

    Studio's workspaces carry a pyproject.toml with no `[project]` table, where
    `uv run` exits 2 before canvas starts.
    """
    for directory in (plugin_dir, *plugin_dir.parents):
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file():
            return any(line.strip() == "[project]" for line in pyproject.read_text().splitlines())
    return False


def validate_command(plugin_dir: Path) -> list[str]:
    """The plugin project's own canvas through uv, else `canvas` from PATH (Studio's image)."""
    if is_uv_project(plugin_dir) or not shutil.which("canvas"):
        return ["uv", "run", "canvas", "validate", str(plugin_dir)]
    return ["canvas", "validate", str(plugin_dir)]


def run_validate(plugin_dir: Path) -> str | None:
    """What the agent must fix, or None when `canvas validate` passes."""
    try:
        result = subprocess.run(
            validate_command(plugin_dir),
            cwd=plugin_dir,
            capture_output=True,
            text=True,
            timeout=VALIDATE_TIMEOUT_SECONDS,
            check=False,
        )
    except OSError:
        return "`canvas validate` could not start (neither `canvas` nor `uv` is on PATH)."
    except subprocess.TimeoutExpired:
        return f"`canvas validate` did not finish within {VALIDATE_TIMEOUT_SECONDS} seconds."
    if result.returncode == 0:
        return None
    output = "\n".join(t for t in (result.stdout.strip(), result.stderr.strip()) if t)
    if "No such command 'validate'" in output:
        return "`canvas validate` could not run: this canvas CLI predates it. Upgrade the `canvas` package."
    return "`canvas validate` reported errors the Canvas plugin runner will reject:\n\n" + (
        output[-OUTPUT_LIMIT:] or "(no output)"
    )


def main(stdin: str) -> int:
    """Run the gate for one hook payload and return the hook's exit code."""
    mode = environ.get(MODE_VARIABLE, "off").strip().lower() or "off"
    if mode not in MODES:
        print(f"{MODE_VARIABLE}={mode!r} is not one of {', '.join(MODES)}; the gate is off.", file=sys.stderr)
        return 1
    if mode == "off":
        return 0
    plugin_dir = target_dir(json.loads(stdin or "{}"))
    if plugin_dir is None:
        return 0
    problem = run_validate(plugin_dir)
    if problem is None:
        return 0
    if mode == "block":
        print(f"CPA plugin gate ({plugin_dir.name}): {problem}\n\nFix these, then try again.", file=sys.stderr)
        return 2
    context = f"CPA plugin gate, advisory only ({MODE_VARIABLE}=advise), for {plugin_dir.name}: {problem}"
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.stdin.read()))
