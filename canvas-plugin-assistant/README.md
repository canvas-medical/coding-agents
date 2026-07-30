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

## Environment Variables

CPA uses three environment variables to manage workspace context. These must be set before starting Claude.

### Starting a CPA Session

```bash
# Navigate to your workspace directory first
cd /path/to/your/workspace

# Start Claude with CPA environment
export CPA_RUNNING=1 && export CPA_WORKSPACE_DIR=$(pwd) && claude
```

To work on an existing plugin:

```bash
export CPA_RUNNING=1 && export CPA_WORKSPACE_DIR=$(pwd) && export CPA_PLUGIN_DIR=$(pwd)/my-plugin && claude
```

### Variable Reference

| Variable              | Required          | Purpose                                                                                                                                             |
|-----------------------|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| `CPA_RUNNING`         | Always            | Set to `1` to enable CPA. Commands refuse to run without it.                                                                                        |
| `CPA_WORKSPACE_DIR`   | Always            | Root workspace directory. Used for storing workflow artifacts in `.cpa-workflow-artifacts/` before being moved within the created plugin directory. |
| `CPA_PLUGIN_DIR`      | For most commands | Specific plugin directory to work on. Must be a subdirectory of `CPA_WORKSPACE_DIR`.                                                                |
| `CPA_SECRET_FILEPATH` | No                | Override the default plugin secrets file path. See [Plugin Secrets](#plugin-secrets).                                                                |

### Command Requirements

Commands validate environment variables at startup using `validate_cpa_environment.py`:

All Python tooling in skills, agents, commands, and scripts must be executed via `uv run ...` (for scripts, use `uv run python <script>.py ...`). Do
not use bare `python` or `pip` in command workflows.

| Command                        | CPA_PLUGIN_DIR Required?                       |
|--------------------------------|------------------------------------------------|
| `:check-setup`                 | No (validates all variables)                   |
| `:new-plugin`                  | Optional (required for Phase 3 implementation) |
| `:coverage`                    | Yes                                            |
| `:security-review`             | Yes                                            |
| `:database-performance-review` | Yes                                            |
| `:deploy`                      | Yes                                            |
| `:wrap-up`                     | Yes                                            |

### Session End

CPA registers no session hooks: it writes nothing on `/exit`. Committing happens in the `:wrap-up` command, where untracked files are reviewed (and
scanned for secrets) and pushing is confirmed with you first.

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
- **companion-app-patterns**: UI, data-access, and packaging conventions for provider companion plugins (mobile-oriented modals on the `provider_companion_*` scopes)

### Slash Commands

Commands are namespaced with `cpa:` prefix when installed via the marketplace.

| Command                        | Description                                                 |
|--------------------------------|-------------------------------------------------------------|
| `:check-setup`                 | Verify environment tools (uv, unbuffer)                     |
| `:new-plugin`                  | Start brainstorming a new plugin specification              |
| `:create-icon`                 | Generate SVG icon and convert to 48x48 PNG for Applications |
| `:analyze-instance`            | Analyze Canvas instance configuration                       |
| `:deploy`                      | Deploy plugin and monitor logs                              |
| `:coverage`                    | Run tests with coverage, offer to improve if below 90%      |
| `:security-review`             | Comprehensive security audit with report                    |
| `:database-performance-review` | Database query optimization review with report              |
| `:wrap-up`                     | Final checklist before calling a plugin "done"              |
| `:run-evals`                   | Run eval suite to test review command accuracy              |

## Credentials Setup

Add your Canvas instance credentials to `~/.canvas/credentials.ini`:

```ini
[plugin-testing]
client_id = your_client_id
client_secret = your_client_secret
root_password = your_admin_password

[customer-instance]
client_id = ...
client_secret = ...
root_password = ...
```

- `client_id` / `client_secret`: For Canvas CLI (API access)
- `root_password`: For admin portal access (instance analyzer)

### Plugin Secrets

Plugins that declare `secrets` in `CANVAS_MANIFEST.json` need secret values for deployment. CPA reads these values from a per-instance JSON file and
passes them to the `canvas install` command — secret values are never exposed to Claude Code.

**Default location:**

```
~/.canvas/plugin-secrets/{instance}.json
```

**File format** (keyed by plugin name):

```json
{
  "my_plugin": {
    "API_KEY": "sk-...",
    "WEBHOOK_SECRET": "abc..."
  },
  "other_plugin": {
    "TOKEN": "xyz..."
  }
}
```

On each deployment, CPA automatically syncs the file with the variables declared in `CANVAS_MANIFEST.json` (the modern `variables` array; the deprecated `secrets` array is still read as a fallback): missing entries are added with empty values and stale entries are removed. Fill in the values before deploying.

**Custom file path:**

Set `CPA_SECRET_FILEPATH` to override the default location:

```bash
export CPA_SECRET_FILEPATH=/path/to/my-secrets.json
```

When set, this single file is used for all instances (the instance name is ignored for file resolution). This is useful for CI/CD pipelines or shared
secret stores.

If a secret value is empty or missing at deploy time, CPA skips it and shows a warning. The install still proceeds — the warning is informational.

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
    - Interactive commit: stages tracked changes only, reviews/secret-scans any untracked files before including them, and confirms before pushing

## Icon Generation

Canvas Medical plugin Applications require a 48x48 PNG icon. The `:create-icon` command generates SVG icons and automatically converts them to the
required format.

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

The command generates both SVG (vector) and PNG (48x48) versions, storing them in the plugin's `assets/` directory and updating the manifest
automatically.

## Plugin Complexity Guide

| Complexity | Files | When to Use                                |
|------------|-------|--------------------------------------------|
| Simple     | 1-2   | Single event → single effect (most common) |
| Medium     | 8-15  | Multiple handlers, API endpoints           |
| Complex    | 15+   | Interactive UI, LLM integration            |

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
│   ├── testing/               # Test authoring & coverage
│   └── companion-app-patterns/ # Provider companion (mobile) plugin conventions
├── agents/
│   ├── plugin-brainstorm.md   # Requirements gathering
│   ├── instance-analyzer.md   # Instance configuration analysis
│   └── deploy-uat.md          # Deployment and testing
└── scripts/
    ├── convert_svg_to_png.py      # SVG to 48x48 PNG conversion
    ├── compare_review_results.py  # Eval comparison using Anthropic API
    ├── get_plugin_dir.py          # Workspace directory resolution
    └── verify_plugin_structure.py # Check the plugin structure

```

## Workflow Artifacts

Commands and agents write their working files to `.cpa-workflow-artifacts/` in the workspace directory. Every file is scratch space for the session
that produced it, kept out of git via the plugin repo's `.gitignore`. Each report has a fixed name, so a re-run replaces the previous one instead of
piling up.

**Artifacts saved:**
| File | Purpose | Read by |
|------|---------|---------|
| `plugin-spec.md` | Plugin requirements and architecture decisions | `:new-plugin`, deploy-uat, instance-analyze |
| `wrap-up-report.md` | Wrap-up checklist results | `:new-plugin` (marks the plugin as shipped) |
| `security-review.md` | Security audit findings and recommendations | You |
| `db-performance-review.md` | Database query optimization findings | You |
| `coverage-report.md` | Test coverage report | You |
| `instance-config-{hostname}.md` | Instance configuration analysis | You |
| `eval-results-{timestamp}.md` | Eval suite results | You |
| `{case_name}-security-review.md` | Per-case security review (evals) | `compare_review_results.py` |
| `{case_name}-database-review.md` | Per-case database review (evals) | `compare_review_results.py` |

Delete the directory whenever you want: nothing outside the session that wrote a file depends on it.

## Evals

CPA includes an eval framework to verify that `:security-review` and `:database-performance-review` commands correctly detect known issues.

**Blind evaluation:** Eval case names are intentionally non-descriptive (`case_001`, `case_002`, etc.) to avoid biasing reviews. CPA is denied read
access to `expected.json` and `case_index.md`.

**Running evals:**

```bash
# Set API key first
export EVALS_ANTHROPIC_API_KEY=sk-ant-...

# Run :run-evals command in Claude Code
```

**Adding new evals:**
See `evals/README.md` for instructions. Use `case_index.md` (human-readable only) to track what each case tests.

## Tests

CPA includes a comprehensive test suite for the scripts in `scripts/`. Tests are located in `tests/canvas-plugin-assistant/scripts/` at the repository
root.

### Running Tests

```bash
# Compact view
uv run pytest tests/canvas-plugin-assistant/scripts/ -q

# Compact view + coverage
uv run pytest tests/canvas-plugin-assistant/scripts/ --cov=canvas-plugin-assistant/scripts --cov-report=term-missing -q

# Standard view + coverage
uv run pytest tests/canvas-plugin-assistant/scripts/ --cov=canvas-plugin-assistant/scripts --cov-report=term-missing
```

### Tested Modules

| Module                        | Description                         |
|-------------------------------|-------------------------------------|
| `compare_review_results.py`   | Eval comparison using Anthropic API         |
| `constants.py`                | CPA environment variable constants          |
| `convert_svg_to_png.py`       | SVG to 48x48 PNG conversion                 |
| `get_plugin_dir.py`           | Plugin directory resolution                 |
| `mcp_canvas_installer.py`     | MCP server for plugin install with secrets  |
| `secret_requester.py`         | Plugin secret retrieval from local files    |
| `validate_cpa_environment.py` | Environment variable validation             |
| `verify_plugin_structure.py`  | Plugin structure verification               |

### Test Guidelines

Tests follow strict pytest guidelines with 100% coverage target:

- Use `pytest.mark.parametrize` for multiple scenarios
- Use `capsys` fixture for capturing print output
- Verify all mocks with `mock_calls` property
- Follow naming convention: `test_<method>__<case>`
