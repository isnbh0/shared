# Vendored upstream: Microsoft SkillOpt

This tree is a **trimmed, pinned snapshot** of upstream
[microsoft/SkillOpt](https://github.com/microsoft/SkillOpt), vendored so this
repository can carry local CLI backend wiring before an upstream release.

- **Pinned ref:** `v0.1.0` (commit `25da7cb2ddc26eb67eb6cb386915f269d7ee42cf`)
- **Vendored subset:** `skillopt/`, `scripts/`, `configs/`, `data/`,
  `pyproject.toml`, `requirements.txt`, `README.md`, `LICENSE`, `SECURITY.md`.
  Dropped (not imported by the runtime package): `skillopt-assets/`,
  `skillopt_webui/`, `docs/`, `ckpt/`, `*.html`, `mkdocs.yml`, upstream `tests/`.
- **Install:** editable workspace source from `tooling/skillopt/pyproject.toml`
  (`[tool.uv.sources] skillopt = { workspace = true, editable = true }`), so
  `uv sync` builds this tree and provides the `skillopt-train` console script.

## Local delta vs. upstream

The local changes are additive: a `codex_chat` optimizer plus the `pi`
(Earendil) backend, with config and trainer wiring.

**`codex_chat` optimizer:**

- `skillopt/model/__init__.py` — dispatch `codex_chat` optimizer to
  `codex_backend`; wire its deployment/reasoning-effort setters.
- `skillopt/model/backend_config.py` — allow `codex_chat` as an optimizer backend.
- `skillopt/model/common.py` — `codex_chat` default model.

**`pi` backend (`pi_chat` + `pi_exec`):**

- `skillopt/model/pi_backend.py` — NEW: the pi (Earendil) CLI backend. `pi_chat`
  (one-shot `pi -p --mode json --no-tools` optimizer/chat-target) and `pi_exec`
  (agentic `pi -p --mode json` rollout target). Includes JSONL stream parsing,
  pi→SkillOpt usage mapping (pi's `totalTokens` as source of truth), stream-derived
  success (pi's exit code is unreliable), and the billing guards (`PiBillingError`,
  `_assert_allowed_provider`, `_guard_provider`).
- `skillopt/model/__init__.py` — dispatch `pi_chat` (optimizer + chat-target) and
  forward its deployment/reasoning-effort setters; `set_backend`/`get_backend_name`
  legacy compat for `pi`/`pi_exec`.
- `skillopt/model/backend_config.py` — allow `pi_chat` (optimizer + target) and
  `pi_exec` (target); `configure_pi_exec`/`get_pi_exec_config` + `PI_EXEC_*` constants.
- `skillopt/model/common.py` — `pi`/`pi_chat`/`pi_exec` default model + aliases.
- `skillopt/model/codex_harness.py` — `run_target_exec` gains a `pi_exec` branch
  (lazy import of `run_pi_exec`).
- `configs/_base_/default.yaml` — inert `pi_exec_*` + `pi_allowed_metered_providers`
  keys (read only when a user opts into pi).
- `skillopt/config.py`, `scripts/train.py`, `skillopt/engine/trainer.py`,
  `scripts/eval_only.py` — config/env wiring for `pi_exec_*` + `configure_pi_exec`.

The pi tests and `skillopt-oauth` wrapper tests live outside this vendored tree.

## Re-vendoring / rebasing onto a newer upstream

1. `git clone --depth 1 --branch <new-tag> https://github.com/microsoft/SkillOpt`.
2. Re-copy the vendored subset over this tree (same item list as above).
3. Re-apply the local delta (cherry-pick the patch commit, or replay the
   `skillopt/model/` edits — they are small and self-contained).
4. Update the pinned ref above and run `uv sync` + the test suite.
