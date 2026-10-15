# From a page to its larger context

At the seam from writing to navigation, SLASH_MY turns the page the viewer has been reading into a node in a document graph. The source supports it as an example of a camera move that widens the scope of an idea while keeping its subject.

The inspected source is the SLASH_MY production at its 2026-10-02 snapshot (`32dec413`), read in John's workspace, and the [versioned SLASH_MY case](SLASH_MY.md) records what that snapshot contained. The cited files are the seam document (`SEAMS.md`), the scene API (`SCENE_API.md`), the engine (`engine.js`), the findable scene (`scenes/findable.js`), and the brief (`BRIEF.md`). Exact timings are true of this snapshot.

| Scope | Choice and route |
| --- | --- |
| Controls | Measured page bounds, page-to-node scale, transform origin, clipping, and camera zoom. Set the reference frame and transformation origin before tuning movement, keep scene and local coordinates distinct, and measure the final layout during setup. |
| Technique | A pullback followed by an axial cut to rest. Name what the camera move should reveal before choosing it. Large movement serves a question or the reveal of a result; where reading matters, a fixed overview with a labeled inset keeps the context. |
| Scene role | Reveal that this document belongs to a larger system. [Meaningful reveal](../patterns/Meaningful%20reveal.md) asks what new relationship the larger frame shows. |
| Sequence role | A [continuity carrier](../patterns/Continuity%20carriers.md) links the quiet writing passage to the rising activity of navigation. |
| Direction | [Density and rest](../patterns/Density%20and%20rest.md) lets the writing valley hand material to the next section and keeps it from being a disposable pause. |
| Implementation and review | The engine's page geometry and pull, the findable scene's graph drawing, and the seam document's boundary contract. Follow the page as the same object, and inspect the boundary geometry and the sound handoff. |

## How the source keeps the page

`PULL` spans beats 95–96, or 47.5–48 film seconds. `pageGeom()` maps a full-width page into findable's node rectangle, set to x 542, y 228, width 36, height 64. The height is a minimum: the engine allows for the full extent of the written page and does not silently crop it to a nominal node.

`pullAt()` eases the page's visible share of the frame toward `PULL.cut = 0.3` and solves for the zoom that gives it. The page reaches the boundary still moving at the prescribed endpoint rate, then cuts to rest at beat 96. The ease is deliberately stopped short of the tiny node. The seam document gives the reason: put the largest perceptual change on the sync point, and do not spend it earlier while the page is still large.

**Reported:** the production's session records in John's workspace keep the recorded revisions by which this end state was reached. A review reopened a settled move because it had new evidence, which is the rule in [Convergence](../knowledge/Convergence.md) that evidence can bring a closed item back. The pull was first eased on the zoom value. The review measured what that did: the page's motion was spent while it still filled the frame, the page was a 40-pixel dot on the cut's beat, and the boundary's sync points landed 250 ms early. The repair re-eased the pull on what the eye sees, the page's share of the frame. The largest frame-to-frame change fell from 0.115 to 0.084 and then to 0.075, and the second sync point moved from 250 ms to 100 ms early. That is closer but still early, and the history records it as a targeted improvement, leaving the rest to the next round. The recorded reason is the seam document's purpose: put the largest perceptual change on the sync point.

Findable starts drawing the surrounding graph during the pull, under the shared camera, clipped outside the page. At 96 the engine stops drawing the page and findable takes over through `env.pageNode.draw`. The source freezes the content at `PAGE_FREEZE = PB1 - 0.001`, which the documentation calls the page frozen at 96. Because the content and geometry are kept, the page the viewer just read is not swapped for a generic icon.

The node holds for three frames, then opens into the next document view. The brief and the seam document also place the incoming clave at beat 95.5, under the outgoing page. The picture keeps the page recognizable across the transition, and the music prepares the next section.

## Alternative and review

For a dense factual diagram, a fixed overview with a labeled inset may keep comparison easier than shrinking the page. For unrelated subjects, use a clear cut and a label, so the move does not imply that one contains the other.

Inspect the frames before the pull, the last frame before 96, the cut, and the first frames of the unfolding. Does the page stay the same object with its intended crop? Is it drawn once? Can a viewer find it in the graph at normal playback speed? Then listen across the boundary and judge the rise around it. The numerical contract checks the implementation; whether the transition reads as continuous is a playback question.

[Direction](../knowledge/Direction%20and%20critique.md) · [Workbenches and contracts](../knowledge/Production%20workbench.md) · [Home](../Home.md)
