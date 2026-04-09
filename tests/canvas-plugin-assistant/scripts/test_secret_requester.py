"""Tests for secret_requester module."""

import json
from pathlib import Path
from unittest.mock import call, patch

import pytest

from secret_requester import SecretRequester


class TestGetSecrets:
    """Tests for SecretRequester.get_secrets."""

    def test_get_secrets__empty_names(self) -> None:
        """Return empty dict when no secret names are requested."""
        tested = SecretRequester

        result = tested.get_secrets(secret_names=[], instance="test-instance", plugin_name="my_plugin")

        expected: dict = {}
        assert result == expected

    def test_get_secrets__creates_file_when_missing(self, tmp_path: Path) -> None:
        """Create the secrets file with empty values when it does not exist."""
        tested = SecretRequester
        secrets_file = tmp_path / "test-instance.json"

        with patch.object(tested, "_SECRETS_DIR", tmp_path):
            result = tested.get_secrets(
                secret_names=["API_KEY"], instance="test-instance", plugin_name="my_plugin"
            )

        expected: dict = {}
        assert result == expected
        exp_written = {"my_plugin": {"API_KEY": ""}}
        assert json.loads(secrets_file.read_text(encoding="utf-8")) == exp_written

    def test_get_secrets__returns_populated_values(self, tmp_path: Path) -> None:
        """Return only secrets that have non-empty values."""
        tested = SecretRequester
        secrets_file = tmp_path / "test-instance.json"
        secrets_file.write_text(
            json.dumps({"my_plugin": {"API_KEY": "sk-123", "EMPTY_ONE": ""}}), encoding="utf-8"
        )

        with patch.object(tested, "_SECRETS_DIR", tmp_path):
            result = tested.get_secrets(
                secret_names=["API_KEY", "EMPTY_ONE"], instance="test-instance", plugin_name="my_plugin"
            )

        expected = {"API_KEY": "sk-123"}
        assert result == expected

    def test_get_secrets__removes_stale_keys(self, tmp_path: Path) -> None:
        """Remove keys from the file that are no longer in the requested list."""
        tested = SecretRequester
        secrets_file = tmp_path / "inst.json"
        secrets_file.write_text(
            json.dumps({"plug": {"OLD_KEY": "old", "KEEP": "val"}}), encoding="utf-8"
        )

        with patch.object(tested, "_SECRETS_DIR", tmp_path):
            tested.get_secrets(secret_names=["KEEP", "NEW_KEY"], instance="inst", plugin_name="plug")

        expected = {"plug": {"KEEP": "val", "NEW_KEY": ""}}
        assert json.loads(secrets_file.read_text(encoding="utf-8")) == expected

    def test_get_secrets__adds_missing_keys(self, tmp_path: Path) -> None:
        """Add missing secret names with empty values."""
        tested = SecretRequester
        secrets_file = tmp_path / "inst.json"
        secrets_file.write_text(json.dumps({"plug": {}}), encoding="utf-8")

        with patch.object(tested, "_SECRETS_DIR", tmp_path):
            tested.get_secrets(secret_names=["NEW_A", "NEW_B"], instance="inst", plugin_name="plug")

        expected = {"plug": {"NEW_A": "", "NEW_B": ""}}
        assert json.loads(secrets_file.read_text(encoding="utf-8")) == expected

    def test_get_secrets__preserves_other_plugins(self, tmp_path: Path) -> None:
        """Do not modify secrets for other plugins in the same file."""
        tested = SecretRequester
        secrets_file = tmp_path / "inst.json"
        secrets_file.write_text(
            json.dumps({"other_plugin": {"TOKEN": "xyz"}, "my_plugin": {"OLD": "val"}}),
            encoding="utf-8",
        )

        with patch.object(tested, "_SECRETS_DIR", tmp_path):
            tested.get_secrets(secret_names=["NEW"], instance="inst", plugin_name="my_plugin")

        written = json.loads(secrets_file.read_text(encoding="utf-8"))
        exp_other = {"TOKEN": "xyz"}
        assert written["other_plugin"] == exp_other
        exp_my = {"NEW": ""}
        assert written["my_plugin"] == exp_my

    def test_get_secrets__uses_env_var_filepath(self, tmp_path: Path) -> None:
        """Use CPA_SECRET_FILEPATH env var when set."""
        tested = SecretRequester
        secrets_file = tmp_path / "custom-secrets.json"
        secrets_file.write_text(json.dumps({"plug": {"KEY": "val"}}), encoding="utf-8")

        with patch.dict("os.environ", {"CPA_SECRET_FILEPATH": str(secrets_file)}):
            result = tested.get_secrets(secret_names=["KEY"], instance="ignored", plugin_name="plug")

        expected = {"KEY": "val"}
        assert result == expected

    def test_get_secrets__env_var_empty_falls_back(self, tmp_path: Path) -> None:
        """Fall back to _SECRETS_DIR when env var is empty string."""
        tested = SecretRequester
        secrets_file = tmp_path / "inst.json"
        secrets_file.write_text(json.dumps({"plug": {"K": "v"}}), encoding="utf-8")

        with patch.dict("os.environ", {"CPA_SECRET_FILEPATH": ""}), patch.object(tested, "_SECRETS_DIR", tmp_path):
            result = tested.get_secrets(secret_names=["K"], instance="inst", plugin_name="plug")

        expected = {"K": "v"}
        assert result == expected


class TestResolveFile:
    """Tests for SecretRequester._resolve_file."""

    def test__resolve_file__env_var_set(self) -> None:
        """Return path from CPA_SECRET_FILEPATH when set."""
        tested = SecretRequester

        with patch.dict("os.environ", {"CPA_SECRET_FILEPATH": "/custom/path.json"}):
            result = tested._resolve_file("any-instance")

        expected = Path("/custom/path.json")
        assert result == expected

    def test__resolve_file__default_path(self, tmp_path: Path) -> None:
        """Return default path when env var is not set."""
        tested = SecretRequester

        with patch.dict("os.environ", {}, clear=False), patch.object(tested, "_SECRETS_DIR", tmp_path):
            import os
            os.environ.pop("CPA_SECRET_FILEPATH", None)
            result = tested._resolve_file("my-instance")

        expected = tmp_path / "my-instance.json"
        assert result == expected


class TestReadFile:
    """Tests for SecretRequester._read_file."""

    def test__read_file__missing(self, tmp_path: Path) -> None:
        """Return empty dict when the file does not exist."""
        tested = SecretRequester

        result = tested._read_file(tmp_path / "nonexistent.json")

        expected: dict = {}
        assert result == expected

    def test__read_file__valid_json(self, tmp_path: Path) -> None:
        """Return parsed JSON content from existing file."""
        tested = SecretRequester
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps({"plug": {"KEY": "val"}}), encoding="utf-8")

        result = tested._read_file(secrets_file)

        expected = {"plug": {"KEY": "val"}}
        assert result == expected

    def test__read_file__invalid_json(self, tmp_path: Path) -> None:
        """Return empty dict when file contains invalid JSON."""
        tested = SecretRequester
        secrets_file = tmp_path / "bad.json"
        secrets_file.write_text("not-json{{{", encoding="utf-8")

        result = tested._read_file(secrets_file)

        expected: dict = {}
        assert result == expected


class TestSyncKeys:
    """Tests for SecretRequester._sync_keys."""

    def test__sync_keys__preserves_existing(self) -> None:
        """Preserve values for keys that already exist."""
        tested = SecretRequester

        result = tested._sync_keys({"A": "val_a", "B": "val_b"}, ["A", "B"])

        expected = {"A": "val_a", "B": "val_b"}
        assert result == expected

    def test__sync_keys__adds_missing(self) -> None:
        """Add missing keys with empty string values."""
        tested = SecretRequester

        result = tested._sync_keys({}, ["NEW_KEY"])

        expected = {"NEW_KEY": ""}
        assert result == expected

    def test__sync_keys__removes_stale(self) -> None:
        """Exclude keys not in the requested list."""
        tested = SecretRequester

        result = tested._sync_keys({"KEEP": "v", "DROP": "x"}, ["KEEP"])

        expected = {"KEEP": "v"}
        assert result == expected

    def test__sync_keys__both_empty(self) -> None:
        """Return empty dict when both inputs are empty."""
        tested = SecretRequester

        result = tested._sync_keys({}, [])

        expected: dict = {}
        assert result == expected


class TestWriteFile:
    """Tests for SecretRequester._write_file."""

    def test__write_file__writes_json(self, tmp_path: Path) -> None:
        """Write formatted JSON ending with a newline."""
        tested = SecretRequester
        secrets_file = tmp_path / "out.json"

        tested._write_file(secrets_file, {"plug": {"K": "V"}})

        content = secrets_file.read_text(encoding="utf-8")
        expected = True
        assert content.endswith("\n") is expected
        exp_parsed = {"plug": {"K": "V"}}
        assert json.loads(content) == exp_parsed

    def test__write_file__creates_parent_dirs(self, tmp_path: Path) -> None:
        """Create parent directories when they do not exist."""
        tested = SecretRequester
        secrets_file = tmp_path / "deep" / "nested" / "out.json"

        tested._write_file(secrets_file, {"plug": {}})

        result = secrets_file.exists()
        expected = True
        assert result is expected

    def test__write_file__silently_handles_os_error(self, tmp_path: Path) -> None:
        """Do not raise on OSError (e.g., permission denied)."""
        tested = SecretRequester

        with patch.object(Path, "mkdir", side_effect=OSError("permission denied")) as mock_mkdir:
            tested._write_file(tmp_path / "out.json", {"plug": {}})

        exp_mkdir_calls = [call(parents=True, exist_ok=True)]
        assert mock_mkdir.mock_calls == exp_mkdir_calls
