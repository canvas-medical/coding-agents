"""Tests for constants module."""

import pytest

from constants import Constants, _Constants


class TestConstants:
    """Tests for _Constants dataclass and Constants singleton."""

    def test_constants_instance_is_constants_type(self) -> None:
        """Verify Constants is an instance of _Constants."""
        tested = Constants

        result = isinstance(tested, _Constants)

        assert result is True

    @pytest.mark.parametrize(
        ("attr_name", "expected"),
        [
            pytest.param("CPA_RUNNING", "CPA_RUNNING", id="cpa_running"),
            pytest.param("CPA_WORKSPACE_DIR", "CPA_WORKSPACE_DIR", id="cpa_workspace_dir"),
            pytest.param("CPA_PLUGIN_DIR", "CPA_PLUGIN_DIR", id="cpa_plugin_dir"),
        ],
    )
    def test_constant_values(self, attr_name: str, expected: str) -> None:
        """Verify each constant has the expected value."""
        tested = Constants

        result = getattr(tested, attr_name)

        assert result == expected

    def test_constants_is_frozen(self) -> None:
        """Verify Constants instance is immutable (frozen dataclass)."""
        tested = Constants

        with pytest.raises(AttributeError):
            tested.CPA_RUNNING = "new_value"  # type: ignore[misc]
