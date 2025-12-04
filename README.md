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

Clone this repository, then copy your target plugin's `.claude` directory to your plugin working directory (likely one or two levels up from the manifest file of your plugin). Here's how to do it with the Canvas plugin assistant, for example:

```bash
cp -r canvas-plugin-assistant/.claude /path/to/your/plugin/working/directory
```

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

**Slash Commands:**
| Command | Description |
|---------|-------------|
| `/new-plugin` | Start brainstorming a new plugin specification |
| `/analyze-instance` | Analyze Canvas instance configuration |
| `/deploy` | Deploy plugin and monitor logs |
| `/coverage` | Run tests with coverage, offer to improve if below 90% |
| `/wrap-up` | Final checklist before calling a plugin "done" |

See [canvas-plugin-assistant/README.md](canvas-plugin-assistant/README.md) for full documentation.
