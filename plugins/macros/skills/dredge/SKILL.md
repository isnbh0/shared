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
- Use file mtime for time-window filtering.

## Argument handling

- **With a query** (`/dredge "how did we wire up auth"`) — use the text as the search focus.
- **No arg** (`/dredge`) — infer the topic from the current conversation.

## Scope

Default to the **current project's** transcripts (slug derived from `pwd`). Widen based on natural-language hints in the query:

- "across all projects" / "anywhere" / "in any chat" → search every project under `~/.claude/projects/`.
- Names a different repo ("in the craken project") → resolve to that project's slug and search there. If the slug is ambiguous, list candidates under `~/.claude/projects/` and pick by name match.
- Time hints ("yesterday", "last week", "earlier today", "recent") → filter by file mtime.

## Approach

1. Shortlist candidate `.jsonl` files with `rg` / `grep` using keywords from the query. Combine with `find -newer` / mtime for time windows.
2. Read the top candidates to pull the actual context (not just the matching lines).

## Output

- Answer the query directly.
- Cite sessions you drew from as `<project-slug>/<session-id>.jsonl` so the user can jump to them (e.g. `claude --resume <session-id>`).
- If nothing relevant turns up, say so plainly — don't fabricate.
