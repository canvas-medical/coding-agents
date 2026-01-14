# Canvas Plugin Development Assistant

A Claude Code plugin that helps solutions consultants build Canvas Medical plugins through guided dialogue and automated workflows.

## Installation

```shell
# Add the Canvas Medical marketplace
/plugin marketplace add canvas-medical/coding-agents

# Install this plugin
/plugin install cpa@canvas-medical
```

After installation, enable the plugin:

```shell
/plugin
```

Navigate to the **Installed** tab and enable `cpa@canvas-medical`.

Once enabled, commands are available with a namespace prefix (e.g., `/cpa:new-plugin`).

## Quick Start

Run `/cpa:new-plugin` to start a guided brainstorming session that asks clarifying questions and produces a plugin specification for your approval.

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
- **icon-generation**: Generate SVG icons and convert to 48x48 PNG for Canvas plugin Applications

### Slash Commands

Commands are namespaced with `cpa:` prefix when installed via the marketplace.

| Command | Description |
|---------|-------------|
| `:check-setup` | Verify environment tools (uv, unbuffer) |
| `:new-plugin` | Start brainstorming a new plugin specification |
| `:create-icon` | Generate SVG icon and convert to 48x48 PNG for Applications |
| `:analyze-instance` | Analyze Canvas instance configuration |
| `:deploy` | Deploy plugin and monitor logs |
| `:coverage` | Run tests with coverage, offer to improve if below 90% |
| `:security-review` | Comprehensive security audit with report |
| `:database-performance-review` | Database query optimization review with report |
| `:wrap-up` | Final checklist before calling a plugin "done" |
| `:run-evals` | Run eval suite to test review command accuracy |

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

### Evals Setup

To run `:run-evals`, set the `EVALS_ANTHROPIC_API_KEY` environment variable:

```bash
export EVALS_ANTHROPIC_API_KEY=sk-ant-...
```

This key is used by the comparison script to evaluate whether review commands correctly detected expected issues.

## Workflow

```
:check-setup      →  Verify environment tools (uv, unbuffer)
:new-plugin       →  Create plugin from requirements
:deploy           →  Deploy to Canvas instance for UAT
:coverage                    →  Check test coverage (aim for 90%)
:security-review             →  Comprehensive security audit
:database-performance-review →  Database query optimization
:wrap-up                     →  Final checklist before delivery
```

1. **Check Setup** (`:check-setup`)
   - Verify uv and unbuffer are installed

2. **Describe the Problem** (`:new-plugin`)
   - Tell Claude what the customer needs
   - Answer clarifying questions about users, triggers, and outcomes
   - Review and approve the plugin specification
   - Plugin is scaffolded, implemented, and tested

3. **Deploy and Test** (`:deploy`)
   - Deploy to test instance
   - Perform user acceptance testing with real-time log monitoring

4. **Quality Checks** (`:coverage`, `:security-review`, `:database-performance-review`)
   - Verify test coverage meets 90% threshold
   - Run a comprehensive security audit
   - Run a database performance audit

5. **Wrap Up** (`:wrap-up`)
   - Final checklist: security, DB performance, coverage, README
   - Git commit and push

## Icon Generation

Canvas Medical plugin Applications require a 48x48 PNG icon. The `:create-icon` command generates SVG icons and automatically converts them to the required format.

**When icons are needed:**
- Any plugin with an `Application` component (interactive UI panels)
- Icons are automatically generated during `:new-plugin` workflow for Application plugins
- Icons are verified during `:wrap-up` checklist

**Manual icon generation:**
```bash
# In a plugin directory
/cpa:create-icon "medical chart with checkmark"

# Or just ask Claude to create an icon
"I need an icon for a patient scheduling application"
```

**Icon requirements:**
- 48x48 PNG format (automatically generated)
- Saved to `{plugin_name}/assets/` directory
- Referenced in CANVAS_MANIFEST.json as `"icon": "assets/icon-name.png"`
- Professional, healthcare-appropriate design

The command generates both SVG (vector) and PNG (48x48) versions, storing them in the plugin's `assets/` directory and updating the manifest automatically.

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
│   ├── check-setup.md         # :check-setup
│   ├── new-plugin.md          # :new-plugin
│   ├── create-icon.md         # :create-icon
│   ├── analyze-instance.md    # :analyze-instance
│   ├── deploy.md              # :deploy
│   ├── coverage.md            # :coverage
│   ├── security-review.md     # :security-review
│   ├── database-performance-review.md # :database-performance-review
│   ├── wrap-up.md             # :wrap-up
│   └── run-evals.md           # :run-evals
├── evals/
│   ├── case_001/              # Eval cases (non-descriptive names for blind testing)
│   ├── case_002/
│   ├── case_003/
│   └── case_index.md          # Case descriptions (CPA denied access)
├── skills/
│   ├── canvas-sdk/            # SDK documentation
│   ├── plugin-patterns/       # Architecture patterns
│   ├── icon-generation/       # SVG icon generation and PNG conversion
│   ├── plugin-api-server-security/  # SimpleAPI/WebSocket auth
│   ├── fhir-api-client-security/    # FHIR API token security
│   ├── database-performance/  # N+1 query detection
│   └── testing/               # Test authoring & coverage
├── agents/
│   ├── plugin-brainstorm.md   # Requirements gathering
│   ├── instance-analyzer.md   # Instance configuration analysis
│   └── deploy-uat.md          # Deployment and testing
├── hooks/
│   └── hooks.json             # SessionEnd hook for cost tracking
├── scripts/
    ├── convert_svg_to_png.py      # SVG to 48x48 PNG conversion
│   ├── export_session_history.py  # Session history export
│   ├── compare_review_results.py  # Eval comparison using Anthropic API
│   ├── cost_logger.py             # SessionEnd hook script for cost tracking
│   ├── aggregate_costs.py         # Cost analysis and reporting
│   ├── verify_plugin_structure.py # Check the plugin structure
│   └── update_pricing.py          # Model pricing updater
└── model_costs.json               # Claude model pricing data

```

## Workflow Artifacts

CPA saves workflow artifacts to `.cpa-workflow-artifacts/` at the git repository root. These artifacts are critical for:

**Training & Feedback**
- Session histories capture the full dialogue, decisions made, and problems solved
- Reviewing past sessions helps users learn patterns and improve their plugin development skills
- Artifacts provide concrete examples for onboarding new team members

**Continuous Improvement**
- Plugin specs document requirements gathering patterns that worked well
- Security reviews highlight common vulnerabilities to watch for
- Session histories help identify where CPA guidance could be improved

**Cost Tracking & Budgeting**
- Automatic session cost tracking helps monitor AI usage and budget
- Aggregated cost data enables project cost analysis across multiple sessions
- Cost breakdown by model type (Opus, Sonnet, Haiku) informs model selection decisions

**Artifacts saved:**
| File | Purpose |
|------|---------|
| `plugin-spec.md` | Plugin requirements and architecture decisions |
| `coverage-report-{timestamp}.md` | Test coverage report |
| `security-review-{timestamp}.md` | Security audit findings and recommendations |
| `db-performance-review-{timestamp}.md` | Database query optimization findings |
| `claude-history-{sessionId}.txt` | Complete session transcript |
| `eval-results-{timestamp}.md` | Eval suite results |
| `{case_name}-security-review.md` | Per-case security review (evals) |
| `{case_name}-database-review.md` | Per-case database review (evals) |
| `costs/{session-id}.json` | Individual session cost data (tokens, duration, cost) |
| `costs/{workspace-directory}.json` | Aggregated cost summary for all sessions in the workspace |

**Cost Tracking Details:**

CPA automatically tracks session costs via a SessionEnd hook. When a session ends, cost data is saved to `.cpa-workflow-artifacts/costs/` at the git repository root:

- **Individual session files** (`{session-id}.json`): Token usage (input, output, cache read/write), model used, session duration, and calculated cost in USD
- **Aggregated files** (`{workspace-directory}.json`): Summary of all sessions in the workspace (git repository) with total cost, token usage, and session list

Use `scripts/aggregate_costs.py` to analyze costs:
```bash
# View cost summary
./scripts/aggregate_costs.py .cpa-workflow-artifacts/costs/

# Export to CSV
./scripts/aggregate_costs.py --format csv .cpa-workflow-artifacts/costs/ > costs.csv

# Filter by date or model
./scripts/aggregate_costs.py --since 2026-01-01 --model sonnet-4-5 .cpa-workflow-artifacts/costs/
```

Update pricing data with `scripts/update_pricing.py`:
```bash
  export ANTHROPIC_API_KEY=your_api_key_here
./scripts/update_pricing.py
```

**Keep these artifacts.** They're valuable for retrospectives, training, project budgeting, and improving CPA itself.

## Evals

CPA includes an eval framework to verify that `:security-review` and `:database-performance-review` commands correctly detect known issues.

**Blind evaluation:** Eval case names are intentionally non-descriptive (`case_001`, `case_002`, etc.) to avoid biasing reviews. CPA is denied read access to `expected.json` and `case_index.md`.

**Running evals:**
```bash
# Set API key first
export EVALS_ANTHROPIC_API_KEY=sk-ant-...

# Run :run-evals command in Claude Code
```

**Adding new evals:**
See `evals/README.md` for instructions. Use `case_index.md` (human-readable only) to track what each case tests.
