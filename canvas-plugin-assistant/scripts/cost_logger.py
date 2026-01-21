"""
SessionEnd hook that captures cost data from Claude Code session.
This script runs when a Claude Code session ends and stores cost information
in JSON format in the parent directory with the session hash as filename.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from base_logger import BaseLogger
from hook_information import HookInformation


class CostsLogger(BaseLogger):
    """
    Logger that extracts token usage and cost data from Claude Code sessions.

    This logger parses session transcripts to calculate:
    - Token usage (input, output, cache read/write)
    - Session duration
    - Total cost in USD based on model pricing
    - Per-session and aggregated cost summaries
    """

    @classmethod
    def load_pricing(cls) -> dict[str, dict[str, float]]:
        """
        Load pricing data from the model_costs.json file.

        Reads the pricing JSON file and converts per-1M token rates
        to per-token rates for easier calculation.

        Returns:
            Dictionary mapping model names to pricing dictionaries with
            'input', 'output', 'cache_write', and 'cache_read' keys.
            Returns empty dict if the file is not found or invalid.
        """
        pricing_file = Path(__file__).parent.parent / "model_costs.json"
        try:
            with pricing_file.open('r') as f:
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
            print(f"Warning: Pricing file not found at {pricing_file}", file=sys.stderr)
            return {}
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Error loading pricing data: {e}", file=sys.stderr)
            return {}

    @classmethod
    def detect_model_from_transcript(cls, messages: list[dict]) -> str | None:
        """
        Detect the Claude model used in the session from transcript messages.

        Searches through transcript messages for model information in various
        possible locations (direct model field, nested in the message, metadata fields).

        Args:
            messages: List of transcript message dictionaries

        Returns:
            Model identifier string (e.g., 'claude-sonnet-4-5-20250929'),
            or None if not found
        """
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

    @classmethod
    def calculate_cost(cls, token_counts: dict, model: str) -> float | None:
        """
        Calculate cost in USD based on token usage and model pricing.

        Normalizes versioned model names to base models (e.g., removes date suffixes)
        and applies per-token pricing rates.

        Args:
            token_counts: Dictionary with 'input', 'output', 'cache_write',
                         and 'cache_read' token counts
            model: Model identifier string (may include version suffix)

        Returns:
            Cost in USD rounded to 6 decimal places, or None if the model
            is not found in pricing data
        """
        pricing_list = cls.load_pricing()
        # Normalize the model name by removing date suffixes (e.g., -20250929)
        # This handles versioned model names like claude-sonnet-4-5-20250929
        normalized_model = model
        for base_model in pricing_list.keys():
            if model.startswith(base_model):
                normalized_model = base_model
                break

        if normalized_model not in pricing_list:
            return None

        pricing = pricing_list[normalized_model]
        cost = 0.0

        cost += token_counts.get("input", 0) * pricing["input"]
        cost += token_counts.get("output", 0) * pricing["output"]
        cost += token_counts.get("cache_write", 0) * pricing["cache_write"]
        cost += token_counts.get("cache_read", 0) * pricing["cache_read"]

        return round(cost, 6)  # Round to 6 decimal places

    @classmethod
    def parse_timestamp(cls, timestamp_str: str) -> datetime | None:
        """
        Parse ISO timestamp string to a datetime object.

        Tries multiple timestamp formats commonly found in transcripts.

        Args:
            timestamp_str: ISO format timestamp string

        Returns:
            Parsed datetime object, or None if parsing fails
        """
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

    @classmethod
    def session_directory(cls, hook_info: HookInformation) -> Path:
        """
        Return the directory for storing cost session files.

        Args:
            hook_info: Context information about the session

        Returns:
            Path to .cpa-workflow-artifacts/costs/ in the workspace root
        """
        return hook_info.workspace_dir / ".cpa-workflow-artifacts" / "costs"

    @classmethod
    def extraction(cls, hook_info: HookInformation) -> dict:
        """
        Extract cost and token usage information from the session transcript.

        Parses the transcript JSONL file to extract:
        - Token usage statistics (input, output, cache)
        - Session duration and timing
        - Model information
        - Calculated cost in USD

        Args:
            hook_info: Context information including the transcript path

        Returns:
            Dictionary with 'cost_data' key containing all extracted metrics
        """
        cost_data = {}

        try:
            with hook_info.transcript_path.open('r') as f:
                messages = []
                for line in f:
                    if line.strip():
                        try:
                            messages.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

                cost_data["message_count"] = len(messages)

                # Detect model used in session
                model = cls.detect_model_from_transcript(messages)
                if model:
                    cost_data["model"] = model

                # Calculate session duration from timestamps
                timestamps = []
                for msg in messages:
                    if isinstance(msg, dict) and "timestamp" in msg:
                        ts = cls.parse_timestamp(msg["timestamp"])
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
                        # Format 1: usage directly in the message
                        if "usage" in msg:
                            token_usage.append(msg["usage"])
                        # Format 2: usage nested inside the message field
                        elif "message" in msg and isinstance(msg["message"], dict):
                            if "usage" in msg["message"]:
                                usage = msg["message"]["usage"]
                                token_usage.append(usage)
                                # Track cache usage
                                cache_read_total += usage.get("cache_read_input_tokens", 0)
                                cache_write_total += usage.get("cache_creation_input_tokens", 0)

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

                    # Calculate cost in USD if the model is known
                    if model:
                        token_counts = {
                            "input": total_input,
                            "output": total_output,
                            "cache_read": cache_read_total,
                            "cache_write": cache_write_total,
                        }
                        cost_usd = cls.calculate_cost(token_counts, model)
                        if cost_usd is not None:
                            cost_data["cost_usd"] = cost_usd
                            cost_data["cost_formatted"] = f"${cost_usd:.4f}"
                        else:
                            cost_data["cost_calculation_note"] = f"Pricing not available for model: {model}"

        except Exception as e:
            cost_data["transcript_parse_error"] = str(e)

        return {"cost_data": cost_data}

    @classmethod
    def aggregation(cls, session_directory: Path) -> None:
        """
        Aggregate cost data from all session files into a summary.

        Reads all session JSON files and creates an aggregated summary with:
        - Total token usage across all sessions
        - Total cost in USD
        - Session count and per-session details
        - Creation date (preserved) and last update timestamp

        Args:
            session_directory: Directory containing individual session JSON files

        Creates:
            costs_aggregation.json in the parent directory with aggregated metrics
        """
        try:
            aggregated_file = session_directory.parent / "costs_aggregation.json"

            # Check if the aggregated file already exists to preserve created_date
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

            # Loop through all .json files in the parent directory
            for json_file in session_directory.glob("*.json"):
                with open(json_file, 'r') as f:
                    data = json.load(f)
                # Track sessions
                sessions.append({
                    "session_id": data.get('session_id'),
                    "date": data.get('timestamp'),
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

            # Sort sessions by date
            sessions.sort(key=lambda x: x['date'] if x['date'] else '')

            # Determine created_date and last_update
            now = datetime.now(timezone.utc).isoformat()
            created_date = existing_created_date if existing_created_date else now
            last_update = now

            # Save aggregated data
            with open(aggregated_file, 'w') as f:
                json.dump({
                    "created_date": created_date,
                    "last_update": last_update,
                    "session_count": len(sessions),
                    "total_tokens": total_tokens_sum,
                    "cache_usage": cache_usage_sum,
                    "cost_usd": round(cost_usd_sum, 4),
                    "cost_formatted": f"${cost_usd_sum:.4f}",
                    "sessions": sessions
                }, f, indent=2)

            print(f"Aggregated data saved to: {aggregated_file}", file=sys.stderr)
            print(f"  Sessions: {len(sessions)}, Total cost: ${cost_usd_sum:.4f}", file=sys.stderr)

        except Exception as e:
            print(f"Warning: Failed to aggregate data: {e}", file=sys.stderr)
            # Don't fail the main task if aggregation fails


if __name__ == "__main__":
    CostsLogger.run(CostsLogger.hook_information())
