# New Plugin

Start the plugin brainstorming process to transform requirements into a concrete specification.

## Instructions

Use the **plugin-brainstorm** agent to guide the user through requirements gathering.

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
