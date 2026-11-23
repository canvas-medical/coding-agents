#!/usr/bin/env bash
# Remove the commit-less git repository `canvas init` nests in a new plugin container.
#
# Usage: remove_nested_repo.sh <workspace> <plugin_name>
#
# `canvas init` runs `git init` in the new container even inside an existing work tree
# (canvas-plugins canvas_cli/apps/platform/commands.py:1331-1339 at 1.13.0). This deletes that
# `.git` only when it is the root of its own repository and has no commits. Every outcome prints
# one line, and the caller routes on its start:
#   "Removed the nested repository"  removed; continue
#   "No nested repository"           nothing to remove; continue
#   "Nothing removed"                refused; show the line and stop
set -u

workspace="${1:-}"
plugin_name="${2:-}"
dir="$workspace/$plugin_name"

if [ -z "$workspace" ]; then
  echo "Nothing removed: the workspace is empty"
elif [ -z "$plugin_name" ]; then
  echo "Nothing removed: the plugin name is empty"
elif [ ! -d "$dir/.git" ]; then
  echo "No nested repository at $dir; nothing to remove"
elif ! [ "$dir" -ef "$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)" ]; then
  echo "Nothing removed: $dir is not the root of its own repository"
elif [ "$(git -C "$dir" rev-list --all --count)" != "0" ]; then
  echo "Nothing removed: the repository at $dir has commits"
else
  # The checks above prove a commit-less repository rooted at the container. `trash` ships with
  # macOS 15 and later only, so Linux and Studio's image fall back to rm.
  if command -v trash >/dev/null 2>&1; then
    trash "$dir/.git"
  else
    rm -rf "$dir/.git"
  fi
  if [ -e "$dir/.git" ]; then
    echo "Nothing removed: deleting $dir/.git failed"
  else
    echo "Removed the nested repository at $dir/.git"
  fi
fi
