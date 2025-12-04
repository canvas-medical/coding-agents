---
name: database-performance
description: Database query optimization for Canvas plugins - N+1 detection, prefetch_related, select_related
---

# Database Performance Skill

This skill provides database query optimization guidelines for Canvas plugins. Use it to identify N+1 query issues and optimize data access patterns using Django ORM best practices.

## When to Use This Skill

Use this skill when:
- Reviewing plugin code that queries Canvas data models
- Identifying potential N+1 query problems
- Optimizing loops that access related objects
- Auditing database access patterns before deployment

## Quick Detection

Search for these patterns that often indicate N+1 issues:

```bash
# Loops accessing related objects
grep -rn "for.*in.*\.objects" --include="*.py" .
grep -rn "\.filter\|\.get\|\.all" --include="*.py" .
```

## Performance Checklist

Reference the `performance_context.txt` file for detailed patterns including:
- N+1 query detection
- `select_related()` for foreign keys
- `prefetch_related()` for reverse relations and many-to-many
- Common Canvas SDK data model relationships
- Anti-patterns to avoid
