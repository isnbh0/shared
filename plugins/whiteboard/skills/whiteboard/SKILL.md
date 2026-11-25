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
named for the topic where the project keeps scratch notes, or under
`$TMPDIR/my-whiteboard/boards/` if the diagram is throwaway. The file holds raw Mermaid source,
optionally with Mermaid frontmatter.

Run `<skill dir>/wb open <file>` with an absolute or relative path. It installs dependencies,
starts the shared server if needed, and creates the file with a starter diagram if it doesn't
exist. The server keeps running after the session and stops on its own after 30 minutes unused, so
do not stop it. Give the user the printed address; open it in their browser only if they ask. One
page holds every open file as a tab, and `wb open` switches an open page to that file.

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

## Look before describing

Say what the diagram shows only as far as you have seen it. Mermaid's layout can surprise you, so
after structural changes run `wb shot <file>` and view the PNG path it prints. It exits 1 with the
message when the diagram fails to render. It does not change the user's page. Do not drive the
user's own browser.

## Variants

To keep a variant, copy the file to a sibling name rather than overwriting the user's work, then
`wb open` the copy so both appear as tabs.

## Other commands

`wb ls` shows what's open. `wb close <file>` removes a tab for everyone. `wb stop` stops the
server; it is needed only after changing the skill's own app code.

## Conflicts

If the user's unsaved draft and a change to the file collide, their page shows "Reload from file"
and "Overwrite file". No conflict files are written. Tell the user what you changed so they can
choose.

## Requirements

Node 24 or later and pnpm. `wb` names whichever is missing.
