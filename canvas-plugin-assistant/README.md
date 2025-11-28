# Canvas Plugin Development Assistant

A Claude Code plugin that helps solutions consultants build Canvas Medical plugins through guided dialogue and automated workflows.

## Quick Start

Run `/new-plugin` to start a guided brainstorming session that asks clarifying questions and produces a plugin specification for your approval.

## What This Assistant Does

### Agents

**plugin-brainstorm** - Transform vague requirements into concrete plugin specifications:
- Asks structured questions using the chip interface
- Maps requirements to Canvas SDK concepts (events, effects, data models)
- Recommends appropriate architecture complexity
- Produces a `plugin-spec.md` for review before implementation

**instance-analyzer** - Understand Canvas instance configuration:
- Documents roles, teams, questionnaires, note types, appointment types
- Lists installed plugins to identify conflicts or opportunities
- Generates `instance-config-{hostname}.md` report
- Tailors findings to your plugin spec if available

**deploy-uat** - Deploy plugins and guide user acceptance testing:
- Pre-deployment validation (manifest, tests)
- Deploy to dev/staging/production environments
- Real-time log monitoring during testing
- UAT checklist and results documentation

### Skills
- **canvas-sdk**: Complete Canvas SDK documentation (~20k lines)
- **plugin-patterns**: Architecture patterns and best practices
- **api-security**: Security review for API handlers (authentication, authorization)
- **testing**: Unit test authoring, mocking patterns, and coverage checking

### Slash Commands

| Command | Description |
|---------|-------------|
| `/new-plugin` | Start brainstorming a new plugin specification |
| `/analyze-instance` | Analyze Canvas instance configuration |
| `/deploy` | Deploy plugin and monitor logs |
| `/spec` | View or edit current plugin specification |
| `/coverage` | Run tests with coverage, offer to improve if below 90% |

## Credentials Setup

Add your Canvas instance credentials to `~/.canvas/credentials.ini`:

```ini
[plugin-testing]
client_id=your_client_id
client_secret=your_client_secret
root_password=your_admin_password

[customer-instance]
client_id=...
client_secret=...
root_password=...
```

- `client_id` / `client_secret`: For Canvas CLI (API access)
- `root_password`: For admin portal access (instance analyzer)

## Workflow

1. **Describe the Problem**
   - Tell Claude what the customer needs
   - Answer clarifying questions about users, triggers, and outcomes

2. **Review the Specification**
   - Claude produces a plugin specification document
   - Includes events, effects, data requirements, and architecture

3. **Build the Plugin**
   - Use the specification to implement the plugin
   - Reference the skills for SDK details and patterns

4. **Test and Deploy**
   - Deploy to test instance
   - Perform user acceptance testing

## Plugin Complexity Guide

| Complexity | Files | When to Use |
|------------|-------|-------------|
| Simple | 1-2 | Single event → single effect (most common) |
| Medium | 8-15 | Multiple handlers, API endpoints |
| Complex | 15+ | Interactive UI, LLM integration |

~75% of real-world plugins are simple implementations.

## Example Session

```
You: I need to build a plugin for a customer that wants to remind staff
     to call patients before fasting lab appointments.

Claude: I can help design that! Let me understand the requirements...

        When is the reminder needed - when the lab is first ordered,
        or closer to the appointment date?

You: When the lab is ordered, so they can schedule the call.

Claude: Got it. And which staff should receive the reminder -
        a specific team like scheduling, or the ordering provider?

You: The scheduling team.

Claude: Perfect. Here's what I'm thinking:

        **Trigger**: LAB_ORDER_COMMAND__POST_COMMIT
        **Condition**: Lab has fasting requirement checked
        **Effect**: Create task for scheduling team

        This is a simple plugin - just one event handler.

        Let me write up the full specification...

[Claude produces plugin-spec.md with full details]
```

## Files Included

```
.claude/
├── settings.json              # Permission configuration
├── commands/
│   ├── new-plugin.md          # /new-plugin
│   ├── analyze-instance.md    # /analyze-instance
│   ├── deploy.md              # /deploy
│   ├── spec.md                # /spec
│   └── coverage.md            # /coverage
├── skills/
│   ├── canvas-sdk/            # SDK documentation
│   │   ├── SKILL.md
│   │   └── coding_agent_context.txt
│   ├── plugin-patterns/       # Architecture patterns
│   │   ├── SKILL.md
│   │   └── patterns_context.txt
│   ├── api-security/          # API security review
│   │   ├── SKILL.md
│   │   └── security_context.txt
│   └── testing/               # Test authoring & coverage
│       ├── SKILL.md
│       └── testing_context.txt
└── agents/
    ├── plugin-brainstorm.md   # Requirements gathering
    ├── instance-analyzer.md   # Instance configuration analysis
    └── deploy-uat.md          # Deployment and testing
```
