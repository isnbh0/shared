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
