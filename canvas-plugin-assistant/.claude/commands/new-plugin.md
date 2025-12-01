# New Plugin

Start the plugin brainstorming process to transform requirements into a concrete specification, then implement it.

## Instructions

Use the **plugin-brainstorm** agent for the full workflow from spec to deployment.

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

Then continue with the plugin-brainstorm agent workflow:
- Edit the generated protocol handler
- Write tests
- Deploy for UAT
