"""MCP server for Canvas SDK plugin installation with secret management."""

import asyncio
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from secret_requester import SecretRequester


class CanvasInstallerMcp:
    """MCP server providing tools to install and list Canvas SDK plugins.

    Secret values are gathered from ~/.canvas/plugin-secrets/<instance>.json
    and injected into the canvas install command without exposing them to Claude Code.
    """

    @classmethod
    def _parse_secret_names(cls, raw_value: object) -> list[str]:
        """Parse secret names from the CANVAS_MANIFEST.json secrets field."""
        if isinstance(raw_value, list):
            return [str(item).strip() for item in raw_value if str(item).strip()]
        if isinstance(raw_value, str):
            result = [item.strip() for item in raw_value.replace("\n", ",").split(",")]
            return [item for item in result if item]
        return []

    @classmethod
    async def _run_canvas_command(cls, command: list[str], cwd: str) -> str:
        """Run a canvas CLI command and return its output."""
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
            plugin_name: The plugin inner folder name (snake_case).
            instance: Target Canvas instance hostname from ~/.canvas/credentials.ini.
            cwd: Working directory (plugin container directory).
        """
        if not plugin_name:
            return "Error: missing plugin_name"
        if not instance:
            return "Error: missing instance"
        if not cwd:
            return "Error: missing cwd"

        plugin_dir = Path(cwd) / plugin_name
        if not plugin_dir.exists():
            return f"Error: plugin directory not found: {plugin_dir}"

        manifest_file = plugin_dir / "CANVAS_MANIFEST.json"
        if not manifest_file.exists():
            return f"Error: manifest not found: {manifest_file}"

        manifest: dict = json.loads(manifest_file.read_text(encoding="utf-8"))
        secret_names = cls._parse_secret_names(manifest.get("secrets") or [])

        values: dict[str, str] = {}
        if secret_names:
            values = SecretRequester.get_secrets(secret_names, instance, plugin_name)

        command = ["uv", "run", "canvas", "install", plugin_name, "--host", instance]
        provided: list[str] = []
        skipped: list[str] = []
        for name in secret_names:
            value = values.get(name) or ""
            if value:
                command.extend(["--secret", f"{name}={value}"])
                provided.append(name)
            else:
                skipped.append(name)

        result = await cls._run_canvas_command(command=command, cwd=cwd)
        warning = ""
        if skipped:
            warning = f"\nWarning: secrets not provided (missing or empty): {', '.join(skipped)}"
        return f"Install output:\n{result}{warning}"

    @classmethod
    async def list_plugins(cls, instance: str, cwd: str) -> str:
        """List installed Canvas SDK plugins on a Canvas instance.

        Args:
            instance: Target Canvas instance hostname.
            cwd: Working directory.
        """
        if not instance:
            return "Error: missing instance"
        if not cwd:
            return "Error: missing cwd"

        result = await cls._run_canvas_command(
            command=["uv", "run", "canvas", "list", "--host", instance],
            cwd=cwd,
        )
        return f"Installed plugins:\n{result}"

    @classmethod
    def create_server(cls) -> FastMCP:
        """Create and configure the FastMCP server with canvas tools."""
        server = FastMCP("canvas_cmd_line")

        @server.tool()
        async def installer(plugin_name: str, instance: str, cwd: str) -> str:
            """Install a Canvas SDK plugin on a Canvas instance with its secrets.

            Reads secret names from CANVAS_MANIFEST.json and retrieves their values
            from ~/.canvas/plugin-secrets/<instance>.json. The secret values are
            passed to the canvas install command but never returned in the output.

            Args:
                plugin_name: The plugin inner folder name (snake_case).
                instance: Target Canvas instance hostname from ~/.canvas/credentials.ini.
                cwd: Working directory (plugin container directory).
            """
            return await cls.install(plugin_name, instance, cwd)

        @server.tool()
        async def lister(instance: str, cwd: str) -> str:
            """List installed Canvas SDK plugins on a Canvas instance.

            Args:
                instance: Target Canvas instance hostname.
                cwd: Working directory.
            """
            return await cls.list_plugins(instance, cwd)

        return server


if __name__ == "__main__":
    CanvasInstallerMcp.create_server().run()
