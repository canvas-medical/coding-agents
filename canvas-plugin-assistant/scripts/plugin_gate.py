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
import shlex
import shutil
import stat
import subprocess
import sys
from os import environ
from pathlib import Path

MODE_VARIABLE = "CPA_PLUGIN_GATE"
MODES = ("off", "advise", "block")
MANIFEST = "CANVAS_MANIFEST.json"
INSTALLER_TOOL_SUFFIX = "canvas_cmd_line__installer"
PLUGIN_NAME = re.compile(r"[A-Za-z0-9_-]+")
# Shapes that were a live credential in every shipped file they appeared in across installed
# plugins, so a commit adding one is stopped in `block` mode. In a Markdown or reST doc they advise.
CERTAIN_SECRETS = {
    "an Anthropic API key": re.compile(r"\bsk-ant-(?:api|admin)\d{2}-[A-Za-z0-9_-]{80,}"),
    "a Slack token": re.compile(r"\bxox[bp]-\d+-\d+-[A-Za-z0-9-]{20,}"),
    "a Stripe live key": re.compile(r"\b[rs]k_live_[0-9A-Za-z]{24,}"),
    "a GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,})"),
    "an OpenAI key": re.compile(r"\bsk-proj-[A-Za-z0-9_-]{40,}"),
}
SECRET_ASSIGNMENT = re.compile(
    r"(?i)(?:api_?key|secret|token|passw(?:or)?d|private_key)\w*[\"']?\s*[:=]\s*[\"']([^\"'\s]{20,})[\"']"
)
# Private keys only advise: a plugin using mutual TLS can load its client key only from a file
# today, since `requests` takes a path and the sandbox cannot write one.
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----")
ENV_FILE = re.compile(r"(?:^|/)\.env(?:\.(?!example$|sample$|template$)[\w.-]+)?$")
KEY_FILE = re.compile(r"(?:^|/)[^/]+\.(?:pem|key|p12|pfx)$")
DOCS = re.compile(r"\.(?:md|rst)$")
HUNK_START = re.compile(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
# git's global options that take a separate value: `git -C dir commit` is still a commit.
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}
SHELL_SEPARATORS = {"&&", "||", ";", "|", "&", "(", ")"}
# `uv run` options that take a separate value: `uv run --directory work canvas deploy p`.
UV_RUN_VALUE_OPTIONS = {"--directory", "--project", "--with", "--python", "--package", "--env-file", "--extra", "--group"}
# `canvas install`/`deploy` options that take a separate value, so their value is not the plugin path.
CANVAS_VALUE_OPTIONS = {"--host", "--secret", "--variable", "--instance", "--ref", "--branch"}
# Words that run the command after them: `env git commit`, `if git commit; then`.
COMMAND_PREFIXES = {"env", "command", "time", "nohup", "exec", "sudo", "!", "{", "$", "then", "do", "else", "if", "while", "until"}
# How `canvas validate` prints a lint warning: "  ⚠ handlers/h.py:1  [code]  message".
WARNING_LINE = re.compile(r"^[ \t]*(⚠ \S+[ \t]+\[[\w-]+\].*)$", re.MULTILINE)
VALIDATE_TIMEOUT_SECONDS = 120
MAX_SCAN_BYTES = 1_000_000
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
    """A target the gate will not check: checking runs code, and the hook runs before the call
    is approved, so only plugins inside the session's working directory are."""

    reason = "it checks only plugins inside the session's working directory, so it stopped this call. Run it on a plugin from there."


class UnclearTarget(OutsideSession):
    """A command whose directory or plugin depends on shell expansion (`cd ~`, `$DIR`, `pushd`)."""

    reason = "it could not tell which plugin this command acts on, so it stopped it. Use a plain relative path, without `~`, variables, `cd -` or `pushd`."


def inside(path: Path, cwd: Path) -> Path:
    """``path`` resolved, or OutsideSession when it is not within ``cwd``."""
    resolved = path.resolve()
    if resolved != cwd and cwd not in resolved.parents:
        raise OutsideSession
    return resolved


def git(repo: Path, *args: str) -> str:
    """Run git in ``repo`` with no fsmonitor command and unquoted paths; its stdout ("" on failure)."""
    result = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "-c", "core.quotePath=false", "-C", str(repo), *args],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout if result.returncode == 0 else ""


def repo_root(repo: Path) -> Path | None:
    top = git(repo, "rev-parse", "--show-toplevel").strip()
    return Path(top) if top else None


def names(root: Path, *args: str) -> list[str]:
    """File names a git listing prints with `-z`, so no name is quoted or split on a newline."""
    return [name for name in git(root, *args, "-z").split("\0") if name]


def untracked_files(root: Path) -> list[str]:
    """New, non-ignored files, relative to ``root``. The hook runs before the command, so
    `git add new.py && git commit` commits a file that is still untracked here."""
    return names(root, "ls-files", "--others", "--exclude-standard")


def commit_plugins(repo: Path) -> list[Path]:
    """Every plugin holding a file the commit can record (staged, unstaged or new)."""
    root = repo_root(repo)
    if root is None:
        return []
    changed = set(untracked_files(root))
    for staged in (["--cached"], []):
        changed.update(names(root, "diff", "--name-only", "--no-renames", *staged))
    plugins: set[Path] = set()
    for name in changed:
        # Path("a/b/h.py").parents is a/b, a, "." — the folders inside the repo, nearest first.
        owner = next((root / folder for folder in Path(name).parents if (root / folder / MANIFEST).is_file()), None)
        if owner is not None:
            plugins.add(owner)
    return sorted(plugins)


def target_dirs(payload: dict, action: tuple[str, str | None]) -> list[Path]:
    """The plugins the gated call acts on (none when it acts on no plugin)."""
    cwd = Path(payload.get("cwd") or ".").resolve()
    tool_input = payload.get("tool_input") or {}
    kind, detail = action
    if payload.get("tool_name", "").endswith(INSTALLER_TOOL_SUFFIX):
        plugin_name = str(tool_input.get("plugin_name", ""))
        if not PLUGIN_NAME.fullmatch(plugin_name):
            raise OutsideSession
        start = inside(Path(tool_input.get("cwd") or cwd) / plugin_name, cwd)
    elif kind == "commit":
        repo = inside(cwd / detail, cwd) if detail else cwd
        return [inside(plugin, cwd) for plugin in commit_plugins(repo)]
    elif detail:
        # A named target is that plugin or the one directly inside it, never an enclosing plugin
        # the walk up from `find_plugin_dir` would reach.
        named = inside(cwd / detail, cwd)
        if (named / MANIFEST).is_file():
            return [named]
        children = [child for child in named.iterdir() if (child / MANIFEST).is_file()] if named.is_dir() else []
        return children if len(children) == 1 else []
    else:
        start = cwd
    plugin = find_plugin_dir(start)
    return [plugin] if plugin else []


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


def mask(value: str) -> str:
    """Enough of a value to find it, never enough to use it."""
    return f"`{value[:4]}…` ({len(value)} characters)"


def looks_random(value: str) -> bool:
    """A value with lower, upper and digit characters, not a CONSTANT_NAME or a URL."""
    return (
        any(c.islower() for c in value)
        and any(c.isupper() for c in value)
        and any(c.isdigit() for c in value)
        and not value.startswith(("http://", "https://"))
    )


def scan_diff(diff: str) -> tuple[list[str], list[str]]:
    """Credentials on the added lines of a `-U0` diff: (certain, possible), each `path:line: what`."""
    certain: list[str] = []
    possible: list[str] = []
    path, line_number, old_left, new_left = "", 0, 0, 0
    # git counts hunk lines by "\n" alone; splitlines() would also split on "\x0c", " " and others.
    for line in diff.split("\n"):
        if old_left == 0 and new_left == 0:
            # Between hunks only: inside one, an added line reading "++ b/x" shows as "+++ b/x".
            hunk = HUNK_START.match(line)
            if hunk:
                old_left = int(hunk.group(1) or 1)
                line_number = int(hunk.group(2))
                new_left = int(hunk.group(3) or 1)
            elif line.startswith("+++ "):
                path = line[6:] if line.startswith("+++ b/") else line[4:]
            continue
        if line.startswith("-"):
            old_left -= 1
            continue
        if line.startswith(" "):
            old_left, new_left, line_number = old_left - 1, new_left - 1, line_number + 1
            continue
        if not line.startswith("+"):
            continue
        new_left -= 1
        added, where = line[1:], f"{path}:{line_number}"
        line_number += 1
        has_private_key = bool(PRIVATE_KEY.search(added))
        if has_private_key:
            possible.append(f"{where}: a private key (fine only if it is a mutual-TLS client key)")
        for name, pattern in CERTAIN_SECRETS.items():
            match = pattern.search(added)
            if match:
                found = f"{where}: {name} {mask(match.group(0))}"
                (possible if DOCS.search(path) else certain).append(found)
                break
        else:
            if has_private_key:
                continue
            for match in SECRET_ASSIGNMENT.finditer(added):
                if looks_random(match.group(1)):
                    possible.append(f"{where}: a secret-like value ({len(match.group(1))} characters)")
    return certain, possible


def joined(base: str | None, path: str) -> str:
    """``path`` taken relative to ``base`` (an absolute ``path`` stands alone)."""
    return str(Path(base) / path) if base else path


def joined_all(base: str | None, paths: list[str]) -> str | None:
    """``paths`` applied in turn from ``base``, as chained `-C` or `cd` options are."""
    for path in paths:
        base = joined(base, path)
    return base


def upload_target(arguments: list[str]) -> str | None:
    """The plugin path a `canvas install`/`deploy` names: its first positional argument."""
    words = iter(arguments)
    for word in words:
        if word in CANVAS_VALUE_OPTIONS:
            next(words, None)
        elif not word.startswith("-"):
            return word
    return None


def is_literal(word: str) -> bool:
    """Whether ``word`` names a fixed path: the shell expands `~`, `$`, globs and `cd -` into
    paths the gate cannot see."""
    return not (word == "-" or word.startswith("~") or any(c in word for c in "$*?[{"))


def bash_actions(command: str) -> list[tuple[str, str | None]]:
    """Every gated action in the command: (`commit`, the directory git runs in) for each
    `git commit`, (`upload`, the named plugin path) for each `canvas install`/`deploy`.

    Reads each simple command, skipping `NAME=value` prefixes, wrapper words and git's global
    options, and follows `cd`, `git -C` and `uv run --directory`. Raises UnclearTarget when one of
    those depends on shell expansion. A git alias for commit is not resolved.
    """
    # shlex reads a newline as whitespace and a backtick as a word character, which would merge
    # two commands into one; both start a new command in the shell.
    lexer = shlex.shlex(command.replace("\n", ";").replace("`", ";"), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return [("commit", None)] if re.search(r"\bgit\b[\s\S]*\bcommit\b", command) else []
    actions: list[tuple[str, str | None]] = []
    words: list[str] = []
    # Where an earlier `cd` in the same command left the shell, relative to the session's cwd.
    # An expanded `cd` makes it unknown, which matters only if a gated action follows.
    base: str | None = None
    base_unknown = False
    for token in tokens + [";"]:
        if token not in SHELL_SEPARATORS:
            words.append(token)
            continue
        while words and (
            words[0] in COMMAND_PREFIXES
            or words[0] == ""
            or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", words[0])
        ):
            words.pop(0)
        if words[:1] in (["pushd"], ["popd"]) or (words[:1] == ["cd"] and len(words) != 2):
            base_unknown = True
        elif words[:1] == ["cd"]:
            base_unknown = base_unknown or not is_literal(words[1])
            base = joined(base, words[1])
        run_dirs: list[str] = []
        if words[:2] == ["uv", "run"]:
            words = words[2:]
            while words and words[0].startswith("-"):
                option = words.pop(0)
                if option in UV_RUN_VALUE_OPTIONS and words:
                    value = words.pop(0)
                    if option == "--directory":
                        run_dirs.append(value)
        program = Path(words[0]).name if words else ""
        if program == "canvas" and words[1:2] in (["install"], ["deploy"]):
            target = upload_target(words[2:])
            paths = run_dirs + ([target] if target else [])
            if base_unknown or not all(is_literal(path) for path in paths):
                raise UnclearTarget
            actions.append(("upload", joined_all(base, paths)))
        if program == "git":
            rest = iter(words[1:])
            git_dirs: list[str] = []
            for word in rest:
                if word in GIT_VALUE_OPTIONS:
                    value = next(rest, None)
                    if word == "-C" and value:
                        git_dirs.append(value)
                elif not word.startswith("-"):
                    if word == "commit":
                        if base_unknown or not all(is_literal(path) for path in git_dirs):
                            raise UnclearTarget
                        actions.append(("commit", joined_all(base, git_dirs)))
                    break
        words = []
    return actions


def scan_commit(repo: Path) -> tuple[list[str], list[str]]:
    """Credentials the commit in ``repo`` could record (certain, possible): its added lines and
    credential files.

    Unstaged changes are read too, since `git commit -a` and `git commit <path>` record them, and
    so are new untracked files, since `git add new.py && git commit` records them.
    """
    root = repo_root(repo)
    if root is None:
        return [], []
    diff = ("diff", "--no-color", "--no-ext-diff", "--no-textconv", "-U0")
    texts = [git(root, *diff, "--cached"), git(root, *diff)]
    certain: list[str] = []
    possible: list[str] = []
    untracked = untracked_files(root)
    for name in untracked:
        path = root / name
        # A symlink could reach outside the repository, and a huge file would stall the hook.
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode):
            continue
        if info.st_size > MAX_SCAN_BYTES:
            possible.append(f"{name}: a new file too large to scan ({info.st_size} bytes)")
            continue
        try:
            lines = path.read_text(encoding="utf-8").split("\n")
        except UnicodeDecodeError:
            continue
        # The whole new file, shaped as the one added hunk git would show for it.
        texts.append(f"+++ b/{name}\n@@ -0,0 +1,{len(lines)} @@\n" + "".join(f"+{line}\n" for line in lines))
    for text in texts:
        found_certain, found_possible = scan_diff(text)
        certain += found_certain
        possible += found_possible
    for path in names(root, "diff", "--cached", "--name-only", "--diff-filter=A") + untracked:
        if ENV_FILE.search(path):
            certain.append(f"{path}: an environment file")
        elif KEY_FILE.search(path):
            possible.append(f"{path}: a key file (fine only if it is a mutual-TLS client key)")
    return certain, possible


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
    payload = json.loads(stdin or "{}")
    cwd = Path(payload.get("cwd") or ".").resolve()
    plugin_dirs: list[Path] = []
    commit_repos: list[Path] = []
    try:
        if payload.get("tool_name") == "Bash":
            actions = bash_actions(str((payload.get("tool_input") or {}).get("command", "")))
        else:
            actions = [("upload", None)]
        for action in actions:
            touched = target_dirs(payload, action)
            plugin_dirs += [plugin for plugin in touched if plugin not in plugin_dirs]
            if action[0] == "commit" and touched:
                repo = inside(cwd / action[1], cwd) if action[1] else cwd
                commit_repos += [repo] if repo not in commit_repos else []
    except OutsideSession as refused:
        if mode == "block":
            print(f"CPA plugin gate: {refused.reason}", file=sys.stderr)
            return 2
        return 0
    if not plugin_dirs:
        return 0
    names = ", ".join(plugin.name for plugin in plugin_dirs)
    problems: list[str] = []
    advisories: list[str] = []
    certain: list[str] = []
    possible: list[str] = []
    for repo in commit_repos:
        found_certain, found_possible = scan_commit(repo)
        certain += found_certain
        possible += found_possible
    if commit_repos:
        if certain:
            problems.append(
                "the changes this commit can record add what look like live credentials. Remove "
                "each, store it as a manifest secret read with `self.secrets[...]`, and rotate it:\n"
                + "\n".join(certain)
            )
        if possible:
            advisories.append(
                f"CPA plugin gate, for {names}: the changes this commit can record may add "
                "credentials. Check each, and move any real one to a manifest secret:\n" + "\n".join(possible)
            )
    warning_parts: list[str] = []
    for plugin in plugin_dirs:
        problem, warnings = run_validate(plugin)
        if problem is not None:
            problems.append(f"{plugin.name}: {problem}" if len(plugin_dirs) > 1 else problem)
        if warnings:
            warning_parts.append(
                f"CPA plugin gate: `canvas validate` passed for {plugin.name} with warnings. They do not "
                "block; fix them unless the code is intended:\n" + "\n".join(warnings)
            )
    if problems and mode == "block":
        print(
            f"CPA plugin gate ({names}): " + "\n\n".join(problems) + "\n\nFix these, then try again.",
            file=sys.stderr,
        )
        return 2
    context_parts = [
        f"CPA plugin gate, advisory only ({MODE_VARIABLE}=advise), for {names}: {found}" for found in problems
    ]
    context_parts += warning_parts + advisories
    if not context_parts:
        return 0
    context = "\n\n".join(context_parts)
    print(
        json.dumps(
            {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": context}}
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.stdin.read()))
