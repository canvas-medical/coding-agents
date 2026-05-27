"""Lint Canvas plugin source for runtime-sandbox violations before deploy.

The Canvas plugin runner uses RestrictedPython plus an explicit allowlist of
modules and names. Code that violates these rules loads cleanly under normal
Python but fails at deploy time with messages like:

    ImportError: 'csv' is not an allowed import.
    AttributeError: "pkg.sub.NAME" is an invalid attribute name (not in ALLOWED_MODULES)
    RuntimeError: Code is invalid: ('Line N: Augmented assignment of object items and slices is not allowed.', ...)

This linter catches the same classes of violation statically by walking the
plugin's Python AST. Run it before `canvas install` to convert a slow round
trip ("install → wait → read traceback → fix → retry") into instant feedback.

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

# ── Sandbox allowlist (kept in sync with sandbox-allowlist.md and the runner) ──
#
# Per-module name allowlists. Importing the module is fine, but only these
# names are accepted from it. An empty set means the bare module name is
# allowed but no specific imports are pulled out of it.
STDLIB_ALLOWED: dict[str, set[str]] = {
    "__future__": {"annotations"},
    "abc": {"ABC", "abstractmethod"},
    "base64": {"b64decode", "b64encode"},
    "collections": {"Counter", "defaultdict"},
    "dataclasses": {
        "asdict", "astuple", "dataclass", "field", "Field", "fields",
        "InitVar", "replace",
    },
    "datetime": {"date", "datetime", "timedelta", "timezone", "UTC"},
    "decimal": {"Decimal"},
    "enum": {"Enum", "StrEnum"},
    "functools": {"reduce", "wraps"},
    "hashlib": {"sha256"},
    "hmac": {"compare_digest", "new"},
    "http": {"HTTPStatus"},
    "json": {"dumps", "loads"},
    "operator": {"and_"},
    "random": {"choices", "uniform", "randint"},
    "re": {
        "compile", "DOTALL", "findall", "IGNORECASE", "match", "search",
        "split", "sub",
    },
    "string": {"ascii_lowercase", "digits"},
    "time": {"time", "sleep"},
    "typing": {
        "Any", "Callable", "cast", "ClassVar", "Dict", "Final", "Iterable",
        "List", "Literal", "NamedTuple", "NotRequired", "Pattern", "Protocol",
        "Optional", "Sequence", "Tuple", "Type", "TypedDict", "TypeGuard",
        "Union",
    },
    "urllib": {"parse"},
    "urllib.parse": {"urlencode", "quote"},
    "uuid": {"uuid4", "UUID"},
    "zoneinfo": {"ZoneInfo"},
}

THIRD_PARTY_ALLOWED: dict[str, set[str]] = {
    "arrow": {"get", "now", "utcnow"},
    "dateutil": {"relativedelta"},
    "dateutil.relativedelta": {"relativedelta"},
    "defusedxml.ElementTree": {"fromstring"},
    "django.db": {"IntegrityError"},
    "django.db.models": {
        "Avg", "BigIntegerField", "Case", "CharField", "Count", "Exists",
        "IntegerField", "Max", "Min", "Model", "OuterRef", "Prefetch", "Q",
        "Subquery", "Sum", "Value", "When",
    },
    "django.db.models.expressions": {
        "Case", "Exists", "OuterRef", "Subquery", "Value", "When",
    },
    "django.db.models.query": {"Prefetch", "QuerySet"},
    "django.utils.functional": {"cached_property"},
    "jwt": {
        "decode", "encode", "ExpiredSignatureError", "InvalidTokenError",
        "PyJWKClient",
    },
    "pydantic": {
        "BaseModel", "conint", "ConfigDict", "constr", "Field", "RootModel",
        "ValidationError",
    },
    "rapidfuzz": {"fuzz", "process", "utils"},
    "requests": {
        "delete", "get", "patch", "post", "put", "request",
        "RequestException", "Response", "Session",
    },
}

# Module name prefixes that are always allowed (whole subtree).
ALWAYS_ALLOWED_PREFIXES = (
    "canvas_sdk",  # all Canvas SDK modules
)

# Top-level names that are allowed even though they're not stdlib/3rd-party.
ALWAYS_ALLOWED_TOP_LEVEL = {
    "logger",  # runner injects: `from logger import log`
}

# Hint table for common mistakes — keyed by the disallowed module.
HINTS: dict[str, str] = {
    "csv": "csv is blocked. Split lines yourself, or use json if you control the source.",
    "yaml": "PyYAML is blocked. Use json (storage format) or hard-code the config.",
    "os": "os is blocked. Most uses (paths, env, fs) aren't allowed in the sandbox anyway.",
    "subprocess": "subprocess is blocked. Plugins cannot spawn processes.",
    "socket": "socket is blocked. Use requests for HTTP, or canvas_sdk clients.",
    "pathlib": "pathlib is blocked. No filesystem access from inside the runner.",
    "pickle": "pickle is blocked. Use json.dumps/json.loads.",
    "httpx": "httpx is blocked. Use requests (allowed).",
    "urllib.request": "urllib.request is blocked. Use requests.",
    "urllib.error": "urllib.error is blocked. Catch requests.RequestException instead.",
    "importlib": "importlib is blocked. Only static imports are allowed.",
    "logging": "Python logging is blocked. Use `from logger import log` instead.",
    "tempfile": "tempfile is blocked. No filesystem access in the runner.",
    "asyncio": "asyncio is blocked. Plugin handlers are synchronous.",
}


def _is_module_allowed(module: str) -> tuple[bool, str | None]:
    """Return (allowed, hint) for a module name.

    `hint` is a remediation string when the module is not allowed and we have
    a known substitute; None otherwise.
    """
    if module in ALWAYS_ALLOWED_TOP_LEVEL:
        return True, None
    for prefix in ALWAYS_ALLOWED_PREFIXES:
        if module == prefix or module.startswith(prefix + "."):
            return True, None
    if module in STDLIB_ALLOWED or module in THIRD_PARTY_ALLOWED:
        return True, None
    return False, HINTS.get(module)


def _is_name_allowed(module: str, name: str) -> bool:
    """Is `from <module> import <name>` accepted by the runner?"""
    if module in ALWAYS_ALLOWED_TOP_LEVEL:
        return True
    for prefix in ALWAYS_ALLOWED_PREFIXES:
        if module == prefix or module.startswith(prefix + "."):
            return True
    table = STDLIB_ALLOWED if module in STDLIB_ALLOWED else (
        THIRD_PARTY_ALLOWED if module in THIRD_PARTY_ALLOWED else None
    )
    if table is None:
        return False
    allowed = table.get(module, set())
    # Empty set = bare module import is allowed but no name allowlist is
    # enforced (we treat any name as allowed in that case).
    if not allowed:
        return True
    return name in allowed


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

    # ── Imports ──
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            module = alias.name
            top = module.split(".")[0]
            # Plugin's own modules — must be prefixed with plugin_name.
            # `import my_plugin.x.y` is fine; `import x.y` (where x is a
            # sibling of the plugin folder) is the failure mode we see.
            if top == self.plugin_name:
                # Plain `import my_plugin.foo` triggers deep-attribute
                # errors at use sites; warn so the author uses `from ...`.
                self.violations.append(Violation(
                    self.file_path, node.lineno, "import-style",
                    f"Use `from {module} import <name>` instead of "
                    f"`import {module}` — the runner rejects deep "
                    f"attribute access via dotted module paths.",
                ))
                continue
            allowed, hint = _is_module_allowed(module)
            if not allowed:
                msg = f"`import {module}` — not on the Canvas sandbox allowlist."
                if hint:
                    msg += f" {hint}"
                else:
                    msg += (
                        " See sandbox-allowlist.md. If this is one of your "
                        "plugin's own modules, prefix it with the plugin "
                        "name (snake_case folder name)."
                    )
                self.violations.append(Violation(
                    self.file_path, node.lineno, "import", msg,
                ))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        # Relative imports are caught elsewhere (CLAUDE.md mandates absolute);
        # the sandbox rejects them too, but we surface that for clarity.
        if node.level and node.level > 0:
            self.violations.append(Violation(
                self.file_path, node.lineno, "relative-import",
                f"Relative import `from {'.' * node.level}{node.module or ''} "
                "import ...` — Canvas requires absolute imports with the "
                f"full plugin-namespace prefix ({self.plugin_name}.…).",
            ))
            return
        module = node.module or ""
        if not module:
            return
        top = module.split(".")[0]
        if top == self.plugin_name:
            # Internal plugin import, always fine.
            return
        allowed, hint = _is_module_allowed(module)
        if not allowed:
            msg = f"`from {module} import …` — `{module}` is not on the Canvas sandbox allowlist."
            if hint:
                msg += f" {hint}"
            else:
                msg += (
                    " See sandbox-allowlist.md. If this is one of your "
                    "plugin's own modules, prefix it with the plugin "
                    f"name (e.g. `from {self.plugin_name}.{module} import …`)."
                )
            self.violations.append(Violation(
                self.file_path, node.lineno, "import", msg,
            ))
            return
        # Module is allowed — check each imported name.
        for alias in node.names:
            name = alias.name
            if name == "*":
                self.violations.append(Violation(
                    self.file_path, node.lineno, "import-star",
                    f"`from {module} import *` — wildcard imports are "
                    "rejected by the runner; list names explicitly.",
                ))
                continue
            if not _is_name_allowed(module, name):
                self.violations.append(Violation(
                    self.file_path, node.lineno, "import-name",
                    f"`from {module} import {name}` — `{name}` is not on "
                    f"the allowlist for `{module}`. Check "
                    "sandbox-allowlist.md for which names are exposed.",
                ))

    # ── Augmented assignment on subscripts / slices ──
    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        target = node.target
        if isinstance(target, (ast.Subscript,)):
            # Subscripts AND slice targets (which are Subscript nodes with
            # a Slice value) both fail in RestrictedPython.
            self.violations.append(Violation(
                self.file_path, node.lineno, "augmented-subscript",
                "Augmented assignment on a dict item / list item / slice "
                "(e.g. `d[k] += v`) is rejected by the RestrictedPython "
                "sandbox. Rewrite as explicit reassignment: "
                "`d[k] = d[k] + v`.",
            ))
        # Recurse in case the RHS contains nested issues.
        self.generic_visit(node)

    # ── @dataclass(frozen=True) / @dataclass(slots=True) ──
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for deco in node.decorator_list:
            # @dataclass(frozen=True, ...) shape — ast.Call wrapping a name
            # that resolves to `dataclass`. Decorators can also be a bare
            # ast.Name (e.g. @dataclass) which is fine.
            if not isinstance(deco, ast.Call):
                continue
            func = deco.func
            deco_name = ""
            if isinstance(func, ast.Name):
                deco_name = func.id
            elif isinstance(func, ast.Attribute):
                deco_name = func.attr
            if deco_name != "dataclass":
                continue
            for kw in deco.keywords:
                if kw.arg in ("frozen", "slots") and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.violations.append(Violation(
                        self.file_path, deco.lineno, "dataclass-restricted",
                        f"`@dataclass({kw.arg}=True)` uses exec() internally "
                        "and is rejected by the sandbox. For immutable "
                        "records use `typing.NamedTuple`; for plain ones "
                        "drop the kwarg.",
                    ))
        self.generic_visit(node)

    # ── setattr / delattr / bytearray / 3-arg type() calls ──
    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        name = ""
        if isinstance(func, ast.Name):
            name = func.id
        if name == "setattr":
            self.violations.append(Violation(
                self.file_path, node.lineno, "setattr-blocked",
                "`setattr()` is blocked by the sandbox. Use direct attribute "
                "assignment (`obj.attr = value`) instead.",
            ))
        elif name == "delattr":
            self.violations.append(Violation(
                self.file_path, node.lineno, "delattr-blocked",
                "`delattr()` is blocked by the sandbox. Use `del obj.attr` "
                "or rethink the abstraction.",
            ))
        elif name == "bytearray":
            self.violations.append(Violation(
                self.file_path, node.lineno, "bytearray-blocked",
                "`bytearray` is blocked by the sandbox. Use `bytes` for "
                "binary data, or build a string and encode.",
            ))
        elif name == "type" and len(node.args) >= 3:
            # type(name, bases, dict) — dynamic class creation. type(x) for
            # type introspection is fine.
            self.violations.append(Violation(
                self.file_path, node.lineno, "type-3arg-blocked",
                "`type(name, bases, dict)` dynamic class creation is "
                "blocked. Declare the class normally with `class … :`.",
            ))
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
    plugin_name = _read_plugin_name(plugin_dir)
    if not plugin_name:
        # We can still scan for augmented-assignment and import-name
        # violations without the plugin name; we just can't validate
        # internal-import prefixes.
        plugin_name = ""

    # Scope the scan to the inner snake_case plugin folder when we can
    # identify it. The plugin's actual source lives inside
    # `<plugin_dir>/<plugin_name>/`; everything outside that (build
    # caches, test scratch, .venv, .uv, icon-gen artifacts, .cache/uv,
    # cookiecutter leftovers) is never the user's plugin code and was
    # the single biggest source of bogus "thousands of violations"
    # lint reports observed during real-customer use. Skip-list
    # below still applies for anything weird inside the inner folder.
    scan_root = plugin_dir
    if plugin_name:
        inner = plugin_dir / plugin_name
        if inner.is_dir():
            scan_root = inner

    # Directories whose .py files are never the plugin's own source —
    # don't scan them even if they live inside the inner folder. .cache
    # / .canvas / .npm get populated by cookiecutter, canvas-cli, and
    # Studio's runtime; .git is just git plumbing.
    SKIP_DIRS = {
        "__pycache__", "tests", ".venv", ".cache", ".canvas",
        ".npm", ".git", "node_modules", "site-packages",
        ".pytest_cache", ".mypy_cache", ".uv", "build", "dist",
    }
    violations: list[Violation] = []
    for py_file in sorted(scan_root.rglob("*.py")):
        parts = set(py_file.parts)
        if parts & SKIP_DIRS:
            continue
        # Also skip any path under a hidden directory anywhere in the
        # chain (`.local/`, `.foo-cache/`, etc.) — always build scratch.
        if any(p.startswith(".") and p not in (".", "..") for p in py_file.parts[:-1]):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError as e:
            violations.append(Violation(
                py_file, e.lineno or 0, "syntax",
                f"SyntaxError: {e.msg}",
            ))
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
        # Try one level down — invoked from the container layout where the
        # manifest lives inside the inner snake_case folder.
        candidates = list(plugin_dir.glob("*/CANVAS_MANIFEST.json"))
        if len(candidates) == 1:
            plugin_dir = candidates[0].parent
        # Try one level up — invoked from an inner folder whose parent
        # container holds the manifest (less common, but happens).
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
        print(f"OK: no sandbox violations found under {plugin_dir}")
        return 0

    # Group by kind for readability.
    by_kind: dict[str, list[Violation]] = {}
    for v in violations:
        by_kind.setdefault(v.kind, []).append(v)

    print(
        f"FAILED: {len(violations)} sandbox violation(s) under {plugin_dir}\n",
        file=sys.stderr,
    )
    for kind in sorted(by_kind):
        print(f"[{kind}] ({len(by_kind[kind])})", file=sys.stderr)
        for v in by_kind[kind]:
            print(str(v), file=sys.stderr)
        print(file=sys.stderr)
    print(
        "See sandbox-allowlist.md for the full set of allowed imports and "
        "the CLAUDE.md Sandbox section for the compact rules.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
