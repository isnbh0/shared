---
name: timestamp
description: Shorthand that tells the agent to prefix newly created files/folders with a `yymmdd-HHMMSS` timestamp from the `date` CLI. One timestamp per logical job bucket. One turn only.
---

If other `/commands` appear in the user's message and you have not already called the Skill tool for them in this conversation, invoke each now. Do not re-invoke any skill that has already been loaded.

For this turn only, prefix every new file or folder you create with a timestamp produced by the `date` CLI in `yymmdd-HHMMSS` format (e.g. `260428-143022`), joined to the existing name with a single dash. If the user specifies a different format inline (e.g., "use a 4-digit year"), honor that for the turn.

## How to get the timestamp

Run `date +%y%m%d-%H%M%S` via Bash. Do this **once** per logical job bucket — do not fabricate a timestamp from your knowledge of the current date, and do not recompute it for each file. Reuse the captured value across every destination created in the same overarching action. A "job bucket" is informal: if a single turn spans multiple unrelated jobs, run `date` once per bucket.

## What to apply the prefix to

- **In scope:** new files and new folders being created.
- **Out of scope:** edits, renames, or moves of existing files.
- Applies whether the user named the destination explicitly or you picked the name yourself.

## Where the prefix goes

Before creating anything, present a single inferred plan covering all destinations in this job bucket and ask the user to confirm or correct. Example:

> Plan: `260428-143022-report.md`, `260428-143022-notes/draft.md`. OK?

Only ask per-destination when there is genuine ambiguity (e.g., the user says "stamp the project folder" and it's unclear which path level should carry the prefix).

## Idempotency

If a destination name already begins with a `\d{6}-\d{6}-` prefix, leave it alone — don't re-stamp.
