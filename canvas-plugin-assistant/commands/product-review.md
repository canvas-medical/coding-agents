---
name: product-review
---

# Product Review

Evaluate a Canvas plugin from a product perspective: alignment with core tenets, regulatory risk (ONC-certified criteria overlap), and placement/norms. This is complementary to `/cpa:security-review` (engineering concerns) — this command surfaces product judgments a human needs to make.

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

### Step 3: Tenet 1 — Clinical Data Model / USCDI V3

**Rule:** Custom data must not extend the clinical data model for concepts already represented and required in Canvas. Canvas has implemented USCDI V3. Customer data must flow into Canvas's canonical models so it becomes part of the EHI / designated record set.

Reference: https://isp.healthit.gov/united-states-core-data-interoperability-uscdi

**Detect:**

```bash
grep -rn "CustomModel\|AttributeHub" --include="*.py" .
grep -rn "class .*(CustomModel)" --include="*.py" .
```

For each `CustomModel` / `AttributeHub` usage, inspect the fields and ask: **Is this concept already covered by a USCDI V3 data class?**

USCDI V3 data classes (non-exhaustive — flag if a CustomModel looks like one of these):

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

**Flag:** Any `CustomModel`/`AttributeHub` whose fields restate one of the above. Recommend migrating the data capture into Canvas's native model (via the appropriate Command / SDK write path) so the data becomes part of the designated record set.

**Acceptable custom data:** Workflow state (assignment queues, in-progress rollups, reminder acknowledgments), integration bookkeeping (external system IDs, sync timestamps), plugin-specific configuration — none of which are USCDI data classes.

---

### Step 4: Tenet 2 — Placement

**Rule:** Placement communicates *for whom* and *when* a feature is used. Wrong placement trains users to look in the wrong place.

| Plugin purpose | Correct manifest scope | UX surface |
|---|---|---|
| Non-patient-specific configuration (e.g. organization-wide settings, admin UIs) | `provider_menu_item` | Provider menu |
| Patient dashboards, global views, cross-patient rollups | `global` | Panel |
| Patient-specific features (single-patient context) | `patient_specific` | Chart |
| Patient-facing (portal) | `portal_menu_item` | Patient portal |

**Detect:**

```bash
grep -n "\"scope\"" "$INNER/CANVAS_MANIFEST.json"
grep -rn "LaunchModalEffect\|TargetType\." --include="*.py" .
```

For each `application` / UI component:
- Read its declared `scope` in the manifest
- Read what it actually does in code (is it reading/writing a single patient? an org-wide list? staff-only config?)
- Check any `LaunchModalEffect` targets (`RIGHT_CHART_PANE` implies patient chart context; `DEFAULT_MODAL` may be global)

**Flag mismatches**, for example:
- Org-wide admin config surfaced as `patient_specific` (should be `provider_menu_item`)
- A patient-chart feature declared `global` (should be `patient_specific`)
- A cross-patient dashboard declared `patient_specific` (should be `global`)
- A patient-facing feature declared `provider_menu_item` (should be `portal_menu_item`)

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

**Rule:** Any write that affects the patient record must be attributable (who/what/when). Silent or un-attributed mutations break the legal record and make incidents un-investigable.

**Detect — writes to SDK models or custom data:**

```bash
grep -rn "\.save()\|\.create(\|\.update(\|\.delete(" --include="*.py" . | grep -v "test_\|\.venv\|__pycache__"
grep -rn "Effect\|effect_type" --include="*.py" .
```

For each write, verify:
- Writes to **SDK data** flow through `Effect` types (which carry Canvas's built-in attribution + provenance)
- Writes to **plugin custom data** that represent clinical workflow state attribute the actor — either via an explicit `created_by` / `modified_by` field storing staff key, or via documented system-attribution when the action is automated
- Writes triggered by **external systems / webhooks** log the source

**Flag:** Any `CustomModel.save()` / `.create()` path that mutates clinically-relevant state without capturing the actor.

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
**Scope:** Product alignment, placement, coded data capture, native-primitive usage, alert fatigue, configurability, attribution, terminology, ONC certified-criteria overlap.

## Summary

| Tenet | Status | Issues |
|---|---|---|
| 1. Clinical Data Model / USCDI V3 | ✅ / ⚠️ X / ❌ | ... |
| 2. Placement | ✅ / ⚠️ X / ❌ | ... |
| 3. Coded Data Capture | ✅ / ⚠️ X / ❌ | ... |
| 4. Native Canvas Primitives | ✅ / ⚠️ X / ❌ | ... |
| 5. Alert Fatigue | ✅ / ⚠️ X / ❌ | ... |
| 6. Configurability | ✅ / ⚠️ X / ❌ | ... |
| 7. Audit Trail / Attribution | ✅ / ⚠️ X / ❌ | ... |
| 8. Terminology Consistency | ✅ / ⚠️ X / ❌ | ... |
| 9. ONC Certified-Criteria Overlap | ✅ / ⚠️ X / ❌ HIGH | ... |

## Detailed Findings

### 1. Clinical Data Model / USCDI V3
[findings with file:line references, USCDI data class mapping, recommendation]

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
