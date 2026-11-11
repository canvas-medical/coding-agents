#!/usr/bin/env python3
"""PreToolUse gate: run `canvas validate` before a plugin is committed, installed or deployed.

Off unless CPA_PLUGIN_GATE is `advise` (findings go back to Claude, nothing is
stopped) or `block` (a failure stops the tool call, and Claude sees why).
Warnings from a passing validate reach Claude in either mode and never stop anything.
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
# How `canvas validate` prints a lint warning: "  ⚠ handlers/h.py:1  [code]  message".
WARNING_LINE = re.compile(r"^[ \t]*(⚠ \S+[ \t]+\[[\w-]+\].*)$", re.MULTILINE)
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


class OutsideSession(Exception):
    """An installer target the gate will not check: checking runs code, and the hook runs
    before the call is approved, so only plugins inside the session's working directory are."""


def target_dir(payload: dict) -> Path | None:
    """The plugin the gated tool call acts on, or None when it acts on no plugin."""
    cwd = Path(payload.get("cwd") or ".").resolve()
    tool_input = payload.get("tool_input") or {}
    if payload.get("tool_name", "").endswith(INSTALLER_TOOL_SUFFIX):
        plugin_name = str(tool_input.get("plugin_name", ""))
        if not PLUGIN_NAME.fullmatch(plugin_name):
            raise OutsideSession
        target = (Path(tool_input.get("cwd") or cwd) / plugin_name).resolve()
        if target != cwd and cwd not in target.parents:
            raise OutsideSession
        return find_plugin_dir(target)
    return find_plugin_dir(cwd)


def validate_warnings(stdout: str) -> list[str]:
    """The warnings a passing `canvas validate` printed: each `⚠` lint line, and each
    `Warning:` block (such as handlers the manifest never loads) with its `  - ` items."""
    warnings: list[str] = []
    in_block = False
    for line in stdout.splitlines():
        if in_block and line.startswith("  - "):
            warnings[-1] += f"\n{line}"
            continue
        in_block = line.startswith("Warning:")
        if in_block:
            warnings.append(line)
        elif WARNING_LINE.match(line):
            warnings.append(line.strip())
    return warnings


def canvas_executable(plugin_dir: Path) -> str | None:
    """The project's own `.venv` canvas (CPA's scaffold puts it beside or above the plugin),
    else `canvas` from PATH (Studio's image). Never `uv run`, which builds environments.
    """
    for directory in (plugin_dir, plugin_dir.parent):
        candidate = directory / ".venv" / "bin" / "canvas"
        if candidate.is_file():
            return str(candidate)
    return shutil.which("canvas")


def run_validate(plugin_dir: Path) -> tuple[str | None, list[str]]:
    """What the agent must fix (None when `canvas validate` passes), and the warnings it printed."""
    executable = canvas_executable(plugin_dir)
    if executable is None:
        return (
            "`canvas validate` could not start: no `canvas` in the project's `.venv` or on PATH. Run `uv sync`.",
            [],
        )
    try:
        result = subprocess.run(
            [executable, "validate", str(plugin_dir)],
            cwd=plugin_dir,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=VALIDATE_TIMEOUT_SECONDS,
            check=False,
        )
    except OSError as error:
        return f"`canvas validate` could not start ({error}).", []
    except subprocess.TimeoutExpired:
        return f"`canvas validate` did not finish within {VALIDATE_TIMEOUT_SECONDS} seconds.", []
    if result.returncode == 0:
        return None, validate_warnings(result.stdout)
    output = "\n".join(t for t in (result.stdout.strip(), result.stderr.strip()) if t)
    if "No such command 'validate'" in output:
        return (
            "`canvas validate` could not run: this canvas CLI predates it. Upgrade the `canvas` package.",
            [],
        )
    problem = "`canvas validate` reported errors the Canvas plugin runner will reject:\n\n" + (
        output[-OUTPUT_LIMIT:] or "(no output)"
    )
    return problem, []


def main(stdin: str) -> int:
    """Run the gate for one hook payload and return the hook's exit code."""
    mode = environ.get(MODE_VARIABLE, "off").strip().lower() or "off"
    if mode not in MODES:
        # Exit 2, not 1: Claude Code runs the call after a non-blocking error, so a typo would
        # turn the gate off unnoticed.
        print(
            f"{MODE_VARIABLE}={mode!r} is not one of {', '.join(MODES)}. Fix the setting, "
            "or set it to off; until then the plugin gate stops every call it covers.",
            file=sys.stderr,
        )
        return 2
    if mode == "off":
        return 0
    try:
        plugin_dir = target_dir(json.loads(stdin or "{}"))
    except OutsideSession:
        if mode == "block":
            print(
                "CPA plugin gate: it checks only plugins inside the session's working directory, "
                "so it stopped this install. Run it with a plugin from there.",
                file=sys.stderr,
            )
            return 2
        return 0
    if plugin_dir is None:
        return 0
    problem, warnings = run_validate(plugin_dir)
    if problem is not None and mode == "block":
        print(
            f"CPA plugin gate ({plugin_dir.name}): {problem}\n\nFix these, then try again.",
            file=sys.stderr,
        )
        return 2
    if problem is not None:
        context = f"CPA plugin gate, advisory only ({MODE_VARIABLE}=advise), for {plugin_dir.name}: {problem}"
    elif warnings:
        context = (
            f"CPA plugin gate: `canvas validate` passed for {plugin_dir.name} with warnings. They do not block; "
            "fix them unless the code is intended:\n" + "\n".join(warnings)
        )
    else:
        return 0
    print(
        json.dumps(
            {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": context}}
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.stdin.read()))
