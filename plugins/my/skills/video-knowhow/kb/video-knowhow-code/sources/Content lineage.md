# Content lineage

Each page of the package draws on one or more of three lineages, and the package keeps a fourth kind of record, the comparison runs. The lineages are not equally authoritative, and this ledger records which ones stand behind each page.

- **What was learned from SLASH_MY**: technique, parameter values, and measurements taken from SLASH_MY at its 2026-10-02 snapshot (`32dec413`; audio snapshots `fd543f2a` and `f7f9d199`), inspected in John's workspace. SLASH_MY is the one production in the package that John has endorsed. On 2026-10-02 John called it "the most polished/convincing", a judgment about the whole film. The [samples](../samples/README.md) are excerpted from it. The [starter](../starter/README.md) is a small skeleton with the same production structure: one HTML page draws each frame from its frame number, and a script writes the soundtrack from the same beat clock. SLASH_MY's session records, also in John's workspace, go beyond the end state. They record revisions, each decision kept with its before, its after, and the recorded reason, and pages cite them in Reported claims that name the recorded revision.
- **External documented practice**: standards, specifications, research papers, and reference implementations, each checked against its source. The [audio source ledger](Audio%20sources.md) holds the audio claims and their status. [Production lineage](Production%20lineage.md) holds the decades-old documented mechanisms behind the operations.
- **The chatlog**: the record of an earlier production session, indexed by the [chatlog index](Chatlog%20index.md). The paths it names start with `ax-day/...`. It records Stage intro, FOXTALE, and the boundary tests, and it is evidence for the craft of making these films. Nothing in it is specific to SLASH_MY.
- **Comparison runs**: the comparison lab in John's workspace (runs A through C2, D-001 through D-008, and the AX DAY reconstruction). The runs were attempts at a further production. They date from 2026-09-29, before SLASH_MY production began on 2026-10-01, and SLASH_MY superseded the series. The last run, D-008, was left awaiting John's choices, and no run came after it. They are kept as records of the attempt and as specimens you can read. The lab stays in John's workspace, and the case pages report what it found.

Wherever a technique is validated against John's judgment, that judgment covers a single film. External documented practice and the chatlog are backed by their own sources. What was learned from SLASH_MY is backed by one production, the one John endorsed.

## Dating

The dates below are when each page was first recorded. The code shelf predates SLASH_MY: it was built from the earlier production's chatlog on 2026-09-29, and its audio pages were rewritten from the two soundtracks on 2026-10-14. Every craft page and case in the tables below, except Convergence (2026-10-14 21:22) and Two soundtracks (2026-10-14 09:26), was first recorded in one pass at 2026-10-02 19:22. That is about an hour after the SLASH_MY snapshot `32dec413` (18:25) that the pages cite, and one day after SLASH_MY production began (2026-10-01); production commits continued through 2026-10-03.

The dates show that no craft page predates the film it describes. The film did have craft direction, and it came before the pages. The brief set it on the first production day (2026-10-01): section variety on one theme, motifs that recur and change role and register on a second viewing, the arc and pathos of the whole piece, and a seams table. A picture review of the whole film ran before the first round and found it "good at the level of each slot, but the film doesn't hold together as one piece yet". Later rounds included a motifs review, and revision decisions kept settled motifs from being reopened. The craft shelf is an after-the-fact synthesis of that craft-directed production, and what its pages add is the generalization. The craft pages also draw on the motion reference, a summary of a public upstream motion-design collection. It was compiled from gathered external sources on the same day (2026-10-02 13:25), hours before the snapshot, so its influence on the film is not established either.

The two snapshots fall on either side of a superseded mix fix. In SLASH_MY's picture snapshot `32dec413`, the beat-72 clip step acts on the whole mix. A later round replaced it with a band-only dip (`edd3024a`), and that is the form in the audio snapshot `fd543f2a`. The craft cases read `32dec413` and the audio pages read `fd543f2a`, so the two shelves describe different mixes at the same beat. Each page's values are true of the snapshot it names.

## Code shelf

The evidence labels column lists the bold labels each page uses, as defined in [reading a claim](../Editorial%20notes.md#reading-a-claim); "none" means the page has no bold label. Craft pages say how their evidence was gathered in prose, using the craft shelf's [evidence distinctions](../../video-knowhow-craft/Editorial%20notes.md#evidence-distinctions). The three count columns give how many times each page's current text mentions SLASH_MY, cites a `C-<line>` chatlog anchor, and mentions a comparison run (A/B, C, C2, D-001 through D-008, the reconstruction).

| Page | Lineage | Evidence labels | SLASH_MY | chatlog | lab |
| --- | --- | --- | ---: | ---: | ---: |
| [Accessibility and perception](../knowledge/Accessibility%20and%20perception.md) | Mixed: external practice, SLASH_MY values | Checked (SLASH_MY); Reported (SLASH_MY); Interpretation; Interpretation (SLASH_MY); Source status: supported | 8 | 0 | 0 |
| [Assets and provenance](../knowledge/Assets%20and%20provenance.md) | Mixed: chatlog, external practice | none | 0 | 5 | 0 |
| [Audio synthesis](../knowledge/Audio%20synthesis.md) | External documented practice | none | 0 | 0 | 0 |
| [Audiovisual synchronization](../knowledge/Audiovisual%20synchronization.md) | Mixed: SLASH_MY, AX DAY reconstruction, external practice | Checked; Reported; Interpretation; Untested idea | 8 | 0 | 8 |
| [Authoring approaches](../knowledge/Authoring%20approaches.md) | External documented practice | none | 0 | 0 | 0 |
| [Capability boundaries](../knowledge/Capability%20boundaries.md) | Chatlog | none | 0 | 10 | 0 |
| [Capture and encoding](../knowledge/Capture%20and%20encoding.md) | Mixed: external practice, SLASH_MY | none | 3 | 0 | 0 |
| [Delivery and color](../knowledge/Delivery%20and%20color.md) | External documented practice | none | 0 | 0 | 0 |
| [Deterministic rendering](../knowledge/Deterministic%20rendering.md) | Mixed: external practice, SLASH_MY revision | Reported (SLASH_MY) | 2 | 0 | 0 |
| [Dynamics and spectral carving](../knowledge/Dynamics%20and%20spectral%20carving.md) | Mixed: SLASH_MY, AX DAY reconstruction, ledger practice | Checked; Checked (SLASH_MY); Reported; Interpretation; Untested idea; Source status: supported; Source status: partly; Source status: partly (one example); Source status: practice | 33 | 0 | 8 |
| [Groove and feel](../knowledge/Groove%20and%20feel.md) | Mixed: SLASH_MY, AX DAY reconstruction, external studies | Checked; Checked (SLASH_MY); Interpretation; Source status: supported | 27 | 0 | 9 |
| [Iteration and parameterization](../knowledge/Iteration%20and%20parameterization.md) | Mixed: chatlog, SLASH_MY revision | Reported (SLASH_MY) | 2 | 8 | 0 |
| [Mastering and delivery](../knowledge/Mastering%20and%20delivery.md) | Mixed: SLASH_MY, AX DAY reconstruction | Checked; Checked (SLASH_MY); Reported; Reported (SLASH_MY); Reported (commit); Interpretation; Untested idea; Source status: supported; Source status: partly; Source status: partly (one example) | 38 | 0 | 18 |
| [Music under voice-over](../knowledge/Music%20under%20voice-over.md) | Mixed: SLASH_MY, external research | Checked (SLASH_MY); Reported; Interpretation; Source status: supported; Source status: supported (product review); Source status: supported (vendor); Source status: partly; Source status: partly (one example); Source status: partly (secondary); Source status: practice | 16 | 0 | 1 |
| [Pixel art and stylization](../knowledge/Pixel%20art%20and%20stylization.md) | External practice, one trace observation | none | 0 | 0 | 0 |
| [Production bootstrap](../knowledge/Production%20bootstrap.md) | Mixed: SLASH_MY pipeline, external installation practice | Checked; Checked (one machine) | 2 | 0 | 0 |
| [Raster, vector, and DOM](../knowledge/Raster%20vector%20and%20DOM.md) | External documented practice | none | 0 | 0 | 0 |
| [Representation models](../knowledge/Representation%20models.md) | External documented practice | none | 0 | 0 | 0 |
| [Shaders and 3D](../knowledge/Shaders%20and%203D.md) | External documented practice | none | 0 | 0 | 0 |
| [Sound sources and voices](../knowledge/Sound%20sources%20and%20voices.md) | Mixed: SLASH_MY, ledger practice | Checked; Checked (SLASH_MY); Reported; Interpretation; Source status: supported; Source status: partly; Source status: open | 35 | 0 | 19 |
| [Space and delay](../knowledge/Space%20and%20delay.md) | Mixed: SLASH_MY, ledger practice | Checked; Checked (AX DAY reconstruction); Checked (SLASH_MY); Reported; Interpretation; Source status: supported; Source status: partly | 22 | 0 | 11 |
| [Time and motion](../knowledge/Time%20and%20motion.md) | External documented practice | none | 0 | 0 | 0 |
| [Transitions and continuity](../knowledge/Transitions%20and%20continuity.md) | External documented practice | none | 0 | 0 | 0 |
| [Typography in motion](../knowledge/Typography%20in%20motion.md) | External documented practice | none | 0 | 0 | 0 |
| [Verification](../knowledge/Verification.md) | Mixed: external practice, SLASH_MY revision | Reported (SLASH_MY) | 2 | 0 | 0 |
| [Visual hierarchy and composition](../knowledge/Visual%20hierarchy%20and%20composition.md) | External documented practice | none | 0 | 0 | 0 |

| Case | Lineage | Evidence labels | SLASH_MY | chatlog | lab |
| --- | --- | --- | ---: | ---: | ---: |
| [Boundary tests](../cases/Boundary%20tests.md) | Chatlog | none | 0 | 31 | 0 |
| [FOXTALE](../cases/FOXTALE.md) | Chatlog | Interpretation | 0 | 33 | 0 |
| [Soundtrack code](../cases/Soundtrack%20code.md) | Mixed: SLASH_MY, AX DAY reconstruction (code record) | Checked; Checked (AX DAY reconstruction); Checked (SLASH_MY); Reported; Reported (commit); Reported (run notes); Interpretation; Source status: supported; Source status: practice; Source status: open | 126 | 0 | 78 |
| [Stage intro](../cases/Stage%20intro.md) | Mixed: chatlog, reconstruction specimen | Reported (chatlog); Interpretation | 1 | 24 | 4 |

## Craft shelf

Every craft page and case except [Convergence](../../video-knowhow-craft/knowledge/Convergence.md) (2026-10-14 21:22) and [Two soundtracks](../../video-knowhow-craft/cases/Two%20soundtracks.md) (2026-10-14 09:26) was first recorded at 2026-10-02 19:22 (see Dating). The two exceptions came later still, so none predates SLASH_MY. The pages are an after-the-fact synthesis of a production that craft direction demonstrably shaped at the level of its brief and reviews. Their generalizations are informed interpretation and have yet to guide a production of their own. Recorded revision is the exception. [Convergence](../../video-knowhow-craft/knowledge/Convergence.md) and the recorded-revision passages in the case pages give decisions read from the production's session records, each with a before, an after, and the recorded reason. Those passages report the working practice as the records give it. The generalizations drawn from them are still the craft shelf's own.

| Page | Lineage | Evidence labels | SLASH_MY | chatlog | lab |
| --- | --- | --- | ---: | ---: | ---: |
| [Convergence](../../video-knowhow-craft/knowledge/Convergence.md) | SLASH_MY recorded revision (session records) | none | 4 | 0 | 0 |
| [Direction and critique](../../video-knowhow-craft/knowledge/Direction%20and%20critique.md) | Mixed: interpretation, SLASH_MY, C-run record | none | 7 | 0 | 3 |
| [Form, material, and depth](../../video-knowhow-craft/knowledge/Form%20material%20and%20depth.md) | Comparison runs (D-003, D-004), interpretation | none | 0 | 0 | 3 |
| [Foundations](../../video-knowhow-craft/knowledge/Foundations.md) | Interpretation routing to the code-shelf theory pages | none | 0 | 0 | 0 |
| [Motion character](../../video-knowhow-craft/knowledge/Motion%20character.md) | Mixed: interpretation, external reference shelf | none | 1 | 0 | 1 |
| [Musical development](../../video-knowhow-craft/knowledge/Musical%20development.md) | Mixed: interpretation, AX DAY reconstruction example, C and C2 records | none | 3 | 0 | 8 |
| [Production workbench](../../video-knowhow-craft/knowledge/Production%20workbench.md) | Interpretation routing to the code-shelf pages | none | 1 | 0 | 1 |
| [Sound production](../../video-knowhow-craft/knowledge/Sound%20production.md) | Mixed: interpretation, SLASH_MY, code-shelf audio pages | none | 4 | 0 | 8 |
| [Typographic events](../../video-knowhow-craft/knowledge/Typographic%20events.md) | Mixed: AX DAY reconstruction walkthrough, interpretation | none | 2 | 0 | 8 |

| Case | Lineage | Evidence labels | SLASH_MY | chatlog | lab |
| --- | --- | --- | ---: | ---: | ---: |
| [Anticipation to title](../../video-knowhow-craft/cases/Anticipation%20to%20title.md) | Comparison lab (AX DAY reconstruction), interpretation | none | 2 | 0 | 7 |
| [Comparison runs](../../video-knowhow-craft/cases/Comparison%20runs.md) | Comparison runs | none | 1 | 0 | 27 |
| [Jitter to repair](../../video-knowhow-craft/cases/Jitter%20to%20repair.md) | What was learned from SLASH_MY | Reported | 6 | 0 | 0 |
| [SLASH_MY](../../video-knowhow-craft/cases/SLASH_MY.md) | What was learned from SLASH_MY | none | 7 | 0 | 2 |
| [Page to larger context](../../video-knowhow-craft/cases/Page%20to%20larger%20context.md) | What was learned from SLASH_MY | Reported | 3 | 0 | 0 |
| [Two soundtracks](../../video-knowhow-craft/cases/Two%20soundtracks.md) | Mixed: SLASH_MY, AX DAY reconstruction | none | 11 | 0 | 12 |

## Reading the two shelves together

On the code shelf, the relied-on pages are the externally documented practice and what was learned from SLASH_MY's audio. The craft shelf adds interpretation on top. Its pages turn the SLASH_MY observations and the negative findings of the comparison runs into craft statements meant to transfer to other work, so read them as interpretation. A Reported passage that gives a recorded revision reports the production's own practice directly. A claim's evidence label, on the code shelf or in the craft shelf's [evidence distinctions](../../video-knowhow-craft/Editorial%20notes.md#evidence-distinctions), says how the claim was verified. This ledger says where it comes from.
