---
name: analyze-instance
description: Analyze a Canvas instance's configuration to understand the target environment.
---

# Analyze Instance

Analyze a Canvas instance's configuration to understand the target environment.

## Instructions

The analysis reads the instance from Canvas Platform with the person's `canvas login` sign-in.

Use the **instance-analyzer** agent to analyze the Canvas instance configuration. The agent will use the **instance-analyze** skill for detailed guidance.

If the user provides an instance name with the command (e.g., `/analyze-instance plugin-testing`), pass that to the agent as the target instance.
