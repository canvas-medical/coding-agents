---
name: instance-analyze
description: Analyze Canvas instance configuration to understand the target environment for plugin development
---

# Instance Analysis Skill

This skill provides guidance for analyzing a Canvas Medical instance's configuration before building plugins. The analysis informs plugin design decisions and identifies existing resources to leverage.

**Execution standard:** Run Python scripts and Python-based tooling with `uv run ...` (for scripts, `uv run python <script>.py ...`). Do not invoke bare `python` or `pip`.

## When to Use This Skill

Use this skill when:
- Starting a new plugin project and need to understand the target environment
- Need to know what teams, roles, or questionnaires exist for plugin integration
- Want to document current instance configuration for reference
- Checking what plugins are already installed

## Workflow

### Step 1: Understand Plugin Intent

First, ask the user about the plugin they intend to build. This helps identify if there's already a related plugin and tailors the analysis to their specific needs.

```json
{
  "questions": [
    {
      "question": "What plugin are you planning to build? Please describe its purpose briefly.",
      "header": "Plugin Intent",
      "options": [
        {"label": "Clinical Alert", "description": "Alerts for vitals, lab results, or clinical conditions"},
        {"label": "Workflow Automation", "description": "Automate tasks, appointments, or care coordination"},
        {"label": "Data Integration", "description": "Sync data with external systems or EHRs"},
        {"label": "Patient Engagement", "description": "Patient messaging, reminders, or education"}
      ],
      "multiSelect": false
    }
  ]
}
```

Store the user's response to use later when:
- Checking for existing plugins that might overlap or conflict
- Highlighting relevant teams, questionnaires, and note types in the report
- Making plugin development recommendations

### Step 2: Discover Available Instances

List the instances the person's Canvas Platform sign-in can reach:

```bash
uv run --with 'canvas>=1.2.0' python ${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py reachable
```

It prints one slug per line: every instance the person can view, including ones they cannot deploy to. If the command exits 1, show its `ERROR:` line (for example, not signed in: the person runs `uv run --with 'canvas>=1.2.0' canvas login` in their terminal) and stop.

### Step 3: Get Instance Information

Ask the user which instance to analyze using AskUserQuestion, dynamically populating the options with instances discovered in Step 2:

```json
{
  "questions": [
    {
      "question": "What Canvas instance should I analyze?",
      "header": "Instance",
      "options": [
        {"label": "<slug-1>", "description": "Reachable from your Canvas Platform sign-in"},
        {"label": "<slug-2>", "description": "Reachable from your Canvas Platform sign-in"},
        {"label": "...", "description": "One option per listed slug"}
      ],
      "multiSelect": false
    }
  ]
}
```

If the user provides an instance name with the command (e.g., `/analyze-instance plugin-testing`), use that directly without asking.

### Step 4: Fetch Configuration

Read each model from Canvas Platform, which serves what its last sweep of the instance collected. Run one command per model, with the slug from Step 3:

```bash
uv run --with 'canvas>=1.2.0' python ${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py records <slug> CareTeamRole
uv run --with 'canvas>=1.2.0' python ${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py records <slug> Team
uv run --with 'canvas>=1.2.0' python ${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py records <slug> Questionnaire
uv run --with 'canvas>=1.2.0' python ${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py records <slug> NoteType
uv run --with 'canvas>=1.2.0' python ${CLAUDE_PLUGIN_ROOT}/scripts/platform_session.py plugins <slug>
```

Each `records` command prints `{"instance", "model", "collected_at", "records": [{"key", "label", "fields", "collected_at"}]}`. A `plugins` command prints the instance's installed plugins. When a command exits 1, show its `ERROR:` line; an instance the person cannot reach answers "not found".

Map the output to the report sections:

| Report section | Source |
|---|---|
| Roles | `CareTeamRole` rows where `fields.active` is true; `label` and `key` (the coding system and code) |
| Teams | `Team` rows; `fields.members` (staff names) and `fields.responsibilities` |
| Questionnaires | `Questionnaire` rows (inactive ones are not collected); `fields.code` and `fields.use_case_in_charting` |
| Note Types | `NoteType` rows where `fields.is_active` is true; `fields.is_telehealth` and `fields.is_billable` |
| Appointment Types | `NoteType` rows where `fields.is_active` and `fields.is_scheduleable` are true; `fields.possible_durations` and `fields.is_telehealth` |
| Installed Plugins | `plugins` rows, with their `enabled` flag |

Each section carries its `collected_at`. For Roles, Teams, Note Types and Appointment Types, a `null` `collected_at` means Canvas Platform has not read that model on this instance yet; the report says "not read yet by Canvas Platform", never "none". For Questionnaires, an empty `records` with a `null` `collected_at` means either that Canvas Platform has not read them or that the instance has no active questionnaire; the report says "No active questionnaires found, or not read yet by Canvas Platform".

### Step 5: Generate Report

Create a comprehensive markdown report with this structure:

```markdown
# Canvas Instance Configuration Report

**Instance**: {slug}
**Generated**: {date}

Each section below ends with a line `As of the last Canvas Platform sweep: {collected_at}`, or, when `collected_at` is null, `Not read yet by Canvas Platform` (Questionnaires: `No active questionnaires found, or not read yet by Canvas Platform`).

## Summary

| Category | Count |
|----------|-------|
| Roles | X |
| Teams | X |
| Questionnaires | X |
| Note Types | X |
| Appointment Types | X |
| Installed Plugins | X |

## Roles

| Name | Coding |
|------|--------|
| ... | ... |

## Teams

| Name | Members | Responsibilities |
|------|---------|------------------|
| ... | count of staff | ... |

Team members appear as counts. List staff names only when the user asks for them.

## Questionnaires

| Name | Code | Use in charting |
|------|------|-----------------|
| ... | ... | ... |

## Note Types

| Name | Telehealth | Billable |
|------|------------|----------|
| ... | ... | ... |

## Appointment Types

| Name | Durations | Telehealth |
|------|-----------|------------|
| ... | ... | ... |

## Installed Plugins

| Name | Version | Status |
|------|---------|--------|
| ... | ... | Active/Inactive |

## Plugin Development Recommendations

Based on this configuration:

- **Available Teams for Task Assignment**: [list teams that could receive tasks]
- **Relevant Questionnaires**: [questionnaires that might be relevant to the use case]
- **Existing Plugins**: [any plugins that might conflict or complement new development]
```

### Step 6: Save Report

Save the report to `{workspace_dir}/.cpa-workflow-artifacts/instance-config-{instance}.md` (the instance slug), creating the directory if needed.

Tell the user the file path and offer to explain any section in detail.

## Integration with Plugin Spec

If `{workspace_dir}/.cpa-workflow-artifacts/plugin-spec.md` exists (where workspace_dir is the git repository root), read it and tailor the report to highlight:

- Teams that match the spec's task assignment needs
- Questionnaires relevant to the spec's data requirements
- Existing plugins that might overlap

## Important Notes

1. **Read-Only**: This analysis only reads configuration. It does not modify anything.

2. **Relevance Filtering**: When presenting the report, highlight items most relevant to the plugin being developed (if known from a previous brainstorming session).

3. **Plugin Conflicts**: Flag any installed plugins that might interact with what's being built.

## Example Interaction

**User**: "I need to analyze the plugin-testing instance before building a vitals alert plugin"

**You**: *[Uses AskUserQuestion to confirm instance]*

**User**: Confirms plugin-testing

**You**: *[Reads the instance's records and plugins from Canvas Platform]*

**You**: """I've analyzed the plugin-testing instance and saved the report to `.cpa-workflow-artifacts/instance-config-plugin-testing.md`.

Key findings relevant to your vitals alert plugin:
- **3 clinical teams** available for task assignment: Nursing, Care Coordination, Providers
- **No existing vitals-related plugins** installed - no conflicts expected
- **12 active questionnaires** - none specifically for vitals alerts

Would you like me to explain any section in more detail?"""

**User**: Yes / No
