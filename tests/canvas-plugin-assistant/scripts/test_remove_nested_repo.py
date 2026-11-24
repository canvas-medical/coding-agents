"""Tests for remove_nested_repo.sh, which commands/new-plugin.md and agents/plugin-brainstorm.md both run."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT: Path = Path(__file__).resolve().parents[3] / "canvas-plugin-assistant" / "scripts" / "remove_nested_repo.sh"
PLUGIN_NAME: str = "vitals-alert"
GIT_ENV: dict[str, str] = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def make_bin(tmp_path: Path, with_trash: bool) -> Path:
    """Build a PATH directory holding `git` and, optionally, a stand-in `trash`.

    The stand-in moves its argument into `tmp_path/Trash`, so a test never touches the user's Trash.

    Args:
        tmp_path (Path): pytest's per-test directory.
        with_trash (bool): Whether `trash` is on the PATH.

    Returns:
        Path: The directory to put first on PATH.
    """
    bin_dir: Path = tmp_path / "bin"
    bin_dir.mkdir()
    git_path: str | None = shutil.which("git")
    assert git_path is not None
    (bin_dir / "git").symlink_to(git_path)
    if with_trash:
        trash_dir: Path = tmp_path / "Trash"
        trash_dir.mkdir()
        trash: Path = bin_dir / "trash"
        trash.write_text(f'#!/bin/sh\nmv "$1" "{trash_dir}/"\n')
        trash.chmod(0o755)
    return bin_dir


def run_script(tmp_path: Path, arguments: list[str], with_trash: bool = False) -> str:
    """Run the script with a PATH holding only `git`, `/bin`, and optionally `trash`.

    Args:
        tmp_path (Path): pytest's per-test directory.
        arguments (list[str]): The workspace and plugin name arguments.
        with_trash (bool): Whether `trash` is on the PATH.

    Returns:
        str: The script's stdout, stripped.
    """
    bin_dir: Path = make_bin(tmp_path, with_trash)
    bash: str | None = shutil.which("bash")
    assert bash is not None
    env: dict[str, str] = {"PATH": f"{bin_dir}:/bin", "HOME": str(tmp_path)}
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [bash, str(SCRIPT), *arguments],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def git(*args: str) -> None:
    """Run git with a fixed identity.

    Args:
        *args (str): The git arguments.
    """
    subprocess.run(["git", *args], check=True, capture_output=True, env={**os.environ, **GIT_ENV})


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A larger repository with one commit, the workspace `canvas init` runs in.

    Args:
        tmp_path (Path): pytest's per-test directory.

    Returns:
        Path: The workspace root.
    """
    root: Path = tmp_path / "monorepo"
    root.mkdir()
    git("init", "-q", str(root))
    (root / "README.md").write_text("monorepo\n")
    git("-C", str(root), "add", "README.md")
    git("-C", str(root), "commit", "-q", "-m", "init")
    return root


@pytest.mark.parametrize("with_trash", [True, False], ids=["trash", "no_trash"])
def test_removes_a_commit_less_nested_repository(tmp_path: Path, workspace: Path, with_trash: bool) -> None:
    """The fresh repository `canvas init` nests is removed, with or without `trash`, and the workspace's stays."""
    container: Path = workspace / PLUGIN_NAME
    container.mkdir()
    git("init", "-q", str(container))

    output: str = run_script(tmp_path, [str(workspace), PLUGIN_NAME], with_trash)

    assert output == f"Removed the nested repository at {container}/.git"
    assert not (container / ".git").exists()
    assert (workspace / ".git").is_dir()
    assert (tmp_path / "Trash" / ".git").is_dir() is with_trash


def test_empty_plugin_name_never_touches_the_workspace_repository(tmp_path: Path, workspace: Path) -> None:
    """An empty name would point at the workspace's own `.git`, so nothing is removed."""
    output: str = run_script(tmp_path, [str(workspace), ""])

    assert output == "Nothing removed: the plugin name is empty"
    assert (workspace / ".git").is_dir()


def test_plugin_name_reaching_outside_the_workspace_is_refused(tmp_path: Path) -> None:
    """A name like `../sibling` would reach a commit-less repository beside the workspace, so nothing is removed."""
    workspace: Path = tmp_path / "workspace"
    workspace.mkdir()
    sibling: Path = tmp_path / "sibling"
    sibling.mkdir()
    git("init", "-q", str(sibling))

    output: str = run_script(tmp_path, [str(workspace), "../sibling"])

    assert output == "Nothing removed: the plugin name must be a single folder name"
    assert (sibling / ".git").is_dir()


@pytest.mark.parametrize("plugin_name", [".", "..", "nested/vitals-alert"])
def test_plugin_name_that_is_not_one_folder_is_refused(tmp_path: Path, plugin_name: str) -> None:
    """`.` would point at a commit-less workspace's own `.git`, so a name must be exactly one folder."""
    workspace: Path = tmp_path / "workspace"
    (workspace / "nested" / "vitals-alert").mkdir(parents=True)
    git("init", "-q", str(workspace))
    git("init", "-q", str(workspace / "nested" / "vitals-alert"))

    output: str = run_script(tmp_path, [str(workspace), plugin_name])

    assert output == "Nothing removed: the plugin name must be a single folder name"
    assert (workspace / ".git").is_dir()
    assert (workspace / "nested" / "vitals-alert" / ".git").is_dir()


def test_empty_workspace_is_refused(tmp_path: Path) -> None:
    """An unset workspace would resolve the container from the filesystem root, so nothing is removed."""
    output: str = run_script(tmp_path, ["", PLUGIN_NAME])

    assert output == "Nothing removed: the workspace is empty"


def test_no_nested_repository_continues(tmp_path: Path, workspace: Path) -> None:
    """A container with no `.git` of its own reports that there is nothing to remove."""
    container: Path = workspace / PLUGIN_NAME
    container.mkdir()

    output: str = run_script(tmp_path, [str(workspace), PLUGIN_NAME])

    assert output == f"No nested repository at {container}; nothing to remove"


def test_nested_repository_with_a_commit_is_kept(tmp_path: Path, workspace: Path) -> None:
    """A nested repository holding history is someone's work, so it stays."""
    container: Path = workspace / PLUGIN_NAME
    container.mkdir()
    git("init", "-q", str(container))
    (container / "handler.py").write_text("x = 1\n")
    git("-C", str(container), "add", "handler.py")
    git("-C", str(container), "commit", "-q", "-m", "work")

    output: str = run_script(tmp_path, [str(workspace), PLUGIN_NAME])

    assert output == f"Nothing removed: the repository at {container} has commits"
    assert (container / ".git").is_dir()


def test_git_folder_not_rooted_at_the_container_is_kept(tmp_path: Path, workspace: Path) -> None:
    """A `.git` folder that is not a repository rooted at the container is left alone."""
    container: Path = workspace / PLUGIN_NAME
    (container / ".git").mkdir(parents=True)

    output: str = run_script(tmp_path, [str(workspace), PLUGIN_NAME])

    assert output == f"Nothing removed: {container} is not the root of its own repository"
    assert (container / ".git").is_dir()
