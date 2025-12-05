#!/usr/bin/env python3
"""
Export the current Claude Code session's messages to a simplified text file.
Reads ~/.claude/history.jsonl, extracts display text for the current session,
and saves to .claude/artifacts/claude-history-{sessionId}.txt (overwrites if exists).
"""

import json
from pathlib import Path


def main():
    history_file = Path.home() / ".claude" / "history.jsonl"

    if not history_file.exists():
        print(f"History file not found: {history_file}")
        return

    # Read all lines
    lines = history_file.read_text().strip().split("\n")

    if not lines:
        print("History file is empty")
        return

    # Get sessionId from the last line
    last_entry = json.loads(lines[-1])
    session_id = last_entry.get("sessionId")

    if not session_id:
        print("No sessionId found in last history entry")
        return

    # Filter lines for this session and extract display text
    display_texts = []
    for line in lines:
        entry = json.loads(line)
        if entry.get("sessionId") == session_id:
            display = entry.get("display")
            if display:
                display_texts.append(display)

    if not display_texts:
        print(f"No display messages found for session {session_id}")
        return

    # Create output file named by sessionId (overwrites if exists)
    output_dir = Path(".claude/artifacts")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"claude-history-{session_id}.txt"

    # Write display texts
    output_file.write_text("\n".join(display_texts))

    print(f"Exported {len(display_texts)} messages to {output_file}")


if __name__ == "__main__":
    main()
