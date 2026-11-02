"""The cpa plugin's skills load, and its version agrees with the marketplace."""

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PLUGIN = REPO / "canvas-plugin-assistant"
SKILLS = sorted(path.parent for path in (PLUGIN / "skills").glob("*/SKILL.md"))


def _frontmatter(skill_file: Path) -> dict[str, str]:
    """The ``key: value`` lines between a SKILL.md's leading ``---`` fences."""
    lines = skill_file.read_text().splitlines()
    assert lines[0] == "---", f"{skill_file} does not open with frontmatter"
    end = lines.index("---", 1)
    return dict(line.split(": ", 1) for line in lines[1:end])


@pytest.mark.parametrize("skill", SKILLS, ids=[skill.name for skill in SKILLS])
def test_each_skill_is_named_for_its_directory_and_described(skill: Path) -> None:
    """Claude Code finds a skill by its frontmatter name, and picks it by its description."""
    frontmatter = _frontmatter(skill / "SKILL.md")

    assert frontmatter.get("name") == skill.name
    assert frontmatter.get("description", "").strip()


def test_skills_are_found() -> None:
    """The parametrized test above runs over the skills, including agent-patterns."""
    assert "agent-patterns" in {skill.name for skill in SKILLS}


def test_the_plugin_and_marketplace_carry_the_same_version() -> None:
    """Installed copies update only when the marketplace entry's version moves too."""
    plugin = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    marketplace = json.loads((REPO / ".claude-plugin" / "marketplace.json").read_text())
    (entry,) = [p for p in marketplace["plugins"] if p["name"] == plugin["name"]]

    assert entry["version"] == plugin["version"]
