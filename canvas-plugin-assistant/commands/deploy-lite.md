---
name: deploy-lite
---

# Deploy Lite

Quick-deploy the current plugin to a Canvas instance — no version bump, no tests, no commit. Just install and monitor logs.

## Arguments

- `$1` (optional): Target instance name from `~/.canvas/credentials.ini`

## Instructions

**Execution standard:** Run Python scripts and Python-based tooling with `uv run ...` (for scripts, `uv run python <script>.py ...`). Do not invoke
bare `python` or `pip`.

### Step 1: Validate Environment

```bash
uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_cpa_environment.py" --require-plugin-dir
```

**If the script exits with an error:** STOP and show the user the error message. Do NOT proceed.

**If validation passes:** Continue with the steps below.

```bash
cd "$CPA_PLUGIN_DIR"
```

### Step 2: Determine Target Hostname

Resolve the deployment target.

1. Verify the current directory contains a valid Canvas plugin (check for CANVAS_MANIFEST.json)

2. **Handle target instance argument:**
    - If `$1` is provided:
        - Check if `[$1]` section exists in `~/.canvas/credentials.ini`
        - If found: use `$1` as the target hostname
        - If NOT found: list available instances from credentials.ini and use AskUserQuestion to let the user choose
    - If `$1` is not provided:
        - Read `~/.canvas/credentials.ini` and list all available section headers (instance names)
        - **If exactly one instance exists:** use it automatically without asking
        - **If multiple instances exist:** use AskUserQuestion to let the user choose which instance to deploy to. Present each instance as an option.

Save the resolved hostname for the install command and log monitoring.

### Step 3: Start Log Monitoring (BEFORE install)

Start log streaming as a **background task** (`run_in_background: true`):

```bash
unbuffer uv run canvas logs --host {hostname}
```

Save the `bash_id` — you will use it later to check logs.

### Step 4: Verify Cache Busting

If the plugin serves HTML content (has templates/ directory or uses `render_to_string`), verify that:

1. A module-level `_CACHE_BUST = str(int(datetime.now(timezone.utc).timestamp()))` exists in any file that renders HTML
2. `cache_bust` (or equivalent) is passed in the `render_to_string()` context
3. HTML templates use `?v={{ cache_bust }}` on external `<script src>` and `<link href>` URLs, and on plugin-served static asset URLs
4. Any `LaunchModalEffect(url=...)` calls include `?v={_CACHE_BUST}` in the URL

If cache busting is missing, add it before proceeding with deployment.

### Step 5: Install Plugin

Use the **`installer`** MCP tool (provided by the `canvas_cmd_line` MCP server) to install the plugin with its secrets:

- `plugin_name`: the inner folder name (snake_case)
- `instance`: the resolved hostname
- `cwd`: current working directory (the plugin container directory)

The MCP tool reads secret names from `CANVAS_MANIFEST.json`, retrieves their values from `~/.canvas/plugin-secrets/{hostname}.json`, and passes them
to the canvas install command. Secret values are never exposed to Claude Code.

If the response includes a warning about missing secrets, show the warning to the user. The install still proceeds — the warning is informational.

If the install command itself fails, show the error and stop.

### Step 6: Post-Deployment Log Check

After install completes, check the logs and report the result. Do NOT attempt to fix any errors.

1. Wait 5 seconds for logs to accumulate (`sleep 5`)
2. Use **BashOutput** with the saved bash_id to retrieve buffered output (this does NOT stop the background process)
3. Scan for errors (tracebacks, `ERROR`, `Exception`, `RestrictedPython error`, `ModuleNotFoundError`, install failures)
4. Stop log monitoring (KillShell) — always stop regardless of outcome
5. **If errors are found:** show the errors to the user. Do NOT offer to fix them or re-deploy. Just report the errors and stop.
6. **If no errors:** inform the user that the deployment completed successfully. Stop.

## Credentials

Deployment uses credentials from `~/.canvas/credentials.ini`. Instance names are the section headers (e.g., `[plugin-testing]` means the instance name
is `plugin-testing`).

## Examples

- `/cpa:deploy-lite` - Quick deploy (auto-selects instance if only one, otherwise asks)
- `/cpa:deploy-lite plugin-testing` - Quick deploy to plugin-testing instance
