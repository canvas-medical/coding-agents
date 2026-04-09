---
name: create-icon
---

# Create Icon

Generate a branded app icon (black rounded square with white symbol) and convert it to a 128x128 PNG.

## Instructions

When this command is invoked, generate an icon following the icon-generation skill and save the PNG to a location chosen by the user.

### Workflow

Follow these steps in order:

1. **Load Icon Generation Skill**:
   - First, invoke the icon-generation skill to have all icon generation patterns and best practices available
   - Use: `Skill(skill="icon-generation")`

2. **Infer Icon Subject**:
   - Infer an appropriate icon from context — plugin name, purpose, surrounding code
   - Do not ask the user what to draw; figure it out from context
   - If there is truly no context available, then ask

3. **Generate SVG Icon**:
   - Search Lucide for a matching icon by fetching from `https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{name}.svg`
   - If no Lucide match, try Tabler at `https://raw.githubusercontent.com/tabler/tabler-icons/main/icons/outline/{name}.svg`
   - Extract inner elements, strip styling attributes, and wrap in the 128x128 template (see skill for details)
   - If no library match, hand-draw in the 24x24 coordinate space using the `<g transform>` wrapper
   - Run the quality checklist: thumbnail test, element count, optical centering, stroke consistency

4. **Generate Filename**:
   - Convert the icon subject to kebab-case (lowercase with hyphens)
   - Remove special characters and extra spaces
   - Limit to a reasonable length (e.g., "patient-vitals-monitor")
   - Add `.png` extension for the output file

5. **Ask Where to Save**:
   - Ask the user where they want the PNG saved
   - Suggest a default based on context (e.g., `{plugin_name_snake}/assets/` if in a plugin directory, or current directory otherwise)
   - Use the user's chosen location for the output path

6. **Write SVG to `/tmp`**:
   - Use Write tool to save the SVG content to `/tmp/icon-name.svg`
   - This is a temporary intermediate file

7. **Convert to PNG**:
   - Use Bash to execute the conversion command:
     ```bash
     uv run --with cairosvg python -c "import cairosvg; cairosvg.svg2png(url='/tmp/icon-name.svg', write_to='<user-chosen-path>/icon-name.png', output_width=128, output_height=128)"
     ```
   - This creates a 128x128 pixel PNG at the user's chosen location

8. **Delete Temporary SVG**:
   - Remove the temporary file: `rm /tmp/icon-name.svg`
   - Only delete after successful conversion

9. **Report Completion**:
    - Show the path to the generated PNG file
    - Confirm where it was saved

## Error Handling

- **Conversion Failure**: Keep the SVG in `/tmp` so the user can convert it manually
- **SVG Generation Issues**: Ensure valid SVG syntax before writing file
- **File Write Errors**: Check permissions and report clear error messages

## Output Format

After successful generation, display:
```
Icon created successfully:
  PNG: /path/to/icon-name.png (128x128)
```

## Important Notes

- SVG files are temporary — written to `/tmp` and deleted after conversion
- Only the PNG is kept as the final output
- Filenames are auto-generated from the inferred icon subject (kebab-case)
- Do not show SVG code to the user unless there's an error or they request it
- This command does NOT auto-update CANVAS_MANIFEST.json — that's for automated flows only
