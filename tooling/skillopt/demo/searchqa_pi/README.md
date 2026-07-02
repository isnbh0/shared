# Before→after demo: optimizing a prompt on pi, routed to zai/glm-5.2

[한국어](README.ko.md)

A worked SkillOpt run where **both** legs — the target (`pi_exec`) and the optimizer
(`pi_chat`) — run through the `pi` CLI on **`zai/glm-5.2`**. It starts from a
deliberately-bad seed prompt and traces how the `pi_chat` optimizer rewrites it.
(The pi analog of [`searchqa_codex`](../searchqa_codex).)

The target leg is agentic: `pi_exec` loads one skill and runs GLM-5.2 with tools on,
one rollout per task. The optimizer leg is a single-shot `pi_chat` completion on the
same model. The provider/model comes from the `zai/glm-5.2` deployment slug, and a
runtime guard verifies that `zai`/`glm-5.2` actually served every response.

## Result

Held-out **test** set:

| | exact-match | token-F1 |
| --- | --- | --- |
| **before** (bad seed) | **0.00** | 0.11 |
| **after** (optimized) | **1.00** | 1.00 |

`+1.00` exact-match, accepted at step 2, in **198s / 16 pi calls / 54,259 tokens** —
all on `zai/glm-5.2`. (`trace/summary.json`.)

## What the optimizer did

The task ([SearchQA](../../vendor/skillopt/skillopt/envs/searchqa)) scores the text
inside `<answer>…</answer>` with SQuAD exact-match / F1. The seed
(`trace/skill_v0000_BEFORE.md`) is **actively wrong**: it forces a full explanatory
sentence *inside* the answer tags, which can never exact-match the short gold span —
so baseline EM is 0.

The `pi_chat` optimizer (GLM-5.2) diagnosed this from the failed rollouts and
**inverted** the instruction (`trace/best_skill_AFTER.md`):

> **before:** "always write a complete, polished explanation rather than a short
> label … put your full explanation INSIDE `<answer>` … at least 15 words … Never
> put a bare word."
>
> **after:** "put ONLY the concise final answer inside `<answer>` … as brief as
> possible — typically a single word, number, or short phrase … Do not write full
> sentences, restate the question, or add explanatory context."

`trace/history.json`: step 1 `reject` (candidate edit did not clear the gate), step 2
`accept_new_best` (selection 0→1.0), step 3 `skip_no_patches` (already optimal).

## Reproduce

```bash
cd tooling/skillopt
uv sync
PI_ALLOW_METERED=zai uv run skillopt-train \
  --config demo/searchqa_pi/config.yaml \
  --out_root demo/searchqa_pi/outputs/run_pi_pi
```

Requires a `pi` CLI (v0.79.10 here) with a `zai` provider entry serving `glm-5.2`.
Change `model.optimizer` / `model.target` in `config.yaml` for another `provider/model`
slug pi can serve. Never pass `--api-key` — pi resolves auth from its own provider
config.

`skillopt-train` is the direct trainer entry point (the `scripts.train:main` console
script), not the `skillopt-oauth` wrapper. `PI_ALLOW_METERED=zai` opts `zai` into the
allowed-metered provider set; the `config.yaml` key
`pi_allowed_metered_providers: [zai]` records the same policy. Use this only when
you intentionally allow that provider for the run. The run can also be launched
under `skillopt-oauth` with `PI_ALLOW_METERED=zai`. The raw run dir (`outputs/`)
is gitignored; the curated `trace/` is committed.

## Routed to zai/glm-5.2 (verified)

- `trace/config.resolved.json`: `optimizer_backend: pi_chat`, `target_backend:
  pi_exec`, `optimizer_model` / `target_model` both `zai/glm-5.2`.
- Every `pi` `message_end` event echoed `provider: "zai"` and `model: "glm-5.2"`; the
  `actual == intended` runtime guard (`_guard_provider`) checks that on every spawn and
  never tripped (a mismatch raises a non-retryable `PiBillingError` that aborts the run).
- `trace/routing_proof.txt`: the config backends plus the provider/model harvested from
  the persisted `pi` JSON streams (all `zai`/`glm-5.2`) and the guard status.
- `trace/summary.json` `token_summary`: usage attributed to `rollout` (the `pi_exec`
  target) and `analyst` (the `pi_chat` optimizer) stages only.

## Files

```
config.yaml              # the run config (pi_chat optimizer + pi_exec target, zai/glm-5.2, tiny loop)
seed_skill_bad.md        # the deliberately-bad seed prompt
data/{train,val,test}/   # tiny fictional-fact QA split (answers only in context)
trace/                   # committed before→after artifacts:
  skill_v0000_BEFORE.md  #   the seed
  best_skill_AFTER.md    #   the optimized skill
  history.json           #   per-step accept/reject/score
  summary.json           #   baseline vs best, held-out test
  config.resolved.json   #   resolved config (pi_chat/pi_exec, zai/glm-5.2)
  routing_proof.txt      #   provider/model served + guard status
```
