---
name: agent-patterns
description: When and how to build a Canvas plugin as an agent with the Agent Development Kit (`canvas_sdk.agents`) - choosing an agent over a handler that calls an LLM, the inference gateway key, standard tools before custom tools, rules for custom tools, the manifest's `agents` entry (tool grants, approval, run time, progress), what an agent may write, testing with a fake gateway, and the agent items of a security review. Use whenever a spec involves an LLM, AI, a chat, Claude, or a model reasoning over the chart, and when building, reviewing, or testing any plugin that declares `components.agents`.
---

# Agent Development Kit Patterns

The Agent Development Kit (ADK) runs LLM-driven agents as Canvas plugins. An agent reads the chart through tools, reasons over what it finds, and returns effects the platform applies: draft commands, protocol cards, tasks, messages. It runs on a background worker, so a run can take seconds or minutes.

This skill is the judgment layer: when to build an agent, and the rules that make one safe. The API reference is in the **canvas-sdk** skill's `coding_agent_context.txt`; search it for `BEGIN PAGE https://docs.canvasmedical.com/sdk/agents` (overview, quick start, lifecycle, managing state, tools and the full `standard_tools` catalog, prompts, testing, auditing). If the bundle has no such pages, read them at https://docs.canvasmedical.com/sdk/agents/ instead.

## Check the SDK first

The framework is in preview. Before proposing an agent, confirm the plugin's environment ships it:

```bash
uv run python -c "import canvas_sdk.agents"
```

If that fails, or the target instance runs a Canvas release without the framework, build the handler pattern in the next section instead and tell the user why.

Agent runs are also off on an instance until Canvas turns them on for it. On an instance with them off, every run is recorded as refused with "Agent runs are off on this instance.", so when a deployed agent never runs, check its run record for that reason before debugging the plugin, and tell the user to ask their Canvas team to turn agent runs on for the instance.

## Agent, or a handler that calls a model?

| The spec... | Build |
|---|---|
| Needs one model call over input the plugin already has (extract fields from text the plugin already holds, classify a message, summarize a fixed text) | A handler with `canvas_sdk.clients.llms` (`LlmAnthropic` and friends), see the **plugin-patterns** skill. This sends patient data to the provider through the plugin's own key, not the gateway, so the BAA item under Security and compliance applies |
| Reads an incoming fax or upload | An agent with the intake tools (see Standard tools) |
| Lets the model decide what to read or do next: a chart chat, reconciling outside records, reviewing a visit against earlier follow-up, triaging a queue | An agent |
| Needs the model to write to the chart | An agent: its tool grant bounds what it can write and the platform checks every effect against the requesting clinician's permissions |
| Must answer inside a request, in under a second or two | Neither as an LLM call in the request. An agent run is asynchronous: return `202` and let the UI poll or listen for the result |

An agent reaches Anthropic only through Canvas's inference gateway. Never add an `llms/` directory, an OpenAI or Gemini key, or a provider abstraction to an agent plugin, and never import `anthropic` directly (the sandbox refuses it). The one credential is the plugin's gateway key:

```json
"variables": [{"name": "INFERENCE_GATEWAY_KEY", "sensitive": true}]
```

The platform builds the `LLMGateway` passed to `run()` from that key. `gateway.client()` returns a `GatewayClient` pointed at the gateway that offers `messages.create` and `messages.stream` only, not a full Anthropic client, so there is no `client.beta` or `client.models`. Gateway keys are issued per organization in Canvas Platform, and the user's Canvas team issues one for the plugin. The deploy flow's `installer` tool reads it from `~/.canvas/plugin-secrets/<host>.json`, so ask the user to add it there or set it in the plugin's settings in the Admin UI. Never ask for the key in chat or put it on a command line.

## Shape of an agent plugin

- **The agent**: an `AgentPlugin` subclass with `load_state`, `run`, and `save_state`. `run()` usually builds the messages and calls `self.run_tool_loop(gateway, system=..., messages=..., max_turns=...)`, which calls the model with the agent's granted tools until it ends its turn. Always use `self.tools`, never the imported registry: the platform replaces it with the granted tools before `run()`.
- **The trigger**: agents do not subscribe to events. A handler emits `RunAgentEffect(agent_id="<module>:<Class>", scope=..., patient_id=..., note_id=..., trigger_payload={...})` from `compute()`:
  - event-triggered: a `BaseHandler` or `CronTask`;
  - user-initiated (a chat): a `SimpleAPI` POST emits the effect and returns `202`; the UI polls the plugin's own history endpoint, or listens on the run's progress channel (below).
- **Scope** decides which runs wait for each other: `PATIENT`, `PATIENT_AND_STAFF` (a chat with one clinician about one patient), `NOTE`, `STAFF`, `CLAIM`, `KEY` (with `scope_id`), or `AGENT`. Under `KEY` or `AGENT`, key any per-patient state by `self.subject.patient_id`, or one patient's state loads into another's run.
- **The subject**: the platform checks the patient and note the trigger names and sets `self.subject`; `self.requester` is the staff member whose action started the run. Read the patient from `self.subject`, never from `trigger_payload`.
- **State**: stateless, a per-clinician conversation snapshot in Custom Data (`window_messages` keeps it inside the model's budget), or state kept in the chart itself (the reference advisor's protocol cards). See the Managing State page.

## Tools: standard first

`canvas_sdk.agents.standard_tools` already covers most of what specs ask for, each patient-scoped and permission-checked. Grant by `@category` in the manifest:

- `@clinical_reads`: medications, conditions, labs, vitals, allergies, immunizations, notes and note content, goals, imaging, referrals, history, prescriptions and pharmacy fills and requests, open orders awaiting results (`find_open_loops`), documents, demographics
- `@document_reads`: `read_document` answers a question from a consult report, outside record, or imaging report's file
- `@config_reads`: note types, practice locations, labs and lab tests, and `find_clinical_codes` (ICD-10, FDB, allergen, SNOMED, CVX, CPT from Canvas's ontology services)
- `@clinical_writes`: draft commands on the open note (`originate_plan`, `originate_prescribe_medication`, `originate_lab_order`, `originate_diagnose_condition`, history, allergy, medication statement, immunization statement, vitals, and more), `originate_review_note`, and `edit_staged_command` / `delete_staged_command` for drafts
- `@clinical_alerts`, `@task_reads`, `@task_writes`, `@message_reads`, `@message_writes`, `@claims_reads`, `@claims_writes`
- `@intake_reads` and `@intake_writes`: for a run about an incoming document (`RunAgentEffect(scope=DOCUMENT, document_id=...)`, usually from a `DOCUMENT_RECEIVED` handler), read the document, match its patient in code (a patient is suggested only when exactly one matches), and suggest the patient, document type, report values, and reviewer on the review form for a person to confirm. This is the path for fax and document parsing; don't build a patient match or a parser of your own

Check the catalog (Tools page) before writing a tool. When a spec needs a command a standard tool already drafts, such as importing outside records as history, grant that standard tool rather than building the command in a custom tool: its duplicate, coding, and controlled-substance checks run inside it, and a plugin cannot import its builder to reuse them.

### Rules for a custom tool

Register custom tools on the plugin's own `ToolRegistry` (`filter_search_tool` for reads, `originate_command_tool` or `add_effect_tool` for writes, `@tools.tool` otherwise):

- Take the patient and note from `ctx` (`require_patient_id(ctx)`, `ctx["note_id"]`), never from the model's arguments.
- Treat every id the model passes as untrusted, since the model reads patient-written text: confirm the row belongs to `ctx["patient_id"]` before reading or staging anything.
- Declare `effect_types` for every effect the tool stages. The platform drops any effect no granted tool declares.
- Declare `required_permissions` with the permission the chart checks for the same action (such as `"api.change_task"`), so the tool is hidden from requesters who lack it.
- Give a `progress_label` naming the work ("Reading lab results"), never its arguments.
- Raise `max_result_chars` (up to 200,000) only for a result that cannot be paged; every result is resent on each later model call.
- Return a small confirmation dict from a write tool, and raise on bad input: the loop sends the error back to the model so it can correct itself.
- On an originate tool, mark a field `editable=True` only when the tool's `pre_build` neither checks nor derives it; codes and chart ids stay non-editable.

### Custom Data in tools

An agent runs with its plugin's Custom Data namespace and declared access, as a handler does, so a tool can read the plugin's own tables. Use `filter_search_tool` with `queryset_factory=lambda args, pid: MyModel.objects.filter(patient__id=pid)` and `model=MyModel` (which also makes the rows citable).

- **Reads are scoped only by the query.** Filter by the run's patient (`pid`, through the model's `PatientProxy` foreign key), never a patient from the model's arguments, and check any row id the model passes. A table spanning many patients (a work queue) must also keep to patients the requester can see, which the platform does not check row by row. Stored text from patients or outside systems is untrusted input.
- **Writes bypass every agent control.** Saving a `CustomModel` in a tool is a direct database write, not an effect: the tool grant, the requester's permission check, and `tools.approve` (a tool that stages no effect returns its own result, so a listed tool still writes at once) all miss it. No transaction wraps the run, so a failed or timed-out run keeps a row a tool saved, and a run retried after a gateway outage runs its tools again.
- **So write in `save_state`**, which runs only after `run()` returns in time. A tool that must write mid-run keeps to the plugin's own bookkeeping and is idempotent; anything a person should approve, or that changes the chart, is an effect.

## What an agent may write

- Effect tools **draft**: commands are originated, never committed, and a clinician reviews, commits, or signs them. Don't design a spec where the agent signs, commits, or sends on its own.
- A change that commits waits for the requester's approval. `tools.approve` in the manifest makes any granted tool propose instead of apply, with everything one call stages decided as a single proposal, and any granted tool that stages the same effect type proposes too; the plugin's UI shows the proposal and returns a `DecideAgentProposal` effect from a SimpleAPI route, an application, or an action button when the requester approves or denies. Only the requester decides, within an hour; a decision an agent returns is refused. The platform checks only where the decision came from and that its actor is the requester, so it cannot tell the plugin's code from their click: return `DecideAgentProposal` only from the route the requester's own approve or deny control calls, never from the route that starts the run or from code that decides for them.
- The agent acts for its requester: tools they lack the permission for are hidden, every effect is checked against their permissions and patient groups, and a run on a patient they cannot see is refused. A run no user started (a Canvas Bot, API-key, or webhook trigger) acts with the plugin's own trust, but cannot propose, commit a command, or add a lab report; a run a patient started may change only that patient's own records.
- `edit_staged_command` and `delete_staged_command` change only staged drafts in the run's own note, and only kinds the agent's grant can stage.

## Manifest

```jsonc
{
  "components": {
    "handlers": [{"class": "my_plugin.handlers.trigger:ChatTrigger", "description": "..."}],
    "agents": [
      {
        "class": "my_plugin.agents.chat:ChatAgent",
        "description": "Chart chat",
        "tools": {
          "allowed": ["@clinical_reads", "@clinical_writes", "@task_writes"],
          "denied": ["originate_prescribe_medication"],
          "approve": ["@task_writes"]
        },
        "progress": "activity",
        "run_seconds": 600
      }
    ]
  },
  "variables": [{"name": "INFERENCE_GATEWAY_KEY", "sensitive": true}]
}
```

- `tools.allowed` is the agent's whole grant: names and `@category` groups, minus `denied`. With no `allowed`, the agent gets no tools and can return no effects. Grant the least the spec needs.
- `run_seconds`: 600 by default, at most 1800. A run asking for more than the default is an extended run, and the runner admits only a few at a time, so ask only for what the work measurably needs. The run also stops at `max_model_calls` (40 by default, a class attribute).
- `progress`: what a person waiting sees on the run's channel `/plugin-io/ws/<plugin_name>/agent-run-<run_id>/`. `status` (default) sends heartbeats, `activity` adds each tool's label as it starts and finishes, `reply` adds the reply text as it is written. Only the requester can listen, and tool arguments and results are never sent.

## Testing

`canvas_sdk.test_utils.agents` runs an agent as the platform does, with no real model calls:

- `FakeGateway(reply(tool_use("find_conditions")), reply(text("Done.")))` scripts the model's replies and records each request.
- `prepare_agent(AgentClass, allowed=..., denied=..., approve=..., subject=RunSubject(patient_id=...), requester=RunRequester(staff_id=..., permissions=...))` applies the manifest grant and subject.
- `run_agent(agent, gateway)` returns `run.effects`, `run.dropped`, the model calls, and the tool calls.

Use the manifest's real grant in tests, and test each custom tool directly, including the refusal of another patient's id. `run.effects` is what the tool grant keeps: the harness does not run the platform's permission, patient-run or approval checks, and without a `requester` the run is Canvas Bot's and permissions don't limit it. An effect the requester lacks permission for, or a Canvas Bot run's proposal, passes here and fails the run on an instance. Use the **testing** skill for the general setup.

## Security and compliance

When reviewing an agent plugin, check:

- **Untrusted input**: document, message, and lab text reaches the model as data. No tool may let the model change the patient, the note, or another scope through its arguments.
- **Grant**: `tools.allowed` is no wider than the spec; a write grant is justified; commits go through `tools.approve`.
- **Triggers**: a `RunAgentEffect` names a patient the trigger's own context vouches for, not one read from an unauthenticated request body.
- **Custom tools**: they follow the rules above, with tests that another patient's id is refused.
- **The UI**: a chat route authenticates the staff member, and the plugin never broadcasts to an `agent-run-` channel itself (the platform refuses it).
- **PHI leaving Canvas**: an agent's model calls go through the inference gateway. Any other LLM or AI vendor receiving patient data needs a security and compliance review and a BAA first.
- **Chart writes from model output**: an agent whose output lands in the chart or is shown to a clinician as a suggestion falls under Canvas's decision support certification. Flag it for security and compliance review early, while the design can still change.
