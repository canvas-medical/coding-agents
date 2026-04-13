"""Gather secret values for Canvas SDK plugin deployment."""

import json
import os
from pathlib import Path

from constants import Constants


class SecretRequester:
    """Retrieve secret values from per-instance JSON files.

    Secret values are read from the file at CPA_SECRET_FILEPATH (env var),
    or from ~/.canvas/plugin-secrets/<instance>.json if the env var is
    not defined or empty.

    Each file is keyed by plugin name, then secret name:
        {
            "my_plugin": {
                "MY_API_KEY": "sk-...",
                "WEBHOOK_SECRET": "abc..."
            },
            "other_plugin": {
                "TOKEN": "xyz..."
            }
        }

    The plugin section is kept in sync with the requested secret names:
    stale entries are removed and missing entries are added with empty values.
    """

    _SECRETS_DIR: Path = Path.home() / ".canvas" / "plugin-secrets"

    @classmethod
    def get_secrets(cls, secret_names: list[str], instance: str, plugin_name: str) -> dict[str, str]:
        """Get secret values for the given plugin, secret names, and instance.

        Creates the secrets file if it does not exist. Before returning,
        the plugin section is updated to contain exactly the requested
        secret names: stale keys are removed and missing keys are added
        with empty values.

        Args:
            secret_names: List of secret names to retrieve.
            instance: Canvas instance hostname used to locate the secrets file.
            plugin_name: Plugin name used as the top-level key in the file.

        Returns:
            Mapping of secret names to their non-empty values.
        """
        if not secret_names:
            return {}

        secrets_file = cls._resolve_file(instance)
        all_plugins = cls._read_file(secrets_file)
        stored: dict[str, str] = all_plugins.get(plugin_name) or {}
        synced = cls._sync_keys(stored, secret_names)
        all_plugins[plugin_name] = synced
        cls._write_file(secrets_file, all_plugins)

        result: dict[str, str] = {}
        for name in secret_names:
            value = synced.get(name) or ""
            if value:
                result[name] = value
        return result

    @classmethod
    def _resolve_file(cls, instance: str) -> Path:
        """Return the secrets file path from CPA_SECRET_FILEPATH or the default location."""
        env_path = os.environ.get(Constants.CPA_SECRET_FILEPATH) or ""
        if env_path:
            return Path(env_path)
        return cls._SECRETS_DIR / f"{instance}.json"

    @classmethod
    def _read_file(cls, secrets_file: Path) -> dict[str, dict[str, str]]:
        """Read the secrets file, returning empty dict if missing or invalid."""
        if not secrets_file.exists():
            return {}
        try:
            return json.loads(secrets_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    @classmethod
    def _sync_keys(cls, stored: dict[str, str], secret_names: list[str]) -> dict[str, str]:
        """Return a dict containing exactly the requested keys, preserving existing values."""
        result: dict[str, str] = {}
        for name in secret_names:
            result[name] = stored.get(name) or ""
        return result

    @classmethod
    def _write_file(cls, secrets_file: Path, secrets: dict[str, dict[str, str]]) -> None:
        """Write the secrets dict to the JSON file, creating directories as needed."""
        try:
            secrets_file.parent.mkdir(parents=True, exist_ok=True)
            secrets_file.write_text(json.dumps(secrets, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass
