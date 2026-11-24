"""MCP server that deploys Canvas plugins through Canvas Platform and sets their variables without exposing secret values."""

import asyncio
import json
import shlex
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

    STILL_RUNNING_MARKER: str = "is still running after"
    STILL_RUNNING_NOTE: str = (
        "Still running: the deployment is still running on Canvas Platform, so variables were not set."
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

    # Variables are read from the working-tree manifest, which can have moved past the released version.
    VERSION_NOT_CONFIGURED_NOTE: str = (
        "Variables not set: the working-tree CANVAS_MANIFEST.json is not version {version}, so its variables "
        "may not match the ones {version} declares. Set each variable {version} declares in the user's own "
        "terminal:"
    )

    @classmethod
    def _version_not_configured(cls, manifest: dict, instance: str, version: str) -> str | None:
        """The hand-off for a released version whose variables the working-tree manifest cannot describe.

        Args:
            manifest (dict): The working-tree CANVAS_MANIFEST.json.
            instance (str): Target Canvas Platform instance slug.
            version (str): The released version deployed, or empty for a branch or release deploy.

        Returns:
            str | None: The note and `canvas config set` command for the user to run, or None when the
                variables can be set from the working-tree manifest.
        """
        if not version or manifest.get("version") == version:
            return None
        return (
            f"{cls.VERSION_NOT_CONFIGURED_NOTE.format(version=version)}\n"
            f"  canvas config set {shlex.quote(manifest['name'])} KEY=value --instance {shlex.quote(instance)}"
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
        for unmigrated plugins, but emits no values for it; always use
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
    async def deploy(cls, plugin_name: str, instance: str, cwd: str, branch: str = "", version: str = "") -> str:
        """Deploy a Canvas plugin to a Canvas Platform instance, then set its variables.

        Variables are set only when the deploy succeeds, and for a version only when the
        working-tree manifest is that version, since variables are read from it. A deploy
        that stops on pending custom data consent is handed back to the person with the command to run, and a
        deploy still running on Canvas Platform is left for the configurer tool. A plugin
        inside a larger repository, such as a monorepo, deploys with `--snapshot`. An
        empty branch pushes to `main`, the release path. A branch is pushed under that name
        and Canvas Platform deploys it only to test instances; the CLI refuses `main` and
        invalid names (canvas_cli/apps/platform/commands.py:824-840 at 1.13.0). A version
        deploys an already released version with `--plugin <name>@<version>`, which takes no
        folder and pushes nothing, and excludes `--snapshot` and `--branch`
        (canvas_cli/apps/platform/commands.py:985-993, 1098-1117 at 1.13.0).

        Args:
            plugin_name: The inner package folder name, which is the folder passed to `canvas deploy`. Variables are keyed by the manifest name.
            instance: Target Canvas Platform instance slug.
            cwd: Working directory (plugin container directory).
            branch: The work branch to deploy as, passed to `canvas deploy --branch` as one argument. Empty pushes to `main`.
            version: A released version, such as `1.4.0`, to deploy as the manifest name at that version. Empty deploys the folder. Cannot be combined with `branch`.

        Returns:
            str: The deploy output followed by the configure output or a note for the status, ending with a
                `Status:` line: `invalid_input`, `consent_pending`, `still_running`, `dirty_tree`,
                `snapshot_uncommitted`, `snapshot_unsupported`, `snapshot_rollback`,
                `snapshot_replaces_platform`, `deploy_failed`, `deployed_not_configured`, `configure_failed`,
                or `deployed`.
        """
        checked = cls._plugin_manifest(plugin_name, instance, cwd)
        if isinstance(checked, str):
            return cls._with_status(checked, "invalid_input")
        manifest_file, manifest = checked
        if branch and version:
            return cls._with_status(
                "Error: pass either branch or version, not both; a version is already released.", "invalid_input"
            )

        target: list[str]
        if version:
            target = ["--plugin", f"{manifest['name']}@{version}"]
        else:
            snapshot: bool = await cls._in_larger_repo(manifest_file.parent, cwd)
            snapshot_flag: list[str] = ["--snapshot"] if snapshot else []
            branch_flag: list[str] = ["--branch", branch] if branch else []
            target = [plugin_name, *snapshot_flag, *branch_flag]
        result = await cls._run_canvas_command(
            command=["uv", "run", "canvas", "deploy", *target, "--instance", instance],
            cwd=cwd,
        )
        output = f"Deploy output:\n{result}"
        # configurer sets a released version's variables only when the working-tree manifest is that version.
        configurer_version: str = f" with version {version}" if version else ""
        if cls.CONSENT_PENDING_MARKER in result:
            # --no-push deploys Platform's main; --ref deploys the branch the failed attempt already pushed
            # (canvas_cli/apps/platform/commands.py:995-1002, 1131-1134 at 1.13.0).
            reuse_flags: str = f"--ref {shlex.quote(branch)}" if branch else "--no-push"
            reuse_target: str = (
                f"--plugin {shlex.quote(f'{manifest['name']}@{version}')}"
                if version
                else f"{shlex.quote(plugin_name)} {reuse_flags}"
            )
            consent = (
                f"{output}\n\n{cls.CONSENT_NOTE}\n"
                f"  cd {shlex.quote(cwd)} && uv run canvas deploy {reuse_target} "
                f"--instance {shlex.quote(instance)}\n"
                f"After it succeeds there, call the configurer tool{configurer_version} to set variables."
            )
            return cls._with_status(consent, "consent_pending")
        if cls.STILL_RUNNING_MARKER in result:
            return cls._with_status(
                f"{output}\n\n{cls.STILL_RUNNING_NOTE} Call the configurer tool{configurer_version} once the "
                "deployment succeeds.",
                "still_running",
            )
        if any(marker in result for marker in cls.SNAPSHOT_UNCOMMITTED_MARKERS):
            return cls._with_status(f"{output}\n\n{cls.SNAPSHOT_UNCOMMITTED_NOTE}", "snapshot_uncommitted")
        if cls.SNAPSHOT_UNSUPPORTED_MARKER in result:
            return cls._with_status(f"{output}\n\n{cls.SNAPSHOT_UNSUPPORTED_NOTE}", "snapshot_unsupported")
        if cls.SNAPSHOT_ROLLBACK_MARKER in result:
            return cls._with_status(f"{output}\n\n{cls.SNAPSHOT_ROLLBACK_NOTE}", "snapshot_rollback")
        if cls.SNAPSHOT_REPLACES_MARKER in result:
            branch_hand_off: str = f" --branch {shlex.quote(branch)}" if branch else ""
            replaces = (
                f"{output}\n\n{cls.SNAPSHOT_REPLACES_NOTE}\n"
                f"  cd {shlex.quote(cwd)} && uv run canvas deploy {shlex.quote(plugin_name)} "
                f"--snapshot{branch_hand_off} --instance {shlex.quote(instance)}\n"
                "After it succeeds there, call the configurer tool to set variables."
            )
            return cls._with_status(replaces, "snapshot_replaces_platform")
        if cls.UNCOMMITTED_MARKER in result:
            return cls._with_status(f"{output}\n\n{cls.UNCOMMITTED_NOTE}", "dirty_tree")
        if result.startswith("Command failed"):
            return cls._with_status(output, "deploy_failed")
        not_configured: str | None = cls._version_not_configured(manifest, instance, version)
        if not_configured:
            return cls._with_status(f"{output}\n\n{not_configured}", "deployed_not_configured")
        configured, failed = await cls._configure(instance, cwd, manifest)
        return cls._with_status(f"{output}\n\n{configured}", "configure_failed" if failed else "deployed")

    @classmethod
    async def configure(cls, plugin_name: str, instance: str, cwd: str, version: str = "") -> str:
        """Set a Canvas plugin's manifest variables on a Canvas Platform instance.

        For a released version, variables are set only when the working-tree manifest is that version,
        since they are read from it.

        Args:
            plugin_name: The inner package folder name, which holds CANVAS_MANIFEST.json. Variables are keyed by the manifest name.
            instance: Target Canvas Platform instance slug.
            cwd: Working directory (plugin container directory).
            version: The released version the deploy installed, or empty for a branch or release deploy.

        Returns:
            str: The configure output or an error message, ending with a `Status:` line: `invalid_input`,
                `deployed_not_configured`, `configure_failed`, or `configured`.
        """
        checked = cls._plugin_manifest(plugin_name, instance, cwd)
        if isinstance(checked, str):
            return cls._with_status(checked, "invalid_input")
        _, manifest = checked
        not_configured: str | None = cls._version_not_configured(manifest, instance, version)
        if not_configured:
            return cls._with_status(not_configured, "deployed_not_configured")
        configured, failed = await cls._configure(instance, cwd, manifest)
        return cls._with_status(configured, "configure_failed" if failed else "configured")

    @classmethod
    def create_server(cls) -> FastMCP:
        """Create and configure the FastMCP server with canvas tools."""
        server = FastMCP("canvas_cmd_line")

        @server.tool()
        async def deployer(plugin_name: str, instance: str, cwd: str, branch: str = "", version: str = "") -> str:
            """Deploy a Canvas plugin to a Canvas Platform instance and set its variables.

            Runs canvas deploy, then canvas config set for the variables declared in
            CANVAS_MANIFEST.json, except for a released version the working-tree manifest
            is not, which ends with deployed_not_configured instead. The instance is a Canvas Platform instance slug. Values
            come from ~/.canvas/plugin-secrets/<instance>.json keyed by manifest name and are
            never returned in the output. Consent requests for custom data access are never
            answered here: they are returned for the user to answer in their own terminal.
            A plugin inside a larger repository, such as a monorepo, deploys with --snapshot.
            The output ends with one `Status:` line: invalid_input, consent_pending,
            still_running, dirty_tree, snapshot_uncommitted, snapshot_unsupported,
            snapshot_rollback, snapshot_replaces_platform, deploy_failed,
            deployed_not_configured, configure_failed, or deployed.

            Args:
                plugin_name: The inner package folder name. Variables are keyed by the manifest name.
                instance: Canvas Platform instance slug.
                cwd: Working directory (plugin container directory).
                branch: The confirmed work branch. Pass it for every work-in-progress deploy, which Canvas Platform accepts only on test instances. Leave it empty only for the release step of /cpa:wrap-up, which pushes to main.
                version: Only for deploying an already released version, such as `1.4.0`, to another instance. Never combine it with `branch`.
            """
            return await cls.deploy(plugin_name, instance, cwd, branch, version)

        @server.tool()
        async def configurer(plugin_name: str, instance: str, cwd: str, version: str = "") -> str:
            """Set a deployed Canvas plugin's variables on a Canvas Platform instance.

            Runs canvas config set for the variables declared in CANVAS_MANIFEST.json. The
            instance is a Canvas Platform instance slug. Values come from
            ~/.canvas/plugin-secrets/<instance>.json keyed by manifest name and are never
            returned in the output. Use it after the user approves a pending consent request.
            For a released version the working-tree manifest is not, it sets nothing and ends
            with deployed_not_configured. The output ends with one `Status:` line:
            invalid_input, deployed_not_configured, configure_failed, or configured.

            Args:
                plugin_name: The inner package folder name. Variables are keyed by the manifest name.
                instance: Canvas Platform instance slug.
                cwd: Working directory (plugin container directory).
                version: The released version the deployer call passed, if any. Leave it empty otherwise.
            """
            return await cls.configure(plugin_name, instance, cwd, version)

        return server


if __name__ == "__main__":
    CanvasDeployerMcp.create_server().run()
