# /// script
# dependencies = ["cairosvg"]
# requires-python = ">=3.8"
# ///

import sys
import cairosvg

def convert_svg_to_png(svg_path, png_path, size):
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

def main():
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
