"""Tests for update_pricing module."""

import json
import sys
from unittest.mock import ANY, call, patch

import pytest

from conftest import MockContextManager

sys.path.insert(
    0, "/media/DATA/anthropic_plugins/coding-agents/canvas-plugin-assistant/scripts"
)

import update_pricing


# =============================================================================
# Tests for fetch_models_from_api
# =============================================================================


@patch("update_pricing.urlopen")
def test_fetch_models_from_api__success(mock_urlopen, capsys):
    """Test fetch_models_from_api returns model IDs on success."""
    api_response = json.dumps(
        {"data": [{"id": "claude-3-opus-20240229"}, {"id": "claude-3-sonnet-20240229"}]}
    ).encode()
    mock_ctx = MockContextManager(read_data=api_response)
    mock_urlopen.side_effect = [mock_ctx]

    tested = update_pricing.fetch_models_from_api

    result = tested("test-api-key")

    expected = ["claude-opus-3", "claude-sonnet-3"]
    assert result == expected

    exp_urlopen_calls = [call(ANY, timeout=10)]
    assert mock_urlopen.mock_calls == exp_urlopen_calls


@patch("update_pricing.urlopen")
def test_fetch_models_from_api__with_empty_ids_and_duplicates(mock_urlopen, capsys):
    """Test fetch_models_from_api handles empty IDs and duplicate models."""
    api_response = json.dumps(
        {
            "data": [
                {"id": "claude-3-opus-20240229"},
                {"id": ""},  # Empty ID - should be skipped
                {"id": "claude-3-opus-20240301"},  # Duplicate - normalizes to same as first
                {},  # Missing ID - should be skipped
            ]
        }
    ).encode()
    mock_urlopen.side_effect = [MockContextManager(read_data=api_response)]

    tested = update_pricing.fetch_models_from_api

    result = tested("test-api-key")

    # Should only have one model - duplicates and empty IDs are excluded
    expected = ["claude-opus-3"]
    assert result == expected

    exp_urlopen_calls = [call(ANY, timeout=10)]
    assert mock_urlopen.mock_calls == exp_urlopen_calls


@patch("update_pricing.urlopen")
def test_fetch_models_from_api__http_error_401(mock_urlopen, capsys):
    """Test fetch_models_from_api handles 401 HTTPError."""
    from urllib.error import HTTPError

    mock_urlopen.side_effect = [
        HTTPError("url", 401, "Unauthorized", {}, None)
    ]

    tested = update_pricing.fetch_models_from_api

    result = tested("invalid-key")

    expected = None
    assert result is expected

    captured = capsys.readouterr()
    assert "Invalid API key" in captured.err

    exp_urlopen_calls = [call(ANY, timeout=10)]
    assert mock_urlopen.mock_calls == exp_urlopen_calls


@patch("update_pricing.urlopen")
def test_fetch_models_from_api__http_error_other(mock_urlopen, capsys):
    """Test fetch_models_from_api handles non-401 HTTPError."""
    from urllib.error import HTTPError

    mock_urlopen.side_effect = [
        HTTPError("url", 500, "Server Error", {}, None)
    ]

    tested = update_pricing.fetch_models_from_api

    result = tested("test-key")

    expected = None
    assert result is expected

    captured = capsys.readouterr()
    assert "HTTP Error 500" in captured.err

    exp_urlopen_calls = [call(ANY, timeout=10)]
    assert mock_urlopen.mock_calls == exp_urlopen_calls


@patch("update_pricing.urlopen")
def test_fetch_models_from_api__url_error(mock_urlopen, capsys):
    """Test fetch_models_from_api handles URLError."""
    from urllib.error import URLError

    mock_urlopen.side_effect = [URLError("Network unreachable")]

    tested = update_pricing.fetch_models_from_api

    result = tested("test-key")

    expected = None
    assert result is expected

    captured = capsys.readouterr()
    assert "Error fetching models from API" in captured.err

    exp_urlopen_calls = [call(ANY, timeout=10)]
    assert mock_urlopen.mock_calls == exp_urlopen_calls


@patch("update_pricing.urlopen")
def test_fetch_models_from_api__general_exception(mock_urlopen, capsys):
    """Test fetch_models_from_api handles general Exception."""
    mock_urlopen.side_effect = [Exception("Unexpected error")]

    tested = update_pricing.fetch_models_from_api

    result = tested("test-key")

    expected = None
    assert result is expected

    captured = capsys.readouterr()
    assert "Unexpected error" in captured.err

    exp_urlopen_calls = [call(ANY, timeout=10)]
    assert mock_urlopen.mock_calls == exp_urlopen_calls


# =============================================================================
# Tests for normalize_model_id
# =============================================================================


@pytest.mark.parametrize(
    ("model_id", "expected"),
    [
        pytest.param(
            "claude-3-opus-20240229",
            "claude-opus-3",
            id="claude_3_opus",
        ),
        pytest.param(
            "claude-3-5-sonnet-20241022",
            "claude-sonnet-3-5",
            id="claude_3_5_sonnet",
        ),
        pytest.param(
            "claude-opus-4-5-20250929",
            "claude-opus-4-5",
            id="claude_opus_4_5",
        ),
        pytest.param(
            "claude-3-haiku-20240307",
            "claude-haiku-3",
            id="claude_3_haiku",
        ),
        pytest.param(
            "claude-opus-3",
            "claude-opus-3",
            id="already_normalized",
        ),
        pytest.param(
            "claude-sonnet-3-5",
            "claude-sonnet-3-5",
            id="already_normalized_with_subversion",
        ),
        pytest.param(
            "claude-unknown-20240229",
            "claude-unknown",
            id="no_recognized_tier",
        ),
        pytest.param(
            "claude-2",
            "claude-2",
            id="short_id_two_parts",
        ),
        pytest.param(
            "gpt-4",
            "gpt-4",
            id="short_id_non_claude",
        ),
        pytest.param(
            "claude-opus-something",
            "claude-opus-something",
            id="tier_found_but_no_numbers",
        ),
        pytest.param(
            "claude-foo-bar-baz",
            "claude-foo-bar-baz",
            id="three_parts_no_recognized_tier",
        ),
    ],
)
def test_normalize_model_id(model_id, expected):
    """Test normalize_model_id with various model ID formats."""
    tested = update_pricing.normalize_model_id

    result = tested(model_id)

    assert result == expected


# =============================================================================
# Tests for fetch_pricing_from_web
# =============================================================================


@patch("update_pricing.urlopen")
def test_fetch_pricing_from_web__success_tiered_pricing(mock_urlopen, capsys):
    """Test fetch_pricing_from_web with tiered pricing (8+ prices)."""
    # Build HTML that matches the regex patterns in the source
    html_content = b"""
    <html>
    <h3 class="card_pricing_title_text">Sonnet 4.5</h3>
    <span data-value="3" class="tokens_main_val_number">$3</span>
    <span data-value="3.75" class="tokens_main_val_number">$3.75</span>
    <span data-value="15" class="tokens_main_val_number">$15</span>
    <span data-value="18.75" class="tokens_main_val_number">$18.75</span>
    <span data-value="3.75" class="tokens_main_val_number">$3.75</span>
    <span data-value="0.30" class="tokens_main_val_number">$0.30</span>
    <span data-value="4.68" class="tokens_main_val_number">$4.68</span>
    <span data-value="0.375" class="tokens_main_val_number">$0.375</span>
    </html>
    """
    mock_urlopen.side_effect = [MockContextManager(read_data=html_content)]

    tested = update_pricing.fetch_pricing_from_web

    result = tested()

    expected = {
        "claude-sonnet-4-5": {
            "input": 3.0,
            "output": 15.0,
            "cache_write": 3.75,
            "cache_read": 0.30,
        }
    }
    assert result == expected

    exp_urlopen_calls = [call(ANY, timeout=10)]
    assert mock_urlopen.mock_calls == exp_urlopen_calls


@patch("update_pricing.urlopen")
def test_fetch_pricing_from_web__success_simple_pricing(mock_urlopen, capsys):
    """Test fetch_pricing_from_web with simple pricing (4 prices)."""
    html_content = b"""
    <html>
    <h3 class="card_pricing_title_text">Haiku 3.5</h3>
    <span data-value="0.80" class="tokens_main_val_number">$0.80</span>
    <span data-value="4" class="tokens_main_val_number">$4</span>
    <span data-value="1" class="tokens_main_val_number">$1</span>
    <span data-value="0.08" class="tokens_main_val_number">$0.08</span>
    </html>
    """
    mock_urlopen.side_effect = [MockContextManager(read_data=html_content)]

    tested = update_pricing.fetch_pricing_from_web

    result = tested()

    expected = {
        "claude-haiku-3-5": {
            "input": 0.80,
            "output": 4.0,
            "cache_write": 1.0,
            "cache_read": 0.08,
        }
    }
    assert result == expected

    exp_urlopen_calls = [call(ANY, timeout=10)]
    assert mock_urlopen.mock_calls == exp_urlopen_calls


@patch("update_pricing.urlopen")
def test_fetch_pricing_from_web__no_model_titles(mock_urlopen, capsys):
    """Test fetch_pricing_from_web when no model titles are found."""
    html_content = b"""
    <html>
    <p class="Text_text__HrU4N">$15.00</p>
    </html>
    """
    mock_urlopen.side_effect = [MockContextManager(read_data=html_content)]

    tested = update_pricing.fetch_pricing_from_web

    result = tested()

    expected = None
    assert result is expected

    captured = capsys.readouterr()
    assert "No model titles found in HTML" in captured.err

    exp_urlopen_calls = [call(ANY, timeout=10)]
    assert mock_urlopen.mock_calls == exp_urlopen_calls


@patch("update_pricing.urlopen")
def test_fetch_pricing_from_web__no_pricing_extracted(mock_urlopen, capsys):
    """Test fetch_pricing_from_web when no pricing is extracted."""
    # Model title found but no prices (model name doesn't contain Opus/Sonnet/Haiku)
    html_content = b"""
    <html>
    <h3 class="card_pricing_title_text">Unknown Model</h3>
    </html>
    """
    mock_urlopen.side_effect = [MockContextManager(read_data=html_content)]

    tested = update_pricing.fetch_pricing_from_web

    result = tested()

    expected = None
    assert result is expected

    captured = capsys.readouterr()
    assert "No pricing data could be extracted" in captured.err

    exp_urlopen_calls = [call(ANY, timeout=10)]
    assert mock_urlopen.mock_calls == exp_urlopen_calls


@patch("update_pricing.urlopen")
def test_fetch_pricing_from_web__opus_model(mock_urlopen, capsys):
    """Test fetch_pricing_from_web with Opus model (simple pricing)."""
    html_content = b"""
    <html>
    <h3 class="card_pricing_title_text">Opus 4.5</h3>
    <span data-value="15" class="tokens_main_val_number">$15</span>
    <span data-value="75" class="tokens_main_val_number">$75</span>
    <span data-value="18.75" class="tokens_main_val_number">$18.75</span>
    <span data-value="1.50" class="tokens_main_val_number">$1.50</span>
    </html>
    """
    mock_urlopen.side_effect = [MockContextManager(read_data=html_content)]

    tested = update_pricing.fetch_pricing_from_web

    result = tested()

    expected = {
        "claude-opus-4-5": {
            "input": 15.0,
            "output": 75.0,
            "cache_write": 18.75,
            "cache_read": 1.50,
        }
    }
    assert result == expected


@patch("update_pricing.urlopen")
def test_fetch_pricing_from_web__multiple_models(mock_urlopen, capsys):
    """Test fetch_pricing_from_web with multiple models (tests end_pos calculation)."""
    html_content = b"""
    <html>
    <h3 class="card_pricing_title_text">Opus 4.5</h3>
    <span data-value="15" class="tokens_main_val_number">$15</span>
    <span data-value="75" class="tokens_main_val_number">$75</span>
    <span data-value="18.75" class="tokens_main_val_number">$18.75</span>
    <span data-value="1.50" class="tokens_main_val_number">$1.50</span>
    <h3 class="card_pricing_title_text">Haiku 3.5</h3>
    <span data-value="0.80" class="tokens_main_val_number">$0.80</span>
    <span data-value="4" class="tokens_main_val_number">$4</span>
    <span data-value="1" class="tokens_main_val_number">$1</span>
    <span data-value="0.08" class="tokens_main_val_number">$0.08</span>
    </html>
    """
    mock_urlopen.side_effect = [MockContextManager(read_data=html_content)]

    tested = update_pricing.fetch_pricing_from_web

    result = tested()

    expected = {
        "claude-opus-4-5": {
            "input": 15.0,
            "output": 75.0,
            "cache_write": 18.75,
            "cache_read": 1.50,
        },
        "claude-haiku-3-5": {
            "input": 0.80,
            "output": 4.0,
            "cache_write": 1.0,
            "cache_read": 0.08,
        },
    }
    assert result == expected


@patch("update_pricing.urlopen")
def test_fetch_pricing_from_web__insufficient_prices(mock_urlopen, capsys):
    """Test fetch_pricing_from_web with model having fewer than 4 prices."""
    html_content = b"""
    <html>
    <h3 class="card_pricing_title_text">Opus 4.5</h3>
    <span data-value="15" class="tokens_main_val_number">$15</span>
    <span data-value="75" class="tokens_main_val_number">$75</span>
    </html>
    """
    mock_urlopen.side_effect = [MockContextManager(read_data=html_content)]

    tested = update_pricing.fetch_pricing_from_web

    result = tested()

    expected = None
    assert result is expected

    captured = capsys.readouterr()
    assert "Warning: Found 2 prices for Opus 4.5" in captured.err
    assert "No pricing data could be extracted" in captured.err


@patch("update_pricing.urlopen")
def test_fetch_pricing_from_web__http_error(mock_urlopen, capsys):
    """Test fetch_pricing_from_web handles HTTPError."""
    from urllib.error import HTTPError

    mock_urlopen.side_effect = [
        HTTPError("url", 404, "Not Found", {}, None)
    ]

    tested = update_pricing.fetch_pricing_from_web

    result = tested()

    expected = None
    assert result is expected

    captured = capsys.readouterr()
    assert "HTTP Error fetching pricing page" in captured.err


@patch("update_pricing.urlopen")
def test_fetch_pricing_from_web__url_error(mock_urlopen, capsys):
    """Test fetch_pricing_from_web handles URLError."""
    from urllib.error import URLError

    mock_urlopen.side_effect = [URLError("Connection refused")]

    tested = update_pricing.fetch_pricing_from_web

    result = tested()

    expected = None
    assert result is expected

    captured = capsys.readouterr()
    assert "Error fetching pricing page" in captured.err


@patch("update_pricing.urlopen")
def test_fetch_pricing_from_web__general_exception(mock_urlopen, capsys):
    """Test fetch_pricing_from_web handles general Exception."""
    mock_urlopen.side_effect = [Exception("Parse error")]

    tested = update_pricing.fetch_pricing_from_web

    result = tested()

    expected = None
    assert result is expected

    captured = capsys.readouterr()
    assert "Unexpected error parsing pricing" in captured.err


# =============================================================================
# Tests for load_current_pricing
# =============================================================================


@patch("update_pricing.open")
def test_load_current_pricing__success(mock_open):
    """Test load_current_pricing returns pricing data on success."""
    pricing_data = {"models": {"claude-opus-3": {"input": 15.0, "output": 75.0}}}
    mock_file = MockContextManager()
    mock_open.side_effect = [mock_file]

    with patch("update_pricing.json.load") as mock_json_load:
        mock_json_load.side_effect = [pricing_data]

        tested = update_pricing.load_current_pricing

        result = tested()

        expected = {"models": {"claude-opus-3": {"input": 15.0, "output": 75.0}}}
        assert result == expected

        exp_open_calls = [call(update_pricing.PRICING_FILE, "r")]
        assert mock_open.mock_calls == exp_open_calls

        exp_json_load_calls = [call(mock_file)]
        assert mock_json_load.mock_calls == exp_json_load_calls


@patch("update_pricing.open")
def test_load_current_pricing__file_not_found(mock_open):
    """Test load_current_pricing handles FileNotFoundError."""
    mock_open.side_effect = [FileNotFoundError("pricing.json not found")]

    tested = update_pricing.load_current_pricing

    result = tested()

    expected = None
    assert result is expected

    exp_open_calls = [call(update_pricing.PRICING_FILE, "r")]
    assert mock_open.mock_calls == exp_open_calls


@patch("update_pricing.open")
def test_load_current_pricing__json_decode_error(mock_open, capsys):
    """Test load_current_pricing handles JSONDecodeError."""
    mock_file = MockContextManager()
    mock_open.side_effect = [mock_file]

    with patch("update_pricing.json.load") as mock_json_load:
        mock_json_load.side_effect = [json.JSONDecodeError("Invalid JSON", "", 0)]

        tested = update_pricing.load_current_pricing

        result = tested()

        expected = None
        assert result is expected

        captured = capsys.readouterr()
        assert "Error parsing current pricing file" in captured.err

        exp_open_calls = [call(update_pricing.PRICING_FILE, "r")]
        assert mock_open.mock_calls == exp_open_calls

        exp_json_load_calls = [call(mock_file)]
        assert mock_json_load.mock_calls == exp_json_load_calls


# =============================================================================
# Tests for save_pricing
# =============================================================================


@patch("update_pricing.open")
def test_save_pricing__success(mock_open, capsys):
    """Test save_pricing returns True on success."""
    mock_file = MockContextManager()
    mock_open.side_effect = [mock_file]

    with patch("update_pricing.json.dump") as mock_json_dump:
        mock_json_dump.side_effect = [None]

        tested = update_pricing.save_pricing
        pricing_data = {"models": {"claude-opus-3": {"input": 15.0}}}

        result = tested(pricing_data)

        expected = True
        assert result is expected

        captured = capsys.readouterr()
        assert "Pricing data saved to" in captured.out

        exp_open_calls = [call(update_pricing.PRICING_FILE, "w")]
        assert mock_open.mock_calls == exp_open_calls

        exp_json_dump_calls = [call(pricing_data, mock_file, indent=2)]
        assert mock_json_dump.mock_calls == exp_json_dump_calls


@patch("update_pricing.open")
def test_save_pricing__exception(mock_open, capsys):
    """Test save_pricing returns False on exception."""
    mock_open.side_effect = [PermissionError("Cannot write")]

    tested = update_pricing.save_pricing
    pricing_data = {"models": {}}

    result = tested(pricing_data)

    expected = False
    assert result is expected

    captured = capsys.readouterr()
    assert "Error saving pricing data" in captured.err

    exp_open_calls = [call(update_pricing.PRICING_FILE, "w")]
    assert mock_open.mock_calls == exp_open_calls


# =============================================================================
# Tests for automated_update_mode
# =============================================================================


@patch("update_pricing.save_pricing")
@patch("update_pricing.load_current_pricing")
@patch("builtins.input")
def test_automated_update_mode__user_confirms(
    mock_input, mock_load, mock_save, capsys
):
    """Test automated_update_mode when user confirms update."""
    mock_load.side_effect = [
        {"models": {"claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50}}}
    ]
    mock_input.side_effect = ["yes"]
    mock_save.side_effect = [True]

    tested = update_pricing.automated_update_mode
    api_models = ["claude-opus-3"]
    web_pricing = {"claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50}}

    result = tested(api_models, web_pricing)

    expected = True
    assert result is expected

    exp_load_calls = [call()]
    assert mock_load.mock_calls == exp_load_calls

    exp_input_calls = [call("\nSave these changes? (yes/no): ")]
    assert mock_input.mock_calls == exp_input_calls


@patch("update_pricing.save_pricing")
@patch("update_pricing.load_current_pricing")
@patch("builtins.input")
def test_automated_update_mode__user_declines(
    mock_input, mock_load, mock_save, capsys
):
    """Test automated_update_mode when user declines update."""
    mock_load.side_effect = [
        {"models": {"claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50}}}
    ]
    mock_input.side_effect = ["no"]

    tested = update_pricing.automated_update_mode
    api_models = ["claude-opus-3"]
    web_pricing = {"claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50}}

    result = tested(api_models, web_pricing)

    expected = False
    assert result is expected

    captured = capsys.readouterr()
    assert "Changes discarded" in captured.out

    exp_load_calls = [call()]
    assert mock_load.mock_calls == exp_load_calls

    exp_input_calls = [call("\nSave these changes? (yes/no): ")]
    assert mock_input.mock_calls == exp_input_calls

    exp_save_calls = []
    assert mock_save.mock_calls == exp_save_calls


@patch("update_pricing.save_pricing")
@patch("update_pricing.load_current_pricing")
@patch("builtins.input")
def test_automated_update_mode__no_current_pricing(
    mock_input, mock_load, mock_save, capsys
):
    """Test automated_update_mode when no current pricing exists."""
    mock_load.side_effect = [None]
    mock_input.side_effect = ["yes"]
    mock_save.side_effect = [True]

    tested = update_pricing.automated_update_mode
    api_models = ["claude-opus-3"]
    web_pricing = {"claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50}}

    result = tested(api_models, web_pricing)

    expected = True
    assert result is expected

    captured = capsys.readouterr()
    assert "No current pricing data found" in captured.out

    exp_load_calls = [call()]
    assert mock_load.mock_calls == exp_load_calls

    exp_input_calls = [call("\nSave these changes? (yes/no): ")]
    assert mock_input.mock_calls == exp_input_calls


@patch("update_pricing.save_pricing")
@patch("update_pricing.load_current_pricing")
@patch("builtins.input")
def test_automated_update_mode__with_new_models(
    mock_input, mock_load, mock_save, capsys
):
    """Test automated_update_mode with new models detected."""
    mock_load.side_effect = [
        {"models": {"claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50}}}
    ]
    mock_input.side_effect = ["yes"]
    mock_save.side_effect = [True]

    tested = update_pricing.automated_update_mode
    api_models = ["claude-opus-3", "claude-sonnet-3-5"]
    web_pricing = {
        "claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50},
        "claude-sonnet-3-5": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.30},
    }

    result = tested(api_models, web_pricing)

    expected = True
    assert result is expected

    captured = capsys.readouterr()
    assert "New models found: 1" in captured.out
    assert "claude-sonnet-3-5" in captured.out

    exp_load_calls = [call()]
    assert mock_load.mock_calls == exp_load_calls

    exp_input_calls = [call("\nSave these changes? (yes/no): ")]
    assert mock_input.mock_calls == exp_input_calls


@patch("update_pricing.save_pricing")
@patch("update_pricing.load_current_pricing")
@patch("builtins.input")
def test_automated_update_mode__with_updated_prices(
    mock_input, mock_load, mock_save, capsys
):
    """Test automated_update_mode with updated prices detected."""
    mock_load.side_effect = [
        {"models": {"claude-opus-3": {"input": 10.0, "output": 50.0, "cache_write": 12.50, "cache_read": 1.00}}}
    ]
    mock_input.side_effect = ["yes"]
    mock_save.side_effect = [True]

    tested = update_pricing.automated_update_mode
    api_models = ["claude-opus-3"]
    web_pricing = {"claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50}}

    result = tested(api_models, web_pricing)

    expected = True
    assert result is expected

    captured = capsys.readouterr()
    assert "Updated claude-opus-3" in captured.out
    assert "$10.0" in captured.out
    assert "$15.0" in captured.out

    exp_load_calls = [call()]
    assert mock_load.mock_calls == exp_load_calls

    exp_input_calls = [call("\nSave these changes? (yes/no): ")]
    assert mock_input.mock_calls == exp_input_calls


@patch("update_pricing.save_pricing")
@patch("update_pricing.load_current_pricing")
@patch("builtins.input")
def test_automated_update_mode__with_legacy_models(
    mock_input, mock_load, mock_save, capsys
):
    """Test automated_update_mode with legacy models detected."""
    mock_load.side_effect = [
        {
            "models": {
                "claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50},
                "claude-2": {"input": 8.0, "output": 24.0, "cache_write": 10.0, "cache_read": 0.80},
            }
        }
    ]
    mock_input.side_effect = ["yes"]
    mock_save.side_effect = [True]

    tested = update_pricing.automated_update_mode
    api_models = ["claude-opus-3"]
    web_pricing = {"claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50}}

    result = tested(api_models, web_pricing)

    expected = True
    assert result is expected

    captured = capsys.readouterr()
    assert "Kept existing pricing for claude-2" in captured.out

    exp_load_calls = [call()]
    assert mock_load.mock_calls == exp_load_calls

    exp_input_calls = [call("\nSave these changes? (yes/no): ")]
    assert mock_input.mock_calls == exp_input_calls


@patch("update_pricing.save_pricing")
@patch("update_pricing.load_current_pricing")
@patch("builtins.input")
def test_automated_update_mode__save_fails(
    mock_input, mock_load, mock_save, capsys
):
    """Test automated_update_mode when save fails."""
    mock_load.side_effect = [
        {"models": {"claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50}}}
    ]
    mock_input.side_effect = ["yes"]
    mock_save.side_effect = [False]

    tested = update_pricing.automated_update_mode
    api_models = ["claude-opus-3"]
    web_pricing = {"claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50}}

    result = tested(api_models, web_pricing)

    expected = False
    assert result is expected

    captured = capsys.readouterr()
    assert "Failed to save pricing data" in captured.out

    exp_load_calls = [call()]
    assert mock_load.mock_calls == exp_load_calls

    exp_input_calls = [call("\nSave these changes? (yes/no): ")]
    assert mock_input.mock_calls == exp_input_calls


@patch("update_pricing.save_pricing")
@patch("update_pricing.load_current_pricing")
@patch("builtins.input")
def test_automated_update_mode__api_models_without_pricing(
    mock_input, mock_load, mock_save, capsys
):
    """Test automated_update_mode with API models that have no pricing data."""
    mock_load.side_effect = [
        {"models": {"claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50}}}
    ]
    mock_input.side_effect = ["yes"]
    mock_save.side_effect = [True]

    tested = update_pricing.automated_update_mode
    # API has models that don't have web pricing
    api_models = ["claude-opus-3", "claude-new-model"]
    web_pricing = {"claude-opus-3": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50}}

    result = tested(api_models, web_pricing)

    expected = True
    assert result is expected

    captured = capsys.readouterr()
    assert "claude-new-model" in captured.out
    assert "from API has no pricing data" in captured.out
    assert "1 model(s) from API do not have pricing data" in captured.out
    assert "will NOT be added to the pricing file" in captured.out

    exp_load_calls = [call()]
    assert mock_load.mock_calls == exp_load_calls

    exp_input_calls = [call("\nSave these changes? (yes/no): ")]
    assert mock_input.mock_calls == exp_input_calls


# =============================================================================
# Tests for main
# =============================================================================


@patch("update_pricing.automated_update_mode")
@patch("update_pricing.fetch_pricing_from_web")
@patch("update_pricing.fetch_models_from_api")
@patch.dict("os.environ", {}, clear=True)
@patch("sys.exit")
@patch("sys.argv", ["update_pricing.py"])
def test_main__api_key_not_set(
    mock_exit, mock_fetch_api, mock_fetch_web, mock_automated, capsys
):
    """Test main exits when API key is not set."""
    mock_exit.side_effect = [SystemExit(1)]

    tested = update_pricing.main

    with pytest.raises(SystemExit):
        tested()

    captured = capsys.readouterr()
    assert "ANTHROPIC_API_KEY" in captured.err

    exp_exit_calls = [call(1)]
    assert mock_exit.mock_calls == exp_exit_calls

    exp_fetch_api_calls = []
    assert mock_fetch_api.mock_calls == exp_fetch_api_calls

    exp_fetch_web_calls = []
    assert mock_fetch_web.mock_calls == exp_fetch_web_calls

    exp_automated_calls = []
    assert mock_automated.mock_calls == exp_automated_calls


@patch("update_pricing.automated_update_mode")
@patch("update_pricing.fetch_pricing_from_web")
@patch("update_pricing.fetch_models_from_api")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
@patch("sys.exit")
@patch("sys.argv", ["update_pricing.py"])
def test_main__api_fetch_fails(
    mock_exit, mock_fetch_api, mock_fetch_web, mock_automated, capsys
):
    """Test main exits when API fetch fails."""
    mock_fetch_api.side_effect = [None]
    mock_exit.side_effect = [SystemExit(1)]

    tested = update_pricing.main

    with pytest.raises(SystemExit):
        tested()

    captured = capsys.readouterr()
    assert "Failed to fetch models from API" in captured.err

    exp_exit_calls = [call(1)]
    assert mock_exit.mock_calls == exp_exit_calls

    exp_fetch_api_calls = [call("test-key")]
    assert mock_fetch_api.mock_calls == exp_fetch_api_calls

    exp_fetch_web_calls = []
    assert mock_fetch_web.mock_calls == exp_fetch_web_calls

    exp_automated_calls = []
    assert mock_automated.mock_calls == exp_automated_calls


@patch("update_pricing.automated_update_mode")
@patch("update_pricing.fetch_pricing_from_web")
@patch("update_pricing.fetch_models_from_api")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
@patch("sys.exit")
@patch("sys.argv", ["update_pricing.py"])
def test_main__web_pricing_fetch_fails(
    mock_exit, mock_fetch_api, mock_fetch_web, mock_automated, capsys
):
    """Test main exits when web pricing fetch fails."""
    mock_fetch_api.side_effect = [["claude-opus-3"]]
    mock_fetch_web.side_effect = [None]
    mock_exit.side_effect = [SystemExit(1)]

    tested = update_pricing.main

    with pytest.raises(SystemExit):
        tested()

    captured = capsys.readouterr()
    assert "Failed to fetch pricing from web page" in captured.err

    exp_exit_calls = [call(1)]
    assert mock_exit.mock_calls == exp_exit_calls

    exp_fetch_api_calls = [call("test-key")]
    assert mock_fetch_api.mock_calls == exp_fetch_api_calls

    exp_fetch_web_calls = [call()]
    assert mock_fetch_web.mock_calls == exp_fetch_web_calls

    exp_automated_calls = []
    assert mock_automated.mock_calls == exp_automated_calls


@patch("update_pricing.automated_update_mode")
@patch("update_pricing.fetch_pricing_from_web")
@patch("update_pricing.fetch_models_from_api")
@patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}, clear=True)
@patch("sys.argv", ["update_pricing.py"])
def test_main__success(mock_fetch_api, mock_fetch_web, mock_automated, capsys):
    """Test main returns True on success."""
    mock_fetch_api.side_effect = [["claude-opus-3"]]
    mock_fetch_web.side_effect = [{"claude-opus-3": {"input": 15.0, "output": 75.0}}]
    mock_automated.side_effect = [True]

    tested = update_pricing.main

    result = tested()

    expected = True
    assert result is expected

    exp_fetch_api_calls = [call("test-key")]
    assert mock_fetch_api.mock_calls == exp_fetch_api_calls

    exp_fetch_web_calls = [call()]
    assert mock_fetch_web.mock_calls == exp_fetch_web_calls

    exp_automated_calls = [call(["claude-opus-3"], {"claude-opus-3": {"input": 15.0, "output": 75.0}})]
    assert mock_automated.mock_calls == exp_automated_calls
