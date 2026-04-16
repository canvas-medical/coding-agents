# UI Surface Selection

Use this guide to determine which Canvas UI triggers and surfaces fit the plugin's purpose. Triggers are how the user reaches the plugin. Surfaces are what renders when they get there. These are independent choices. A single plugin can register multiple triggers that each open different surfaces. Pick a trigger from the Triggers section, pick a surface from the Surfaces section, then check the Pairings section to confirm they work well together.

## Triggers

Triggers are the entry points that launch a plugin UI. Each trigger is an Application with a scope or an ActionButton with a location, registered in CANVAS_MANIFEST.json. If the spec names a specific trigger, use it. If not, use this section to pick one.

A plugin can register multiple triggers. A common pattern is pairing a `global` or `provider_menu_item` trigger for admin and configuration with a `patient_specific` trigger or ActionButton for the clinical workflow.

### Bento Grid, No Patient Context (`global` scope Application)

The bento grid is the app launcher icon in the top right corner of the Canvas UI. A `global` scope app appears here regardless of whether a patient chart is open. Two clicks to reach (open grid, click app). Low discoverability. Best for utilities that any user might occasionally need but that are not part of a daily clinical workflow. Plugin configuration panels, admin tools, reference lookups, one-time setup wizards. Do not put anything here that the user needs fast access to during a patient encounter because they will not find it in time.

### Chart Header Icon Row (`patient_specific` scope Application with `show_in_panel: true`)

A row of icons in the patient chart header bar, visible whenever a patient chart is open. One click to reach, always visible. High discoverability. The platform passes the patient context to the plugin. Best for tools the clinician reaches frequently during a patient encounter. Care gap checklists, notification history, risk scores, medication reviews. The `panel_priority` field controls icon ordering (lower numbers appear first). The patient chart stays visible alongside whatever surface the plugin opens.

### Bento Grid, Inside Patient Chart (`patient_specific` scope Application without `show_in_panel`)

The bento grid app launcher, but the app only appears when a patient chart is open. Two clicks to reach (open grid, click app). Lower discoverability than the chart header icon row. Best for patient-specific tools the user needs occasionally but not during every encounter. The platform passes the patient context to the plugin. The patient chart stays visible alongside whatever surface the plugin opens.

### Left Sidebar Nav (`provider_menu_item` scope Application)

An entry in the left sidebar navigation, alongside Schedule, Patients, Revenue, and other core Canvas items. The sidebar is behind a hamburger menu in the top left corner and can be collapsed. One click to open the menu, one click to reach the app. Plugin entries appear below the core Canvas items and above the bottom utilities (Settings, Help center, etc.). The `menu_position` field controls placement ("top" for upper section, "bottom" for the lower section near Settings and Help). Best for tools that span multiple patients or do not need a patient chart open at all. Population health dashboards, reporting, admin configuration, bulk operations. The tradeoff is that clicking navigates away from the current context. If the user would constantly need to flip back to a patient chart, this trigger is the wrong choice.

### Patient Portal Nav (`portal_menu_item` scope Application)

A navigation entry in the patient portal left sidebar. Patients see this, not providers. Best for patient-facing tools like forms, educational content, or self-service features.

### Note Header ActionButton

A button that appears on a specific note header. The user is actively working in that note and the action relates to what they are documenting right now. Best for contextual actions that operate on the note content. Generate a summary, insert a template, run a coding suggestion, copy structured data into the note. The click should either do something immediately (originate a command) or open a surface for a follow-up interaction. If the action does not relate to the note the user is looking at, it should not be a note header button.

### Note Footer ActionButton

Lower visual priority than the header. The user sees it after they have finished writing, not while they are actively composing. Best for metadata, status indicators, timestamps, and read-only context. Interactive controls in the footer feel awkward because the user's attention has already moved past the note body.

### Chart Tab (`full_chart` scope Application)

A navigation tab in the patient chart header, displayed alongside the built-in Chart and Profile tabs. One click to reach when the patient chart is open. Best for tools that deserve equal standing with the chart and profile views, like a dedicated clinical workspace that replaces the default chart for specific workflows. The content renders as a full page within the patient chart context.

### Note Tab (NoteApplication)

A tab that appears alongside the note body. The user switches to the tab when they want to dig deeper, but the default note view stays clean. Best for supplementary information that lives alongside the note but does not need to be visible during active documentation. Reference data, historical context, related orders, coding detail breakdowns. Content renders inline using the `NOTE` surface. Good for "I might need this" rather than "I definitely need this right now."

## Surfaces

Surfaces are what renders when a trigger fires. The surface is set via `LaunchModalEffect` with a `TargetType` value. The SDK does not restrict which surface a trigger can open, but some combinations produce bad UX. See the Pairings section for guidance.

### Right Chart Pane (`RIGHT_CHART_PANE` or `RIGHT_CHART_PANE_LARGE`)

A panel on the right side of the viewport. `RIGHT_CHART_PANE_LARGE` is wider than `RIGHT_CHART_PANE`. When opened from a patient context, the patient chart stays visible on the left. The user can glance between the chart and the plugin, copy data mentally or literally, and keep their clinical context intact. When opened from a non-patient context (like a `global` scope trigger), no chart appears alongside it. Design for a narrow vertical layout in both variants.

**Mandatory bottom clearance (right chart pane only).** The Canvas platform renders a Pylon Chat widget as a floating bubble at the bottom-right of the viewport. It sits on top of plugin iframes and overlaps both `RIGHT_CHART_PANE` and `RIGHT_CHART_PANE_LARGE` because they occupy the right edge where the widget lives. Every right chart pane plugin must have `padding-bottom: 120px` on its outermost scrollable container. This applies whether the plugin content fits in the viewport or scrolls. Without this padding the chat bubble will obscure interactive elements and the user cannot reach them. This rule does not apply to full pages, modals, new windows, or inline note surfaces because they do not share the bottom-right viewport area with the widget.

### Full Page (`PAGE`)

A standalone full-width page. The user navigates away from their current context entirely. Best for tools that need maximum screen real estate and do not require simultaneous chart visibility. Dashboards, reports, configuration screens with complex layouts, bulk operations.

**Patient context.** If a full page displays patient-specific data, it must include a patient context header (name plus DOB or MRN) near the top. There is no chart visible to provide identity context. See the Patient Context Header pattern in [web-components.md](web-components.md).

### Modal (`DEFAULT_MODAL`)

A centered overlay that blocks everything behind it. Use it when you need the user's undivided attention for a short moment. Confirmations ("delete this?"), quick data entry that should not be interrupted ("enter override reason"), and alerts that require acknowledgment ("this patient has an active flag"). If the interaction takes more than 20 to 30 seconds, the user will resent the modal because they cannot see anything behind it. Never use a modal for browsing, searching, or any workflow where the user might need to reference the chart.

**Patient context.** Modals that display patient-specific data must include a patient context header (name plus DOB or MRN) near the top. The chart is hidden behind the modal so the user has no other way to verify which patient they are looking at. See the Patient Context Header pattern in [web-components.md](web-components.md).

### New Window (`NEW_WINDOW`)

Opens in a new browser tab. The user leaves the Canvas viewport entirely. Best for content that benefits from a separate window, like printable reports or reference material the user wants to keep open alongside Canvas.

### Inline Note (`NOTE`)

Content renders inside a note tab. Only used with NoteApplication handlers. The content lives within the note itself, not in a separate panel or overlay.

## Host Communication

Plugin iframes on the DEFAULT_MODAL or NOTE surface can send messages back to the Canvas host app through a MessageChannel. The host initiates the channel by posting an INIT_CHANNEL message with a MessagePort. The canvas-plugin-ui.js script handles this handshake automatically when loaded.

Two commands are available through CanvasUI.utils.

**CanvasUI.utils.dismissModal()** sends a CLOSE_MODAL message to the host, which dismisses the modal surface. Use this when the plugin needs to close itself after completing an action (saving data, confirming a choice, canceling).

**CanvasUI.utils.resizeModal(width, height)** sends a RESIZE message to the host with optional width and height values. Pass null for either dimension to leave it unchanged.

```js
// Close the modal after saving
CanvasUI.utils.dismissModal();

// Resize the modal to fit content
CanvasUI.utils.resizeModal(600, 400);

// Resize only the height
CanvasUI.utils.resizeModal(null, 300);
```

Include this communication bridge only for DEFAULT_MODAL and NOTE surfaces. It loads automatically with canvas-plugin-ui.js so no additional setup is needed. Plugins on RIGHT_CHART_PANE, RIGHT_CHART_PANE_LARGE, PAGE, or NEW_WINDOW surfaces do not use these commands.

## Pairings

The SDK does not enforce trigger-to-surface restrictions. Any trigger can technically open any surface. But some combinations produce good UX and others break the user's workflow. Use these recommendations.

### Standard Pairings

**Chart header icon row or bento grid (`patient_specific`) to right chart pane.** The most common clinical pattern. The clinician clicks the icon in the chart header (or opens the bento grid), and a panel slides in on the right while the patient chart stays visible. Use `RIGHT_CHART_PANE_LARGE` unless the content is simple enough for the narrower variant.

**Bento grid (`global`) to right chart pane.** Same right panel surface, but launched from the bento grid without a patient chart open. Works well for plugin configuration and admin tools. No chart is visible alongside, so do not design the content to reference patient data.

**Left sidebar nav (`provider_menu_item`) to full page.** The standard pattern for standalone workspaces. User clicks a nav item, gets a full page. Dashboards, reporting, admin panels with complex layouts. This is what users expect from sidebar navigation.

**Patient portal nav (`portal_menu_item`) to full page.** Same logic as provider menu. Patient-facing tools get a full page in the portal.

**Note header ActionButton to right chart pane.** The clinician clicks a button on the note they are working in. The right panel opens with the plugin while the note stays visible on the left. Use this when the clinician needs to reference the note while interacting with the plugin. Visit summaries, coding suggestions, template insertion previews.

**Note header ActionButton to modal.** Use when the interaction is short and focused. The note disappears behind the modal, so this only works for quick confirmations, single-field inputs, or alerts that take under 30 seconds.

**Chart tab (`full_chart`) to full page.** The chart tab navigates to a full page within the patient chart context. Use this for tools that need a dedicated workspace at the same level as Chart and Profile.

**Note tab (NoteApplication) to inline note.** Supplementary reference content lives in a tab within the note. No separate panel or overlay.

### Awkward Pairings (technically work, bad UX)

**Left sidebar nav to right chart pane.** The user navigates to the sidebar, but the content appears as a right panel with nothing meaningful on the left. Confusing layout.

**ActionButton to full page.** The user clicks a button on a note and gets yanked away from the note entirely. Breaks the contextual nature of action buttons.

**Bento grid (`global`) to right chart pane with chart-dependent content.** The panel opens but no chart is visible. If the plugin references patient data, the user has no way to verify which patient they are looking at. Only use this combination for non-patient content like settings or admin tools.

### Multi-Trigger Architecture

A plugin often needs more than one entry point. Common patterns follow.

**Admin plus clinical.** A `global` or `provider_menu_item` trigger opens a configuration page or panel. A `patient_specific` trigger or ActionButton opens the clinical view in a right chart pane. For example, custom-reminders uses `global` for campaign admin and `patient_specific` for the patient reminder view.

**Navigation plus note action.** A `provider_menu_item` trigger opens a full page for the main workflow. A note header ActionButton opens a right chart pane for quick note-level actions. For example, note-templates uses left nav for the template builder and an ActionButton for applying templates to notes.

**Clinical plus reference.** A `patient_specific` trigger opens the primary clinical tool in a right chart pane. A NoteApplication renders supplementary data inline in a note tab. For example, visit-summaries uses an ActionButton for summary generation and note tabs for previous visit and since-last-visit reference data.
