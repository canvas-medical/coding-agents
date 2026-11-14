"""Tests for the plugin-quality rule-manifest validator.

Includes the tripwire tests: for each way the manifest can be wrong, assert the
validator reports it; and assert the real committed manifest validates clean.
"""

import textwrap

import validate_rules as vr


def _valid_rule(**overrides):
    """A structurally valid rule dict; override single fields for negative tests."""
    rule = {
        "rule_id": "PERF-N1-001",
        "title": "N+1",
        "axis": "performance",
        "severity": "nudge",
        "stages": ["initial_build", "iteration"],
        "delivery": "push",
        "always_on": False,
        "detector": {"type": "regex", "pattern": r"\.all\(\)"},
        "teach_ref": "database-performance#quick-detection",
        "fix": "BAD/GOOD/Action",
        "runtime_signal": "query_count",
    }
    rule.update(overrides)
    return rule


SKILLS = {"database-performance", "plugin-api-server-security"}


def _manifest(rules, forward_ref_skills=("memory",)):
    """Wrap rules in a manifest dict."""
    return {"forward_ref_skills": list(forward_ref_skills), "rules": rules}


# --- validate_manifest: happy path ------------------------------------------

def test_valid_rule_has_no_errors():
    """A well-formed rule produces no errors."""
    assert vr.validate_manifest(_manifest([_valid_rule()]), SKILLS) == []


def test_forward_ref_skill_is_accepted():
    """A teach_ref to a not-yet-authored (forward-ref) skill is allowed."""
    rule = _valid_rule(teach_ref="memory#cache-accumulation")
    assert vr.validate_manifest(_manifest([rule]), SKILLS) == []


# --- validate_manifest: structural / enum failures --------------------------

def test_empty_rule_reports_all_missing_fields():
    """A rule missing every field is reported (covers all field-absent paths)."""
    errors = vr.validate_manifest(_manifest([{}]), SKILLS)
    assert any("missing required field" in e for e in errors)


def test_duplicate_rule_id():
    """Two rules with the same id are flagged."""
    errors = vr.validate_manifest(_manifest([_valid_rule(), _valid_rule()]), SKILLS)
    assert any("duplicate rule_id" in e for e in errors)


def test_bad_rule_id_format():
    """A rule_id not matching the pattern is flagged."""
    errors = vr.validate_manifest(_manifest([_valid_rule(rule_id="bad_id")]), SKILLS)
    assert any("does not match the required pattern" in e for e in errors)


def test_invalid_enums():
    """Invalid axis/severity/delivery/runtime_signal/always_on are each flagged."""
    rule = _valid_rule(
        axis="x", severity="x", delivery="x", runtime_signal="x", always_on="yes"
    )
    errors = vr.validate_manifest(_manifest([rule]), SKILLS)
    joined = "\n".join(errors)
    assert "invalid axis" in joined
    assert "invalid severity" in joined
    assert "invalid delivery" in joined
    assert "invalid runtime_signal" in joined
    assert "always_on must be a boolean" in joined


def test_stages_must_be_non_empty_list():
    """An empty stages list is flagged."""
    errors = vr.validate_manifest(_manifest([_valid_rule(stages=[])]), SKILLS)
    assert any("stages must be a non-empty list" in e for e in errors)


def test_invalid_stage_value():
    """An unknown stage name is flagged."""
    errors = vr.validate_manifest(_manifest([_valid_rule(stages=["nope"])]), SKILLS)
    assert any("invalid stage" in e for e in errors)


def test_detector_missing_keys():
    """A detector without type/pattern is flagged."""
    errors = vr.validate_manifest(_manifest([_valid_rule(detector={"type": "regex"})]), SKILLS)
    assert any("detector must have" in e for e in errors)


def test_detector_invalid_type():
    """An unknown detector type is flagged."""
    rule = _valid_rule(detector={"type": "spooky", "pattern": "x"})
    errors = vr.validate_manifest(_manifest([rule]), SKILLS)
    assert any("invalid detector type" in e for e in errors)


def test_detector_regex_must_compile():
    """A regex detector whose pattern does not compile is flagged."""
    rule = _valid_rule(detector={"type": "regex", "pattern": "("})
    errors = vr.validate_manifest(_manifest([rule]), SKILLS)
    assert any("regex does not compile" in e for e in errors)


def test_teach_ref_bad_format():
    """A teach_ref without a '#section' is flagged."""
    errors = vr.validate_manifest(_manifest([_valid_rule(teach_ref="database-performance")]), SKILLS)
    assert any("teach_ref must be" in e for e in errors)


def test_teach_ref_unknown_skill():
    """A teach_ref to a skill that neither exists nor is forward-referenced is flagged."""
    errors = vr.validate_manifest(_manifest([_valid_rule(teach_ref="ghost#x")]), SKILLS)
    assert any("unknown skill" in e for e in errors)


# --- validate_skill_rule_refs -----------------------------------------------

def test_skill_citing_unknown_rule_is_flagged(tmp_path):
    """A SKILL.md citing a rule_id absent from the manifest is flagged; a known id passes."""
    (tmp_path / "good").mkdir()
    (tmp_path / "good" / "SKILL.md").write_text("see PERF-N1-001 for details")
    (tmp_path / "bad").mkdir()
    (tmp_path / "bad" / "SKILL.md").write_text("see FAKE-RULE-999 for details")
    errors = vr.validate_skill_rule_refs(tmp_path, {"PERF-N1-001"})
    assert errors == ["bad: cites unknown rule_id 'FAKE-RULE-999'"]


# --- validate_readme --------------------------------------------------------

def test_readme_in_sync():
    """Matching README and skills sets produce no error."""
    assert vr.validate_readme({"a", "b"}, {"a", "b"}) == []


def test_readme_missing_and_extra():
    """A README that omits a skill and lists a nonexistent one is flagged both ways."""
    errors = vr.validate_readme({"a", "ghost"}, {"a", "b"})
    assert "missing b" in errors[0]
    assert "lists nonexistent ghost" in errors[0]


def test_readme_only_missing():
    """A README that only omits a skill (none extra) is flagged."""
    assert "missing b" in vr.validate_readme({"a"}, {"a", "b"})[0]


def test_readme_only_extra():
    """A README that only lists a nonexistent skill (none missing) is flagged."""
    assert "lists nonexistent ghost" in vr.validate_readme({"a", "ghost"}, {"a"})[0]


# --- parsers / io -----------------------------------------------------------

def test_parse_readme_skills(tmp_path):
    """The '### Skills' bullets are parsed; other sections are ignored."""
    readme = tmp_path / "README.md"
    readme.write_text(
        textwrap.dedent(
            """
            ### Skills

            - **alpha**: one
            - **beta-two**: two

            ### Slash Commands

            - **gamma**: ignored
            """
        )
    )
    assert vr.parse_readme_skills(readme) == {"alpha", "beta-two"}


def test_discover_skill_names(tmp_path):
    """Only directories containing a SKILL.md are discovered."""
    (tmp_path / "s1").mkdir()
    (tmp_path / "s1" / "SKILL.md").write_text("x")
    (tmp_path / "s2").mkdir()  # no SKILL.md
    assert vr.discover_skill_names(tmp_path) == {"s1"}


def test_load_yaml(tmp_path):
    """load_yaml parses a file into a dict."""
    path = tmp_path / "x.yaml"
    path.write_text("a: 1\n")
    assert vr.load_yaml(path) == {"a": 1}


# --- real manifest + CLI (green) --------------------------------------------

def test_real_manifest_validates_clean():
    """The committed rules.yaml is consistent with the skills and README."""
    errors = vr.collect_errors(vr.MANIFEST_DEFAULT, vr.SKILLS_DIR_DEFAULT, vr.README_DEFAULT)
    assert errors == [], errors


def test_main_ok(capsys):
    """main() returns 0 and prints OK on the real manifest."""
    assert vr.main([]) == 0
    assert "OK:" in capsys.readouterr().out


def test_main_reports_errors(tmp_path, capsys):
    """main() returns 1 and prints INVALID when the manifest is broken."""
    manifest = tmp_path / "rules.yaml"
    manifest.write_text("rules:\n  - {}\n")
    skills = tmp_path / "skills"
    skills.mkdir()
    readme = tmp_path / "README.md"
    readme.write_text("### Skills\n")
    code = vr.main(["--manifest", str(manifest), "--skills-dir", str(skills), "--readme", str(readme)])
    assert code == 1
    assert "INVALID:" in capsys.readouterr().out
