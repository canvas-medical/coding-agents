"""Tests for convert_svg_to_png module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# Mock cairosvg before importing the module under test
sys.modules["cairosvg"] = MagicMock()

from conftest import is_dataclass
from convert_svg_to_png import ConversionInput, SvgToPngConverter


class TestConversionInput:
    """Tests for the ConversionInput dataclass."""

    def test_class(self) -> None:
        """Verify ConversionInput is a dataclass with correct fields."""
        tested = ConversionInput
        fields = {
            "svg_path": Path,
            "png_path": Path,
            "size": int,
        }
        assert is_dataclass(tested, fields)

    def test_default_size(self) -> None:
        """Verify default size is 48."""
        tested = ConversionInput(
            svg_path=Path("/input.svg"),
            png_path=Path("/output.png"),
        )
        result = tested.size
        expected = 48
        assert result == expected


class TestSvgToPngConverter:
    """Tests for the SvgToPngConverter class."""

    @patch("convert_svg_to_png.sys")
    def test_parse_arguments__valid_args(self, mock_sys) -> None:
        """Test parse_arguments with valid arguments."""
        tested = SvgToPngConverter
        mock_sys.argv = ["script.py", "/path/to/input.svg", "/path/to/output.png"]

        result = tested.parse_arguments()

        expected = ConversionInput(
            svg_path=Path("/path/to/input.svg"),
            png_path=Path("/path/to/output.png"),
        )
        assert result == expected

        exp_sys_calls = []
        assert mock_sys.mock_calls == exp_sys_calls

    @pytest.mark.parametrize(
        "argv",
        [
            pytest.param(["script.py"], id="no_args"),
            pytest.param(["script.py", "/input.svg"], id="one_arg"),
            pytest.param(
                ["script.py", "/input.svg", "/output.png", "extra"],
                id="three_args",
            ),
        ],
    )
    @patch("convert_svg_to_png.sys")
    def test_parse_arguments__invalid_arg_count(self, mock_sys, argv) -> None:
        """Test parse_arguments exits with invalid argument count."""
        tested = SvgToPngConverter
        mock_sys.argv = argv
        mock_sys.exit.side_effect = [SystemExit(1)]

        with pytest.raises(SystemExit):
            tested.parse_arguments()

        exp_sys_calls = [
            call.stderr.write("Usage: convert_svg_to_png.py <svg_path> <png_path>"),
            call.stderr.write("\n"),
            call.exit(1),
        ]
        assert mock_sys.mock_calls == exp_sys_calls

    @patch("convert_svg_to_png.cairosvg")
    def test_convert__success(self, mock_cairosvg) -> None:
        """Test convert returns True on successful conversion."""
        mock_cairosvg.svg2png.side_effect = [None]

        svg_content = b"<svg></svg>"
        with patch.object(Path, "read_bytes") as mock_read_bytes:
            mock_read_bytes.side_effect = [svg_content]
            conversion_input = ConversionInput(
                svg_path=Path("/input.svg"),
                png_path=Path("/output.png"),
                size=64,
            )

            tested = SvgToPngConverter
            result = tested.convert(conversion_input)

            expected = True
            assert result is expected

            exp_read_bytes_calls = [call()]
            assert mock_read_bytes.mock_calls == exp_read_bytes_calls

        exp_cairosvg_calls = [
            call.svg2png(
                bytestring=b"<svg></svg>",
                write_to="/output.png",
                output_width=64,
                output_height=64,
            ),
        ]
        assert mock_cairosvg.mock_calls == exp_cairosvg_calls

    @patch("convert_svg_to_png.sys")
    @patch("convert_svg_to_png.cairosvg")
    def test_convert__failure(self, mock_cairosvg, mock_sys) -> None:
        """Test convert returns False and prints error on failure."""
        mock_cairosvg.svg2png.side_effect = [Exception("Conversion error")]

        with patch.object(Path, "read_bytes") as mock_read_bytes:
            mock_read_bytes.side_effect = [b"<svg></svg>"]
            conversion_input = ConversionInput(
                svg_path=Path("/input.svg"),
                png_path=Path("/output.png"),
            )

            tested = SvgToPngConverter
            result = tested.convert(conversion_input)

            expected = False
            assert result is expected

            exp_read_bytes_calls = [call()]
            assert mock_read_bytes.mock_calls == exp_read_bytes_calls

        exp_cairosvg_calls = [
            call.svg2png(
                bytestring=b"<svg></svg>",
                write_to="/output.png",
                output_width=48,
                output_height=48,
            ),
        ]
        assert mock_cairosvg.mock_calls == exp_cairosvg_calls

        exp_sys_calls = [
            call.stderr.write("Error converting /input.svg: Conversion error"),
            call.stderr.write("\n"),
        ]
        assert mock_sys.mock_calls == exp_sys_calls

    @patch("convert_svg_to_png.sys")
    @patch("convert_svg_to_png.print")
    @patch.object(SvgToPngConverter, "convert")
    def test_run__success(self, mock_convert, mock_print, mock_sys) -> None:
        """Test run prints success message and exits with 0."""
        mock_convert.side_effect = [True]
        mock_sys.exit.side_effect = [SystemExit(0)]

        conversion_input = ConversionInput(
            svg_path=Path("/input.svg"),
            png_path=Path("/output.png"),
        )

        with pytest.raises(SystemExit):
            SvgToPngConverter.run(conversion_input)

        exp_convert_calls = [call(conversion_input)]
        assert mock_convert.mock_calls == exp_convert_calls

        exp_print_calls = [call("\u2713 Successfully created: /output.png")]
        assert mock_print.mock_calls == exp_print_calls

        exp_sys_calls = [call.exit(0)]
        assert mock_sys.mock_calls == exp_sys_calls

    @patch("convert_svg_to_png.sys")
    @patch.object(SvgToPngConverter, "convert")
    def test_run__failure(self, mock_convert, mock_sys) -> None:
        """Test run prints failure message and exits with 1."""
        mock_convert.side_effect = [False]
        mock_sys.exit.side_effect = [SystemExit(1)]

        conversion_input = ConversionInput(
            svg_path=Path("/input.svg"),
            png_path=Path("/output.png"),
        )

        with pytest.raises(SystemExit):
            SvgToPngConverter.run(conversion_input)

        exp_convert_calls = [call(conversion_input)]
        assert mock_convert.mock_calls == exp_convert_calls

        exp_sys_calls = [
            call.stderr.write("\u2717 Conversion failed"),
            call.stderr.write("\n"),
            call.exit(1),
        ]
        assert mock_sys.mock_calls == exp_sys_calls
