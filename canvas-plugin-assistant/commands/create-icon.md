# Create Icon

Generate an SVG icon from a description and automatically convert it to 48x48 PNG format.

## Instructions

When this command is invoked, generate an SVG icon based on the user's description and automatically convert it to a 48x48 PNG format suitable for Canvas Medical plugins.

### Workflow

Follow these steps in order:

1. **Load Icon Generation Skill**:
   - First, invoke the icon-generation skill to have all icon generation patterns and best practices available
   - Use: `Skill(skill="icon-generation")`

2. **Parse Description**:
   - Extract the icon description from the command argument
   - If no description provided, ask the user what kind of icon they want
   - Consider the context (e.g., if working in a plugin directory, tailor suggestions)

3. **Generate SVG Icon**:
   - Create a clean, professional SVG icon based on the description
   - Follow the patterns from the icon-generation skill
   - For Canvas Medical contexts, use professional healthcare-appropriate designs
   - Use appropriate colors, shapes, and design elements
   - Ensure the SVG is well-formed with proper viewBox and dimensions (e.g., viewBox="0 0 100 100")
   - Keep the design simple and clear at small sizes (will be rendered at 48x48)

4. **Generate Filename**:
   - Convert the description to kebab-case (lowercase with hyphens)
   - Remove special characters and extra spaces
   - Limit to reasonable length (e.g., "patient-vitals-monitor")
   - Add `.svg` extension for SVG file
   - Add `.png` extension for PNG file

5. **Determine Save Location**:
   - Check if currently in a Canvas plugin directory (look for CANVAS_MANIFEST.json)
   - If in plugin directory: save to the inner plugin folder (snake_case folder name)
   - If not in plugin directory: save to current working directory
   - Report the save location to the user

6. **Save SVG File**:
   - Use Write tool to save the SVG content
   - Save with the generated filename
   - Example: `icon-name.svg`

7. **Check UV Installation**:
   - Use Bash to check if `uv` is installed: `which uv`
   - If not installed, install it automatically:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - After installation, may need to use full path: `~/.cargo/bin/uv`

8. **Convert to PNG**:
   - Use Bash to execute the conversion command:
     ```bash
     uv run --with cairosvg python ${CLAUDE_PLUGIN_ROOT}/scripts/convert-svg-to-png.py <svg-file> <png-file>
     ```
   - Replace `<svg-file>` with the generated SVG filename (include path if not in current directory)
   - Replace `<png-file>` with the same base name but `.png` extension
   - The script will create a 48x48 pixel PNG

9. **Update CANVAS_MANIFEST.json (if applicable)**:
   - If in a Canvas plugin directory, ask the user if they want to update the manifest
   - If yes, update the `icon` field with just the filename (not full path)
   - Example: `"icon": "icon-name.png"`

10. **Handle Conversion Results**:
    - **On Success**: Report both file paths to the user
    - **On Failure**:
      - Inform user that PNG conversion failed
      - Confirm SVG file was still saved successfully
      - Provide the SVG file path for manual conversion if needed

11. **Report Completion**:
    - Show paths to both generated files
    - Confirm where they were saved
    - If manifest was updated, mention that as well

## Error Handling

- **UV Installation Fails**: Provide clear error message and manual installation instructions
- **SVG Generation Issues**: Ensure valid SVG syntax before writing file
- **File Write Errors**: Check permissions and report clear error messages
- **Conversion Script Errors**: Keep SVG file and report the error from the conversion script
- **Manifest Update Errors**: Ensure the manifest exists and is valid JSON

## Output Format

After successful generation, display:
```
Icon created successfully:
  SVG: /path/to/icon-name.svg
  PNG: /path/to/icon-name.png (48x48)
```

If in a plugin directory and manifest was updated:
```
Icon created successfully:
  SVG: /path/to/plugin_name/icon-name.svg
  PNG: /path/to/plugin_name/icon-name.png (48x48)

CANVAS_MANIFEST.json updated with icon reference
```

## Important Notes

- Always save both SVG and PNG files (do not delete the SVG)
- Use ${CLAUDE_PLUGIN_ROOT} environment variable for script path portability
- The conversion script uses cairosvg via uv for dependency isolation
- Filenames are auto-generated from the description (kebab-case)
- For Canvas plugins, icons must be in the inner plugin directory (snake_case folder)
- Both files save to the appropriate directory based on context
- Do not show SVG code to user unless there's an error or they request it
- Canvas Medical plugin icons should be professional and healthcare-appropriate

## Examples

Example 1 - Basic usage:
```
User: /create-icon "medical chart with checkmark"