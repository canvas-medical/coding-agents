---
name: deploy
description: Deploy the current plugin to a Canvas Platform instance.
---

# Deploy Plugin

Deploy the current plugin to a Canvas Platform instance.

## Arguments

- `$1` (optional): Canvas Platform instance slug (e.g. `acme-staging`)
  - If provided: verify it is one of the instances you can deploy to, then proceed to pre-deployment checks
  - If omitted: use the only deployable instance, or ask the user to choose when there are several

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

### Step 2: Determine Target Instance

Resolve the deployment target **before** delegating to the agent, so the agent does not need to ask.

1. Locate the inner package and read the plugin name:

   ```bash
   PACKAGE_DIR=$(dirname */CANVAS_MANIFEST.json)
   uv run python -c "import json,sys; print(json.load(open(sys.argv[1]))['name'])" "$PACKAGE_DIR/CANVAS_MANIFEST.json"
   ```

   If there is no `*/CANVAS_MANIFEST.json`, STOP: this directory is not a plugin container. The printed manifest `name` is the plugin name.

2. **Repository check.** Canvas Platform deploys plugins named `<prefix>__<package>` that are committed to a git repository. Run `git -C "$CPA_PLUGIN_DIR" rev-parse --show-toplevel`:
   - **Prints `$CPA_PLUGIN_DIR`:** the plugin is its own repository, the `canvas init` layout. `canvas deploy` commits and pushes that repository.
   - **Prints another path:** the plugin sits inside a larger repository, such as a monorepo. Tell the user it deploys as a snapshot: the `deployer` tool passes `--snapshot`, which pushes the package folder as committed at HEAD and leaves that repository's remotes and config alone, and refuses uncommitted changes in the package rather than committing them (canvas-plugins `canvas_cli/apps/platform/git.py:300-329` at 0.262.0). Commits for it are made in that repository, scoped to the package folder.
   - **Fails (not in a git repository):** the plugin is a legacy plugin.

   The plugin is also a legacy plugin when the manifest `name` has no `<prefix>__` part (no `__`). For a legacy plugin, show this guidance and STOP (deploy nothing):

   > This plugin cannot be deployed to Canvas Platform as it is. Either:
   > - Rename the package folder, the manifest `name`, and every import to `<prefix>__<package>` (the prefix is listed by the `whoami` command below), and commit it to a git repository: run `git init` in the plugin container directory, or keep it inside an existing repository; or
   > - Create a fresh plugin with `canvas init` and move the code into it; or
   > - Deploy it as it is with `/cpa:deploy-legacy`, which uses `canvas install` and `~/.canvas/credentials.ini` and works only until December 14, 2026.

   To list the prefixes, run `uv run --with 'canvas>=0.262.0' python "${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py" whoami`.

3. **Canvas CLI version.** `uv run canvas --version` must be 0.262.0 or newer. If it is older, run `uv add 'canvas[test-utils]>=0.262.0'` in the container, then continue.

4. **List the deployable instances.** From `$CPA_PLUGIN_DIR`:

   ```bash
   uv run --with 'canvas>=0.262.0' python "${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py" instances
   ```

   The script prints one instance slug per line. **If it exits non-zero** (for example `Not signed in to Canvas Platform ...`): show its output and STOP. When it reports not signed in, tell the user to run `uv run --with 'canvas>=0.262.0' canvas login` in their own terminal (it opens a browser) and then run this command again. If the user does not sign in, the command stops here.

5. **Handle the target instance argument:**
   - If `$1` is provided and listed: use `$1` as the target instance
   - If `$1` is provided but not listed: use AskUserQuestion with the listed slugs as options so the user can choose or correct the name
   - If `$1` is not provided:
     - **If exactly one instance is listed:** use it automatically without asking
     - **If several are listed:** use AskUserQuestion with one option per slug:

```json
{
  "questions": [
    {
      "question": "Which Canvas instance should I deploy to?",
      "header": "Instance",
      "options": [
        {"label": "<instance-1>", "description": "Deployable Canvas Platform instance"},
        {"label": "<instance-2>", "description": "Deployable Canvas Platform instance"},
        {"label": "...", "description": "One option per listed slug"}
      ],
      "multiSelect": false
    }
  ]
}
```

Save the resolved instance slug and the plugin name (the inner package folder). You will pass them to the agent.

### Step 3: Deploy via Agent

Use the **deploy-uat** agent to handle version bump, validation, local git commit, and deploy. Pass the resolved instance slug so the agent does not need to ask again.

Tell the agent: "Deploy to {instance}", and, when the repository check found a larger repository, "The plugin is inside the larger repository at {toplevel}, so it deploys as a snapshot".

The agent returns when the deploy is complete, or when it stopped: uncommitted changes declined, deploy failed, a snapshot refused, or a custom data consent request or a snapshot confirmation was denied or left unanswered. The agent owns the consent hand-off (see its Step 4). Continue to Step 4 only when the agent reports the deploy complete. If the agent reports a stop, relay its report to the user and end the command.

### Step 4: UAT

This command does not read Canvas logs: `canvas logs` signs in with `~/.canvas/credentials.ini`, not with the Canvas Platform sign-in, so it cannot confirm that the plugin loaded or ran.

- Tell user: "Plugin deployed to {instance}. I can't read Canvas logs for Canvas Platform deploys, so I can't confirm it loaded: go ahead and test in Canvas, and tell me what you see."
- When the user reports a problem: work from what they describe and the plugin's tests, fix the code, and deploy again with this command.

After successful UAT, guide the user to the next step in the workflow.

## Sign-in

`canvas deploy` acts as the person signed in with `canvas login` (or `CANVAS_PLATFORM_TOKEN`). This command does not use `~/.canvas/credentials.ini`. Plugin variable values live in `~/.canvas/plugin-secrets/<instance slug>.json`, keyed by the manifest name.

## CPA Workflow

This command is **step 3** in the Canvas Plugin Assistant workflow:

```
/cpa:check-setup      →  Verify environment tools and Canvas Platform sign-in
/cpa:new-plugin       →  Create plugin from requirements
/cpa:deploy           →  Deploy to Canvas instance for UAT  ← YOU ARE HERE
/cpa:coverage         →  Check test coverage (aim for 90%)
/cpa:security-review  →  Comprehensive security audit
/cpa:database-performance-review  →  Database query optimization
/cpa:wrap-up          →  Final checklist before delivery
```

After successful UAT, guide the user to the next step in the workflow.

## Examples

- `/cpa:deploy` - Interactive deployment (uses the only deployable instance, otherwise asks which)
- `/cpa:deploy acme-staging` - Deploy directly to the acme-staging instance
- `/cpa:deploy acme-prod` - Deploy directly to the acme-prod instance
