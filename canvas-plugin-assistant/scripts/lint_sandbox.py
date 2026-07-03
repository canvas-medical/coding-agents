"""Lint Canvas plugin source for sandbox-rejected Python *constructs* before deploy.

Import/manifest/handler-load validation is delegated to `canvas validate` (run it
first — it performs the real RestrictedPython load against the runner's own
allowlist, so it can never drift). This script covers the complementary gap:
RestrictedPython constructs that `canvas validate`'s module-level load can't see
because they only fail when a *handler body* runs on the instance — e.g. a
`setattr()` inside `compute()` loads clean but raises at request time.

Every rule here is verified against the runner sandbox (see canvas-plugins
`canvas_cli/apps/plugin/test_plugin_lint.py`, which pins the same rules with
tripwire tests). Notably `@dataclass(frozen=True)` / `slots=True` are NOT flagged
— they load and run fine in the sandbox.

Usage:
    python3 lint_sandbox.py <plugin-dir>

`<plugin-dir>` must contain `CANVAS_MANIFEST.json` (the inner plugin folder).

Exit codes:
    0 — no violations
    1 — one or more violations found
    2 — usage / I/O error
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


class Violation:
    __slots__ = ("path", "lineno", "kind", "message")

    def __init__(self, path: Path, lineno: int, kind: str, message: str):
        self.path = path
        self.lineno = lineno
        self.kind = kind
        self.message = message

    def __str__(self) -> str:
        return f"  {self.path}:{self.lineno}  [{self.kind}]  {self.message}"


class SandboxLinter(ast.NodeVisitor):
    def __init__(self, file_path: Path, plugin_name: str):
        self.file_path = file_path
        self.plugin_name = plugin_name
        self.violations: list[Violation] = []

    # ── Structural import rules the runner rejects (not allowlist — delegated
    #    to `canvas validate`). These give faster, clearer feedback than a load
    #    traceback and don't drift.
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            module = alias.name
            # `import my_plugin.foo` triggers deep-attribute errors at use sites
            # (the sandbox rejects deep attribute access via dotted module
            # paths); nudge the author to `from my_plugin.foo import <name>`.
            if self.plugin_name and module.split(".")[0] == self.plugin_name and "." in module:
                self.violations.append(
                    Violation(
                        self.file_path,
                        node.lineno,
                        "import-style",
                        f"Use `from {module} import <name>` instead of `import {module}` "
                        "— the runner rejects deep attribute access via dotted module paths.",
                    )
                )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level and node.level > 0:
            self.violations.append(
                Violation(
                    self.file_path,
                    node.lineno,
                    "relative-import",
                    f"Relative import `from {'.' * node.level}{node.module or ''} import ...` "
                    "— Canvas requires absolute imports with the full plugin-namespace prefix "
                    f"({self.plugin_name}.…).",
                )
            )
            return
        for alias in node.names:
            if alias.name == "*":
                self.violations.append(
                    Violation(
                        self.file_path,
                        node.lineno,
                        "import-star",
                        f"`from {node.module or ''} import *` — wildcard imports are rejected "
                        "by the runner; list names explicitly.",
                    )
                )

    # ── Augmented assignment on subscripts / slices ──
    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if isinstance(node.target, ast.Subscript):
            self.violations.append(
                Violation(
                    self.file_path,
                    node.lineno,
                    "augmented-subscript",
                    "Augmented assignment on a dict item / list item / slice "
                    "(e.g. `d[k] += v`) is rejected by the RestrictedPython sandbox. "
                    "Rewrite as explicit reassignment: `d[k] = d[k] + v`.",
                )
            )
        self.generic_visit(node)

    # ── setattr / delattr / bytearray / 3-arg type() calls ──
    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        name = func.id if isinstance(func, ast.Name) else ""
        if name == "setattr":
            self.violations.append(
                Violation(
                    self.file_path,
                    node.lineno,
                    "setattr-blocked",
                    "`setattr()` is blocked by the sandbox. Use direct attribute "
                    "assignment (`obj.attr = value`) instead.",
                )
            )
        elif name == "delattr":
            self.violations.append(
                Violation(
                    self.file_path,
                    node.lineno,
                    "delattr-blocked",
                    "`delattr()` is blocked by the sandbox. Use `del obj.attr`.",
                )
            )
        elif name == "bytearray":
            self.violations.append(
                Violation(
                    self.file_path,
                    node.lineno,
                    "bytearray-blocked",
                    "`bytearray` is not available in the sandbox. Use `bytes` for binary data.",
                )
            )
        elif name == "type" and len(node.args) >= 3:
            # type(name, bases, dict) — dynamic class creation. type(x) is fine.
            self.violations.append(
                Violation(
                    self.file_path,
                    node.lineno,
                    "type-3arg-blocked",
                    "`type(name, bases, dict)` dynamic class creation is not available in "
                    "the sandbox. Declare the class normally with `class … :`.",
                )
            )
        self.generic_visit(node)


def _read_plugin_name(plugin_dir: Path) -> str | None:
    manifest = plugin_dir / "CANVAS_MANIFEST.json"
    if not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    name = data.get("name")
    return name if isinstance(name, str) and name else None


def lint(plugin_dir: Path) -> list[Violation]:
    plugin_name = _read_plugin_name(plugin_dir) or ""

    # Scope the scan to the inner snake_case plugin folder when we can identify
    # it. The plugin's actual source lives inside `<plugin_dir>/<plugin_name>/`;
    # everything outside (build caches, .venv, .uv, cookiecutter leftovers) is
    # never the user's code and was the biggest source of bogus violations.
    scan_root = plugin_dir
    if plugin_name:
        inner = plugin_dir / plugin_name
        if inner.is_dir():
            scan_root = inner

    # Directories whose .py files are never the plugin's own source.
    SKIP_DIRS = {
        "__pycache__", "tests", ".venv", ".cache", ".canvas",
        ".npm", ".git", "node_modules", "site-packages",
        ".pytest_cache", ".mypy_cache", ".uv", "build", "dist",
    }
    violations: list[Violation] = []
    for py_file in sorted(scan_root.rglob("*.py")):
        if set(py_file.parts) & SKIP_DIRS:
            continue
        if any(p.startswith(".") and p not in (".", "..") for p in py_file.parts[:-1]):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError as e:
            violations.append(Violation(py_file, e.lineno or 0, "syntax", f"SyntaxError: {e.msg}"))
            continue
        linter = SandboxLinter(py_file, plugin_name)
        linter.visit(tree)
        violations.extend(linter.violations)
    return violations


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: lint_sandbox.py <plugin-dir>", file=sys.stderr)
        return 2
    plugin_dir = Path(argv[1]).resolve()
    if not plugin_dir.is_dir():
        print(f"ERROR: {plugin_dir} is not a directory", file=sys.stderr)
        return 2
    if not (plugin_dir / "CANVAS_MANIFEST.json").is_file():
        # Try one level down — the container layout keeps the manifest inside
        # the inner snake_case folder.
        candidates = list(plugin_dir.glob("*/CANVAS_MANIFEST.json"))
        if len(candidates) == 1:
            plugin_dir = candidates[0].parent
        elif (plugin_dir.parent / "CANVAS_MANIFEST.json").is_file():
            plugin_dir = plugin_dir.parent
        else:
            print(
                f"ERROR: no CANVAS_MANIFEST.json found in {plugin_dir}, "
                "its immediate children, or its parent",
                file=sys.stderr,
            )
            return 2

    violations = lint(plugin_dir)
    if not violations:
        print(f"OK: no sandbox-construct violations found under {plugin_dir}")
        return 0

    by_kind: dict[str, list[Violation]] = {}
    for v in violations:
        by_kind.setdefault(v.kind, []).append(v)

    print(f"FAILED: {len(violations)} sandbox-construct violation(s) under {plugin_dir}\n", file=sys.stderr)
    for kind in sorted(by_kind):
        print(f"[{kind}] ({len(by_kind[kind])})", file=sys.stderr)
        for v in by_kind[kind]:
            print(str(v), file=sys.stderr)
        print(file=sys.stderr)
    print(
        "These constructs fail at runtime in the sandbox. Run `canvas validate` "
        "for import / manifest / handler-load errors.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
