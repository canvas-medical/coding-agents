"""MCP server that deploys Canvas plugins through Canvas Platform and sets their variables without exposing secret values."""

import asyncio
import json
import shlex
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from mcp_canvas_installer import CanvasInstallerMcp
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

    STILL_RUNNING_MARKER: str = "is still running after"
    STILL_RUNNING_NOTE: str = (
        "Still running: the deployment is still running on Canvas Platform, so variables were not set. "
        "Call the configurer tool once the deployment succeeds."
    )

    UNCOMMITTED_MARKER: str = "You have uncommitted changes"
    UNCOMMITTED_NOTE: str = (
        "Uncommitted files: canvas deploy refuses any uncommitted or untracked file in the repository. "
        "Do not retry with --yes: it commits every file, including ones the user left out, and pushes them "
        "to Canvas Platform. Commit the files the user approves and add the rest to .git/info/exclude, "
        "then call the deployer tool again."
    )

    # A plugin inside a larger repository deploys with --snapshot, whose refusals
    # are in canvas_cli/apps/platform/git.py (snapshot_source, _guard_platform_history).
    SNAPSHOT_UNCOMMITTED_MARKERS: tuple[str, ...] = (
        "--snapshot deploys only committed work",
        "has no committed files",
    )
    SNAPSHOT_UNCOMMITTED_NOTE: str = (
        "Uncommitted snapshot: --snapshot deploys only the package as committed, and the CLI never commits in "
        "the larger repository. Show the user the files above and ask whether to commit them there. Do not "
        "retry with --yes, then call the deployer tool again once the package is committed."
    )

    SNAPSHOT_UNSUPPORTED_MARKER: str = "--snapshot cannot deploy this plugin as committed"
    SNAPSHOT_UNSUPPORTED_NOTE: str = (
        "Unsupported snapshot entries: a submodule, symbolic link, or file stored through a filter (Git LFS, "
        "git-crypt) cannot reach an instance as its content. The user must replace each path above with a "
        "regular committed file before deploying."
    )

    SNAPSHOT_ROLLBACK_MARKER: str = "would roll the plugin back"
    SNAPSHOT_ROLLBACK_NOTE: str = (
        "Rollback refused: Canvas Platform was last deployed from a commit whose changes this checkout lacks. "
        "The user must update the checkout to include them, such as with git pull, then deploy again."
    )

    SNAPSHOT_REPLACES_MARKER: str = "This snapshot would replace them"
    SNAPSHOT_REPLACES_NOTE: str = (
        "Platform changes would be replaced: files above were changed on Canvas Platform, and only a person at "
        "a terminal can confirm replacing them. Show the files to the user and have them run the command below "
        "in their own terminal, or copy Canvas Platform's versions into the package and commit them. Do not "
        "call the deployer tool again for this."
    )

    @classmethod
    async def _in_larger_repo(cls, plugin_dir: Path, cwd: str) -> bool:
        """Whether the plugin sits inside a git repository rooted somewhere other than `cwd`.

        `canvas deploy` refuses such a package unless it is passed `--snapshot`
        (canvas_cli/apps/platform/commands.py `_require_package_at_repo_root`).

        Args:
            plugin_dir (Path): The package folder.
            cwd (str): The plugin container directory, where a standalone plugin's repository is rooted.

        Returns:
            bool: True when `git rev-parse --show-toplevel` names a directory other than `cwd`, compared
                by file identity so a symlinked or differently cased `cwd` still matches its own root.
        """
        process = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            str(plugin_dir),
            "rev-parse",
            "--show-toplevel",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout_bytes, _ = await process.communicate()
        toplevel: str = stdout_bytes.decode("utf-8", errors="replace").strip()
        if process.returncode != 0 or not toplevel:
            return False
        return not Path(toplevel).samefile(cwd)

    @classmethod
    def _with_status(cls, text: str, status: str) -> str:
        """End a tool result with its one machine-readable status line.

        The deploy prose routes only on this line, never on the CLI text above it.

        Args:
            text (str): The tool result.
            status (str): One of the documented statuses, such as `deployed` or `deploy_failed`.

        Returns:
            str: The result followed by `Status: <status>`.
        """
        return f"{text}\n\nStatus: {status}"

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
            plugin_name: The inner package folder name, which holds CANVAS_MANIFEST.json.
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

        try:
            manifest: dict = json.loads(manifest_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            return f"Error: manifest is not valid JSON: {manifest_file}: {error}"
        return manifest_file, manifest

    @classmethod
    async def _configure(cls, instance: str, cwd: str, manifest: dict) -> tuple[str, bool]:
        """Set the manifest variables on the instance from the secrets file.

        Variables are keyed by the manifest name, which is the name Canvas Platform manages the plugin under.
        Values are passed to the CLI and never included in the returned text.

        Args:
            instance: Target Canvas Platform instance slug.
            cwd: Working directory (plugin container directory).
            manifest: Parsed CANVAS_MANIFEST.json.

        Returns:
            tuple[str, bool]: The configure output or a note that nothing was set, and whether `canvas config set` failed.
        """
        manifest_name: str = manifest["name"]
        names = cls._parse_variable_names(manifest)
        values: dict[str, str] = {}
        if names:
            values = SecretRequester.get_secrets(names, instance, manifest_name)

        provided = [name for name in names if values.get(name)]
        skipped = [name for name in names if not values.get(name)]
        warning = ""
        if skipped:
            warning = f"\nWarning: secrets not provided (missing or empty): {', '.join(skipped)}"
        if not provided:
            return f"Configure skipped: no variable values found in the secrets file.{warning}", False

        command = ["uv", "run", "canvas", "config", "set", manifest_name]
        command.extend(f"{name}={values[name]}" for name in provided)
        command.extend(["--instance", instance])
        result = await cls._run_canvas_command(command=command, cwd=cwd)
        return f"Configure output:\n{result}{warning}", result.startswith("Command failed")

    @classmethod
    async def deploy(cls, plugin_name: str, instance: str, cwd: str) -> str:
        """Deploy a Canvas plugin to a Canvas Platform instance, then set its variables.

        Variables are set only when the deploy succeeds. A deploy that stops on pending
        custom data consent is handed back to the person with the command to run, and a
        deploy still running on Canvas Platform is left for the configurer tool. A plugin
        inside a larger repository, such as a monorepo, deploys with `--snapshot`.

        Args:
            plugin_name: The inner package folder name, which is the folder passed to `canvas deploy`. Variables are keyed by the manifest name.
            instance: Target Canvas Platform instance slug.
            cwd: Working directory (plugin container directory).

        Returns:
            str: The deploy output followed by the configure output or a note for the status, ending with a
                `Status:` line: `invalid_input`, `consent_pending`, `still_running`, `dirty_tree`,
                `snapshot_uncommitted`, `snapshot_unsupported`, `snapshot_rollback`,
                `snapshot_replaces_platform`, `deploy_failed`, `configure_failed`, or `deployed`.
        """
        checked = cls._plugin_manifest(plugin_name, instance, cwd)
        if isinstance(checked, str):
            return cls._with_status(checked, "invalid_input")
        manifest_file, manifest = checked

        snapshot: bool = await cls._in_larger_repo(manifest_file.parent, cwd)
        snapshot_flag: list[str] = ["--snapshot"] if snapshot else []
        result = await cls._run_canvas_command(
            command=["uv", "run", "canvas", "deploy", plugin_name, *snapshot_flag, "--instance", instance],
            cwd=cwd,
        )
        output = f"Deploy output:\n{result}"
        if cls.CONSENT_PENDING_MARKER in result:
            consent = (
                f"{output}\n\n{cls.CONSENT_NOTE}\n"
                f"  cd {shlex.quote(cwd)} && uv run canvas deploy {shlex.quote(plugin_name)} "
                f"--no-push --instance {shlex.quote(instance)}\n"
                "After it succeeds there, call the configurer tool to set variables."
            )
            return cls._with_status(consent, "consent_pending")
        if cls.STILL_RUNNING_MARKER in result:
            return cls._with_status(f"{output}\n\n{cls.STILL_RUNNING_NOTE}", "still_running")
        if any(marker in result for marker in cls.SNAPSHOT_UNCOMMITTED_MARKERS):
            return cls._with_status(f"{output}\n\n{cls.SNAPSHOT_UNCOMMITTED_NOTE}", "snapshot_uncommitted")
        if cls.SNAPSHOT_UNSUPPORTED_MARKER in result:
            return cls._with_status(f"{output}\n\n{cls.SNAPSHOT_UNSUPPORTED_NOTE}", "snapshot_unsupported")
        if cls.SNAPSHOT_ROLLBACK_MARKER in result:
            return cls._with_status(f"{output}\n\n{cls.SNAPSHOT_ROLLBACK_NOTE}", "snapshot_rollback")
        if cls.SNAPSHOT_REPLACES_MARKER in result:
            replaces = (
                f"{output}\n\n{cls.SNAPSHOT_REPLACES_NOTE}\n"
                f"  cd {shlex.quote(cwd)} && uv run canvas deploy {shlex.quote(plugin_name)} "
                f"--snapshot --instance {shlex.quote(instance)}\n"
                "After it succeeds there, call the configurer tool to set variables."
            )
            return cls._with_status(replaces, "snapshot_replaces_platform")
        if cls.UNCOMMITTED_MARKER in result:
            return cls._with_status(f"{output}\n\n{cls.UNCOMMITTED_NOTE}", "dirty_tree")
        if result.startswith("Command failed"):
            return cls._with_status(output, "deploy_failed")
        configured, failed = await cls._configure(instance, cwd, manifest)
        return cls._with_status(f"{output}\n\n{configured}", "configure_failed" if failed else "deployed")

    @classmethod
    async def configure(cls, plugin_name: str, instance: str, cwd: str) -> str:
        """Set a Canvas plugin's manifest variables on a Canvas Platform instance.

        Args:
            plugin_name: The inner package folder name, which holds CANVAS_MANIFEST.json. Variables are keyed by the manifest name.
            instance: Target Canvas Platform instance slug.
            cwd: Working directory (plugin container directory).

        Returns:
            str: The configure output or an error message, ending with a `Status:` line: `invalid_input`,
                `configure_failed`, or `configured`.
        """
        checked = cls._plugin_manifest(plugin_name, instance, cwd)
        if isinstance(checked, str):
            return cls._with_status(checked, "invalid_input")
        _, manifest = checked
        configured, failed = await cls._configure(instance, cwd, manifest)
        return cls._with_status(configured, "configure_failed" if failed else "configured")

    @classmethod
    def create_server(cls) -> FastMCP:
        """Create and configure the FastMCP server with canvas tools."""
        server = FastMCP("canvas_cmd_line")

        @server.tool()
        async def deployer(plugin_name: str, instance: str, cwd: str) -> str:
            """Deploy a Canvas plugin to a Canvas Platform instance and set its variables.

            Runs canvas deploy, then canvas config set for the variables declared in
            CANVAS_MANIFEST.json. The instance is a Canvas Platform instance slug. Values
            come from ~/.canvas/plugin-secrets/<instance>.json keyed by manifest name and are
            never returned in the output. Consent requests for custom data access are never
            answered here: they are returned for the user to answer in their own terminal.
            A plugin inside a larger repository, such as a monorepo, deploys with --snapshot.
            The output ends with one `Status:` line: invalid_input, consent_pending,
            still_running, dirty_tree, snapshot_uncommitted, snapshot_unsupported,
            snapshot_rollback, snapshot_replaces_platform, deploy_failed, configure_failed,
            or deployed.

            Args:
                plugin_name: The inner package folder name. Variables are keyed by the manifest name.
                instance: Canvas Platform instance slug.
                cwd: Working directory (plugin container directory).
            """
            return await cls.deploy(plugin_name, instance, cwd)

        @server.tool()
        async def configurer(plugin_name: str, instance: str, cwd: str) -> str:
            """Set a deployed Canvas plugin's variables on a Canvas Platform instance.

            Runs canvas config set for the variables declared in CANVAS_MANIFEST.json. The
            instance is a Canvas Platform instance slug. Values come from
            ~/.canvas/plugin-secrets/<instance>.json keyed by manifest name and are never
            returned in the output. Use it after the user approves a pending consent request.
            The output ends with one `Status:` line: invalid_input, configure_failed, or configured.

            Args:
                plugin_name: The inner package folder name. Variables are keyed by the manifest name.
                instance: Canvas Platform instance slug.
                cwd: Working directory (plugin container directory).
            """
            return await cls.configure(plugin_name, instance, cwd)

        @server.tool()
        async def installer(plugin_name: str, instance: str, cwd: str) -> str:
            """Install a legacy Canvas SDK plugin (no organization prefix) with canvas install, for /cpa:deploy-legacy.

            Reads secret names from CANVAS_MANIFEST.json and retrieves their values
            from ~/.canvas/plugin-secrets/<instance>.json. The secret values are
            passed to the canvas install command but never returned in the output.
            canvas install and credentials.ini stop working on December 14, 2026.
            The output ends with one `Status:` line: invalid_input, install_failed, or installed.

            Args:
                plugin_name: The plugin inner folder name (snake_case).
                instance: Target Canvas instance hostname from ~/.canvas/credentials.ini.
                cwd: Working directory (plugin container directory).
            """
            return await CanvasInstallerMcp.install(plugin_name, instance, cwd)

        return server


if __name__ == "__main__":
    CanvasDeployerMcp.create_server().run()
