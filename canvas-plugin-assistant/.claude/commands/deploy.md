# Deploy Plugin

Deploy the current plugin to a Canvas instance with log monitoring.

## Instructions

Use the **deploy-uat** agent to handle deployment and testing.

1. Verify the current directory contains a valid Canvas plugin (check for CANVAS_MANIFEST.json)
2. Run pre-deployment checks:
   - `uv run canvas validate-manifest .`
   - `uv run pytest` (if tests exist)
3. Ask which environment to deploy to
4. **Start log monitoring BEFORE install** (background task with `run_in_background: true`):
   - `unbuffered uv run canvas logs --host {hostname}`
   - This captures installation errors and runtime behavior
5. Deploy using `uv run canvas install`
6. For UAT:
   - Tell user logs are running, to test and say "check the logs" when ready
   - Use BashOutput to retrieve and analyze log entries on user request
   - Use KillShell when testing is complete

## Credentials

Deployment uses credentials from `~/.canvas/credentials.ini`. The instance section needs `client_id` and `client_secret` for the Canvas CLI.

## Arguments

- `/deploy` - Interactive deployment (asks which instance)
- `/deploy plugin-testing` - Deploy directly to plugin-testing
- `/deploy acme-health` - Deploy directly to specified instance
