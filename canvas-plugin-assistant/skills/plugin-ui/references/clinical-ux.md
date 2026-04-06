# Clinical UX Guidelines

These rules are driven by the clinical environment. Clinicians work under time pressure, use tablets at the bedside, deal with long medical terminology, and make decisions where errors have real-world patient consequences.

## Accessibility and Touch Targets

- Minimum touch target size is `44px` by `44px` for all interactive elements (buttons, checkboxes, toggles, links, table row actions). Clinicians use tablets at the bedside and rolling cart touchscreens.
- Clickable areas can be visually smaller than 44px as long as the hit area (padding included) meets the minimum.
- All color pairings must meet WCAG AA contrast ratio (4.5:1 for normal text, 3:1 for large text). Green `#22BA45` on white and white on green both pass. Muted text `#767676` on white passes at 4.6:1.
- Never rely on color alone to convey meaning. Pair color with text, icons, or patterns. A red badge should also have a label like "Critical" or an icon.

## Information Density

- Distinguish between form views and data display views. Forms use the standard spacing scale (12px between fields, 16px section gaps). Data display views (medication lists, lab results, visit histories) can use tighter spacing (8px between rows, 12px section gaps) to show more information without scrolling.
- Clinicians want to see as much relevant information at a glance as possible. Do not add whitespace for aesthetics in data-dense screens. Every pixel of vertical space costs scrolling.
- In data display views, use the 14px font size for all content. Reserve 16px for headings only.

## Visual Hierarchy and Scanning

- Clinicians scan, they do not read. The most critical piece of information on any screen must be identifiable within one second.
- In a medication list, the drug name and dose are primary. The prescriber and date are secondary.
- In a lab result, the value and its abnormal/normal status are primary. The collection time and ordering provider are secondary.
- In a patient list, the patient name and chief concern are primary. The appointment time and status are secondary.
- Use font-weight `700` and dark text (`rgba(0,0,0,0.87)`) for primary information. Use regular weight and muted text (`#767676`) for secondary information. This creates a two-level hierarchy without needing different font sizes.

## Confirmation Hierarchy

Not all consequential actions are destructive. Clinical workflows include actions that are irreversible or have real-world impact without being "delete" operations. Use this hierarchy to decide when confirmation is needed.

- **No confirmation needed.** Saving a draft, toggling a UI preference, filtering a list, expanding or collapsing a section. These are low-risk and easily reversible.
- **Soft confirmation (undo banner).** Closing a care gap flag, dismissing an alert, marking a task complete. Show an inline banner with an undo option for 5 seconds. The action takes effect immediately but can be reversed.
- **Hard confirmation (dialog).** Sending a message to a patient, submitting a referral, signing a note, overriding a clinical alert. These leave the plugin's scope and affect external systems or the patient record. Show a confirmation dialog that names the specific action and its consequence.
- **Destructive confirmation (dialog with typed input).** Deleting patient-facing data, removing a medication, canceling an order. Show a confirmation dialog that requires the user to type "delete" or the item name before proceeding.

## Long Text and Truncation

Medical terminology produces long strings. Drug names, diagnosis descriptions, allergy lists, and procedure names regularly exceed available width.

- In tables and lists, truncate with ellipsis after one line. Show the full text in a tooltip on hover.
- In cards and detail views, wrap the full text. Do not truncate content the user came to read.
- In badges and pills, truncate with ellipsis and set a max-width. Keep the badge readable but compact.
- Never truncate patient names, medication doses, or allergy information in contexts where the truncated version could cause a clinical misidentification.

## Date and Time Display

- Use absolute dates for clinical documentation. "Mar 24, 2026" not "2 days ago." Relative dates create ambiguity in medical records.
- Include time when it matters clinically (medication administration, vital signs, lab draws). Format as "Mar 24, 2026 2:30 PM."
- For timestamps in non-clinical contexts like audit logs, last-edited indicators, and sync status, relative time is acceptable ("5 minutes ago", "yesterday").
- Never display dates in MM/DD/YYYY numeric format. Use the three-letter month abbreviation to avoid ambiguity.

## Keyboard Efficiency

- Forms must support tab navigation in logical order (top to bottom, left to right for paired fields).
- The submit button must be reachable by tabbing from the last field. Pressing Enter in a single-line input should submit the form if there is only one input and one submit action.
- Do not trap keyboard focus. If a modal or dropdown is open, Escape should close it and return focus to the element that opened it.

## Patient Context Safety

- When a plugin displays patient-specific data, the patient's identity must be visible on the screen. In a right chart pane, the chart on the left provides this context. In a modal or standalone page, the plugin must show the patient's name and at least one identifier (date of birth or MRN) near the top.
- Never display clinical data from one patient in a context where the user might believe they are looking at a different patient.
