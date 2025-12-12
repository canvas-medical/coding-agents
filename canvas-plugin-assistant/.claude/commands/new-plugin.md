# New Plugin

Start the plugin brainstorming process to transform requirements into a concrete specification, then implement it.

## Instructions

Use the **plugin-brainstorm** agent for the full workflow from spec to deployment.

### Phase 0: Create Git Branch

**Before anything else, create a new branch for this plugin work.**

Generate a branch name using three random words in kebab-case. Examples:
- `mercury-purring-lion`
- `crystal-dancing-falcon`
- `amber-swift-turtle`

```bash
git checkout -b {branch_name}
git push -u origin {branch_name}
```

Tell the user the branch name you created.

### Phase 1: Gather Requirements

1. Invoke the canvas-sdk skill to have SDK documentation available
2. Ask the user to describe the problem they're trying to solve
3. Use AskUserQuestion to gather structured requirements:
   - Who experiences the problem?
   - What should trigger the plugin?
   - What should the plugin create or do?
4. Map answers to Canvas SDK concepts (events, effects)
5. Write a `../.cpa-workflow-artifacts/plugin-spec.md` file with the specification
6. Wait for user approval before any implementation

If a `../.cpa-workflow-artifacts/plugin-spec.md` already exists, ask if they want to:
- Start fresh (replace it)
- Continue refining the existing spec

### Phase 2: Implement (after user approves spec)

**⚠️ CRITICAL: After the user approves the spec, you MUST run `canvas init` as the very first step:**

```bash
echo "{plugin_name}" | uv run canvas init
cd {plugin_name}
```

**Do NOT create files or directories manually.** The `canvas init` command creates the correct project structure. Only edit the files it generates.

After `canvas init` completes:

1. **Verify project structure:**

   The expected structure is:
   ```
   {plugin_name}/                    # Container: kebab-case (you are here)
   ├── pyproject.toml
   ├── tests/
   │   └── ...
   └── {plugin_name_snake}/          # Inner: snake_case version
       ├── CANVAS_MANIFEST.json
       ├── README.md
       └── protocols/
   ```

   Run these verification checks:

   ```bash
   # Convert plugin name to inner folder name (kebab to snake)
   INNER=$(echo "{plugin_name}" | tr '-' '_')

   # Verify structure
   echo "Verifying project structure..."

   # Inner folder should exist
   test -d "$INNER" && echo "OK: Inner folder '$INNER' exists" || echo "ERROR: Inner folder '$INNER' not found"

   # CANVAS_MANIFEST.json should be INSIDE inner folder
   test -f "$INNER/CANVAS_MANIFEST.json" && echo "OK: CANVAS_MANIFEST.json in correct location" || echo "ERROR: CANVAS_MANIFEST.json not in $INNER/"

   # tests/ should be at container level
   test -d "tests" && echo "OK: tests/ at container level" || echo "ERROR: tests/ not found"

   # pyproject.toml should be at container level
   test -f "pyproject.toml" && echo "OK: pyproject.toml present" || echo "ERROR: pyproject.toml missing"
   ```

   **If any checks fail:** Report errors to the user and investigate before proceeding. Do NOT continue with implementation until structure is correct.

2. **Ensure `.gitignore` includes `.claude`** (to keep Claude Code local settings out of the repo):
   - Check if `.gitignore` exists in the plugin directory
   - If it exists, check if it already contains `.claude`
   - If not, append `.claude` to the file
   - If `.gitignore` doesn't exist, create it with `.claude` as the first entry

3. **Replace `pyproject.toml` with the minimal version:**

   The `canvas init` scaffold may include unnecessary configuration. Replace it with this minimal file:

   ```toml
   # This pyproject.toml is only used for local development and testing.
   # The Canvas plugin has its own packaging process that doesn't use this file.

   [project]
   name = "{plugin_name}"
   version = "0.0.0"
   requires-python = ">=3.12"
   dependencies = [
       "django>=4.2.0",
   ]

   [dependency-groups]
   dev = [
       "mypy>=1.19.0",
       "pytest>=8.0.0",
       "pytest-cov>=4.1.0",
       "pytest-django>=4.7.0",
       "pytest-mock>=3.12.0",
   ]

   [tool.coverage.run]
   omit = ["tests/*"]
   ```

   Add runtime dependencies (arrow, httpx, etc.) to `dependencies` only as needed during implementation.

   Add to the root project, the `mypy.ini` file:
   ```ini
   [mypy]
   explicit_package_bases = True
   
   check_untyped_defs = True
   disallow_incomplete_defs = True
   disallow_untyped_calls = True
   disallow_untyped_decorators = False
   disallow_untyped_defs = True
   error_summary = True
   
   show_error_context = True
   strict_equality = True
   strict_optional = True
   
   warn_no_return = True
   warn_redundant_casts = True
   warn_return_any = True
   warn_unreachable = True
   warn_unused_configs = True
   warn_unused_ignores = True
   
   follow_imports = silent
   ignore_missing_imports = True
   no_implicit_optional = True
   pretty = False
   
   python_version = 3.12
   exclude = debug
   ```


4. **Commit the scaffolded plugin:**
   ```bash
   git add -A .
   git commit -m "initialize {plugin_name} plugin scaffold"
   git push
   ```

   **CRITICAL:** Always use `git add -A .` (with the trailing `.`) to scope changes to the current directory only. Never use `git add --all` or `git add -A` without a path.

Then continue with the plugin-brainstorm agent workflow:
- Edit the generated protocol handler
- **CRITICAL: Invoke the testing skill before writing tests**
  - Use: `Skill(skill="testing")` to load testing guidelines
  - Follow patterns from testing_context.txt for mock verification
  - Always verify mock calls using `mock.mock_calls`, not assertion methods
- Write tests following the testing skill guidelines
- Deploy for UAT

## Git Commit Style

Use concise declarative voice for all commit messages:
- "add handler for vitals monitoring"
- "implement authentication for webhook endpoint"
- "fix threshold comparison logic"
- "update tests for edge cases"

Do NOT use: "Added...", "Adding...", "I added...", or similar.

## CPA Workflow

This command is **step 2** in the Canvas Plugin Assistant workflow:

```
/check-setup      →  Verify environment tools (uv, unbuffer)
/new-plugin       →  Create plugin from requirements  ← YOU ARE HERE
/deploy           →  Deploy to Canvas instance for UAT
/coverage         →  Check test coverage (aim for 90%)
/security-review-cpa  →  Comprehensive security audit
/wrap-up          →  Final checklist before delivery
```

After implementation, guide the user to `/deploy` for UAT testing.
