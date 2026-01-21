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
  cp $${CC_PLUGIN_ROOT}/.claude/settings.json .claude/settings.local.json
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
ls -d */ 2>/dev/null | grep -v '^\.' | sed 's|/$||'
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

### 5. Check Git Repository

```bash
git rev-parse --is-inside-work-tree
```

- **If returns "true"**: Report "Current directory is in a git repository" and continue
- **If fails**: Report the issue:
  ```
  The current directory must be inside a git repository.

  If this is a new workspace, initialize git:

  git init

  If you need to work in an existing repository, navigate to it first, then restart Claude:

  cd /path/to/your/repo
  export CPA_RUNNING=1 
  export CPA_WORKSPACE_DIR=$(pwd)
  claude
  ```
  Then ask user to initialize git or navigate to the correct directory.

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
uv run canvas --version
```

- **If works**: Report the Canvas CLI version
- **If fails**: Note that Canvas CLI will be installed when creating a plugin (it's a dependency)

### 9. Check Claude Model

Identify which Claude model you are currently running (you know this from your system context).

- **If you are Opus**: Report "Model: Opus (Recommended)"
- **If you are Sonnet or Haiku**: Report your current model and recommend switching to Opus:
  ```
  Model: [your current model name]

  ⚠️  Recommendation: Switch to Opus for optimal plugin development.

  Opus provides the best reasoning and code quality for complex plugin development.
  To switch, use the /model command or update your .claude/settings.json file to set "model": "opus".
  ```

### 10. Report Results

If all checks pass, report:

```
✓ Environment ready!

  .claude/settings.local.json: exists
  CPA_RUNNING: 1
  CPA_WORKSPACE_DIR: [value]
  CPA_PLUGIN_DIR: [value or "empty (ready for new plugin)"]
  Git repository: ✓
  uv: installed
  unbuffer: installed
  Canvas CLI: [version or "will be installed with plugin"]
  model: [current model] [with recommendation if not opus]

You're ready to start building Canvas plugins.

Next step:
- To create a new plugin: Ensure CPA_PLUGIN_DIR is empty, then run /cpa:new-plugin
- To work on an existing plugin: Set CPA_PLUGIN_DIR to the plugin directory
```

If any checks fail, summarize what needs to be fixed before proceeding and provide clear instructions.

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
