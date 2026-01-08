---
name: canvas-sdk
description: Canvas SDK reference and documentation access for Canvas platform capabilities, API usage, implementation patterns, and testing
---

# Canvas SDK Reference

This skill provides comprehensive documentation for the Canvas Medical SDK, enabling development of Canvas plugins.

## When to Use This Skill

Use this skill when you need information about:
- Canvas SDK classes, methods, and APIs
- Event types and their context structures
- Effect types and their payloads
- Data models (Patient, Condition, Medication, etc.)
- Handler types (BaseProtocol, SimpleAPI, Application, CronTask)
- Canvas CLI commands
- Plugin manifest structure

## Key Documentation Sections

### Handlers
- **BaseProtocol**: Event-driven handlers responding to Canvas events
- **SimpleAPI**: HTTP endpoints and WebSocket handlers
- **Application**: UI applications launched from the app drawer
- **CronTask**: Scheduled task execution
- **ActionButton**: UI buttons in notes and patient headers

### Events
- Record lifecycle events (patient, appointment, lab results)
- Command lifecycle events (prescribe, diagnose, assess, etc.)
- Search result events for customizing dropdowns

### Effects
- AddBannerAlert: Display alerts in patient timeline
- AddTask: Create tasks for staff
- LaunchModalEffect: Open modals/panels
- Patient metadata effects
- Billing effects

### Data Models
- Patient, Appointment, LabOrder, Medication
- Condition, AllergyIntolerance, Observation
- Note, Task, Staff, Team

## Usage

**IMPORTANT**: The full SDK documentation is bundled with this skill. **DO NOT download, curl, or fetch remote files.**

The context file `coding_agent_context.txt` is located **in the same directory as this SKILL.md file**.

When you read this skill, note the path to this SKILL.md file, then read `coding_agent_context.txt` from that same directory.

For example, if this SKILL.md is at:
```
/some/path/skills/canvas-sdk/SKILL.md
```

Then read:
```
/some/path/skills/canvas-sdk/coding_agent_context.txt
```

To use this skill:
1. **Read `coding_agent_context.txt` from this skill's directory** - it already exists locally
2. Search the file for specific class names, event types, or effect types
3. Use the documentation to understand Canvas SDK capabilities

The context file contains ~20000 lines of comprehensive SDK documentation including all handlers, events, effects, and data models.

**NEVER attempt to curl or download coding_agent_context.txt - it is already bundled here.**
