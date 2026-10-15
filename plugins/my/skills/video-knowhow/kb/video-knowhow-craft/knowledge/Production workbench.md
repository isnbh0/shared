# Production workbench

Choose a representation and a time model that keep the decisions the piece depends on, then check the rendered and encoded files the audience will actually receive. The code shelf pages remain canonical, and this page connects them to the craft pages.

## Prepare the representation and assets

Use [representation models](../../video-knowhow-code/knowledge/Representation%20models.md), [authoring approaches](../../video-knowhow-code/knowledge/Authoring%20approaches.md), and [assets and provenance](../../video-knowhow-code/knowledge/Assets%20and%20provenance.md). A flat image gives one view, so a camera move that shows surfaces the image never had needs more source material. Text needs real fonts and measured bounds. A prepared illustration can hold character that would be expensive to rebuild procedurally.

The [Operations](../../video-knowhow-code/Operations.md#describe-and-organize-the-sources) page lists the source, parameter, mapping, layout, compositing, and repetition operations. One upstream lesson applies as is: an archived implementation snippet usually depends on its own runtime (fonts, helper libraries, build steps), and it runs as a standalone program only with its full HTML and runtime taken from the source snapshot.

## Own time and shared events

[Deterministic rendering](../../video-knowhow-code/knowledge/Deterministic%20rendering.md) explains evaluation at the requested time, seeded variation, readiness, and simulation history. When frames are requested out of order, a stateful simulation needs fixed stepping, checkpoints, or a bake. Getting the same frame state every time and getting byte-identical encoded output are separate claims.

For audiovisual events, record one sync landmark and its units, then derive the visual times and sample times from it through [synchronization](../../video-knowhow-code/knowledge/Audiovisual%20synchronization.md). The trigger time may differ from the moment of peak brightness or the audible attack. The AX DAY reconstruction's `T.DROP` gives picture and sound one shared event, and the [worked title](Typographic%20events.md) shows why shared timing alone does not guarantee that the text is complete and readable on that frame.

## Make collaboration boundaries visible

The [SLASH_MY case](../cases/SLASH_MY.md) shows a scene contract: local beats, shared helpers, transforms, who owns each handoff, and one source for score events. Its seam document (`SEAMS.md`) records what each side must keep intact. The procedure you can reuse: before two scenes are composed together, state the outgoing object or camera state, the incoming state, the coordinate space, the overlap interval, and the sound that carries across.

A smaller project may need only a short table of boundaries. The point is to prevent double drawing, a camera reset, an inherited alpha, or two impacts scheduled independently. Inspect before, on, and after the seam, including out-of-order seeks. [Continuity carriers](../patterns/Continuity%20carriers.md) explains which relationships are worth that engineering effort.

## Capture, inspect, and deliver

| Question | Canonical procedure | What the check establishes |
| --- | --- | --- |
| Are the intended frames captured? | [Capture and encoding](../../video-knowhow-code/knowledge/Capture%20and%20encoding.md) | The captured frames themselves; a browser preview may use different clocks or asset readiness. |
| Does compositing preserve the intended surface? | [Raster, vector, and DOM](../../video-knowhow-code/knowledge/Raster%20vector%20and%20DOM.md), [shaders and 3D](../../video-knowhow-code/knowledge/Shaders%20and%203D.md) | Whether multiple samples have correct weights and a chosen color-space treatment. |
| Does the sound retain its hierarchy? | [Sound production](Sound%20production.md), [audio synthesis](../../video-knowhow-code/knowledge/Audio%20synthesis.md) | Peak and loudness measurements check level; musical appeal is a question for listening. |
| Does the actual file work? | [Delivery and color](../../video-knowhow-code/knowledge/Delivery%20and%20color.md), [verification](../../video-knowhow-code/knowledge/Verification.md) | Decode, frame count, color, and stream checks establish the file's technical properties; pacing and comprehension need playback. |
| Can revisions be judged? | [Iteration and parameterization](../../video-knowhow-code/knowledge/Iteration%20and%20parameterization.md) | Whether each swept parameter answers an interpretable perceptual question. |

Inspect the first useful frame, the strongest treatment, the last arrival, the scene boundaries, and the ending, then watch and listen to the whole encoded file at delivery size. Check the way the file will actually be opened. FOXTALE once failed when viewed standalone, after a render that had succeeded; its [case](../../video-knowhow-code/cases/FOXTALE.md) explains the reported repair and the limits on what is available.

John's workspace keeps preliminary notes on a lintable video system. They ask how much of a film's sync between picture, audio, and copy could be declared and checked exactly, using an engine trace mode, declared cue lists, and lint rules. Passing a declared rule is evidence about that rule. [Diagnosis](../maps/Diagnose.md) and [whole-piece critique](Direction%20and%20critique.md) still need perceptual questions.

[Scopes](../maps/Scopes.md) · [Home](../Home.md)
