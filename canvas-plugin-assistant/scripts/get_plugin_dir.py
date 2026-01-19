#!/usr/bin/env python3
"""
Usage:
    workspace_dir = $(python3 scripts/get-plugin-dir.py)
"""
from os import environ
from pathlib import Path

from constants import Constants


class PluginDir:

    @classmethod
    def run(cls) -> Path:
        result = environ.get(Constants.CPA_PLUGIN_DIR, "")
        if not result:
            return Path.cwd()
        return Path(result)


if __name__ == "__main__":
    print(PluginDir.run())
