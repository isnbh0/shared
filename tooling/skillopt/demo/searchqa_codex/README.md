# Before→after demo: optimizing a prompt on the codex subscription

A worked SkillOpt run where **both** legs — the target (`codex_exec`) and the
optimizer (`codex_chat`) — run on the **codex / ChatGPT OAuth subscription**, with
no metered API call possible. It starts from a deliberately-bad seed prompt and
traces how the `codex_chat` optimizer rewrites it.

The optimizer leg is only possible because of the vendored `codex_chat` backend
(`../../vendor/skillopt`) and the wrapper's `--optimizer_backend` injection — stock
SkillOpt restricts the optimizer to a metered chat API.

## Result

Held-out **test** set, exact-match (`hard`):

| | exact-match | token-F1 |
| --- | --- | --- |
| **before** (bad seed) | **0.00** | 0.18 |
| **after** (optimized) | **1.00** | 1.00 |

`+1.00` exact-match, accepted at step 1, in **88s / 16 codex calls / 54k tokens** —
all on the subscription. (`trace/summary.json`.)

## What the optimizer did

The task ([SearchQA](../../vendor/skillopt/skillopt/envs/searchqa)) scores the text
inside `<answer>…</answer>` with SQuAD exact-match / F1. The seed
(`trace/skill_v0000_BEFORE.md`) is **actively wrong**: it forces a full explanatory
sentence *inside* the answer tags, which can never exact-match the short gold span —
so baseline EM is 0.

The `codex_chat` optimizer diagnosed this from the failed rollouts and **inverted**
the instruction (`trace/best_skill_AFTER.md`):

> **before:** "always write a complete, polished explanation rather than a short
> label … put your full explanation INSIDE `<answer>` … at least 15 words … Never
> put a bare word."
>
> **after:** "return only the shortest exact answer span … Do not add explanation,
> restate the question, or include surrounding context … A bare word, number, name,
> or short phrase is correct when that is the minimal answer."

`trace/history.json`: step 1 `accept_new_best` (selection 0→1.0), steps 2–3
`skip_no_patches` (already optimal).

## Reproduce

```bash
cd tooling/skillopt
uv sync
unset CODEX_PROFILE OPENAI_API_KEY AZURE_OPENAI_API_KEY ANTHROPIC_API_KEY
export SKILLOPT_OAUTH_LOG_DIR=demo/searchqa_codex/outputs/_oauth_log
uv run skillopt-oauth \
  --config demo/searchqa_codex/config.yaml \
  --target_backend codex_exec --optimizer_backend codex_chat \
  --out_root demo/searchqa_codex/outputs/run_codex_codex
```

Requires a codex ChatGPT subscription (`~/.codex/auth.json`, `auth_mode: "chatgpt"`).
Models are `gpt-5.5` (the codex/upstream default); change `model.optimizer` /
`model.target` in `config.yaml` for another slug your subscription serves.

`--optimizer_backend codex_chat` is passed explicitly here so it shows in the audit
record; omit it and the wrapper **injects** it (codex → `codex_chat`). The raw run
dir (`outputs/`) is gitignored; the curated `trace/` is committed.

## Stayed on the subscription (verified)

- `trace/oauth_runs.jsonl` (`handoff`): `provider: codex`, `preflight.verdict:
  oauth`, `OPTIMIZER_BACKEND: codex_chat`.
- `trace/config.resolved.json`: `optimizer_backend: codex_chat`, `target_backend:
  codex_exec`.
- `trace/summary.json` `token_summary`: usage attributed to `rollout` (target) and
  `analyst` (optimizer) stages only — no azure/openai stage.
- A secret-leak grep over the outputs returns nothing; the env scrub strips every
  `*_API_KEY` / `*_AUTH_TOKEN`, so a mis-route to a metered backend would fail
  closed rather than bill.

## Files

```
config.yaml              # the run config (codex/codex, gpt-5.5, tiny loop)
seed_skill_bad.md        # the deliberately-bad seed prompt
data/{train,val,test}/   # tiny fictional-fact QA split (answers only in context)
trace/                   # committed before→after artifacts:
  skill_v0000_BEFORE.md  #   the seed
  best_skill_AFTER.md    #   the optimized skill
  history.json           #   per-step accept/reject/score
  summary.json           #   baseline vs best, held-out test
  config.resolved.json   #   proof of routing
  oauth_runs.jsonl       #   the guard's audit record
```
