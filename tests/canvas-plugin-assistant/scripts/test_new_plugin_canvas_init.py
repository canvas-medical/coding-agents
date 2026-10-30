"""Tripwire for the nested-repository removal in commands/new-plugin.md."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from canvas_cli.apps.platform import commands

PLUGIN: str = "acme__vitals_alert"


def test_canvas_init_still_nests_a_repository_inside_a_work_tree(tmp_path: Path) -> None:
    """`canvas init` inside a work tree still runs `git init` in the new container.

    commands/new-plugin.md Step 3 removes that nested `.git` with a guarded block. This runs the installed
    CLI's real `init` with only Canvas Platform stubbed, so it fails as soon as a canvas-plugins release
    skips `git init` inside a work tree, whatever form that fix takes.

    Args:
        tmp_path (Path): pytest's per-test directory, holding the larger repository.
    """
    workspace: Path = tmp_path / "monorepo"
    workspace.mkdir()
    subprocess.run(["git", "init", "-q", str(workspace)], check=True)
    project_dir: Path = workspace / "vitals-alert"

    def scaffold(plugin_type: str, prefix: str) -> Path:
        """Stand in for `canvas init`'s template step, creating the container and its manifest.

        Args:
            plugin_type (str): The template type `init` asked for.
            prefix (str): The organization prefix `init` chose.

        Returns:
            Path: The container directory.
        """
        package_dir: Path = project_dir / PLUGIN
        package_dir.mkdir(parents=True)
        (package_dir / "CANVAS_MANIFEST.json").write_text(json.dumps({"name": f"{prefix}__vitals_alert"}))
        return project_dir

    client: MagicMock = MagicMock()
    client.me.return_value = {
        "organizations": [{"slug": "acme", "plugin_prefix": "acme", "capabilities": ["push_plugin_code"]}],
    }
    client.register_plugin.return_value = {"git_url": "https://platform.example/git/acme/acme__vitals_alert.git"}

    with (
        patch.object(commands.auth, "resolve_platform_url", return_value="https://platform.example"),
        patch.object(commands.auth, "stored_tokens", return_value={"access_token": "token"}),
        patch.object(commands, "PlatformClient", return_value=client),
        patch.object(commands.instance_plugin, "scaffold", side_effect=scaffold),
        patch.object(commands.git, "connect_remote"),
    ):
        commands.init(plugin_type="handler", organization=None)

    assert (project_dir / ".git").exists(), (
        "canvas init no longer runs git init inside an existing work tree. Raise CPA's canvas floor "
        "(every `canvas>=` pin) to the release that carries that fix, then delete the guarded nested "
        "`.git` removal block in canvas-plugin-assistant/commands/new-plugin.md Step 3, the Step 4 "
        "instruction to remove it, and this test file"
    )
