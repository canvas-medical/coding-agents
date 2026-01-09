---
name: icon-generation
description: Generate SVG icons and convert them to 48x48 PNG format for Canvas plugins and applications
---

# Icon Generation Skill

This skill provides the capability to generate SVG icons from descriptions and automatically convert them to 48x48 PNG format, which is the standard size for Canvas Medical plugin icons.

## When to Use This Skill

This skill should be automatically invoked when:
- Creating a new Canvas plugin that requires an application icon
- The user explicitly requests an icon (e.g., "create an icon", "I need an icon", "generate an icon")
- Working on a plugin's `CANVAS_MANIFEST.json` and an `icon` field needs to be populated
- The user describes an icon they want (e.g., "I want a blue rocket ship icon")

## Icon Generation Workflow

Follow these steps to generate an icon:

### 1. Parse Description

Extract or generate a clear description of the icon. If working on a plugin:
- Use the plugin name and purpose to generate an appropriate icon description
- Consider the medical/healthcare context for Canvas plugins
- Keep descriptions clear and specific

Examples:
- "medical chart with checkmark"
- "stethoscope with blue accent"
- "vitals monitoring dashboard icon"
- "patient alert notification bell"

### 2. Generate SVG Icon

Create a clean, professional SVG icon based on the description:
- Use appropriate colors, shapes, and design elements
- Ensure the SVG is well-formed with proper viewBox and dimensions
- Target a square aspect ratio (e.g., viewBox="0 0 100 100")
- Keep the design simple and clear at small sizes (will be 48x48 PNG)
- For medical/healthcare icons, use professional, clean styling
- Avoid overly complex details that won't render well at 48x48

**SVG Best Practices:**
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <!-- Simple, clear shapes -->
  <!-- Appropriate colors -->
  <!-- Professional styling -->
</svg>
```

### 3. Generate Filename

Convert the description to kebab-case:
- Lowercase with hyphens
- Remove special characters and extra spaces
- Limit to reasonable length
- Examples:
  - "medical chart with checkmark" → `medical-chart-with-checkmark.svg`
  - "vitals monitoring icon" → `vitals-monitoring-icon.svg`

### 4. Save SVG File

Use the Write tool to save the SVG content:
- Save to current working directory with generated filename
- For Canvas plugins, save to the inner plugin directory's `assets/` folder (snake_case folder)
- Create the `assets/` directory if it doesn't exist: `mkdir -p {plugin_name_snake}/assets`
- Example: `{plugin_name_snake}/assets/medical-chart-icon.svg`

### 5. Check UV Installation

Before converting, verify `uv` is installed:

```bash
which uv
```

If not installed, install it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, you may need to use the full path: `~/.cargo/bin/uv`

### 6. Convert to PNG

Use the conversion script to create a 48x48 PNG:

```bash
uv run --with cairosvg python ${CLAUDE_PLUGIN_ROOT}/scripts/convert-svg-to-png.py <svg-file> <png-file>
```

Replace:
- `<svg-file>` with the generated SVG filename
- `<png-file>` with the same base name but `.png` extension

The script creates a 48x48 pixel PNG suitable for Canvas applications.

### 7. Update CANVAS_MANIFEST.json (if applicable)

If generating an icon for a Canvas plugin, update the manifest:

```json
{
  "name": "Plugin Name",
  "version": "1.0.0",
  "applications": [
    {
      "class": "plugin_name.applications.my_app:MyApp",
      "name": "My Application",
      "icon": "assets/icon-filename.png",
      ...
    }
  ]
}
```

The `icon` field should reference the path relative to the manifest location (e.g., `assets/icon-filename.png`).

### 8. Handle Results

**On Success:**
- Report both file paths to the user
- Confirm the icon is ready for use
- If for a plugin, confirm the manifest has been updated

**On Failure:**
- Inform user that PNG conversion failed
- Confirm SVG file was still saved successfully
- Provide the SVG file path for manual conversion if needed

## Output Format

After successful generation, display:
```
Icon created successfully:
  SVG: /path/to/assets/icon-name.svg
  PNG: /path/to/assets/icon-name.png (48x48)
```

For Canvas plugins, also mention:
```
CANVAS_MANIFEST.json updated with icon reference: "assets/icon-name.png"
```

## Important Notes

- Always save both SVG and PNG files (do not delete the SVG)
- Use ${CLAUDE_PLUGIN_ROOT} environment variable for script path portability
- The conversion script uses cairosvg via uv for dependency isolation
- Filenames are auto-generated from the description (kebab-case)
- For Canvas plugins, icons must be in the inner plugin directory's `assets/` folder (e.g., `{plugin_name_snake}/assets/`)
- Create the `assets/` directory if it doesn't exist before saving icons
- Do not show SVG code to user unless there's an error or they specifically request it
- Canvas Medical plugins should have professional, healthcare-appropriate icon designs

## Canvas Plugin Context

When generating icons for Canvas Medical plugins:
- Consider the healthcare/medical context
- Use professional, trustworthy design language
- Common themes: medical charts, stethoscopes, alerts, vitals, patient care
- Colors should be professional (blues, greens, neutrals are common)
- Avoid overly playful or casual designs
- The icon represents the plugin in the Canvas UI, so it should be immediately recognizable

## Error Handling

- **UV Installation Fails**: Provide clear error message and manual installation instructions
- **SVG Generation Issues**: Ensure valid SVG syntax before writing file
- **File Write Errors**: Check permissions and report clear error messages
- **Conversion Script Errors**: Keep SVG file and report the error from the conversion script
- **Manifest Update Errors**: Ensure the manifest file exists and is valid JSON

## Examples

### Example 1: New Plugin Icon
```
User is creating a "vitals-alert" plugin that monitors patient vital signs.

1. Generate description: "medical vitals monitor with alert icon"
2. Create SVG with heart rate line and alert symbol
3. Create assets directory: mkdir -p vitals_alert/assets
4. Save as: vitals_alert/assets/vitals-alert-icon.svg
5. Convert to: vitals_alert/assets/vitals-alert-icon.png
6. Update CANVAS_MANIFEST.json applications entry: "icon": "assets/vitals-alert-icon.png"
```

### Example 2: User Request
```
User says: "I need a blue database icon with a checkmark"

1. Use description: "blue database icon with checkmark"
2. Create SVG with database cylinder and green checkmark
3. Save as: blue-database-icon-with-checkmark.svg
4. Convert to: blue-database-icon-with-checkmark.png
5. Report both files created
```

### Example 3: Auto-detection During Plugin Creation
```
Assistant is running canvas init for a new plugin called "patient-scheduler"
After scaffold is created, CANVAS_MANIFEST.json needs an icon.

1. Generate description from plugin purpose: "calendar scheduling icon for patient appointments"
2. Create professional SVG with calendar and medical cross
3. Create assets directory: mkdir -p patient_scheduler/assets
4. Save as: patient_scheduler/assets/patient-scheduler-icon.svg
5. Convert to: patient_scheduler/assets/patient-scheduler-icon.png
6. Update manifest applications entry: "icon": "assets/patient-scheduler-icon.png"
7. Commit with other scaffold files
```
