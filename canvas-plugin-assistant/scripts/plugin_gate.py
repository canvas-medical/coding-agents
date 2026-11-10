#!/usr/bin/env python3
"""PreToolUse gate: run `canvas validate` before a plugin is committed, installed or deployed.

Off unless CPA_PLUGIN_GATE is `advise` (findings go back to Claude, nothing is
stopped) or `block` (a failure stops the tool call, and Claude sees why).
Stdlib only, so the hook never depends on a resolver being healthy.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from os import environ
from pathlib import Path

MODE_VARIABLE = "CPA_PLUGIN_GATE"
MODES = ("off", "advise", "block")
MANIFEST = "CANVAS_MANIFEST.json"
INSTALLER_TOOL_SUFFIX = "canvas_cmd_line__installer"
PLUGIN_NAME = re.compile(r"[A-Za-z0-9_-]+")
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
    """The plugin the gated tool call acts on, or None when it acts on no plugin.

    The hook runs before the call is approved, so an installer target outside the
    session's working directory is never checked: checking runs code there.
    """
    cwd = Path(payload.get("cwd") or ".").resolve()
    tool_input = payload.get("tool_input") or {}
    if payload.get("tool_name", "").endswith(INSTALLER_TOOL_SUFFIX):
        plugin_name = str(tool_input.get("plugin_name", ""))
        if not PLUGIN_NAME.fullmatch(plugin_name):
            return None
        target = (Path(tool_input.get("cwd") or cwd) / plugin_name).resolve()
        if target != cwd and cwd not in target.parents:
            return None
        return find_plugin_dir(target)
    return find_plugin_dir(cwd)


def canvas_executable(plugin_dir: Path) -> str | None:
    """The project's own `.venv` canvas (CPA's scaffold puts it beside or above the plugin),
    else `canvas` from PATH (Studio's image). Never `uv run`, which builds environments."""
    for directory in (plugin_dir, plugin_dir.parent):
        candidate = directory / ".venv" / "bin" / "canvas"
        if candidate.is_file():
            return str(candidate)
    return shutil.which("canvas")


def run_validate(plugin_dir: Path) -> str | None:
    """What the agent must fix, or None when `canvas validate` passes."""
    executable = canvas_executable(plugin_dir)
    if executable is None:
        return "`canvas validate` could not start: no `canvas` in the project's `.venv` or on PATH. Run `uv sync`."
    try:
        result = subprocess.run(
            [executable, "validate", str(plugin_dir)],
            cwd=plugin_dir,
            capture_output=True,
            text=True,
            timeout=VALIDATE_TIMEOUT_SECONDS,
            check=False,
        )
    except OSError as error:
        return f"`canvas validate` could not start ({error})."
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
