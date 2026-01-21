"""
Update model pricing data using Anthropic API and pricing page.
Fetches current model list from API and pricing from web page automatically.
"""

import json
import sys
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

API_URL = "https://api.anthropic.com/v1/models"
PRICING_URL = "https://claude.com/pricing#api"
PRICING_FILE = Path(__file__).parent.parent / "model_costs.json"

def fetch_models_from_api(api_key: str) -> list[str] | None:
    """
    Fetch available models from Anthropic API.

    Args:
        api_key: Anthropic API key from environment variable.

    Returns:
        List of model IDs, or None if fetch fails.
    """

    try:
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        }
        req = Request(API_URL, headers=headers)

        print("Fetching models from Anthropic API...", file=sys.stderr)
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

            # API returns: {"data": [{"id": "claude-3-opus-20240229", "type": "model", ...}, ...]}
            models = []
            for model in data.get('data', []):
                model_id = model.get('id', '')
                if model_id:
                    # Normalize model ID to base version (remove date suffixes)
                    # e.g., "claude-3-opus-20240229" -> "claude-opus-3"
                    base_id = normalize_model_id(model_id)
                    if base_id not in models:
                        models.append(base_id)

            print(f"✓ Found {len(models)} unique model families", file=sys.stderr)
            return models

    except HTTPError as e:
        if e.code == 401:
            print("Error: Invalid API key", file=sys.stderr)
        else:
            print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        return None
    except URLError as e:
        print(f"Error fetching models from API: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return None

def normalize_model_id(model_id: str) -> str:
    """
    Normalize a model ID to its base version.

    Examples:
        claude-3-opus-20240229 -> claude-opus-3
        claude-3-5-sonnet-20241022 -> claude-sonnet-3-5
        claude-3-5-haiku-20241022 -> claude-haiku-3-5
        claude-opus-4-5-20250929 -> claude-opus-4-5
        claude-sonnet-4-5 -> claude-sonnet-4-5 (already normalized)
    """
    # Remove date suffixes (8 digits at end)
    if len(model_id) >= 9 and model_id[-8:].isdigit():
        model_id = model_id[:-9]  # Remove -YYYYMMDD

    # Parse the components
    parts = model_id.split('-')

    if len(parts) < 3 or parts[0] != 'claude':
        return model_id

    # Identify tier (opus, sonnet, haiku)
    tiers = ['opus', 'sonnet', 'haiku']
    tier = None
    tier_index = -1

    for i, part in enumerate(parts):
        if part in tiers:
            tier = part
            tier_index = i
            break

    if not tier:
        return model_id  # No recognized tier found

    # Collect version numbers (everything that's not 'claude' or the tier)
    numbers = [p for i, p in enumerate(parts) if i != 0 and i != tier_index and (p.isdigit() or '.' in p)]

    if numbers:
        version = '-'.join(numbers)
        return f"claude-{tier}-{version}"

    return model_id

def fetch_pricing_from_web() -> dict[str, dict[str, float]] | None:
    """
    Fetch pricing information from Claude pricing page.

    Returns:
        Dictionary mapping normalized model IDs to pricing data, or None if fetch fails.
        Example: {"claude-opus-4-5": {"input": 5.00, "output": 25.00, ...}}
    """
    try:
        print("Fetching pricing from web page...", file=sys.stderr)
        req = Request(PRICING_URL, headers={'User-Agent': 'Mozilla/5.0'})

        with urlopen(req, timeout=10) as response:
            html_content = response.read().decode('utf-8')

        # Parse pricing information from HTML
        # The page structure uses:
        # - <h3 class="card_pricing_title_text">Model Name</h3>
        # - <span data-value="PRICE" class="tokens_main_val_number">PRICE</span>
        pricing = {}

        # Find all model cards (each has a title and pricing)
        # Pattern: <h3...>Model X.X</h3> followed by data-value prices
        model_title_pattern = r'<h3[^>]*class="[^"]*card_pricing_title_text[^"]*"[^>]*>([^<]+)</h3>'

        # Find all model titles
        model_matches = list(re.finditer(model_title_pattern, html_content))

        if not model_matches:
            print("Warning: No model titles found in HTML", file=sys.stderr)
            return None

        for i, model_match in enumerate(model_matches):
            model_name = model_match.group(1).strip()

            # Normalize model name to our format
            # "Opus 4.5" -> "claude-opus-4-5"
            model_id = None
            if 'Opus' in model_name:
                version = model_name.replace('Opus', '').strip().replace('.', '-')
                model_id = f"claude-opus-{version}"
            elif 'Sonnet' in model_name:
                version = model_name.replace('Sonnet', '').strip().replace('.', '-')
                model_id = f"claude-sonnet-{version}"
            elif 'Haiku' in model_name:
                version = model_name.replace('Haiku', '').strip().replace('.', '-')
                model_id = f"claude-haiku-{version}"

            if not model_id:
                continue

            # Extract context after this model (until next model or 2000 chars)
            start_pos = model_match.end()
            if i + 1 < len(model_matches):
                end_pos = model_matches[i + 1].start()
            else:
                end_pos = start_pos + 2000

            context = html_content[start_pos:end_pos]

            # Extract all data-value attributes in this context
            # Pattern: data-value="NUMBER"
            price_pattern = r'data-value="(\d+(?:\.\d+)?)"'
            prices = re.findall(price_pattern, context)

            if len(prices) >= 8:
                # Tiered pricing model (e.g., Sonnet 4.5)
                # Structure: Input (≤200K, >200K), Output (≤200K, >200K), Cache Write (≤200K, >200K), Cache Read (≤200K, >200K)
                # We use the first tier (≤200K) prices: indices [0, 2, 4, 5]
                input_price = float(prices[0])
                output_price = float(prices[2])
                cache_write_price = float(prices[4])
                cache_read_price = float(prices[5])

                pricing[model_id] = {
                    "input": input_price,
                    "output": output_price,
                    "cache_write": cache_write_price,
                    "cache_read": cache_read_price
                }
                print(f"  ✓ Found pricing for {model_id}: Input=${input_price}, Output=${output_price} (using ≤200K tier)", file=sys.stderr)
            elif len(prices) >= 4:
                # Simple pricing model (Opus, Haiku)
                # Structure: Input, Output, Cache Write, Cache Read
                input_price = float(prices[0])
                output_price = float(prices[1])
                cache_write_price = float(prices[2])
                cache_read_price = float(prices[3])

                pricing[model_id] = {
                    "input": input_price,
                    "output": output_price,
                    "cache_write": cache_write_price,
                    "cache_read": cache_read_price
                }
                print(f"  ✓ Found pricing for {model_id}: Input=${input_price}, Output=${output_price}", file=sys.stderr)
            else:
                print(f"  ⚠ Warning: Found {len(prices)} prices for {model_name} (expected 4 or 8)", file=sys.stderr)

        if pricing:
            print(f"✓ Successfully extracted pricing for {len(pricing)} models", file=sys.stderr)
            return pricing
        else:
            print("Warning: No pricing data could be extracted from page", file=sys.stderr)
            return None

    except HTTPError as e:
        print(f"HTTP Error fetching pricing page: {e.code} {e.reason}", file=sys.stderr)
        return None
    except URLError as e:
        print(f"Error fetching pricing page: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error parsing pricing: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None

def load_current_pricing() -> dict | None:
    """
    Load current pricing data from the model_costs.json file.

    Returns:
        Dictionary with pricing data structure, or None if file not found or invalid
    """
    try:
        with open(PRICING_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing current pricing file: {e}", file=sys.stderr)
        return None

def save_pricing(pricing_data: dict) -> bool:
    """
    Save pricing data to the model_costs.json file.

    Args:
        pricing_data: Dictionary containing pricing information to save

    Returns:
        True if save succeeded, False otherwise
    """
    try:
        with open(PRICING_FILE, 'w') as f:
            json.dump(pricing_data, f, indent=2)
        print(f"✓ Pricing data saved to {PRICING_FILE}")
        return True
    except Exception as e:
        print(f"Error saving pricing data: {e}", file=sys.stderr)
        return False

def automated_update_mode(api_models: list[str], web_pricing: dict[str, dict[str, float]]) -> bool:
    """
    Automated mode for updating pricing using API models and web pricing.

    Compares the current pricing database with newly fetched API models and web pricing,
    shows a summary of changes, and prompts for user confirmation before saving.

    Args:
        api_models: List of model IDs from the Anthropic API
        web_pricing: Dictionary of pricing data scraped from the web

    Returns:
        True if user confirmed and save succeeded, False otherwise
    """
    print("\n" + "="*70)
    print("AUTOMATED PRICING UPDATE")
    print("="*70)

    current = load_current_pricing()
    if not current:
        print("No current pricing data found. Creating new file...")
        current = {
            "last_updated": "",
            "source": PRICING_URL,
            "note": "Prices are per 1M tokens in USD",
            "models": {}
        }

    print(f"\nCurrent pricing data:")
    print(f"  Last updated: {current.get('last_updated', 'Never')}")
    print(f"  Models in database: {len(current.get('models', {}))}")

    # Compare API models with current database
    current_models = set(current.get('models', {}).keys())
    api_model_set = set(api_models)

    new_models = api_model_set - current_models
    missing_from_api = current_models - api_model_set

    print(f"\n  Models from API: {len(api_models)}")
    print(f"  New models found: {len(new_models)}")
    if new_models:
        for m in sorted(new_models):
            print(f"    + {m}")

    if missing_from_api:
        print(f"\n  Models in database but not in API: {len(missing_from_api)}")
        for m in sorted(missing_from_api):
            print(f"    - {m} (might be deprecated)")

    # Merge pricing: Use web pricing for known models, keep existing for others
    updated_models = {}

    # Add all models that have web pricing
    for model_id, prices in web_pricing.items():
        updated_models[model_id] = prices
        if model_id in current.get('models', {}):
            old_prices = current['models'][model_id]
            if prices != old_prices:
                print(f"\n  Updated {model_id}:")
                print(f"    Input:       ${old_prices['input']} → ${prices['input']}")
                print(f"    Output:      ${old_prices['output']} → ${prices['output']}")
                print(f"    Cache Write: ${old_prices['cache_write']} → ${prices['cache_write']}")
                print(f"    Cache Read:  ${old_prices['cache_read']} → ${prices['cache_read']}")
            else:
                print(f"  ✓ {model_id} (no changes)")
        else:
            print(f"  + Added {model_id} with pricing from web")

    # Keep existing models that aren't in web pricing (legacy models)
    for model_id, prices in current.get('models', {}).items():
        if model_id not in updated_models:
            updated_models[model_id] = prices
            print(f"  ✓ Kept existing pricing for {model_id} (not found on web)")

    # Check for API models without pricing
    models_without_pricing = []
    for model_id in api_models:
        if model_id not in updated_models:
            models_without_pricing.append(model_id)
            print(f"  ⚠ Warning: {model_id} from API has no pricing data")

    if models_without_pricing:
        print(f"\n⚠ {len(models_without_pricing)} model(s) from API do not have pricing data.")
        print("They will NOT be added to the pricing file.")

    # Prepare updated data
    updated_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "source": PRICING_URL,
        "note": "Prices are per 1M tokens in USD",
        "models": updated_models
    }

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total models: {len(updated_models)}")
    print(f"  From web pricing: {len(web_pricing)}")
    print(f"  Legacy models kept: {len(updated_models) - len(web_pricing)}")
    print(f"  API models without pricing: {len(models_without_pricing)}")

    print("\n" + "="*70)
    print("UPDATED PRICING DATA")
    print("="*70)
    print(json.dumps(updated_data, indent=2))

    print("\n" + "="*70)
    confirm = input("\nSave these changes? (yes/no): ").strip().lower()
    if confirm in ['yes', 'y']:
        if save_pricing(updated_data):
            print("\n✓ Pricing updated successfully!")
            return True
        else:
            print("\n✗ Failed to save pricing data")
            return False
    else:
        print("\nChanges discarded.")
        return False

def main() -> bool | None:
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Update Claude model pricing data automatically using Anthropic API and pricing page",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update pricing (requires ANTHROPIC_API_KEY environment variable)
    export ANTHROPIC_API_KEY=your_api_key_here
  %(prog)s

  # Use a different environment variable name
    export MY_ANTHROPIC_KEY=your_api_key_here
  %(prog)s --api-key-env MY_ANTHROPIC_KEY

How it works:
  - Fetches model list from Anthropic API (requires API key)
  - Fetches pricing from https://claude.com/pricing#api automatically
  - Updates model_costs.json with merged data
  - No manual price entry required
        """
    )
    parser.add_argument(
        '--api-key-env',
        default='ANTHROPIC_API_KEY',
        help='Name of environment variable containing the API key (default: ANTHROPIC_API_KEY)'
    )

    args = parser.parse_args()

    print("="*70)
    print("Claude Code - Pricing Update Utility")
    print("="*70)

    # Check for API key in environment variable
    api_key_env_name = args.api_key_env
    api_key = os.environ.get(api_key_env_name)

    if not api_key:
        print(f"\n✗ Error: API key not found in environment variable", file=sys.stderr)
        print(f"\nEnvironment variable '{api_key_env_name}' is not set.", file=sys.stderr)
        print("\nTo use this script, you must:", file=sys.stderr)
        print(f"  1. Obtain an API key from https://console.anthropic.com/", file=sys.stderr)
        print(f"  2. Set the environment variable:", file=sys.stderr)
        print(f"      export {api_key_env_name}=your_api_key_here", file=sys.stderr)
        print(f"  3. Run the script again", file=sys.stderr)
        print("\nAlternatively, use a different environment variable:", file=sys.stderr)
        print(f"      export MY_KEY=your_api_key_here", file=sys.stderr)
        print(f"     {sys.argv[0]} --api-key-env MY_KEY", file=sys.stderr)
        sys.exit(1)

    # Fetch models from API
    print(f"\nUsing API key from environment variable: {api_key_env_name}")
    print("Fetching models from Anthropic API...")

    api_models = fetch_models_from_api(api_key)

    if not api_models:
        print("\n✗ Error: Failed to fetch models from API", file=sys.stderr)
        print("\nPossible reasons:", file=sys.stderr)
        print("  - Invalid API key", file=sys.stderr)
        print("  - Network connectivity issues", file=sys.stderr)
        print("  - API endpoint unavailable", file=sys.stderr)
        sys.exit(1)

    print(f"\n✓ Successfully fetched {len(api_models)} model families from API")
    print("\nModels found:")
    for model in sorted(api_models):
        print(f"  - {model}")

    # Fetch pricing from the web page
    print()
    web_pricing = fetch_pricing_from_web()

    if not web_pricing:
        print("\n✗ Error: Failed to fetch pricing from web page", file=sys.stderr)
        print("\nPossible reasons:", file=sys.stderr)
        print("  - Network connectivity issues", file=sys.stderr)
        print("  - Pricing page structure changed", file=sys.stderr)
        print("  - Page unavailable", file=sys.stderr)
        sys.exit(1)

    # Run automated update mode with API models and web pricing
    return automated_update_mode(api_models, web_pricing)

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nUpdate cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
