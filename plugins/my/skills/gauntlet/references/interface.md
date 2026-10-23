# Gauntlet interface

Each feature below removes a reason to stop and think. The templates in `../assets/` already
have all of them, so keep them when you adapt a template.

## Features

- **One file, no server.** The page opens from `file://` with every excerpt embedded. Each side
  renders in a `srcdoc` iframe, scaled to fit the window, and both sides use the same frame size.
  When many excerpts share stylesheets, store each sheet once by content hash and reference it
  from the excerpts.
- **Flip in place.** Space swaps A and B in the same spot, so small differences show as motion.
  F toggles side by side. Every load starts in flip mode.
- **One key per answer.** Enter picks the side showing. A, B and N (or 1, 2, 0) answer directly.
- **Auto-advance.** After an answer the page moves on after a short pause. ← goes back on a
  fixed page and undoes the last answer on an adaptive one.
- **Optional note.** The note field is there for a word when one comes, and Esc leaves it.
  Don't ask for notes: putting reasons into words is what the page replaces.
- **Progress.** A bar shows answered of total. Adaptive pages show an estimate that updates as
  answers come in.
- **Resume.** Answers save to `localStorage` under the page's store key, so a reload picks up at
  the first unanswered pair. Give each page its own versioned key so that one round can't
  overwrite another.
- **Export.** Download writes JSON with a fixed filename to Downloads. Copy puts the same JSON on
  the clipboard. A partial export is fine.
- **Blind.** The page shows only A and B. A fixed page keeps its key in a separate file. An
  adaptive page has to carry its search definitions but never displays values.
- **Short sittings.** Aim for about 40 pairs or 5 minutes per page. Numbness sets in well before
  100 pairs, and it doesn't show on the page.

## Filling a template

Replace the placeholders, then inject the data and the project code:

| Placeholder | Value |
| --- | --- |
| `__TITLE__` | Browser tab title |
| `__PROMPT__` | The question shown in the header, in the person's terms, framed as a quick gut call |
| `__HELP__` | Extra help text for this page, or empty. Mention identical pairs when the page has nulls |
| `__STORE__` | `localStorage` key, versioned for each page |
| `__NAME__` | Gauntlet name, written into the export |
| `__FILE__` | Export filename |
| `__WIDTH__` | Default frame width in CSS pixels |
| `/*DATA*/` | The page's data, as a JSON literal |
| `/*PROJECT*/` | Project code that defines `srcdoc()` and, optionally, `frameWidth()` |

Use function replacements (`.replace('/*DATA*/', () => json)`) so that `$` sequences in the data
survive.

### Fixed page (`gauntlet.tpl.html`)

- `DATA.trials` is the ordered list of pairs, `[{ id, ... }]`. The other fields belong to the
  project.
- `srcdoc(trial, side)` returns the full HTML document for side `'A'` or `'B'`.
- `frameWidth(trial)` is optional. It returns a width when one trial needs a wider frame than
  `__WIDTH__`.
- The key, in its own file, maps each trial `id` to which side carries the change and what the
  change is.

Export:

```json
{ "gauntlet": "name", "exportedAt": "…", "answered": 38, "total": 38,
  "responses": { "T01": { "choice": "A|B|N", "via": "key|this", "note": "", "ms": 4210,
                          "mode": "flip|side", "flips": 3, "at": "…" } } }
```

`via: "this"` means Enter on the side showing. `flips` counts Space presses.

### Adaptive page (`gauntlet-adaptive.tpl.html`)

- `DATA.seed`: an integer. The next pair is a pure function of the seed and the answers so far,
  so a reload or an undo always shows the same pair.
- `DATA.searches`: `[{ id, base, far, res, grain, group?, label?, unit?, ... }]`
  - `base`: the current value.
  - `far`: the first probe, an obviously bad value.
  - `res`: stop when the bracket is this narrow.
  - `grain`: probes snap to multiples of it.
  - `group`: optional. Consecutive pairs avoid repeating a group, such as an excerpt.
- `DATA.nulls`: `[{ at, group?, ... }]`. A null pair is shown once `at` answers have been given.
  Leftover nulls go at the end.
- `DATA.confirmGap`: the minimum number of pairs between a search's last probe and its confirm.
  The confirm repeats the nearest losing value with the sides swapped.
- `srcdoc(item, variant)` returns the HTML for one side.
  - `item` is `{ kind: 'probe'|'confirm'|'null', search, value, nullIdx, group, variantOn }`.
  - `variant` is true when this side should show `value`, and false for the base.
  - For a null, `variant` is false on both sides, and `item.nullIdx` points into `DATA.nulls`.
- `frameWidth(item)` is optional, as on the fixed page. Use it when a value itself changes the
  width.

Export: `{ gauntlet, exportedAt, answered, summary, history }`.

- `history` is every answer in order. Each entry has the item fields plus the answer fields
  above. `choice` is a side, so compare it with `variantOn` to tell whether the variant won.
- `summary` maps each search id to `{ label, unit, base, far, heldUpTo, lostAt, done, beatBase }`.
  - `heldUpTo` is the furthest value that held, meaning the variant was preferred or answered
    "same".
  - `lostAt` is the nearest value that lost. It is null when even `far` held.
  - `beatBase` lists the probe values where the variant was preferred outright.

## Checking a page

Any check that proves the page works will do. These have worked:

- **Render signature.** Drive the page headless and compare a signature of each pair's two sides.
  The signature has to cover what the variables change: layout and colour for CSS, frames or
  audio for media, text for copy. A variant identical to its base usually means the material
  already had that value.
- **Simulated reader.** For an adaptive page, answer with a simulated reader whose limits are
  known. Each search should end within one step of its limit, undo should show the same pair
  again, and the page should reach its done screen.
- **Screenshots.** Look at the first pair and the most extreme pair of each variable.

## Other media

`srcdoc` can hold anything a browser plays, so video, audio, images and charts fit the same
templates. A `<video>` or `<audio>` side needs embedded or local files, and long clips slow every
pair down. Keep media pairs short and pages shorter.
