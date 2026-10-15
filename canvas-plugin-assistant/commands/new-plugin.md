---
name: new-plugin
description: Start the plugin brainstorming process to transform requirements into a concrete specification, then implement it. Also supports updating an existing plugin with version bumping.
---

# New Plugin

Start the plugin brainstorming process to transform requirements into a concrete specification, then implement it. Also supports updating an existing plugin with version bumping.

## Instructions

**Execution standard:** Run Python scripts and Python-based tooling with `uv run ...` (for scripts, `uv run python <script>.py ...`). Do not invoke bare `python` or `pip`.

### Step 1: Validate Environment

```bash
uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_cpa_environment.py" --plugin-dir-optional
```

**If the script exits with an error:** STOP and show the user the error message. Do NOT proceed.

**If validation passes:** The output will indicate whether this is a new plugin creation or continuing implementation.

### Step 2: Determine Workflow Phase

Check whether this is a new plugin creation or continuing implementation:

```bash
echo "CPA_PLUGIN_DIR: $CPA_PLUGIN_DIR"
```

**If CPA_PLUGIN_DIR is NOT set or empty:**
- This is a **new plugin creation**
- Continue to **Phase 1: Gather Requirements** below

**If CPA_PLUGIN_DIR IS set:**
- This is **continuing implementation** after scaffolding
- Change to the plugin directory and skip to **Phase 3: Implementation** below

```bash
cd "$CPA_PLUGIN_DIR"
echo "Continuing implementation for: $(basename "$CPA_PLUGIN_DIR")"
```

---

## Workflow Phases

This command handles three scenarios:

1. **New Plugin Creation** (CPA_PLUGIN_DIR not set):
   - Phase 1: Gather Requirements
   - Phase 2: Scaffold Plugin Structure
   - Then STOP and instruct user to set CPA_PLUGIN_DIR

2. **Continue Implementation** (CPA_PLUGIN_DIR is set, user chooses "Continue implementation"):
   - Skip directly to Phase 3: Implementation

3. **Update Existing Plugin** (CPA_PLUGIN_DIR is set, user chooses "Update existing plugin"):
   - Skip directly to Phase 3: Update Mode

---

Use the **plugin-brainstorm** agent for the full workflow from spec to deployment, or in **update mode** for modifying existing plugins.

### Phase 1: Gather Requirements

**Only run this phase if CPA_PLUGIN_DIR is NOT set (new plugin creation).**

#### Gate: Choose the publishing organization

Before gathering requirements, confirm the person can publish a plugin:

```bash
uv run --with 'canvas>=0.245.0' python "${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py" publishers
```

Each output line is `<slug> <plugin_prefix>__`.

- **Non-zero exit:** STOP and show the output. If signed out, ask the user to run `uv run --with 'canvas>=0.245.0' canvas login` in their own terminal (it opens a browser), then re-run `/cpa:new-plugin`; do NOT run `canvas login` yourself. If no organization can publish, tell the user an organization admin must grant them the Plugin developer role.
- **One line:** Use its slug as `org_slug`.
- **Several lines:** Ask which one publishes this plugin and use the chosen slug as `org_slug`:

```json
{
  "questions": [
    {
      "question": "Which organization will publish this plugin?",
      "header": "Organization",
      "options": [
        {"label": "acme (acme__)", "description": "Plugin prefix acme__"},
        {"label": "beta-clinic (beta__)", "description": "Plugin prefix beta__"}
      ],
      "multiSelect": false
    }
  ]
}
```

Build one option per line of script output, labeled `slug (prefix__)`.

#### Requirements steps

1. Invoke the canvas-sdk skill to have SDK documentation available
2. Ask the user to describe the problem they're trying to solve
3. Check native coverage with the canvas-platform skill to determine if the ask is fully, partially, or not at all covered by native Canvas functionality
4. Use AskUserQuestion to gather structured requirements, scoped to what isn't natively covered:
   - Who experiences the problem?
   - What should trigger the plugin?
   - What should the plugin create or do?
5. Map answers to Canvas SDK concepts (events, effects)
6. Write a `$CPA_WORKSPACE_DIR/.cpa-workflow-artifacts/plugin-spec.md` file with the specification
7. Wait for user approval before any implementation

If `$CPA_WORKSPACE_DIR/.cpa-workflow-artifacts/plugin-spec.md` already exists, ask if they want to:
- Start fresh (replace it)
- Continue refining the existing spec

### Phase 2: Scaffold Plugin (after user approves spec)

**Only run this phase if CPA_PLUGIN_DIR is NOT set (new plugin creation).**

**⚠️ CRITICAL: After the user approves the spec, you MUST run `canvas init` to create the plugin structure.**

#### Step 1: Generate Plugin Name

Based on the requirements and specification, invent a descriptive plugin name in kebab-case. Examples:
- `vitals-alert`
- `appointment-reminder`
- `lab-result-notifier`

The name should be:
- Descriptive of what the plugin does
- In kebab-case (lowercase with hyphens)
- 2-4 words maximum

#### Step 2: Use the publishing organization

Use the organization slug chosen at the start of Phase 1 as `org_slug`.

#### Step 3: Run canvas init

```bash
# Store the plugin name and organization
plugin_name="[generated-plugin-name]"
org_slug="[chosen-organization-slug]"

# Run canvas init from workspace directory
cd "$CPA_WORKSPACE_DIR"
echo "$plugin_name" | uv run --with 'canvas>=0.245.0' canvas init --org "$org_slug"
```

**Check the organization prefix:**

```bash
ls "$plugin_name"/*__*/CANVAS_MANIFEST.json
```

**If it finds no file:** STOP. The plugin was scaffolded without an organization prefix and was not registered, so it cannot be deployed. `canvas init` does this in two cases:

- **Signed out:** it scaffolds silently. Ask the user to run `uv run --with 'canvas>=0.245.0' canvas login` in their own terminal.
- **Signed in, but no organization lets them push plugin code:** it prints "scaffolded without a publisher prefix". Tell the user an organization admin must grant them the Plugin developer role.

Either way, remove the scaffolded folder (with `trash`) and re-run `/cpa:new-plugin` once that is fixed.

This creates:
```
$CPA_WORKSPACE_DIR/
└── {plugin_name}/                    # Kebab-case container directory, its own git repo
    ├── pyproject.toml
    ├── tests/
    └── {package}/                    # Inner package: {prefix}__{name_snake}
        ├── CANVAS_MANIFEST.json
        ├── README.md
        └── handlers/
```

`{package}` is the inner package folder, `<prefix>__<name>` with the name in snake_case. The command also registers the plugin on Canvas Platform and runs `git init` in the container with `origin` pointing at Canvas Platform.

#### Step 4: Verify Project Structure

```bash
cd "$CPA_WORKSPACE_DIR/$plugin_name"
uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/verify_plugin_structure.py"
test "$(git rev-parse --show-toplevel)" = "$CPA_WORKSPACE_DIR/$plugin_name" && echo "OK: container is its own git repository" || echo "ERROR: container is not the git repository root"
```

Expected structure:
```
$CPA_WORKSPACE_DIR/
├── .cpa-workflow-artifacts/          # Still in workspace (will be moved in Phase 3)
└── {plugin_name}/                    # Container (kebab-case)
    ├── pyproject.toml
    ├── tests/
    └── {package}/                    # Inner package: {prefix}__{name_snake}
        ├── CANVAS_MANIFEST.json
        ├── README.md
        └── handlers/
```

**If any checks fail:** Report errors to the user and investigate before proceeding.

#### Step 5: Configure Plugin Directory

**Ensure `.gitignore` includes `.claude`** (to keep Claude Code local settings out of the repo):

```bash
cd "$CPA_WORKSPACE_DIR/$plugin_name"

if [ ! -f .gitignore ]; then
  echo ".claude" > .gitignore
elif ! grep -q "^\.claude$" .gitignore; then
  echo ".claude" >> .gitignore
fi
```

The same way, add to `.gitignore`:
- `.cpa-workflow-artifacts`
- `.pytest_cache`
- `.__pycache__`
- `.coverage`
- any other files or directories that git should ignored 

`.cpa-workflow-artifacts` stays local: the reports and specs inside it are working notes for the current session, not deliverables, and committing them puts session detail into a customer's plugin repo.


**Replace `pyproject.toml` with the minimal version:**

```toml
# This pyproject.toml is only used for local development and testing.
# The Canvas plugin has its own packaging process that doesn't use this file.

[project]
name = "{plugin_name}"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = [
    "django>=4.2.0",
    "canvas[test-utils]>=0.245.0",
]

[dependency-groups]
dev = [
    "mypy>=1.19.0",
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-django>=4.7.0",
    "pytest-mock>=3.12.0",
]

[tool.coverage.run]
omit = ["tests/*"]
```

Add runtime dependencies (arrow, httpx, etc.) to `dependencies` only as needed during implementation.

**Add `mypy.ini` file to the container directory:**

```ini
[mypy]
explicit_package_bases = True

check_untyped_defs = True
disallow_incomplete_defs = True
disallow_untyped_calls = True
disallow_untyped_decorators = False
disallow_untyped_defs = True
error_summary = True

show_error_context = True
strict_equality = True
strict_optional = True

warn_no_return = True
warn_redundant_casts = True
warn_return_any = True
warn_unreachable = True
warn_unused_configs = True
warn_unused_ignores = True

follow_imports = silent
ignore_missing_imports = True
no_implicit_optional = True
pretty = False

python_version = 3.12
exclude = debug
```

#### Step 6: Commit the Scaffolded Plugin

```bash
cd "$CPA_WORKSPACE_DIR/$plugin_name"
git add -A .
git commit -m "initialize $plugin_name plugin scaffold

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**CRITICAL:** Always use `git add -A .` (with the trailing `.`) to scope changes to the current directory only.

The commit stays local. `/cpa:deploy` pushes it to Canvas Platform.

#### Step 7: Instruct User to Set CPA_PLUGIN_DIR

**STOP and tell the user:**

```
✓ Plugin scaffolded successfully!

The plugin directory is: $CPA_WORKSPACE_DIR/{plugin_name}

To continue with implementation, set CPA_PLUGIN_DIR and restart:

1. /exit
2. Run: export CPA_PLUGIN_DIR=$CPA_WORKSPACE_DIR/{plugin_name}
3. Run: claude
4. Run: /cpa:new-plugin (this will continue to Phase 3: Implementation)

DO NOT PROCEED until the user has set CPA_PLUGIN_DIR and restarted Claude.
```

---

### Phase 3: Implementation or Update (when CPA_PLUGIN_DIR is set)

**This phase runs when the user has already scaffolded the plugin and set CPA_PLUGIN_DIR.**

#### Step 1: Move .cpa-workflow-artifacts

If `.cpa-workflow-artifacts` exists in `CPA_WORKSPACE_DIR`, move it into the plugin directory:

```bash
if [ -d "$CPA_WORKSPACE_DIR/.cpa-workflow-artifacts" ]; then
  mv "$CPA_WORKSPACE_DIR/.cpa-workflow-artifacts" "$CPA_PLUGIN_DIR/"
  echo "Moved .cpa-workflow-artifacts into plugin directory"
fi
```

#### Step 2: Verify Plugin Directory

```bash
cd "$CPA_PLUGIN_DIR"
plugin_name=$(basename "$CPA_PLUGIN_DIR")
echo "Plugin directory: $plugin_name"
```

#### Step 3: Determine Mode

Check if the plugin has already been through the wrap-up process (i.e., is a completed plugin):

```bash
cd "$CPA_PLUGIN_DIR"
if [ -f ".cpa-workflow-artifacts/wrap-up-report.md" ]; then
  echo "PLUGIN_COMPLETED=true"
else
  echo "PLUGIN_COMPLETED=false"
fi
```

**If `PLUGIN_COMPLETED=true`:** The plugin has been through wrap-up — this is an **update**. Proceed directly to **Step 4b**.

**If `PLUGIN_COMPLETED=false`:** Ask the user what they want to do:

```json
{
  "questions": [
    {
      "question": "What would you like to do with this plugin?",
      "header": "Mode",
      "options": [
        {"label": "Continue implementation", "description": "Resume building the plugin from where you left off"},
        {"label": "Update existing plugin", "description": "Make changes to a completed plugin (includes version bump)"}
      ],
      "multiSelect": false
    }
  ]
}
```

**If "Continue implementation":** Proceed to **Step 4a** below.

**If "Update existing plugin":** Proceed to **Step 4b** below.

#### Step 4a: Continue Implementation

This is the standard resume flow. The **plugin-brainstorm** agent will handle implementation.

The agent will:
- Edit the generated protocol handler
- Create Application class if needed
- Generate icon for Applications (mandatory)
- Write tests following the testing skill guidelines
- Deploy for UAT

#### Step 4b: Update Existing Plugin

This flow handles modifying a completed plugin. The **plugin-brainstorm** agent will run in **update mode**.

Tell the agent to run in **update mode**. The agent will:
1. Read and summarize the existing plugin code and CANVAS_MANIFEST.json
2. Ask the user what changes they want
3. Implement the changes using the canvas-sdk skill for reference
4. Run security checks and tests
5. Bump the version in CANVAS_MANIFEST.json with user confirmation
6. Proceed to deployment

## Git Commit Style

Use concise declarative voice for all commit messages:
- "add handler for vitals monitoring"
- "implement authentication for webhook endpoint"
- "fix threshold comparison logic"
- "update tests for edge cases"

Do NOT use: "Added...", "Adding...", "I added...", or similar.

## CPA Workflow

This command is **step 2** in the Canvas Plugin Assistant workflow:

```
/cpa:check-setup      →  Verify environment tools (uv, unbuffer)
/cpa:new-plugin       →  Create plugin from requirements  ← YOU ARE HERE
/cpa:deploy           →  Deploy to Canvas instance for UAT
/cpa:coverage         →  Check test coverage (aim for 90%)
/cpa:security-review  →  Comprehensive security audit
/cpa:database-performance-review  →  Database query optimization
/cpa:wrap-up          →  Final checklist before delivery
```

After the user sets CPA_PLUGIN_DIR and restarts, guide them through implementation.
