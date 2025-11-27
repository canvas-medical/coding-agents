# Analyze Instance

Analyze a Canvas instance's configuration to understand the target environment.

## Instructions

Use the **instance-analyzer** agent to document the Canvas instance configuration.

1. Ask which Canvas instance to analyze (e.g., plugin-testing, customer dev instance)
2. Read credentials from `~/.canvas/credentials.ini`:
   - The instance section should contain `client_id`, `client_secret`, and `root_password`
   - If `root_password` is missing, tell the user to add it to their credentials file
3. Extract configuration from admin portal using the root_password:
   - Roles
   - Teams
   - Questionnaires
   - Note types
   - Appointment types
   - Installed plugins
4. Generate `instance-config-{hostname}.md` report
5. If `plugin-spec.md` exists, highlight configuration relevant to the planned plugin

## Credentials Setup

If the user hasn't configured credentials, instruct them:

> Add `root_password` to your `~/.canvas/credentials.ini` under the instance section:
> ```ini
> [plugin-testing]
> client_id=your_client_id
> client_secret=your_client_secret
> root_password=your_admin_password
> ```

## Arguments

If the user provides an instance name with the command (e.g., `/analyze-instance plugin-testing`), use that as the target instance.
