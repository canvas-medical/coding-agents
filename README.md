# Claude Code Plugins

Plugins for Claude Code are combinations of skills, agents, slash commands, and other context to improve the effectiveness and autonomy of Claude Code for specialized tasks.

You can learn more about how they work here: https://code.claude.com/docs/en/plugins

## Requirements

These plugins requires a recent version of Claude Code. Always update claude to ensure you have the latest features.

```bash
claude update
```

Install `uv` for Python package management:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For log monitoring during deployment and user acceptance testing, install `expect` (provides the `unbuffer` command):

```bash
brew install expect
```

## Installation

Add the marketplace and install plugins using Claude Code's plugin system:

```shell
# Add the Canvas Medical marketplace
/plugin marketplace add canvas-medical/coding-agents

# Install a plugin (e.g., cpa)
/plugin install cpa@canvas-medical
```

After installation, enable the plugin:

```shell
/plugin
```

Navigate to the **Installed** tab and enable the plugin. Once enabled, plugin commands are available with a namespace prefix (e.g., `/cpa:new-plugin`).

To view all available commands:

```shell
/help
```

To turn on the auto-update (recommanded):
```shell
/plugin
```
Go to `Marketplaces` with Tab key, then select `canvas-medical` with the Arrows keys and press Enter, then select `Enable auto-update` and press Enter.


## Available Plugins

### canvas-plugin-assistant

Guided Canvas plugin development with SDK reference, patterns, security review, and deployment workflows.

**Features:**
- Brainstorm plugin requirements through guided dialogue
- Canvas SDK documentation (~20k lines) always available
- Architecture patterns based on handler count complexity
- Icon generation for Application plugins (SVG to 48x48 PNG)
- API security review for authentication/authorization
- Unit test authoring with 90% coverage target
- Instance configuration analysis
- Deployment with log monitoring

**Slash Commands** (prefixed with `cpa:` when installed via marketplace):
| Command | Description |
|---------|-------------|
| `:check-setup` | Verify environment tools (uv, unbuffer, canvas CLI) |
| `:new-plugin` | Start brainstorming a new plugin specification |
| `:create-icon` | Generate SVG icon and convert to 48x48 PNG for Applications |
| `:analyze-instance` | Analyze Canvas instance configuration |
| `:deploy` | Deploy plugin and monitor logs |
| `:coverage` | Run tests with coverage, offer to improve if below 90% |
| `:security-review` | Comprehensive security audit (API auth, FHIR tokens, secrets) |
| `:database-performance-review` | Review for N+1 queries and ORM optimization |
| `:wrap-up` | Final checklist before calling a plugin "done" |
| `:run-evals` | Execute eval cases to verify review commands |

**Workflow Artifacts:**
Review commands save timestamped reports to `.cpa-workflow-artifacts/` at the git repository root. These reports are useful for code review and audit trails.

See [canvas-plugin-assistant/README.md](canvas-plugin-assistant/README.md) for full documentation.

### pytest-forge

Generate and validate pytest unit tests following strict guidelines with 100% code coverage.

**Features:**
- Automated test generation from Python source files
- Test validation against custom guidelines
- Intelligent test improvement suggestions
- Project setup with pytest and coverage tools
- Auto-configuration check at session start for unconfigured projects

**Slash Commands** (prefixed with `pytest:` when installed via marketplace):
| Command | Description |
|---------|-------------|
| `:setup` | Configure pytest and coverage tools for your project |
| `:generate-tests` | Generate comprehensive tests for a Python source file |
| `:validate-tests` | Check tests for guideline compliance and coverage gaps |
| `:improve-tests` | Analyze and enhance existing tests |

**Testing Guidelines Enforced:**
- Strict naming conventions (`test_method_name`, `test_method_name__case`)
- Standard variable names (`tested`, `result`, `expected`, `exp_*`)
- Mock verification using `mock_calls` instead of `assert_called_with()`
- `side_effect` preferred over `return_value`
- 100% code coverage requirement

See [pytest-forge/README.md](pytest-forge/README.md) for full documentation.
