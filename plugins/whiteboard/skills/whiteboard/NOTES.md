# whiteboard notes

[`README.md`](README.md) maps the directory and gives the commands for working on it. This file
explains how the application works. `wb` runs `pnpm install` itself on first use.

## How it works

**Two channels.** The server listens on TCP `127.0.0.1:P` (default 5179, `WHITEBOARD_PORT`) for
the page, and on the Unix socket `STATE/P/control.sock` for `wb`. Browsers cannot reach Unix
sockets, so only the control channel takes file paths. The page channel has a fixed route table:
documents by ID from the open set, and the files of the page built at startup, looked up in a table
made from the build output. No page request maps a URL onto the filesystem. Every page request
needs `Host: 127.0.0.1:P` and, when sent, a matching `Origin`, which blocks other sites and DNS
rebinding.

**One server per port.** The server binds its TCP port before anything else, with no fallback, so
the operating system refuses a second server. The holder of port `P` owns `STATE/P/` (control
socket, `server.log`, built page), where `STATE` is `WHITEBOARD_STATE_DIR` or
`$TMPDIR/whiteboard`. While it builds the page it answers 503 with `x-whiteboard-starting: 1`,
so a `wb` that lost a simultaneous start keeps waiting for the winner. `wb` starts the server
detached when health fails and waits up to 120 s.

**Page build.** The server builds `app/` with Vite into `STATE/P/page` at startup. After changing
server, app, or Mermaiden sources, run `wb stop` so the next command starts a fresh server and
rebuilds the page.

**Idle exit.** The server exits after 30 minutes (`WHITEBOARD_IDLE_MINUTES`) with no request and
no page event stream open.

**Files.** `server/workspace.ts` is the only code that reads, writes, creates, or watches files,
and the only code that derives document IDs (sha256 of the real path) and revisions (sha256 of the
text). Every write carries a base rev, or `null` for "must not exist", and the compare runs inside
a per-path serialized section before an atomic temp-file rename that keeps the file mode. Text is
written exactly; nothing is appended. Files must be regular, UTF-8, and at most 2 MB. One
directory watcher per directory feeds `changed` events.

**Page sync.** Each tab's state is a value of the union in `app/src/sync.ts` (`unloaded`, `synced`,
`dirty`, `saving`, `conflict`, `orphaned`), changed only by the pure function `step`, which is total
over every state and event. Tab marks, the status line, the preview, and the editor text are all
computed from the state. Saves are debounced 400 ms and compare-and-swap against the base rev;
every save result re-reads the file, and saves run through `app/src/serial.ts` so they never
overlap. A change on disk under an unsaved draft becomes a conflict with "Reload from file" and
"Overwrite file"; a tab closed elsewhere keeps its draft. The Monaco editor loads on the first
"Edit".

**Preview view.** The preview is a pan-and-zoom pane (`app/src/viewport.ts`, arithmetic in
`app/src/view-math.ts`). The wheel zooms around the cursor; with "Scroll to pan" on, the wheel pans
and ctrl/⌘+wheel or a pinch zooms. Dragging pans. The toolbar has Fit, zoom out and in, and the
zoom percentage, which returns to 100 %. With the preview focused, `+`, `-`, `0`, Shift+1, and the
arrow keys do the same. A view follows fit (refitting on every render and resize) until the person
zooms or pans; after that, live edits keep the view. Each tab's view is restored when switching
back. "Highlight related" (flowcharts only) highlights a hovered node's ancestors and descendants
with the toolkit's relationship highlight. "Grid" draws a dot grid that moves and scales with the
view (the viewport sets `--view-x`, `--view-y`, `--view-k` on the pane). "Step through messages"
(sequence diagrams only) runs the toolkit's sequence playback: a bar floating over the preview's
bottom has Previous, the position and current label, and Next; with the preview focused, ←/→ step
and Home/End go to the first message and to the overview of all messages. Each step pans the least
needed to show the current message (`followRect`); the overview fits. A live edit keeps the
position; switching tabs starts from the first message. "Freeze participants" (sequence diagrams
only, on by default) pins copies of the participant header and footer rows to the pane's top and
bottom while panning, with the toolkit's pinned rows; during playback it shows only the revealed
participants and keeps the footers above the playback bar, and followed messages stay clear of
both. The toolkit hides the frozen rows when they would be too large at the current zoom; the
toggle's tooltip then says why. `app/src/sequence-view.ts` wires playback and frozen rows to the
pane: the copies are drawn in an overlay SVG in pane coordinates (styles are snapshotted before
attaching, since the copies leave the diagram's stylesheet), and the toolkit's lifeline underlay
is moved from the stage into the pane. The toggles persist in the browser's
`localStorage`.

**Share link.** The toolbar's link button copies a view-only link to the hosted Mermaiden demo
(`https://isnbh0.github.io/mermaiden/?view=1#pako:…`) for the active tab's current text, unsaved
draft included, with the grid, highlight, playback, and freeze toggles as the demo's aspects.
`app/src/share.ts` builds the demo's `pako:` hash (base64url of zlib-deflated JSON) with the
browser's `CompressionStream`; `tests/unit/share.test.ts` decodes it with Node's zlib and, when
a Mermaiden checkout is at `MERMAIDEN_DIR` (by default `~/local/src/mermaiden`), with the demo's
own codec too, so a format change there fails the test. Without a checkout those two tests are
skipped.

**Page styles.** `app/src/styles.css` is organized by concern: tokens; one control anatomy (icon or
text button) with one set of hover, pressed, `aria-pressed`, focus-visible, and disabled states
for every button; then each region's layout, where the parent owns the gaps between groups. A
region changes `--surface` so the hover and pressed tints read against its background. Icons are
Lucide symbols in a sprite at the top of `app/index.html`.

**Readiness contract.** The preview host `#preview` has `data-wb-state` = `rendering`, `rendered`
(one frame after the SVG is inserted), or `error`, with `[data-wb-error]` holding the message.
`wb shot` and the e2e tests wait on it.

**Mermaiden.** `vendor/mermaiden` and `vendor/mermaiden-toolkit` hold the packed contents of those
packages, and `package.json` depends on them by `file:` path, so no Mermaiden checkout is needed.
`vendor/update.sh` rebuilds and repacks both from a checkout and records the commit in
`vendor/SOURCE`; run `pnpm install` and `wb stop` after it. Vite `resolve.dedupe: ["mermaid"]`
keeps one Mermaid instance, the skill's own.

## Checks

`pnpm check` runs, in order:

- `typecheck`: `tsc` over the server, CLI, tests, and the page.
- Unit tests (`tests/unit`): the workspace (paths, reads, writes, watching), the route tables, the
  sync table enumerated over every state and event, and `Serial`. Two property tests: the
  workspace's no-lost-update law (random writers and external edits through one `Workspace`;
  external edits run between write groups) and the sync model (one tab against a model file with
  compare-and-swap, late and failed responses, external edits, closing and reopening).
- Integration tests (`tests/integration`): the real server and the `wb` CLI as subprocesses,
  including simultaneous starts, a port held by another program, and `wb shot`.
- E2e tests (`tests/e2e`, Playwright, headless Chromium): tabs, the preview, and editing with
  conflicts. Install the browser once with `pnpm exec playwright install chromium-headless-shell`.

Named gaps:

- An external edit that lands between the server's compare and its rename can be overwritten. The
  window is milliseconds, and the server does not own other programs' writes.
- If the user runs `wb open` on a file while a `wb shot` that opened it is running, the shot's
  closing step removes the tab. Running `wb open` again restores it.
- The editor keeps one line-ending style per file (LF or CRLF, whichever dominates). A file with
  mixed line endings is saved in its dominant style after the first edit.
- An orphaned tab whose last save landed before the close still reopens as a conflict, even when
  its draft equals the file; "Reload from file" resolves it.

## Follow-ups

- **Markdown with Mermaid blocks rendered in place,** then a general preview for agent output
  (HTML, images). The opener states a file's kind (for example `wb open --kind markdown`), so raw
  Mermaid files named `.md` stay valid.
- **Render as data:** `wb inspect <path>` reporting parse errors, the semantic graph from
  `renderWithSemantics`, and layout bounds, so agents need fewer screenshots.
- **A back-channel from the person:** selecting, pinning, or annotating nodes, streamed to agents
  through `wb events`.
- **A script interface for agents:** running small scripts against a document or graph API instead
  of chaining CLI calls.
- **Direct editing in the render,** such as renaming a node label or dragging out an edge.
- **Automatic restart when sources change:** health could report a hash of the server and page
  sources so `wb` restarts a stale server itself. Until then, `wb stop` does it by hand.
- **Smaller items:** Mermaid syntax highlighting in Monaco and a dark theme.
