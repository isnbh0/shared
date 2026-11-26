# whiteboard skill

This directory is the whole skill: the instructions an agent follows and the application those
instructions drive. Install it by copying or linking the entire directory. The application shows
Mermaid files, which are plain-text diagram sources, as tabs on a page in the browser and keeps the
page and the files in sync.

## Where things are

| Path | What it holds |
| --- | --- |
| [`SKILL.md`](SKILL.md) | The instructions an agent reads when the skill is selected. It governs how the agent uses the whiteboard. |
| `wb` | The launcher the agent runs. It checks the Node version, then runs `cli/wb.ts`. |
| `cli/` | The `wb` commands, which talk to the server and start it when needed. |
| `server/` | The local server. It holds the set of open files, and it alone reads, writes, and watches them. |
| `app/` | The browser page: tabs, the diagram preview, and the editor. |
| `vendor/` | Packed copies of Mermaiden, the library that renders the diagrams and provides the highlight and step-through features. [`vendor/README.md`](vendor/README.md) says how to refresh them. |
| `tests/` | Unit, integration, and browser tests. |
| `agents/openai.yaml` | Tells Codex not to select the skill on its own. |
| [`NOTES.md`](NOTES.md) | How the application works, what the checks cover, known gaps, and follow-ups. |

## Changing the application

It needs Node 24 or later and pnpm 9 or later. Node runs the TypeScript sources directly, so only
the page has a build step, and the server performs it at startup.

    pnpm install
    pnpm check

`pnpm check` runs the type check and every test. The browser tests need a headless browser, one
that runs without a window, installed once:

    pnpm exec playwright install chromium-headless-shell

A running server keeps the page it built at startup. After changing `app/` or `vendor/`, run
`./wb stop` so the next command rebuilds it.
