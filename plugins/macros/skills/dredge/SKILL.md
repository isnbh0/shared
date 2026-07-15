---
name: dredge
description: Explicit-request macro. Activate only when the user directly requests this macro; never infer activation from task characteristics. Skill — Search prior coding-agent chat transcripts (Claude Code, Codex, ...) for context. Use when the user explicitly activates this skill or asks to recall or dig up something from past chats.
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

Do NOT re-invoke this skill recursively.
Execute the workflow below once, then stop.

## Task

Find and surface context from prior coding-agent chat transcripts relevant to the user's query.

## Where transcripts live

Each coding agent keeps its own transcript store.

- **Claude Code** — `~/.claude/projects/<project-slug>/*.jsonl`, where `<project-slug>` is the absolute project path with `/` replaced by `-` (e.g. `/Users/x/repo` → `-Users-x-repo`). The current project's slug can be derived from `pwd`.
- **Codex and other agents** — each has its own layout, indexed by AgentsView. The grep fallback only knows Claude Code's layout.
- Each `.jsonl` file is one session; each line is a JSON message event with fields like `role`, `content`, `timestamp`.
- On the grep backend, use file mtime for time-window filtering. (The AgentsView backend filters on per-message timestamps instead — see "Search backend".)

## Argument handling

- **With a query** — use the text supplied with `macros:dredge` as the search focus.
- **No query** — infer the topic from the current conversation.

## Scope

Default to the **current project's** transcripts (slug derived from `pwd`). Widen based on natural-language hints in the query:

- "across all projects" / "anywhere" / "in any chat" → search every project under `~/.claude/projects/`.
- Names a different repo ("in the craken project") → resolve to that project's slug and search there. If the slug is ambiguous, list candidates under `~/.claude/projects/` and pick by name match.
- Time hints ("yesterday", "last week", "earlier today", "recent") → filter by file mtime.

## Search backend

dredge has two backends. Resolve config by merging these files per key (first
existing wins; precedence: project override > user-local > user):

1. `.agents/skill-configs/dredge/config.yaml` — per-repo override (optional)
2. `~/.agents/skill-configs/dredge/config.local.yaml` — user-local
3. `~/.agents/skill-configs/dredge/config.yaml` — user (global)

Legacy fallback (older installs): the same files under `~/.claude/skill-configs/dredge/` and `.claude/skill-configs/dredge/`. If config is found only at a legacy path, use it and offer to move it to the new location.

With no config, behave as `backend: auto`. See `config.example.yaml` for all keys.

- **AgentsView** (when `backend` is `auto` and `agentsview` is on PATH, or `backend` is `agentsview`):
  1. If `sync_before_search` (default true), run `agentsview sync` first (incremental;
     ~sub-second when warm). This is required — search hits a SQLite index that is stale
     until synced. The sync prints a noisy progress bar; ignore it (only the final
     `Sync complete` line matters).
  2. `agentsview session search "<query>" --format json --in <search_in> --limit 30`,
     adding the scope/time/agent flags below.
  3. For each promising match, fetch context with
     `agentsview session messages <session_id> --from <ordinal> --limit <n> --format json`
     (do NOT read the whole `.jsonl`). The `ordinal` from `session search` indexes directly
     into `session messages --from`. Use `agentsview session export <session_id>` only when
     the full raw transcript is needed.
- **grep** (when `backend` is `grep`, or `auto`/`agentsview` and the binary is missing):
  the file-scan approach in "Approach" below.

Never hard-fail: if AgentsView is unavailable or errors, warn briefly and fall back to grep.

### AgentsView flag mapping

On the AgentsView backend, translate the natural-language scope/time hints (see "Scope") to flags:

- **Current project** → resolve `basename(pwd)`, confirm it appears exactly once in
  `agentsview projects --json`, and pass `--project <name>` only if it resolves unambiguously.
  If two projects share that basename (collision), omit `--project` and fall back to slug-grep
  for that scope rather than returning wrong-project hits.
- **"across all projects" / "anywhere"** → omit `--project`.
- **Named repo** → match its basename against `projects --json` (same collision rule).
- **Time hints** ("yesterday", "last week", "earlier today") → `--date-from` / `--date-to` /
  `--date <YYYY-MM-DD>` / `--active-since <RFC3339>` (per-message timestamps, not file mtime).
- Filter to specific agents with `--agent <name>` per the `agents` config (e.g.
  `--agent claude --agent codex`); omit `--agent` entirely when `agents: all` (the default)
  to search every indexed coding agent. `--include-children` only if `include_children` is true.
- **Concept recall** → `--fts` (fast tokenized search over messages); **exact string / error
  message** → `--regex` or the default substring match.

## Approach

The grep fallback (also the AgentsView path's last resort):

1. Shortlist candidate `.jsonl` files with `rg` / `grep` using keywords from the query. Combine with `find -newer` / mtime for time windows.
2. Read the top candidates to pull the actual context (not just the matching lines).

## Output

- Answer the query directly.
- Cite each session you drew from by agent + `<session-id>`, with that agent's resume command when you know it (e.g. `claude --resume <session-id>` for Claude Code, `codex resume <session-id>` for Codex). The AgentsView `session_id` is the agent's native session id; the grep path cites `<project-slug>/<session-id>.jsonl`.
- If you don't know an agent's resume command, cite the agent name + session id alone.
- If nothing relevant turns up, say so plainly — don't fabricate.
