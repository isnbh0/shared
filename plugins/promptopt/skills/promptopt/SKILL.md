---
name: promptopt
description: Run a fully guided, artifact-backed prompt optimization workflow. Use when the user wants an application prompt, prompt builder, agent instruction, routing prompt, or LLM workflow improved against user-provided train/val cases without directly editing source files.
---

# PromptOpt

Run a guided prompt optimization workflow end to end: gather missing inputs,
create artifacts, run the bounded search, and stop with a decision record.

## Ground Rules

- After configuration is resolved, write only inside the PromptOpt run workspace.
- First-use config bootstrap may write
  `.agents/skill-configs/promptopt/config.yaml` when the user approves it.
- Do not edit application source files, prompts, or config in place.
- Do not invent product intent, output contracts, train cases, val cases, or
  acceptance criteria.
- Train/val cases are user-owned inputs.
- Provisional cases are allowed only when explicitly requested or approved by
  the user, and must be marked untrusted until reviewed.
- Every candidate must be tied to optimizer state, evidence, ledger entries,
  and a decision record.
- Prefer smaller or simpler prompts when candidates are behaviorally equivalent,
  and justify added prompt cost when recommending a longer candidate.
- End when the budget is reached, the stopping rule is reached, or the user
  explicitly decides the run is done.

## Configuration

Resolve config in this order:

1. Explicit path or settings from the user.
2. `.agents/skill-configs/promptopt/config.local.yaml`.
3. `.agents/skill-configs/promptopt/config.yaml`.

PromptOpt has no legacy `.claude/skill-configs/promptopt/` fallback because its
first marketplace release starts on the `.agents/skill-configs/` convention.

If no config exists, stop and ask:

- Where to store PromptOpt run workspaces.
- Whether to use `.agent-workspace/promptopt/runs` or a custom path.
- Whether to write the chosen path to `.agents/skill-configs/promptopt/config.yaml`
  before continuing, or use it only as an explicit setting for the current run.

Wait for the answer. If the user approves persistence, write the config before
continuing. If the user declines persistence, continue with the explicit
workspace path for this run only. See `config.example.yaml` beside this skill for
supported fields.

Resolved fields:

- `workspace_dir`: directory for run workspaces.
- `default_iteration_budget`: optional default maximum search steps.
- `default_candidate_batch_size`: optional default candidate count per step.
- `default_prompt_growth_policy`: optional wording for prompt length/cost
  preference.

## Workspace

Create one run directory per optimization:

```text
${workspace_dir}/
└── YYMMDD-HHMMSS-{slug}/
    ├── brief.md
    ├── preflight.md
    ├── cases/
    │   ├── train.jsonl
    │   ├── val.jsonl
    │   └── final-review.jsonl        # optional, only if user provides it
    ├── prompts/
    │   ├── baseline.md
    │   └── selected.md               # final recommendation copy, if any
    ├── baseline/
    │   └── outputs/
    │       ├── train.jsonl
    │       └── val.jsonl
    ├── baseline-results.md
    ├── candidates/
    │   └── cNNN/
    │       ├── prompt.md
    │       ├── rationale.md
    │       ├── outputs/
    │       └── result.md
    ├── state.json
    ├── ledger.md
    └── decision.md
```

Use kebab-case for `{slug}` based on the target behavior. If the target behavior
is not clear enough to name, do not create the run yet.

For a populated example, inspect
`assets/example-workspace/260101-120000-ticket-router/`. Use it to show users
what files they need and how the artifacts fit together. Do not treat example
cases or outputs as real run data.

## Workflow

Phases:

1. Resolve config and workspace.
2. Run preflight and collect missing user-owned inputs.
3. Create run workspace and materialize artifacts.
4. Snapshot baseline prompt and runtime context.
5. Run baseline on train/val cases.
6. Initialize optimizer state for search.
7. Search with stateful candidate steps.
8. Stop on budget, stopping rule, or user decision.
9. Write decision record.

### Step 1: Resolve Config And Workspace

Follow the Configuration section. If multiple incomplete prior runs exist for
the same target, ask whether to resume one or create a new run.

### Step 2: Run Preflight

Before optimizing, collect every required user-owned input. Inspect the
repository only to discover existing prompt paths, invocation paths, parsers, and
output contracts; do not infer product judgments from code alone.

Required:

- Target behavior: what should improve.
- Prompt target: prompt file, prompt builder, route, workflow, or feature area.
- Output contract: required fields, formats, labels, refusal behavior, fallback
  behavior, or downstream parser expectations.
- Default policy: what to do for ambiguous, incomplete, conflicting, or
  out-of-domain input.
- Train cases.
- Val cases.
- Acceptance criteria.
- Iteration budget or stopping rule.

Optional:

- Final-review cases kept out of optimizer steering.
- Prompt cost preference: length, readability, latency, token cost, or no stated
  preference.

If anything required is missing, ask the user for all missing items in one
preflight request and stop. Do not start optimization with placeholders.

### Step 3: Create Run Workspace

Create the timestamped run directory and materialize:

- `brief.md`: the user-owned decision context.
- `preflight.md`: what was checked, what was provided, and what remains unknown.
- `cases/train.jsonl`: user-provided or explicitly approved train cases.
- `cases/val.jsonl`: user-provided or explicitly approved val cases.
- `cases/final-review.jsonl`: optional user-provided final-review cases.
- Empty output directories for baseline and candidate results.
- `state.json`: initial optimizer state without baseline or candidate results.
- `ledger.md`: empty candidate ledger.

Case format:

```json
{"id":"case-id","input":{},"expected":{},"why_it_matters":"..."}
```

Preserve the user's case content. Normalize structure only when needed for
execution, and record any normalization in `preflight.md`.

### Step 4: Snapshot Baseline

Write `prompts/baseline.md` with:

- Prompt text or prompt-builder summary.
- Source path or discovery note.
- Invocation path, if known.
- Output contract.
- Model/runtime assumptions, if known.
- Input shaping, parser expectations, tool context, and other context needed to
  faithfully replay the LLM call, if known.

If the prompt cannot be found from the user's target description, pause and ask.

### Step 5: Run Baseline

Run the baseline against train and val cases using the most faithful available
non-mutating path. Valid modes include app runtime execution, CLI or harness
execution that faithfully replays the LLM context, and artifact-only/context
reconstruction only when the LLM context can be faithfully reproduced from the
available artifacts.

If the LLM context cannot be faithfully reproduced, do not treat the run as
scored evidence. Record the fidelity gap, mark the evidence insufficient, and
pause for the missing context or user-provided outputs.

Record the execution mode, reproduced context, and any material fidelity gaps in
the run-level state and `decision.md`. Result artifacts may summarize or refer
to that run-level evidence note instead of repeating it. Record baseline outputs
under `baseline/outputs/` and summarize failures in `baseline-results.md`. Do
not change source files to run the baseline.

### Step 6: Initialize Optimizer State For Search

`state.json` must track:

- Objective and constraints.
- Case manifest and exposure notes.
- Baseline prompt snapshot and results.
- Candidate ledger pointer.
- Selection state: selected candidates, current frontier, or leading candidate.
- Rejected hypotheses.
- Open risks.
- Search policy.
- Prompt cost preference.
- Stop condition.

### Step 7: Search With Stateful Candidate Steps

For each search step:

1. Read the current optimizer state.
2. Propose one or more bounded candidates.
3. Record each candidate under `candidates/cNNN/`.
4. Evaluate candidates on the agreed train/val basis using the same execution
   mode, reproduced-context, fidelity-gap, and insufficient-evidence rules as
   the baseline.
5. Update `state.json` and `ledger.md`.
6. Decide whether to continue, stop, or ask the user.

Each candidate records:

- Candidate id.
- Parent candidate ids.
- Operation type.
- Hypothesis being tested.
- Prompt patch or replacement summary.
- Expected improvement.
- Expected risk.
- Prompt cost or complexity change.
- Execution mode or run-level evidence reference.
- Reproduced context or run-level evidence reference.
- Fidelity gaps or run-level evidence reference.
- Train results.
- Val results.
- Contract failures.
- Regressions.
- Selection status.

Choose candidate operations from the current state, evidence, and failure
analysis. Keep enough structure that another agent can replay why a candidate
was tried and why it was kept or rejected.

### Step 8: Stop

Stop when:

- The iteration budget is reached.
- The stopping rule is reached.
- No candidate improves the relevant evidence enough to justify continuing.
- Required information is missing.
- The user explicitly says the run is done.

If stopping because information is missing, write the partial state and ask for
the missing input.

### Step 9: Write Decision Record

Write `decision.md` with:

- Target behavior and prompt target.
- Train/val case manifest.
- Baseline summary.
- Execution mode.
- Reproduced context.
- Fidelity gaps.
- Candidate ledger summary.
- Selection state summary.
- Recommended candidate, if any.
- Why it was selected.
- Prompt cost or complexity increase and why it is justified.
- Val exposure notes.
- Known regressions and unresolved risks.
- Recommendation: promote, hold, or reject.
- What the user would need to do if they choose to apply the candidate.

Final output is recommendation-only unless the user requests a separate
source-editing task.

## Quality Bar

- The run is inspectable from workspace artifacts alone.
- The candidate ledger explains the search path.
- Val cases are optimizer-visible comparison data, not held-out final-review data.
- Any user-provided final-review cases are kept out of candidate steering.
- Longer prompts are justified by evidence, not accepted by default.
- The final answer gives the path to `decision.md` and the recommended next
  user action.
