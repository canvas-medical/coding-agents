# /// script
# dependencies = ["cairosvg"]
# requires-python = ">=3.8"
# ///
"""
Convert SVG files to PNG format using CairoCVG.

This script provides a simple command-line interface for converting SVG vector graphics
to PNG raster images with a fixed size (48x48 pixels).

Usage:
    uv run --with cairosvg python convert_svg_to_png.py <svg_path> <png_path>

Dependencies:
    - cairosvg: Used for SVG to PNG conversion
"""

import sys
import cairosvg


def convert_svg_to_png(svg_path: str, png_path: str, size: int) -> bool:
    """
    Convert an SVG file to PNG format with specified dimensions.

    Args:
        svg_path: Path to the input SVG file
        png_path: Path where the output PNG should be saved
        size: Width and height in pixels for the output PNG (square)

    Returns:
        True if conversion succeeded, False otherwise
    """
    try:
        # Read SVG content
        with open(svg_path, 'rb') as f:
            svg_content = f.read()

        # Convert to PNG
        cairosvg.svg2png(
            bytestring=svg_content,
            write_to=png_path,
            output_width=size,
            output_height=size
        )

        return True
    except Exception as e:
        print(f"Error converting {svg_path}: {e}", file=sys.stderr)
        return False

def main() -> None:
    """
    Main entry point for the SVG to PNG conversion script.

    Parses command-line arguments and performs the conversion with a fixed size of 48x48 pixels.
    Exits with code 0 on success, 1 on failure.
    """
    if len(sys.argv) != 3:
        print("Usage: convert_svg_to_png.py <svg_path> <png_path>", file=sys.stderr)
        sys.exit(1)

    svg_path = sys.argv[1]
    png_path = sys.argv[2]
    size = 48
    if convert_svg_to_png(svg_path, png_path, size):
        print(f"✓ Successfully created: {png_path}")
        sys.exit(0)
    else:
        print(f"✗ Conversion failed", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
