# skillopt-oauth

Run [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt) safely on your
`claude` / `codex` **OAuth subscription** CLIs.

It is two parts: a thin env-scrub + OAuth-preflight **guard** that wraps upstream's
`skillopt-train`, and a minimal **vendored fork** of SkillOpt (`vendor/skillopt`,
pinned to v0.1.0) that adds a `codex_chat` optimizer backend. Together they let the
**whole** optimize loop — both the target (rollout) and the optimizer (reflect)
legs — run on the `claude` / `codex` subscription CLI, with no metered API call
possible. Upstream owns the training loop (rollout → reflect → gate → checkpoint),
the scorers, and the CLI exec backends; this package adds the billing-safety
upstream omits and the one optimizer backend it was missing, then hands off.

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
3. **Route both legs onto the CLI** — point `CLAUDE_CODE_EXEC_PATH` /
   `CODEX_EXEC_PATH` at the OAuth CLI, and inject an explicit `--optimizer_backend`
   (`codex_chat` / `claude_chat`) so the optimizer/reflect leg rides the
   subscription too. Upstream's `--backend` macro otherwise defaults the optimizer
   to the metered `openai_chat`, and env is inert for upstream's selection — so the
   injected flag is what actually keeps the whole loop off the metered API.

Then it `exec`s upstream's `skillopt-train`, passing through all of your arguments.

## Quick start

```bash
cd tooling/skillopt
uv sync                      # builds the vendored skillopt fork (editable) + this guard
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

## The whole loop on the subscription (`codex_chat`)

SkillOpt splits each run into a **target** (executes the task) and an **optimizer**
(reflects on failures and rewrites the skill). Upstream ships CLI *target* backends
(`codex_exec`, `claude_code_exec`) but restricts the *optimizer* to chat/API
backends — for codex it defaults to the metered `openai_chat`. So out of the box the
optimizer leg can't run on the codex subscription, and once the keys are scrubbed it
fails closed.

The vendored fork (`vendor/skillopt`) closes that gap with a `codex_chat` optimizer
that shells `codex exec` (no API key), wired into the live dispatcher next to the
existing `claude_chat`. The guard then **injects** `--optimizer_backend` so the
optimizer rides the same OAuth CLI as the target — making every target×optimizer
combination subscription-native:

| target ↓ / optimizer → | `claude_chat` | `codex_chat` |
| --- | --- | --- |
| `claude_code_exec` | ✓ | ✓ |
| `codex_exec` | ✓ | ✓ |

Pass `--target_backend` / `--optimizer_backend` explicitly, or let the guard pick the
per-provider default (`codex` → `codex_chat`, `claude` → `claude_chat`); override with
`SKILLOPT_OAUTH_OPTIMIZER`. A worked before→after run lives in
[`demo/searchqa_codex/`](demo/searchqa_codex/): a deliberately-bad seed prompt
optimized on the codex/codex loop, entirely on the subscription.

The fork is a pinned, trimmed snapshot of upstream (`vendor/skillopt/PINNED_UPSTREAM.md`);
the local delta is just the `codex_chat` wiring under `skillopt/model/`.

## Records & observability

The guard is the only thing that knows *which* credential it proved, *which*
metered keys it neutralized, and *where* it routed — the security/billing-audit
fact nobody downstream captures. So per invocation it leaves a **secret-safe,
queryable record of its own decision**, plus a structured stderr log line.

- **Where.** One JSONL file, `.agent-workspace/skillopt-oauth/runs.jsonl`
  (cwd-relative; override with `SKILLOPT_OAUTH_LOG_DIR`). It's **append-only** and
  already gitignored at the repo root.
- **What.** One line per decision point, keyed by a generated `run_id`:
  `refused` (preflight failed closed), `dry_run`, `handoff` (written *before*
  exec/supervise, so a kill still leaves a trace), `exec_failed` (adds a sanitized
  `error`: exception class + `errno`, never the OS message), and — under
  `SKILLOPT_OAUTH_SUPERVISE=1` — `completed` (adds `exit_code`, `duration_s`,
  `end_ts`). Those event-specific fields are absent on the other events. Lines for
  one invocation share a `run_id` and may be non-adjacent; **readers join on `run_id`**.
- **No credential ever recorded.** Records hold only env *names* (never values —
  `scrubbed_keys` is the sorted set of stripped names, and any name that isn't a
  plain identifier is itself redacted), a **redacted** copy of the argv, and
  routing/preflight metadata. The argv redaction covers `--secret_flag value`,
  `--secret_flag=value`, `allow_abbrev` abbreviations (`--azure_api_k`), **and** the
  bare `section.key=value` tokens of upstream's preferred `--cfg-options` channel
  (`model.azure_api_key=…`) — every secret value becomes `<redacted>`. No credential
  value, config-file contents, or raw OS exception text is ever written. Redaction
  runs on a copy — the live argv handed to upstream is verbatim. (Operational,
  non-secret facts *are* recorded by design: the resolved CLI binary path, `cwd`, and
  the `--out_root` you passed — an audit record needs to know what ran and where. The
  file is created `0o600`, `O_NOFOLLOW`, owner-only.)
- **Fail-soft.** The stderr line is the contract; the file is an add-on. Any write
  error (bad dir, full disk, deleted `cwd`, planted symlink, non-serializable record)
  warns to stderr and the launch proceeds — records never block or slow a run.

The `run_id` is also exported into the child as `SKILLOPT_OAUTH_RUN_ID`, a
non-intrusive hook for correlating the guard's record with upstream's own output
(under `--out_root`).

### Env-var surface (all optional)

| Var | Effect |
| --- | --- |
| `SKILLOPT_OAUTH_TARGET` | Pin the provider to guard/route (`claude`\|`codex`) when the args don't say. |
| `SKILLOPT_OAUTH_OPTIMIZER` | Optimizer backend to inject (default `codex_chat`/`claude_chat` per provider); `off`\|`none`\|empty disables injection so upstream/config decides. |
| `SKILLOPT_OAUTH_LOG_DIR` | Record dir. Default `.agent-workspace/skillopt-oauth`. |
| `SKILLOPT_OAUTH_LOG=0\|off` | Disable the **file** write (the stderr line still emits). |
| `SKILLOPT_OAUTH_LOG_LEVEL` | stderr verbosity (default `INFO`). Decision lines log at `INFO`; refusals and launch failures at `ERROR` (so `LOG_LEVEL=ERROR` keeps those, `CRITICAL` silences stderr). The record file is unaffected by this. |
| `SKILLOPT_OAUTH_DRY_RUN=1` | Preflight + scrub + route, print the would-be launch, **don't exec**. |
| `SKILLOPT_OAUTH_SUPERVISE=1` | Wait on the child and record a `completed` line (exit code + duration). |
| `SKILLOPT_OAUTH_INJECT_OUT_ROOT=1` | When `--out_root` is absent, inject one under the record dir for correlation (off by default; it relocates upstream's default output dir). |
| `SKILLOPT_OAUTH_RUN_ID` | *Exported into the child*, not read — the correlation hook above. |

### Dry-run demo (no billing)

```
$ SKILLOPT_OAUTH_DRY_RUN=1 skillopt-oauth --backend claude_code_exec \
    --config x.yaml --azure_api_key sk-…
skillopt-oauth: dry-run for 'claude'; run_id=…; would exec skillopt-train (no launch)
skillopt-oauth dry-run (no exec):
  provider:    claude
  would exec:  skillopt-train --backend claude_code_exec --config x.yaml --azure_api_key '<redacted>'
  env removed: ['ANTHROPIC_API_KEY']
  env added:   ['CLAUDE_CODE_EXEC_PATH', 'OPTIMIZER_BACKEND', 'SKILLOPT_OAUTH_RUN_ID', 'TARGET_BACKEND']
```

It writes a `dry_run` record, prints the redacted launch, returns `0`, and never
execs — the safe way to inspect what a real run would do.

### Supervise (opt-in completion record)

By default the guard `exec`s upstream and gets out of the way — it stays out of the
run's failure path, a billing-safety tool's core virtue. Set
`SKILLOPT_OAUTH_SUPERVISE=1` to instead wait on the child (inherited stdio, signals
forwarded) and append a `completed` record with the exit code and duration.

## Caveat: subscription headless billing is targeted, re-verify

As of 2026-06-30, headless `claude -p` and `codex exec` run on the **subscription**
(no API key). But Anthropic announced (effective 2026-06-15) moving Agent SDK /
`claude -p` / GitHub Actions onto separate metered credits, then **paused** it on
the due date and is reworking it with promised advance notice. It was reverted, not
shipped — but it was explicitly targeted, so treat headless subscription billing as
fragile and **re-verify before any long or automated run**. The env scrub and
fail-closed preflight here are the hedge: if the metered split re-ships, a run that
can't prove OAuth refuses to start rather than billing you.
