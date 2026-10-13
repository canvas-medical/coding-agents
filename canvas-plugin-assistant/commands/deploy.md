---
name: deploy
description: Deploy the current plugin to a Canvas Platform instance, with log monitoring where the person's role on the instance allows it.
---

# Deploy Plugin

Deploy the current plugin to a Canvas Platform instance, with log monitoring when the person can read plugin logs on the instance.

## Arguments

- `$1` (optional): Canvas Platform instance slug (e.g. `acme-staging`)
  - If provided: verify it is one of the test instances you can deploy to, then proceed to pre-deployment checks
  - If omitted: use the only deployable test instance, or ask the user to choose when there are several

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

Resolve the deployment target **before** delegating to the agent, because the parent needs the instance to start log monitoring.

1. Locate the inner package and read the plugin name:

   ```bash
   PACKAGE_DIR=$(dirname */CANVAS_MANIFEST.json)
   uv run python -c "import json,sys; print(json.load(open(sys.argv[1]))['name'])" "$PACKAGE_DIR/CANVAS_MANIFEST.json"
   ```

   If there is no `*/CANVAS_MANIFEST.json`, STOP: this directory is not a plugin container. The printed manifest `name` is the plugin name.

2. **Repository check.** Canvas Platform deploys plugins named `<prefix>__<package>` that are committed to a git repository. Run `git -C "$CPA_PLUGIN_DIR" rev-parse --show-toplevel`:
   - **Prints `$CPA_PLUGIN_DIR`:** the plugin is its own repository, the `canvas init` layout. `canvas deploy` commits and pushes that repository.
   - **Prints another path:** the plugin sits inside a larger repository, such as a monorepo. Tell the user it deploys as a snapshot: the `deployer` tool passes `--snapshot`, which pushes the package folder as committed at HEAD and leaves that repository's remotes and config alone, and refuses uncommitted changes in the package rather than committing them (canvas-plugins `canvas_cli/apps/platform/git.py:319-345` at 1.13.0). Commits for it are made in that repository, scoped to the package folder.
   - **Fails (not in a git repository):** ask the user whether to run `git init` in `$CPA_PLUGIN_DIR`, the plugin's repository root, because the CLI's own offer to do it appears only in a terminal (`canvas_cli/apps/platform/git.py:107-135` at 1.13.0). On yes, run `git init` there. On no, STOP and deploy nothing.

   A manifest `name` without a `<prefix>__` part deploys as it is; Canvas Platform decides whether the person may deploy that name, and the `deployer` tool reports a refusal as `deploy_failed`.

3. **Canvas CLI version.** `uv run canvas --version` must be 1.2.0 or newer. If it is older, run `uv add 'canvas[test-utils]>=1.2.0'` in the container, then continue.

4. **List the deployable instances.** From `$CPA_PLUGIN_DIR`:

   ```bash
   uv run --with 'canvas>=1.2.0' python "${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py" instances
   ```

   The script prints one line per instance, `<slug> test_instance=<true|false> production=<true|false> logs=<true|false>`. **If it exits non-zero** (for example `Not signed in to Canvas Platform ...`): show its output and STOP. When it reports not signed in, tell the user to run `uv run --with 'canvas>=1.2.0' canvas login` in their own terminal (it opens a browser) and then run this command again. If the user does not sign in, the command stops here.

   Work in progress deploys as a branch, which Canvas Platform accepts only on test instances and refuses on any other instance (canvas-plugins `canvas_cli/apps/platform/commands.py:1071-1076` at 1.13.0). Keep only the lines with `test_instance=true`: they are the instances this command offers.

   **If no line has `test_instance=true`:** STOP and tell the user that a Deploy manager or Organization admin designates a test instance on the instance's Plugin management tab in Canvas Platform ([Designating test instances](https://help.canvasmedical.com/articles/4724162094-designating-test-instances)). Deploy nothing.

5. **Handle the target instance argument** (among the test instances only):
   - If `$1` is provided and listed: use `$1` as the target instance
   - If `$1` is on a line of the instance list above with `test_instance=false`: tell the user that work in progress deploys only to test instances, and that a release to `$1` goes through `/cpa:wrap-up`. Then continue as if `$1` were not provided.
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

6. **Choose the branch.** Canvas Platform's `main` is published only by `/cpa:wrap-up`, so this command deploys the work as a branch (`canvas deploy --branch` pushes HEAD to that branch and refuses `main` and malformed names, `commands.py:824-840` and `:1071-1076` at 1.13.0). Run:

   ```bash
   git -C "$CPA_PLUGIN_DIR" branch --show-current
   ```

   - **Prints a name other than `main`:** ask with AskUserQuestion, replacing `<name>` with the printed name:

```json
{
  "questions": [
    {
      "question": "Deploy this work as branch `<name>` on Canvas Platform? It deploys only to test instances.",
      "header": "Branch",
      "options": [
        {"label": "Use <name> (Recommended)", "description": "Push the current branch to Canvas Platform under its own name"},
        {"label": "Another name", "description": "I'll type a different work branch name"}
      ],
      "multiSelect": false
    }
  ]
}
```

   - **Prints `main`, or nothing (detached HEAD):** ask the user for a work branch name, suggesting `<plugin short name>-wip`. Never offer `main` as the default. Do not deploy until the user gives a name.

   A typed name is used as given. If the CLI refuses it, the `deployer` tool reports `Status: deploy_failed` with the CLI's reason, the agent stops, and the user re-runs `/cpa:deploy` with another name.

Save the resolved instance slug, the confirmed branch, and the plugin name (the inner package folder). You will pass them to the agent and use the slug for log monitoring.

### Step 3: Reference Review

Run this before log monitoring starts so a blocking finding never leaves a log tail running.

Set `ARTIFACTS` to `$CPA_PLUGIN_DIR/.cpa-workflow-artifacts` (where `/cpa:new-plugin` moves the artifacts once the plugin exists), or to `$CPA_WORKSPACE_DIR/.cpa-workflow-artifacts` when the contract is only there. If neither holds `existing-plugins-reference.md`, or its `## PATTERNS` section is `None.`, skip to Step 4.

Use the **reference-reviewer** agent with this brief:

```
contract: $ARTIFACTS/existing-plugins-reference.md
ledger: $ARTIFACTS/reference-review.json
repo: $CPA_PLUGIN_DIR
base_sha: <plugin_sha of the last ledger entry marked "deployed": true, or empty>
head_sha: <output of git rev-parse HEAD>
prior_findings: <findings already in the ledger, with their dispositions>
deviations: $ARTIFACTS/plugin-spec.md
```

The reviewer diffs `base_sha` against the working tree, so uncommitted changes that this deploy is about to ship are reviewed too.

- If it returns no findings, add `"deployed": true` to its ledger entry and continue.
- If it returns findings, show them and ask the user whether to fix first or deploy anyway.
  - **Fix first:** stop the deploy here, leaving the entry without `deployed`. Fix the code, then run `/cpa:deploy` again. Only deployed reviews are a base, so the rerun diffs from the last deployed review and re-raises whatever still deviates.
  - **Deploy anyway:** set each finding's `disposition` to `declined: <reason>`, add `"deployed": true` to the entry, and continue.
  - Whenever a finding gets a disposition, give the same disposition to every earlier finding in the ledger for the same pattern and build location that has none.
- If the reviewer fails without writing a ledger entry, append `{"plugin_sha": "<head_sha>", "status": "review skipped: <reason>"}` to the ledger and continue.

### Step 4: Start Log Monitoring (BEFORE deploy)

`canvas logs` signs in through Canvas Platform, which issues the log token for an instance it manages (canvas-plugins `canvas_cli/apps/logs/logs.py:113-153` and `canvas_cli/apps/platform/routing.py:62-90` at 1.13.0). Read the instance's `logs=` value from the Step 2 line:

- **`logs=true`:** start log streaming **in the parent context**, so the background process survives the agent lifecycle, as a **background task** (`run_in_background: true`):

  ```bash
  unbuffer uv run canvas logs --host {instance}
  ```

  Save the `bash_id` to use it later to check logs. This captures deployment errors and runtime behavior, including a handler that fails to load in the sandbox, which leaves the plugin enabled with that handler missing.
- **`logs=false`:** tell the user they lack the Plugin developer or Deploy manager role on {instance}, so logs are unavailable for this deploy. Continue.

### Step 5: Deploy via Agent

Use the **deploy-uat** agent to handle version bump, validation, local git commit, and deploy. Pass the resolved instance slug so the agent does not need to ask again.

Tell the agent: "Deploy to {instance} as branch {branch}", and, when the repository check found a larger repository, "The plugin is inside the larger repository at {toplevel}, so it deploys as a snapshot".

The agent returns when the deploy is complete, or when it stopped: uncommitted changes declined, deploy failed, a snapshot refused, or a custom data consent request or a snapshot confirmation was denied or left unanswered. The agent owns the consent hand-off (see its Step 4). Continue to Step 6 only when the agent reports the deploy complete. If the agent reports a stop, stop log monitoring (KillShell) if it is running, relay the agent's report to the user, and end the command.

### Step 6: Post-Deployment Log Check

Skip this step when Step 4 started no log stream.

After the agent returns and the deploy is complete, check the logs **in the parent context** (you own the background process).

1. Wait 5 seconds for logs to accumulate (`sleep 5`)
2. Use **BashOutput** with the saved bash_id to retrieve buffered output (this does NOT stop the background process)
3. **If the background shell has exited:** the stream did not start or has dropped (for example Canvas Platform refused the log token), so there are no logs to check. Show its output to the user, say logs are unavailable for this deploy, and treat logs as unavailable for the rest of this command.
4. Scan for errors (tracebacks, `ERROR`, `Exception`, `RestrictedPython error`, `ModuleNotFoundError`, deploy failures)
5. **If errors are found:**
   1. Stop log monitoring (KillShell)
   2. Show the errors to the user
   3. Analyze root cause and fix the code
   4. Re-deploy (repeat from Step 3, so the fix is reviewed too)
6. **If no errors:** leave log monitoring running and continue to UAT

### Step 7: UAT

- **Log stream running:** tell the user: "Plugin deployed to {instance}, and no errors detected in logs. Log monitoring is running: go ahead and test in Canvas. Tell me to 'check the logs' when you want to see what happened."
  - When the user says "check the logs": use BashOutput with the saved bash_id to retrieve and analyze log entries. If the background shell has exited, say the stream has ended and logs are unavailable.
  - When testing is complete: use KillShell to stop the background log stream
- **No log stream:** tell the user: "Plugin deployed to {instance}. Canvas logs are unavailable for this deploy, so I can't confirm it loaded: go ahead and test in Canvas, and tell me what you see."
  - When the user reports a problem: work from what they describe and the plugin's tests, fix the code, and deploy again with this command.

After successful UAT, guide the user to the next step in the workflow.

## Sign-in

`canvas deploy` acts as the person signed in with `canvas login` (or `CANVAS_PLATFORM_TOKEN`). `canvas logs` uses the same sign-in. Plugin variable values live in `~/.canvas/plugin-secrets/<instance slug>.json`, keyed by the manifest name.

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
- `/cpa:deploy acme-prod` - acme-prod is not a test instance, so the command says a release there goes through `/cpa:wrap-up` and asks for a test instance
