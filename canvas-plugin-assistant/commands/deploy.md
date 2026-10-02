---
name: deploy
description: Deploy the current plugin to a Canvas instance with log monitoring.
---

# Deploy Plugin

Deploy the current plugin to a Canvas instance with log monitoring.

## Arguments

- `$1` (optional): Target instance name from `~/.canvas/credentials.ini`
  - If provided: verify it exists in credentials, then proceed to pre-deployment checks
  - If omitted: prompt the user to select an environment

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

### Step 1a: Canvas Code Style (advisory)

Read back the style status recorded by `/cpa:style`:

```bash
uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/style_status.py" --check
```

| Exit | Meaning | What to do |
|------|---------|------------|
| 0 | every check passed | Continue. |
| 1 | a check failed | Tell the user, offer to run `/cpa:style`, continue if they decline. |
| 3 | unknown (no record, unreadable, a check never ran, or the code changed after the checks did) | Same: offer `/cpa:style`, continue if they decline. |

**This is advisory — never refuse to deploy on style.** Deploying deliberately-dirty code for a quick UAT pass is legitimate, and the Studio deploy path treats style as a soft gate for the same reason. Print the verdict, offer the fix, respect the answer.

Why it is here at all: on the Studio path `canvas install` gates style deterministically, but this command is the CPA-native route to an instance and has no such gate. Without this nudge, unstyled code reaches UAT and only gets cleaned at wrap-up — so the tree a reviewer tested is not the tree that ships. `/cpa:wrap-up` remains the firm pre-delivery backstop.

### Step 2: Determine Target Hostname

Resolve the deployment target **before** delegating to the agent — the parent needs the hostname to start log monitoring.

1. Verify the current directory contains a valid Canvas plugin (check for CANVAS_MANIFEST.json)

2. **Handle target instance argument:**
   - If `$1` is provided:
     - Check if `[$1]` section exists in `~/.canvas/credentials.ini`
     - If found: use `$1` as the target hostname
     - If NOT found: list available instances from credentials.ini and ask the user to choose or correct the name
   - If `$1` is not provided:
     - Ask which environment to deploy to

Save the resolved hostname — you will pass it to the agent and use it for log monitoring.

### Step 3: Start Log Monitoring (BEFORE install)

**Start log monitoring in the parent context** so the background process survives the agent lifecycle.

Start log streaming as a **background task** (`run_in_background: true`):

```bash
unbuffer uv run canvas logs --host {hostname}
```

Save the `bash_id` — you will use it later to check logs. This captures installation errors and runtime behavior.

### Step 4: Deploy via Agent

Use the **deploy-uat** agent to handle version bump, validation, git commit/push, and install. Pass the resolved hostname so the agent does not need to ask again.

Tell the agent: "Deploy to {hostname}".

The agent will return when the install is complete.

### Step 5: Post-Deployment Log Check

After the agent returns and the install is complete, check the logs **in the parent context** (you own the background process).

1. Wait 5 seconds for logs to accumulate (`sleep 5`)
2. Use **BashOutput** with the saved bash_id to retrieve buffered output (this does NOT stop the background process)
3. Scan for errors (tracebacks, `ERROR`, `Exception`, `RestrictedPython error`, `ModuleNotFoundError`, install failures)
4. **If errors are found:**
   1. Stop log monitoring (KillShell)
   2. Show the errors to the user
   3. Analyze root cause and fix the code
   4. Re-deploy (repeat from step 3)
5. **If no errors:** leave log monitoring running and continue to UAT

### Step 6: UAT

Log monitoring is still running in the background (owned by this parent context).

- Tell user: "Plugin deployed successfully — no errors detected in logs. Log monitoring is running — go ahead and test in Canvas. Tell me to 'check the logs' when you want to see what happened."
- When the user says "check the logs": use BashOutput with the saved bash_id to retrieve and analyze log entries
- When testing is complete: use KillShell to stop the background log stream

After successful UAT, guide the user to the next step in the workflow.

## Credentials

Deployment uses credentials from `~/.canvas/credentials.ini`. Instance names are the section headers (e.g., `[plugin-testing]` means the instance name is `plugin-testing`).

## CPA Workflow

This command is **step 3** in the Canvas Plugin Assistant workflow:

```
/cpa:check-setup      →  Verify environment tools (uv, unbuffer)
/cpa:new-plugin       →  Create plugin from requirements
/cpa:style            →  Format + lint + type-check to the Canvas standard
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
