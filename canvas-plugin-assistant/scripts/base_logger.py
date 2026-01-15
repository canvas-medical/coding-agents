import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from get_workspace_dir import get_workspace_dir
from hook_information import HookInformation


class BaseLogger:
    @classmethod
    def hook_information(cls) -> HookInformation:
        try:
            hook_input = json.load(sys.stdin)
            return HookInformation(
                session_id=hook_input["session_id"],
                exit_reason=hook_input["reason"],
                transcript_path=Path(hook_input["transcript_path"]),
                working_directory=Path(hook_input["cwd"]),
                workspace_dir=get_workspace_dir(),
            )
        except json.JSONDecodeError as e:
            print(f"Error parsing hook input: {e}", file=sys.stderr)
            sys.exit(1)

    @classmethod
    def run(cls, hook_info: HookInformation) -> None:
        # Create .cpa-workflow-artifacts/costs/ directory at workspace root
        session_directory = cls.session_directory(hook_info)
        session_directory.mkdir(parents=True, exist_ok=True)

        # Write to JSON file in .cpa-workflow-artifacts/costs/ with session hash as filename
        output_file = session_directory / f"{hook_info.session_id}.json"
        try:
            with open(output_file, 'w') as f:
                json.dump({
                              "session_id": hook_info.session_id,
                              "timestamp": datetime.now(timezone.utc).isoformat(),
                              "exit_reason": hook_info.exit_reason,
                              "working_directory": hook_info.working_directory.as_posix(),
                              "transcript_path": hook_info.transcript_path.as_posix(),
                          } | cls.extraction(hook_info), f, indent=2)
            print(f"Cost data saved to: {output_file}", file=sys.stderr)

            # Aggregate costs by working directory
            cls.aggregation(session_directory)

            sys.exit(0)
        except Exception as e:
            print(f"Error writing cost data: {e}", file=sys.stderr)
            sys.exit(1)

    @classmethod
    def session_directory(cls, hook_info: HookInformation) -> Path:
        raise NotImplementedError

    @classmethod
    def extraction(cls, hook_info: HookInformation) -> dict:
        raise NotImplementedError

    @classmethod
    def aggregation(cls, session_directory: Path) -> None:
        raise NotImplementedError
