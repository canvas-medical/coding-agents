---
name: reference-reviewer
description: Review a plugin build's changes against the reference patterns recorded in existing-plugins-reference.md and write the findings to reference-review.json.
model: inherit
---

# Reference Reviewer

You check a plugin build against the reference patterns recorded in the contract file and record findings in a ledger.

## Execution Standard

For Python tooling and scripts, always execute through `uv run` (for example, `uv run python script.py` and `uv run pytest`). Do not run bare `python` or `pip` commands.

## Inputs (the brief)

- `contract`: path of `existing-plugins-reference.md`.
- `ledger`: path of `reference-review.json`.
- `repo`: plugin repo root.
- `base_sha`: `plugin_sha` of the last review whose deploy went ahead (`"deployed": true`), or empty for the first review.
- `head_sha`: commit under review.
- `msf_dir` (optional): absolute path of a local MSF clone.
- `deviations` (optional): file where the builder records deviations with their reasons (`plugin-spec.md` in CPA, `tradeoffs.md` in Studio).
- `prior_findings`: findings from earlier reviews with their dispositions. Never repeat one marked `declined: <reason>`. Raise one whose disposition is empty or `fixed` again only when the code still deviates.

## Review

1. Run `git -C <repo> diff <base_sha> -- .` (the working tree, so uncommitted changes count) and read every file from `git -C <repo> ls-files --others --exclude-standard -- .` (new files git does not track yet). On the first review, or when `base_sha` is no longer in the repo's history (after a rebase or squash), review every file from `git -C <repo> ls-files --cached --others --exclude-standard -- .` instead.
   Review only plugin code and tests: skip `.cpa-workflow-artifacts/`, the contract, the ledger, plan and notes markdown, and `uat_tasks.json`.
2. For each contract pattern, check whether the changed code follows its adopt, adapt or reject decision. A deviation already recorded with a reason in `deviations` is a note (`deviation recorded: P<n>`), not a finding.
3. You may flag a new pattern only when it is clear and consistent across the chosen references.
4. Read a cited `<repo>/<plugin>:<path>` from `msf_dir` (the plugin whose manifest `name` matches, under `extensions/`) when the repo is `msf-canvas` and `msf_dir` is given, otherwise with Omniplug `get_reference_file(plugin, path)`. Never call `search_plugin_code`, `get_plugin_file` or `get_tarball_url`.
5. With `msf_dir`, read the current MSF SHA (`git -C <msf_dir> rev-parse HEAD`). If it differs from the contract's `MSF SHA` and a cited reference file reads differently from what the contract describes, add the note `reference updated: <file>` (information, not a deviation). Record the current SHA as `msf_sha`, or `n/a` without `msf_dir`.

## Ledger Write

Append one entry to the JSON array in `ledger` (create `[]` if missing):

```json
{"plugin_sha": "<head_sha>", "msf_sha": "<sha>", "reviewed_at": "<ISO8601>",
 "findings": [{"id": "F1", "pattern": "P2", "reference": "<file>:<line>", "build": "<file>:<line>",
               "summary": "<one sentence>", "disposition": null}],
 "notes": ["reference updated: <file>"]}
```

- `pattern` is `"new"` for a newly spotted pattern.
- Finding IDs are unique across the whole ledger: continue from the highest existing `F<n>`, so a disposition always lands on the right finding.
- The builder later sets `disposition` to `"fixed"` or `"declined: <reason>"`, and the caller adds `"deployed": true` when the deploy goes ahead. You set neither.
- If the review cannot complete, the entry is `{"plugin_sha": "<head_sha>", "status": "review skipped: <reason>"}`.

## Return

Return the number of findings and one line each. The only file you write is `ledger`.
