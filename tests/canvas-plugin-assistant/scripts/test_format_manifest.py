"""Tests for format_manifest.py."""

import json
from pathlib import Path

from format_manifest import canonicalize, format_file, main


class TestCanonicalize:
    """Tests for the canonicalize() key-ordering."""

    def test_orders_top_level_components_and_variables(self) -> None:
        """Known keys are ordered by convention; components and variable entries too."""
        manifest = {
            "readme": "NONE",
            "name": "p",
            "components": {"views": [], "commands": [], "handlers": []},
            "variables": [{"sensitive": True, "name": "TOKEN"}],
            "sdk_version": "0.1.0",
        }

        result = canonicalize(manifest)

        assert list(result) == [
            "sdk_version",
            "name",
            "variables",
            "components",
            "readme",
        ]
        assert list(result["components"]) == ["commands", "handlers", "views"]
        assert list(result["variables"][0]) == ["name", "sensitive"]

    def test_preserves_unknown_keys_and_non_dict_shapes(self) -> None:
        """Unknown keys are kept; non-dict components / non-list variables pass through."""
        manifest = {"name": "p", "components": "oops", "variables": "oops", "extra": 1}

        result = canonicalize(manifest)

        assert result["components"] == "oops"
        assert result["variables"] == "oops"
        assert result["extra"] == 1

    def test_non_dict_variable_entry_passes_through(self) -> None:
        """A non-dict entry inside variables is left untouched."""
        result = canonicalize({"name": "p", "variables": ["raw", {"name": "X"}]})

        assert result["variables"] == ["raw", {"name": "X"}]


class TestFormatFile:
    """Tests for format_file()."""

    def test_reformats_and_is_idempotent(self, tmp_path: Path) -> None:
        """First pass reformats (True); a second pass reports unchanged (False)."""
        path = tmp_path / "CANVAS_MANIFEST.json"
        path.write_text(json.dumps({"name": "p", "sdk_version": "0.1.0"}))

        assert format_file(str(path)) is True
        assert format_file(str(path)) is False
        assert path.read_text().endswith("\n")

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        """An unreadable path returns None (skip), not an exception."""
        assert format_file(str(tmp_path / "nope.json")) is None

    def test_invalid_json_returns_none(self, tmp_path: Path) -> None:
        """Malformed JSON returns None (skip)."""
        path = tmp_path / "CANVAS_MANIFEST.json"
        path.write_text("{not json")

        assert format_file(str(path)) is None

    def test_non_object_top_level_returns_none(self, tmp_path: Path) -> None:
        """A top level that is not an object returns None (skip)."""
        path = tmp_path / "CANVAS_MANIFEST.json"
        path.write_text("[]")

        assert format_file(str(path)) is None


class TestMain:
    """Tests for main()."""

    def test_no_args_returns_2(self) -> None:
        """No paths → usage error, exit code 2."""
        assert main([]) == 2

    def test_reports_reformatted_and_unchanged(self, tmp_path: Path, capsys) -> None:
        """Valid files exit 0 and print their per-file status."""
        path = tmp_path / "CANVAS_MANIFEST.json"
        path.write_text(json.dumps({"name": "p", "sdk_version": "0.1.0"}))

        assert main([str(path)]) == 0
        assert "reformatted" in capsys.readouterr().out
        assert main([str(path)]) == 0
        assert "unchanged" in capsys.readouterr().out

    def test_bad_path_returns_2(self, tmp_path: Path) -> None:
        """A path that can't be parsed makes main exit 2."""
        assert main([str(tmp_path / "missing.json")]) == 2
