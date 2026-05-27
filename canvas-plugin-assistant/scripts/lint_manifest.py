"""Lint Canvas plugin manifest + Custom Data setup before deploy.

Companion to `lint_sandbox.py`. Catches the four most-common Custom
Data setup bugs from real-customer use, none of which the runner
reports cleanly:

  1. CustomModel subclasses outside `<plugin>/models/` (silently not
     loaded — tables never created).
  2. CustomModel subclasses present but no `custom_data` block in
     CANVAS_MANIFEST.json (tables never created).
  3. `.filter(id=…)` / `.get(id=…)` against the plugin's CustomModel
     classes — Custom Models use `dbid` as their primary key, not
     `id` (only core SDK models have `id`).
  4. Lazy ForeignKey string refs to the plugin's CustomModel classes —
     Canvas's model loader runs eagerly and silently drops string refs
     that don't resolve at import time.

Usage:
    python3 lint_manifest.py <plugin-dir>

`<plugin-dir>` should be either the outer container (where
CANVAS_MANIFEST.json lives) or the inner snake_case folder (where the
plugin's Python lives). The script searches both directions for the
manifest, like lint_sandbox.py.

Exit codes:
    0 — clean
    1 — violations found
    2 — usage / I/O error
"""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path


SKIP_DIRS = {
    "__pycache__", "tests", ".venv", ".cache", ".canvas",
    ".npm", ".git", "node_modules", "site-packages",
    ".pytest_cache", ".mypy_cache", ".uv", "build", "dist",
}


@dataclass
class Violation:
    path: Path
    line: int
    kind: str
    message: str

    def __str__(self) -> str:
        return f"  {self.path}:{self.line}  [{self.kind}]  {self.message}"


def _walk_py(root: Path):
    if not root.is_dir():
        return
    for py_file in sorted(root.rglob("*.py")):
        parts = set(py_file.parts)
        if parts & SKIP_DIRS:
            continue
        if any(p.startswith(".") and p not in (".", "..") for p in py_file.parts[:-1]):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue
        yield py_file, tree


def lint(outer_dir: Path, inner_dir: Path, manifest: dict) -> list[Violation]:
    violations: list[Violation] = []

    # Pass 1 — find CustomModel subclasses and check directory location.
    custom_model_class_names: set[str] = set()
    custom_model_definition_files: list[Path] = []
    for py_file, tree in _walk_py(inner_dir):
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            base_names: list[str] = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_names.append(base.id)
                elif isinstance(base, ast.Attribute):
                    base_names.append(base.attr)
            if "CustomModel" not in base_names:
                continue
            custom_model_class_names.add(node.name)
            custom_model_definition_files.append(py_file)
            rel = (
                py_file.relative_to(inner_dir)
                if py_file.is_relative_to(inner_dir)
                else py_file
            )
            if rel.parts[0] != "models":
                violations.append(Violation(
                    rel, node.lineno, "custom-model-wrong-dir",
                    f"`class {node.name}(CustomModel)` lives under "
                    f"`{rel.parts[0]}/` — Canvas only loads models from "
                    "`<plugin>/models/`. Move the file into "
                    "`<plugin>/models/` (alongside an `__init__.py`) or "
                    "the tables will silently never be created.",
                ))

    # Pass 2 — manifest must declare a `custom_data` block.
    if custom_model_class_names and not manifest.get("custom_data"):
        sample = custom_model_definition_files[0]
        rel_sample = (
            sample.relative_to(outer_dir)
            if sample.is_relative_to(outer_dir)
            else sample
        )
        first_class = sorted(custom_model_class_names)[0]
        plugin_name = manifest.get("name", "plugin")
        violations.append(Violation(
            Path("CANVAS_MANIFEST.json"), 0, "missing-custom-data-block",
            f"Plugin defines CustomModel subclass(es) "
            f"(e.g. `{first_class}` in `{rel_sample}`) but the manifest "
            "has no `custom_data` block — without it, no tables will be "
            "created and queries will fail at runtime. Add a top-level "
            "entry such as:\n"
            f'      "custom_data": {{"namespace": "your_org__{plugin_name}", '
            '"access": "read_write"}',
        ))

    # Pass 3 — `.filter(id=…)` / `.get(id=…)` against CustomModels.
    if custom_model_class_names:
        for py_file, tree in _walk_py(inner_dir):
            rel = (
                py_file.relative_to(inner_dir)
                if py_file.is_relative_to(inner_dir)
                else py_file
            )
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if not isinstance(node.func, ast.Attribute):
                    continue
                if node.func.attr not in ("filter", "get"):
                    continue
                receiver = node.func.value
                receiver_name = ""
                if (
                    isinstance(receiver, ast.Attribute)
                    and receiver.attr == "objects"
                    and isinstance(receiver.value, ast.Name)
                ):
                    receiver_name = receiver.value.id
                if receiver_name not in custom_model_class_names:
                    continue
                for kw in node.keywords:
                    if kw.arg == "id":
                        violations.append(Violation(
                            rel, node.lineno, "custom-model-id-vs-dbid",
                            f"`{receiver_name}.objects.{node.func.attr}"
                            "(id=…)` — CustomModels use `dbid` as their "
                            "primary key (only core SDK models have "
                            "`id`). Use `dbid=…` instead.",
                        ))
                        break

    # Pass 4 — lazy ForeignKey string refs to local CustomModels.
    if custom_model_class_names:
        for py_file, tree in _walk_py(inner_dir):
            rel = (
                py_file.relative_to(inner_dir)
                if py_file.is_relative_to(inner_dir)
                else py_file
            )
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                fn = node.func
                fn_name = ""
                if isinstance(fn, ast.Name):
                    fn_name = fn.id
                elif isinstance(fn, ast.Attribute):
                    fn_name = fn.attr
                if fn_name not in ("ForeignKey", "OneToOneField", "ManyToManyField"):
                    continue
                if not node.args:
                    continue
                first = node.args[0]
                if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
                    continue
                bare = first.value.split(".", 1)[-1]
                if bare not in custom_model_class_names:
                    continue
                violations.append(Violation(
                    rel, node.lineno, "lazy-fk-string-ref",
                    f"`{fn_name}(\"{first.value}\", …)` uses a lazy "
                    "string reference to a CustomModel defined in this "
                    "plugin. Canvas's plugin loader resolves models "
                    "eagerly; string refs to local classes can silently "
                    f"drop. Import the class directly: "
                    f"`{fn_name}({bare}, …)`.",
                ))

    return violations


def _resolve_dirs(start: Path) -> tuple[Path, Path, dict] | None:
    """Locate the outer (manifest) and inner (code) directories from a
    starting point that could be either one. Returns (outer, inner,
    manifest) or None if the manifest can't be found.
    """
    manifest_path: Path | None = None
    if (start / "CANVAS_MANIFEST.json").is_file():
        manifest_path = start / "CANVAS_MANIFEST.json"
    else:
        # Try one level down (start is the container, manifest in a child).
        candidates = [
            p for p in start.glob("*/CANVAS_MANIFEST.json")
            if not set(p.parts) & SKIP_DIRS
        ]
        if len(candidates) == 1:
            manifest_path = candidates[0]
        elif (start.parent / "CANVAS_MANIFEST.json").is_file():
            manifest_path = start.parent / "CANVAS_MANIFEST.json"
    if not manifest_path:
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(manifest, dict):
        return None
    outer = manifest_path.parent
    inner_name = manifest.get("name")
    inner = outer
    if isinstance(inner_name, str) and inner_name and (outer / inner_name).is_dir():
        inner = outer / inner_name
    return outer, inner, manifest


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: lint_manifest.py <plugin-dir>", file=sys.stderr)
        return 2
    start = Path(argv[1]).resolve()
    if not start.is_dir():
        print(f"ERROR: {start} is not a directory", file=sys.stderr)
        return 2
    resolved = _resolve_dirs(start)
    if resolved is None:
        print(
            f"ERROR: no readable CANVAS_MANIFEST.json found near {start}",
            file=sys.stderr,
        )
        return 2
    outer, inner, manifest = resolved
    violations = lint(outer, inner, manifest)
    if not violations:
        print(f"OK: no manifest/data-model violations under {outer}")
        return 0
    print(
        f"FAILED: {len(violations)} manifest/data-model violation(s) under {outer}\n",
        file=sys.stderr,
    )
    by_kind: dict[str, list[Violation]] = {}
    for v in violations:
        by_kind.setdefault(v.kind, []).append(v)
    for kind in sorted(by_kind):
        print(f"[{kind}] ({len(by_kind[kind])})", file=sys.stderr)
        for v in by_kind[kind]:
            print(str(v), file=sys.stderr)
        print(file=sys.stderr)
    print(
        "See the Custom Data section of CLAUDE.md (or "
        "sandbox-allowlist.md) for remediation details.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
