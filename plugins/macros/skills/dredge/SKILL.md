---
name: dredge
description: Search prior Claude Code chat transcripts under ~/.claude/projects for context. Use when the user invokes /dredge or asks to recall or dig up something from past chats.
argument-hint: "[\"freeform query\"]"
---

If other `/commands` appear in the user's message and you have not already called the Skill tool for them in this conversation, invoke each now. Do not re-invoke any skill that has already been loaded.

Do NOT re-invoke this skill via the Skill tool.
Execute the workflow below once, then stop.

## Task

Find and surface context from prior Claude Code chat transcripts relevant to the user's query.

## Where transcripts live

- Path: `~/.claude/projects/<project-slug>/*.jsonl`
- `<project-slug>` is the absolute project path with `/` replaced by `-` (e.g. `/Users/x/repo` → `-Users-x-repo`). The current project's slug can be derived from `pwd`.
- Each `.jsonl` file is one session; each line is a JSON message event with fields like `role`, `content`, `timestamp`.
- On the grep backend, use file mtime for time-window filtering. (The AgentsView backend filters on per-message timestamps instead — see "Search backend".)

## Argument handling

- **With a query** (`/dredge "how did we wire up auth"`) — use the text as the search focus.
- **No arg** (`/dredge`) — infer the topic from the current conversation.

## Scope

Default to the **current project's** transcripts (slug derived from `pwd`). Widen based on natural-language hints in the query:

- "across all projects" / "anywhere" / "in any chat" → search every project under `~/.claude/projects/`.
- Names a different repo ("in the craken project") → resolve to that project's slug and search there. If the slug is ambiguous, list candidates under `~/.claude/projects/` and pick by name match.
- Time hints ("yesterday", "last week", "earlier today", "recent") → filter by file mtime.

## Search backend

dredge has two backends. Resolve config from these files (first existing wins per
key; precedence: project override > user-local > user):

1. `~/.claude/skill-configs/dredge/config.local.yaml`
2. `~/.claude/skill-configs/dredge/config.yaml`
3. `.claude/skill-configs/dredge/config.yaml` (optional per-repo override)

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
- `--agent claude` unless `include_other_agents` is true; `--include-children` only if
  `include_children` is true.
- **Concept recall** → `--fts` (fast tokenized search over messages); **exact string / error
  message** → `--regex` or the default substring match.

## Approach

The grep fallback (also the AgentsView path's last resort):

1. Shortlist candidate `.jsonl` files with `rg` / `grep` using keywords from the query. Combine with `find -newer` / mtime for time windows.
2. Read the top candidates to pull the actual context (not just the matching lines).

## Output

- Answer the query directly.
- Cite the sessions you drew from by `<session-id>` so the user can resume them with `claude --resume <session-id>` (the AgentsView `session_id` is the Claude session UUID; the grep path cites `<project-slug>/<session-id>.jsonl`).
- For non-claude agents (only possible when `include_other_agents` is on), cite the agent name + session id without the `claude --resume` hint.
- If nothing relevant turns up, say so plainly — don't fabricate.
