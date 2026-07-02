# SkillOpt Guard

[한국어](README.ko.md)

Run [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt) through local
agent CLIs with explicit routing, credential preflight, and secret scrubbing.

This directory contains two pieces:

- `SkillOpt Guard`, exposed as the `skillopt-oauth` command, around
  `skillopt-train`.
- `vendor/skillopt`, a pinned SkillOpt fork with local backend wiring for
  `codex_chat`, `pi_chat`, and `pi_exec`.

The guard keeps target rollouts and optimizer rewrites on the intended local CLI
path. It supports `claude`, `codex`, and `pi`.

## What the guard does

Before it hands off to `skillopt-train`, `skillopt-oauth`:

1. **Preflights credentials.** It verifies the selected provider can run with the
   intended local auth. For `claude`, it checks `CLAUDE_CODE_OAUTH_TOKEN`, the
   macOS Keychain item `Claude Code-credentials`, or
   `~/.claude/.credentials.json`. For `codex`, it checks `~/.codex/auth.json`
   with `auth_mode == "chatgpt"`. For `pi`, it checks the configured provider
   entry and the metered-provider opt-in rules below.
2. **Scrubs metered secrets.** It removes every `*_API_KEY` and `*_AUTH_TOKEN`
   from the child environment. `CLAUDE_CODE_OAUTH_TOKEN` is preserved because it
   is the Claude Code OAuth token.
3. **Routes both SkillOpt roles.** It sets the target backend and injects an
   optimizer backend unless you already supplied one.

Provider defaults:

| Provider | Target backend | Optimizer backend |
| --- | --- | --- |
| `claude` | `claude_code_exec` | `claude_chat` |
| `codex` | `codex_exec` | `codex_chat` |
| `pi` | `pi_exec` | `pi_chat` |

## Quick Start

```bash
cd tooling/skillopt
uv sync
uv run pytest
```

Run a guarded SkillOpt job:

```bash
uv run skillopt-oauth \
  --backend codex_exec \
  --config demo/searchqa_codex/config.yaml \
  --out_root demo/searchqa_codex/outputs/run_codex_codex
```

The provider is inferred from `--backend`, `--target_backend`, or
`--optimizer_backend`. You can pin it with
`SKILLOPT_OAUTH_TARGET=claude|codex|pi`.

If the preflight fails, the guard exits before launching `skillopt-train`:

```text
skillopt-oauth: codex would resolve to a non-subscription credential (probe -> 'none');
refusing to launch so the run cannot be silently billed to a metered API.
```

Use a dry run to inspect routing without launching SkillOpt:

```bash
SKILLOPT_OAUTH_DRY_RUN=1 uv run skillopt-oauth \
  --backend codex_exec \
  --config demo/searchqa_codex/config.yaml
```

## Vendored SkillOpt Fork

`vendor/skillopt` is pinned to upstream SkillOpt `v0.1.0`. The local delta is
additive backend and config wiring:

- `codex_chat`: a CLI-backed optimizer that shells `codex exec`.
- `pi_chat`: a one-shot `pi -p --mode json --no-tools` optimizer/chat-target.
- `pi_exec`: an agentic rollout target using `pi -p --mode json` with tools on.

The regular SkillOpt training loop, datasets, evaluation flow, and checkpointing
remain in the vendored package. See
[`vendor/skillopt/PINNED_UPSTREAM.md`](vendor/skillopt/PINNED_UPSTREAM.md) for the
pin and local-delta inventory.

## Codex and Claude Subscription Runs

Upstream SkillOpt target backends can run `codex_exec` and `claude_code_exec`, but
the optimizer defaults to `openai_chat` unless configured. The guard injects
`codex_chat` or `claude_chat` so the optimizer leg uses the same local CLI path as
the target leg.

You can set backends explicitly:

```bash
uv run skillopt-oauth \
  --config demo/searchqa_codex/config.yaml \
  --target_backend codex_exec \
  --optimizer_backend codex_chat \
  --out_root demo/searchqa_codex/outputs/run_codex_codex
```

The committed [`demo/searchqa_codex/`](demo/searchqa_codex/) run shows a
before/after SearchQA optimization on `codex_exec` + `codex_chat`.

## pi Backend

The `pi` backend lets SkillOpt route each role to a `provider/model` deployment
slug, for example `zai/glm-5.2`, `openai-codex/gpt-5.5`, or
`github-copilot/gpt-5.5`.

- `pi_chat` is available for optimizer calls and chat targets.
- `pi_exec` is available for agentic target rollouts.
- A bare model name falls back to `PI_PROVIDER`, defaulting to `openai-codex`.
- Runtime guards verify that the streamed `provider` and `model` match the pin.

Example config:

```yaml
model:
  optimizer_backend: pi_chat
  target_backend: pi_exec
  optimizer: zai/glm-5.2
  target: zai/glm-5.2
  pi_allowed_metered_providers: [zai]
```

Direct trainer launch:

```bash
PI_ALLOW_METERED=zai uv run skillopt-train \
  --config demo/searchqa_pi/config.yaml \
  --out_root demo/searchqa_pi/outputs/run_pi_pi
```

Guarded launch:

```bash
PI_ALLOW_METERED=zai uv run skillopt-oauth \
  --backend pi_exec \
  --config demo/searchqa_pi/config.yaml \
  --out_root demo/searchqa_pi/outputs/run_pi_pi
```

### Metered Provider Opt-In

`openai-codex` and `github-copilot` are treated as subscription providers.
`zai` and `anthropic` are treated as metered providers and must be opted in when
running under `skillopt-oauth`.

Opt in with either:

- `PI_ALLOW_METERED=zai,anthropic`
- `model.pi_allowed_metered_providers: [zai, anthropic]` in the leaf config file

`PI_ALLOW_METERED` wins when both are present. The guard reads
`model.pi_allowed_metered_providers` from the leaf `--config` file only; it does
not resolve `_base_` inheritance for this preflight.

## Records

Each guard invocation writes a secret-safe JSONL record unless disabled:

- Default path: `.agent-workspace/skillopt-oauth/runs.jsonl`
- Override: `SKILLOPT_OAUTH_LOG_DIR=/path/to/dir`
- Disable file writes: `SKILLOPT_OAUTH_LOG=0`

Records include the event type (`refused`, `dry_run`, `handoff`, `exec_failed`,
and optionally `completed`), a generated `run_id`, scrubbed env names, redacted
argv, provider, backend routing, and output root. Credential values are never
recorded.

Set `SKILLOPT_OAUTH_SUPERVISE=1` to keep the guard process around and append a
`completed` record with exit code and duration.

## Environment Variables

| Var | Effect |
| --- | --- |
| `SKILLOPT_OAUTH_TARGET` | Pin provider routing: `claude`, `codex`, or `pi`. |
| `SKILLOPT_OAUTH_OPTIMIZER` | Optimizer backend to inject. `off`, `none`, or empty disables injection. |
| `SKILLOPT_OAUTH_DRY_RUN=1` | Preflight, scrub, and print the launch without execing. |
| `SKILLOPT_OAUTH_SUPERVISE=1` | Wait for the child and record completion. |
| `SKILLOPT_OAUTH_LOG_DIR` | Record directory. |
| `SKILLOPT_OAUTH_LOG=0` | Disable record-file writes. |
| `SKILLOPT_OAUTH_LOG_LEVEL` | Stderr log level. |
| `SKILLOPT_OAUTH_INJECT_OUT_ROOT=1` | Inject `--out_root` under the record directory when absent. |
| `SKILLOPT_OAUTH_RUN_ID` | Exported into the child for correlation. |
| `PI_ALLOW_METERED` | Comma-separated metered `pi` providers allowed for this run. |

## Demos

- [`demo/searchqa_codex/`](demo/searchqa_codex/): `codex_exec` target with
  `codex_chat` optimizer.
- [`demo/searchqa_pi/`](demo/searchqa_pi/): `pi_exec` target with `pi_chat`
  optimizer routed to `zai/glm-5.2`.

Both demos keep curated trace artifacts under `trace/`; raw `outputs/` directories
are gitignored.
