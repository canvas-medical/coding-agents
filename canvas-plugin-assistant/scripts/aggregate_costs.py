#!/usr/bin/env python3
"""
Aggregate and analyze session cost data across multiple session files.
This script reads all session JSON files and generates summary reports.
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Aggregate Claude Code session cost data"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing session JSON files (default: current directory)"
    )
    parser.add_argument(
        "--format",
        choices=["summary", "detailed", "csv", "json"],
        default="summary",
        help="Output format (default: summary)"
    )
    parser.add_argument(
        "--since",
        help="Only include sessions since this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--model",
        help="Filter by model name (e.g., claude-sonnet-4-5)"
    )
    parser.add_argument(
        "--sort-by",
        choices=["date", "cost", "duration", "tokens"],
        default="date",
        help="Sort sessions by field (default: date)"
    )
    return parser.parse_args()

def parse_timestamp(ts_str):
    """Parse timestamp string to datetime object."""
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        return None

def load_session_files(directory, since_date=None, model_filter=None):
    """Load all session JSON files from directory."""
    sessions = []
    directory = Path(directory)

    # Look for JSON files that match session ID pattern (UUID format)
    for json_file in directory.glob("*.json"):
        # Skip special files
        if json_file.name in ["plugin.json", "hooks.json", "settings.local.json"]:
            continue

        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

                # Filter by date if specified
                if since_date:
                    ts = parse_timestamp(data.get("timestamp", ""))
                    if not ts or ts.date() < since_date:
                        continue

                # Filter by model if specified
                if model_filter:
                    model = data.get("cost_data", {}).get("model", "")
                    if model_filter.lower() not in model.lower():
                        continue

                sessions.append(data)
        except Exception as e:
            print(f"Warning: Could not load {json_file}: {e}", file=sys.stderr)

    return sessions

def sort_sessions(sessions, sort_by):
    """Sort sessions by specified field."""
    if sort_by == "date":
        return sorted(sessions, key=lambda s: s.get("timestamp", ""))
    elif sort_by == "cost":
        return sorted(
            sessions,
            key=lambda s: s.get("cost_data", {}).get("cost_usd", 0),
            reverse=True
        )
    elif sort_by == "duration":
        return sorted(
            sessions,
            key=lambda s: s.get("cost_data", {}).get("duration_seconds", 0),
            reverse=True
        )
    elif sort_by == "tokens":
        return sorted(
            sessions,
            key=lambda s: s.get("cost_data", {}).get("total_tokens", {}).get("total", 0),
            reverse=True
        )
    return sessions

def print_summary(sessions):
    """Print summary statistics."""
    if not sessions:
        print("No session data found.")
        return

    total_cost = sum(s.get("cost_data", {}).get("cost_usd", 0) for s in sessions)
    total_tokens_input = sum(s.get("cost_data", {}).get("total_tokens", {}).get("input", 0) for s in sessions)
    total_tokens_output = sum(s.get("cost_data", {}).get("total_tokens", {}).get("output", 0) for s in sessions)
    total_cache_read = sum(s.get("cost_data", {}).get("cache_usage", {}).get("cache_read", 0) for s in sessions)
    total_cache_write = sum(s.get("cost_data", {}).get("cache_usage", {}).get("cache_write", 0) for s in sessions)
    total_duration = sum(s.get("cost_data", {}).get("duration_seconds", 0) for s in sessions)

    # Group by model
    by_model = defaultdict(lambda: {"count": 0, "cost": 0.0, "tokens": 0})
    for s in sessions:
        model = s.get("cost_data", {}).get("model", "unknown")
        cost = s.get("cost_data", {}).get("cost_usd", 0)
        tokens = s.get("cost_data", {}).get("total_tokens", {}).get("total", 0)
        by_model[model]["count"] += 1
        by_model[model]["cost"] += cost
        by_model[model]["tokens"] += tokens

    print("=" * 70)
    print("SESSION COST SUMMARY")
    print("=" * 70)
    print(f"Total Sessions:        {len(sessions)}")
    print(f"Total Cost:            ${total_cost:.4f}")
    print(f"Total Input Tokens:    {total_tokens_input:,}")
    print(f"Total Output Tokens:   {total_tokens_output:,}")
    print(f"Total Tokens:          {total_tokens_input + total_tokens_output:,}")
    print(f"Cache Read Tokens:     {total_cache_read:,}")
    print(f"Cache Write Tokens:    {total_cache_write:,}")

    if total_duration > 0:
        hours = int(total_duration // 3600)
        minutes = int((total_duration % 3600) // 60)
        print(f"Total Duration:        {hours}h {minutes}m")

    print("\nBY MODEL:")
    print("-" * 70)
    for model, stats in sorted(by_model.items(), key=lambda x: x[1]["cost"], reverse=True):
        print(f"  {model}:")
        print(f"    Sessions: {stats['count']}")
        print(f"    Cost:     ${stats['cost']:.4f}")
        print(f"    Tokens:   {stats['tokens']:,}")

    print("\nTOP 10 MOST EXPENSIVE SESSIONS:")
    print("-" * 70)
    expensive = sorted(
        sessions,
        key=lambda s: s.get("cost_data", {}).get("cost_usd", 0),
        reverse=True
    )[:10]

    for i, s in enumerate(expensive, 1):
        cost = s.get("cost_data", {}).get("cost_usd", 0)
        tokens = s.get("cost_data", {}).get("total_tokens", {}).get("total", 0)
        model = s.get("cost_data", {}).get("model", "unknown")
        duration = s.get("cost_data", {}).get("duration_formatted", "N/A")
        timestamp = s.get("timestamp", "")[:10]  # Just the date

        print(f"  {i}. ${cost:.4f} - {tokens:,} tokens - {model} - {duration} - {timestamp}")

    print("=" * 70)

def print_detailed(sessions):
    """Print detailed information for each session."""
    print("=" * 70)
    print("DETAILED SESSION REPORT")
    print("=" * 70)

    for i, s in enumerate(sessions, 1):
        print(f"\nSession {i}/{len(sessions)}")
        print("-" * 70)
        print(f"Session ID:     {s.get('session_id', 'N/A')}")
        print(f"Timestamp:      {s.get('timestamp', 'N/A')}")
        print(f"Exit Reason:    {s.get('exit_reason', 'N/A')}")
        print(f"Working Dir:    {s.get('working_directory', 'N/A')}")

        cost_data = s.get("cost_data", {})
        if cost_data:
            print(f"Model:          {cost_data.get('model', 'N/A')}")
            print(f"Cost:           ${cost_data.get('cost_usd', 0):.4f}")
            print(f"Duration:       {cost_data.get('duration_formatted', 'N/A')}")

            total_tokens = cost_data.get("total_tokens", {})
            if total_tokens:
                print(f"Input Tokens:   {total_tokens.get('input', 0):,}")
                print(f"Output Tokens:  {total_tokens.get('output', 0):,}")
                print(f"Total Tokens:   {total_tokens.get('total', 0):,}")

            cache_usage = cost_data.get("cache_usage", {})
            if cache_usage:
                print(f"Cache Read:     {cache_usage.get('cache_read', 0):,}")
                print(f"Cache Write:    {cache_usage.get('cache_write', 0):,}")

def print_csv(sessions):
    """Print data in CSV format."""
    print("session_id,timestamp,model,cost_usd,input_tokens,output_tokens,total_tokens,cache_read,cache_write,duration_seconds,exit_reason")

    for s in sessions:
        session_id = s.get("session_id", "")
        timestamp = s.get("timestamp", "")
        exit_reason = s.get("exit_reason", "")

        cost_data = s.get("cost_data", {})
        model = cost_data.get("model", "")
        cost = cost_data.get("cost_usd", 0)
        duration = cost_data.get("duration_seconds", 0)

        total_tokens = cost_data.get("total_tokens", {})
        input_tokens = total_tokens.get("input", 0)
        output_tokens = total_tokens.get("output", 0)
        total = total_tokens.get("total", 0)

        cache_usage = cost_data.get("cache_usage", {})
        cache_read = cache_usage.get("cache_read", 0)
        cache_write = cache_usage.get("cache_write", 0)

        print(f"{session_id},{timestamp},{model},{cost},{input_tokens},{output_tokens},{total},{cache_read},{cache_write},{duration},{exit_reason}")

def print_json(sessions):
    """Print data in JSON format."""
    print(json.dumps(sessions, indent=2))

def main():
    args = parse_args()

    # Parse since date if provided
    since_date = None
    if args.since:
        try:
            since_date = datetime.strptime(args.since, "%Y-%m-%d").date()
        except ValueError:
            print(f"Error: Invalid date format '{args.since}'. Use YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    # Load session files
    sessions = load_session_files(args.directory, since_date, args.model)

    if not sessions:
        print("No session files found matching criteria.", file=sys.stderr)
        sys.exit(0)

    # Sort sessions
    sessions = sort_sessions(sessions, args.sort_by)

    # Output in requested format
    if args.format == "summary":
        print_summary(sessions)
    elif args.format == "detailed":
        print_detailed(sessions)
    elif args.format == "csv":
        print_csv(sessions)
    elif args.format == "json":
        print_json(sessions)

if __name__ == "__main__":
    main()
