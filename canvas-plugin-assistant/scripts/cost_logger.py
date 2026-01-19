#!/usr/bin/env python3
"""
SessionEnd hook that captures cost data from Claude Code session.
This script runs when a Claude Code session ends and stores cost information
in JSON format in the parent directory with the session hash as filename.
"""

import json
import sys
import subprocess
from os import environ
from pathlib import Path
from datetime import datetime, timezone
from constants import Constants

# Path to pricing data file
PRICING_FILE = Path(__file__).parent.parent / "model_costs.json"

def load_pricing():
    """Load pricing data from JSON file."""
    try:
        with open(PRICING_FILE, 'r') as f:
            data = json.load(f)
            # Convert prices from per-1M to per-token rates
            pricing = {}
            for model, prices in data.get('models', {}).items():
                pricing[model] = {
                    "input": prices["input"] / 1_000_000,
                    "output": prices["output"] / 1_000_000,
                    "cache_write": prices["cache_write"] / 1_000_000,
                    "cache_read": prices["cache_read"] / 1_000_000,
                }
            return pricing
    except FileNotFoundError:
        print(f"Warning: Pricing file not found at {PRICING_FILE}", file=sys.stderr)
        return {}
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Error loading pricing data: {e}", file=sys.stderr)
        return {}

# Load pricing data once at module level
PRICING = load_pricing()

def detect_model_from_transcript(messages):
    """Detect the Claude model used in the session from transcript messages."""
    for msg in messages:
        if isinstance(msg, dict):
            # Check various possible locations for model info
            if "model" in msg:
                return msg["model"]
            if "message" in msg and isinstance(msg["message"], dict):
                if "model" in msg["message"]:
                    return msg["message"]["model"]
            # Check in metadata or other fields
            if "metadata" in msg and isinstance(msg["metadata"], dict):
                if "model" in msg["metadata"]:
                    return msg["metadata"]["model"]
    return None

def calculate_cost(token_counts, model):
    """Calculate cost in USD based on token usage and model."""
    if not model:
        return None

    # Normalize model name by removing date suffixes (e.g., -20250929)
    # This handles versioned model names like claude-sonnet-4-5-20250929
    normalized_model = model
    for base_model in PRICING.keys():
        if model.startswith(base_model):
            normalized_model = base_model
            break

    if normalized_model not in PRICING:
        return None

    pricing = PRICING[normalized_model]
    cost = 0.0

    cost += token_counts.get("input", 0) * pricing["input"]
    cost += token_counts.get("output", 0) * pricing["output"]
    cost += token_counts.get("cache_write", 0) * pricing["cache_write"]
    cost += token_counts.get("cache_read", 0) * pricing["cache_read"]

    return round(cost, 6)  # Round to 6 decimal places

def parse_timestamp(timestamp_str):
    """Parse ISO timestamp string to datetime object."""
    try:
        # Try parsing with various formats
        for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%f%z"]:
            try:
                return datetime.strptime(timestamp_str.replace("+00:00", "Z"), fmt)
            except ValueError:
                continue
        # Fallback: try fromisoformat
        return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except Exception:
        return None

def extract_cost_from_transcript(transcript_path):
    """Extract cost information from the transcript file."""
    cost_data = {}

    try:
        if not Path(transcript_path).exists():
            return cost_data

        with open(transcript_path, 'r') as f:
            messages = []
            for line in f:
                if line.strip():
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            cost_data["message_count"] = len(messages)

            # Detect model used in session
            model = detect_model_from_transcript(messages)
            if model:
                cost_data["model"] = model

            # Calculate session duration from timestamps
            timestamps = []
            for msg in messages:
                if isinstance(msg, dict) and "timestamp" in msg:
                    ts = parse_timestamp(msg["timestamp"])
                    if ts:
                        timestamps.append(ts)

            if len(timestamps) >= 2:
                duration_seconds = (timestamps[-1] - timestamps[0]).total_seconds()
                cost_data["duration_seconds"] = round(duration_seconds, 2)
                # Human-readable duration
                hours, remainder = divmod(int(duration_seconds), 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    cost_data["duration_formatted"] = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    cost_data["duration_formatted"] = f"{minutes}m {seconds}s"
                else:
                    cost_data["duration_formatted"] = f"{seconds}s"

            # Look for cost-related information in messages
            # This would include token usage, API calls, etc.
            token_usage = []
            cache_read_total = 0
            cache_write_total = 0
            total_input = 0
            total_output = 0

            for msg in messages:
                if isinstance(msg, dict):
                    # Check for token usage in various possible locations
                    # Format 1: usage directly in message
                    if "usage" in msg:
                        token_usage.append(msg["usage"])
                    # Format 2: usage nested inside message field
                    elif "message" in msg and isinstance(msg["message"], dict):
                        if "usage" in msg["message"]:
                            usage = msg["message"]["usage"]
                            token_usage.append(usage)
                            # Track cache usage
                            cache_read_total += usage.get("cache_read_input_tokens", 0)
                            cache_write_total += usage.get("cache_creation_input_tokens", 0)
                    # Format 3: token_usage field
                    if "token_usage" in msg:
                        token_usage.append(msg["token_usage"])

            if token_usage:
                cost_data["token_usage_details"] = token_usage

                # Calculate totals
                total_input = sum(u.get("input_tokens", 0) for u in token_usage if isinstance(u, dict))
                total_output = sum(u.get("output_tokens", 0) for u in token_usage if isinstance(u, dict))
                cache_read_total = sum(u.get("cache_read_input_tokens", 0) for u in token_usage if isinstance(u, dict))
                cache_write_total = sum(u.get("cache_creation_input_tokens", 0) for u in token_usage if isinstance(u, dict))

                if total_input or total_output:
                    cost_data["total_tokens"] = {
                        "input": total_input,
                        "output": total_output,
                        "total": total_input + total_output
                    }

                # Add cache usage if available
                if cache_read_total or cache_write_total:
                    cost_data["cache_usage"] = {
                        "cache_read": cache_read_total,
                        "cache_write": cache_write_total
                    }

                # Calculate cost in USD if model is known
                if model:
                    token_counts = {
                        "input": total_input,
                        "output": total_output,
                        "cache_read": cache_read_total,
                        "cache_write": cache_write_total,
                    }
                    cost_usd = calculate_cost(token_counts, model)
                    if cost_usd is not None:
                        cost_data["cost_usd"] = cost_usd
                        cost_data["cost_formatted"] = f"${cost_usd:.4f}"
                    else:
                        cost_data["cost_calculation_note"] = f"Pricing not available for model: {model}"

    except Exception as e:
        cost_data["transcript_parse_error"] = str(e)

    return cost_data

def main():
    try:
        if environ.get(Constants.CPA_RUNNING, "0") != "1":
            sys.exit(0)
        # Read hook input from stdin
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error parsing hook input: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract session information
    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", "")
    reason = hook_input.get("reason", "unknown")

    # Find git repository root to create .cpa-workflow-artifacts at workspace level
    # Use the helper script from the same directory
    script_dir = Path(__file__).parent
    try:
        result = subprocess.run(
            ["python3", str(script_dir / "get_plugin_dir.py")],
            cwd=cwd if cwd else None,
            capture_output=True,
            text=True,
            check=True
        )
        workspace_dir = Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to cwd if helper script not found
        workspace_dir = Path(cwd) if cwd else Path.cwd()

    # Create .cpa-workflow-artifacts/costs/ directory at workspace root
    costs_dir = workspace_dir / ".cpa-workflow-artifacts" / "costs"
    costs_dir.mkdir(parents=True, exist_ok=True)

    # Prepare output data
    session_data = {
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "exit_reason": reason,
        "working_directory": str(cwd),
        "transcript_path": str(transcript_path)
    }

    # Extract cost information from transcript
    if transcript_path:
        cost_info = extract_cost_from_transcript(transcript_path)
        if cost_info:
            session_data["cost_data"] = cost_info

    # Write to JSON file in .cpa-workflow-artifacts/costs/ with session hash as filename
    output_file = costs_dir / f"{session_id}.json"

    try:
        with open(output_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        print(f"Cost data saved to: {output_file}", file=sys.stderr)

        # Aggregate costs by working directory
        aggregate_by_working_directory(costs_dir, workspace_dir)

        sys.exit(0)
    except Exception as e:
        print(f"Error writing cost data: {e}", file=sys.stderr)
        sys.exit(1)

def aggregate_by_working_directory(parent_dir: Path, workspace_dir: Path):
    """
    Aggregate all session costs for the workspace (git repository root).

    Args:
        parent_dir: Directory containing session JSON files (.cpa-workflow-artifacts/costs/)
        workspace_dir: The workspace directory (git root) to aggregate sessions for
    """
    try:
        # Sanitize workspace directory for use as filename
        # Replace slashes and special chars with underscores
        workspace_str = str(workspace_dir)
        safe_dirname = workspace_str.replace('/', '_').replace('\\', '_')
        if safe_dirname.startswith('_'):
            safe_dirname = safe_dirname[1:]  # Remove leading underscore

        aggregated_file = parent_dir / f"{safe_dirname}.json"

        # Check if aggregated file already exists to preserve created_date
        existing_created_date = None
        if aggregated_file.exists():
            try:
                with open(aggregated_file, 'r') as f:
                    existing_data = json.load(f)
                    existing_created_date = existing_data.get('created_date')
            except (json.JSONDecodeError, IOError):
                # If we can't read the existing file, we'll create a new one
                pass

        # Find all session files for this working directory
        sessions = []
        total_tokens_sum = {"input": 0, "output": 0, "total": 0}
        cache_usage_sum = {"cache_write": 0, "cache_read": 0}
        cost_usd_sum = 0.0

        # Loop through all .json files in parent directory
        for json_file in parent_dir.glob("*.json"):
            # Skip aggregated files (they contain working directory name)
            if json_file.name != f"{safe_dirname}.json" and not json_file.stem.startswith('_'):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)

                    # Only include sessions from the same workspace
                    working_dir = data.get('working_directory')
                    if working_dir and working_dir.startswith(workspace_str):
                        session_id = data.get('session_id')
                        session_date = data.get('timestamp')

                        # Track sessions
                        sessions.append({
                            "session_id": session_id,
                            "date": session_date,
                            "duration": data.get('cost_data', {}).get('duration_formatted'),
                            "cost_usd": data.get('cost_data', {}).get('cost_usd', 0)
                        })

                        # Aggregate metrics
                        cost_data = data.get('cost_data', {})
                        total_tokens = cost_data.get('total_tokens', {})
                        # total_tokens is a dict with {input, output, total}
                        if isinstance(total_tokens, dict):
                            total_tokens_sum['input'] += total_tokens.get('input', 0)
                            total_tokens_sum['output'] += total_tokens.get('output', 0)
                            total_tokens_sum['total'] += total_tokens.get('total', 0)

                        cache = cost_data.get('cache_usage', {})
                        cache_usage_sum['cache_write'] += cache.get('cache_write', 0)
                        cache_usage_sum['cache_read'] += cache.get('cache_read', 0)

                        cost_usd_sum += cost_data.get('cost_usd', 0)

                except (json.JSONDecodeError, KeyError, IOError):
                    # Skip invalid or unreadable files
                    continue

        if not sessions:
            # No sessions found for this working directory
            return

        # Sort sessions by date
        sessions.sort(key=lambda x: x['date'] if x['date'] else '')

        # Determine created_date and last_update
        now = datetime.now(timezone.utc).isoformat()
        created_date = existing_created_date if existing_created_date else now
        last_update = now

        # Create aggregated data
        aggregated_data = {
            "workspace_directory": workspace_str,
            "created_date": created_date,
            "last_update": last_update,
            "session_count": len(sessions),
            "total_tokens": total_tokens_sum,
            "cache_usage": cache_usage_sum,
            "cost_usd": round(cost_usd_sum, 4),
            "cost_formatted": f"${cost_usd_sum:.4f}",
            "sessions": sessions
        }

        # Save aggregated data
        with open(aggregated_file, 'w') as f:
            json.dump(aggregated_data, f, indent=2)

        print(f"Aggregated data saved to: {aggregated_file}", file=sys.stderr)
        print(f"  Sessions: {len(sessions)}, Total cost: ${cost_usd_sum:.4f}", file=sys.stderr)

    except Exception as e:
        print(f"Warning: Failed to aggregate data: {e}", file=sys.stderr)
        # Don't fail the main task if aggregation fails

if __name__ == "__main__":
    main()
