# Deploy Plugin

Deploy the current plugin to a Canvas instance with log monitoring.

## Arguments

- `$1` (optional): Target instance name from `~/.canvas/credentials.ini`
  - If provided: verify it exists in credentials, then proceed to pre-deployment checks
  - If omitted: prompt the user to select an environment

## Prerequisites

This command requires:
- `CPA_RUNNING` must be set to 1
- `CPA_WORKSPACE_DIR` must be set
- `CPA_PLUGIN_DIR` must be set to an existing plugin directory

## Instructions

### Step 1: Check CPA_RUNNING

```bash
echo $CPA_RUNNING
```

**If CPA_RUNNING is not set to "1":**
- STOP and tell the user:
  ```
  ERROR: CPA_RUNNING is not set to 1.

  Please /exit and run:
  export CPA_RUNNING=1 && claude

  Then run this command again.
  ```

### Step 2: Check CPA_WORKSPACE_DIR

```bash
echo $CPA_WORKSPACE_DIR
```

**If CPA_WORKSPACE_DIR is not set:**
- STOP and tell the user:
  ```
  ERROR: CPA_WORKSPACE_DIR is not set.

  Please /exit, navigate to your workspace directory, and run:
  export CPA_WORKSPACE_DIR=$(pwd) && claude

  Then run this command again.
  ```

### Step 3: Check CPA_PLUGIN_DIR

```bash
echo $CPA_PLUGIN_DIR
```

**If CPA_PLUGIN_DIR is not set or empty:**
- STOP and tell the user:
  ```
  ERROR: CPA_PLUGIN_DIR is not set.

  This command requires an existing plugin. To work on a plugin:

  1. /exit
  2. Run: export CPA_PLUGIN_DIR=$CPA_WORKSPACE_DIR/[plugin-name]
  3. Run: claude

  To see available plugins, list subdirectories in your workspace.
  ```

**If CPA_PLUGIN_DIR is set:**
- Verify it's a subdirectory of CPA_WORKSPACE_DIR and exists:

```bash
if [[ "$CPA_PLUGIN_DIR" != "$CPA_WORKSPACE_DIR"/* ]]; then
  echo "ERROR: CPA_PLUGIN_DIR must be a subdirectory of CPA_WORKSPACE_DIR"
  echo "  CPA_PLUGIN_DIR: $CPA_PLUGIN_DIR"
  echo "  CPA_WORKSPACE_DIR: $CPA_WORKSPACE_DIR"
  exit 1
elif [ ! -d "$CPA_PLUGIN_DIR" ]; then
  echo "ERROR: CPA_PLUGIN_DIR points to non-existent directory: $CPA_PLUGIN_DIR"
  exit 1
else
  cd "$CPA_PLUGIN_DIR"
  echo "Working in plugin: $(basename "$CPA_PLUGIN_DIR")"
fi
```

---

Use the **deploy-uat** agent to handle deployment and testing.

1. Verify the current directory contains a valid Canvas plugin (check for CANVAS_MANIFEST.json)

2. **Handle target instance argument:**
   - If `$1` is provided:
     - Check if `[$1]` section exists in `~/.canvas/credentials.ini`
     - If found: use `$1` as the target hostname and skip to step 4
     - If NOT found: list available instances from credentials.ini and ask the user to choose or correct the name
   - If `$1` is not provided:
     - Ask which environment to deploy to (current behavior)

3. Ask which environment to deploy to (only if no valid `$1` was provided)

4. **Version bump (if changes are detected):**
   - Check `git status --porcelain` for uncommitted changes
   - Ask the user: Patch (bug fix), Minor (new feature), or Major (breaking change)?
   - Read current `plugin_version` from `CANVAS_MANIFEST.json`
   - Bump version: Patch increments Z, Minor increments Y and resets Z, Major increments X and resets Y,Z
   - Update `CANVAS_MANIFEST.json` with a new version
   - Report: "Bumped version: X.Y.Z → X.Y.Z+1"

5. Run pre-deployment validation:
   - `uv run canvas validate-manifest .`
   - `uv run pytest` (if tests exist)
   - `uv run mypy --config-file=mypy.ini .`

6. **Start log monitoring BEFORE install** (background task with `run_in_background: true`):
   - `unbuffer uv run canvas logs --host {hostname}`
   - This captures installation errors and runtime behavior

7. Deploy using `uv run canvas install`

8. For UAT:
   - Tell user logs are running to test and say "check the logs" when ready
   - Use BashOutput to retrieve and analyze log entries on a user request
   - Use KillShell when testing is complete

## Credentials

Deployment uses credentials from `~/.canvas/credentials.ini`. Instance names are the section headers (e.g., `[plugin-testing]` means the instance name is `plugin-testing`).

## CPA Workflow

This command is **step 3** in the Canvas Plugin Assistant workflow:

```
/cpa:check-setup      →  Verify environment tools (uv, unbuffer)
/cpa:new-plugin       →  Create plugin from requirements
/cpa:deploy           →  Deploy to Canvas instance for UAT  ← YOU ARE HERE
/cpa:coverage         →  Check test coverage (aim for 90%)
/cpa:security-review  →  Comprehensive security audit
/cpa:database-performance-review  →  Database query optimization
/cpa:wrap-up          →  Final checklist before delivery
```

After successful UAT, guide the user to the next step in the workflow.

## Examples

- `/cpa:deploy` - Interactive deployment (asks which instance)
- `/cpa:deploy plugin-testing` - Deploy directly to plugin-testing instance
- `/cpa:deploy xpc` - Deploy directly to xpc instance
