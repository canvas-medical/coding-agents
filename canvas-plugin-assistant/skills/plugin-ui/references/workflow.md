# UI Workflow

This file sequences the agent through the right reference files for each phase of UI work. A plugin can have multiple views (a chart pane, a modal, a settings page). Steps 2 through 5 run independently for each view.

## Routing Table

| Step | Task | Reference file | What the agent does |
|---|---|---|---|
| 0 | Verify setup | [setup.md](setup.md) | Check that `canvas-plugin-ui.js` and `canvas-plugin-ui.css` exist in the plugin's `static/` directory, the head loads the three tags (Google Fonts Lato, CSS, JS), SimpleAPI routes serve both assets through `StaffSessionAuthMixin`, and no global CSS reset is present. If anything is missing, stop and fix before any component work. |
| 1 | Inventory views | None | List every distinct screen the plugin has or needs. For each view, note what data it shows, what actions the user can take, and whether a patient chart must be open. If HTML exists, read the templates. If building from scratch, derive views from the requirements. This produces the view list that later steps iterate over. |
| 2 | Surface selection (per view) | [surface-selection.md](surface-selection.md) | For existing views, check whether the current surface fits. If a different surface is a better match, soft propose it with reasoning. Do not change without user approval. For new views, walk through the triggers, surfaces, and pairings sections and pick the combination. If two options are close, present both with tradeoffs and let the user pick. |
| 3 | Component selection (per view) | [component-usage.md](component-usage.md), [anti-patterns.md](anti-patterns.md) | For existing views, audit component choices against the rules. Flag raw HTML where a web component exists. Flag hard rule violations (toggle with submit, wrong button color). For new views, choose components based on the data and actions from step 1. Use web components for every available element, falling back to raw HTML only for patterns listed in [patterns.md](patterns.md). Scan for every anti-pattern in `anti-patterns.md`. |
| 4 | Build or refactor HTML (per view) | [web-components.md](web-components.md), [component-usage.md](component-usage.md), [DESIGN.md](../DESIGN.md), [patterns.md](patterns.md), [writing-style.md](writing-style.md) | Start from the Plugin HTML Boilerplate in `setup.md`. Build with `<canvas-*>` components. Use DESIGN.md for token selection when writing custom CSS. Use `patterns.md` for multi-component layouts (empty states, filter bar, patient context header). Apply writing-style.md rules to every user facing string. Cross-check every tag name and attribute against the documented API in `web-components.md`. If the existing HTML has JavaScript, complete the protocol in [refactor-safety.md](refactor-safety.md) before modifying any markup. |
| 5 | Clinical UX and interaction patterns (per view) | [interaction-patterns.md](interaction-patterns.md), [DESIGN.md](../DESIGN.md) | Verify touch targets meet 44 px minimum. Use DESIGN.md for visual hierarchy, information density, truncation rules, and date formatting. Confirmation hierarchy matches action severity. Patient identity visible on standalone pages and modals showing patient data. Keyboard navigation works. ARIA attributes present per interaction-patterns.md minimums. Focus management correct for modals and dynamic content. Right chart pane bottom clearance applied. |
| 6 | Validate | [validation-checklist.md](validation-checklist.md) | Run the six-phase validation protocol. Each phase must pass completely before the next begins. Reread the generated HTML as a string before starting. Fix violations within each phase and rerun until clean. Only present the result after all six phases produce zero violations. |

## Refactor Safety

When existing HTML contains `<script>` tags or inline event attributes, complete the four-part protocol in [refactor-safety.md](refactor-safety.md) before modifying any markup.

## Common Mistakes

Patterns agents have missed in past refactors or got wrong in new builds live in [anti-patterns.md](anti-patterns.md). Scan every entry during Step 3 and list any matches in the `refactor-safety.md` Part D risk summary so the user sees the full swap plan before work begins.
