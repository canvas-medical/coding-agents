# UI Surface Selection

Use this decision sequence to determine which Canvas UI surface fits the plugin's purpose. The choice of surface shapes the entire UX, so get this right before designing any screens.

## Decision Sequence

1. Does this tool need a patient chart open? If no, use a left nav page. If yes, continue.
2. Does the user need to see the chart while using this tool? If yes, use a right chart pane. If no, continue.
3. Is this a quick interruption (under 30 seconds)? If yes, use a modal. If no, continue.
4. Is this tied to a specific note? If yes, use a note header button for actions or a note tab for reference data. If no, use a right chart pane.
5. Does this need to be reachable from any screen regardless of context? If yes, use the left nav. If only sometimes, use the bento grid.

## Left Nav Page (`provider_menu_item` + `TargetType.PAGE`)

A standalone workspace. The user navigates away from their current context to use it. Best for tools that span multiple patients or don't need a patient chart open at all. Population health dashboards, reporting, admin configuration, bulk operations. The tradeoff is that you're pulling the clinician out of their current workflow, so the tool needs to justify that context switch. If the user would constantly need to flip back to a patient chart, it doesn't belong here.

**Patient context.** If a left nav page displays patient-specific data, it must include a patient context header (name plus DOB or MRN) near the top. There is no chart visible to provide identity context. See the Patient Context Header pattern in [web-components.md](web-components.md).

## Bento Grid (`global` scope)

Two clicks to reach (open grid, click app). Low discoverability. Best for utilities that any user might occasionally need but that aren't part of a daily clinical workflow. Reference lookups, settings pages, one-time configuration wizards. Don't put anything here that the user needs fast access to during a patient encounter because they won't find it in time.

## Right Chart Pane (`patient_specific` or launched via ActionButton with `RIGHT_CHART_PANE_LARGE`)

The clinical workhorse. The patient chart stays visible on the left while the plugin occupies the right panel. The user can glance between the chart and the plugin, copy data mentally or literally, and keep their clinical context intact. Best for tools that augment the chart view: visit summaries, care gap checklists, risk scores, medication reviews, prior auth status. If the requirement says "the clinician needs this information while documenting" or "while reviewing the chart," this is almost always the right surface. The constraint is width, so design for a narrow vertical layout.

**Mandatory bottom clearance.** The Canvas platform renders a Pylon Chat widget at the bottom-right of the viewport. It overlaps the right chart pane and will cover buttons, form actions, or any other content near the bottom of the plugin. Every right chart pane plugin must have `padding-bottom: 120px` on its outermost scrollable container. This applies whether the plugin content fits in the viewport or scrolls. Without this padding the chat bubble will obscure interactive elements and the user cannot reach them.

## Modal (`LaunchModalEffect`)

Blocks the chart. That's the defining characteristic. Use it when you need the user's undivided attention for a short moment. Confirmations ("delete this?"), quick data entry that shouldn't be interrupted ("enter override reason"), and alerts that require acknowledgment ("this patient has an active flag"). If the interaction takes more than 20 to 30 seconds, the user will resent the modal because they can't see anything behind it. Never use a modal for browsing, searching, or any workflow where the user might need to reference the chart.

**Patient context.** Modals that display patient-specific data must include a patient context header (name plus DOB or MRN) near the top. The chart is hidden behind the modal so the user has no other way to verify which patient they are looking at. See the Patient Context Header pattern in [web-components.md](web-components.md).

## Note Header ActionButton

Appears on a specific note. The user is actively working in that note and the action relates to what they're documenting right now. Best for contextual actions that operate on the note's content: generate a summary, insert a template, run a coding suggestion, copy structured data into the note. The click should either do something immediately (originate a command) or open a right pane or modal for a quick follow-up. If the action doesn't relate to the note the user is looking at, it shouldn't be a note header button.

## Note Footer

Lower visual priority than the header. The user sees it after they've finished writing, not while they're actively composing. Best for metadata, status indicators, timestamps, and read-only context. Interactive controls in the footer feel awkward because the user's attention has already moved past the note body.

## Note Tab

Supplementary information that lives alongside the note but doesn't need to be visible during active documentation. Reference data, historical context, related orders, coding detail breakdowns. The user switches to the tab when they want to dig deeper, but the default note view stays clean. Good for "I might need this" rather than "I definitely need this right now."
