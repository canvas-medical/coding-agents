#!/usr/bin/env python3
"""Reads and writes .cpa-workflow-artifacts/style-status.json.

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
  style_status.py --check [--plugin-dir DIR] [--json]   # read the record back

Outcomes are ``pass``, ``fail``, or ``skip``. A skipped check is omitted from
``checks`` rather than recorded as passing, so the file never claims a check
succeeded when it did not run.

``style_clean`` is:
  true   every required check ran and passed
  false  a check that ran failed
  null   a required check did not run, so the state is genuinely unknown

``tree_digest`` fingerprints the sources the checks ran against, so a reader can
tell a verdict about this code from a verdict about code that has changed since.
That staleness is the one way a record misleads while being entirely well-formed,
so validating the shape alone would never catch it.

Reading is ``inspect_status``, which returns a ``StatusReport`` carrying the
verdict, the per-check booleans and the failed names; ``read_status`` is the
``(verdict, detail)`` view of it, and ``--check --json`` is the same report for
callers in another language or another repo. Consumers should use one of those
rather than loading the JSON directly, which is how the checks below get missed.
For an untrustworthy record the report's per-check fields stay empty instead of
repeating values out of a payload the verdict has already rejected.

Exit codes:
  --run / --record
    0  the status file was written
    2  bad usage, or the file could not be written
  --check
    0  the plugin is recorded clean
    1  a check that ran failed
    3  unknown: no record, unreadable, an unrecognized version, a required
       check that did not run, or a record describing different code. Distinct
       from 1 so a caller can say "re-run the checks" rather than "fix your
       code". Never 0 -- an unreadable record is not a pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# Where the record lives, relative to the plugin directory. CPA commits this
# directory so the status travels with the plugin; Studio gitignores it so it
# stays a local record of the build.
STATUS_PATH = Path(".cpa-workflow-artifacts") / "style-status.json"

# Bumped whenever the payload shape changes, so `read_status` can reject a shape
# it does not understand instead of misinterpreting it. A reader that skips this
# comparison is the one failure that is silent: a future v3 gets read as a v2.
#
# v2 adds `tree_digest`. The bump is what makes the upgrade safe: a v1 record
# carries no digest, so a v2 reader cannot tell whether it describes the current
# code, and the version check already answers UNKNOWN for it.
SCHEMA_VERSION = 2

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

# Resolving a tool on a cold uv cache downloads it, so the probe gets its own
# budget rather than borrowing the check's.
_PROBE_TIMEOUT = 120

# The style toolchain, resolved through uv instead of assumed present on PATH.
# Neither tool is declared by the plugins this runs against -- the example
# plugins' pyproject mentions ruff nowhere and Studio-generated repos have no
# pyproject at all -- so a bare `uv run ruff` exits 2, "Failed to spawn: ruff",
# and a bare `ruff` depends on whatever the machine happens to have.
#
# `--no-project` is what keeps this from creating a `.venv` inside the plugin
# directory, which is the same virtualenv `_RUFF_SCOPE_ARGS` exists to keep ruff
# out of. `--with` pins the version, so the verdict is reproducible rather than
# a property of the host.
#
# These specs are duplicated in `commands/style.md`, `commands/new-plugin.md`
# and `.github/workflows/update-canvas-ruff-config.yml`; a test asserts all
# four agree, because a drifted pin means the workflow validates against a ruff
# that is not the one running.
PINNED_RUFF = "ruff==0.15.14"
BOUNDED_MYPY = "mypy>=1.19.0,<2"

# The canonical mypy ruleset, used when a plugin ships no mypy.ini of its own.
# Without it mypy is skipped without ever being invoked, and because mypy is in
# REQUIRED_CHECKS that leaves `style_clean` null and `--check` answering UNKNOWN
# no matter how many rounds run. That is the normal case rather than an edge
# one: of five recently sampled Studio-generated plugins, none had a mypy.ini
# and none had a pyproject.toml. Studio's gate has always had this fallback.
FALLBACK_MYPY_CONFIG = Path(__file__).parent.parent / "config" / "mypy.ini"


def resolve_mypy_config(plugin_dir: Path, mypy_config: str | None) -> Path | None:
    """The mypy config to use, preferring the plugin's own over the fallback.

    Returns None only when neither resolves, which is the one case where
    skipping mypy is the honest answer.
    """
    if mypy_config:
        candidate = Path(mypy_config)
        if not candidate.is_absolute():
            candidate = plugin_dir / candidate
        if candidate.is_file():
            return candidate
    if FALLBACK_MYPY_CONFIG.is_file():
        return FALLBACK_MYPY_CONFIG
    return None

# Directories the digest never descends into: the record's own home, and the
# caches and virtualenvs that churn without the plugin's sources changing.
# Getting this set wrong is the failure that matters: too narrow and the digest
# moves on its own, every read answers UNKNOWN, and the nudge becomes noise
# people learn to click past.
_DIGEST_SKIP_DIRS = frozenset(
    {
        ".cpa-workflow-artifacts",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "node_modules",
    }
)

# What the checks actually read. Both tools are pointed at the plugin dir and
# both read stubs as well as sources: ruff lints and formats `.pyi`, and mypy
# prefers a `foo.pyi` over its `foo.py` sibling for what it reports, so a stub
# can decide a verdict with no `.py` changing at all.
_DIGEST_SUFFIXES = frozenset({".py", ".pyi"})

# mypy's config, matched at the top level only, because that is the only place
# anything looks for it: ``resolve_mypy_config`` reads ``plugin_dir/mypy.ini``
# in preference to the canonical ruleset. A nested copy is not an input, so
# digesting it would stale a record for a file nothing read.
#
# The manifest is not listed here because it is not found by name at a fixed
# depth -- see ``find_manifest``, whose result the digest covers wherever it
# resolved.
#
# The ruff ruleset is deliberately absent: it is passed by path from outside the
# plugin, and ``ruff --config <file>`` replaces hierarchical discovery entirely,
# so a plugin-local ruff config is never read either. The version pin and the CI
# sync are what hold the ruleset steady instead.
_DIGEST_TOP_LEVEL_NAMES = frozenset({"mypy.ini"})

# Manifests that belong to the tooling rather than to the plugin. canvas-cli
# ships template manifests inside its own package, so a plugin that has synced a
# virtualenv contains several.
_MANIFEST_SKIP_DIRS = _DIGEST_SKIP_DIRS | {"site-packages"}

# Keeps ruff out of the plugin's own virtualenv. The Canvas ruleset sets
# `exclude`, which REPLACES ruff's built-in exclusions rather than adding to
# them, and `.venv` is one of the defaults it drops -- so without this, `ruff
# format` and `ruff check --fix` walk into `.venv` and rewrite installed
# dependency source. `respect-gitignore` only covers it inside a git repo whose
# .gitignore lists `.venv`, which a plugin checked out as a plain directory is
# not.
#
# It is expressed as an inline config override rather than a command-line
# exclude flag, because the two subcommands do not accept the same flags:
# `ruff check` takes `--extend-exclude` but `ruff format` does not, and rejects
# it with "unexpected argument" (exit 2) -- which stops formatting happening at
# all while leaving `.venv` untouched, so it looks like the fix working.
# `--exclude` is accepted by both and is wrong for both: it REPLACES the
# ruleset's list, un-excluding `canvas_generated/` and `canvas_cli/templates/`.
#
# A second `--config` carrying a `key=value` override is accepted by both and
# extends rather than replaces, so it also tracks whatever the synced ruleset
# excludes instead of restating it. Measured against ruff 0.15.14 on a tree
# holding `.venv/`, `canvas_generated/` and `src/`: format rewrites only `src`,
# and check reports only `src`.
#
# This lives here, and in the same commands in `commands/style.md`, rather than
# in `config/pyproject.toml`: that file is a verbatim mirror of canvas-plugins'
# own pyproject, which `.github/workflows/update-canvas-ruff-config.yml`
# overwrites and pushes on a weekly cron. An edit there regresses within a week.
_RUFF_SCOPE_ARGS = ("--config", 'extend-exclude=[".venv"]')


def find_manifest(plugin_dir: Path) -> Path | None:
    """The plugin's CANVAS_MANIFEST.json, which is not always at ``plugin_dir``.

    The canonical layout puts the manifest in the inner snake_case package while
    CPA_PLUGIN_DIR is the kebab-case container, so looking only at
    ``plugin_dir/CANVAS_MANIFEST.json`` finds nothing on exactly the layout
    /cpa:new-plugin creates.

    Prefers the manifest whose own directory basename equals its ``name`` field,
    which is the directory ``canvas install`` names the plugin after; among
    equal candidates the shallowest wins. That is deliberately the same rule
    Studio resolves with, so the two enforcement points agree about which
    manifest is the plugin's.
    """
    candidates = [
        path
        for path in plugin_dir.rglob("CANVAS_MANIFEST.json")
        if path.is_file()
        and not _MANIFEST_SKIP_DIRS.intersection(path.relative_to(plugin_dir).parts)
    ]
    if not candidates:
        return None

    matching = [path for path in candidates if path.parent.name == _manifest_name(path)]
    pool = matching or candidates
    return min(pool, key=lambda path: len(path.relative_to(plugin_dir).parts))


def _manifest_name(manifest: Path) -> str | None:
    """The ``name`` a manifest declares, or None if it is unreadable."""
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data.get("name") if isinstance(data, dict) else None


def digest_files(plugin_dir: Path) -> list[Path]:
    """The files the digest covers, sorted, relative to ``plugin_dir``."""
    manifest = find_manifest(plugin_dir)
    found = []
    for path in plugin_dir.rglob("*"):
        relative = path.relative_to(plugin_dir)
        if _DIGEST_SKIP_DIRS.intersection(relative.parts):
            continue
        if not path.is_file():
            continue
        top_level_config = (
            len(relative.parts) == 1 and relative.name in _DIGEST_TOP_LEVEL_NAMES
        )
        if path.suffix in _DIGEST_SUFFIXES or top_level_config or path == manifest:
            found.append(relative)
    return sorted(found)


def tree_digest(plugin_dir: Path) -> str | None:
    """A digest of the sources the checks looked at, or None if it can't be taken.

    Recorded alongside the outcomes so a reader can tell a verdict about *this*
    code from a verdict about code that has since changed. That is the one way a
    record can mislead while being entirely well-formed, which no amount of
    validating its shape would catch.

    Names go into the hash as well as contents, so renaming a file or adding an
    empty one moves the digest. None on an unreadable tree: without a digest the
    record cannot be shown to be current, and every reader treats that as
    unknown rather than assuming it is.
    """
    accumulator = hashlib.sha256()
    try:
        for relative in digest_files(plugin_dir):
            accumulator.update(str(relative).encode("utf-8"))
            accumulator.update(b"\0")
            accumulator.update((plugin_dir / relative).read_bytes())
            accumulator.update(b"\0")
    except OSError as exc:
        print(f"style_status: could not digest the tree: {exc}", file=sys.stderr)
        return None
    return accumulator.hexdigest()


def build_payload(outcomes: dict[str, str], digest: str | None = None) -> dict:
    """Assemble the status payload from per-check outcomes.

    ``outcomes`` maps a check name to ``pass``/``fail``/``skip``. Skipped checks
    are dropped from ``checks``; a required check that is skipped or absent makes
    ``style_clean`` null rather than vacuously true.

    ``digest`` is the ``tree_digest`` of the sources the checks ran against, and
    is what lets a later read tell whether the code has moved on since.
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
    return {
        "version": SCHEMA_VERSION,
        "style_clean": style_clean,
        "checks": checks,
        "tree_digest": digest,
    }


# What `inspect_status` concluded about a plugin. UNKNOWN is deliberately distinct
# from FAILED: a record that is missing, unreadable, of an unrecognized version,
# or that says a required check never ran means nobody has assessed this code, so
# the answer is "re-run the checks" rather than "fix your code". It is never
# reported as CLEAN -- defaulting an unreadable status to a pass would be the
# vacuous-true defect this file's rules exist to prevent, moved to the read side.
CLEAN = "clean"
FAILED = "failed"
UNKNOWN = "unknown"

_VERDICT_EXIT = {CLEAN: 0, FAILED: 1, UNKNOWN: 3}


@dataclass(frozen=True)
class StatusReport:
    """Everything a caller may safely conclude from a recorded status.

    ``verdict`` and ``detail`` are the pair ``read_status`` returns. The rest is
    the structure a consumer would otherwise re-derive by parsing the JSON
    itself, which is exactly how the checks below get skipped.

    The per-check fields are populated ONLY for a record that validated. An
    untrustworthy one leaves them empty rather than echoing values out of a
    payload the verdict has just rejected, so a caller cannot act on numbers the
    verdict does not stand behind.
    """

    verdict: str
    detail: str
    present: bool = False
    checks: dict[str, bool] = field(default_factory=dict)
    failed: list[str] = field(default_factory=list)
    style_clean: bool | None = None
    path: str = ""

    @property
    def exit_code(self) -> int:
        """This verdict as a process exit code: 0 clean, 1 failed, 3 unknown."""
        return _VERDICT_EXIT[self.verdict]

    def as_dict(self) -> dict:
        """The report as JSON-serializable data, for ``--check --json``."""
        return {
            "verdict": self.verdict,
            "detail": self.detail,
            "exit_code": self.exit_code,
            "present": self.present,
            "checks": dict(self.checks),
            "failed": list(self.failed),
            "style_clean": self.style_clean,
            "path": self.path,
        }


def inspect_status(plugin_dir: Path) -> StatusReport:
    """Read the recorded status for ``plugin_dir`` as a structured report.

    Every way of failing to get a trustworthy answer collapses to UNKNOWN, so a
    caller cannot accidentally treat one as a pass.

    That includes a record about code that has since changed. The record is a
    claim about the tree the checks ran against, and on the CPA side the
    artifacts directory is committed, so a hand-edit after ``/cpa:style``, a
    checkout of an older commit, or a merge taking one side's status and the
    other side's code all present a verdict about a different tree. Comparing
    ``tree_digest`` is what turns that from invisible into UNKNOWN.
    """
    path = plugin_dir / STATUS_PATH
    location = str(path)

    def unknown(detail: str, present: bool = True) -> StatusReport:
        return StatusReport(UNKNOWN, detail, present=present, path=location)

    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return unknown("no style status recorded", present=False)
    except OSError as exc:
        return unknown(f"style status unreadable: {exc}")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return unknown(f"style status is not valid JSON: {exc}")
    if not isinstance(payload, dict):
        return unknown("style status is not an object")

    version = payload.get("version")
    if version != SCHEMA_VERSION:
        return unknown(
            f"style status version {version!r} is not {SCHEMA_VERSION} "
            "(written by a different version of this tool)"
        )

    checks = payload.get("checks")
    if not isinstance(checks, dict):
        return unknown("style status has no checks")

    # A value that is neither true nor false is a corrupt record, not a dirty
    # plugin, so it is UNKNOWN rather than FAILED. FAILED is reserved for a
    # literal false, which is a real finding about the code.
    malformed = sorted(
        name for name, passed in checks.items() if passed is not True and passed is not False
    )
    if malformed:
        return unknown(f"non-boolean result for: {', '.join(malformed)}")

    # Presence, not value: an absent key means that check did not run. Checked
    # before failures on purpose -- an incomplete assessment dominates a known
    # failure, because re-running surfaces that failure anyway while the reverse
    # would report a partial verdict as the whole story.
    missing = [name for name in REQUIRED_CHECKS if name not in checks]
    if missing:
        return unknown(f"did not run: {', '.join(missing)}")

    # Freshness last among the rejections, because "this describes different
    # code" is only worth saying once the record is known to be well-formed and
    # complete. A v1 record never reaches here: it fails the version check.
    recorded = payload.get("tree_digest")
    if not isinstance(recorded, str):
        return unknown("style status carries no tree digest")
    current = tree_digest(plugin_dir)
    if current is None:
        return unknown("could not digest the plugin to tell whether the record is current")
    if current != recorded:
        return unknown("recorded against different code; the plugin changed after the checks ran")

    failed = sorted(name for name, passed in checks.items() if passed is False)
    if failed:
        return StatusReport(
            FAILED,
            ", ".join(failed),
            present=True,
            checks=dict(checks),
            failed=failed,
            style_clean=payload.get("style_clean"),
            path=location,
        )

    if payload.get("style_clean") is not True:
        return unknown("every check passed but style_clean is not true")
    return StatusReport(
        CLEAN,
        "every check passed",
        present=True,
        checks=dict(checks),
        style_clean=True,
        path=location,
    )


def read_status(plugin_dir: Path) -> tuple[str, str]:
    """The recorded verdict for ``plugin_dir`` as ``(verdict, explanation)``.

    The narrow view of :func:`inspect_status`, for callers that only branch on
    the verdict.
    """
    report = inspect_status(plugin_dir)
    return report.verdict, report.detail


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


def tool_cmd(spec: str, *args: str) -> list[str]:
    """The argv for running one style tool through uv at a pinned version."""
    return ["uv", "run", "--no-project", "--with", spec, *args]


def tool_available(spec: str, tool: str, cwd: Path) -> bool:
    """Whether ``tool`` resolves and runs, checked before trusting its exit code.

    This is not a nicety. ``uv run`` passes the child's exit code through, but
    when uv cannot resolve ``--with`` itself -- an unsatisfiable pin, a cache
    miss with no network -- uv exits **1**, which is indistinguishable from the
    tool running and reporting diagnostics. Without this probe an outage would
    record ``style_clean: false`` against code nothing examined, and a false
    failure blocks a deploy where a skip does not.

    Measured against uv 0.12.5: an unresolvable package and ``--offline`` with a
    cold cache both exit 1, while a malformed version string exits 2.
    """
    probe = _run(tool_cmd(spec, tool, "--version"), cwd, _PROBE_TIMEOUT)
    return probe is not None and probe[0] == 0


def run_checks(
    plugin_dir: Path, ruff_config: str, mypy_config: str | None
) -> dict[str, str]:
    """Run the four style checks against ``plugin_dir`` and return per-check outcomes.

    ruff formatting and lint are auto-fixed in place, as is manifest formatting;
    what remains is reported. A check that cannot run is a skip.
    """
    outcomes: dict[str, str] = {}

    if not tool_available(PINNED_RUFF, "ruff", plugin_dir):
        print(
            f"style_status: could not resolve {PINNED_RUFF} through uv — "
            "skipping the ruff check",
            file=sys.stderr,
        )
        check = None
    else:
        formatted = _run(
            tool_cmd(
                PINNED_RUFF,
                "ruff", "format",
                "--config", ruff_config,
                *_RUFF_SCOPE_ARGS,
                ".",
            ),
            plugin_dir,
            _RUFF_TIMEOUT,
        )
        # Formatting has no outcome of its own -- it is applied, not reported --
        # but a formatter that could not run at all has to say so. Silence here
        # is indistinguishable from a clean format, and the two subcommands do
        # not accept the same flags, so an argument `ruff format` rejects stops
        # formatting happening while every other check still passes.
        if formatted is not None and formatted[0] not in TOOL_REPORTED_ON_CODE:
            print(
                f"style_status: ruff format could not run: {formatted[1]}",
                file=sys.stderr,
            )

        check = _run(
            tool_cmd(
                PINNED_RUFF,
                "ruff", "check", "--fix",
                "--config", ruff_config,
                *_RUFF_SCOPE_ARGS,
                "--output-format", "concise",
                ".",
            ),
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

    resolved_mypy_config = resolve_mypy_config(plugin_dir, mypy_config)
    if resolved_mypy_config is None:
        print(
            "style_status: no mypy config available, including the fallback at "
            f"{FALLBACK_MYPY_CONFIG} — skipping the mypy check",
            file=sys.stderr,
        )
        outcomes["mypy"] = "skip"
    elif not tool_available(BOUNDED_MYPY, "mypy", plugin_dir):
        print(
            f"style_status: could not resolve {BOUNDED_MYPY} through uv — "
            "skipping the mypy check",
            file=sys.stderr,
        )
        outcomes["mypy"] = "skip"
    else:
        mypy = _run(
            tool_cmd(
                BOUNDED_MYPY,
                "mypy",
                "--config-file", str(resolved_mypy_config),
                ".",
            ),
            plugin_dir,
            _MYPY_TIMEOUT,
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

    manifest = find_manifest(plugin_dir)
    if manifest is not None:
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
        "--check",
        action="store_true",
        help="read the recorded status back (exit 0 clean, 1 failed, 3 unknown)",
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
    parser.add_argument(
        "--json",
        action="store_true",
        help="with --check, print the full report as JSON (exit code unchanged)",
    )
    args = parser.parse_args(argv)

    if args.json and not args.check:
        print("style_status: --json applies to --check", file=sys.stderr)
        return 2

    plugin_dir = Path(args.plugin_dir).resolve()
    if not plugin_dir.is_dir():
        print(f"style_status: not a directory: {plugin_dir}", file=sys.stderr)
        return 2

    if args.check:
        report = inspect_status(plugin_dir)
        if args.json:
            print(json.dumps(report.as_dict(), sort_keys=True))
        else:
            print(f"{report.verdict}: {report.detail}")
        return report.exit_code

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

    # Digested after the checks, never before: ruff rewrites files as it fixes
    # them, so a digest taken first would describe a tree that no longer exists
    # by the time the record lands.
    payload = build_payload(outcomes, tree_digest(plugin_dir))
    try:
        dest = write_status(plugin_dir, payload)
    except OSError as exc:
        print(f"style_status: could not write status: {exc}", file=sys.stderr)
        return 2
    print(f"{json.dumps(payload)} -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
