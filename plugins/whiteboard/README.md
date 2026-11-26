# Whiteboard: Shared Mermaid Diagrams

Whiteboard lets a person and a coding agent work on the same diagram at the same time. The diagrams
are Mermaid files: plain text that describes a flowchart, a sequence diagram, or a similar figure,
which the Mermaid library draws as a picture. The agent edits the file on disk. The person watches
and edits it in a page in their browser. Each side's changes reach the other within a moment.

The plugin holds one skill, self-contained under `skills/whiteboard/`. A skill is a folder of
instructions and tools that an agent loads for a particular job. This file is human reference
documentation.

## Starting it

You start the whiteboard yourself, by selecting the skill in your agent host, the program you talk
to the agent in. The [cross-platform guide](../../docs/cross-platform/README.md) shows how each
host selects a skill. The agent does not load it on its own.

The agent then picks or creates a Mermaid file, opens it on the whiteboard, and gives you an
address beginning with `http://127.0.0.1:5179/`. Open that address in your browser.

## The page

One page holds every open file as a tab.

- **Preview.** The diagram redraws as the file changes. Drag to pan, scroll to zoom, and use "Fit"
  to see the whole diagram.
- **Editor.** "Edit" opens a text editor for the file. Your changes save to the file as you type.
- **Flowcharts.** "Highlight related" marks everything that leads to or from the node under the
  cursor.
- **Sequence diagrams.** "Step through messages" walks the diagram one message at a time, and
  "Freeze participants" keeps the participant names in view while you pan.
- **Share link.** The link button copies a view-only link to the diagram on the hosted
  [Mermaiden demo](https://isnbh0.github.io/mermaiden/). The link itself carries the diagram's
  text.
- **Conflicts.** When the file changes while you have unsaved edits, the page offers "Reload from
  file" and "Overwrite file".

## What the agent runs

The skill ships a command-line tool named `wb`, which the agent uses on your behalf.

| Command | Effect |
| --- | --- |
| `wb open <file>` | Adds the file as a tab, creating it if missing, and switches open pages to it |
| `wb ls` | Lists the open files and says whether a page is connected |
| `wb read <file>` | Prints the file and its revision, a fingerprint of the current text |
| `wb write <file> --rev <rev>` | Replaces the file only if it is still at that revision, so your edits are not overwritten |
| `wb shot <file>` | Renders the diagram to a PNG image, so the agent can look at it before describing it |
| `wb close <file>` | Removes the tab |
| `wb stop` | Stops the server |

## Requirements and costs

- Node 24 or later and pnpm 9 or later. `wb` names whichever is missing or too old.
- The first `wb open` downloads about 400 MB of dependencies into the skill's `node_modules/`.
- The first `wb shot` downloads a headless browser, one that runs without a window, of about
  100 MB.
- `wb open` starts a small server that only your own machine can reach. It keeps running after the
  agent session ends and exits after 30 minutes with no page open.
- Open tabs last only while the server runs. The files stay where they are.
- The default port is 5179; set `WHITEBOARD_PORT` to use another. The server's log and screenshots
  live under `$TMPDIR/whiteboard/`, or under `WHITEBOARD_STATE_DIR` when set.

## Going further

- [`skills/whiteboard/SKILL.md`](skills/whiteboard/SKILL.md) is what the agent follows.
- [`skills/whiteboard/README.md`](skills/whiteboard/README.md) maps the application's source for
  anyone changing it.
