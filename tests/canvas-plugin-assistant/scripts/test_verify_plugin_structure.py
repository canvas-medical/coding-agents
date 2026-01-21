"""Tests for verify_plugin_structure module."""

import os
from pathlib import Path

import pytest

from verify_plugin_structure import kebab_to_snake, verify_structure


class TestKebabToSnake:
    """Tests for the kebab_to_snake function."""

    @pytest.mark.parametrize(
        ("input_name", "expected"),
        [
            pytest.param("my-plugin", "my_plugin", id="single_hyphen"),
            pytest.param("my-cool-plugin", "my_cool_plugin", id="multiple_hyphens"),
            pytest.param("plugin", "plugin", id="no_hyphens"),
            pytest.param("a-b-c-d", "a_b_c_d", id="many_hyphens"),
            pytest.param("", "", id="empty_string"),
        ],
    )
    def test_kebab_to_snake(self, input_name: str, expected: str) -> None:
        """Test kebab_to_snake converts hyphen to underscore."""
        tested = kebab_to_snake
        result = tested(input_name)

        assert result == expected


class TestVerifyStructure:
    """Tests for the verify_structure function."""

    def test_verify_structure__all_valid(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure returns True when all checks pass."""
        # Setup: Create valid structure
        inner_folder = tmp_path / "my_plugin"
        inner_folder.mkdir()
        (inner_folder / "CANVAS_MANIFEST.json").touch()
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").touch()

        # Change to tmp_path to test relative paths
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested("my-plugin")

            expected = True
            assert result is expected

            captured = capsys.readouterr()
            assert "OK: Inner folder 'my_plugin' exists" in captured.out
            assert "OK: CANVAS_MANIFEST.json in correct location" in captured.out
            assert "OK: tests/ at container level" in captured.out
            assert "OK: pyproject.toml at container level" in captured.out
            assert "Structure validation passed." in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__inner_folder_missing(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure returns False when inner folder is missing."""
        # Setup: Create structure without inner folder
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested("my-plugin")

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert "ERROR: Inner folder 'my_plugin' not found" in captured.out
            assert "ERROR: CANVAS_MANIFEST.json not found" in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__manifest_at_container_level(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure returns False when manifest is at container level only."""
        # Setup: Create inner folder but manifest at wrong level
        inner_folder = tmp_path / "my_plugin"
        inner_folder.mkdir()
        (tmp_path / "CANVAS_MANIFEST.json").touch()  # Wrong location
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested("my-plugin")

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert "ERROR: CANVAS_MANIFEST.json at container level - should be inside my_plugin/" in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__tests_inside_inner_folder(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure returns False when tests/ is inside inner folder."""
        # Setup: Create tests inside inner folder instead of container
        inner_folder = tmp_path / "my_plugin"
        inner_folder.mkdir()
        (inner_folder / "CANVAS_MANIFEST.json").touch()
        (inner_folder / "tests").mkdir()  # Wrong location
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested("my-plugin")

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert "ERROR: tests/ inside inner folder - should be at container level" in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__no_tests_warning(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure returns True with warning when no tests/ found."""
        # Setup: Valid structure but no tests folder
        inner_folder = tmp_path / "my_plugin"
        inner_folder.mkdir()
        (inner_folder / "CANVAS_MANIFEST.json").touch()
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested("my-plugin")

            expected = True
            assert result is expected

            captured = capsys.readouterr()
            assert "WARNING: No tests/ directory found" in captured.out
            assert "Structure validation passed with 1 warning(s)." in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__no_pyproject_warning(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure returns True with warning when no pyproject.toml."""
        # Setup: Valid structure but no pyproject.toml
        inner_folder = tmp_path / "my_plugin"
        inner_folder.mkdir()
        (inner_folder / "CANVAS_MANIFEST.json").touch()
        (tmp_path / "tests").mkdir()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested("my-plugin")

            expected = True
            assert result is expected

            captured = capsys.readouterr()
            assert "WARNING: pyproject.toml not found" in captured.out
            assert "Structure validation passed with 1 warning(s)." in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__duplicate_manifest(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure returns False when manifest in both locations."""
        # Setup: Manifest in both container and inner folder
        inner_folder = tmp_path / "my_plugin"
        inner_folder.mkdir()
        (inner_folder / "CANVAS_MANIFEST.json").touch()
        (tmp_path / "CANVAS_MANIFEST.json").touch()  # Duplicate
        (tmp_path / "tests").mkdir()
        (tmp_path / "pyproject.toml").touch()

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested("my-plugin")

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert "ERROR: CANVAS_MANIFEST.json in BOTH locations - remove container level copy" in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__errors_with_warnings(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure shows both errors and warnings count."""
        # Setup: Missing inner folder (error) + no tests + no pyproject (warnings)
        # Nothing created - all checks will fail or warn

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested("my-plugin")

            expected = False
            assert result is expected

            captured = capsys.readouterr()
            assert "STRUCTURE VALIDATION FAILED: 2 error(s)" in captured.out
            assert "Also found 2 warning(s)" in captured.out
        finally:
            os.chdir(original_cwd)

    def test_verify_structure__multiple_warnings_no_errors(self, tmp_path: Path, capsys) -> None:
        """Test verify_structure passes with multiple warnings."""
        # Setup: Valid inner folder and manifest, but missing tests and pyproject
        inner_folder = tmp_path / "my_plugin"
        inner_folder.mkdir()
        (inner_folder / "CANVAS_MANIFEST.json").touch()
        # No tests/ and no pyproject.toml

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            tested = verify_structure
            result = tested("my-plugin")

            expected = True
            assert result is expected

            captured = capsys.readouterr()
            assert "WARNING: No tests/ directory found" in captured.out
            assert "WARNING: pyproject.toml not found" in captured.out
            assert "Structure validation passed with 2 warning(s)." in captured.out
        finally:
            os.chdir(original_cwd)
