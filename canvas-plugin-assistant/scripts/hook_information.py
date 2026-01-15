from pathlib import Path
from typing import NamedTuple


class HookInformation(NamedTuple):
    session_id: str
    exit_reason: str
    transcript_path: Path
    workspace_dir: Path
    working_directory: Path