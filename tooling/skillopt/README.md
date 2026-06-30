# skillopt-oauth

Run [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt) safely on your
`claude` / `codex` **OAuth subscription** CLIs.

This is a thin env-scrub + OAuth-preflight guard around upstream's
`claude_code_exec` / `codex_exec` backends — **not a fork**. Upstream owns the
training loop (rollout → reflect → gate → checkpoint), the scorers, and the CLI
exec backends; this package adds only the billing-safety upstream omits, then
hands off.

## Why this exists

Upstream's exec backends spawn the CLI with `subprocess.run`, which inherits the
parent environment. In headless `claude -p` / `codex exec` mode a stray
`ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`) **always overrides** the OAuth session,
silently routing the call onto the metered provider API — even with a valid
subscription. One Max user hit **$1,800 in two days** this way
([anthropics/claude-code#37686](https://github.com/anthropics/claude-code/issues/37686)).
Upstream does no env scrub and no OAuth preflight at any exec site, so the hole is
open by default.

`skillopt-oauth` closes it by construction, before launching upstream:

1. **Fail-closed OAuth preflight** — confirm a subscription credential for the
   provider in use, and refuse to launch otherwise. claude: `CLAUDE_CODE_OAUTH_TOKEN`,
   the macOS login Keychain item `Claude Code-credentials`, or
   `~/.claude/.credentials.json`. codex: `~/.codex/auth.json` with
   `auth_mode == "chatgpt"`. (The Keychain is probed by *existence only* — never
   by decrypting the secret, which can pop an ACL prompt that hangs a headless run.)
2. **Env scrub** — strip every `*_API_KEY` / `*_AUTH_TOKEN` from the environment the
   child inherits, so a metered fallback is impossible. `CLAUDE_CODE_OAUTH_TOKEN`
   (an OAuth token, not an API key) is preserved.
3. **Route to the CLI backends** — point `TARGET_BACKEND` / `OPTIMIZER_BACKEND` and
   `CLAUDE_CODE_EXEC_PATH` / `CODEX_EXEC_PATH` at the OAuth CLIs.

Then it `exec`s upstream's `skillopt-train`, passing through all of your arguments.

## Quick start

```bash
cd tooling/skillopt
uv sync                      # installs upstream skillopt[claude] + this guard
uv run pytest                # hermetic; spends nothing

# Drive an upstream run safely. All args after `skillopt-oauth` pass straight
# through to `skillopt-train`; the guard preflights, scrubs, and routes first.
uv run skillopt-oauth --backend claude_code_exec --config configs/<env>/default.yaml
```

The target provider is inferred from `--backend` / `--target_backend` (anything
mentioning `codex` → codex; `claude` → claude), or pinned with
`SKILLOPT_OAUTH_TARGET=claude|codex`; it defaults to `claude`.

If no subscription credential is reachable, the guard exits non-zero **before**
launching upstream — it never silently falls back to a metered API:

```
$ skillopt-oauth --backend codex_exec --config …
skillopt-oauth: codex would resolve to a non-subscription credential (probe -> 'none');
refusing to launch so the run cannot be silently billed to a metered API. …
```

To pick an env, supply data, and configure the loop, see upstream's docs
(`skillopt-train --help`, `EnvAdapter`, `SplitDataLoader`, and `configs/`).

## Caveat: subscription headless billing is targeted, re-verify

As of 2026-06-30, headless `claude -p` and `codex exec` run on the **subscription**
(no API key). But Anthropic announced (effective 2026-06-15) moving Agent SDK /
`claude -p` / GitHub Actions onto separate metered credits, then **paused** it on
the due date and is reworking it with promised advance notice. It was reverted, not
shipped — but it was explicitly targeted, so treat headless subscription billing as
fragile and **re-verify before any long or automated run**. The env scrub and
fail-closed preflight here are the hedge: if the metered split re-ships, a run that
can't prove OAuth refuses to start rather than billing you.
