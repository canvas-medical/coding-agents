#!/usr/bin/env bash
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPONENTS_DIR="$SKILL_DIR/assets/components"
TOKENS_FILE="$SKILL_DIR/assets/tokens.css"
TYPOGRAPHY_FILE="$SKILL_DIR/assets/typography.css"

CREATE=false

usage() {
    echo "Usage: $(basename "$0") [--create] <target-directory>"
    echo ""
    echo "Bundles all canvas web components into canvas-components.js"
    echo "and copies tokens.css and typography.css into the target directory."
    echo ""
    echo "Options:"
    echo "  --create  Create the target directory if it does not exist"
    echo ""
    echo "Example:"
    echo "  $(basename "$0") /path/to/plugin/static/"
    echo "  $(basename "$0") --create /path/to/new-plugin/static/"
    exit 1
}

while [ $# -gt 0 ]; do
    case "$1" in
        --create) CREATE=true; shift ;;
        -*) echo "Unknown option: $1"; usage ;;
        *) break ;;
    esac
done

if [ $# -ne 1 ]; then
    usage
fi

TARGET_DIR="$1"

if [ ! -d "$TARGET_DIR" ]; then
    if [ "$CREATE" = true ]; then
        mkdir -p "$TARGET_DIR"
        echo "Created target directory: $TARGET_DIR"
    else
        echo "Error: target directory does not exist: $TARGET_DIR"
        echo "  Use --create to create it automatically."
        exit 1
    fi
fi

if [ ! -d "$COMPONENTS_DIR" ]; then
    echo "Error: components directory not found: $COMPONENTS_DIR"
    exit 1
fi

if [ ! -f "$TOKENS_FILE" ]; then
    echo "Error: tokens.css not found: $TOKENS_FILE"
    exit 1
fi

if [ ! -f "$TYPOGRAPHY_FILE" ]; then
    echo "Error: typography.css not found: $TYPOGRAPHY_FILE"
    exit 1
fi

BUNDLE="$TARGET_DIR/canvas-components.js"
> "$BUNDLE"

count=0
for file in "$COMPONENTS_DIR"/canvas-*.js; do
    [ -f "$file" ] || continue
    if [ $count -gt 0 ]; then
        echo "" >> "$BUNDLE"
    fi
    cat "$file" >> "$BUNDLE"
    count=$((count + 1))
    echo "  + $(basename "$file")"
done

cp "$TOKENS_FILE" "$TARGET_DIR/tokens.css"
cp "$TYPOGRAPHY_FILE" "$TARGET_DIR/typography.css"

echo ""
echo "Bundled $count components into $BUNDLE"
echo "Copied tokens.css into $TARGET_DIR/tokens.css"
echo "Copied typography.css into $TARGET_DIR/typography.css"
