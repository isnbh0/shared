# SkillOpt-OAuth — Design

This document is the durable context for the tool: what it is for, the
constraints that shape it, and the design choices it makes — especially relative
to upstream Microsoft SkillOpt. It describes the system as it is today. For a
runnable walkthrough see [`examples/timestamp_optimize/`](../examples/timestamp_optimize/README.md);
for usage see [`../README.md`](../README.md).

---

## 1. Intent

SkillOpt-OAuth runs the SkillOpt skill-optimization algorithm with **every** LLM
call — rollout, reflect/optimizer, and judge — dispatched through the OAuthed
`claude` / `codex` CLIs on **subscription** sessions, never through metered
provider API keys and never through the raw Messages API.

**What SkillOpt is.** Microsoft SkillOpt ("ReflACT") treats a markdown **skill
document** as the thing being trained for a frozen LLM agent, and improves it
with an ML-shaped loop: `epoch → batch → rollout → score → reflect/patch under a
learning-rate edit budget → validation gate → best_skill.md`. Upstream already
ships CLI-shelling backends, so "route everything through subscription CLIs" is
mostly a matter of making that the *only* path and hardening it.

**Why OAuth-CLI.** Agentic rollouts are token-heavy; a subscription is roughly
10–50× cheaper than metered API for this workload, and keeps spend inside a
predictable plan instead of a per-token bill.

**Goals.**
1. Funnel every rollout/reflect/judge call through a single OAuth-asserted
   chokepoint (§3.1).
2. Drive the SkillOpt loop from a long-lived Python controller that itself makes
   **zero** LLM calls — all calls are dispatched to provider pools.
3. Parallelize to the limit the algorithm permits, with real backpressure (§3.3–§3.4).
4. Harden the validation gate against CLI nondeterminism (§5.3).
5. Dogfood the repo's own skills as benchmark envs — `timestamp` and
   `spex:write-phased`, both with clean deterministic scorers.

**Non-goals.** Single-box only (no distributed scheduling). Deterministic-scorer
envs only for now (LLM-judge envs are deferred). The controller is never a
dynamic multi-agent workflow — a workflow may appear one level *down*, when the
skill *being optimized* orchestrates subagents, but never as the harness itself.

---

## 2. Relationship to upstream SkillOpt

The guiding principle is **"fork, don't reimplement"**: keep SkillOpt's tested ML
core untouched and extend only at the backend execution seam. It is important to
be precise about how far that principle is realized today.

**Today the fork forks the *shape* and reimplements the *substance*.** The
package is self-contained: it does **not** import a single line of upstream
SkillOpt at runtime. It mirrors SkillOpt's loop shape (epoch → batch → rollout →
score → reflect-under-LR → gate → checkpoint), its LR-decay schedule
(`loop.lr_at`), its gating concept, its frozen validation split, and the
`EnvAdapter` / `SplitDataLoader` surface — all in local code.

Two **upstream-integration seams** exist and are deliberately **dormant**:

| Seam | Where | Current state | Enable by |
| --- | --- | --- | --- |
| Env base classes | `base.py` `try: from skillopt.envs import EnvAdapter, SplitDataLoader except Exception:` | The `except` fallback runs — local `abc.ABC`s with the fork's surface | Pin `skillopt`; the `try` import then wins |
| Reflection proposer | `reflect.make_upstream_propose_fn` (wraps `gradient.run_minibatch_reflect` *unmodified*) | Defined but **never called**; the shipped proposer is `train.py:make_propose_fn` | Wire `make_upstream_propose_fn` into `LoopDeps.propose_fn` |

The upstream dependency is **commented out** in `pyproject.toml`
(`# "skillopt==<PINNED_VERSION>"`), and only `pyyaml` is actually installed.
Running self-contained is what makes `uv sync` work offline and keeps the test
suite hermetic.

**Surface caveat.** The local `EnvAdapter`/`SplitDataLoader` define the fork's
*intended* contract (`build_train_env` / `build_eval_env` / `rollout` /
`get_task_types`; deliberately **no `evaluate()`** — deterministic scoring lives
in each env's `scorer` + `run_batch`). If a pinned upstream exposes a different
surface (e.g. requires `evaluate()`), confirm the real import path/surface before
relying on it; the tests pass on the fallback regardless.

**Bottom line for a reader:** treat this as a standalone harness that *preserves
SkillOpt's algorithm shape and semantics*, with documented seams to delegate to
the real upstream code once a version is pinned.

---

## 3. Constraints

### 3.1 OAuth-only billing — the load-bearing constraint

Metered-API fallback is meant to be **impossible by construction, not by
convention.** `OAuthCLIExecutor.run_cli` is the single chokepoint every call
flows through; there is deliberately no API or chat code path in the package. The
guards, and why each exists:

- **Child-env scrub** (`_build_child_env`). Drop every variable whose name ends
  in `_API_KEY` or `_AUTH_TOKEN` (plus explicit pops of `ANTHROPIC_API_KEY`,
  `ANTHROPIC_AUTH_TOKEN`, `OPENAI_API_KEY`, `CODEX_API_KEY`) from the **child**
  environment. *Why:* in `claude -p` mode a present `ANTHROPIC_API_KEY` **always**
  overrides the OAuth session and silently bills metered API (a Max subscriber
  reportedly hit \$1,800 in two days this way). The parent env is left untouched;
  `CLAUDE_CODE_OAUTH_TOKEN` (an OAuth token from `claude setup-token`, not an API
  key) survives the scrub for claude and is never handed to codex.
- **Fail-closed OAuth preflight** (`_preflight`, memoized per provider). A probe
  must resolve to `'oauth'`; any other verdict (`'api_key'`, `'none'`) **raises**
  rather than risk a silent metered call. The probe: claude →
  `CLAUDE_CODE_OAUTH_TOKEN`, else `~/.claude/.credentials.json` `subscriptionType`,
  else the macOS login-Keychain item `Claude Code-credentials`; codex →
  `~/.codex/auth.json` `auth_mode == 'chatgpt'`. The keychain check is
  existence-only (no `-g`/`-w`) because decrypting the secret can pop an ACL
  prompt that would hang a headless run. The probe is injectable so tests stay
  hermetic.
- **Never `--bare`** (`_guard_no_bare`). `claude --bare` bypasses OAuth/keychain
  and *requires* an API key, and is slated to become the `-p` default in a future
  release. The executor never constructs it; the guard fails loudly if a future
  change ever sneaks it into argv.
- **CLI version pinning.** Pin the `claude`/`codex` versions so the future
  bare-default flip (or any auth-precedence change) cannot alter billing silently.
- **Auth/billing warning detection** (`_AUTH_BILLING_RE`). Scan stdout+stderr; a
  hit sets `CliResult.auth_billing_warning`, which the scheduler treats as a
  fatal, **non-retryable** `AuthBillingError` even on a clean (exit 0) run —
  retrying would re-run the same metered call. The regex is deliberately narrow
  (matches real signatures like "credit balance", "rate limit", "billed to your
  API credits", "ANTHROPIC_API_KEY detected") so a model's benign prose or a JSON
  `modelUsage` field cannot false-positive and abort a good run.
- **Model assertion** (`_assert_model`). Recover the model that actually ran (the
  `[[SKILLOPT_MODEL:…]]` marker, else claude's `--output-format json` `modelUsage`
  key). A same-family alias (`opus` vs `claude-opus-4-8`) matches; a cross-family
  report (pinned `opus`, ran `haiku` — a silent downgrade) raises. Absence is
  non-fatal; only a contradiction is.

**This is a moving target — re-verify before long runs.** Verified 2026-06-30:
`claude -p` (Claude Code 2.1.195, Max keychain) and `codex exec` (ChatGPT OAuth,
`auth_mode=chatgpt`) both bill to subscription. But Anthropic *announced*
(effective 2026-06-15) moving Agent SDK + `claude -p` + GitHub Actions onto
separate metered credits, then **paused it on the due date** and is reworking it —
reverted, not shipped, but explicitly targeted. Weekly caps also apply to headless
automation (checkpoint/resume is what survives them). Codex unattended
subscription tokens are Business/Enterprise-only; personal plans rely on a seeded
`auth.json` sharing the human's quota.

### 3.2 Dual identity

Two OAuth identities, each a separate usage cap. Defaults route rollouts +
validation to `claude` and reflect/judge to `codex` (`rollout_provider="claude"`,
`reflect_provider="codex"`). This is both throughput (≈2× by splitting load
across caps) and a **strategic hedge**: if the metered split re-ships for one
vendor, route everything to the other (`codex exec` is a different vendor/policy)
without ever touching an API key.

### 3.3 Concurrency only where the math permits

Fan out rollouts, validation evals, and minibatch *proposals*; serialize
steps/epochs and the gate critical section, because each step depends on the
gated skill. The controller (`loop.py`) makes zero LLM calls itself — every call
is dispatched to a provider pool via injected `rollout_fn` / `propose_fn`.

### 3.4 Backpressure is mandatory

Theoretical max ≠ realizable max. Concurrency must be realized with per-provider
semaphores, token-bucket pacing, exponential backoff + full jitter, and a circuit
breaker (§4.2) — not just a high fan-out number.

### 3.5 Hermetic testing

Tests never call a real CLI or touch real OAuth. A stub CLI fixture stands in for
both binaries; the OAuth probe and the scheduler's clock/sleep are injectable.
`train.py` exposes `--stub` and `--fake-oauth` for an offline smoke. The suite is
the correctness signal (126 tests).

---

## 4. The execution layer (real-CLI contract)

### 4.1 The chokepoint and per-provider commands

Every call is one `OAuthCLIExecutor.run_cli`. Command construction is provider-
and role-aware (`allow_writes` is set for rollouts, which must create files, and
left off for reflect, which only emits text):

| | claude (rollout) | codex (reflect) |
| --- | --- | --- |
| base | `claude -p <prompt> --output-format json` | `codex exec -s <sandbox> --skip-git-repo-check` (prompt on stdin) |
| writes | `--permission-mode acceptEdits` (when `allow_writes`) | `-s workspace-write` vs `read-only` |
| model/effort | `--model <m>` (if pinned) | `-c model_reasoning_effort=<e>` (omitted if unset), `-c model=<m>` (if pinned) |

`--output-format json` makes claude's stdout a single machine-readable result
object, which is also how the model that ran is recovered (`modelUsage` keys —
there is no top-level `model` field).

### 4.2 The bounded async scheduler

One `ProviderPool` per provider (per OAuth identity):

- **Hard concurrency ceiling** — `asyncio.Semaphore(max_concurrency)` (default
  `claude_pool=6`, `codex_pool=6`).
- **Token bucket** — `rate_per_min/60` tokens/sec (default 60/min), below the
  provider cap; clock/sleep injectable for fake-clock tests.
- **Bounded admission queue** — `maxsize = max(1, max_concurrency*8)`; blocks when
  full → backpressure.
- **Exponential backoff + full jitter** — `uniform(0, min(max_backoff,
  base_backoff·2^(attempt-1)))`; defaults `base_backoff=2.0`, `max_backoff=60`,
  `max_retries=5`.
- **Circuit breaker** — closed → open after 5 consecutive failures → fails fast →
  after 30s admits one half-open probe → closes on success.
- **Adaptive concurrency** — a rate-limit streak shrinks the *effective* limit
  (halve, floor 1); a sustained OK streak restores it. Enforced by parking
  permits out of the semaphore, so the hard ceiling always holds.
- **Classification seam** (`classify_cli_result`) — exit 0 + no warning → success;
  exit 0 + `auth_billing_warning` → `AuthBillingError` (fatal, fail-closed); 429 /
  rate-limit marker → `RateLimitError` (retryable + shrink); other nonzero incl.
  the timeout sentinel `124` → `TransientError` (retryable). Resilience engages
  only for jobs built via `cli_job` (which runs this classifier); the shipped
  `rollout_fn`/`propose_fn` and the timestamp adapter all route through it.

### 4.3 Real-CLI realities the wiring encodes

These are non-obvious facts about the headless CLIs that the execution layer is
built around (each was verified against the live CLIs):

- `ANTHROPIC_API_KEY` wins over OAuth in `-p` mode — hence the child-env scrub.
- On macOS the claude subscription credential lives in the login Keychain
  (`Claude Code-credentials`), not a file.
- Real `claude` does **not** auto-load a workspace `.agents/skills/` dir, so the
  candidate skill is **inlined into the rollout prompt** (`_rollout_prompt`); the
  model is told to create artifacts at the workspace top level for the scorer.
- The edit engine is **line-based** (§5.2), so the reflect prompt instructs
  single-line anchors and prefers an anchor-free append; reflect output (which may
  be prose-wrapped) is reduced to its JSON object before parsing.
- codex's ChatGPT login wins over `OPENAI_API_KEY`; `codex exec` stdout is the
  final message (not JSON); `model_reasoning_effort` accepts `minimal|low|medium|
  high` (not `xhigh`, which is a Claude-ism).

---

## 5. The optimization algorithm (and where it diverges from stock)

### 5.1 The loop

`step` = sample a batch → run `n_samples` rollouts per task and score → reflect →
**gate critical section** (re-baseline the prior skill, evaluate the candidate on
the frozen val split, decide) → on accept, swap the skill and maybe emit
`best_skill.md` → advance cursors → write-ahead checkpoint. Steps and epochs are
sequential; everything inside a step that can fan out, does.

### 5.2 Reflection — the one stated fidelity compromise

> Stock SkillOpt applies minibatch reflections **sequentially** against an
> evolving skill. We parallel-**propose** edits across minibatches against the
> **same** pre-step skill, then deterministically **merge** under the global LR
> edit budget. This changes optimization dynamics slightly but is the only way to
> parallelize reflection; the merge enforces the same LR budget.

`reflection_mode: sequential` recovers exact stock behavior (apply each
minibatch's proposal to the evolving doc in order, decrementing the shared budget,
stopping when exhausted). The merge/clamp/apply layer is the fork's own and fully
deterministic (no LLM): dedup by `op_id`, global sort by `(kind, anchor, text)`,
hard-clamp to `flat[:lr]`, fixed apply order (deletes → replaces → adds).

**Edit-op contract (shipped path):** `{"kind": add|delete|replace, "anchor": str,
"text": str}`, applied **line-based** — `add` appends `text` as a new line
(`anchor: ""`) or after the first line containing `anchor`; `delete`/`replace`
act on the first line containing `anchor`. An op whose anchor matches no line is a
silent no-op. The parser accepts a bare array or `{"edits": [...]}`; malformed
payloads get one optional repair retry, else are dropped.

> **Two edit-op schemas live in the tree — know which is active.** The shipped
> reflection path uses `{kind, anchor, text}` (above). A *dormant* path
> (`backends.py`'s `run_reflect`, validated by `executor.validate_patch` /
> `parse_patch_json`) uses a different shape, `{op, target, content}`. Nothing on
> the live loop imports `backends.py`; treat its schema as off-path until/unless
> that backend is wired in.

### 5.3 The gate — variance-aware acceptance

The CLI execution layer has no temperature/seed knob, so a single-sample `>` gate
would accept measurement noise and let the skill degrade. Modes (`gate_mode`):

- **variance** (default): accept iff `mean(val_new) − mean(val_old) > max(2·σ_gate,
  1/M)`, with `M = len(val_tasks)`.
- **strict**: `mean(val_new) > mean(val_old)` — reproduces stock SkillOpt's
  single-sample gate.
- **paired**: the variance threshold **and** an exact binomial sign-test `p < 0.05`.

`σ_gate` is **A/A-calibrated per epoch** (`calibrate_sigma_gate`): evaluate the
*same* skill over val twice with caching bypassed (else the second run returns the
cache and σ is trivially 0), and take `pstdev` of the per-task deltas. With fully
deterministic scorers σ collapses to 0 and the `1/M` floor dominates — exactly as
intended. Supporting hardening: `n_samples` self-consistency (`aggregate_samples`:
hard = majority vote, soft = median), a paired **re-baseline** of the prior skill
under the *current* model each step (never trust a stale stored score), and a
result cache keyed by `(skill_hash, task_id, model, provider)` so the cache can
never mask model/CLI drift.

### 5.4 Deterministic scorers, not an LLM judge

The gate is only meaningful when scoring is low-variance, so envs use pure-Python
scorers (regex / structure / schema) and reserve LLM judges for when they are
unavoidable. `timestamp`: hard = 1 iff every produced top-level name matches
`^\d{6}-\d{6}-` and at least `min_artifacts` were produced; soft = fraction
matching. `spex_write_phased`: a structure + required-headers + phase-marker
check. Both yield zero gate noise.

### 5.5 Write-ahead checkpoint / resume

A complete `TrainState` (skill doc, step/epoch, data cursor, RNG state, best
score + best skill, result cache) is persisted **after every step**, written
atomically (tmp file + `fsync` + `os.replace`); `best_skill.md` is emitted the
same way. An interrupted write never corrupts the WAL — on resume the in-flight
step is simply recomputed (it left no committed state). Guarantee: a completed run
resumes to a no-op; a run interrupted mid-epoch resumes from the last committed
step and deterministically reproduces the uninterrupted result. Operationally this
is what lets a run survive a weekly-cap interruption.

---

## 6. Configuration model

Three namespaces describe one run and are reconciled in
`train.reconcile_loop_config` with precedence **explicit override > env YAML > P1
`Config` default**:

- **`Config`** (`config.py`, flat) — pools, rates, retries, LR, reflection mode,
  model pins, `reasoning_effort` (default `high`).
- **env YAML** (`configs/<env>/default.yaml`, nested) — providers, `rollout.n_samples`,
  `train.batch_size`/`split_seed`, `loader.val_fraction`, `gate.mode`, paths.
- **`LoopConfig`** (`loop.py`) — the canonical shape the loop consumes.

Every knob worth changing for a run is also a CLI flag (`--batch-size`,
`--n-samples`, `--val-n-samples`, `--initial-skill`, `--rollout-provider`,
`--reflect-provider`, `--reasoning-effort`, `--steps-per-epoch`, `--epochs`), so a
run can be shrunk, re-routed, or re-seeded without editing committed config.

---

## 7. Known risks & deferred features

**Open risks.**
- **Upstream surface assumption** (§2) — the local base-class fallback is the
  contract today; a pinned upstream may differ.
- **Three config namespaces coexist** — reconciled, but a field added to one must
  be threaded through the mapping (`reconcile_loop_config`).
- **Two edit-op schemas** (§5.2) — keep new reflection work on the `{kind, anchor,
  text}` path.
- **OAuth-headless billing is a moving target** (§3.1) — re-verify before long
  automated runs; the §3.1 guards are the defense in depth.
- **Stub writes no files** — the hermetic stub prints canned text but creates no
  artifacts, so the *real* deterministic scorer returns `hard=0` against it. The
  stub proves wiring, not optimization; the unit tests are the correctness signal,
  and `examples/timestamp_optimize/` is the real-optimization signal.

**Deferred (out of scope for now).** LLM-judge envs; vendoring/patching upstream
`gradient.py` beyond the wrap seam; multi-machine scheduling; a Claude
dynamic-workflow rollout backend (for the skill-orchestrates-subagents case);
committing run artifacts into git (`.agent-workspace/` is gitignored by repo
convention).

---

## 8. Testing posture

Hermetic by construction: a stub CLI stands in for both binaries; the OAuth probe
and scheduler clock/sleep are injectable; no test spends a real token. Coverage
spans the executor (command construction, env scrub, preflight, model assertion,
billing detection), the scheduler (pools, backoff, breaker, classification), the
gate (σ calibration, accept modes), reflection (parse/merge/apply determinism),
checkpoint/resume, the scorers, and the real-CLI compatibility paths. The
committed example (`examples/timestamp_optimize/`) is the one place an end-to-end
*real* optimization run is exercised — intentionally outside the hermetic suite.
