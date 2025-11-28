# View/Edit Plugin Specification

View or edit the current plugin specification.

## Instructions

1. Check if `plugin-spec.md` exists in the current directory
2. If it exists:
   - Read and display a summary of the spec
   - Ask what the user wants to do (view full spec, edit section, start fresh)
3. If it doesn't exist:
   - Tell the user no spec exists yet
   - Offer to run `/new-plugin` to create one

## Actions

When user wants to edit, use AskUserQuestion:

```json
{
  "questions": [
    {
      "question": "What would you like to do with the spec?",
      "header": "Action",
      "options": [
        {"label": "View full spec", "description": "Display the complete specification"},
        {"label": "Edit trigger", "description": "Change the event or conditions"},
        {"label": "Edit effects", "description": "Change what the plugin creates"},
        {"label": "Edit architecture", "description": "Change complexity or components"},
        {"label": "Start fresh", "description": "Delete and create a new spec"}
      ],
      "multiSelect": false
    }
  ]
}
```

## Summary Format

When displaying a summary, show:

```
Plugin: {name}
Trigger: {event_type}
Effects: {effect_list}
Complexity: {simple/medium/complex}
```
