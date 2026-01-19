from dataclasses import dataclass


@dataclass(frozen=True)
class _Constants:
    CPA_RUNNING: str = "CPA_RUNNING"
    CPA_WORKSPACE_DIR: str = "CPA_WORKSPACE_DIR"
    CPA_PLUGIN_DIR: str = "CPA_PLUGIN_DIR"


Constants = _Constants()
