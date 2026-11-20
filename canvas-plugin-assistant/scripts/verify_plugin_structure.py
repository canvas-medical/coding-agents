"""Verify Canvas plugin project structure after canvas init."""

import json
import sys
from pathlib import Path


def verify_structure() -> bool:
    """
    Verify the Canvas plugin project structure from the container folder.

    Expected structure:
        {plugin_name}/                    # Container: kebab-case
        ├── pyproject.toml
        ├── tests/
        └── {package}/                    # Inner package: <prefix>__<name>
            ├── CANVAS_MANIFEST.json
            └── ...

    Returns:
        True if structure is valid (no errors), False otherwise.
        Warnings do not cause failure.
    """
    errors = 0
    warnings = 0

    print("Checking project structure...")
    print()

    # Check 1: exactly one package folder holds CANVAS_MANIFEST.json
    manifests = sorted(Path(".").glob("*/CANVAS_MANIFEST.json"))
    manifest_container = Path("CANVAS_MANIFEST.json")
    inner_path: Path | None = None

    if len(manifests) == 1:
        inner_path = manifests[0].parent
        print(f"OK: Inner folder '{inner_path.name}' holds CANVAS_MANIFEST.json")
    elif manifests:
        names = ", ".join(manifest.parent.name for manifest in manifests)
        print(f"ERROR: More than one package folder holds a CANVAS_MANIFEST.json: {names}")
        errors += 1
    elif manifest_container.is_file():
        print("ERROR: CANVAS_MANIFEST.json at container level - should be inside the package folder")
        errors += 1
    else:
        print("ERROR: CANVAS_MANIFEST.json not found")
        errors += 1

    # Check 2: manifest name equals the package folder name
    if inner_path is not None:
        try:
            manifest_name = json.loads((inner_path / "CANVAS_MANIFEST.json").read_text()).get("name")
        except json.JSONDecodeError:
            print("ERROR: CANVAS_MANIFEST.json is not valid JSON")
            errors += 1
        else:
            if manifest_name != inner_path.name:
                print(f"ERROR: Manifest name '{manifest_name}' does not match the package folder '{inner_path.name}'")
                errors += 1

    # Check 3: tests/ at container level
    if Path("tests").is_dir():
        print("OK: tests/ at container level")
    elif inner_path is not None and (inner_path / "tests").is_dir():
        print("ERROR: tests/ inside inner folder - should be at container level")
        errors += 1
    else:
        print("WARNING: No tests/ directory found")
        warnings += 1

    # Check 4: pyproject.toml at container level
    if Path("pyproject.toml").is_file():
        print("OK: pyproject.toml at container level")
    else:
        print("WARNING: pyproject.toml not found")
        warnings += 1

    # Check 5: No duplicate CANVAS_MANIFEST.json
    if inner_path is not None and manifest_container.is_file():
        print("ERROR: CANVAS_MANIFEST.json in BOTH locations - remove container level copy")
        errors += 1

    print()
    if errors > 0:
        print(f"STRUCTURE VALIDATION FAILED: {errors} error(s)")
        if warnings > 0:
            print(f"Also found {warnings} warning(s)")
        return False
    if warnings > 0:
        print(f"Structure validation passed with {warnings} warning(s).")
    else:
        print("Structure validation passed.")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 1:
        print("Usage: verify_plugin_structure.py (run from the plugin container folder)", file=sys.stderr)
        sys.exit(1)

    sys.exit(0 if verify_structure() else 1)
