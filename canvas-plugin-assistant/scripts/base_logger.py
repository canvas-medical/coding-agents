"""
Abstract base class for Claude Code session hook loggers.

This module provides a template method pattern for creating hooks that log
session information. Subclasses implement specific extraction and aggregation
logic while the base class handles the common workflow.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from get_workspace_dir import get_workspace_dir
from hook_information import HookInformation


class BaseLogger:
    """
    Abstract base class for session hook loggers.

    This class provides a template for hooks that extract information from
    Claude Code session transcripts and aggregate data across multiple sessions.

    Subclasses must implement:
        - session_directory(): Define where to store session data
        - extraction(): Extract relevant data from the transcript
        - aggregation(): Aggregate data across multiple sessions
    """
    @classmethod
    def hook_information(cls) -> HookInformation:
        """
        Parse hook input from stdin and return HookInformation.

        Reads JSON input from stdin containing session context and converts
        it into a HookInformation object with workspace directory resolution.

        Returns:
            HookInformation containing session context and paths

        Raises:
            SystemExit: If JSON parsing fails
        """
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
        """
        Execute the logging workflow: extract, save, and aggregate session data.

        This is the main entry point that orchestrates the logging process:
        1. Creates the session directory if it doesn't exist
        2. Extracts relevant data from the session transcript
        3. Saves session data to a JSON file named after the session ID
        4. Triggers aggregation across all session files

        Args:
            hook_info: Context information about the session

        Raises:
            SystemExit: With code 0 on success, 1 on failure
        """
        # Create session directory at workspace root
        session_directory = cls.session_directory(hook_info)
        session_directory.mkdir(parents=True, exist_ok=True)

        # Write to JSON file with session hash as filename
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
            print(f"Session data saved to: {output_file}", file=sys.stderr)

            # Aggregate data across all sessions
            cls.aggregation(session_directory)

            sys.exit(0)
        except Exception as e:
            print(f"Error writing session data: {e}", file=sys.stderr)
            sys.exit(1)

    @classmethod
    def session_directory(cls, hook_info: HookInformation) -> Path:
        """
        Return the directory path where session files should be stored.

        Subclasses must implement this to define their storage location,
        typically under .cpa-workflow-artifacts/<category>/.

        Args:
            hook_info: Context information about the session

        Returns:
            Path to the directory for storing session files

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError

    @classmethod
    def extraction(cls, hook_info: HookInformation) -> dict:
        """
        Extract relevant data from the session transcript.

        Subclasses must implement this to parse the transcript and extract
        the data they're interested in (e.g., costs, user inputs).

        Args:
            hook_info: Context information including the transcript path

        Returns:
            Dictionary of extracted data to be merged into the session file

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError

    @classmethod
    def aggregation(cls, session_directory: Path) -> None:
        """
        Aggregate data across all session files in the directory.

        Subclasses must implement this to create summary files that combine
        data from multiple sessions (e.g., total costs, all user inputs).

        Args:
            session_directory: Directory containing individual session JSON files

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError
