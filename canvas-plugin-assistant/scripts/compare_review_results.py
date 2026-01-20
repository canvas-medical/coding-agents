#!/usr/bin/env python3
"""
Compare review results against expected findings using Anthropic API.

This script takes generated review reports (security and/or database) and an expected.json file,
then uses Claude to determine if the expected findings were detected.

Usage:
    python compare_review_results.py \
        --security-report path/to/security-review-output.md \
        --database-report path/to/database-review-output.md \
        --expected path/to/expected.json

Environment:
    EVALS_ANTHROPIC_API_KEY: Required API key for Anthropic
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests


def call_anthropic(api_key: str, prompt: str) -> dict:
    """
    Call Anthropic API with a prompt and return the response.

    Args:
        api_key: Anthropic API key for authentication
        prompt: User prompt to send to the model

    Returns:
        Dictionary with either:
        - {'success': True, 'content': <response text>} on success
        - {'success': False, 'error': <error message>} on failure
    """
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "x-api-key": api_key,
    }
    payload = {
        "model": "claude-sonnet-4-5-20250929",
        "temperature": 0.0,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)

    if response.status_code == 200:
        data = response.json()
        content = data.get("content", [{}])[0].get("text", "")
        return {"success": True, "content": content}
    else:
        return {"success": False, "error": response.text}


def compare_findings(security_report: str, database_report: str, expected: dict, api_key: str) -> dict:
    """
    Use Anthropic API to compare review reports against expected findings.

    Constructs a prompt with expected findings and generated reports, then uses
    Claude to determine if each expected issue was detected in the reports.

    Args:
        security_report: Content of the security review report (might be empty)
        database_report: Content of the database review report (might be empty)
        expected: Dictionary with 'eval_name' and 'expected_findings' list
        api_key: Anthropic API key for authentication

    Returns:
        Dictionary with:
        - eval_name: Name of the evaluation
        - findings: List of dictionaries with 'category', 'severity', 'detected', 'explanation'
        - overall_pass: True if all must_detect findings were detected
        - error: Error message if API call or parsing failed (optional)
    """
    findings_text = "\n".join(
        f"- [{f['severity']}] {f['category']}: {f['description']} (must_detect: {f['must_detect']})"
        for f in expected.get("expected_findings", [])
    )

    # Combine reports
    combined_reports = ""
    if security_report:
        combined_reports += f"## Security Review Report\n\n```\n{security_report}\n```\n\n"
    if database_report:
        combined_reports += f"## Database Performance Review Report\n\n```\n{database_report}\n```\n\n"

    prompt = f"""You are evaluating whether security/performance review reports correctly detected expected issues.

## Expected Findings

The review(s) should have detected these issues:

{findings_text}

## Generated Review Reports

{combined_reports}

## Task

For EACH expected finding listed above, determine if ANY of the review reports detected it.

Respond with JSON in this exact format:
```json
{{
  "findings": [
    {{
      "category": "category from expected finding",
      "severity": "severity from expected finding",
      "detected": true/false,
      "explanation": "Brief explanation of why you determined it was or wasn't detected"
    }}
  ],
  "overall_verdict_matches": true/false,
  "explanation": "Brief overall assessment"
}}
```

Be generous in interpretation - if any report mentions the issue in any reasonable way, count it as detected.
The category and severity don't need to match exactly, just the core issue."""

    response = call_anthropic(api_key, prompt)

    if not response["success"]:
        return {
            "eval_name": expected.get("eval_name", "unknown"),
            "error": response.get("error", "API call failed"),
            "overall_pass": False,
        }

    # Extract JSON from response
    content = response["content"]
    try:
        # Find JSON block in response
        json_match = re.search(r"```json\s*\n(.*?)\n\s*```", content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(1))
        else:
            # Try parsing entire content as JSON
            result = json.loads(content)

        # Determine overall pass (all must_detect findings detected)
        must_detect_findings = [
            f for f in expected.get("expected_findings", []) if f.get("must_detect", True)
        ]
        detected_count = sum(
            1 for f in result.get("findings", []) if f.get("detected", False)
        )
        overall_pass = detected_count >= len(must_detect_findings)

        return {
            "eval_name": expected.get("eval_name", "unknown"),
            "findings": result.get("findings", []),
            "overall_pass": overall_pass,
            "explanation": result.get("explanation", ""),
        }

    except json.JSONDecodeError as e:
        return {
            "eval_name": expected.get("eval_name", "unknown"),
            "error": f"Failed to parse API response: {e}",
            "raw_response": content,
            "overall_pass": False,
        }

def main() -> None:
    """
    Main entry point for the review comparison script.

    Parses command-line arguments, loads expected findings, reads review reports,
    and uses Claude to determine if expected issues were detected.

    Exits with code 0 if all must_detect findings passed, 1 otherwise.
    """
    parser = argparse.ArgumentParser(
        description="Compare review results against expected findings"
    )
    parser.add_argument(
        "--security-report", help="Path to the security review report"
    )
    parser.add_argument(
        "--database-report", help="Path to the database performance review report"
    )
    parser.add_argument(
        "--expected", required=True, help="Path to expected.json file"
    )
    parser.add_argument(
        "--output", help="Optional path to save JSON results"
    )
    args = parser.parse_args()

    # Require at least one report
    if not args.security_report and not args.database_report:
        print("ERROR: At least one of --security-report or --database-report is required", file=sys.stderr)
        sys.exit(1)

    # Get API key
    api_key = os.environ.get("EVALS_ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: EVALS_ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Read files
    expected_path = Path(args.expected)

    if not expected_path.exists():
        print(f"ERROR: Expected file not found: {expected_path}", file=sys.stderr)
        sys.exit(1)

    security_report = ""
    if args.security_report:
        security_path = Path(args.security_report)
        if security_path.exists():
            security_report = security_path.read_text()
        else:
            print(f"WARNING: Security report not found: {security_path}", file=sys.stderr)

    database_report = ""
    if args.database_report:
        database_path = Path(args.database_report)
        if database_path.exists():
            database_report = database_path.read_text()
        else:
            print(f"WARNING: Database report not found: {database_path}", file=sys.stderr)

    expected = json.loads(expected_path.read_text())

    # Compare
    result = compare_findings(security_report, database_report, expected, api_key)

    # Output
    output_json = json.dumps(result, indent=2)

    if args.output:
        Path(args.output).write_text(output_json)
        print(f"Results saved to: {args.output}")
    else:
        print(output_json)

    # Exit code based on pass/fail
    sys.exit(0 if result.get("overall_pass", False) else 1)


if __name__ == "__main__":
    main()
