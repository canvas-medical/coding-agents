"""The `installer` tool behind /cpa:deploy-legacy: canvas install with secret management, until December 14, 2026."""

import asyncio
import json
from pathlib import Path

from secret_requester import SecretRequester


class CanvasInstallerMcp:
    """Installs legacy Canvas SDK plugins (no organization prefix) with `canvas install`.

    Secret values are gathered from ~/.canvas/plugin-secrets/<instance>.json
    and injected into the canvas install command without exposing them to Claude Code.
    The `installer` tool is registered on the `canvas_cmd_line` server in mcp_canvas_deployer.py.
    """

    @classmethod
    def _with_status(cls, text: str, status: str) -> str:
        """End a tool result with its one machine-readable status line.

        The legacy deploy prose routes only on this line, never on the CLI text above it.

        Args:
            text (str): The tool result.
            status (str): One of `invalid_input`, `install_failed`, or `installed`.

        Returns:
            str: The result followed by `Status: <status>`.
        """
        return f"{text}\n\nStatus: {status}"

    @classmethod
    def _parse_variable_names(cls, manifest: dict) -> list[str]:
        """Return the list of variable names declared in a manifest.

        Reads the modern `variables: [{name, sensitive?, default?}, ...]`
        schema. Falls back to the legacy `secrets: [name, ...]` array
        for unmigrated plugins, but emits no values for it: always use
        `variables` (`canvas validate` warns on a legacy `secrets`-only
        manifest).

        Args:
            manifest (dict): The parsed CANVAS_MANIFEST.json.

        Returns:
            list[str]: The declared variable names.
        """
        variables = manifest.get("variables")
        if isinstance(variables, list) and variables:
            names: list[str] = []
            for entry in variables:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("name")
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())
            return names
        raw_secrets = manifest.get("secrets")
        if isinstance(raw_secrets, list):
            return [str(item).strip() for item in raw_secrets if str(item).strip()]
        if isinstance(raw_secrets, str):
            result = [item.strip() for item in raw_secrets.replace("\n", ",").split(",")]
            return [item for item in result if item]
        return []

    @classmethod
    async def _run_canvas_command(cls, command: list[str], cwd: str) -> str:
        """Run a canvas CLI command and return its output.

        Args:
            command (list[str]): The command and its arguments.
            cwd (str): The directory to run it in.

        Returns:
            str: The combined output, prefixed with `Command failed with exit code N` on failure,
                or `Invalid cwd: <path>` when the directory does not exist.
        """
        cwd_path = Path(cwd)
        if not cwd_path.exists() or not cwd_path.is_dir():
            return f"Invalid cwd: {cwd_path}"

        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=str(cwd_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await process.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
        stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
        output_parts = [value for value in [stdout, stderr] if value]
        result = "\n".join(output_parts).strip() or "(no output)"

        if process.returncode == 0:
            return result
        return f"Command failed with exit code {process.returncode}\n{result}"

    @classmethod
    async def install(cls, plugin_name: str, instance: str, cwd: str) -> str:
        """Install a Canvas SDK plugin on a Canvas instance with its secrets.

        Args:
            plugin_name (str): The plugin inner folder name (snake_case).
            instance (str): Target Canvas instance hostname from ~/.canvas/credentials.ini.
            cwd (str): Working directory (plugin container directory).

        Returns:
            str: The install output or an error message, ending with a `Status:` line: `invalid_input`,
                `install_failed`, or `installed`.
        """
        if not plugin_name:
            return cls._with_status("Error: missing plugin_name", "invalid_input")
        if not instance:
            return cls._with_status("Error: missing instance", "invalid_input")
        if not cwd:
            return cls._with_status("Error: missing cwd", "invalid_input")

        plugin_dir = Path(cwd) / plugin_name
        if not plugin_dir.exists():
            return cls._with_status(f"Error: plugin directory not found: {plugin_dir}", "invalid_input")

        manifest_file = plugin_dir / "CANVAS_MANIFEST.json"
        if not manifest_file.exists():
            return cls._with_status(f"Error: manifest not found: {manifest_file}", "invalid_input")

        manifest: dict = json.loads(manifest_file.read_text(encoding="utf-8"))
        secret_names: list[str] = cls._parse_variable_names(manifest)

        values: dict[str, str] = {}
        if secret_names:
            values = SecretRequester.get_secrets(secret_names, instance, plugin_name)

        command: list[str] = ["uv", "run", "canvas", "install", plugin_name, "--host", instance]
        skipped: list[str] = []
        for name in secret_names:
            value = values.get(name) or ""
            if value:
                command.extend(["--secret", f"{name}={value}"])
            else:
                skipped.append(name)

        result: str = await cls._run_canvas_command(command=command, cwd=cwd)
        warning: str = ""
        if skipped:
            warning = f"\nWarning: secrets not provided (missing or empty): {', '.join(skipped)}"
        failed: bool = result.startswith(("Command failed with exit code", "Invalid cwd:"))
        return cls._with_status(f"Install output:\n{result}{warning}", "install_failed" if failed else "installed")
