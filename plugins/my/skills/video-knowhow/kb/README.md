# Video know-how

John's practice notes on making video with code, in two linked shelves, packaged from John's repository at commit `000082caeb02a9d7d6c2c2406111c3bd3e17df2f` (2026-10-16).

- **[Video know-how: craft](video-knowhow-craft/Home.md)** is the craft shelf: motion controls, scenes, sequences, whole-piece direction, sound production, and production cases. Its Home is the usual starting point.
- **[Video know-how: code](video-knowhow-code/Home.md)** is the code shelf: representations, reusable operations, audio technique, capture and delivery, and the original cases and boundary tests.

**What the package relies on.** The two shelves rest on externally documented practice and on what was learned from SLASH_MY, the skills hype film, the one production John endorses. The craft shelf's generalizations, drawn from SLASH_MY, are informed interpretation and have yet to guide a production of their own. The chatlog productions and the comparison runs are records of earlier attempts, since superseded, and are kept as evidence and as specimens. [Content lineage](video-knowhow-code/sources/Content%20lineage.md) classifies every page.

## What this package contains

The package holds two shelves whose pages link to each other, a [starter](video-knowhow-code/starter/README.md), a [showcase](video-knowhow-code/showcase/README.md) (a runnable example video built on the starter), [samples](video-knowhow-code/samples/README.md) generalized from the SLASH_MY production, the ledgers ([content lineage](video-knowhow-code/sources/Content%20lineage.md), the [audio source ledger](video-knowhow-code/sources/Audio%20sources.md), the [chatlog index](video-knowhow-code/sources/Chatlog%20index.md), [social examples](video-knowhow-code/sources/Social%20examples.md)), curated excerpts of relied-on external claims under `video-knowhow-code/sources/excerpts/`, the [Glossary](video-knowhow-code/Glossary.md), and [attribution](ATTRIBUTION.md). Every shipped link is an internal relative link or a web link, and workspace material is described in prose.

## Conventions

Each shelf's `AGENTS.md` lists its entry pages, ledgers, and reference areas: [craft](video-knowhow-craft/AGENTS.md) and [code](video-knowhow-code/AGENTS.md). The writing rules, including evidence labels and page format, are in each shelf's Editorial notes: [craft](video-knowhow-craft/Editorial%20notes.md) and [code](video-knowhow-code/Editorial%20notes.md). [Integration ownership](video-knowhow-craft/Integration.md) records which page owns each shared subject. Every defined term is in the [Glossary](video-knowhow-code/Glossary.md), rendered from `video-knowhow-code/glossary.toml`.

## Link and term checks

From this folder:

```sh
uv run video-knowhow-craft/tools/linkcheck.py
uv run video-knowhow-craft/tools/termcheck.py
```

The checkers use only the Python standard library (3.13 or later). The link checker reports four classes of relative link: ok, broken inside the package, outside the package, and missing local media. It exits non-zero only for broken links. On a clean run every relative link is ok; web links are not fetched. The term checker reports, as file:line, any retired term variant in the shipped prose, any glossary term used nowhere, and a Glossary page that is not the current render of glossary.toml. It exits non-zero on any finding.

## Starting a production

- `video-knowhow-code/starter/`: the runnable starter.
- `video-knowhow-code/showcase/`: a runnable example video built on the starter, with its stills, clips and sound snippets.
- `video-knowhow-code/samples/`: curated samples from the SLASH_MY production.
- `video-knowhow-code/knowledge/Production bootstrap.md`: the production bootstrap page.

## What stays in John's workspace

- **The SLASH_MY production source.** Pages describe it in prose: which files, which snapshot (`32dec413`, 2026-10-02; audio snapshots `fd543f2a` and `f7f9d199`), and what was inspected.
- **The reference shelves.** The motion reference (a generated mirror of the public [Awesome AI Motion](https://github.com/gongnyang/awesome-ai-motion) collection) and John's design collection. Pages inline the relied-on claims and name the collection.
- **The comparison lab.** The comparison runs (A through C2, D-001 through D-008, and the AX DAY reconstruction), kept as records of the attempt, which SLASH_MY superseded. The case pages report their findings.
- **The chatlog and rendered media.** [The chatlog index](video-knowhow-code/sources/Chatlog%20index.md) keeps line anchors, record UUIDs, and descriptions so a reader can find a passage. The chatlog files and the rendered MP4s and WAVs stay in the workspace; the showcase ships only its small review media, in `video-knowhow-code/showcase/media/`.

## Provenance

Snapshots are named in prose: the SLASH_MY picture snapshot `32dec413` (2026-10-02), its audio snapshots `fd543f2a` and `f7f9d199`, the flash-check snapshot `1fdc6435`, the AX DAY reconstruction's snapshot `e5ae340d`. The hashes identify versions in John's workspace, where the full source was inspected.
