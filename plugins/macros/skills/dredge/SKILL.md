---
name: dredge
description: Explicit-request macro. Activate only when the user directly requests this macro; never infer activation from task characteristics. Skill — Search prior coding-agent transcripts and prompt histories for past requests. Use when the user explicitly activates this skill or asks to recall or dig up something from past chats.
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

Do NOT re-invoke this skill recursively.
Execute the workflow below once, then stop.

## Task

Find and surface context from prior coding-agent chat transcripts relevant to the user's query.

## Where transcripts live

Each coding agent keeps its own transcript store.

- **Claude Code** — `~/.claude/projects/<project-slug>/*.jsonl`, where `<project-slug>` is the absolute project path with `/` replaced by `-` (e.g. `/Users/x/repo` → `-Users-x-repo`). The current project's slug can be derived from `pwd`.
- **Pi** — by default `~/.pi/agent/sessions/<project-dir>/*.jsonl`. Respect `PI_CODING_AGENT_SESSION_DIR`, or `PI_CODING_AGENT_DIR` (whose `sessions` subdirectory is the default); a session may also use a custom `--session-dir`. The first JSONL record has `type: "session"`, `id`, and `cwd`; message records have `type: "message"`, a `timestamp`, and a nested `message` containing `role` and `content`. Entries may branch through `id` and `parentId`.
- **Codex** — `${CODEX_HOME:-~/.codex}/sessions/` contains date-organized JSONL files; also check `archived_sessions/` under the same home. A `session_meta` record has `payload.id` and `payload.cwd`; `response_item` records can contain messages under `payload.role` and `payload.content`, alongside tool and other events.
- **Gemini CLI** — `~/.gemini/tmp/<project>/chats/` contains session JSON and JSONL files. For AgentsView, respect its `GEMINI_DIR` override when set. Resolve project directories from Gemini's project registry or verified session metadata; do not guess from a basename. A session has a native session ID and messages; formats vary by version.
- **Antigravity CLI (agy)** — `~/.gemini/antigravity-cli/conversations/` contains SQLite conversation databases and may contain decoded `<id>.trajectory.json` sidecars. Older stores may contain encrypted `.pb` files, prompt history and plaintext artifacts. These are distinct from Gemini CLI. AgentsView may index full transcripts or only summaries. `agy-reader` can produce sidecars or export supported databases offline, but decoding can fail for unsupported formats and a daemon may require authentication. Never assume all databases are readable.
- **Other agents** — each has its own layout, indexed by AgentsView when supported.
- Session formats and event schemas vary by agent and version; JSONL is not universal.
- On the grep backend, file mtime can shortlist raw files for an ordinary time-window lookup. For a complete inventory, inspect message timestamps rather than excluding files solely by mtime. AgentsView uses per-message timestamps; prompt histories use their record timestamps.

## Argument handling

- **With a query** — use the text supplied with `macros:dredge` as the search focus.
- **No query** — infer the topic from the current conversation.

## Scope

Default to the **current project's** transcripts. Widen based on natural-language hints in the query:

- "across all projects" / "anywhere" / "in any chat" → search all available project stores.
- Names a different repo ("in the craken project") → resolve its project path. If ambiguous, inspect candidate project paths.
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
     adding the scope/time/agent flags below. For exhaustive searches, follow
     `next_cursor` with `--cursor` until there are no more pages. If the installed
     version cannot paginate, vary queries and report any remaining result cap.
  3. For each promising match, fetch context with
     `agentsview session messages <session_id> --from <ordinal> --limit <n> --format json`
     (do NOT read the whole `.jsonl`). The `ordinal` from `session search` indexes directly
     into `session messages --from`. Use `agentsview session export <session_id>` only when
     the full raw transcript is needed.
- **grep** (when `backend` is `grep`, or `auto`/`agentsview` and the binary is missing):
  the file-scan approach in "Approach" below.

Never hard-fail: if AgentsView is unavailable or errors, warn briefly and fall back to grep.

### Antigravity CLI coverage

When Antigravity CLI is in scope, search its indexed sessions and available
plaintext sidecars. An index can contain only summaries, so also inspect raw
sources when their coverage is relevant, even if the index has hits. Use
`antigravity.reader` from config, or `agy-reader` on PATH, to attempt an offline
export of relevant `.db` files into a private temporary directory, using
`<reader> export-offline --format=json --out=<new-file> <database>`. The reader
may refuse unsupported or in-progress data. Offline exports are reconstructed
from saved data; they are not daemon-verified presentations.

If offline presentation decoding fails and `antigravity.source_reader` is
configured, it may be called with the database path and a new output path to
recover searchable source-format JSON. Treat this as source evidence with an
unverified presentation. If neither reader succeeds, report the gap. Search
existing recovery snapshots when useful, but identify them as point-in-time
copies that may be older than the current database. Clean up temporary exports
when finished; do not install tools, start background jobs, or create persistent
sidecars as part of a search.

Use verified workspace paths to apply project scope; do not assume an
unattributed session belongs to the current project. Apply time filters to
message timestamps where available and deduplicate results by native session ID
and message identity.

### AgentsView flag mapping

On the AgentsView backend, translate the natural-language scope/time hints (see "Scope") to flags:

- **Current project** → resolve `basename(pwd)`, confirm it appears exactly once in
  `agentsview projects --json`, and pass `--project <name>` only if it resolves unambiguously.
  If two projects share that basename (collision), omit `--project` and fall back to scoped raw-file search
  for that scope rather than returning wrong-project hits.
- **"across all projects" / "anywhere"** → omit `--project`.
- **Named repo** → match its basename against `projects --json` (same collision rule).
- **Time hints** ("yesterday", "last week", "earlier today") → `--date-from` / `--date-to` /
  `--date <YYYY-MM-DD>` / `--active-since <RFC3339>` (per-message timestamps, not file mtime).
- Filter to specific agents with `--agent <name>` per the `agents` config; query each requested agent separately and deduplicate. Omit `--agent` entirely when `agents: all` (the default) to search every indexed coding agent. For ordinary searches, use
  `--include-children` only if `include_children` is true. For a complete
  inventory, pass `--include-children`, `--include-automated`, and
  `--include-one-shot` when supported, unless the user excludes those sessions.
  Report any excluded type.
- **Concept recall** → `--fts` (fast tokenized search over messages); **exact string / error
  message** → `--regex` or the default substring match.

## Approach

The grep fallback (also the AgentsView path's last resort):

1. Search likely Claude, Codex, Pi, Gemini CLI, and Antigravity CLI stores within the requested scope; for a complete inventory, search all available stores. For Codex and Pi, select files by the session metadata's `cwd`, comparing resolved paths where possible. Include known custom session directories and report coverage limits that affect the answer.
2. Shortlist searchable session files with `rg` / `grep` using keywords from the query. Parse Gemini JSON and JSONL according to their actual structure; inspect matching messages and their timestamps. Use `find -newer` / mtime only to narrow ordinary lookups; for a complete date-limited inventory, check message timestamps across candidate project files.
3. For Antigravity, search available plaintext sidecars and transcript exports, including `~/.gemini/antigravity-cli/recovery-unverified/` and `~/.gemini/antigravity-cli/recovery-source-experimental/exports/` and `~/.gemini/antigravity-cli/recovery-source-experimental/rendered/` when present, and inspect prompt history or artifacts as partial evidence. Read any accompanying recovery notes: unverified daemon exports have unknown completeness; experimental source exports and rendered snapshots may have been compared with daemon responses using a locally modified reader; report the documented verification scope and limitations. Do not present these local results as upstream-verified transcripts. Search preserved referenced artifacts when relevant. Do not grep binary databases as if they were transcripts. For offline decoding, follow the Antigravity coverage guidance above.
4. Read the top candidates to pull the actual context (not just the matching lines). For Pi, inspect nested messages and their parent links when needed to distinguish branches; cite the header's session ID, not the filename timestamp.

## Coverage check

Decide whether the user wants a best match or a complete inventory separately
from project scope. For a focused lookup, start with likely transcripts and
consult prompt history when matches are missing or an artifact suggests a
transcript gap. For a complete inventory, search available prompt histories and
raw transcripts as well as the index. Apply the same project and date scope to
each source, using record timestamps rather than file mtime for prompt history.

- **AgentsView** searches indexed messages and tool events. Sync can index
  surviving files but cannot recover a missing transcript.
- **Antigravity coverage**: inspect session fidelity and compare indexed sessions with available conversation files when completeness matters. Summary-only entries, decoding failures, missing databases, and sessions without verified project identity limit coverage. Search unassigned sessions where appropriate, but do not attribute them to a project without evidence.
- **Raw session stores** can contain surviving transcripts absent from the
  index. The known paths above include Gemini and available Antigravity plaintext; inspect other agent
  stores only when their layout is verified.
- **Prompt histories** record user requests, often without the assistant's
  response. Claude Code's `~/.claude/history.jsonl` has `display`,
  `pastedContents`, `timestamp`, `project`, and `sessionId` fields. Search
  `display` and relevant pasted content; retain the record's provenance. Add
  other agents' histories only after verifying their locations and formats.
- **User-supplied artifacts** provide search terms and evidence of an output,
  but cannot establish the exact request or conversation by themselves. Read
  an artifact's title, date, names, and distinctive phrases first, then search
  its path/name and content terms across applicable sources.

For each history hit, check whether the native transcript still exists before
fetching context or giving a resume command. Label evidence as **transcript
confirmed**, **prompt-history confirmed**, or **artifact inferred**. Deduplicate
the same request across sources by agent, session ID, and prompt identity
(timestamp or text); group distinct requests that share a session. Report the
projects, agents, session types, and sources actually searched, including any
missing stores or result caps that limit confidence.

## Output

- Answer the query directly.
- Cite each session by agent and native session ID. When the transcript exists and you know the resume command, include it (e.g. `claude --resume <session-id>`, `codex resume <session-id>`, `pi --session <session-file-path>`, or `agy --conversation <id>`). Include the raw path when needed to locate or resume the session. Pi filenames include a timestamp as well as the ID; AgentsView may prefix IDs with the agent name.
- If nothing relevant turns up, say so plainly and identify the sources searched;
  do not imply that missing stores were searched or that no other cases exist.
