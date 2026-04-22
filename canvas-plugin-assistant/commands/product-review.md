---
name: product-review
---

# Product Review

Evaluate a Canvas plugin from a product perspective: alignment with core tenets, regulatory risk (ONC-certified criteria overlap), and placement/norms. This is complementary to `/cpa:security-review` (engineering concerns) — this command surfaces product judgments a human needs to make.

The underlying tenets are also available as the `product-review` skill for inline application during plugin development (not only at review time). This command is the end-to-end workflow (environment validation, report generation, next-step routing); the skill is the rule set you apply while planning and writing code.

## Instructions

**Execution standard:** Run Python scripts and Python-based tooling with `uv run ...` (for scripts, `uv run python <script>.py ...`). Do not invoke bare `python` or `pip`.

### Step 1: Validate Environment

```bash
uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/validate_cpa_environment.py" --require-plugin-dir
```

**If the script exits with an error:** STOP and show the user the error message. Do NOT proceed.

**If validation passes:** Continue with the steps below.

```bash
cd "$CPA_PLUGIN_DIR"
INNER=$(basename "$PWD" | tr '-' '_')
```

Work through each tenet. For every finding, capture `file:line` references so the user can jump to the source. These are product judgments — flag and discuss, do NOT auto-fix.

---

### Step 2: Orient — read the manifest and README

Before evaluating any tenet, load the plugin's intent so the rest of the review is grounded.

```bash
cat "$INNER/CANVAS_MANIFEST.json"
cat "$INNER/README.md" 2>/dev/null
```

Note for later use:
- Declared `scope` for each component (e.g. `patient_specific`, `portal_menu_item`, `global`, `provider_menu_item`)
- Declared `components` (protocols, applications, commands, questionnaires, content, etc.)
- Declared `secrets`
- The plugin's stated purpose

---

### Step 3: Tenet 1 — Designated Record Set / Clinical Data Model

**Rule:** Custom data must not extend the record for concepts that belong in the Designated Record Set (DRS). Canvas's native models are the DRS; USCDI V3 is a subset of it. Customer data used to make decisions about a patient — clinical, billing, or administrative — must flow into Canvas's canonical models so it becomes part of the DRS and is available for exports, disclosures, amendments, and audits.

References:
- HIPAA DRS definition: https://www.accountablehq.com/post/designated-record-set-examples-under-hipaa-what-s-included-and-what-s-not
- USCDI V3: https://isp.healthit.gov/united-states-core-data-interoperability-uscdi

**The DRS test:** *"If the information is used to make a decision about the patient — clinical, billing, coverage, or care coordination — it belongs in the DRS."* If yes, it must flow into a Canvas native model. Custom data is for workflow mechanics, not decision-relevant content.

**Detect:**

```bash
grep -rn "CustomModel\|AttributeHub" --include="*.py" .
grep -rn "class .*(CustomModel)" --include="*.py" .
```

For each `CustomModel` / `AttributeHub` usage, inspect the fields and ask: **Is this concept part of the DRS?** Walk the tables below in order — USCDI first (the required subset), then broader DRS categories.

**USCDI V3 data classes (required subset of DRS) — flag if a CustomModel looks like one of these:**

| USCDI Data Class | Canvas equivalent — use this, NOT custom data |
|---|---|
| Patient demographics (name, DOB, sex, race, ethnicity, address, phone, preferred language, sexual orientation, gender identity) | `Patient` + contact/demographic fields |
| Problems / conditions | `Condition` (via Diagnose / Assess commands) |
| Medications | `Medication` + `MedicationStatement` (via Prescribe / Medication Statement commands) |
| Allergies and intolerances | `AllergyIntolerance` (via Allergy command) |
| Immunizations | `Immunization` (via Immunize command) |
| Vital signs | `Observation` (via Vitals command) |
| Laboratory | `Observation` / `DiagnosticReport` / `ServiceRequest` |
| Smoking status / social history | `Observation` (social history category) |
| Procedures | `Procedure` |
| Care team members | `CareTeam` |
| Goals | `Goal` (via Goal command) |
| Assessment and plan of treatment | `Assessment` / `Plan` command and `Note` |
| Encounters | `Note` / encounter record |
| Provenance | Canvas-managed, do not reimplement |
| Unique device identifier(s) for implantable devices | `Device` record |
| Clinical notes | `Note` |
| Health concerns | `Condition` |
| Care plan | `CarePlan` / Goal |
| Health insurance information | `Coverage` |

**Broader DRS categories (beyond USCDI) — also flag:**

| DRS Category | Examples | Canvas equivalent |
|---|---|---|
| Additional clinical documentation | Progress notes, consult notes, operative notes, discharge summaries, therapy notes (non-psychotherapy), referral letters | `Note` + appropriate `Command` / `Document` |
| Diagnostic artifacts | Pathology reports, imaging reports, cardiac tracings, ECGs | `DiagnosticReport` / `Observation` / `Document` |
| Orders and administration records | Orders, order sets, medication administration records | Order commands (`Prescribe`, `LabOrder`, `ImagingOrder`) |
| Care coordination communications | Referrals, inter-provider messages, consult requests affecting treatment | `Refer` command, `Note`, `Document` |
| Authorizations & consents | Consents, releases, treatment authorizations, prior authorization files | `Consent` / `Document` |
| Billing & encounter records | Encounter forms, itemized bills, remittance details, billing correspondence, claim files, EOBs | `Claim` / `Coverage` / native billing models |
| Utilization / case management | Case management notes, disease management records, nurse advice documentation, appeals / grievances | `Note` + `Task` + appropriate Command |
| Imported external data used for decisions | External lab feeds, HIE imports, device data once incorporated into care | The corresponding native clinical model (not a custom blob) |
| Patient-generated health data *used for care decisions* | PROs, home BP readings, symptom diaries once reviewed and incorporated | `Observation` / `Questionnaire` response |

**Excluded from the DRS — custom data is appropriate here:**

| Category | Why it's excluded | Notes |
|---|---|---|
| **Psychotherapy notes** | HIPAA-special — *separate* notes documenting/analyzing counseling session content | **Do not store in `Note` either** — if plugin handles psychotherapy notes, escalate to Product/Compliance; requires a separate controlled store |
| Quality assurance / peer review / internal audits | Excluded unless used for individual patient decisions | Custom data or internal tooling is fine |
| Business planning, forecasting, underwriting workpapers | Not about individual patients | Custom data is fine |
| De-identified / limited datasets for research | Excluded from DRS by definition | Custom data is fine |
| Personal notes / memory aids not shared | "Sticky note for myself" — not a record | Custom data is fine (see sticky-note pattern) |
| Litigation holds | Excluded by regulation | Escalate to Compliance; don't touch via plugin |

**Acceptable custom data (mechanical / non-decisional):**
- Workflow state (assignment queues, in-progress rollups, reminder acknowledgments, dismissals)
- Integration bookkeeping (external system IDs, sync timestamps, webhook cursors)
- Plugin-specific configuration (settings, user preferences, catalog/template definitions)
- Ephemeral session state (cache keys, QR-code session IDs, WebSocket session bindings)
- Per-user UI preferences (hidden items, sort orders)

The test: *if removing this custom data would change what the record says about the patient or what a covered entity would use to make a decision about them, it belongs in a Canvas native model, not custom data.*

**Flag:** Any `CustomModel` / `AttributeHub` whose fields restate a concept from either the USCDI or broader DRS tables above. Recommend migrating the data capture into Canvas's native model (via the appropriate Command / SDK write path) so the data becomes part of the designated record set.

**Flag HIGH:** Any plugin handling psychotherapy notes — these have special HIPAA treatment and are neither DRS-bound nor conventional `Note`-bound. Escalate to Product/Compliance before any storage decision.

**Flag HIGH (billing/claims):** Plugins that create, modify, or transmit billing, claims, or EOB content outside Canvas's billing primitives — this is DRS content and likely ONC-adjacent. Confirm with Product before routing around native billing.

---

### Step 4: Tenet 2 — Placement

**Rule:** Placement communicates *for whom* and *when* a feature is used. Wrong placement trains users to look in the wrong place — and one application should do one thing. A feature that mixes patient-specific work with settings/admin work belongs in two applications, not one.

**Scope → surface mapping:**

| Plugin purpose | Correct manifest scope | UX surface | Examples |
|---|---|---|---|
| Settings / configuration / admin / user preferences — not centered on clinical data display | `provider_menu_item` | Provider menu | Catalog management, template CRUD, integration setup, org-wide defaults, user-preference editors, admin dashboards |
| Cross-patient clinical panel activities — population / worklist / rollup views | `global` | Panel | Worklists, queues, population-health dashboards, cohort views, cross-patient reports |
| Single-patient context — acting on *this* patient's record | `patient_specific` | Chart | Patient-chart widgets, per-patient actions, chart-side panels, per-patient data entry |
| Patient-facing (portal) | `portal_menu_item` | Patient portal | Patient-side forms, patient-visible content, patient self-service |

**`provider_menu_item` vs. `global` — the subtle one:**

Both live outside a patient chart, but they are not the same surface.

- `provider_menu_item` is for **settings-ish** work: configuring the plugin, managing templates/catalogs, editing user preferences, org-wide admin actions. The user goes here to *change how the system behaves*, not to look at clinical data.
- `global` is for **panel-level clinical activities**: worklists, queues, rollups, population dashboards. The user goes here to *act on clinical data across many patients*.

If the feature answers "how should the system behave?" → `provider_menu_item`. If it answers "what's happening across my patients?" → `global`. If in doubt, ask: does opening this UI show patient clinical data as its primary content? If yes → `global`. If no → `provider_menu_item`.

**Detect:**

```bash
grep -n "\"scope\"" "$INNER/CANVAS_MANIFEST.json"
grep -rn "LaunchModalEffect\|TargetType\." --include="*.py" .
grep -rn "class .*(Application)\|class .*(ActionButton)" --include="*.py" .
grep -rn "@api\.\(get\|post\|put\|delete\|patch\)\|def \(get\|post\|put\|delete\|patch\)" --include="*.py" .
grep -rn "patient_id\|patient\.id\|self\.event\.context" --include="*.py" .
```

For each `application` / UI component:
- Read its declared `scope` in the manifest.
- Read what it actually does in code — is it reading/writing a single patient? org-wide config? cross-patient rollup?
- Check `LaunchModalEffect` targets (`RIGHT_CHART_PANE` implies patient chart; `DEFAULT_MODAL` may be global or patient-modal).
- **Enumerate every endpoint / handler the application exposes.** Classify each one individually as: patient-specific action, global/cross-patient action, or settings/config action.

**Flag — basic mismatches:**
- Org-wide admin config surfaced as `patient_specific` (should be `provider_menu_item`)
- A patient-chart feature declared `global` (should be `patient_specific`)
- A cross-patient dashboard declared `patient_specific` (should be `global`)
- A patient-facing feature declared `provider_menu_item` (should be `portal_menu_item`)
- A settings-ish UI declared `global` (should be `provider_menu_item`) or vice versa — clinical panel mis-scoped as settings

**Flag — mixed-scope apps (one application doing two jobs):**

*Patient-scoped app mutating non-patient state (most common):*
- App declared `patient_specific` but has endpoints that create, update, or delete records not tied to the current patient
- Endpoint that mutates a shared catalog / template / default / user preference while living behind a chart button
- Endpoint whose path params do not include a patient identifier, inside an application whose manifest scope is `patient_specific`
- Symptom: CRUD handlers (POST/PUT/DELETE) on `/routes/favorites`, `/templates`, `/config`, `/settings`, `/catalog` inside a `patient_specific` application
- **Fix:** Split into two applications — a `patient_specific` one for the per-patient action (read-only catalog + act on this patient), and a `provider_menu_item` one for the management/CRUD surface.

*Global-scoped app acting on a single patient (less common):*
- App declared `global` but every handler takes a `patient_id` from URL/body and operates only on that patient
- The "panel" / "dashboard" framing is a fiction — the UI is really a one-patient tool surfaced from the wrong place
- **Fix:** Move to `patient_specific`, or if the app legitimately spans patients, surface the single-patient drill-down as a distinct `patient_specific` application linked from the panel.

**The "one app, one job" test:** For each application, list its endpoints in two columns: *patient-specific* vs. *non-patient-specific*. If both columns have entries, the application should probably be split. Mixed scopes teach users to find global settings only when they happen to have a patient chart open (or vice versa), which is a durable source of confusion.

---

### Step 5: Tenet 3 — Coded Data Capture & Code-Based Matching

**Rule:** Clinical concepts must be captured and matched by standard codes (SNOMED CT, LOINC, RxNorm, ICD-10-CM, CPT, CVX), not by display strings. String matching is fragile across locales, synonyms, casing, and vendor feeds; it also breaks interoperability.

**Detect — string matching on clinical concepts:**

```bash
grep -rn "\.name\s*==\|\.name\.lower()\|\.display\s*==\|\.display\.lower()\|\.icontains\|name__icontains\|display__icontains" --include="*.py" .
grep -rn "name__in\s*=\s*\[" --include="*.py" .
```

For each hit, check if the match is against a clinical concept (condition, medication, allergy, observation, procedure, immunization). If so — **flag**. Clinical matching should use `code` + `system` fields.

**Detect — capture paths that skip codes:**

Look for flows that store a user-typed string (e.g. chief complaint, diagnosis, allergy reaction, medication name) without an accompanying code. Grep UI and form handlers for free-text fields that capture clinical concepts.

**Recommend instead:**
- Condition/problem matching → SNOMED CT code or ICD-10-CM code
- Medication matching → RxNorm code
- Lab / observation → LOINC code
- Immunization → CVX code
- Procedure → CPT or SNOMED CT
- Anything user-facing that captures one of the above should offer a code-bound picker, not free text

---

### Step 6: Tenet 4 — Don't Duplicate Native Canvas Functionality

**Rule:** If Canvas already has a primitive for it, use the primitive. Parallel systems fragment the record, break downstream reports/exports, and add maintenance burden on the customer.

**Detect — common duplications:**

| Plugin pattern | Use this Canvas primitive instead |
|---|---|
| Custom "survey" / "screening" / "assessment" UI that stores Q&A in a CustomModel | `Questionnaire` (via `canvas_sdk.v1.data.questionnaire`) |
| Custom task/to-do list with status tracking | `Task` / `AddTask` effect |
| Custom "note" / "journal" / free-text clinical documentation | `Note` + appropriate `Command` |
| Custom scheduling / appointment slots | Canvas scheduling primitives |
| Custom reminders surfaced as banners | `AddTask`, `AddBannerAlert`, or native reminder systems |
| Custom "intake form" storing structured clinical data | `Questionnaire` + coded mappings |
| Custom goal tracking | `Goal` command |
| Custom allergy/medication/condition capture | The corresponding Command (Allergy, Prescribe, Diagnose, etc.) |

```bash
grep -rn "class .*(CustomModel)" --include="*.py" . -A 20
grep -rn "Questionnaire\|AddTask\|AddBannerAlert\|Note\|Goal" --include="*.py" .
```

For each `CustomModel`, ask: "Could this be a Questionnaire response, Task, Note, or Command result instead?" If yes — **flag** and recommend the primitive.

---

### Step 7: Tenet 5 — Alert Fatigue & Workflow Interruption

**Rule:** Every interruption (banner, popup, modal, required-field hook) should be *justified*, *contextual*, and *dismissible*. EHR alert fatigue is a documented cause of burnout and missed clinically important alerts.

**Detect:**

```bash
grep -rn "AddBannerAlert\|LaunchModalEffect\|ShowPatientChartSummarySection\|AutocompleteSearchResultsEffect" --include="*.py" .
```

For each interruption, evaluate:

1. **Trigger scope** — Does it fire on every event, or only when a clinically meaningful condition is met? (e.g. firing on *every* patient chart open = fatigue risk; firing only when `systolic > 180` = justified.)
2. **Dismissibility / debouncing** — Can the clinician dismiss it? Is it suppressed after acknowledgment or for a sensible interval?
3. **Criticality vs. presentation** — Is a BLOCKING modal being used for informational content? Prefer passive surfacing (banner, chart section, task) over blocking UI unless the content is truly critical and requires acknowledgment.
4. **Required fields / pre-commit hooks** — Are they forcing clinician input that is not clinically necessary?

**Flag:**
- Alerts that fire unconditionally
- Blocking modals used for informational content
- Multiple banners stacking on the same event
- Required-field enforcement without a strong clinical rationale

---

### Step 8: Tenet 6 — Configurability of Clinical Logic

**Rule:** Clinical thresholds, code lists, target ranges, and decision cutoffs vary by specialty, population, and customer. They belong in configuration (secrets, settings, or configurable content), not hardcoded in Python.

**Detect — hardcoded clinical values:**

```bash
grep -rn -E "(>|<|>=|<=|==)\s*[0-9]+" --include="*.py" . | grep -vE "test_|\.venv|__pycache__"
grep -rn -E "\[[\"']?[A-Z][0-9]{2}" --include="*.py" .
grep -rn "systolic\|diastolic\|a1c\|bmi\|ldl\|hdl\|egfr\|creatinine" --include="*.py" -i
```

For each hit, classify:
- **Hardcoded clinical threshold** (e.g. `systolic > 140`, `a1c >= 9`, `bmi < 18.5`) → **flag** as configurability risk
- **Hardcoded code list** (e.g. a Python list of ICD-10 codes for "diabetes") → **flag**; code lists evolve (new CPT/ICD releases) and vary by customer → move to manifest/secrets or a content file the customer can update

**Recommend:**
- Thresholds → declare as plugin setting in `CANVAS_MANIFEST.json` secrets with sensible defaults
- Code lists → ship as plugin content (JSON/CSV in `content/`) or configurable setting so customers can extend without a code change

---

### Step 9: Tenet 7 — Audit Trail & Attribution

**Rule:** The audit trail must reflect the *real actor* that performed an action. Actor identity is distinct from routing/assignment fields, and the distinction determines whether a given pattern is HIGH.

**Two concepts to keep separate:**

1. **Actor** — who actually performed the action (pressed the button, made the API call, triggered the effect). Must be captured in Canvas's audit. For session-authenticated calls, this is the logged-in Staff. For API-key / service-account / webhook calls, this is the **bot** (the integration's service account). It must never be silently attributed to a clinician who did not actually perform the action.

2. **Routing / assignment** — fields the caller supplies that *name* a clinician for business reasons: `provider_id` on a note (whose note is this?), `assignee` on a task, `prescriber_id` on a carried-forward prescription, `author` of a draft. These are legitimate for an integration to set. They tell Canvas "file this under Dr. X" — they do not attest that Dr. X authored the content.

**Detect — writes to SDK models or custom data:**

```bash
grep -rn "\.save()\|\.create(\|\.update(\|\.delete(" --include="*.py" . | grep -v "test_\|\.venv\|__pycache__"
grep -rn "Effect\|effect_type" --include="*.py" .
grep -rn "APIKeyAuthMixin\|StaffSessionAuthMixin" --include="*.py" .
grep -rn "\.sign(\|\.lock(\|push_charges\|commit_charges\|\.commit(" --include="*.py" .
grep -rn "provider_id.*=\|staff_id.*=\|author_id.*=" --include="*.py" .
```

For each write, verify:
- Writes to **SDK data** flow through `Effect` types (which carry Canvas's built-in attribution + provenance)
- Writes to **plugin custom data** that represent clinical workflow state attribute the actor — either via an explicit `created_by` / `modified_by` field storing staff key, or via documented system-attribution when the action is automated
- Writes triggered by **external systems / webhooks** log the source (the bot / inbound origin, not an impersonated clinician)

**Flag HIGH:**
- **API-key-authenticated endpoints that trigger attestation events as a named clinician.** An attestation is an action Canvas (or the clinician herself) treats as certification of correctness:
  - **Electronic signature** on a note, order, or form (`NoteEffect.sign`, `CommandEffect.commit` on signing-adjacent commands, e-prescribe send, form signature)
  - **Signing-adjacent commits**: actions that Canvas treats as the clinician's certification — confirm with Canvas internals whether `push_charges`, `commit`, or similar imply a signature
- **Shadow-override patterns**: side-channel metadata keys that change *displayed* data while the underlying record stays untouched (downstream viewers see the edited version and may assume the named clinician approved it)

**Flag MEDIUM:**
- `CustomModel.save()` / `.create()` / `.update()` mutating clinically relevant state without capturing the actor at all (neither bot nor staff)
- Missing Canvas-side audit records for high-impact operations (print, export, transmission) — the event happened but can't be reconstructed
- API-key auth on endpoints that touch PHI-bearing data without a corresponding audit entry naming the bot

**Not a Tenet 7 flag (but call out for customers):**
- API-key-authenticated endpoints that **create or route** records on behalf of a named clinician for non-attestation purposes (bulk import, scheduling, CCM dashboards, task routing, unsigned note creation attributed to a provider). Legitimate integration patterns. The README should document that:
  - The audit trail stamps the **integration bot** as the real actor
  - `provider_id` / `assignee` / `author` fields are **routing**, not attestation
  - Named clinicians should only receive routing for records where their real attestation is not required
  - It is the **customer's responsibility** to ensure the integration is used within those bounds

**Golden patterns:**
- *Clinician-driven action* → `StaffSessionAuthMixin` + `staff_id` from `canvas-logged-in-user-id` header + `Effect` types for all mutations.
- *Integration-driven action on behalf of a clinician* → API-key / service-account auth + `provider_id` in the body names the routing target + Canvas audit stamps the **bot** as the real actor + README documents that attestation is NOT implied.

---

### Step 10: Tenet 8 — Terminology Consistency

**Rule:** Use Canvas vocabulary (so users and developers navigate consistently) and standard clinical vocabulary (so data is interoperable).

**Canvas vocabulary:**

| Canvas term | Wrong alternatives to flag |
|---|---|
| Patient | Client, Member, Subject, User |
| Staff | Provider, Clinician, User, Doctor (in code/model names — display strings are fine) |
| Note | Visit (when referring to the record), Encounter Record |
| Command | Form, Widget, Entry |
| Effect | Action, Output |
| Protocol | Trigger, Rule Engine |
| Questionnaire | Survey, Form, Intake |
| Task | To-Do, Reminder, Action Item |

**Detect:**

```bash
grep -rn "class Client\|class Member\|provider_id\|provider_key\|provider_name\|clinician" --include="*.py" .
grep -rn -i "client_id\|user_id" --include="*.py" .
```

Review hits in context — display strings to patients can say "your provider" (that's fine); model/field names, class names, and variable names should use Canvas terms.

**Clinical vocabulary:** In addition to Tenet 3 (code-based matching), make sure field names reflect standard code systems: `snomed_code`, `loinc_code`, `rxnorm_code`, `icd10_code`, `cvx_code` — rather than `dx_code`, `med_code`, `lab_code` with unspecified system.

---

### Step 11: Tenet 9 — ONC Certified Criteria Overlap

**Rule:** Canvas holds ONC Health IT certification for specific §170.315 criteria. A plugin that *replaces* or *parallels* a certified path can put the customer out of compliance, or force Canvas to re-certify. Overlap must be intentional and scoped.

Reference: https://www.canvasmedical.com/compliance/onc/mandatory-disclosures (Certificate #15.04.04.3112.Canv.01.00.1.220523)

**Certified criteria Canvas holds — flag any overlap:**

| Criterion | Functionality | Flag the plugin if it… |
|---|---|---|
| §170.315(a)(1) | CPOE — medications | Creates, modifies, or routes medication orders outside native Rx command |
| §170.315(a)(2) | CPOE — labs | Creates or routes lab orders outside native Order command |
| §170.315(a)(3) | CPOE — diagnostic imaging | Creates or routes imaging orders outside native Order command |
| §170.315(a)(4) | Drug interaction / allergy checks in CPOE | Implements its own DDI/DAI checking in the order path |
| §170.315(a)(5) | Demographics | Captures or mutates demographic fields in a custom store |
| §170.315(a)(12) | Family health history | Stores family health history outside Canvas's native model |
| §170.315(a)(14) | Implantable device list | Tracks implanted devices outside `Device` |
| §170.315(b)(1) | Transitions of care documentation | Generates/consumes TOC documents |
| §170.315(b)(2) | Clinical information reconciliation | Reconciles medications / allergies / problems |
| §170.315(b)(3) | Electronic prescribing | Prescribes outside native Rx command |
| §170.315(b)(10) | Electronic health information export | Implements bulk record export |
| §170.315(b)(11) | Decision support interventions | Implements CDS that replaces/parallels native CDS, **or ships plugin-authored clinical guidance (titration schedules, dosing defaults, decision rules, alert thresholds) baked into code or default content** |
| §170.315(c)(1–3) | Clinical quality measures — record / import / report | Records, imports, or reports CQMs |
| §170.315(e)(1) | Patient view / download / transmit | Exposes patient-facing record access |
| §170.315(e)(3) | Patient health information capture | Captures patient-reported data in a custom store (should be Questionnaire) |
| §170.315(f)(1) | Immunization registry transmission | Transmits immunizations to a registry |
| §170.315(f)(5) | Public health case reporting | Transmits case reports |
| §170.315(g)(10) | Standardized API (FHIR) | Exposes its own FHIR-shaped API in place of Canvas's |

**Detect:**

```bash
grep -rn "Prescribe\|MedicationOrder\|LabOrder\|ImagingOrder\|Immunization\|FamilyHistory\|Device\|CarePlan\|Coverage" --include="*.py" .
grep -rn "fhir\|FHIR" --include="*.py" .
grep -rn "cqm\|quality_measure" --include="*.py" -i
```

For each hit, cross-reference the plugin's stated purpose against the certified criteria table. When overlap exists:

- **If the plugin augments Canvas's path** (e.g. adds a decision-support nudge that sits next to the native Rx command): document it, note the interaction, and confirm it doesn't bypass Canvas's certified flow.
- **If the plugin replaces Canvas's path** (e.g. a parallel prescribing UI that writes orders through a custom pipe): **flag as HIGH** — this is a compliance and re-certification risk. Recommend routing through native Commands / Effects.
- **If the plugin exports or transmits certified content** (EHI export, immunization registry, case reporting, patient VDT): **flag as HIGH** — confirm with the product team before shipping.

**Plugin-authored clinical content vs. plugin-surfaced fields (Tenet 9 + §170.315(b)(11)):**

The CDS-lite concern is specifically about **clinical guidance the plugin ships** — not about the plugin exposing fields the user can type clinical content into.

Flag as CDS-lite:
- Hardcoded dosing schedules (e.g. "Starting / Titration / Maintenance" shipped as default medication labels)
- Default clinical thresholds baked into code (e.g. `SYSTOLIC_ALERT = 140`)
- Default code lists representing a clinical opinion (e.g. which ICD-10 codes count as "diabetes" for this plugin's logic)
- Default screening intervals, default follow-up windows, default titration steps — anything where the plugin author encoded a clinical decision the customer will inherit

Do **not** flag:
- A plugin that offers a `label` / `notes` / `threshold` field the user populates with their own clinical content — that's user-authored, not plugin-authored
- A plugin that surfaces Canvas's own CDS output (e.g. reads a `BannerAlert` effect and re-renders it) — Canvas owns the provenance
- A plugin that wraps a native certified command (e.g. pre-fills `PrescribeCommand` with user-saved templates) as long as the defaults themselves are not plugin-shipped clinical guidance

**The test:** "If I remove the plugin's shipped content/defaults, does any clinical opinion remain in the plugin?" If yes — the plugin is authoring clinical guidance and needs provenance (source, reviewer, review cadence) or needs to move to formal CDS. If no — the plugin is a mechanism and the clinical judgment sits with the customer.

**Recommendation when CDS-lite is flagged:** move defaults to customer-owned content (aligns with Tenet 6), **or** document clinical source + review cadence in the README, **or** promote to a formal CDS intervention with provenance. Often the Tenet 6 fix (move defaults out of code) resolves the Tenet 9 concern as a side effect.

---

### Step 12: Generate Product Review Report

Create a timestamp and workspace directory:

```bash
WORKSPACE_DIR=$(uv run python "${CLAUDE_PLUGIN_ROOT}/scripts/get_plugin_dir.py")
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
REPORT_FILE="$WORKSPACE_DIR/.cpa-workflow-artifacts/product-review-$TIMESTAMP.md"
```

Save the report:

```markdown
# Product Review Report: {plugin_name}

**Generated:** {timestamp}
**Reviewer:** Claude Code (CPA)
**Scope:** Designated Record Set / clinical data model, placement, coded data capture, native-primitive usage, alert fatigue, configurability, attribution, terminology, ONC certified-criteria overlap.

## Summary

| Tenet | Status | Issues |
|---|---|---|
| 1. Designated Record Set / Clinical Data Model | ✅ / ⚠️ X / ❌ | ... |
| 2. Placement | ✅ / ⚠️ X / ❌ | ... |
| 3. Coded Data Capture | ✅ / ⚠️ X / ❌ | ... |
| 4. Native Canvas Primitives | ✅ / ⚠️ X / ❌ | ... |
| 5. Alert Fatigue | ✅ / ⚠️ X / ❌ | ... |
| 6. Configurability | ✅ / ⚠️ X / ❌ | ... |
| 7. Audit Trail / Attribution | ✅ / ⚠️ X / ❌ | ... |
| 8. Terminology Consistency | ✅ / ⚠️ X / ❌ | ... |
| 9. ONC Certified-Criteria Overlap | ✅ / ⚠️ X / ❌ HIGH | ... |

## Detailed Findings

### 1. Designated Record Set / Clinical Data Model
[findings with file:line references, DRS / USCDI category mapping, recommendation]

### 2. Placement
[manifest scope vs. actual behavior, mismatches, recommendation]

### 3. Coded Data Capture
[string-match hits, code-system recommendation per concept]

### 4. Native Canvas Primitives
[CustomModel-to-primitive mappings, recommendation]

### 5. Alert Fatigue
[effect inventory, trigger-scope assessment, dismissibility review]

### 6. Configurability
[hardcoded values, proposed configuration surface]

### 7. Audit Trail / Attribution
[write paths missing actor, recommendation]

### 8. Terminology Consistency
[mismatches, recommended rename scope]

### 9. ONC Certified-Criteria Overlap
[criterion-by-criterion overlap, augment-vs-replace classification, compliance risk]

## Priority Recommendations

| Priority | Tenet | Issue | Location | Recommendation |
|---|---|---|---|---|
| HIGH | ... | ... | file:line | ... |
| MEDIUM | ... | ... | file:line | ... |
| LOW | ... | ... | file:line | ... |

## Verdict

**✅ PASS** — no product-level concerns

OR

**⚠️ DISCUSSION NEEDED** — X items require product judgment (Y HIGH, Z MEDIUM)

OR

**❌ BLOCKERS** — regulatory / compliance risk from ONC overlap; escalate before shipping.
```

Tell the user the report path.

---

### Step 13: Offer to Guide (Do Not Auto-Fix)

These are product judgments, not engineering defects. Do **not** silently refactor. Use `AskUserQuestion` to route next steps:

```json
{
  "questions": [
    {
      "question": "Product review found items that warrant discussion. How would you like to proceed?",
      "header": "Product review next steps",
      "options": [
        {"label": "Walk through each finding", "description": "Discuss findings one at a time and decide on fixes together"},
        {"label": "Fix structural items only", "description": "Apply non-controversial changes (terminology renames, moving thresholds to config, placement fixes) — skip judgment calls"},
        {"label": "Review only", "description": "I'll take the report to the product team"}
      ],
      "multiSelect": false
    }
  ]
}
```

**If the user chooses to walk through findings:** Go tenet by tenet, show the user each finding, propose a concrete change, and apply it only after confirmation. For Tenet 1 (USCDI) and Tenet 9 (ONC overlap) findings, do **not** silently migrate data paths — always confirm with the user first, because these can have customer-facing or compliance implications.

**If the user chooses structural items only:** Apply renames (Tenet 8), move hardcoded clinical values to configuration (Tenet 6), and fix clear scope/placement mismatches (Tenet 2). Do not touch USCDI data migrations or ONC-overlap items without confirmation.

After any changes, re-run the affected checks and update the report with "RESOLVED" status where applicable.

---

## CPA Workflow

This command is complementary to `/cpa:security-review` — it surfaces *product* concerns, where security-review surfaces *engineering* concerns. Run it before `/cpa:wrap-up` for any customer-facing or clinically-impactful plugin.

```
/cpa:check-setup                 →  Verify environment tools
/cpa:new-plugin                  →  Create plugin from requirements
/cpa:deploy                      →  Deploy to Canvas instance for UAT
/cpa:coverage                    →  Check test coverage (aim for 90%)
/cpa:security-review             →  Engineering security audit
/cpa:product-review              →  Product / regulatory / norms review   ← YOU ARE HERE
/cpa:database-performance-review →  Database query optimization
/cpa:wrap-up                     →  Final checklist before delivery
```

After the product review passes (or its findings are triaged), continue to `/cpa:wrap-up`.
