---
name: plugin-patterns
description: Canvas plugin architecture patterns, best practices, and implementation templates
---

# Canvas Plugin Patterns

This skill provides architectural patterns, best practices, and implementation guidance for building Canvas plugins. It supplements the SDK reference with practical patterns learned from real-world plugins.

## When to Use This Skill

Use this skill when you need:
- Plugin architecture recommendations
- Implementation patterns and templates
- Best practices for testing, error handling, security
- Guidance on plugin complexity decisions
- Common anti-patterns to avoid
- Implementation of:
  - AWS S3
  - LLM (Anthropic Claude, OpenAI ChatGPT, Google Gemini)
  - Twilio
  - SendGrid
  - Extend.ai

## Quick Reference

Reference the `patterns_context.txt` file for detailed patterns and examples.

> **Effects are applied only after the handler returns, as a single batch capped at 64 MB (gRPC).** A handler that emits effects proportional to an unbounded queryset (all providers/patients/appointments) can exceed that ceiling, and the entire batch is **silently dropped** — the plugin logs the work as done but nothing lands. Scaling the worker does not fix this; it is a batching problem. Chunk large fan-out through a queue + cron (one small effect batch per invocation). See the **database-performance** skill (§"Canvas Execution Limits") for the full pattern, plus the write-amplification and over-hydration/memory failure modes that don't show up as N+1.
