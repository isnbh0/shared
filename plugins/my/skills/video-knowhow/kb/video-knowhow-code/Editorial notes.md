# Editorial notes

These pages organize knowledge from a chatlog and from references checked separately. The chatlog holds requests, code, tool output, interpretation, and claims made looking back, and each of these carries a different weight as evidence.

## Reading a claim

Each claim carries one of four evidence labels, defined in the Glossary: [Checked](Glossary.md#checked), [Reported](Glossary.md#reported), [Interpretation](Glossary.md#interpretation), and [Untested idea](Glossary.md#untested-idea). A Reported claim is useful as a case.

A label is a bold lead-in that ends in a colon inside the bold, written `**Head:**` or `**Head (qualifier):**`. The heads are Checked, Reported, Interpretation, Untested idea, and, for a claim backed by the audio source ledger, `Source status: supported`, `partly`, `practice`, or `open`. A qualifier is optional and comes from a short fixed list: Checked takes SLASH_MY, AX DAY reconstruction, both productions, or one machine; Reported takes SLASH_MY, AX DAY reconstruction, chatlog, commit, run notes, recorded revision, or comparison-run record; Interpretation takes SLASH_MY or AX DAY reconstruction; Untested idea takes none; a source status takes secondary, vendor, product review, or one example. Detail such as a commit hash goes in the sentence, as in `**Reported (commit):** according to commit …`. Bold text that starts with a head is always a whole label. Any other bold lead-in, such as a step name or a term, puts the colon or a period outside the bold: `**Fonts**:` or `**Fonts.**`. `tools/termcheck.py` in the craft shelf checks this grammar, and its docstring lists the exact rules.

Keep these distinctions in the prose where they matter. Write page titles and maps to help a reader make a decision, and keep them from turning the conversation into a universal recipe. A case can keep exact parameters and outcomes. A focused concept page explains why the choice matters and when it may transfer to another piece.

An evidence label says how a claim was verified. Where the content comes from is a separate question, answered in [content lineage](sources/Content%20lineage.md). Every page draws on what was learned from SLASH_MY, external documented practice, the chatlog, or the comparison runs, and each source is kept as the record of the attempt it was.

The craft shelf labels evidence by how it was gathered: source inspection, rendered-frame inspection, continuous playback, listening, human feedback, and interpretation or recommendation. Its [evidence distinctions](../video-knowhow-craft/Editorial%20notes.md#evidence-distinctions) map those six labels onto these four.

## Sources and maintenance

The [chatlog index](sources/Chatlog%20index.md) describes the chatlog and locates the relevant passages by line number, record UUID where one exists, and a description of the content. The chatlog files stay in John's workspace. A chatlog citation says what the conversation contains. It does not show that a tool result, a claim about an external platform, or a visual judgment is independently true. [Social examples](sources/Social%20examples.md) keeps a creator's description of their process apart from what the inspected media shows. Focused pages link directly to separately checked sources for technical and current claims, and relied-on passages are copied into `sources/excerpts/`.

The [audio source ledger](sources/Audio%20sources.md) holds the external sources behind the audio technique pages. Each claim has a [source status](Glossary.md#source-status) (supported, partly, practice, or open), and pages cite it with the source status lead-in described in [reading a claim](#reading-a-claim). Add a new external audio claim to the ledger before citing it.

Sources are named in prose: which production, which snapshot, what was inspected. The SLASH_MY audio snapshots are `fd543f2a` and `f7f9d199`; the AX DAY reconstruction's snapshot is `e5ae340d`. [Soundtrack code](cases/Soundtrack%20code.md#snapshots-and-reading-the-code) lists them.

When you add material, keep the smallest source reference that lets a reader find it, keep what was observed apart from what was inferred, and state the relevant limit next to the claim. Recheck claims about current product behavior and support when they bear on a new decision. Production history, rebuttals nobody needs, and source bookkeeping stay out of reader pages.

## Page format and links

A page is Markdown without frontmatter and starts with its H1. File names are sentence-case words with spaces, such as `Music under voice-over.md`; the H1 can be fuller than the file name.

- **Concept pages** in `knowledge/`, `theory/`, `recipes/`, and `sources/`, plus the Glossary and Operations, have a noun-phrase H1 that names the subject: "Groove and feel", "Audio source ledger".
- **Maps** in `maps/` route a decision. Their H1 names the area ("Theory", "Untested ideas") or the reader's task or question ("Choose a visual representation", "What can code specify?").
- **Cases** in `cases/` start with "Case:" and a noun phrase: "Case: FOXTALE pixel-game trailer".
- **Ledgers** in `sources/` hold the source records: audio claims, chatlog citations, social examples, and the lineage of every page.

Links are relative and keep the target's extension, `.md` for pages. Encode spaces as `%20`. Heading anchors use GitHub slugs, such as `#snapshots-and-reading-the-code`. Link a file, never a folder: for a folder, link its `README.md` or the file the reader needs.

Links into `../video-knowhow-craft/` stay inside the zip package. Every shipped link is an internal relative link or a web link, and pages carry no paths, commands, or snapshot links into John's workspace. When content comes from a workspace collection (the reference shelves, the SLASH_MY production source, the comparison runs, or the chatlog), the page says so in prose and inlines the relied-on material. Rendered MP4s and WAVs from the productions stay in the workspace, and each shipped mention of one names the written note or explanation that records the finding.

From this folder, `uv run ../video-knowhow-craft/tools/linkcheck.py` checks every link and heading anchor on both shelves. It fails only on broken links inside the package. `uv run ../video-knowhow-craft/tools/package.py --dry-run` runs the same check on the files the zip will contain.
