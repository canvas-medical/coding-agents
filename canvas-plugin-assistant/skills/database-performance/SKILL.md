---
name: database-performance
description: Database performance for Canvas plugins - N+1 detection, over-hydration/memory, write amplification, and Canvas execution limits (effect-batch ceiling, dbid PK)
---

# Database Performance Skill

This skill provides database performance guidelines for Canvas plugins. Query count (N+1) is only one failure mode. Real go-live incidents on Canvas instances have been caused just as often by **over-hydration/memory**, **write amplification**, **unbounded reconcile scope**, and **Canvas-specific execution limits** — none of which are fixed by adding `select_related`. Use this skill to diagnose across all four axes, not just N+1.

## The four failure modes

1. **Read count (N+1):** many small queries where one join/prefetch would do. Fix with `select_related` / `prefetch_related`.
2. **Over-hydration / memory:** too few queries, but each pulls too much — wide rows × many rows, a large related row joined just to read one value, or a **large text/JSON blob column** (e.g. `Note._body`) loaded for every row when nothing reads it. A single blob column can dwarf the rest of the row, so this is often the biggest per-row cost. Fix by *not* loading what you don't use: `.defer()` blob columns, `.values()`/`.only()` projections, drop unneeded joins, trim serializers. A related non-query variant: **accumulating unbounded state across invocations** — a cron/backfill that keeps all results-so-far in one cache blob or in-process list (read → concat → re-serialize each call) grows with total items, not per-batch. Persist only the cursor/metadata. This whole axis is the one people miss because it *looks* optimized.
3. **Write amplification:** redundant or cascading writes (re-saving unchanged rows; each write triggering a handler/external push). Fix with content-hash no-op guards, idempotency, and convergence.
4. **Canvas execution limits:** the 64 MB gRPC effect-batch ceiling, effects applied only after the handler returns, and custom-data models keyed on `dbid` (not `id`). These are invisible to generic Django advice.

## When more queries is BETTER

Do **not** reflexively add `select_related`. Adding a join to a **large** relation (e.g. `Note`) that you only need one scalar from is an anti-pattern: it hydrates the whole row per result and drives memory. To read a related object's primary key, use the FK column that's already on the row (`appointment.note_id`), never `select_related("note").note.dbid`. Prefer more, narrower queries over one fat over-fetching join when the joined row is large and mostly unused.

Likewise, do not load **large text/JSON blob columns** you don't use. `Note._body` and other `*_body`/`*_json`/`payload`/document fields can be far larger than every other field combined; pulling them across many rows is a memory blowout even at a perfect query count. Default to `.defer("_body", ...)` or `.only(...)` the small fields, or `.values(...)` when you only need scalars. See `performance_context.txt` §"Over-Hydration & Memory."

## When to Use This Skill

Use this skill when:
- Reviewing plugin code that queries Canvas data models
- Diagnosing memory growth / container memkills on a hot endpoint (hit on many page loads)
- Reviewing sync / webhook / reconcile paths for redundant or runaway writes
- Reviewing handlers that emit many effects, or that query custom-data (SDK) models
- Auditing data access patterns before deployment

## Diagnose before you grep

The GTM performance PRs that landed all *measured first*, then attributed root cause. Before proposing fixes:
- Identify the **hot path** (which endpoint/handler, how often it runs).
- Estimate **rows × row width** per request (memory), and **writes/effects per trigger** (amplification), not just query count.
- Confirm scaling workers/memory would actually help — an oversized effect batch or a non-converging import is algorithmic, and no amount of scaling fixes it.

## Quick Detection

```bash
# Loops accessing related objects (N+1)
grep -rn "for.*in.*\.objects" --include="*.py" .
# select_related on a relation only used for its id (over-hydration)
grep -rn "select_related(" --include="*.py" .
# large text/JSON blob columns pulled without .defer()/.only() (over-hydration)
grep -rn "_body\|_json\|_html\|payload\|\.content" --include="*.py" .
# cache/state accumulators: full blob read+concat+re-serialize each run (memory)
grep -rn "cache.get\|cache.set\|json.loads\|json.dumps" --include="*.py" .
# Count/order_by("id") on custom-data models — FieldError (PK is dbid)
grep -rn 'Count("id")\|order_by("id")\|Count(.id.)' --include="*.py" .
# Writes in sync/webhook paths without a change guard (write amplification)
grep -rn "\.update(\|\.save(" --include="*.py" .
```

## Performance Checklist

Reference the `performance_context.txt` file for detailed patterns including:
- N+1 query detection (`select_related` / `prefetch_related`)
- Over-hydration & memory (drop unneeded joins, `.values()`/`.only()`, serializer contracts)
- Write amplification & idempotency (content-hash no-op guards, convergence, cascades)
- Canvas execution limits (`dbid` PK, 64 MB effect-batch ceiling, queue+cron chunking)
- Bounding reconcile/sync work to what changed
- Common Canvas SDK data model relationships and anti-patterns
