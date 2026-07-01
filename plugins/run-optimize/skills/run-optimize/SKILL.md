---
name: Optimizing Skills with SkillOpt
description: Optimizes an existing skill or prompt against a graded task set using the vendored SkillOpt supervised optimizer. User-invoked via /run-optimize; not auto-triggered.
argument-hint: "[path-to-seed-skill]"
disable-model-invocation: true
---

# Optimizing Skills with SkillOpt

Drive the vendored SkillOpt tooling to optimize an existing skill/prompt against a scored task set, then read the results and offer to write the improved skill back.

## When to use

Use this when the user has a skill or prompt and wants it made measurably better. SkillOpt is a **supervised** optimizer: it rewrites the skill to score higher on a graded task set (train/val/test). "Better" is only meaningful against that scored set. If there is no way to grade success, this skill cannot help — say so plainly and stop.

This is an interactive workflow. At every real decision point below, **ask the user in prose** and wait for their answer. Do not invent flags or run non-interactively.

## The crux, stated up front

The single hardest and most important part is **establishing graded tasks**. Everything else (backend, model, config knobs) is mechanical. If the graded set is wrong, the optimizer will confidently make the skill worse. Spend your effort here and be honest with the user about it.

## Configuration

The skill reads optional defaults from a config file. Resolution precedence (first match wins):

1. **Explicit override** — the user states a provider/model/backend/out_root for this run
2. **Local config** (`.agents/skill-configs/run-optimize/config.local.yaml`) — personal/local, gitignored
3. **Project config** (`.agents/skill-configs/run-optimize/config.yaml`) — project scope, committed
4. **Legacy fallback** (`.claude/skill-configs/run-optimize/config.local.yaml`, then `config.yaml`) — older installs; if found only here, use it and offer to move it to the new location
5. **Built-in default** — the subscription-safe codex path described below

See `config.example.yaml` beside this file for every supported field.

## Setup

1. If the user gives explicit choices for this run, use them and skip config lookup.
2. Otherwise check the config paths above in order.
3. **If no config is found**, tell the user:
   > "No run-optimize config found. I can proceed with the subscription-safe default (codex via the OAuth guard, model gpt-5.5) or you can pin a provider/model/backends. I'll write your choice to `.agents/skill-configs/run-optimize/config.yaml`. (See `config.example.yaml` for reference.)"
   Wait for their answer, then write the config before continuing. Every field is optional; anything unset falls back to the codex default.

## Workflow

Copy this checklist when running the skill:

```
SkillOpt Progress:
- [ ] Step 1: Load config / first-time setup
- [ ] Step 2: Identify the seed skill (record its path)
- [ ] Step 3: Establish graded tasks (the crux)
- [ ] Step 4: Choose the environment/scorer (QA vs custom) and confirm the success criterion
- [ ] Step 5: Choose chat vs exec target
- [ ] Step 6: Choose model/provider (subscription-safe default; GLM offer)
- [ ] Step 7: Scaffold the run workspace and write config.yaml (extends _base_, size the splits)
- [ ] Step 8: Confirm the resolved plan, then launch
- [ ] Step 9: Read the results
- [ ] Step 10: Offer to write best_skill.md back over the recorded seed
```

**Step 1 — Load config / first-time setup.** Follow the Setup section. Resolve the default provider, model, backends, out_root, and whether to use the guard.

**Step 2 — Identify the seed skill.** Ask which `.md` file to optimize, and **record its path** — this one path is both what the run reads (`env.skill_init`, Step 7) and the single write-back target (Step 10). If the user passed a path as an argument, confirm it. Read the seed so you understand what it does and how it is used — that informs Steps 4 and 5. Make sure the seed is under version control before you overwrite it in Step 10.

**Step 3 — Establish graded tasks (the crux).** Determine how success is scored, then get a task set with train/val/test splits.
- **If the user already has graded data**, use it. Confirm its shape matches the chosen environment (Step 4).
- **If they do not**, help them assemble a starter set. You may draft candidate tasks, but **flag clearly that AI-drafted or synthetic tasks must be human-reviewed before the optimization is trusted.** SkillOpt optimizes toward whatever the graded set rewards — a wrong gold answer or an unanswerable task teaches the skill the wrong lesson. For QA-shaped tasks specifically, every gold answer must be correct and actually findable in the task's `context`, because scoring compares the model's answer against the `answers` field.
- You need three splits: **train** (the optimizer learns from these), **val** (selection/gate), **test** (held-out final report). Keep them disjoint. Small is fine to start (the demos use 3/3/2).

**Step 4 — Choose the environment/scorer, and confirm the success criterion.** This fork is the one most likely to silently corrupt the whole run: if you grade a non-QA skill as if it were QA, the exact-match/F1 number measures nothing and the optimizer will "improve" the skill against a meaningless signal. So **propose a classification, then get the user to confirm the criterion before proceeding.**
- **Short-answer QA** (question + context → short answer): the built-in `searchqa` env grades it with normalized exact-match (hard score) and token-level F1 (soft score). Before committing to this path, ask the user directly: *"Is normalized exact-match / token-F1 against a short gold answer a faithful measure of this skill succeeding?"* **Only proceed on the QA path after an explicit yes.** No scoring code required.
- **Non-QA success** (e.g. a coding-agent skill where success = a task was completed correctly) — this is the likely-common case for this repo's own skills, and a first-class path, not an edge case. `searchqa` cannot score it; forcing it would grade the wrong thing. You need a **custom environment**, which does mean writing scoring code. Walk the user through it or hand it off honestly — do not fabricate a scorer or pretend `searchqa` fits. Skeleton:
  1. **Copy the template** (from `tooling/skillopt`): `cp -r vendor/skillopt/skillopt/envs/_template vendor/skillopt/skillopt/envs/<your_env>`. It ships `config_template.yaml`, `env_template.py`, `loader_template.py`, and `README.md`.
  2. **Rename files/classes** and **implement the TODO blocks** — the `rollout` scoring in `adapter.py` and `_normalize_item` in `loader.py` — following the template's `README.md`.
  3. **Register** the key in `_register_builtins()` in `vendor/skillopt/scripts/train.py`.
  Model it on an existing exec-style env: **`spreadsheetbench`** (`vendor/skillopt/skillopt/envs/spreadsheetbench/`) stages the skill and runs an agent with tools, then scores task completion — the closest analog to a coding-agent skill.
- **Get the authoritative env list at runtime; do not trust a frozen list.** The registry is dependency-gated (each built-in is imported behind a `try/except`), so the registered set varies by checkout. Inspect `_ENV_REGISTRY` in `vendor/skillopt/scripts/train.py`, or set a bogus `env.name` and read the tool's `Available: [...]` error. As an illustrative current snapshot, this checkout registers `alfworld, docvqa, livemathematicianbench, officeqa, searchqa, spreadsheetbench` — verify rather than assume.

**Step 5 — Choose chat vs exec target.** Pick by how the skill is really used, and ask the user to confirm:
- **Tool-using coding-agent skill → an `*_exec` target** (`codex_exec`, `claude_code_exec`, or `pi_exec`). Exec targets stage the skill as a real `.agents/skills/skillopt-target/SKILL.md` in an agent workspace with tools — the faithful mode for a skill that drives an agent.
- **Pure prompt → a `*_chat` target** (`openai_chat`, `claude_chat`, `qwen_chat`, `minimax_chat`, or `pi_chat`). Chat targets inject the skill as a system prompt, no skill file staged. Note: for codex the only valid target is `codex_exec` — `codex_chat` is optimizer-only and is rejected as a target backend.
- Pick the **optimizer backend** the same way; a `*_chat` optimizer is the norm (`codex_chat`, `claude_chat`, or `pi_chat`).
- Allowed sets — optimizer_backend: `openai_chat, claude_chat, codex_chat, qwen_chat, minimax_chat, pi_chat`; target_backend: `openai_chat, claude_chat, codex_exec, claude_code_exec, qwen_chat, minimax_chat, pi_chat, pi_exec`.

**Step 6 — Choose model/provider.** Default to the subscription-safe path; offer GLM.
- **Default (subscription-safe): codex via the OAuth guard.** `skillopt-oauth` runs an OAuth preflight and scrubs every `*_API_KEY` / `*_AUTH_TOKEN` from the environment so no metered API fallback is possible. Model `gpt-5.5`, backends `codex_exec` (target) + `codex_chat` (optimizer). The Claude subscription is the same path with `claude_code_exec` + `claude_chat`.
- **Offer: GLM via pi.** `zai/glm-5.2` on the `pi` backend is opt-in-metered but free on this user's setup. Launch with the `PI_ALLOW_METERED=zai` env var. Present this as an explicit opt-in, not the default.
- Set the model slug to something the chosen subscription/provider actually serves.

**Step 7 — Scaffold the run workspace and write config.yaml.** SkillOpt reads its inputs from files on disk, so materialize them before launching.
1. **Scaffold from a shipped demo** (from `tooling/skillopt`): `cp -r demo/searchqa_codex runs/<skill-name>` (or `demo/searchqa_pi` for the GLM path) — these are the canonical copy-me templates. Then remove the copied `outputs/`, `trace/`, and `seed_skill_bad.md`: you regenerate outputs and point at your own seed. What you keep is the `config.yaml` shape and the `data/{train,val,test}/` layout to fill.
2. **Materialize the graded tasks** from Step 3 into `runs/<skill-name>/data/train/items.json`, `.../val/items.json`, and `.../test/items.json` (schema below).
3. **Point at the real seed.** Set `env.skill_init` to the seed path you recorded in Step 2 — the user's actual file, not a copy. The run reads it there and Step 10 writes back to the same path. An absolute path or a path relative to `tooling/skillopt` both work.
4. **Write `config.yaml`** at `runs/<skill-name>/config.yaml` — **exactly two directories under `tooling/skillopt`** so the `_base_` relative path resolves — from the skeleton below, filling the model/backend block per Steps 5–6.
5. **Size the splits** — this is a hard requirement:
   - `train.train_size` must **exactly equal** the train-split item count, or be `0` (auto-derive). A mismatch raises a `ValueError` and the run aborts. Count the items yourself.
   - `evaluation.sel_env_num` ≤ val-split count and `evaluation.test_env_num` ≤ test-split count. These are soft-clamped (a too-large value silently uses all items, no error), but set them to the real counts for clarity. `0` means "use all items in the split."

**Step 8 — Confirm the resolved plan, then launch.** A run spends subscription quota (codex/claude) or metered budget (GLM) and takes real wall-clock; that spend is not reversible. Before launching, **summarize the resolved plan back to the user and get an explicit go-ahead**:
- provider and model slug,
- optimizer and target backends,
- `out_root` — it resolves as `<default_out_root>/<skill-name>/outputs/<run-tag>` (e.g. `runs/<skill-name>/outputs/run_codex`), where `<default_out_root>` comes from config (default `runs`) and `<run-tag>` names this run,
- the counted train / val / test split sizes.
Only after the user says go, run the exact command from the Launch section, from `tooling/skillopt` (run `uv sync` once first).

**Step 9 — Read the results.** From the `out_root` you passed, read:
- `best_skill.md` — the optimized skill
- `history.json` — full run history (per-step edits and scores)
- `skills/skill_vNNNN.md` — per-version snapshots
- the **baseline-vs-best on the held-out test split** printed at the end of the run
Summarize the delta for the user honestly. If best did not beat baseline on test, say so — do not overwrite the seed with a non-improvement.

**Step 10 — Offer to write the result back.** Ask the user before touching the seed. If they agree, copy `best_skill.md` over the seed path you recorded in Step 2 — the user's real file, **never a staged copy**. Show a diff first and confirm the seed is committed so the change is reversible.

## Config skeleton

Fill the placeholders. This extends the shared base and mirrors the demo configs.

```yaml
_base_: ../../vendor/skillopt/configs/_base_/default.yaml

model:
  optimizer: gpt-5.5              # a model slug your subscription/provider serves
  target: gpt-5.5
  optimizer_backend: codex_chat  # optimizer engine (see allowed sets in Step 5)
  target_backend: codex_exec     # exec = stages SKILL.md with tools; chat = system-prompt only
  reasoning_effort: low
  # codex-exec target knobs (present only for codex_exec):
  codex_exec_reasoning_effort: low
  codex_exec_sandbox: workspace-write

train:
  num_epochs: 1
  train_size: <N_TRAIN>          # MUST equal the train-split item count exactly (or 0 to auto-derive)
  batch_size: 1
  accumulation: 1
  seed: 0

gradient:
  minibatch_size: 1
  merge_batch_size: 1
  analyst_workers: 1
  max_analyst_rounds: 1
  failure_only: false

optimizer:
  learning_rate: 2               # edit_budget: max edits per step
  min_learning_rate: 2
  lr_scheduler: constant
  lr_control_mode: fixed
  skill_update_mode: patch       # deterministic apply, no extra optimizer call
  use_slow_update: false
  use_meta_skill: false

evaluation:
  use_gate: true
  gate_metric: soft              # accept incremental F1 gains
  sel_env_num: <N_VAL>           # <= val-split count (0 = use all)
  test_env_num: <N_TEST>         # <= test-split count
  eval_test: true

env:
  name: searchqa
  # paths below are relative to tooling/skillopt (the run working directory)
  skill_init: <path-to-your-seed.md>  # the real seed from Step 2; the run reads it here and Step 10 writes back here
  split_mode: split_dir
  split_dir: runs/<skill-name>/data   # must contain train/ val/ test/, each with items.json
  data_path: ""
  max_turns: 1
  max_completion_tokens: 16384
  workers: 4
  exec_timeout: 180
  limit: 0
```

**GLM variant** — replace the `model:` block with:

```yaml
model:
  optimizer: zai/glm-5.2
  target: zai/glm-5.2
  optimizer_backend: pi_chat
  target_backend: pi_exec
  reasoning_effort: low
  pi_exec_thinking: "off"             # quoted so YAML keeps the string
  pi_allowed_metered_providers: [zai] # see troubleshooting; prefer the PI_ALLOW_METERED env
```

**Claude subscription variant** — set `optimizer: claude-...`, `target: claude-...` to a slug your plan serves, `optimizer_backend: claude_chat`, `target_backend: claude_code_exec`.

**Ratio splits (alternative to split_dir).** If the user has a single `items.json` instead of pre-split folders, set `env.split_mode: ratio`, `env.data_path: <path/to/items.json>`, `env.split_seed: 0`, and `train.train_size: 0` (counts come from apportionment). **Ask the user for the `env.split_ratio` (train:val:test)** instead of assuming one — a supervised optimizer usually wants the most data in `train`, so a train-heavy split like `"6:2:2"` is a reasonable starting point. Confirm the apportionment leaves enough val/test items to be meaningful.

## Task data schema (searchqa)

For the `searchqa` environment, each split is a JSON **array** of items. `split_dir` layout:

```
data/
├── train/items.json
├── val/items.json
└── test/items.json
```

Each item has exactly these four fields:

```json
{"id": "t1",
 "question": "In what year was the Zorblax Prize first awarded?",
 "context": "[DOC] The Zorblax Prize ... was first awarded in 1973 ...",
 "answers": ["1973"]}
```

- `id` (str), `question` (str), `context` (str; passages, `[DOC]`-separated), `answers` (list of gold strings).
- Scoring: the model's answer (last `<answer>...</answer>`, else last non-empty line) is normalized SQuAD-style; `em` (exact match) → hard score, token-level `f1` → soft score, both against `answers`. So the gold answer must appear/be derivable from `context`.

## Launch (verified commands)

Run from the repo's `tooling/skillopt` directory. Do this once first:

```bash
cd tooling/skillopt
uv sync
```

**Subscription-safe (codex via the OAuth guard) — the default:**

```bash
unset CODEX_PROFILE OPENAI_API_KEY AZURE_OPENAI_API_KEY ANTHROPIC_API_KEY
export SKILLOPT_OAUTH_LOG_DIR=runs/<skill-name>/outputs/_oauth_log
uv run skillopt-oauth \
  --config runs/<skill-name>/config.yaml \
  --target_backend codex_exec --optimizer_backend codex_chat \
  --out_root runs/<skill-name>/outputs/run_codex
```

For the Claude subscription, swap the backend flags: `--target_backend claude_code_exec --optimizer_backend claude_chat`. The guard also accepts a minimal form: `uv run skillopt-oauth --backend claude_code_exec --config <cfg>`.

**GLM via pi (opt-in metered, free here) — the direct trainer:**

```bash
PI_ALLOW_METERED=zai uv run skillopt-train \
  --config runs/<skill-name>/config.yaml \
  --out_root runs/<skill-name>/outputs/run_glm
```

To run GLM under the guard instead, **signal pi on argv** (not just in config) plus the env var:

```bash
PI_ALLOW_METERED=zai uv run skillopt-oauth \
  --config runs/<skill-name>/config.yaml \
  --target_backend pi_exec --optimizer_backend pi_chat \
  --out_root runs/<skill-name>/outputs/run_glm
```

`skillopt-train` (the vendored console script) and `skillopt-oauth` (the guard wrapper) are the supported entry points. Do not invoke `python scripts/train.py` directly — that path is fragile.

## Troubleshooting

- **`Configured train_size=... does not match loaded train split size=...`** — set `train.train_size` to the exact train-split item count, or `0` to auto-derive.
- **Env not found / `Available: [...]`** — `env.name` must be a registered env. The live set is dependency-gated, so read it at runtime from the `Available: [...]` error or from `_ENV_REGISTRY` in `vendor/skillopt/scripts/train.py` (this checkout currently registers `alfworld, docvqa, livemathematicianbench, officeqa, searchqa, spreadsheetbench`). For anything else, build a custom env (Step 4).
- **`Missing '<name>/' subdirectory in split_dir`** — `split_dir` must contain `train/`, `val/`, and `test/`, each with a `*.json` array.
- **`Unsupported target backend: 'codex_chat'`** — `codex_chat` is optimizer-only; for codex the target must be `codex_exec`. See Step 5's allowed sets.
- **GLM run bills / gets refused, or opt-in is ignored** — `model.pi_allowed_metered_providers` is read from the **leaf `--config` only** (it does not follow `_base_` inheritance), so an opt-in inherited from a base config is missed. Prefer the `PI_ALLOW_METERED=zai` env var; it is authoritative and always wins.
- **Guard runs GLM as `claude` and skips pi enforcement** — the guard infers the provider from argv/env, not the config file. Put `--target_backend pi_exec --optimizer_backend pi_chat` on argv (or set `SKILLOPT_OAUTH_TARGET=pi`) so pi is actually preflighted and gated.
- **OAuth preflight fails (guard returns exit 2, writes a `refused` record)** — you are not on a valid subscription session for the provider, or a stale key is set. Log into the codex/claude CLI and ensure `*_API_KEY` vars are unset (the guard scrubs them, but the `unset` line above makes intent explicit).
- **`best_skill.md` did not beat baseline on test** — do not overwrite the seed. Report the non-improvement and consider revisiting the graded tasks (Step 3) or loop sizing.

## Notes

- Ask at every genuine decision point (seed, tasks, success criterion, env, target, provider, pre-launch plan, write-back). Recommend the default and let the user redirect.
- Synthetic/AI-drafted tasks are a liability until a human reviews them. State this every time you draft tasks.
- Paths in the config and the launch commands are relative to `tooling/skillopt`; the `_base_` path is relative to the config file's own directory (two levels up to `tooling/skillopt`).
- Keep the seed skill under version control before Step 10 so the write-back is reversible.