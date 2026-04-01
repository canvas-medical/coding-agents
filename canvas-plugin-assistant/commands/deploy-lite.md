---
name: deploy-lite
---

# Deploy Lite

Quick-deploy the current plugin to a Canvas instance — no version bump, no tests, no commit. Just install and monitor logs.

## Arguments

- `$1` (optional): Target instance name from `~/.canvas/credentials.ini`

## Instructions

**Execution standard:** Run Python scripts and Python-based tooling with `uv run ...` (for scripts, `uv run python <script>.py ...`). Do not invoke bare `python` or `pip`.

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

Read the plugin name from `CANVAS_MANIFEST.json` and install directly — no version bump, no other validation, no git commit.

```bash
uv run canvas install {plugin_name} --host {hostname}
```

If the install command itself fails, show the error and stop.

### Step 6: Post-Deployment Log Check

After install completes, check the logs.

1. Wait 5 seconds for logs to accumulate (`sleep 5`)
2. Use **BashOutput** with the saved bash_id to retrieve buffered output (this does NOT stop the background process)
3. Scan for errors (tracebacks, `ERROR`, `Exception`, `RestrictedPython error`, `ModuleNotFoundError`, install failures)
4. **If errors are found:**
   1. Stop log monitoring (KillShell)
   2. Show the errors to the user
   3. Use AskUserQuestion to ask:
      ```json
      {
        "questions": [
          {
            "question": "Errors were detected in the deployment logs. What would you like to do?",
            "header": "Deployment errors",
            "options": [
              {"label": "Try to fix the issue", "description": "I'll analyze the errors and attempt a fix, then redeploy"},
              {"label": "Stop here", "description": "I'll look into this myself"}
            ],
            "multiSelect": false
          }
        ]
      }
      ```
   4. If the user chooses "Try to fix the issue": analyze root cause, fix the code, and re-deploy (repeat from Step 3)
   5. If the user chooses "Stop here": stop and let the user take over
5. **If no errors:** leave log monitoring running and continue to Step 7

### Step 7: User Testing

Log monitoring is still running in the background.

Use AskUserQuestion to tell the user:

```json
{
  "questions": [
    {
      "question": "Plugin deployed successfully — no errors detected in logs. Log monitoring is running. Please test the plugin in Canvas and let me know the result.",
      "header": "Test the plugin",
      "options": [
        {"label": "Everything works", "description": "The plugin is working as expected"},
        {"label": "There's a problem", "description": "Something isn't working right — I'll describe the issue"}
      ],
      "multiSelect": false
    }
  ]
}
```

- If **"Everything works"**: use KillShell to stop the background log stream. Report success.
- If **"There's a problem"**: use BashOutput with the saved bash_id to retrieve logs. Show the user any relevant log entries and ask them to describe the problem. Then work with the user to diagnose and fix the issue. If a fix is made, re-deploy (repeat from Step 3).
- If at any point the user says "check the logs": use BashOutput with the saved bash_id to retrieve and analyze log entries.

## Credentials

Deployment uses credentials from `~/.canvas/credentials.ini`. Instance names are the section headers (e.g., `[plugin-testing]` means the instance name is `plugin-testing`).

## Examples

- `/cpa:deploy-lite` - Quick deploy (auto-selects instance if only one, otherwise asks)
- `/cpa:deploy-lite plugin-testing` - Quick deploy to plugin-testing instance
