# Writing Style

Rules for every user facing string the skill generates. Button labels, tooltips, headings, modal bodies, banners, empty states, error messages, form labels, and onboarding copy. Paired with a clinical vocabulary carve out so established medical and Canvas product terms survive the puffery filter. For empty state specific voice rules (be specific, be action oriented, be educational or blunt by type), see [component-usage.md](component-usage.md) Voice subsection inside Empty States. This file governs prose everywhere else and extends that subsection's principles.

## Why this exists

Large language models leave characteristic fingerprints in writing. Em dashes, title case headings, puffery clusters, vague attribution, inflation of significance, collaborative assistant tone. The patterns are well documented, including in the Wikipedia editor guide Signs of AI writing. They also happen to be bad UI writing independently, so enforcing the rules improves clarity whether or not the author is an LLM. The catch for clinical software is that several flagged words (vital, critical, significant, active, acute, pivotal, present, underlying) have legitimate clinical meaning and must not be blanket banned. This file names the rules, the exceptions, and the contextual test.

## Scope by surface

Not every rule fires on every string. Short utility copy resists rules that are statistical across long prose (section summaries, rule of three padding). Longer copy surfaces (onboarding, help, modal bodies) are where puffery creeps in. The table below names the scope.

| Rule category | Fires on |
|---|---|
| Banned punctuation (em dash, en dash, curly quotes) | All strings |
| Sentence case headings | Headings only |
| No didactic disclaimers | Modal bodies, banners, onboarding, help text |
| No collaborative assistant tone | All strings |
| No knowledge cutoff disclaimers | All strings |
| No emoji as decoration | All strings |
| Puffery vocabulary | All strings, check phrase in context |
| Weasel wording | Banners, modal bodies, onboarding, help text |
| Inflation of significance | Banners, modal bodies, onboarding |
| Participle commentary | Tooltips, modal bodies, onboarding, help text |
| Negative parallelism | All strings |
| Rule of three padding | Onboarding, help text, long modal bodies |
| Elegant variation | All strings |
| Section summaries or closing conclusions | Modal bodies only |

## Rules that always apply

- **No em dashes or en dashes.** Replace with commas, parentheses, or separate sentences. Avoid, "Add medication, confirm the dose" written with an em dash between the clauses. Prefer, "Add medication. Confirm the dose."
- **No curly quotes or smart apostrophes.** Straight ASCII quotes only. Curly characters break HTML attributes and template strings.
- **Sentence case in headings.** Capitalize the first word and proper nouns only. Avoid, "Active Medications". Prefer, "Active medications".
- **No didactic disclaimers.** Phrases like "It is important to note", "Please be aware", "It should be emphasized" are AI throat clearing. If the user needs a warning, use canvas-banner. Avoid, "It is important to note that the dose has changed". Prefer, render a canvas-banner with "Dose changed. Review before signing."
- **No collaborative assistant tone.** No first person plural, no chatbot offers of help. Avoid, "Let me help you add a medication". Prefer, "Add medication".
- **No knowledge cutoff disclaimers.** Phrases like "As of my last update", "training data", "I cannot access real time". These leak from the LLM shell occasionally. Cut on sight.
- **No emoji as decoration.** Visual breaks come from canvas-icon, banner severity variants, and canvas-divider. Emoji rendering varies across installs and is a localization and accessibility risk.
- **No overuse of bold.** Bold is reserved for rare inline emphasis inside paragraph text. Button labels, headings, and short labels never carry bold.

## Vocabulary to avoid

The contextual test. Check the phrase, not the word. "Vital signs" is clinical. "Vital role" is puffery. The same word can be both. The clinical carve out below covers the legitimate uses.

- **Puffery clusters.** Vibrant, boasts, tapestry, testament, indelible, deeply rooted, enduring legacy, marks a turning point, stands as. None has a clinical meaning. Cut unconditionally.
- **Inflation of significance.** Serves as, stands as, plays a key role in, sets the stage for, symbolizing. Historical narration, not clinical function. A medication does not serve as anything, it is prescribed.
- **Weasel wording.** Studies show, research suggests, experts agree, industry reports, several sources, some critics. UI copy cites a concrete source or stays concrete.
- **Participle commentary.** Empowering, ensuring, highlighting, fostering, showcasing, leveraging. Adds words without meaning. Cut the participle and name the verb.
- **Promotional stems.** Seamlessly, effortlessly, streamlined, powerful, comprehensive, robust, intuitive. Common in onboarding drift. Replace with the concrete action the surface performs.

## Clinical vocabulary carve out

The rule is contextual, not lexical. The table names the word, when to keep it, and when to cut it.

| Word | Keep when | Avoid when |
|---|---|---|
| Vital | "Vital signs", "vitals" (the medical measurement set) | "Vital role", "vital importance" |
| Critical | "Critical value" (lab category), "critical care", "critical condition", severity levels | "Critical to success", "critical path" in UI copy |
| Significant | "Clinically significant", "statistically significant", "significant change from baseline" | "Significant contribution", "significant milestone" |
| Active | "Active medications", "active problems", "active encounter" (Canvas status attribute) | "Active role", "active participation" |
| Chronic | "Chronic conditions", "chronic pain" (diagnostic classification) | Rarely misused, still avoid outside diagnostic context |
| Acute | "Acute allergic reaction", "acute care" (diagnostic and severity) | "Acute awareness", "acute insight" |
| Pivotal | "Pivotal trial", "pivotal study" (clinical research) | "Pivotal moment", "plays a pivotal role" |
| Present, presenting | "Presenting complaint", "presents with", "present illness" | "Present new opportunities", "present a case for" |
| Underlying | "Underlying condition" | "Underlying principles", "underlying themes" |
| Key | A concrete identifier or a named Canvas concept | "Key insights", "key role", "key takeaways" |

Canvas domain terms that are always safe. Encounter, episode, encounter note, problem list, chief complaint, chart, order, prescription, allergy, intolerance, medication, dose, signature, reconciliation, refill, referral. Use these without hesitation.

## Structural patterns to avoid

- **Negative parallelism.** Patterns like "Not just X, but Y" and "Not X, but Y" read as marketing microcopy. Name the thing once. Avoid, "Not just a confirmation, but a safety check". Prefer, "Confirm this action."
- **Rule of three padding.** Three parallel adjectives or three parallel phrases that manufacture coverage. Avoid, "Fast, reliable, and secure". Pick the one the user needs to know.
- **Elegant variation.** Do not alternate synonyms for the same entity. A patient is a patient, not "the individual", "the subject", "the person in question". A medication is a medication, not "the pharmaceutical agent".
- **Overly exhaustive tooltips.** A tooltip that describes the button, the shortcut, related screens, and the rationale is too much. Prefer the shortest string that lets the clinician act.
- **Section summaries in modal bodies.** Closing paragraphs that restate the modal title or conclude with a value statement. Cut them.
- **Inline-header vertical lists inside UI strings.** Bullet, bold term, colon, descriptive text is an AI style tell. This file uses that format because it is reference documentation. UI copy does not.

## Examples

Empty state heading.
- Avoid, "Empowering Clinicians with a Vibrant, Seamless Medication Workflow".
- Prefer, "No medications recorded".

Tooltip.
- Avoid, "This button serves as the primary action for adding a new medication order, ensuring a streamlined prescribing experience".
- Prefer, "Add medication".

Banner.
- Avoid, "It is important to note that the patient's vitals reflect a pivotal shift in their clinical journey".
- Prefer, "Vitals updated at 09 12. Heart rate elevated".

Modal body.
- Avoid, "Not just a simple confirmation, this step represents a commitment to patient safety, highlighting the importance of the decision ahead".
- Prefer, "Confirm this action. The order will be sent to the pharmacy".

Error message.
- Avoid, "Unfortunately, we were unable to fulfill your request at this time, but rest assured our team is working diligently on a resolution".
- Prefer, "Could not save. Retry in a moment".

Form label.
- Avoid, "Please enter the patient's vital signs below, ensuring accuracy".
- Prefer, "Vital signs".

Button label.
- Avoid, "Save Your Changes Now".
- Prefer, "Save".

Onboarding heading.
- Avoid, "Effortlessly Streamline Your Comprehensive Charting Workflow".
- Prefer, "Chart a visit".

## Validation touch points

The Phase 2 Writing Style check block in [validation-checklist.md](validation-checklist.md) verifies every rule above. Run the checklist after generating or editing any user facing string. The clinical carve out runs before the vocabulary check, so "vital signs" passes while "vital role" fails.
