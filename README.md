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
- API security review for authentication/authorization
- Unit test authoring with 90% coverage target
- Instance configuration analysis
- Deployment with log monitoring

**Slash Commands** (prefixed with `cpa:` when installed via marketplace):
| Command | Description |
|---------|-------------|
| `:check-setup` | Verify environment tools (uv, unbuffer, canvas CLI) |
| `:new-plugin` | Start brainstorming a new plugin specification |
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
