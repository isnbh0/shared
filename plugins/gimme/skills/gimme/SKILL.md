---
name: gimme
description: User-invoked shorthand that inverts delegation — produce a filesystem bundle (checklist, drop-bin directory, notes template) of human-only actions and artifacts blocking project progress, and launch the user's editor on it.
---

If other `/commands` appear in the user's message and you have not already called the Skill tool for them in this conversation, invoke each now. Do not re-invoke any skill that has already been loaded.

**This skill is only ever invoked by the user.** Never invoke it on your own initiative.

When the user invokes `/gimme`, stop implementing and produce a **filesystem deliverable** — a timestamped bundle the user can open and fill in right now. No chat-only output.

## Config

Resolve config with the following precedence (first match wins):

1. Local: `.claude/skill-configs/gimme/config.local.yaml`
2. Project: `.claude/skill-configs/gimme/config.yaml`
3. No config → **stop and ask the user to set one up** using `config.example.yaml` from this skill as a reference. Required: `workspace_dir`. Optional: `launch_command`.

## Bundle layout

Create `${workspace_dir}/{YYYYMMDD-HHMMSS}-{slug}/` containing:

```
checklist.md   # numbered checkbox list; each item has Action / Why-you / Drop-path
notes.md       # template with pre-labeled headings for URLs, paragraphs, decisions
dropbox/       # empty directory for file artifacts (screenshots, exports, etc.)
```

`{slug}` is a short kebab-case topic derived from the conversation (e.g. `acme-integration`). If unclear, ask the user for one word before writing.

## Checklist contents

Include items that require:

- **Credentials, accounts, or auth** — API keys, OAuth grants, SSO logins, tokens you can't mint.
- **Access to human-only platforms** — web UIs behind login walls, mobile apps, desktop software, hardware, paid services without CLI/API.
- **External artifacts** — screenshots, exported data, signed documents, vendor responses, files from systems you can't reach.
- **Taste or judgment calls** the user reserved for themselves — visual/UX decisions, naming, strategic direction, stakeholder sign-off.
- **Real-world actions** — contacting a person, filing an external ticket, making a purchase, running something on a machine you don't have.

Exclude anything you could do yourself with the tools available.

Each checklist item:

1. **Action** — imperative, specific, atomic (one credential, one file, one decision).
2. **Why it's on you** — the concrete reason it can't be done from the agent loop.
3. **Drop path** — an exact path inside the bundle where the result goes. Files → `dropbox/<name>.<ext>`. Pasted text/URLs → a named heading in `notes.md` (create the heading in the template). Only use "reply in chat" when no artifact is produced.

Order items by what unblocks the most downstream work first. Note dependencies between items.

If **nothing** is blocked on the human, create no bundle, say so plainly in chat, and stop.

## notes.md template

Pre-populate with one `## <heading>` per checklist item that expects pasted text/URLs, each followed by a `<!-- paste here -->` placeholder. The user fills in the placeholders; you read the file to pick up.

## Launch

After writing the bundle, if `launch_command` is set, substitute the literal token `{path}` with the absolute path to the bundle directory and run the resulting command via the Bash tool. If the command fails or is unset, report the bundle path in chat instead.

## Chat response

Keep it short: one sentence stating the bundle path, and (if relevant) which item to do first.
