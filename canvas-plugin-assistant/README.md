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
- **plugin-api-server-security**: Security review for SimpleAPI/WebSocket handlers (when plugin is the server)
- **fhir-api-client-security**: Security review for FHIR API usage (token scopes, patient-scoped tokens)
- **database-performance**: N+1 query detection and Django ORM optimization
- **testing**: Unit test authoring, mocking patterns, and coverage checking

### Slash Commands

| Command | Description |
|---------|-------------|
| `/check-setup` | Verify environment tools (uv, unbuffer) |
| `/new-plugin` | Start brainstorming a new plugin specification |
| `/analyze-instance` | Analyze Canvas instance configuration |
| `/deploy` | Deploy plugin and monitor logs |
| `/coverage` | Run tests with coverage, offer to improve if below 90% |
| `/security-review-cpa` | Comprehensive security audit with report |
| `/wrap-up` | Final checklist before calling a plugin "done" |

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

```
/check-setup      →  Verify environment tools (uv, unbuffer)
/new-plugin       →  Create plugin from requirements
/deploy           →  Deploy to Canvas instance for UAT
/coverage         →  Check test coverage (aim for 90%)
/security-review-cpa  →  Comprehensive security audit
/wrap-up          →  Final checklist before delivery
```

1. **Check Setup** (`/check-setup`)
   - Verify uv and unbuffer are installed

2. **Describe the Problem** (`/new-plugin`)
   - Tell Claude what the customer needs
   - Answer clarifying questions about users, triggers, and outcomes
   - Review and approve the plugin specification
   - Plugin is scaffolded, implemented, and tested

3. **Deploy and Test** (`/deploy`)
   - Deploy to test instance
   - Perform user acceptance testing with real-time log monitoring

4. **Quality Checks** (`/coverage`, `/security-review-cpa`)
   - Verify test coverage meets 90% threshold
   - Run comprehensive security audit

5. **Wrap Up** (`/wrap-up`)
   - Final checklist: security, DB performance, coverage, README
   - Git commit and push

## Plugin Complexity Guide

| Complexity | Files | When to Use |
|------------|-------|-------------|
| Simple | 1-2 | Single event → single effect (most common) |
| Medium | 8-15 | Multiple handlers, API endpoints |
| Complex | 15+ | Interactive UI, LLM integration |

~75% of real-world plugins are simple implementations.

## Files Included

```
.claude/
├── settings.json              # Permission configuration
├── commands/
│   ├── check-setup.md         # /check-setup
│   ├── new-plugin.md          # /new-plugin
│   ├── analyze-instance.md    # /analyze-instance
│   ├── deploy.md              # /deploy
│   ├── coverage.md            # /coverage
│   ├── security-review.md     # /security-review-cpa
│   └── wrap-up.md             # /wrap-up
├── skills/
│   ├── canvas-sdk/            # SDK documentation
│   ├── plugin-patterns/       # Architecture patterns
│   ├── plugin-api-server-security/  # SimpleAPI/WebSocket auth
│   ├── fhir-api-client-security/    # FHIR API token security
│   ├── database-performance/  # N+1 query detection
│   └── testing/               # Test authoring & coverage
├── agents/
│   ├── plugin-brainstorm.md   # Requirements gathering
│   ├── instance-analyzer.md   # Instance configuration analysis
│   └── deploy-uat.md          # Deployment and testing
├── scripts/
│   └── export-session-history.py  # Session history export
└── artifacts/                 # Generated reports and specs
```
