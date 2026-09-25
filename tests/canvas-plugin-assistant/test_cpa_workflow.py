"""The "## CPA Workflow" block is copy-pasted into every command file.

Eight copies of the same list drifted eight different ways: four never learned
about `/cpa:style`, `style.md` carried a shorter list of its own, `check-setup`
was described three different ways, and the column alignment varied. Each copy is
read by an agent deciding what to run next, so a stale one sends it to the wrong
step.

These tests render the block from `cpa_workflow.STEPS` and assert every file
matches, so adding or renaming a command fails here instead of silently leaving
seven files behind.
"""

import re
from pathlib import Path

import pytest
from cpa_workflow import STEPS, render

COMMANDS_DIR = (
    Path(__file__).resolve().parents[2] / "canvas-plugin-assistant" / "commands"
)

HEADING = "## CPA Workflow"


def _workflow_files() -> list[Path]:
    """Command files carrying a workflow block."""
    return sorted(p for p in COMMANDS_DIR.glob("*.md") if HEADING in p.read_text())


def _block(path: Path) -> str:
    """The fenced block body inside the file's workflow section."""
    _, _, tail = path.read_text().partition(HEADING)
    match = re.search(r"```\n(.*?)```", tail, re.DOTALL)
    assert match, f"{path.name} has a {HEADING} heading but no fenced block"
    return match.group(1)


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda p: p.name)
def test_workflow_block_matches_the_canonical_list(path: Path) -> None:
    """Every command's block is exactly the canonical list, marker on its own step."""
    assert _block(path) == render(path.stem), (
        f"{path.name}'s CPA Workflow block has drifted. Re-render it from "
        f"cpa_workflow.STEPS, or update STEPS if the workflow really changed."
    )


@pytest.mark.parametrize("name", [name for name, _ in STEPS])
def test_every_step_names_a_real_command(name: str) -> None:
    """A step in the list corresponds to a command file that exists.

    Catches a renamed or deleted command leaving a dangling step behind.
    """
    assert (COMMANDS_DIR / f"{name}.md").is_file(), (
        f"STEPS names /cpa:{name} but {name}.md does not exist"
    )


def test_every_workflow_file_is_a_step() -> None:
    """A command that shows the workflow is itself part of it.

    Otherwise its block has no `← YOU ARE HERE` marker and the reader cannot tell
    where they are.
    """
    step_names = {name for name, _ in STEPS}
    orphans = [p.name for p in _workflow_files() if p.stem not in step_names]

    assert not orphans, f"these show the workflow but are not steps in it: {orphans}"


def test_the_marker_appears_exactly_once_per_file() -> None:
    """Two markers, or none, both leave the reader guessing."""
    for path in _workflow_files():
        assert _block(path).count("← YOU ARE HERE") == 1, path.name
