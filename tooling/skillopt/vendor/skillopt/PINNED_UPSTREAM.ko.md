# Vendored upstream: Microsoft SkillOpt

[English](PINNED_UPSTREAM.md)

이 트리는 upstream [microsoft/SkillOpt](https://github.com/microsoft/SkillOpt)의 **trimmed, pinned snapshot**입니다. upstream release 전에 이 repository에서 로컬 CLI backend wiring을 담을 수 있도록 vendoring했습니다.

- **Pinned ref:** `v0.1.0` (commit `25da7cb2ddc26eb67eb6cb386915f269d7ee42cf`)
- **Vendored subset:** `skillopt/`, `scripts/`, `configs/`, `data/`, `pyproject.toml`, `requirements.txt`, `README.md`, `LICENSE`, `SECURITY.md`.
  runtime package가 import하지 않는 항목은 제외했습니다: `skillopt-assets/`, `skillopt_webui/`, `docs/`, `ckpt/`, `*.html`, `mkdocs.yml`, upstream `tests/`.
- **Install:** `tooling/skillopt/pyproject.toml`의 editable workspace source(`[tool.uv.sources] skillopt = { workspace = true, editable = true }`)를 사용합니다. 따라서 `uv sync`가 이 트리를 빌드하고 `skillopt-train` console script를 제공합니다.

## upstream 대비 로컬 delta

로컬 변경은 additive입니다. `codex_chat` 옵티마이저와 `pi`(Earendil) backend를 추가하고, config와 trainer wiring을 연결했습니다.

**`codex_chat` optimizer:**

- `skillopt/model/__init__.py` — `codex_chat` optimizer를 `codex_backend`으로 dispatch하고 deployment/reasoning-effort setter를 연결합니다.
- `skillopt/model/backend_config.py` — `codex_chat`을 optimizer backend로 허용합니다.
- `skillopt/model/common.py` — `codex_chat` 기본 모델.

**`pi` backend(`pi_chat` + `pi_exec`):**

- `skillopt/model/pi_backend.py` — NEW: pi(Earendil) CLI backend입니다. `pi_chat`은 one-shot `pi -p --mode json --no-tools` optimizer/chat-target이고, `pi_exec`는 agentic `pi -p --mode json` rollout target입니다. JSONL stream parsing, pi→SkillOpt usage mapping(pi의 `totalTokens`를 source of truth로 사용), stream-derived success(pi exit code는 신뢰할 수 없음), billing guard(`PiBillingError`, `_assert_allowed_provider`, `_guard_provider`)를 포함합니다.
- `skillopt/model/__init__.py` — `pi_chat`(optimizer + chat-target)을 dispatch하고 deployment/reasoning-effort setter를 전달합니다. `pi`/`pi_exec`용 `set_backend`/`get_backend_name` legacy compatibility도 포함합니다.
- `skillopt/model/backend_config.py` — `pi_chat`(optimizer + target)과 `pi_exec`(target)를 허용합니다. `configure_pi_exec`/`get_pi_exec_config` 및 `PI_EXEC_*` constants를 추가합니다.
- `skillopt/model/common.py` — `pi`/`pi_chat`/`pi_exec` 기본 모델과 alias.
- `skillopt/model/codex_harness.py` — `run_target_exec`에 `pi_exec` branch를 추가합니다(`run_pi_exec` lazy import).
- `configs/_base_/default.yaml` — 사용자가 pi를 opt in할 때만 읽히는 inert `pi_exec_*` 및 `pi_allowed_metered_providers` key.
- `skillopt/config.py`, `scripts/train.py`, `skillopt/engine/trainer.py`, `scripts/eval_only.py` — `pi_exec_*` 및 `configure_pi_exec` config/env wiring.

pi tests와 `skillopt-oauth` wrapper tests는 이 vendored tree 바깥에 있습니다.

## 새 upstream으로 re-vendor / rebase

1. `git clone --depth 1 --branch <new-tag> https://github.com/microsoft/SkillOpt`.
2. 위 vendored subset 목록과 같은 항목을 이 트리 위에 다시 복사합니다.
3. 로컬 delta를 다시 적용합니다. patch commit을 cherry-pick하거나 작고 self-contained한 `skillopt/model/` edits를 replay합니다.
4. 위 pinned ref를 업데이트하고 `uv sync`와 test suite를 실행합니다.
