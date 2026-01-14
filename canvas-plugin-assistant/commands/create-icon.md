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
   - If no description is provided, ask the user what kind of icon they want
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
   - Limit to a reasonable length (e.g., "patient-vitals-monitor")
   - Add `.svg` extension for an SVG file
   - Add `.png` extension for a PNG file

5. **Determine Save Location**:
   - Check if currently in a Canvas plugin directory (look for CANVAS_MANIFEST.json)
   - If in plugin directory: save to the inner plugin folder's `assets/` directory (snake_case folder name)
   - If not in the plugin directory: save to the current working directory
   - Report the save location to the user

6. **Create Assets Directory (if needed)**:
   - If saving to a Canvas plugin directory, ensure the `assets/` directory exists
   - Use: `mkdir -p {plugin_name_snake}/assets`
   - Skip this step if not in a plugin directory

7. **Save SVG File**:
   - Use Write tool to save the SVG content
   - Save with the generated filename
   - For plugins: `{plugin_name_snake}/assets/icon-name.svg`
   - For non-plugins: `icon-name.svg`

8. **Check UV Installation**:
   - Use Bash to check if `uv` is installed: `which uv`
   - If not installed, install it automatically:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - After installation, may need to use the full path: `~/.cargo/bin/uv`

9. **Convert to PNG**:
   - Use Bash to execute the conversion command:
     ```bash
     uv run --with cairosvg python ${CLAUDE_PLUGIN_ROOT}/scripts/convert_svg_to_png.py <svg-file> <png-file>
     ```
   - Replace `<svg-file>` with the generated SVG filename (include the path if not in current directory)
   - Replace `<png-file>` with the same base name but `.png` extension
   - The script will create a 48x48 pixel PNG

10. **Update CANVAS_MANIFEST.json (if applicable)**:
    - If in a Canvas plugin directory, ask the user if they want to update the manifest
    - If yes, update the applications entry's `icon` field with the relative path
    - Example: `"icon": "assets/icon-name.png"`

11. **Handle Conversion Results**:
    - **On Success**: Report both file paths to the user
    - **On Failure**:
      - Inform user that PNG conversion failed
      - Confirm SVG file was still saved successfully
      - Provide the SVG file path for manual conversion if needed

12. **Report Completion**:
    - Show paths to both generated files
    - Confirm where they were saved
    - If manifest was updated, mention that as well

## Error Handling

- **UV Installation Fails**: Provide a clear error message and manual installation instructions
- **SVG Generation Issues**: Ensure valid SVG syntax before writing a file
- **File Write Errors**: Check permissions and report clear error messages
- **Conversion Script Errors**: Keep the SVG file and report the error from the conversion script
- **Manifest Update Errors**: Ensure the manifest exists and is valid JSON

## Output Format

After a successful generation, display:
```
Icon created successfully:
  SVG: /path/to/icon-name.svg
  PNG: /path/to/icon-name.png (48x48)
```

If in a plugin directory and manifest was updated:
```
Icon created successfully:
  SVG: /path/to/plugin_name/assets/icon-name.svg
  PNG: /path/to/plugin_name/assets/icon-name.png (48x48)

CANVAS_MANIFEST.json updated with icon reference: "assets/icon-name.png"
```

## Important Notes

- Always save both SVG and PNG files (do not delete the SVG)
- Use ${CLAUDE_PLUGIN_ROOT} environment variable for script path portability
- The conversion script uses cairosvg via uv for dependency isolation
- Filenames are auto-generated from the description (kebab-case)
- For Canvas plugins, icons must be in the inner plugin directory's `assets/` folder (e.g., `{plugin_name_snake}/assets/`)
- Create the `assets/` directory if it doesn't exist before saving icons
- Both files save to the appropriate directory based on context
- Do not show SVG code to the user unless there's an error, or they request it
- Canvas Medical plugin icons should be professional and healthcare-appropriate

## Examples

Example 1 - Basic usage:
```
User: /cpa:create-icon "medical chart with checkmark"