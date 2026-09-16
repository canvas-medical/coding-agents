---
name: style
description: Format, lint, and type-check the plugin to the Canvas code-style standard, fixing issues until it passes.
---

# Style Check

Bring the plugin up to the Canvas code-style standard and keep fixing until it
passes cleanly: ruff formatting and lint, mypy type-checking, and canonical
manifest formatting.

**This is a fix-and-repeat loop, not a report.** Run each check, edit the code to
resolve whatever it flags, and re-run until every check passes with nothing
remaining. Fix the issues yourself — do not stop to ask which ones to address, and
do not hand back a list of errors for someone else to resolve. The goal is
clean-on-exit, reached by iterating.

**Cap the loop at 4 rounds.** Attempt the full fix cycle (Steps 2–5) at most four
times. If issues still remain after the fourth round, stop iterating — do not keep
looping. Leave the code in its best state and record the outcome in the style-status
file (Step 6), so there is a durable record of which checks passed.

## Instructions

**Execution standard:** Run Python scripts and Python-based tooling with `uv run ...` (for scripts, `uv run python <script>.py ...`). Do not invoke bare `python` or `pip`.

ruff and mypy are resolved with `uv run --no-project --with <pinned spec>`, exactly as written below. Three things depend on that form, so do not shorten it:

- a plugin does not declare either tool, so a plain `uv run ruff` exits 2 with "Failed to spawn: ruff"
- `--no-project` is what stops uv creating a `.venv` inside the plugin directory
- `--with` pins the version, so the verdict comes from the ruleset rather than from whatever the machine has installed

Step 6 records the verdict using these same pinned versions, so iterating here and recording there cannot disagree.

### Step 1: Locate the plugin

```bash
uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_cpa_environment.py" \
  --require-plugin-dir --require-style-tools
cd "$CPA_PLUGIN_DIR"
```

If the environment validation fails, resolve the reported environment issue first, then continue. `--require-style-tools` confirms `uv` can actually resolve ruff and mypy before the loop starts; without it, an unresolvable toolchain surfaces much later as a verdict of `null` rather than as a setup problem.

The Canvas ruff ruleset lives in `${CLAUDE_PLUGIN_ROOT}/config/pyproject.toml` — a verbatim, CI-synced copy of `canvas-plugins/pyproject.toml`, the same rules that gate every other Canvas Python repo.

Every ruff command below passes a second `--config` carrying `extend-exclude=[".venv"]`. That ruleset sets `exclude`, which *replaces* ruff's built-in exclusions rather than adding to them, and `.venv` is one of the defaults it drops, so without this ruff walks into the plugin's own virtualenv and `--fix` rewrites installed dependency source.

Use this form rather than an exclude flag. `ruff format` does not accept `--extend-exclude` and exits 2 on it, which stops formatting happening while still leaving `.venv` alone, so it looks like it worked. `--exclude` is accepted by both subcommands and is wrong for both: it replaces the ruleset's list and un-excludes `canvas_generated/` and `canvas_cli/templates/`. The override belongs on the command line rather than in the config file, which a weekly workflow overwrites verbatim.

### Step 2: Format

```bash
uv run --no-project --with ruff==0.15.14 \
  ruff format --config "${CLAUDE_PLUGIN_ROOT}/config/pyproject.toml" \
       --config 'extend-exclude=[".venv"]' .
```

### Step 3: Lint, auto-fix, then fix the rest

```bash
uv run --no-project --with ruff==0.15.14 \
  ruff check --fix --config "${CLAUDE_PLUGIN_ROOT}/config/pyproject.toml" \
       --config 'extend-exclude=[".venv"]' .
```

ruff fixes what it can automatically. For every remaining violation — commonly a missing google-style docstring (`D` rules), an unused name, or a simplification (`SIM`) — edit the code to resolve it, then run this step again. Repeat until ruff reports nothing left.

### Step 4: Type-check

```bash
mypy_ini=mypy.ini
[ -f "$mypy_ini" ] || mypy_ini="${CLAUDE_PLUGIN_ROOT}/config/mypy.ini"
uv run --no-project --with "mypy>=1.19.0,<2" \
  mypy --config-file="$mypy_ini" .
```

The plugin's own `mypy.ini` wins; the fallback is the canonical Canvas ruleset, which is also what Step 6 records against. A plugin CPA did not scaffold usually has no `mypy.ini` at all, and passing a path that does not exist makes mypy exit 2 without reporting on the code.

For each mypy error, edit the code to fix it (add the missing annotation, correct the type, handle the `None` case), then re-run. Repeat until mypy passes with no errors.

### Step 5: Format the manifest

```bash
uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/format_manifest.py" CANVAS_MANIFEST.json
```

This applies the canonical key order and 2-space indent; it is safe to run repeatedly.

### Step 6: Record the style status

Record the outcome by running the status script, which re-runs every check and writes `.cpa-workflow-artifacts/style-status.json` from their actual exit codes:

```bash
uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/style_status.py" --run \
  --ruff-config "${CLAUDE_PLUGIN_ROOT}/config/pyproject.toml" \
  --mypy-config mypy.ini
```

Do not hand-write this file. The script is the only producer — Studio's deploy gate records through the same script — so the payload shape and the pass/fail rule cannot drift between the two. It prints the payload it wrote; read that line back to confirm the final state.

`style_clean` is `true` only when every check ran and passed, `false` when a check failed, and `null` when a required check could not run at all (so an unassessed build never reads back as a clean one). A skipped check is omitted from `checks` rather than recorded as passing. This is a durable, committed record of the build (`.cpa-workflow-artifacts/` is tracked in the repo), not a message to anyone.

If it reports `style_clean: false` after four rounds, leave the code in its best state and move on — the file records which check is outstanding.

## CPA Workflow

Run this before deploying or wrapping up:

```
/cpa:check-setup      →  Verify environment tools (uv, unbuffer)
/cpa:new-plugin       →  Create plugin from requirements
/cpa:style            →  Format + lint + type-check to the Canvas standard  ← YOU ARE HERE
/cpa:deploy           →  Deploy to Canvas instance for UAT
/cpa:coverage         →  Check test coverage (aim for 90%)
/cpa:security-review  →  Comprehensive security audit
/cpa:database-performance-review  →  Database query optimization
/cpa:wrap-up          →  Final checklist before delivery
```
