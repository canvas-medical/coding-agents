# Patterns

Copy-paste templates that span multiple components or cover content shapes that do not have a dedicated component yet. Use these verbatim when the context matches. Decision rules for which type to pick live in `component-usage.md`. Visual tokens referenced here live in `DESIGN.md`.

## Empty State

Empty state is typed by cause. Four markup variants cover the full taxonomy. The decision rules that pick which one to use live in `component-usage.md` Empty States.

Placement. Center vertically and horizontally inside short containers (card bodies, sidebar panels under 400 pixels tall). Top align with `--space-huge` padding inside tall containers (full page regions, modal bodies) so the block sits where the eye lands rather than floating in the middle.

### First use

User has never added data here.

```html
<div style="padding: var(--space-huge); text-align: center">
  <h3 style="margin: 0 0 var(--space-small); font-weight: 700">No medications recorded</h3>
  <p style="margin: 0 0 var(--space-medium); color: var(--color-text-muted, #767676)">Track this patient's active medications here.</p>
  <canvas-button>Add first medication</canvas-button>
</div>
```

### User cleared

Data existed, the user removed it all.

```html
<div style="padding: var(--space-huge); text-align: center">
  <h3 style="margin: 0 0 var(--space-small); font-weight: 700">Medication list cleared</h3>
  <p style="margin: 0 0 var(--space-medium); color: var(--color-text-muted, #767676)">All medications were removed. Add a new entry or restore the previous list.</p>
  <canvas-button style="margin-right: var(--space-small)">Add medication</canvas-button>
  <canvas-button variant="ghost">Restore previous</canvas-button>
</div>
```

### Filter no results

Underlying data exists, the current filter excludes everything. Render inside the same container that holds the filtered list or table.

```html
<div style="padding: var(--space-huge); text-align: center">
  <h3 style="margin: 0 0 var(--space-small); font-weight: 700">No results match your filters</h3>
  <p style="margin: 0 0 var(--space-medium); color: var(--color-text-muted, #767676)">Try widening the date range or removing a tag.</p>
  <canvas-button variant="ghost">Clear filters</canvas-button>
</div>
```

### Load error

Fetch failed. Do not reuse the centered empty pattern. Use `canvas-banner` so the user can tell a failed load from a true empty.

```html
<canvas-banner variant="error">
  <span slot="title">Could not load medications</span>
  <span slot="description">Check your connection and try again.</span>
  <canvas-button slot="action" variant="ghost">Retry</canvas-button>
</canvas-banner>
```

## Loading, Empty, Error State Machine

Every data region renders in one of four states. Pick the right one.

- **Loading.** Fetch in flight. Render `canvas-loader`. Do not render the empty pattern during this window, an empty state that flashes before rows arrive reads as broken.
- **Populated.** Fetch resolved with one or more rows. Render the list or table.
- **Empty.** Fetch resolved with zero rows. Render the typed empty state from the four above.
- **Error.** Fetch failed. Render a `canvas-banner variant="error"`, not the centered empty pattern.

Gate the empty pattern behind fetch resolution. Mount it only after rows is known to be zero, never alongside the loader. A surface that swaps directly from empty to populated without a loading state reads as flicker.

## Patient Context Header

Use in modals or standalone pages where the patient chart is not visible. See `surface-selection.md` for which surfaces require this header.

```html
<div style="display: flex; align-items: center; gap: var(--space-small);
  padding-bottom: var(--space-small); border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-medium)">
  <span style="font-weight: 700">Jane Smith</span>
  <span style="color: var(--color-text-muted, #767676); font-size: .92857143em">DOB: Mar 15, 1985</span>
  <span style="color: var(--color-text-muted, #767676); font-size: .92857143em">MRN: 12345</span>
</div>
```

## Filter Bar

A horizontal row of form elements above a table. Wrap in `canvas-card` plus `canvas-card-body` plus `canvas-inline-row`. Use `canvas-input type="date"` for date range fields. Decision rules for this pattern live in `component-usage.md` Inline Form Rows.

```html
<canvas-card>
  <canvas-card-body>
    <canvas-inline-row>
      <canvas-input label="From" type="date"></canvas-input>
      <canvas-input label="To" type="date"></canvas-input>
      <canvas-dropdown label="Provider">
        <canvas-option value="" selected>All Providers</canvas-option>
        <canvas-option value="1">Dr. Alvarez</canvas-option>
      </canvas-dropdown>
      <canvas-button>Load Appointments</canvas-button>
    </canvas-inline-row>
  </canvas-card-body>
</canvas-card>
```

For a filter bar above a table with bulk actions, add a second `canvas-card-body no-padding` for the table and a `canvas-card-footer` for the selection count on the left and action buttons on the right. See the Filter Bar (with table and action footer) card in `examples/showcase.html` under the Form section.

## Sortable List Minimum Height

Empty receiving lists need a minimum drop target so the user can still drop onto an empty column.

- Token. `--canvas-sortable-min-height`. Default `calc(var(--space-medium) * 2)`.
- Applied via `:host`. Ensures an empty column still catches a drop.
