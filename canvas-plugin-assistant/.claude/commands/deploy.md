# Deploy Plugin

Deploy the current plugin to a Canvas instance with log monitoring.

## Arguments

- `$1` (optional): Target instance name from `~/.canvas/credentials.ini`
  - If provided: verify it exists in credentials, then proceed to pre-deployment checks
  - If omitted: prompt user to select an environment

## Instructions

Use the **deploy-uat** agent to handle deployment and testing.

1. Verify the current directory contains a valid Canvas plugin (check for CANVAS_MANIFEST.json)

2. **Handle target instance argument:**
   - If `$1` is provided:
     - Check if `[$1]` section exists in `~/.canvas/credentials.ini`
     - If found: use `$1` as the target hostname and skip to step 4
     - If NOT found: list available instances from credentials.ini and ask user to choose or correct the name
   - If `$1` is not provided:
     - Ask which environment to deploy to (current behavior)

3. Ask which environment to deploy to (only if no valid `$1` was provided)

4. Run pre-deployment checks:
   - `uv run canvas validate-manifest .`
   - `uv run pytest` (if tests exist)

5. **Start log monitoring BEFORE install** (background task with `run_in_background: true`):
   - `unbuffer uv run canvas logs --host {hostname}`
   - This captures installation errors and runtime behavior

6. Deploy using `uv run canvas install`

7. For UAT:
   - Tell user logs are running, to test and say "check the logs" when ready
   - Use BashOutput to retrieve and analyze log entries on user request
   - Use KillShell when testing is complete

## Credentials

Deployment uses credentials from `~/.canvas/credentials.ini`. Instance names are the section headers (e.g., `[plugin-testing]` means the instance name is `plugin-testing`).

## Examples

- `/deploy` - Interactive deployment (asks which instance)
- `/deploy plugin-testing` - Deploy directly to plugin-testing
- `/deploy xpc` - Deploy directly to xpc instance
