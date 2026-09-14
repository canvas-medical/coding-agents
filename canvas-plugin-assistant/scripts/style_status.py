#!/usr/bin/env python3
"""Sole producer of .cpa-workflow-artifacts/style-status.json.

Both enforcement points for the Canvas code-style standard record their outcome
through this one file: CPA's ``/cpa:style`` (``--run``, which executes the checks
itself) and Studio's deploy-time gate (``--record``, which already holds the exit
codes and only needs the JSON emitted). Keeping a single producer means the
payload shape, the ``style_clean`` rule, and the atomic write cannot drift
between the two repos.

Stdlib-only on purpose: a deploy-critical caller must not depend on a resolver
being healthy, so Studio invokes this with plain ``python3``.

Usage:
  style_status.py --run [--plugin-dir DIR] --ruff-config PATH [--mypy-config PATH]
  style_status.py --record ruff=pass mypy=fail manifest=skip [--plugin-dir DIR]
  style_status.py --record none            # nothing ran; records the unknown state

Outcomes are ``pass``, ``fail``, or ``skip``. A skipped check is omitted from
``checks`` rather than recorded as passing, so the file never claims a check
succeeded when it did not run.

``style_clean`` is:
  true   every required check ran and passed
  false  a check that ran failed
  null   a required check did not run, so the state is genuinely unknown

Exit codes:
  0  the status file was written
  2  bad usage, or the file could not be written
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Where the record lives, relative to the plugin directory. CPA commits this
# directory so the status travels with the plugin; Studio gitignores it so it
# stays a local record of the build.
STATUS_PATH = Path(".cpa-workflow-artifacts") / "style-status.json"

# Bumped whenever the payload shape changes, so a reader can reject a shape it
# does not understand instead of misinterpreting it.
SCHEMA_VERSION = 1

# Checks that must have run for `style_clean` to be a real answer. The manifest
# check is excluded: it only applies to a plugin that has a CANVAS_MANIFEST.json,
# formatting is auto-applied, and it never blocks.
REQUIRED_CHECKS = ("ruff", "mypy")

CHECK_NAMES = ("ruff", "mypy", "manifest")
OUTCOMES = ("pass", "fail", "skip")

# Exit codes that mean the tool RAN and is describing the plugin: 0 clean, 1
# diagnostics. Anything else means it could not do its job, so it has said
# nothing about the code and the check is recorded as skipped, not failed.
#
# ruff and mypy both document 2 as "the tool itself failed" -- an unparseable or
# missing config, a bad argument. Testing the complement rather than `== 2` also
# covers what the documented contract does not: a signal kill is negative (-9 on
# an OOM-kill) and a future version could add a code above 2.
#
# Verified against ruff 0.15.14 and mypy 1.19: violations, a source syntax error,
# and a missing input file all exit 1; an unknown rule selector, a missing
# --config path, and a missing mypy --config-file all exit 2.
TOOL_REPORTED_ON_CODE = (0, 1)

_RUFF_TIMEOUT = 60
_MYPY_TIMEOUT = 120
_MANIFEST_TIMEOUT = 15


def build_payload(outcomes: dict[str, str]) -> dict:
    """Assemble the status payload from per-check outcomes.

    ``outcomes`` maps a check name to ``pass``/``fail``/``skip``. Skipped checks
    are dropped from ``checks``; a required check that is skipped or absent makes
    ``style_clean`` null rather than vacuously true.
    """
    checks = {
        name: outcome == "pass"
        for name, outcome in outcomes.items()
        if outcome in ("pass", "fail")
    }
    if any(outcomes.get(name, "skip") == "skip" for name in REQUIRED_CHECKS):
        style_clean = None
    else:
        style_clean = all(checks.values())
    return {"version": SCHEMA_VERSION, "style_clean": style_clean, "checks": checks}


def write_status(plugin_dir: Path, payload: dict) -> Path:
    """Atomically write ``payload`` to the status file under ``plugin_dir``.

    Writes a temporary file in the destination directory and ``os.replace``s it
    into place, so a reader (or CPA's own ``git add``) only ever sees the whole
    old file or the whole new one, never a torn one.
    """
    dest = plugin_dir / STATUS_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload) + "\n"
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(dest.parent),
        prefix=".style-status-",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, dest)
    except OSError:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise
    return dest


def _run(cmd: list[str], cwd: Path, timeout: int) -> tuple[int, str] | None:
    """Run ``cmd``; return (returncode, combined output), or None if it could not
    run at all (spawn failure or timeout), which is a skip rather than a failure."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except (FileNotFoundError, OSError) as exc:
        print(f"style_status: could not spawn {cmd[0]}: {exc}", file=sys.stderr)
        return None
    except subprocess.TimeoutExpired:
        print(
            f"style_status: {cmd[0]} timed out after {timeout}s", file=sys.stderr
        )
        return None
    return proc.returncode, proc.stdout.decode("utf-8", errors="ignore").strip()


def run_checks(
    plugin_dir: Path, ruff_config: str, mypy_config: str | None
) -> dict[str, str]:
    """Run the four style checks against ``plugin_dir`` and return per-check outcomes.

    ruff formatting and lint are auto-fixed in place, as is manifest formatting;
    what remains is reported. A check that cannot run is a skip.
    """
    outcomes: dict[str, str] = {}

    _run(["ruff", "format", "--config", ruff_config, "."], plugin_dir, _RUFF_TIMEOUT)

    check = _run(
        [
            "ruff", "check", "--fix",
            "--config", ruff_config,
            "--output-format", "concise",
            ".",
        ],
        plugin_dir,
        _RUFF_TIMEOUT,
    )
    if check is None:
        outcomes["ruff"] = "skip"
    else:
        returncode, output = check
        if returncode not in TOOL_REPORTED_ON_CODE:
            print(f"style_status: ruff could not run: {output}", file=sys.stderr)
            outcomes["ruff"] = "skip"
        else:
            outcomes["ruff"] = "pass" if returncode == 0 else "fail"
            if returncode != 0:
                print(output, file=sys.stderr)

    if mypy_config and Path(mypy_config).is_file():
        mypy = _run(
            ["mypy", "--config-file", mypy_config, "."], plugin_dir, _MYPY_TIMEOUT
        )
        if mypy is None:
            outcomes["mypy"] = "skip"
        else:
            returncode, output = mypy
            if returncode not in TOOL_REPORTED_ON_CODE:
                print(f"style_status: mypy could not run: {output}", file=sys.stderr)
                outcomes["mypy"] = "skip"
            else:
                outcomes["mypy"] = "pass" if returncode == 0 else "fail"
                if returncode != 0:
                    print(output, file=sys.stderr)
    else:
        outcomes["mypy"] = "skip"

    manifest = plugin_dir / "CANVAS_MANIFEST.json"
    if manifest.is_file():
        formatter = Path(__file__).parent / "format_manifest.py"
        result = _run(
            [sys.executable, str(formatter), str(manifest)],
            plugin_dir,
            _MANIFEST_TIMEOUT,
        )
        outcomes["manifest"] = (
            "skip" if result is None else ("pass" if result[0] == 0 else "fail")
        )
    else:
        outcomes["manifest"] = "skip"

    return outcomes


def parse_record(values: list[str]) -> dict[str, str]:
    """Parse ``name=outcome`` pairs. The single token ``none`` means nothing ran."""
    if values == ["none"]:
        return dict.fromkeys(CHECK_NAMES, "skip")
    outcomes: dict[str, str] = {}
    for value in values:
        name, _, outcome = value.partition("=")
        if name not in CHECK_NAMES:
            raise ValueError(f"unknown check {name!r} (expected one of {CHECK_NAMES})")
        if outcome not in OUTCOMES:
            raise ValueError(
                f"unknown outcome {outcome!r} for {name} (expected one of {OUTCOMES})"
            )
        outcomes[name] = outcome
    for name in CHECK_NAMES:
        outcomes.setdefault(name, "skip")
    return outcomes


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--run", action="store_true", help="run the checks, then record their outcomes"
    )
    mode.add_argument(
        "--record",
        nargs="+",
        metavar="NAME=OUTCOME",
        help="record outcomes the caller already has ('none' for nothing ran)",
    )
    parser.add_argument("--plugin-dir", default=".", help="the plugin directory")
    parser.add_argument("--ruff-config", help="path to the Canvas ruff ruleset")
    parser.add_argument("--mypy-config", help="path to the mypy config")
    args = parser.parse_args(argv)

    plugin_dir = Path(args.plugin_dir).resolve()
    if not plugin_dir.is_dir():
        print(f"style_status: not a directory: {plugin_dir}", file=sys.stderr)
        return 2

    if args.run:
        if not args.ruff_config:
            print("style_status: --run requires --ruff-config", file=sys.stderr)
            return 2
        if not Path(args.ruff_config).is_file():
            print(
                f"style_status: ruff config not found: {args.ruff_config}",
                file=sys.stderr,
            )
            outcomes = dict.fromkeys(CHECK_NAMES, "skip")
        else:
            outcomes = run_checks(plugin_dir, args.ruff_config, args.mypy_config)
    else:
        try:
            outcomes = parse_record(args.record)
        except ValueError as exc:
            print(f"style_status: {exc}", file=sys.stderr)
            return 2

    payload = build_payload(outcomes)
    try:
        dest = write_status(plugin_dir, payload)
    except OSError as exc:
        print(f"style_status: could not write status: {exc}", file=sys.stderr)
        return 2
    print(f"{json.dumps(payload)} -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
