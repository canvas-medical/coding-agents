#!/usr/bin/env python3
"""
SessionEnd hook that extracts and logs user inputs from Claude Code sessions.

This script parses session transcripts to identify different types of user inputs:
- Free text messages
- Slash commands
- Question/answer pairs from AskUserQuestion interactions

The extracted inputs are saved per session and aggregated across all sessions
in the workspace.
"""

import json
import re
from pathlib import Path

from base_logger import BaseLogger
from hook_information import HookInformation


class UserInputsLogger(BaseLogger):
    """
    Logger that extracts user inputs from Claude Code session transcripts.

    This logger identifies and categorizes three types of user interactions:
    1. free_text: Natural language messages from the user
    2. slash_command: Commands invoked with /command-name syntax
    3. question_answer: Responses to AskUserQuestion prompts
    """
    @classmethod
    def session_directory(cls, hook_info: HookInformation) -> Path:
        """
        Return the directory for storing user input session files.

        Args:
            hook_info: Context information about the session

        Returns:
            Path to .cpa-workflow-artifacts/user_inputs/ in the workspace root
        """
        return hook_info.workspace_dir / ".cpa-workflow-artifacts" / "user_inputs"

    @classmethod
    def extraction(cls, hook_info: HookInformation) -> dict:
        """
        Extract user inputs from the session transcript.

        Parses the transcript JSONL file to identify:
        - Free text user messages (not commands or XML)
        - Slash commands (extracted from <command-name> tags)
        - Question/answer pairs (from AskUserQuestion tool results)

        Args:
            hook_info: Context information including the transcript path

        Returns:
            Dictionary with 'user_inputs' key containing the list of input objects.
            Each input object has 'input', 'type', and optionally 'question' fields.
        """
        result = []
        with hook_info.transcript_path.open('r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Only process user messages that aren't meta (skill expansions)
                if entry.get("type") != "user" or entry.get("isMeta"):
                    continue

                content = entry.get("message", {}).get("content")
                if not content:
                    continue

                # Case 1: String content (could be command or free text)
                if isinstance(content, str):
                    # Check for slash commands
                    command_match = re.search(r"<command-name>([^<]+)</command-name>", content)
                    if command_match:
                        result.append({
                            "input": command_match.group(1).strip(),
                            "type": "slash_command"
                        })
                    # Free text (not a command, not starting with XML-like tags)
                    elif not content.startswith("<"):
                        result.append({
                            "input": content,
                            "type": "free_text"
                        })

                # Case 2: Array content (tool results, including AskUserQuestion answers)
                elif isinstance(content, list):
                    for item in content:
                        if item.get("type") != "tool_result":
                            continue

                        result_content = item.get("content", "")
                        if not isinstance(result_content, str):
                            continue

                        # Check for AskUserQuestion responses
                        if result_content.startswith("User has answered your questions:"):
                            # Extract question-answer pairs
                            # Format: "question"="answer", "question2"="answer2"
                            answers_part = result_content.replace(
                                "User has answered your questions: ", ""
                            ).replace(
                                ". You can now continue with the user's answers in mind.", ""
                            )
                            # Parse "question"="answer" patterns
                            pattern = r'"([^"]+)"="([^"]+)"'
                            matches = re.findall(pattern, answers_part)

                            for question, answer in matches:
                                result.append({
                                    "input": answer,
                                    "type": "question_answer",
                                    "question": question
                                })
        return {"user_inputs": result}

    @classmethod
    def aggregation(cls, session_directory: Path) -> None:
        """
        Aggregate user inputs from all session files into a single summary.

        Reads all session JSON files in the directory and combines their
        user_inputs into a single aggregation file.

        Args:
            session_directory: Directory containing individual session JSON files

        Creates:
            user_inputs_aggregation.json in the parent directory with all inputs
        """
        aggregated_file = session_directory.parent / "user_inputs_aggregation.json"

        inputs = []
        for json_file in session_directory.glob("*.json"):
            with open(json_file, 'r') as file_f:
                data = json.load(file_f)
                inputs.append(data.get('user_inputs', []))

        with aggregated_file.open('w') as aggregated_f:
            json.dump({'inputs': inputs}, aggregated_f, indent=2)


if __name__ == "__main__":
    UserInputsLogger.run(UserInputsLogger.hook_information())
