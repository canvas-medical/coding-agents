---
name: custom-data-patterns
description: Custom Data anti-patterns and corrections for Canvas plugins - unnecessary compatibility checks, misuse of AttributeHubs vs CustomModels
---

# Custom Data Patterns

This skill identifies common anti-patterns in how Canvas plugins use Custom Data (CustomModels and AttributeHubs) and provides corrections. These patterns have been observed in real customer plugins.

## When to Use This Skill

Invoke this skill **proactively** as soon as Custom Data is involved — don't wait for a review phase. Use it when:
- The plugin spec calls for persistent data storage (CustomModels or AttributeHubs)
- You are about to write or edit model definitions that subclass `CustomModel`
- You are about to write or edit code that uses `AttributeHub`
- You are adding relationships (ForeignKey, OneToOneField, ManyToManyField) to SDK models
- Reviewing existing plugin code that uses Custom Data

## Quick Reference

Reference the `custom_data_context.txt` file for detailed anti-patterns with BAD/GOOD examples.
