#!/usr/bin/env python3
"""
Compare review results against expected findings using Anthropic API.

This script takes a generated review report and an expected.json file,
then uses Claude to determine if the expected findings were detected.

Usage:
    python compare_review_results.py --report path/to/review-output.md --expected path/to/expected.json

Environment:
    ANTHROPIC_API_KEY: Required API key for Anthropic
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests


def call_anthropic(api_key: str, prompt: str) -> dict:
    """Call Anthropic API and return response."""
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


def compare_findings(report_content: str, expected: dict, api_key: str) -> dict:
    """
    Use Anthropic API to compare report against expected findings.

    Returns dict with:
    - eval_name: Name of the eval
    - findings: List of {finding, detected, explanation}
    - overall_pass: True if all must_detect findings were detected
    """
    findings_text = "\n".join(
        f"- [{f['severity']}] {f['category']}: {f['description']} (must_detect: {f['must_detect']})"
        for f in expected.get("expected_findings", [])
    )

    prompt = f"""You are evaluating whether a security/performance review report correctly detected expected issues.

## Expected Findings

The review should have detected these issues:

{findings_text}

## Generated Review Report

```
{report_content}
```

## Task

For EACH expected finding listed above, determine if the review report detected it.

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

Be generous in interpretation - if the report mentions the issue in any reasonable way, count it as detected.
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
        import re

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


def main():
    parser = argparse.ArgumentParser(
        description="Compare review results against expected findings"
    )
    parser.add_argument(
        "--report", required=True, help="Path to the generated review report"
    )
    parser.add_argument(
        "--expected", required=True, help="Path to expected.json file"
    )
    parser.add_argument(
        "--output", help="Optional path to save JSON results"
    )
    args = parser.parse_args()

    # Get API key
    api_key = os.environ.get("EVALS_ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: EVALS_ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Read files
    report_path = Path(args.report)
    expected_path = Path(args.expected)

    if not report_path.exists():
        print(f"ERROR: Report file not found: {report_path}", file=sys.stderr)
        sys.exit(1)

    if not expected_path.exists():
        print(f"ERROR: Expected file not found: {expected_path}", file=sys.stderr)
        sys.exit(1)

    report_content = report_path.read_text()
    expected = json.loads(expected_path.read_text())

    # Compare
    result = compare_findings(report_content, expected, api_key)

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
