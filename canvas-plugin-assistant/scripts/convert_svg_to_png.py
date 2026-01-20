# /// script
# dependencies = ["cairosvg"]
# requires-python = ">=3.8"
# ///
"""
Convert SVG files to PNG format using CairoSVG.

This script provides a simple command-line interface for converting SVG vector graphics
to PNG raster images with a fixed size (48x48 pixels).

Usage:
    uv run --with cairosvg python convert_svg_to_png.py <svg_path> <png_path>

Dependencies:
    - cairosvg: Used for SVG to PNG conversion
"""

import sys
from dataclasses import dataclass
from pathlib import Path

import cairosvg


@dataclass
class ConversionInput:
    """
    Input parameters for SVG to PNG conversion.

    Attributes:
        svg_path: Path to the input SVG file
        png_path: Path where the output PNG should be saved
        size: Width and height in pixels for the output PNG (square)
    """
    svg_path: Path
    png_path: Path
    size: int = 48


class SvgToPngConverter:
    """
    Converter for transforming SVG files to PNG format.

    This class provides class methods to parse command-line arguments,
    perform the conversion, and run the complete workflow.
    """

    @classmethod
    def parse_arguments(cls) -> ConversionInput:
        """
        Parse command-line arguments for conversion parameters.

        Expects exactly two arguments: svg_path and png_path.

        Returns:
            ConversionInput with parsed paths and default size

        Raises:
            SystemExit: If argument count is incorrect
        """
        if len(sys.argv) != 3:
            print("Usage: convert_svg_to_png.py <svg_path> <png_path>", file=sys.stderr)
            sys.exit(1)

        return ConversionInput(
            svg_path=Path(sys.argv[1]),
            png_path=Path(sys.argv[2]),
        )

    @classmethod
    def convert(cls, conversion_input: ConversionInput) -> bool:
        """
        Convert an SVG file to PNG format with specified dimensions.

        Args:
            conversion_input: Parameters including paths and output size

        Returns:
            True if conversion succeeded, False otherwise
        """
        try:
            svg_content = conversion_input.svg_path.read_bytes()

            cairosvg.svg2png(
                bytestring=svg_content,
                write_to=str(conversion_input.png_path),
                output_width=conversion_input.size,
                output_height=conversion_input.size
            )

            return True
        except Exception as e:
            print(f"Error converting {conversion_input.svg_path}: {e}", file=sys.stderr)
            return False

    @classmethod
    def run(cls, conversion_input: ConversionInput) -> None:
        """
        Execute the conversion workflow.

        This is the main entry point that orchestrates the conversion process:
        1. Performs the SVG to PNG conversion
        2. Reports success or failure
        3. Exits with appropriate code

        Args:
            conversion_input: Parameters for the conversion

        Raises:
            SystemExit: With code 0 on success, 1 on failure
        """
        if cls.convert(conversion_input):
            print(f"✓ Successfully created: {conversion_input.png_path}")
            sys.exit(0)
        else:
            print("✗ Conversion failed", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    SvgToPngConverter.run(SvgToPngConverter.parse_arguments())
