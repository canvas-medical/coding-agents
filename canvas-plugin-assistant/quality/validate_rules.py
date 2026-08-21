"""Validate the plugin-quality rule manifest (rules.yaml), the SSOT.

Checks structural integrity of the manifest and its consistency with the CPA
skills and README. Runs in CI and is importable for tests. It does NOT execute
detectors — lint code-generation from the manifest is M4.

Cross-check semantics (accepted at the M0 review; tighten in M2):
  - skill -> manifest: any rule_id-shaped token cited inside a SKILL.md must
    exist in the manifest (catches typos/orphans as skills start citing rules).
  - manifest -> skill: every rule's teach_ref must resolve to a skill that
    exists under skills/, OR to a skill named in `forward_ref_skills` (authored
    later, in M2). Section anchors are recorded but not validated in M0.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

AXES = {"security", "performance", "memory", "correctness"}
SEVERITIES = {"block", "nudge"}
DELIVERIES = {"push", "pull"}
RUNTIME_SIGNALS = {"query_count", "peak_rss", "latency", "none"}
DETECTOR_TYPES = {"regex", "ast", "whole_plugin"}
STAGES = {"discovery", "initial_build", "iteration", "final_review", "published"}
REQUIRED_FIELDS = (
    "rule_id",
    "title",
    "axis",
    "severity",
    "stages",
    "delivery",
    "always_on",
    "detector",
    "teach_ref",
    "fix",
    "runtime_signal",
)
RULE_ID_RE = re.compile(r"[A-Z]{2,}(?:-[A-Z0-9]+)+-\d{3}")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CPA = _REPO_ROOT / "canvas-plugin-assistant"
MANIFEST_DEFAULT = _CPA / "quality" / "rules.yaml"
SKILLS_DIR_DEFAULT = _CPA / "skills"
README_DEFAULT = _CPA / "README.md"


def load_yaml(path: Path) -> dict:
    """Parse a YAML file into a dict."""
    return yaml.safe_load(path.read_text())


def discover_skill_names(skills_dir: Path) -> set[str]:
    """Return the names of directories under skills_dir that hold a SKILL.md."""
    return {p.name for p in skills_dir.iterdir() if (p / "SKILL.md").is_file()}


def parse_readme_skills(readme_path: Path) -> set[str]:
    """Extract the skill names bulleted under the README '### Skills' section."""
    names: set[str] = set()
    in_section = False
    for line in readme_path.read_text().splitlines():
        if line.startswith("### "):
            in_section = line.strip() == "### Skills"
            continue
        if in_section:
            match = re.match(r"\s*-\s+\*\*([\w-]+)\*\*", line)
            if match:
                names.add(match.group(1))
    return names


def validate_manifest(manifest: dict, skill_names: set[str]) -> list[str]:
    """Validate structure, enums, regex compilation, uniqueness and teach_refs."""
    errors: list[str] = []
    forward_refs = set(manifest.get("forward_ref_skills", []))
    known_skills = skill_names | forward_refs
    seen_ids: set[str] = set()

    for index, rule in enumerate(manifest.get("rules", [])):
        rid = rule.get("rule_id", f"<rule #{index}>")

        missing = [f for f in REQUIRED_FIELDS if f not in rule]
        if missing:
            errors.append(f"{rid}: missing required field(s): {', '.join(missing)}")

        if "rule_id" in rule:
            if not RULE_ID_RE.fullmatch(rule["rule_id"]):
                errors.append(f"{rid}: rule_id does not match the required pattern")
            if rule["rule_id"] in seen_ids:
                errors.append(f"{rid}: duplicate rule_id")
            seen_ids.add(rule["rule_id"])

        if "axis" in rule and rule["axis"] not in AXES:
            errors.append(f"{rid}: invalid axis {rule['axis']!r}")
        if "severity" in rule and rule["severity"] not in SEVERITIES:
            errors.append(f"{rid}: invalid severity {rule['severity']!r}")
        if "delivery" in rule and rule["delivery"] not in DELIVERIES:
            errors.append(f"{rid}: invalid delivery {rule['delivery']!r}")
        if "runtime_signal" in rule and rule["runtime_signal"] not in RUNTIME_SIGNALS:
            errors.append(f"{rid}: invalid runtime_signal {rule['runtime_signal']!r}")
        if "always_on" in rule and not isinstance(rule["always_on"], bool):
            errors.append(f"{rid}: always_on must be a boolean")

        if "stages" in rule:
            stages = rule["stages"]
            if not isinstance(stages, list) or not stages:
                errors.append(f"{rid}: stages must be a non-empty list")
            else:
                bad = [s for s in stages if s not in STAGES]
                if bad:
                    errors.append(f"{rid}: invalid stage(s): {', '.join(map(str, bad))}")

        if "detector" in rule:
            errors.extend(_validate_detector(rid, rule["detector"]))

        if "teach_ref" in rule:
            errors.extend(_validate_teach_ref(rid, rule["teach_ref"], known_skills))

    return errors


def _validate_detector(rid: str, detector: object) -> list[str]:
    """Validate a rule's detector block (type, pattern, regex compilation)."""
    if not isinstance(detector, dict) or "type" not in detector or "pattern" not in detector:
        return [f"{rid}: detector must have 'type' and 'pattern'"]
    errors: list[str] = []
    if detector["type"] not in DETECTOR_TYPES:
        errors.append(f"{rid}: invalid detector type {detector['type']!r}")
    if detector["type"] == "regex":
        try:
            re.compile(detector["pattern"])
        except re.error as exc:
            errors.append(f"{rid}: detector regex does not compile: {exc}")
    return errors


def _validate_teach_ref(rid: str, teach_ref: object, known_skills: set[str]) -> list[str]:
    """Validate teach_ref format and that its skill exists or is forward-referenced."""
    if not isinstance(teach_ref, str) or "#" not in teach_ref:
        return [f"{rid}: teach_ref must be '<skill>#<section>'"]
    skill = teach_ref.split("#", 1)[0]
    if skill not in known_skills:
        return [f"{rid}: teach_ref points at unknown skill {skill!r}"]
    return []


def validate_skill_rule_refs(skills_dir: Path, rule_ids: set[str]) -> list[str]:
    """Every rule_id-shaped token cited in a SKILL.md must exist in the manifest."""
    errors: list[str] = []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        for token in RULE_ID_RE.findall(skill_md.read_text()):
            if token not in rule_ids:
                errors.append(
                    f"{skill_md.parent.name}: cites unknown rule_id {token!r}"
                )
    return errors


def validate_readme(readme_names: set[str], skill_names: set[str]) -> list[str]:
    """The README '### Skills' list must exactly match the skills on disk."""
    if readme_names == skill_names:
        return []
    missing = skill_names - readme_names
    extra = readme_names - skill_names
    parts = []
    if missing:
        parts.append(f"missing {', '.join(sorted(missing))}")
    if extra:
        parts.append(f"lists nonexistent {', '.join(sorted(extra))}")
    return [f"README '### Skills' out of sync with skills/: {'; '.join(parts)}"]


def collect_errors(
    manifest_path: Path, skills_dir: Path, readme_path: Path
) -> list[str]:
    """Run every check and return the combined list of errors (empty == valid)."""
    manifest = load_yaml(manifest_path)
    skill_names = discover_skill_names(skills_dir)
    rule_ids = {r["rule_id"] for r in manifest.get("rules", []) if "rule_id" in r}
    errors = validate_manifest(manifest, skill_names)
    errors += validate_skill_rule_refs(skills_dir, rule_ids)
    errors += validate_readme(parse_readme_skills(readme_path), skill_names)
    return errors


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: validate the manifest and print the result."""
    parser = argparse.ArgumentParser(description="Validate the plugin-quality rule manifest.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--skills-dir", type=Path, default=SKILLS_DIR_DEFAULT)
    parser.add_argument("--readme", type=Path, default=README_DEFAULT)
    args = parser.parse_args(argv)

    errors = collect_errors(args.manifest, args.skills_dir, args.readme)
    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    manifest = load_yaml(args.manifest)
    print(f"OK: {len(manifest.get('rules', []))} rules validated")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
