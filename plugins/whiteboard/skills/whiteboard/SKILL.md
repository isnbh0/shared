---
name: whiteboard
description: >-
  Explicit-request macro. Activate only when the user directly requests this macro;
  never infer activation from task characteristics. Skill — Open Mermaid files as tabs on a shared local whiteboard, synced both ways with the files, for the conversation.
disable-model-invocation: true
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

Set up a shared whiteboard: Mermaid files on disk that you edit and the user edits in a local page
in their browser. One page holds every open file as a tab with a live preview and an editor, and
each side's changes reach the other within a moment.

## Start it

Pick the file. Use one the user names or one that already fits the topic. Otherwise create a file
named for the topic where the project keeps scratch notes, or in `docs/` if it keeps none. Put it
under `$TMPDIR/whiteboard/boards/` only when the user says the diagram is throwaway. The file holds
raw Mermaid source, optionally with Mermaid frontmatter.

Run `<skill dir>/wb open <file>` with an absolute or relative path. It installs dependencies the
first time, starts the shared server if needed, and creates the file and its directory with a
starter diagram if the file doesn't exist, saying `created` on stderr. The server keeps running
after the session and stops on its own after 30 minutes with no page open, so do not stop it. Give
the user the printed address; open it in their browser only if they ask. One page holds every open
file as a tab, and `wb open` switches an open page to that file.

Open tabs last only while the server runs; after it stops, `wb open` each file again.

## Work on it together

Treat the file as shared. The user may edit it at any moment, so work from what is there now, not
from what you read earlier.

- Small targeted edits with your edit tool, made right after a fresh read, are fine.
- For larger rewrites, run `wb read <file>` and note the `rev` it prints on stderr, then
  `wb write <file> --rev <rev>` with the new text on stdin. Use `--rev none` to create a file that
  must not exist yet. `wb read` and `wb write` work on any file and do not add tabs.
- A refused write prints the file's current rev. Run `wb read` again on its own, rebuild the
  content from that output, and write with the new rev. Never prepare the content first and chain
  it after a read.
- Notice the user's edits and respond to them when they matter to the conversation. Use the
  diagram where a picture helps, and keep talking in chat where it does not.

Before drawing a flowchart, decide what its arrows mean. If a skill for that is available, such as
merbook's action-flow or artifact-process-flow, load it and follow it for the diagram's content.

## Look before describing

Say what the diagram shows only as far as you have seen it. Mermaid's layout can surprise you, so
after structural changes run `wb shot <file>` and view the PNG path it prints. It exits 1 with the
message when the diagram fails to render. It does not change the user's page. The first `wb shot`
on a machine downloads a headless browser (about 100 MB). Do not drive the user's own browser.

## Variants

To keep a variant, copy the file to a sibling name rather than overwriting the user's work, change
the copy, then `wb open` it so both appear as tabs.

## Other commands

`wb ls` shows what's open and ends by saying whether a page is connected. `wb close <file>` removes
a tab for everyone. `wb stop` stops the server; it is needed only after changing the skill's own
app code. The server's state, its log, and screenshots live under `$TMPDIR/whiteboard/`, or
`WHITEBOARD_STATE_DIR`; `WHITEBOARD_PORT` picks another port when the default is taken.

## Conflicts

If the user's unsaved draft and a change to the file collide, their page shows "Reload from file"
and "Overwrite file". No conflict files are written. Tell the user what you changed so they can
choose.

## Requirements

Node 24 or later and pnpm 9 or later. `wb` names whichever is missing or too old. On a host that
sandboxes commands, `wb open` needs the network the first time and permission to listen on a
loopback port, so ask for that approval.
