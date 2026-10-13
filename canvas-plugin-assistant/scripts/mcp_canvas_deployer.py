"""MCP server that deploys Canvas plugins through Canvas Platform and sets their variables without exposing secret values."""

import asyncio
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from secret_requester import SecretRequester


class CanvasDeployerMcp:
    """MCP server providing tools to deploy Canvas plugins and set their variables.

    Variable values are gathered from ~/.canvas/plugin-secrets/<instance>.json
    and passed to the canvas config set command without exposing them to Claude Code.
    """

    CONSENT_PENDING_MARKER: str = "is waiting on these requests"
    CONSENT_NOTE: str = (
        "Consent needed: this deployment is waiting on custom data access consent that only a person at a "
        "terminal can answer. Show the requests above to the user and have them run the command below in "
        "their own terminal. Do not retry with --yes."
    )

    @classmethod
    def _parse_variable_names(cls, manifest: dict) -> list[str]:
        """Return the list of variable names declared in a manifest.

        Reads the modern `variables: [{name, sensitive?, default?}, ...]`
        schema. Falls back to the legacy `secrets: [name, ...]` array
        for unmigrated plugins, but emits no values for it — always use
        `variables` (`canvas validate` warns on a legacy `secrets`-only
        manifest).
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
    def _plugin_manifest(cls, plugin_name: str, instance: str, cwd: str) -> tuple[Path, dict] | str:
        """Validate the tool arguments and load the plugin manifest.

        Args:
            plugin_name: The inner package folder name, `<prefix>__<name>`, which is also the manifest name.
            instance: Target Canvas Platform instance slug.
            cwd: Working directory (plugin container directory).

        Returns:
            tuple[Path, dict] | str: The manifest path and parsed manifest, or an error message.
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
        return manifest_file, manifest

    @classmethod
    async def _configure(cls, plugin_name: str, instance: str, cwd: str, manifest: dict) -> str:
        """Set the manifest variables on the instance from the secrets file.

        Values are passed to the CLI and never included in the returned text.

        Args:
            plugin_name: The inner package folder name, `<prefix>__<name>`, which is also the manifest name.
            instance: Target Canvas Platform instance slug.
            cwd: Working directory (plugin container directory).
            manifest: Parsed CANVAS_MANIFEST.json.

        Returns:
            str: The configure output, or a note that nothing was set.
        """
        names = cls._parse_variable_names(manifest)
        values: dict[str, str] = {}
        if names:
            values = SecretRequester.get_secrets(names, instance, plugin_name)

        provided = [name for name in names if values.get(name)]
        skipped = [name for name in names if not values.get(name)]
        warning = ""
        if skipped:
            warning = f"\nWarning: secrets not provided (missing or empty): {', '.join(skipped)}"
        if not provided:
            return f"Configure skipped: no variable values found in the secrets file.{warning}"

        command = ["uv", "run", "canvas", "config", "set", plugin_name]
        command.extend(f"{name}={values[name]}" for name in provided)
        command.extend(["--instance", instance])
        result = await cls._run_canvas_command(command=command, cwd=cwd)
        return f"Configure output:\n{result}{warning}"

    @classmethod
    async def deploy(cls, plugin_name: str, instance: str, cwd: str) -> str:
        """Deploy a Canvas plugin to a Canvas Platform instance, then set its variables.

        Variables are set only when the deploy succeeds. A deploy that stops on pending
        custom data consent is handed back to the person with the command to run.

        Args:
            plugin_name: The inner package folder name, `<prefix>__<name>`, which is also the manifest name.
            instance: Target Canvas Platform instance slug.
            cwd: Working directory (plugin container directory).

        Returns:
            str: The deploy output followed by the configure output or the consent note.
        """
        checked = cls._plugin_manifest(plugin_name, instance, cwd)
        if isinstance(checked, str):
            return checked
        _, manifest = checked

        result = await cls._run_canvas_command(
            command=["uv", "run", "canvas", "deploy", plugin_name, "--instance", instance],
            cwd=cwd,
        )
        output = f"Deploy output:\n{result}"
        if cls.CONSENT_PENDING_MARKER in result:
            return (
                f"{output}\n\n{cls.CONSENT_NOTE}\n"
                f"  cd {cwd} && uv run canvas deploy {plugin_name} --no-push --instance {instance}\n"
                "After it succeeds there, call the configurer tool to set variables."
            )
        if result.startswith("Command failed"):
            return output
        return f"{output}\n\n{await cls._configure(plugin_name, instance, cwd, manifest)}"

    @classmethod
    async def configure(cls, plugin_name: str, instance: str, cwd: str) -> str:
        """Set a Canvas plugin's manifest variables on a Canvas Platform instance.

        Args:
            plugin_name: The inner package folder name, `<prefix>__<name>`, which is also the manifest name.
            instance: Target Canvas Platform instance slug.
            cwd: Working directory (plugin container directory).

        Returns:
            str: The configure output, or an error message.
        """
        checked = cls._plugin_manifest(plugin_name, instance, cwd)
        if isinstance(checked, str):
            return checked
        _, manifest = checked
        return await cls._configure(plugin_name, instance, cwd, manifest)

    @classmethod
    def create_server(cls) -> FastMCP:
        """Create and configure the FastMCP server with canvas tools."""
        server = FastMCP("canvas_cmd_line")

        @server.tool()
        async def deployer(plugin_name: str, instance: str, cwd: str) -> str:
            """Deploy a Canvas plugin to a Canvas Platform instance and set its variables.

            Runs canvas deploy, then canvas config set for the variables declared in
            CANVAS_MANIFEST.json. The instance is a Canvas Platform instance slug. Values
            come from ~/.canvas/plugin-secrets/<instance>.json keyed by plugin name and are
            never returned in the output. Consent requests for custom data access are never
            answered here: they are returned for the user to answer in their own terminal.

            Args:
                plugin_name: The inner package folder name, `<prefix>__<name>`, which is also the manifest name.
                instance: Canvas Platform instance slug.
                cwd: Working directory (plugin container directory).
            """
            return await cls.deploy(plugin_name, instance, cwd)

        @server.tool()
        async def configurer(plugin_name: str, instance: str, cwd: str) -> str:
            """Set a deployed Canvas plugin's variables on a Canvas Platform instance.

            Runs canvas config set for the variables declared in CANVAS_MANIFEST.json. The
            instance is a Canvas Platform instance slug. Values come from
            ~/.canvas/plugin-secrets/<instance>.json keyed by plugin name and are never
            returned in the output. Use it after the user approves a pending consent request.

            Args:
                plugin_name: The inner package folder name, `<prefix>__<name>`, which is also the manifest name.
                instance: Canvas Platform instance slug.
                cwd: Working directory (plugin container directory).
            """
            return await cls.configure(plugin_name, instance, cwd)

        return server


if __name__ == "__main__":
    CanvasDeployerMcp.create_server().run()
