"""Tests for verify_plugin_structure module."""

import json
import os
import runpy
import sys
from pathlib import Path

import pytest

from verify_plugin_structure import verify_structure

SCRIPT: str = str(
    Path(__file__).resolve().parents[3]
    / "canvas-plugin-assistant"
    / "scripts"
    / "verify_plugin_structure.py"
)


def write_manifest(folder: Path, name: str) -> None:
    """Create folder holding a CANVAS_MANIFEST.json with the given plugin name."""
    folder.mkdir(exist_ok=True)
    (folder / "CANVAS_MANIFEST.json").write_text(json.dumps({"name": name}))


class TestVerifyStructure:
    """Tests for the verify_structure function."""

    def test_verify_structure__prefixed_package_passes(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure returns True for a prefixed package with tests and pyproject."""
        write_manifest(tmp_path / "acme__vitals_alert", "acme__vitals_alert")
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested()

            expected = True
            assert result is expected

            captured = capsys.readouterr()
            assert "OK: Inner folder 'acme__vitals_alert' holds CANVAS_MANIFEST.json" in captured.out
            assert "OK: tests/ at container level" in captured.out
            assert "OK: pyproject.toml at container level" in captured.out
            assert "Structure validation passed." in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__no_manifest_fails(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure returns False when no CANVAS_MANIFEST.json exists."""
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested()

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert "ERROR: CANVAS_MANIFEST.json not found" in captured.out
            assert "STRUCTURE VALIDATION FAILED: 1 error(s)" in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__container_level_manifest_fails(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure returns False when the manifest sits at container level only."""
        (tmp_path / "acme__vitals_alert").mkdir()
        (tmp_path / "CANVAS_MANIFEST.json").write_text(json.dumps({"name": "acme__vitals_alert"}))
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested()

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert "ERROR: CANVAS_MANIFEST.json at container level - should be inside the package folder" in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__two_packages_fails(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure refuses two packages, because Canvas deploys exactly one plugin per repo."""
        write_manifest(tmp_path / "acme__first", "acme__first")
        write_manifest(tmp_path / "acme__second", "acme__second")
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested()

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert (
                "ERROR: More than one package folder holds a CANVAS_MANIFEST.json: acme__first, acme__second"
                in captured.out
            )
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__name_mismatch_fails(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure refuses an unprefixed manifest name, because Platform rejects it on push."""
        write_manifest(tmp_path / "acme__vitals_alert", "vitals_alert")
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested()

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert "ERROR: Manifest name 'vitals_alert' does not match the package folder 'acme__vitals_alert'" in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__tests_inside_inner_folder_fails(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure returns False when tests/ is inside the package folder."""
        inner = tmp_path / "acme__vitals_alert"
        write_manifest(inner, "acme__vitals_alert")
        (inner / "tests").mkdir()
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested()

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert "ERROR: tests/ inside inner folder - should be at container level" in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__missing_tests_warns(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure passes with a warning when tests/ is missing."""
        write_manifest(tmp_path / "acme__vitals_alert", "acme__vitals_alert")
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested()

            expected = True
            assert result is expected

            captured = capsys.readouterr()
            assert "WARNING: No tests/ directory found" in captured.out
            assert "Structure validation passed with 1 warning(s)." in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__missing_pyproject_warns(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure passes with a warning when pyproject.toml is missing."""
        write_manifest(tmp_path / "acme__vitals_alert", "acme__vitals_alert")
        (tmp_path / "tests").mkdir()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested()

            expected = True
            assert result is expected

            captured = capsys.readouterr()
            assert "WARNING: pyproject.toml not found" in captured.out
            assert "Structure validation passed with 1 warning(s)." in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__duplicate_manifest_fails(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure refuses a manifest in both locations, because Canvas would read the wrong one."""
        write_manifest(tmp_path / "acme__vitals_alert", "acme__vitals_alert")
        (tmp_path / "CANVAS_MANIFEST.json").write_text(json.dumps({"name": "acme__vitals_alert"}))
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested()

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert "ERROR: CANVAS_MANIFEST.json in BOTH locations - remove container level copy" in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__errors_with_warnings(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure reports both error and warning counts."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested()

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert "STRUCTURE VALIDATION FAILED: 1 error(s)" in captured.out
            assert "Also found 2 warning(s)" in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__invalid_manifest_json_fails(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure refuses an unreadable manifest, because its name cannot be checked."""
        inner = tmp_path / "acme__vitals_alert"
        inner.mkdir()
        (inner / "CANVAS_MANIFEST.json").write_text("{not json")
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested()

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert "ERROR: CANVAS_MANIFEST.json is not valid JSON" in captured.out
        finally:
            os.chdir(original_cwd)


class TestMain:
    """Tests for the command line entry point."""

    def test_main__argument_is_usage_error(self, monkeypatch, capsys) -> None:
        """Test running with an argument exits 1 with a usage message."""
        monkeypatch.setattr(sys, "argv", [SCRIPT, "extra"])

        with pytest.raises(SystemExit) as exit_info:
            runpy.run_path(SCRIPT, run_name="__main__")

        assert exit_info.value.code == 1
        assert "Usage: verify_plugin_structure.py" in capsys.readouterr().err

    @pytest.mark.parametrize(
        ("with_manifest", "code"),
        [
            pytest.param(True, 0, id="valid"),
            pytest.param(False, 1, id="invalid"),
        ],
    )
    def test_main__exit_code(self, tmp_path: Path, monkeypatch, with_manifest: bool, code: int) -> None:
        """Test running with no arguments exits 0 on a valid structure and 1 otherwise."""
        if with_manifest:
            write_manifest(tmp_path / "acme__vitals_alert", "acme__vitals_alert")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(sys, "argv", [SCRIPT])

        with pytest.raises(SystemExit) as exit_info:
            runpy.run_path(SCRIPT, run_name="__main__")

        assert exit_info.value.code == code


class TestVerifyStructureScenarios:
    """verify_structure on containers as the CPA workflow actually leaves them."""

    def test_verify_structure__mid_workflow_container_with_fixture_manifest(self, tmp_path: Path, monkeypatch, capsys) -> None:
        """Only a package folder one level down counts; dot folders and a fixture manifest under tests/ do not."""
        package = tmp_path / "acme__vitals_alert"
        write_manifest(package, "acme__vitals_alert")
        (package / "__init__.py").write_text("")
        (package / "README.md").write_text("# vitals alert\n")
        (package / "handlers").mkdir()
        (package / "handlers" / "__init__.py").write_text("")
        (package / "handlers" / "event_handlers.py").write_text("")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "__init__.py").write_text("")
        (tmp_path / "tests" / "test_event_handlers.py").write_text("")
        (tmp_path / "tests" / "fixtures").mkdir()
        write_manifest(tmp_path / "tests" / "fixtures" / "legacy", "vitals_alert")
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "vitals-alert"\n')
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        (tmp_path / ".cpa-workflow-artifacts").mkdir()
        (tmp_path / ".cpa-workflow-artifacts" / "plugin-spec.md").write_text("# Plugin spec\n")
        monkeypatch.chdir(tmp_path)

        result = verify_structure()

        assert result is True
        output = capsys.readouterr().out
        assert "OK: Inner folder 'acme__vitals_alert' holds CANVAS_MANIFEST.json" in output
        assert "legacy" not in output
        assert "ERROR" not in output
        assert "Structure validation passed." in output
