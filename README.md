# Claude Code Plugins

Plugins for Claude Code are combinations of skills, agents, slash commands, and other context to improve the effectiveness and autonomy of Claude Code for specialized tasks.

You can learn more about how they work here: https://code.claude.com/docs/en/plugins

## Installation

```
/plugin marketplace add canvas-medical/coding-agents
/plugin install canvas-plugin-assistant@canvas-medical
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
| `/spec` | View or edit current plugin specification |
| `/coverage` | Run tests with coverage, offer to improve if below 90% |

See [canvas-plugin-assistant/README.md](canvas-plugin-assistant/README.md) for full documentation.
