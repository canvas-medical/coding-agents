---
name: deploy-lite
description: Quick-deploy the current plugin to a Canvas instance through Canvas Platform: no version bump, no tests. Commits, deploys, and checks logs where credentials.ini allows it.
---

# Deploy Lite

Quick-deploy the current plugin to a Canvas instance through Canvas Platform: no version bump, no tests. Commits, deploys, and checks logs when `~/.canvas/credentials.ini` has a section for the instance.

## Arguments

- `$1` (optional): Canvas Platform instance slug (e.g. `acme-staging`)

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

### Step 2: Determine Target Instance

Resolve the deployment target.

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

   To list the prefixes, run `uv run --with 'canvas>=0.263.0' python "${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py" whoami`.

3. **Canvas CLI version.** `uv run canvas --version` must be 0.263.0 or newer. If it is older, run `uv add 'canvas[test-utils]>=0.263.0'` in the container, then continue.

4. **List the deployable instances.** From `$CPA_PLUGIN_DIR`:

   ```bash
   uv run --with 'canvas>=0.263.0' python "${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py" instances
   ```

   The script prints one instance slug per line. **If it exits non-zero** (for example `Not signed in to Canvas Platform ...`): show its output and STOP. When it reports not signed in, tell the user to run `uv run --with 'canvas>=0.263.0' canvas login` in their own terminal (it opens a browser) and then run this command again. If the user does not sign in, the command stops here.

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

Save the resolved instance slug and the plugin name (the inner package folder) for the deploy and log monitoring.

### Step 3: Start Log Monitoring (BEFORE deploy)

`canvas logs` signs in with the client credentials in the `~/.canvas/credentials.ini` section named after the instance slug, not with the Canvas Platform sign-in (canvas-plugins `canvas_cli/apps/logs/logs.py:339` and `canvas_cli/apps/auth/utils.py:55-58` at 0.262.0). Check for that section, reading only section headers, since the file holds client secrets:

```bash
grep -qx "\[{instance}\]" ~/.canvas/credentials.ini 2>/dev/null && echo "logs=available" || echo "logs=unavailable"
```

- **`logs=available`:** start log streaming as a **background task** (`run_in_background: true`), and save the `bash_id`:

  ```bash
  unbuffer uv run canvas logs --host {instance}
  ```

- **`logs=unavailable`:** there is no log stream for this deploy. Continue.

Whenever this command stops before Step 6, stop log monitoring (KillShell) if it is running.

### Step 4: Verify Cache Busting

If the plugin serves HTML content (has templates/ directory or uses `render_to_string`), verify that:

1. A module-level `_CACHE_BUST = str(int(datetime.now(timezone.utc).timestamp()))` exists in any file that renders HTML
2. `cache_bust` (or equivalent) is passed in the `render_to_string()` context
3. HTML templates use `?v={{ cache_bust }}` on external `<script src>` and `<link href>` URLs, and on plugin-served static asset URLs
4. Any `LaunchModalEffect(url=...)` calls include `?v={_CACHE_BUST}` in the URL

If cache busting is missing, add it before proceeding with deployment.

### Step 5: Commit and Deploy

`canvas deploy` deploys only committed work, so commit first. No version bump and no tests.

1. Check for uncommitted work in the plugin container directory:

   ```bash
   git status --porcelain .
   ```

   If the output is empty, go to the deploy below.

2. Stage tracked changes only:

   ```bash
   git add -u .
   ```

3. List untracked files (`git status --porcelain --untracked-files=all . | grep '^??'`). If there are any, read each one and flag any that look like secrets or local-only scratch (`*.env`, `*secret*`, `*credential*`, `*.key`, `*.pem`, `*token*`, or contents with `api_key`, `password`, `Bearer `, `-----BEGIN`). Ask once with AskUserQuestion which to include, defaulting to none and never pre-selecting a flagged file:

```json
{
  "questions": [
    {
      "question": "There are untracked files in the plugin directory. Which should be included in this commit? (Files that look like secrets are flagged, so leave them out unless you are sure.)",
      "header": "Untracked files",
      "options": [
        {"label": "None, commit tracked only", "description": "Recommended. Leaves every untracked file out of the commit."},
        {"label": "Select specific files", "description": "I'll tell you which untracked files are safe to add"},
        {"label": "All untracked", "description": "Add every untracked file (only if none are flagged and you've reviewed them)"}
      ],
      "multiSelect": false
    }
  ]
}
```

   Only `git add` the specific untracked files the user approves.

   - **Plugin is its own repository:** `canvas deploy` refuses to deploy while any untracked file remains, so add every untracked file the user leaves out to `.git/info/exclude` (local to this clone, never committed):

     ```bash
     echo "path/to/left-out-file" >> "$(git rev-parse --git-dir)/info/exclude"
     ```

   - **Plugin is inside a larger repository:** the commit lands on the current branch of that repository, so show the staged files (`git diff --cached --stat .`) and ask before committing. A snapshot refuses any uncommitted or untracked file inside the package folder (canvas-plugins `canvas_cli/apps/platform/git.py:317-324` at 0.262.0), and untracked files elsewhere in the repository do not block it. For each untracked file in the package that the user leaves out, ask whether to delete it or ignore it in that repository's `.gitignore`; never edit the repository's `.git/info/exclude` without asking.

4. Commit (never push; `canvas deploy` pushes the commit to the plugin's Canvas Platform repository, or a snapshot of the package folder for a plugin inside a larger repository):

   ```bash
   git commit -m "quick deploy {plugin_name}"
   ```

   If the user declines to commit, STOP: `canvas deploy` refuses to deploy while uncommitted changes remain.

5. Deploy. Use the **`deployer`** MCP tool (provided by the `canvas_cmd_line` MCP server) to deploy the plugin and set its variables:

   - `plugin_name`: the inner package folder name (`$PACKAGE_DIR`)
   - `instance`: the resolved instance slug
   - `cwd`: current working directory (the plugin container directory)

   The MCP tool runs `canvas deploy` (with `--snapshot` when the plugin sits inside a larger repository; it detects this itself, so pass the same arguments either way), then reads variable names from `CANVAS_MANIFEST.json`, retrieves their values from `~/.canvas/plugin-secrets/{instance}.json`, and passes them to `canvas config set`. Secret values are never exposed to Claude Code.

   If the response includes a warning about missing secrets, show the warning to the user. The deploy still proceeds, and the warning is informational.

   The last line of the tool output is `Status: <status>`. Route on that line alone, never on the `canvas deploy` text above it. Never call `deployer` again for `consent_pending`, `still_running`, or `snapshot_replaces_platform`: a second call creates a second waiting deployment, or meets the same refusal. The **`configurer`** tool also ends with a `Status:` line: `configured`, `configure_failed`, or `invalid_input`. When a `configurer` call below ends with anything other than `Status: configured`, handle it as `configure_failed` (sub-step 14).

6. **`Status: consent_pending`**: the deployment is waiting on custom data access consent. Only a person at a terminal can answer it:

   1. Show the request lines (the `•` lines in the output) verbatim.
   2. Explain: approving gives one plugin access to another plugin's custom data on that instance, and only a person at a terminal can answer.
   3. Give the exact command from the tool output (`cd <dir> && uv run canvas deploy <plugin> --no-push --instance <instance>`) and ask the user to run it in their own terminal, approve or deny, and tell you when it finished.
   4. Wait for the user. Never answer the request yourself, never pass `--yes`, never call the Platform consent API, and never claim the deploy succeeded.
   5. **User approved and the command succeeded:** call the **`configurer`** MCP tool with the same `plugin_name`, `instance`, and `cwd`, then continue to Step 6.
   6. **User denied:** the deployment is cancelled. Report that and stop.
   7. **User does not act:** the deployment stays pending on Canvas Platform. Tell the user and stop.

7. **`Status: still_running`**: the deployment is still running on Canvas Platform and variables were not set. Tell the user, give them the deployment id from the output, and wait for them to confirm on Canvas Platform that the deployment succeeded, then call the **`configurer`** MCP tool with the same `plugin_name`, `instance`, and `cwd`, and continue to Step 6. If the deployment fails, show the failure and stop.

8. **`Status: dirty_tree`**: the repository still has uncommitted or untracked files. Never pass `--yes`: it commits every file, including the ones the user left out. Repeat sub-steps 1-4 above for the files listed by `git status --porcelain`, then call `deployer` again.

9. **`Status: snapshot_uncommitted`**: the plugin is inside a larger repository, and its package folder has uncommitted or untracked files, or no committed files at all. A snapshot deploys only committed work and never commits for you. Show the listed files and ask whether to commit them (sub-steps 1-4, for the larger repository) or whether the user commits them; never pass `--yes`. Once they are committed, deleted, or ignored, call `deployer` again. If the user declines, stop.

10. **`Status: snapshot_unsupported`**: the package folder holds a submodule, a symbolic link, or a file stored through a filter such as Git LFS or git-crypt, which a snapshot cannot carry. Show the listed paths, tell the user each must become a regular committed file, and stop.

11. **`Status: snapshot_rollback`**: Canvas Platform's `main` was last deployed from a commit whose changes this checkout's HEAD lacks, so this deploy would roll the plugin back. Show the listed files, tell the user to update the checkout so it includes those changes (for example `git pull`), and stop.

12. **`Status: snapshot_replaces_platform`**: files in the package were changed on Canvas Platform (for example a catalog listing edited there), and this snapshot would replace them. Only a person at a terminal can confirm that:

    1. Show the listed files verbatim.
    2. Give the user both ways forward: run the exact command from the tool output (`cd <dir> && uv run canvas deploy <plugin> --snapshot --instance <instance>`) in their own terminal and confirm replacing them; or keep Canvas Platform's versions by checking them out with `canvas clone <name>`, copying them into the package folder, and committing.
    3. Wait for the user. Never confirm it yourself and never pass `--yes`.
    4. **User ran the command and it succeeded:** call the **`configurer`** MCP tool with the same `plugin_name`, `instance`, and `cwd`, then continue to Step 6.
    5. **User copied Platform's versions and committed:** call `deployer` again.
    6. **User does not act:** nothing was deployed. Tell the user and stop.

13. **`Status: deploy_failed` or `Status: invalid_input`**: the deploy did not run or failed. Show the output and stop.

14. **`Status: configure_failed`**: the plugin is deployed but its variables were not set. Show the output and tell the user the plugin is running without its variables until the **`configurer`** MCP tool ends with `Status: configured`, then continue to Step 6.

15. **`Status: deployed`**: the deploy succeeded, and every variable with a value in the secrets file is set (a missing-secrets warning names the rest). Continue to Step 6.

### Step 6: Post-Deployment Log Check

After the deploy completes, report the result. Do NOT attempt to fix any errors.

- **No log stream (Step 3 started none):** tell the user the deployment completed, and that Canvas logs are unavailable for this deploy, so it cannot confirm that the plugin loaded: logs stream only with a `~/.canvas/credentials.ini` section for the instance. Ask them to test in Canvas. Stop.
- **Log stream started:**
  1. Wait 5 seconds for logs to accumulate (`sleep 5`)
  2. Use **BashOutput** with the saved bash_id to retrieve buffered output (this does NOT stop the background process)
  3. **If the background shell is no longer running:** the stream did not start or has dropped. Show its output, tell the user the deployment completed but Canvas logs are unavailable, ask them to test in Canvas, and stop.
  4. Scan for errors (tracebacks, `ERROR`, `Exception`, `RestrictedPython error`, `ModuleNotFoundError`, deploy failures)
  5. Stop log monitoring (KillShell): always stop regardless of outcome
  6. **If errors are found:** show the errors to the user. Do NOT offer to fix them or re-deploy. Just report the errors and stop.
  7. **If no errors:** tell the user the deployment completed and no errors were detected in logs. Stop.

## Sign-in

`canvas deploy` acts as the person signed in with `canvas login` (or `CANVAS_PLATFORM_TOKEN`). `~/.canvas/credentials.ini` is used only by `canvas logs`, and only when it has a section named after the instance; `credentials.ini` support ends December 14, 2026. Plugin variable values live in `~/.canvas/plugin-secrets/<instance slug>.json`, keyed by the manifest name.

## Examples

- `/cpa:deploy-lite` - Quick deploy (auto-selects instance if only one, otherwise asks)
- `/cpa:deploy-lite acme-staging` - Quick deploy to the acme-staging instance
