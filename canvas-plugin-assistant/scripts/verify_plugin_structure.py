"""Verify Canvas plugin project structure after canvas init."""

import sys
from pathlib import Path


def kebab_to_snake(name: str) -> str:
    """Convert kebab-case to snake_case."""
    return name.replace("-", "_")


def verify_structure(plugin_name: str) -> bool:
    """
    Verify the Canvas plugin project structure.

    Expected structure:
        {plugin_name}/                    # Container: kebab-case
        ├── pyproject.toml
        ├── tests/
        └── {plugin_name_snake}/          # Inner: snake_case
            ├── CANVAS_MANIFEST.json
            └── ...

    Returns:
        True if structure is valid (no errors), False otherwise.
        Warnings do not cause failure.
    """
    inner_name = kebab_to_snake(plugin_name)
    errors = 0
    warnings = 0

    print("Checking project structure...")
    print(f"Container: {plugin_name}")
    print(f"Expected inner folder: {inner_name}")
    print()

    # Check 1: Inner folder exists
    inner_path = Path(inner_name)
    if inner_path.is_dir():
        print(f"OK: Inner folder '{inner_name}' exists")
    else:
        print(f"ERROR: Inner folder '{inner_name}' not found")
        errors += 1

    # Check 2: CANVAS_MANIFEST.json is inside inner folder
    manifest_inner = inner_path / "CANVAS_MANIFEST.json"
    manifest_container = Path("CANVAS_MANIFEST.json")

    if manifest_inner.is_file():
        print(f"OK: CANVAS_MANIFEST.json in correct location")
    elif manifest_container.is_file():
        print(f"ERROR: CANVAS_MANIFEST.json at container level - should be inside {inner_name}/")
        errors += 1
    else:
        print(f"ERROR: CANVAS_MANIFEST.json not found")
        errors += 1

    # Check 3: tests/ at container level
    tests_container = Path("tests")
    tests_inner = inner_path / "tests"

    if tests_container.is_dir():
        print(f"OK: tests/ at container level")
    elif tests_inner.is_dir():
        print(f"ERROR: tests/ inside inner folder - should be at container level")
        errors += 1
    else:
        print(f"WARNING: No tests/ directory found")
        warnings += 1

    # Check 4: pyproject.toml at container level
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.is_file():
        print(f"OK: pyproject.toml at container level")
    else:
        print(f"WARNING: pyproject.toml not found")
        warnings += 1

    # Check 5: No duplicate CANVAS_MANIFEST.json
    if manifest_container.is_file() and manifest_inner.is_file():
        print(f"ERROR: CANVAS_MANIFEST.json in BOTH locations - remove container level copy")
        errors += 1

    print()
    if errors > 0:
        print(f"STRUCTURE VALIDATION FAILED: {errors} error(s)")
        if warnings > 0:
            print(f"Also found {warnings} warning(s)")
        return False
    else:
        if warnings > 0:
            print(f"Structure validation passed with {warnings} warning(s).")
        else:
            print("Structure validation passed.")
        return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: verify_plugin_structure.py <plugin-name>", file=sys.stderr)
        sys.exit(1)

    plugin_name = sys.argv[1]
    success = verify_structure(plugin_name)
    sys.exit(0 if success else 1)
