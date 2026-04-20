---
name: wrap-up
description: Final checklist before calling a plugin "done" for this version.
---

# Wrap Up Plugin

Final checklist before calling a plugin "done" for this version.

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

Run through each checklist item, report findings, and give a clear verdict.

### Step 2: Project Structure Validation

**Before any other checks, verify the plugin has the correct folder structure.**

```bash
uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/verify_plugin_structure.py"
```

**If structure validation fails:**
- Report all errors to the user
- Offer to fix each issue (move files to correct locations)
- Do NOT proceed with other checks until the structure is correct

**Common fixes:**

Determine the inner package folder (`<prefix>__<name>`):
```bash
INNER=$(dirname */CANVAS_MANIFEST.json)
```

| Issue | Fix |
|-------|-----|
| CANVAS_MANIFEST.json at container level | `mv CANVAS_MANIFEST.json <prefix>__<name>/` |
| tests/ inside inner folder | `mv $INNER/tests ./` (run the `INNER=` line above first) |
| No inner folder | Re-run `canvas init` or restructure manually |

---

### 1. Security Review

Run the comprehensive security review command:

```
/cpa:security-review
```

This covers:
- **Plugin API Server Security** - SimpleAPI/WebSocket authentication and authorization
- **FHIR API Client Security** - Token scopes, patient-scoped tokens, token storage
- **Application Scope** - Manifest scope alignment with token usage
- **Secrets Declaration** - All tokens properly declared

The command saves a report to `.cpa-workflow-artifacts/` and offers to fix any issues found.

### 2. Database Performance Review

Check if the plugin queries Canvas data models:

```bash
grep -rn "\.objects\." --include="*.py" .
```

**If data queries exist:**
- Invoke the **database-performance** skill
- Look for N+1 query patterns (queries inside loops)
- Check for missing `select_related()` on foreign key access
- Check for missing `prefetch_related()` on reverse relations
- Report any performance issues found

**If no data queries:** Mark database performance as N/A.

### 3. Type checking

```bash
uv run mypy --config-file=mypy.ini .
```

**If errors exist:** Flag this as a blocker.

### 4. Test Coverage

Run coverage check:

```bash
uv run pytest --cov=. --cov-report=term-missing --cov-branch
```

**If coverage < 90%:**
- Tell the user coverage needs improvement
- Offer to run `/cpa:coverage` to address gaps

**If coverage ≥ 90%:** Mark tests as passing.

**If no tests exist:** Flag this as a blocker.

### 5. Debug Log Cleanup

Check for debug logging statements that were added during UAT troubleshooting:

```bash
grep -rn "\[DEBUG\]\|# DEBUG\|# TODO\|print(" --include="*.py" .
```

Also look for excessive logging that should be removed:

```bash
grep -rn "log\.\(info\|debug\|warning\)" --include="*.py" . | head -30
```

**Review each log statement:**
- Remove any `[DEBUG]` prefixed logs - these were for troubleshooting
- Remove `print()` statements - use logger instead or remove entirely
- Keep meaningful operational logs (errors, important business events)
- Remove verbose logs that dump full objects or contexts

**Good logs to keep:**
```python
log.info(f"Alert created for patient {patient_id}")
log.warning(f"Missing required field: {field_name}")
```

**Logs to remove:**
```python
log.info(f"[DEBUG] Full event context: {self.event.context}")  # Too verbose
log.info(f"[DEBUG] Entering compute()")  # Only useful during debugging
print(f"vitals: {vitals}")  # Should use logger, and too verbose
```

### 6. Dead Code Removal

Identify and remove unused code:

**Step 1: Trace from manifest declarations**

Read `CANVAS_MANIFEST.json` and verify every declared component exists and is used:
- Each `protocols` entry should have a corresponding file that's actually needed
- Each `commands` entry should reference code that exists
- Each `applications` entry should reference code that exists
- Each `content` entry should be used

Remove any declarations for code that no longer exists, and remove code that isn't declared in the manifest.

**Step 2: Check for unused imports**

```bash
grep -rn "^from\|^import" --include="*.py" .
```

Review each file for imports that aren't used in the code.

**Step 3: Check for unused functions and variables**

Look for:
- Functions defined but never called
- Variables assigned but never read
- Commented-out code blocks (delete them, git has history)
- Placeholder/scaffolding code from `canvas init` that wasn't needed

**Step 4: Remove dead tests**

Check that all test files test code that still exists:
- If a handler was removed, remove its tests
- If a function was renamed, update or remove old tests
- Remove `test_models.py` if it's just scaffolding

**Common dead code from scaffolding:**
- `handlers/my_handler.py` - default placeholder if you renamed your handler
- `test_models.py` - often unused scaffolding
- Unused effect imports (e.g., `AddTask` if you only use `AddBannerAlert`)
- Empty or stub methods that were never implemented

**Remove dead code rather than commenting it out.** Git history preserves old code if needed.

### 7. Cache Busting Verification

**If the plugin serves HTML content**, verify cache busting is properly implemented.

Check if the plugin uses HTML templates or `render_to_string`:

```bash
INNER=$(dirname */CANVAS_MANIFEST.json)
ls "$INNER"/templates/ 2>/dev/null; grep -rn "render_to_string" --include="*.py" .
```

**If HTML content exists, verify all four requirements:**

1. **Module-level `_CACHE_BUST` token** exists in every file that renders HTML:
   ```bash
   grep -rn "_CACHE_BUST" --include="*.py" .
   ```
   Expected: `_CACHE_BUST = str(int(datetime.now(timezone.utc).timestamp()))` at module level.

2. **`cache_bust` passed in template context** for every `render_to_string()` call:
   ```bash
   grep -rn "render_to_string" --include="*.py" -A 5 .
   ```
   Every call must include `"cache_bust": _CACHE_BUST` (or equivalent) in its context dict.

3. **HTML templates use `?v={{ cache_bust }}`** on all external resource URLs:
   ```bash
   grep -rn "src=\|href=" --include="*.html" .
   ```
   Every `<script src>`, `<link href>`, and plugin-served static asset URL must end with `?v={{ cache_bust }}`. Flag any that don't.

4. **`LaunchModalEffect(url=...)` calls include cache busting**:
   ```bash
   grep -rn "LaunchModalEffect" --include="*.py" -A 3 .
   ```
   Any `url=` argument must include `?v={_CACHE_BUST}`.

**If any requirement is missing:** Fix it before proceeding. Do NOT use `Path`, `json.load`, or filesystem reads for the token — use the UTC timestamp approach.

**If no HTML content:** Mark as N/A.

### 8. WebSocket Deploy Resilience

**If the plugin uses a WebSocket** (a `WebSocketAPI` handler, a `Broadcast` effect, or client-side `new WebSocket(...)`), verify it's built to survive Canvas's daytime blue/green deploys. A deploy closes every live socket mid-session and clients reconnect onto a freshly booted process, so a socket that works in testing can silently lose updates or hammer the new container in production.

Check whether the plugin uses WebSockets:

```bash
grep -rn "WebSocketAPI\|Broadcast(" --include="*.py" .
grep -rn "new WebSocket(" --include="*.html" --include="*.js" .
```

**If a WebSocket exists, verify all four:**

1. **Re-fetch the snapshot on every (re)connect**, wired to the socket's `open` event — not only on initial page load. Broadcasts are ephemeral, so anything sent during the gap is lost; the reconnect must reconcile by pulling current state:
   ```bash
   grep -rn "addEventListener(\"open\"\|addEventListener('open'\|\.onopen" --include="*.html" --include="*.js" .
   ```
   The `open` handler must call the same "load current state" fetch the page uses on first load.

2. **Reconnect with exponential backoff + jitter + a cap** — never a fixed delay. Every client drops at once at cutover, so a fixed delay is a thundering herd against the single container that just booted:
   ```bash
   grep -rn "setTimeout\|reconnect\|Math.random" --include="*.html" --include="*.js" .
   ```
   Flag any fixed-delay reconnect (e.g. `setTimeout(connect, 4000)`).

3. **Reconnect immediately on the browser `online` event** instead of waiting out a backoff timer:
   ```bash
   grep -rn "\"online\"\|'online'" --include="*.html" --include="*.js" .
   ```

4. **Mutating `POST`s are idempotent** — they re-check current state and no-op if the desired state already holds, since a cutover can drop the response and the client will retry. Review each mutating SimpleAPI route (assign-to-me, mark-complete, originate-command, etc.) for a state pre-check before it emits its effect.

Full rationale and worked client code are in the **canvas-sdk** skill ("WebSockets must survive blue/green deploys") and the **companion-app-patterns** skill's context file ("Surviving deploys & reconnection").

**If any requirement is missing:** Fix it before proceeding.

**If no WebSocket:** Mark as N/A.

### 9. README Review

Read the plugin's README.md and verify:

**Must have:**
- [ ] Plugin name and brief description
- [ ] What events/triggers the plugin responds to
- [ ] What effects/actions the plugin produces
- [ ] Any configuration requirements
- [ ] Any external dependencies or integrations

**Must NOT have:**
- [ ] Outdated information (old handler names, removed features)
- [ ] TODOs or placeholder text
- [ ] Overly verbose explanations (keep it succinct)
- [ ] Internal implementation details users don't need

**Should match:**
- [ ] Handler list matches actual code
- [ ] Event types match CANVAS_MANIFEST.json
- [ ] Any environment variables mentioned are accurate

Update the README if issues are found.

### 10. Application Icon Check

**If the plugin has an Application component, verify it has an icon.**

Check CANVAS_MANIFEST.json for applications:

```bash
INNER=$(dirname */CANVAS_MANIFEST.json)
grep -A 10 '"applications"' "$INNER/CANVAS_MANIFEST.json" 2>/dev/null
```

**If applications exist:**

For each application entry, verify:
- [ ] The `icon` field is present
- [ ] The icon file exists in the inner plugin directory
- [ ] The icon is a PNG file (48x48 recommended)
- [ ] The filename matches what's in the manifest

Check icon files:
```bash
INNER=$(dirname */CANVAS_MANIFEST.json)
ls -lh "$INNER"/assets/*.png 2>/dev/null || echo "No PNG icons found"
```

**If Application exists but no icon:**
- Offer to create an icon using the icon-generation skill
- Invoke `Skill(skill="icon-generation")` to generate an appropriate icon
- Update the manifest with the icon filename

**If no applications:** Mark as N/A.

### 11. License Check

Check for any license file or license mentions:

```bash
ls -la LICENSE* license* 2>/dev/null
grep -i "license\|MIT\|BSD\|Apache\|GPL" README.md 2>/dev/null
```

**⚠️ IMPORTANT: Plugins built for specific customers should NOT have open source licenses.**

If a LICENSE file exists or the README mentions a license (MIT, BSD, Apache, GPL, etc.), ask the user:

```json
{
  "questions": [
    {
      "question": "I found a license file or license mention. Is this plugin intended for open source distribution?",
      "header": "License check",
      "options": [
        {"label": "Yes, open source", "description": "This is a public/community plugin"},
        {"label": "No, remove it", "description": "This is a customer-specific plugin, remove the license"}
      ],
      "multiSelect": false
    }
  ]
}
```

If the user says to remove it, delete the LICENSE file and remove any license section from the README.

### 12. Final Verdict

After all checks, present a summary:

```markdown
## Wrap-Up Summary

| Check | Status | Notes |
|-------|--------|-------|
| Project Structure | ✅ Pass / ❌ Errors | ... |
| Plugin API Security | ✅ Pass / ⚠️ Issues / N/A | ... |
| FHIR Client Security | ✅ Pass / ⚠️ Issues / N/A | ... |
| DB Performance | ✅ Pass / ⚠️ N+1 Issues / N/A | ... |
| Type checking | ✅ Pass / ❌ Errors | ... |
| Coverage | ✅ 92% / ❌ 78% | ... |
| Debug Logs | ✅ Clean / ⚠️ Removed X logs | ... |
| Dead Code | ✅ Clean / ⚠️ Removed X items | ... |
| Cache Busting | ✅ Pass / ⚠️ Fixed / N/A | ... |
| WebSocket Resilience | ✅ Pass / ⚠️ Fixed / N/A | ... |
| README | ✅ Current / ⚠️ Updated | ... |
| Application Icon | ✅ Present / ⚠️ Created / N/A | ... |
| License | ✅ None / ⚠️ Removed / ✅ Intentional | ... |

### Verdict

**✅ Ready to ship** - You can call it done for this version.

OR

**❌ Changes needed:**
1. Fix the security issue in `/api/webhook.py` - missing auth check
2. Run `/cpa:coverage` to improve test coverage to 90%
3. Update README to remove reference to deleted handler
```

**Save the wrap-up report:**

Save the report, overwriting any previous run:

```bash
mkdir -p "$CPA_PLUGIN_DIR/.cpa-workflow-artifacts"
REPORT_FILE="$CPA_PLUGIN_DIR/.cpa-workflow-artifacts/wrap-up-report.md"

# Create the report (replace {plugin_name} with actual plugin name)
cat > "$REPORT_FILE" <<'REPORT_END'
# Wrap-Up Report: {plugin_name}

**Generated:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Reviewer:** Claude Code (CPA)

## Wrap-Up Summary

| Check | Status | Notes |
|-------|--------|-------|
| Project Structure | {status} | {notes} |
| Plugin API Security | {status} | {notes} |
| FHIR Client Security | {status} | {notes} |
| DB Performance | {status} | {notes} |
| Type checking | {status} | {notes} |
| Coverage | {status} | {notes} |
| Debug Logs | {status} | {notes} |
| Dead Code | {status} | {notes} |
| Cache Busting | {status} | {notes} |
| WebSocket Resilience | {status} | {notes} |
| README | {status} | {notes} |
| Application Icon | {status} | {notes} |
| License | {status} | {notes} |

## Verdict

{verdict_text}

REPORT_END

echo "Wrap-up report saved: $REPORT_FILE"
```

Replace the placeholders with actual results from each check.

Use AskUserQuestion if any issues were found:

```json
{
  "questions": [
    {
      "question": "I found issues that should be addressed. How would you like to proceed?",
      "header": "Next steps",
      "options": [
        {"label": "Fix all issues", "description": "I'll address each issue now"},
        {"label": "Ship anyway", "description": "Accept current state, ship this version"},
        {"label": "Review details", "description": "Show me more about each issue"}
      ],
      "multiSelect": false
    }
  ]
}
```

### 13. Commit Changes (Interactive)

**After all checks pass (or issues are resolved), commit the plugin changes.**

This is done here, in the live session, on purpose — so untracked files can be reviewed and you are asked before anything is staged or pushed. **Never blindly `git add -A` and never push without explicit confirmation.**

**Step 13a — Show what changed:**

```bash
cd "$CPA_PLUGIN_DIR"
git status --porcelain .
```

Split the output into:
- **Tracked changes** (lines starting with ` M`, `M `, `MM`, ` D`, `D `, `R `, etc.) — modifications and deletions of files git already tracks.
- **Untracked files** (lines starting with `??`) — new files git does not yet track.

**Step 13b — Stage tracked changes only:**

```bash
git add -u .
```

`-u` stages modifications and deletions of already-tracked files and **never** picks up untracked files. This is the safe default: a stray secrets dump, `.env`, or scratch file written during the session is not swept in.

**Step 13c — Review untracked files before including any:**

If there are untracked files, do NOT add them automatically. For each one, read it and decide whether it is safe and intended for the repo:

```bash
# inspect each untracked file
git status --porcelain . | awk '/^\?\?/ {print $2}'
```

Read each untracked file and **flag any that look like they contain secrets or are local-only scratch**, in particular:
- filenames matching `*.env`, `*secret*`, `*credential*`, `*install*`, `*.key`, `*.pem`, `*token*`
- contents containing high-entropy strings or substrings like `token`, `api_key`, `apikey`, `password`, `secret`, `Bearer `, `-----BEGIN`

Present the untracked files to the user and ask which (if any) to include. Default to **none**, and never pre-select a flagged file:

```json
{
  "questions": [
    {
      "question": "There are untracked files in the plugin directory. Which should be included in this commit? (Files that look like secrets are flagged — leave them out unless you are sure.)",
      "header": "Untracked files",
      "options": [
        {"label": "None — commit tracked only", "description": "Recommended. Leaves every untracked file out of the commit."},
        {"label": "Select specific files", "description": "I'll tell you which untracked files are safe to add"},
        {"label": "All untracked", "description": "Add every untracked file (only if none are flagged and you've reviewed them)"}
      ],
      "multiSelect": false
    }
  ]
}
```

Only `git add` the specific untracked files the user explicitly approves. If a flagged (possible-secret) file is among them, confirm a second time and suggest adding it to `.gitignore` instead.

**Step 13d — Show the staged diff and commit:**

```bash
git diff --cached --stat
```

If there is nothing staged, report "no changes to commit" and skip to Step 14. Otherwise commit (replace `{plugin_name}` with the actual name):

```bash
git commit -m "complete {plugin_name} wrap-up

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Step 13e, Release:**

Releasing publishes this version to `main` on Canvas Platform, where every instance can install it. It is outward-facing and irreversible, so confirm first, and run it through the **`deployer`** MCP tool (provided by the `canvas_cmd_line` MCP server), never a Bash `canvas deploy`.

1. **Check the `deployer` tool is available.** When it is not in this session, or a call to it is refused (Studio denies it), skip this step: say Studio publishes through its Publish button, and nothing is merged or pushed.
2. Ask:

   ```json
   {
     "questions": [
       {
         "question": "Release this version? It publishes to main on Canvas Platform, where every instance can install it.",
         "header": "Release?",
         "options": [
           {"label": "Release now", "description": "Publish the committed plugin to main on Canvas Platform and deploy it to an instance you choose"},
           {"label": "Don't release", "description": "Leave the commit local; I'll release it myself later"}
         ],
         "multiSelect": false
       }
     ]
   }
   ```

   On "Don't release", skip to Step 14.
3. Check where the plugin sits with `git rev-parse --show-toplevel`:
   - **Prints `$CPA_PLUGIN_DIR` (the plugin is its own repository):** the release deploys `main`. When `git branch --show-current` is not `main`, ask:

     ```json
     {
       "questions": [
         {
           "question": "The release deploys main, and you are on a work branch. Fast-forward main to it?",
           "header": "Merge to main?",
           "options": [
             {"label": "Fast-forward main", "description": "Run git switch main && git merge --ff-only <work branch>, so main holds this version"},
             {"label": "Don't release", "description": "Stay on the work branch and release later"}
           ],
           "multiSelect": false
         }
       ]
     }
     ```

     On "Fast-forward main", run the commands. When the repository has no local `main` (`git rev-parse --verify --quiet refs/heads/main` prints nothing, as after a `git init` that named the first branch `master`), run `git switch -c main` instead, which starts `main` at the work branch. When `main` cannot fast-forward, stop and say so; nothing is pushed.
   - **Prints another path (the plugin is inside a larger repository):** no merge happens. The `deployer` tool pushes a snapshot of the package folder as committed at HEAD to `main`, and it refuses an uncommitted or untracked file in the package (`Status: snapshot_uncommitted`).
4. List the instances with `uv run --with 'canvas>=1.2.0' python "${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py" instances`. Each line is `<slug> test_instance=<true|false> production=<true|false> logs=<true|false>`. Ask which instance to deploy the release to, offering every line (a release is not limited to test instances, and a work branch deploy is). When the line says `production=true`, confirm first with the production block in `agents/deploy-uat.md` (the "Environment Promotion" JSON block); on "No, cancel", stop.
5. Call `deployer` with `plugin_name`, `instance`, `cwd`, and `branch` left empty. An empty `branch` pushes to `main` and deploys it (canvas-plugins `canvas_cli/apps/platform/commands.py:1050-1051` at 1.13.0). Route on the `Status:` line exactly as `agents/deploy-uat.md` Step 4 does, including `snapshot_uncommitted` (offer to commit the package files in the larger repository; never pass `--yes`).

To install the released version on more instances later, list the instances as in step 4 and ask which one to install it on. When the chosen line says `production=true`, confirm first with the production block in `agents/deploy-uat.md` (the "Environment Promotion" JSON block); on "No, cancel", stop. Then call `deployer` with `plugin_name`, `instance`, `cwd`, `version` set to the released version (for example `1.4.0`), and `branch` empty. That runs `canvas deploy --plugin <name>@<version>`, which takes no folder and pushes nothing (`commands.py:985-993`, `1098-1117` at 1.13.0). Route on the `Status:` line exactly as `agents/deploy-uat.md` Step 4 does.

### 14. Wrap-Up Complete

**After the commit step, the plugin is ready for this version.**

## CPA Workflow

This command is the **final step** in the Canvas Plugin Assistant workflow:

```
/cpa:check-setup                 →  Verify environment tools and Canvas Platform sign-in
/cpa:new-plugin                  →  Create plugin from requirements
/cpa:deploy                      →  Deploy to Canvas instance for UAT
/cpa:coverage                    →  Check test coverage (aim for 90%)
/cpa:security-review             →  Engineering security audit
/cpa:product-review              →  Product / regulatory / norms review
/cpa:database-performance-review →  Database query optimization
/cpa:wrap-up                     →  Final checklist, commit, and release  ← YOU ARE HERE
```

After wrap-up passes, the plugin is ready to ship!
