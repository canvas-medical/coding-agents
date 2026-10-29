---
name: check-setup
description: Verify the development environment has all required tools and configuration before starting plugin development.
---

# Check Setup

Verify the development environment has all required tools and configuration before starting plugin development.

## Instructions

### CRITICAL: Check `.claude/settings.local.json` FIRST

**This is a mandatory first check. If it fails, do not proceed with any other checks.**

```bash
ls -la .claude/settings.local.json
```

**If the file exists:**
- Report ".claude/settings.local.json exists ✓"
- Continue to the environment variable checks below

**If the file does NOT exist:**
- Report the error and STOP immediately:
  ```
  ERROR: .claude/settings.local.json not found in current directory.

  To set up the Canvas Plugin Assistant configuration:

  1. /exit
  2. Run: 
  mkdir -p .claude
  export CC_PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT}
  cp ${CC_PLUGIN_ROOT}/.claude/settings.json .claude/settings.local.json
  claude
  3. Then run /cpa:check-setup again

  Cannot proceed with setup checks until this file exists.
  ```
- **DO NOT run any of the checks below**
- **DO NOT continue**
- **STOP HERE**

---

## Environment Variable Checks

**Only run these checks if `.claude/settings.local.json` exists.**

### 2. Check CPA_RUNNING Environment Variable

```bash
echo $CPA_RUNNING
```

- **If set to "1"**: Report "CPA_RUNNING is set correctly" and continue
- **If not set or not "1"**: Report the issue:
  ```
  CPA_RUNNING must be set to "1" for Canvas Plugin Assistant to work.

  To start Claude with the correct environment:

  export CPA_RUNNING=1
  claude
  ```
  Then ask user to restart Claude with the correct environment.

### 3. Check CPA_WORKSPACE_DIR Environment Variable

```bash
echo $CPA_WORKSPACE_DIR
pwd
```

- **If CPA_WORKSPACE_DIR matches current directory**: Report "CPA_WORKSPACE_DIR is set correctly: [value]" and continue
- **If not set or doesn't match current directory**: Report the issue:
  ```
  CPA_WORKSPACE_DIR must be set to your current working directory.

  To start Claude with the correct environment, navigate to your workspace directory and run:

  export CPA_WORKSPACE_DIR=$(pwd)
  export CPA_RUNNING=1
  claude
  ```
  Then ask user to restart Claude with the correct environment.

### 4. Check CPA_PLUGIN_DIR Environment Variable

```bash
echo $CPA_PLUGIN_DIR
# List non-hidden subdirectories
find . -mindepth 1 -maxdepth 1 -type d -not -name '.*' | sed 's|^\./||'
```

**Validation logic:**

- **If CPA_PLUGIN_DIR is set**:
  - Check if it's a subdirectory of CPA_WORKSPACE_DIR: `[[ "$CPA_PLUGIN_DIR" == "$CPA_WORKSPACE_DIR"/* ]]`
  - Check if the directory exists: `[ -d "$CPA_PLUGIN_DIR" ]`
  - **If valid**: Report "CPA_PLUGIN_DIR is set to: [value]"
  - **If invalid**: Report error:
    ```
    CPA_PLUGIN_DIR is set but invalid.

    It must be a subdirectory of CPA_WORKSPACE_DIR and must exist.

    Current value: $CPA_PLUGIN_DIR
    Expected parent: $CPA_WORKSPACE_DIR

    To fix:
    - To work on a new plugin: unset CPA_PLUGIN_DIR
    - To work on an existing plugin: export CPA_PLUGIN_DIR=$CPA_WORKSPACE_DIR/[plugin-name]
    ```

- **If CPA_PLUGIN_DIR is not set or empty**:
  - List subdirectories (non-hidden)
  - **If no subdirectories exist**: Report "CPA_PLUGIN_DIR is empty (ready for new plugin)"
  - **If subdirectories exist**: Report "CPA_PLUGIN_DIR is empty. Existing plugins found: [list]. To work on a plugin, set: export CPA_PLUGIN_DIR=$CPA_WORKSPACE_DIR/[plugin-name]"

### 5. Check for `git`

```bash
which git
```

- **If found**: Report "git is installed" and continue
- **If not found**: Report the issue:
  ```
  git is required. Install it from https://git-scm.com/downloads
  ```
  Then ask user to install it and re-run `/cpa:check-setup` after.

### 6. Check for `uv`

```bash
which uv
```

- **If found**: Report "uv is installed" and continue
- **If not found**: Report the issue and provide the installation command:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
  Then ask user to run the command and re-run `/cpa:check-setup` after.

### 7. Check for `unbuffer`

```bash
which unbuffer
```

- **If found**: Report "unbuffer is installed" and continue
- **If not found**: Report the issue and provide the installation command:
  ```bash
  brew install expect
  ```
  (unbuffer is part of the expect package)
  Then ask user to run the command and re-run `/cpa:check-setup` after.

### 8. Check for Canvas CLI

```bash
uv run --with 'canvas>=0.262.0' canvas --version
```

`canvas` 0.262.0 or later is needed for `canvas deploy` (0.262.0 adds `--snapshot`, for a plugin inside a larger repository).

- **If works**: Report the Canvas CLI version
- **If fails**: Note that Canvas CLI will be installed when creating a plugin (it's a dependency)

### 9. Check Canvas Platform sign-in

```bash
uv run --with 'canvas>=0.262.0' python "${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py" whoami
uv run --with 'canvas>=0.262.0' python "${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py" publishers
```

- **If `whoami` passes**: Report the Platform host and email from its "Signed in to <url> as <email>" line, each publishing organization with its plugin prefix, and the instances you can deploy to
  - **If `publishers` exits non-zero while `whoami` passes (signed in, no publishing organization)**: This is a blocking issue for creating plugins, because `/cpa:new-plugin` stops without a publishing organization. Report it in the failures summary (step 12) and not as "Environment ready!", and tell the user an organization admin must grant the Plugin developer role. `/cpa:deploy` and `/cpa:deploy-lite` push plugin code on every deploy, so they need the same role
- **If it fails**: Show its message and ask the user to run this in their own terminal (it opens a browser to sign in), then re-run `/cpa:check-setup`. Do not run `canvas login` yourself:
  ```bash
  uv run --with 'canvas>=0.262.0' canvas login
  ```

### 10. Check legacy deploy credentials (optional)

```bash
grep '^\[' ~/.canvas/credentials.ini
uv run --with 'canvas>=0.262.0' python "${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py" instances
```

Read only the section headers, as above: the file holds client secrets and passwords.

Only `/cpa:deploy-legacy` uses this file, for plugins without an organization prefix: it deploys with `canvas install` and streams logs with `canvas logs`, both signed in with a section named after the instance. `/cpa:deploy` and `/cpa:deploy-lite` do not use it and do not stream logs.

- **If the file exists**: Report "legacy deploys available for: [section names other than `localhost`]".
- **If the file is missing or has no such section**: Report nothing; this is not a failure.
- In either case, note that `credentials.ini` support ends December 14, 2026, and `/cpa:deploy-legacy` is removed by then.

### 11. Check Claude Model

Identify which Claude model you are currently running (you know this from your system context).

- **If you are Opus**: Report "Model: Opus (Recommended)"
- **If you are Sonnet or Haiku**: Report your current model and recommend switching to Opus:
  ```
  Model: [your current model name]

  ⚠️  Recommendation: Switch to Opus for optimal plugin development.

  Opus provides the best reasoning and code quality for complex plugin development.
  To switch, use the /model command or update your .claude/settings.json file to set "model": "opus".
  ```

### 12. Report Results

If all checks pass, report:

```
✓ Environment ready!

  .claude/settings.local.json: exists
  CPA_RUNNING: 1
  CPA_WORKSPACE_DIR: [value]
  CPA_PLUGIN_DIR: [value or "empty (ready for new plugin)"]
  git: installed
  uv: installed
  unbuffer: installed
  Canvas CLI: [version or "will be installed with plugin"]
  Canvas Platform: signed in to [Platform host] as [email], publishing as [org slug(s)], deployable instances: [slugs or "none"]
  Legacy deploys: [instances with a credentials.ini section, or "not configured (optional)"]; removed by December 14, 2026
  model: [current model] [with recommendation if not opus]

You're ready to start building Canvas plugins.

Next step:
- To create a new plugin: Ensure CPA_PLUGIN_DIR is empty and you are signed in to Canvas Platform, then run /cpa:new-plugin
- To work on an existing plugin: Set CPA_PLUGIN_DIR to the plugin directory
```

If any checks fail, including a signed-in person with no publishing organization, summarize what needs to be fixed before proceeding and provide clear instructions. Do not print "Environment ready!" in that case.

## CPA Workflow

This command is the **first step** in the Canvas Plugin Assistant workflow:

```
/cpa:check-setup      →  Verify environment tools  ← YOU ARE HERE
/cpa:new-plugin       →  Create plugin from requirements
/cpa:deploy           →  Deploy to Canvas instance for UAT
/cpa:coverage         →  Check test coverage (aim for 90%)
/cpa:security-review  →  Comprehensive security audit
/cpa:database-performance-review  →  Database query optimization
/cpa:wrap-up          →  Final checklist before delivery
```

After a successful check of the setup, guide the user to the next step in the workflow.
