# Check Setup

Verify the development environment has all required tools before starting plugin development.

## Instructions

Run these checks in sequence:

### 1. Check for `uv`

```bash
which uv
```

- **If found**: Report "uv is installed" and continue
- **If not found**: Report the issue and provide installation command:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
  Then ask user to run the command and re-run `/check-setup` after.

### 2. Check for `unbuffer`

```bash
which unbuffer
```

- **If found**: Report "unbuffer is installed" and continue
- **If not found**: Report the issue and provide installation command:
  ```bash
  brew install expect
  ```
  (unbuffer is part of the expect package)
  Then ask user to run the command and re-run `/check-setup` after.

### 3. Check for Canvas CLI

```bash
uv run canvas --version
```

- **If works**: Report Canvas CLI version
- **If fails**: Note that Canvas CLI will be installed when creating a plugin (it's a dependency)

### 4. Report Results

If all checks pass, report:

```
Environment ready!

  uv: installed
  unbuffer: installed
  canvas CLI: [version or "will be installed with plugin"]

You're ready to start building Canvas plugins.

Next step: Run /new-plugin to create your first plugin.
```

If any checks fail, summarize what needs to be installed before proceeding.

## CPA Workflow

This command is the **first step** in the Canvas Plugin Assistant workflow:

```
/check-setup      →  Verify environment tools  ← YOU ARE HERE
/new-plugin       →  Create plugin from requirements
/deploy           →  Deploy to Canvas instance for UAT
/coverage         →  Check test coverage (aim for 90%)
/security-review      →  Comprehensive security audit
/wrap-up          →  Final checklist before delivery
```

Always guide users through this flow sequentially.
