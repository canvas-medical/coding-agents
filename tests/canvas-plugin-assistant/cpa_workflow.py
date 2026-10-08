"""Canonical CPA workflow step list, plus the renderer both the sync and the test use."""

# The workflow, in order: (command name, one-line description). This is the single
# source of truth; every command file's "## CPA Workflow" block is rendered from it.
STEPS = [
    ("check-setup", "Verify environment tools (uv, unbuffer)"),
    ("new-plugin", "Create plugin from requirements"),
    ("style", "Format + lint + type-check to the Canvas standard"),
    ("deploy", "Deploy to Canvas instance for UAT"),
    ("coverage", "Check test coverage (aim for 90%)"),
    ("security-review", "Comprehensive security audit"),
    ("database-performance-review", "Database query optimization"),
    ("wrap-up", "Final checklist before delivery"),
]

# Column the descriptions start at. `/cpa:database-performance-review` is longer
# than this, so a minimum separator is enforced rather than assumed.
_COLUMN = 22
_MIN_GAP = 2
_MARKER = "  ← YOU ARE HERE"


def render(current: str) -> str:
    """The workflow block body, with the marker on ``current``'s line."""
    lines = []
    for name, description in STEPS:
        command = f"/cpa:{name}"
        gap = max(_COLUMN - len(command), _MIN_GAP)
        line = f"{command}{' ' * gap}→  {description}"
        if name == current:
            line += _MARKER
        lines.append(line)
    return "\n".join(lines) + "\n"
