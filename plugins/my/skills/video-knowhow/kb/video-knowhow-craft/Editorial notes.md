# Editorial notes

This shelf is drawn from recorded productions and collections. It is working craft guidance across scopes, written as rules of thumb and starting points to adapt. A technique can work as documented and still fail in a particular film.

## Page roles

Maps route a reader's task. Decision notes explain conditions, alternatives, and diagnostics. Technique guides explain how a technique works and which controls interact. Patterns explain relationships that recur at scene, sequence, or direction scope. Recipes demonstrate an arrangement. Cases keep the intent, the source version, the observations, and what remains uncertain. Workbench guides explain procedures and constraints. A page can combine these forms where that makes the explanation better, and no page needs empty template sections.

## Evidence distinctions

The craft shelf's six evidence labels are defined in the Glossary: [source inspection](../video-knowhow-code/Glossary.md#source-inspection), [rendered-frame inspection](../video-knowhow-code/Glossary.md#rendered-frame-inspection), [continuous playback](../video-knowhow-code/Glossary.md#continuous-playback), [listening](../video-knowhow-code/Glossary.md#listening), [human feedback](../video-knowhow-code/Glossary.md#human-feedback), and [interpretation or recommendation](../video-knowhow-code/Glossary.md#interpretation-or-recommendation). A comment in source code can be stale, so check the order in which the code runs before describing it. Attribute older frame observations to their run notes unless you inspect the frames again. Put the interpretation label next to its claim, in tables too.

These six say how evidence was gathered. The [code shelf](../video-knowhow-code/Editorial%20notes.md#reading-a-claim) uses four labels that say how well a claim stands. Its pages, such as the [Soundtrack code case](../video-knowhow-code/cases/Soundtrack%20code.md), keep their labels when cited here. When a claim moves between the shelves, the labels correspond as follows. A bold label written with its colon inside the bold follows the code shelf's label grammar in [reading a claim](../video-knowhow-code/Editorial%20notes.md#reading-a-claim).

| Label here | Code shelf label |
| --- | --- |
| Source inspection | Checked |
| Rendered-frame inspection | Checked when inspected directly; Reported when the observation comes from run notes |
| Continuous playback, listening, human feedback | Reported, attributed to its run notes, commit, or John |
| Interpretation or recommendation | Interpretation; Untested idea for an extension |

The editing behind this shelf was a reading of recorded source and prose, done without rerendering, watching continuous video, or auditioning scores. An evidence label says how a claim was gathered or checked. Where the claim comes from is recorded in [content lineage](../video-knowhow-code/sources/Content%20lineage.md): what was learned from SLASH_MY, external documented practice, the chatlog, and the comparison runs, each kept as the record of the attempt it was. The [SLASH_MY case](cases/SLASH_MY.md#what-this-case-is) states what John's 2026-10-02 verdict covers. Older case observations keep the review limits they were recorded with.

## Values and visual judgment

A numerical default is either a starting point to adapt or a property of the case it was cited from. After changing one, recheck content length, font metrics, size, units, camera crop, phrase, and delivery. A recipe's five seconds may not give replacement copy enough reading time.

Use source inspection to find causes worth testing, and judge the result with the kind of looking or listening that fits it. More grain, blur, loudness, or code does not prove an improvement. A clean encode establishes the delivery properties, and emotional force and comprehension need their own review. [Diagnose](maps/Diagnose.md) offers alternatives suited to the passage in front of you and can be used without this maintenance page.

## Availability and attribution

The guidance rests on recorded prose and source. Optional media that stays on John's machine is labeled where it is linked and comes with a written explanation or preview. Remote examples stay with the source records that cite them and remain external dependencies. Every route in this shelf works from the written prose alone.

The motion reference is drawn from the public [Awesome AI Motion](https://github.com/gongnyang/awesome-ai-motion) collection and kept in John's workspace with a recorded upstream snapshot, bilingual records, stable IDs, and per-card attribution. Where a page here leans on one of its cards, it inlines the relied-on claim and names the source in prose.

Case pages name their sources in prose: the production, the snapshot (the SLASH_MY picture snapshot `32dec413`, its audio snapshots `fd543f2a` and `f7f9d199`, the AX DAY reconstruction `e5ae340d`), and what was inspected in John's workspace.

## Page format and links

A page is Markdown without frontmatter and starts with its H1. File names are short sentence-case words with spaces, such as `Sound production.md`; the H1 can be fuller than the file name.

- **Knowledge pages and patterns** in `knowledge/` and `patterns/`, plus Integration ownership, have a noun-phrase H1 that names the subject: "Motion character", "Continuity carriers". A walkthrough can name its procedure instead: "Execute a typographic event".
- **Maps** in `maps/` name the reader's task: "Make a deliverable", "Diagnose a weak passage", "Study production cases".
- **Cases** in `cases/` name the production or the arc they follow as a noun phrase: "SLASH_MY", "From jitter to an understandable repair".

Links are relative and keep the target's extension, `.md` for pages. Encode spaces as `%20`. Heading anchors use GitHub slugs, such as `#evidence-distinctions`. Link a file, never a folder: for a folder, link its `README.md` or the file the reader needs.

Links into `../video-knowhow-code/` stay inside the zip package. Every shipped link is an internal relative link or a web link, and pages carry no paths, commands, or snapshot links into John's workspace. When content comes from a workspace collection (the reference shelves, the SLASH_MY production source, the comparison runs, or the chatlog), the page says so in prose and inlines the relied-on material.

## Maintenance

[Integration](Integration.md) records which page owns each shared subject. Update the owning explanation once and link to it from other scopes. The upstream motion reference and the SLASH_MY production source are read-only: update this shelf and its recorded snapshot, and leave their files as they are.

The [roundup](roundup/motion-production-roundup.md) is a numbered outline of this shelf, with a [no-JavaScript HTML page](roundup/motion-production-roundup-no-js.html) and an interactive one beside it. Its glossary items link to the package Glossary and do not restate definitions. Do not edit the HTML pages by hand. From this folder, `uv run roundup/render_static.py` rebuilds both from the outline and `../video-knowhow-code/glossary.toml`.

Terms are edited in `../video-knowhow-code/glossary.toml`: `uv run tools/glossary.py` renders the [Glossary](../video-knowhow-code/Glossary.md), and `uv run tools/termcheck.py` reports retired variants in shipped prose.

For link review, run `uv run tools/linkcheck.py` from this folder. It checks files, exact case, heading anchors, encoded spaces, and folder targets across both shelves, against the files on this machine, and fails only on broken links inside the package. `uv run tools/package.py --dry-run` runs the same check and the term check on a fresh copy of the last commit, so it matches Git's tracked files and shows what the zip will contain. Review by hand what the checker cannot see: all five Home starting points, whether the inline summaries match the collections they summarize, and the three case paths in both directions. A required explanation should make sense without the workspace's files. `uv run tools/package.py OUT_DIR` builds the zip package of both shelves.

[Home](Home.md)
