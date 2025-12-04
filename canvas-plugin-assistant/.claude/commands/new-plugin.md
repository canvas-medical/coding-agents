# New Plugin

Start the plugin brainstorming process to transform requirements into a concrete specification, then implement it.

## Instructions

Use the **plugin-brainstorm** agent for the full workflow from spec to deployment.

### Phase 0: Create Git Branch

**Before anything else, create a new branch for this plugin work.**

Generate a branch name using three random words in kebab-case. Examples:
- `mercury-purring-lion`
- `crystal-dancing-falcon`
- `amber-swift-turtle`

```bash
git checkout -b {branch_name}
git push -u origin {branch_name}
```

Tell the user the branch name you created.

### Phase 1: Gather Requirements

1. Invoke the canvas-sdk skill to have SDK documentation available
2. Ask the user to describe the problem they're trying to solve
3. Use AskUserQuestion to gather structured requirements:
   - Who experiences the problem?
   - What should trigger the plugin?
   - What should the plugin create or do?
4. Map answers to Canvas SDK concepts (events, effects)
5. Write a `plugin-spec.md` file with the specification
6. Wait for user approval before any implementation

If a `plugin-spec.md` already exists in the current directory, ask if they want to:
- Start fresh (replace it)
- Continue refining the existing spec

### Phase 2: Implement (after user approves spec)

**⚠️ CRITICAL: After the user approves the spec, you MUST run `canvas init` as the very first step:**

```bash
echo "{plugin_name}" | uv run canvas init
cd {plugin_name}
```

**Do NOT create files or directories manually.** The `canvas init` command creates the correct project structure. Only edit the files it generates.

After `canvas init` completes, commit the scaffolded plugin:

```bash
git add .
git commit -m "initialize {plugin_name} plugin scaffold"
git push
```

Then continue with the plugin-brainstorm agent workflow:
- Edit the generated protocol handler
- Write tests
- Deploy for UAT

## Git Commit Style

Use concise declarative voice for all commit messages:
- "add handler for vitals monitoring"
- "implement authentication for webhook endpoint"
- "fix threshold comparison logic"
- "update tests for edge cases"

Do NOT use: "Added...", "Adding...", "I added...", or similar.

## CPA Workflow

This command is **step 2** in the Canvas Plugin Assistant workflow:

```
/check-setup     →  Verify environment tools (uv, unbuffer)
/new-plugin      →  Create plugin from requirements  ← YOU ARE HERE
/deploy          →  Deploy to Canvas instance for UAT
/coverage        →  Check test coverage (aim for 90%)
/wrap-up         →  Final checklist before delivery
```

After implementation, guide the user to `/deploy` for UAT testing.
