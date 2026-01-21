# New Plugin

Start the plugin brainstorming process to transform requirements into a concrete specification, then implement it.

## Instructions

### Step 1: Validate Environment

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_cpa_environment.py" --plugin-dir-optional
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
- Continue to **Phase 0: Create a Git Branch** below

**If CPA_PLUGIN_DIR IS set:**
- This is **continuing implementation** after scaffolding
- Change to the plugin directory and skip to **Phase 3: Implementation** below

```bash
cd "$CPA_PLUGIN_DIR"
echo "Continuing implementation for: $(basename "$CPA_PLUGIN_DIR")"
```

---

## Workflow Phases

This command handles two scenarios:

1. **New Plugin Creation** (CPA_PLUGIN_DIR not set):
   - Phase 0: Create Git Branch
   - Phase 1: Gather Requirements
   - Phase 2: Scaffold Plugin Structure
   - Then STOP and instruct user to set CPA_PLUGIN_DIR

2. **Continue Implementation** (CPA_PLUGIN_DIR is set):
   - Skip directly to Phase 3: Implementation

---

Use the **plugin-brainstorm** agent for the full workflow from spec to deployment.

### Phase 0: Create a Git Branch

**Only run this phase if CPA_PLUGIN_DIR is NOT set (new plugin creation).**

**Before anything else, create a new branch for this plugin to work.**

Generate a branch name using three random words in kebab-case. Examples:
- `mercury-purring-lion`
- `crystal-dancing-falcon`
- `amber-swift-turtle`

```bash
git checkout -b {branch_name}
git push -u origin {branch_name}
```

Tell the user the branch name you created.

### Phase 1: Gather Requirements

**Only run this phase if CPA_PLUGIN_DIR is NOT set (new plugin creation).**

1. Invoke the canvas-sdk skill to have SDK documentation available
2. Ask the user to describe the problem they're trying to solve
3. Use AskUserQuestion to gather structured requirements:
   - Who experiences the problem?
   - What should trigger the plugin?
   - What should the plugin create or do?
4. Map answers to Canvas SDK concepts (events, effects)
5. Write a `$CPA_WORKSPACE_DIR/.cpa-workflow-artifacts/plugin-spec.md` file with the specification
6. Wait for user approval before any implementation

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

#### Step 2: Run canvas init

```bash
# Store the plugin name
plugin_name="[generated-plugin-name]"

# Run canvas init from workspace directory
cd "$CPA_WORKSPACE_DIR"
echo "$plugin_name" | uv run canvas init
```

This creates:
```
$CPA_WORKSPACE_DIR/
└── {plugin_name}/                    # Kebab-case container directory
    ├── pyproject.toml
    ├── tests/
    └── {plugin_name_snake}/          # Snake_case inner directory
        ├── CANVAS_MANIFEST.json
        ├── README.md
        └── protocols/
```

#### Step 3: Verify Project Structure

```bash
cd "$CPA_WORKSPACE_DIR/$plugin_name"
plugin_name_snake=$(echo "$plugin_name" | tr '-' '_')

# Quick structure check
echo "Verifying structure..."
test -d "$plugin_name_snake" && echo "OK: Inner folder '$plugin_name_snake' exists" || echo "ERROR: Inner folder not found"
test -f "$plugin_name_snake/CANVAS_MANIFEST.json" && echo "OK: Manifest in correct place" || echo "ERROR: Manifest missing"
test -d "tests" && echo "OK: tests/ at container level" || echo "ERROR: tests/ not found"
```

Expected structure:
```
$CPA_WORKSPACE_DIR/
├── .cpa-workflow-artifacts/          # Still in workspace (will be moved in Phase 3)
└── {plugin_name}/                    # Container (kebab-case)
    ├── pyproject.toml
    ├── tests/
    └── {plugin_name_snake}/          # Inner (snake_case)
        ├── CANVAS_MANIFEST.json
        ├── README.md
        └── protocols/
```

**If any checks fail:** Report errors to the user and investigate before proceeding.

#### Step 4: Configure Plugin Directory

**Ensure `.gitignore` includes `.claude`** (to keep Claude Code local settings out of the repo):

```bash
cd "$CPA_WORKSPACE_DIR/$plugin_name"

if [ ! -f .gitignore ]; then
  echo ".claude" > .gitignore
elif ! grep -q "^\.claude$" .gitignore; then
  echo ".claude" >> .gitignore
fi
```

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
    "canvas[test-utils]",
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

#### Step 5: Commit the Scaffolded Plugin

```bash
cd "$CPA_WORKSPACE_DIR/$plugin_name"
git add -A .
git commit -m "initialize $plugin_name plugin scaffold

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push
```

**CRITICAL:** Always use `git add -A .` (with the trailing `.`) to scope changes to the current directory only.

#### Step 6: Instruct User to Set CPA_PLUGIN_DIR

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

### Phase 3: Implementation (when CPA_PLUGIN_DIR is set)

**This phase runs when the user has already scaffolded the plugin and set CPA_PLUGIN_DIR.**

#### Step 1: Move .cpa-workflow-artifacts

If `.cpa-workflow-artifacts` exists in `CPA_WORKSPACE_DIR`, move it into the plugin directory:

```bash
if [ -d "$CPA_WORKSPACE_DIR/.cpa-workflow-artifacts" ]; then
  mv "$CPA_WORKSPACE_DIR/.cpa-workflow-artifacts" "$CPA_PLUGIN_DIR/"
  echo "Moved .cpa-workflow-artifacts into plugin directory"
fi
```

#### Step 2: Continue Implementation

Verify we're in the plugin directory:

```bash
cd "$CPA_PLUGIN_DIR"
plugin_name=$(basename "$CPA_PLUGIN_DIR")
echo "Continuing implementation for: $plugin_name"
```

This phase is handled by the **plugin-brainstorm** agent.

The agent will:
- Edit the generated protocol handler
- Create Application class if needed
- Generate icon for Applications (mandatory)
- Write tests following the testing skill guidelines
- Deploy for UAT

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
