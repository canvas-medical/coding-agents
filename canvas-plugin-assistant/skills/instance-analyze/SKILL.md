---
name: instance-analyze
description: Analyze Canvas instance configuration to understand the target environment for plugin development
---

# Instance Analysis Skill

This skill provides guidance for analyzing a Canvas Medical instance's configuration before building plugins. The analysis informs plugin design decisions and identifies existing resources to leverage.

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

Read credentials from `~/.canvas/credentials.ini` to discover configured instances:

```bash
cat ~/.canvas/credentials.ini
```

Parse the file to extract all section names (instance names). Each section represents a configured Canvas instance:

```ini
[instance-name]
client_id=xxx
client_secret=yyy
root_password=zzz
```

### Step 3: Get Instance Information

Ask the user which instance to analyze using AskUserQuestion, dynamically populating the options with instances discovered in Step 2:

```json
{
  "questions": [
    {
      "question": "What Canvas instance should I analyze?",
      "header": "Instance",
      "options": [
        {"label": "<instance-1>", "description": "From credentials.ini"},
        {"label": "<instance-2>", "description": "From credentials.ini"},
        {"label": "...", "description": "Add all discovered instances"}
      ],
      "multiSelect": false
    }
  ]
}
```

If the user provides an instance name with the command (e.g., `/analyze-instance plugin-testing`), use that directly without asking.

After the user selects an instance, verify it has `root_password` configured. If missing, tell the user:

> Please add `root_password` to your `~/.canvas/credentials.ini` under the `[{instance}]` section:
> ```ini
> [plugin-testing]
> client_id=your_client_id
> client_secret=your_client_secret
> root_password=your_admin_password
> ```

### Step 4: Fetch Configuration

Use the scraper script to extract configuration from the admin portal:

```bash
uv run python ${CLAUDE_PLUGIN_ROOT}/scripts/scrape_canvas_instance.py <instance_name> <root_password>
```

This script uses browser automation to:

1. **Login to Admin Portal**
   - Navigate to `https://{hostname}.canvasmedical.com/admin/`
   - Username: `root`
   - Password: `root_password` from credentials.ini

2. **Extract Configuration** from these pages:
   - `/admin/api/careteamrole/` - Roles (where `is active` is true)
   - `/admin/api/team/` - Teams
   - `/admin/api/questionnaire/` - Questionnaires (where `is active` is true)
   - `/admin/api/notetype/` - Note types (where `is active` is true)
   - `/admin/api/notetype/` - Appointment types (where `is active` and `is schedulable` are true)
   - `/admin/plugin_io/plugin/` - Installed plugins

### Step 5: Generate Report

Create a comprehensive markdown report with this structure:

```markdown
# Canvas Instance Configuration Report

**Instance**: {hostname}.canvasmedical.com
**Generated**: {date}

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

| Name | Description |
|------|-------------|
| ... | ... |

## Teams

| Name | Members | Description |
|------|---------|-------------|
| ... | ... | ... |

## Questionnaires

| Name | Code | Status |
|------|------|--------|
| ... | ... | Active/Inactive |

## Note Types

| Name | Category |
|------|----------|
| ... | ... |

## Appointment Types

| Name | Duration | Category |
|------|----------|----------|
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

Save the report to `instance-config-{hostname}.md` in the current working directory.

Tell the user the file path and offer to explain any section in detail.

## Integration with Plugin Spec

If `{workspace_dir}/.cpa-workflow-artifacts/plugin-spec.md` exists (where workspace_dir is the git repository root), read it and tailor the report to highlight:

- Teams that match the spec's task assignment needs
- Questionnaires relevant to the spec's data requirements
- Existing plugins that might overlap

## Important Notes

1. **Credentials Security**: Never log or store credentials. Use them only for the session.

2. **Read-Only**: This analysis only reads configuration. It does not modify anything.

3. **Relevance Filtering**: When presenting the report, highlight items most relevant to the plugin being developed (if known from a previous brainstorming session).

4. **Plugin Conflicts**: Flag any installed plugins that might interact with what's being built.

## Example Interaction

**User**: "I need to analyze the plugin-testing instance before building a vitals alert plugin"

**You**: *[Uses AskUserQuestion to confirm instance]*

**User**: Confirms plugin-testing

**You**: *[Reads credentials and runs scraper script]*

**You**: """I've analyzed the plugin-testing instance and saved the report to `instance-config-plugin-testing.md`.

Key findings relevant to your vitals alert plugin:
- **3 clinical teams** available for task assignment: Nursing, Care Coordination, Providers
- **No existing vitals-related plugins** installed - no conflicts expected
- **12 active questionnaires** - none specifically for vitals alerts

Would you like me to explain any section in more detail?"""

**User**: Yes / No