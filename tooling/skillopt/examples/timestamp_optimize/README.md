# Example: optimizing the `timestamp` skill on real OAuth CLIs

A minimal, end-to-end run of the optimizer against live `claude` and `codex`
subscriptions. It starts from a deliberately **bad** initial skill and watches
the frozen-validation score climb from **0 → 1** as the loop learns the rule.

```bash
./run.sh                 # writes to ./run-out
```

Requires a subscription-OAuth `claude` login and a ChatGPT-OAuth `codex` login.
It spends real subscription tokens (~20 CLI calls, ~2 min). **No API keys are
used** — the executor scrubs every `*_API_KEY` / `*_AUTH_TOKEN` from the child
environment and fails closed unless an OAuth credential is confirmed (the macOS
Keychain item `Claude Code-credentials` for claude; `auth_mode: chatgpt` in
`~/.codex/auth.json` for codex).

## What the run does

`timestamp` rewards a skill that makes an agent prefix **every** new file and
folder with a `YYMMDD-HHMMSS-` timestamp. Scoring is deterministic (a regex over
the produced names — no LLM judge).

- **Initial skill** (`initial_bad.md`): tells the agent to use "short, clear,
  lowercase names" and never mentions timestamps → every rollout scores 0.
- **Rollout** (Claude identity): `claude -p` runs in a fresh workspace with
  `--permission-mode acceptEdits`, reads the inlined candidate skill, and creates
  the task's files. The scorer scans the workspace.
- **Reflection** (codex / ChatGPT identity): `codex exec` reads the current skill
  and the reward rule and returns an edit-op JSON patch improving it.
- **Variance gate**: after A/A-calibrating a noise floor `σ_gate`, it accepts a
  candidate only when `Δval > max(2·σ_gate, 1/M)`.

## A real run (captured)

```
done: env=timestamp epoch=1 step=2 best_score=1.0

== trajectory (frozen-val hard score per skill-doc hash) ==
best_score = 1.0   epoch = 1   step = 2   sigma_gate = 0.0
  skill-doc 2202c6b8:  mean_hard=0.000        # initial bad skill
      ts-val-01: hard=0 soft=0.0
      ts-val-02: hard=0 soft=0.0
      ts-val-03: hard=0 soft=0.0
  skill-doc 8613d45c:  mean_hard=1.000        # step 1 candidate -> gate ACCEPTS
      ts-val-01: hard=1 soft=1.0
      ts-val-02: hard=1 soft=1.0
      ts-val-03: hard=1 soft=1.0
  skill-doc d54ca798:  mean_hard=1.000        # step 2 candidate -> gate REJECTS (Δ=0)
      ts-val-01: hard=1 soft=1.0
      ts-val-02: hard=1 soft=1.0
      ts-val-03: hard=1 soft=1.0
```

Reading the trajectory:

- **Step 1** — the bad skill scores `val_old = 0`; reflection appends an
  assertive timestamp rule; the candidate scores `val_new = 1.0`. With a
  deterministic scorer `σ_gate = 0`, so the threshold is `1/M = 1/3`, and
  `Δ = 1.0 > 1/3` → **accept**. `best_skill.md` is written.
- **Step 2** — reflection proposes a further tweak; it also scores `1.0`, so
  `Δ = 0` is within the noise floor → **reject**. The run has converged; `best`
  stays at the step-1 skill. This shows the gate's selectivity, not just its
  acceptance.

## The learned skill (`best_skill.md`)

The accepted skill is the initial document plus the appended rule reflection
discovered:

```
# File naming

When creating files or folders for a task, give them short, clear, lowercase
names that describe their contents (for example: summary.md, notes.txt, drafts).
Keep names simple and human-readable.

Override all earlier naming guidance: EVERY file and folder you create for a task
MUST have a name beginning with an exact YYMMDD-HHMMSS- timestamp prefix (six
digits, dash, six digits, dash), e.g. 260630-142210-summary.md or
260630-142210-drafts; do not create any file or folder without this prefix.
```

## Files

| File | Purpose |
| --- | --- |
| `run.sh` | runs the loop, then prints the trajectory + learned skill |
| `initial_bad.md` | the deliberately bad starting skill |
| `show_trajectory.py` | renders the val-score trajectory from `checkpoint.json` |

## Shrinking or reshaping a run

Every knob is a flag (precedence: flag > env YAML > `Config` default), so no
committed config needs editing:

```bash
uv run python -m skillopt_oauth.train --env timestamp \
  --epochs 1 --steps-per-epoch 1 --batch-size 1 --n-samples 1 \
  --initial-skill ./initial_bad.md \
  --rollout-provider claude --reflect-provider codex \
  --out-dir ./run-out
```
