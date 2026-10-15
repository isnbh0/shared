# From jitter to an understandable repair

This path starts at a control and works up to the reason for using it. Read the table downward from an effect, or upward from direction to implementation. The example is the pain-then-repair pattern SLASH_MY documents for its slots, as used in its visual-grounding scene. The reading comes from inspecting the recorded source.

The source was inspected at a 2026-10-02 snapshot of the production in John's workspace, and the full SLASH_MY case records what that snapshot contained. The cited files are the engine (`engine.js`), the scene API (`SCENE_API.md`), the brief, and the visual-grounding scene (`scenes/visual-grounding.js`).

| Scope | Choice and route |
| --- | --- |
| Controls | `steppedAt`, `stepped`, and `stepJitter` quantize local time and seeded offsets. [Motion character](../knowledge/Motion%20character.md) explains how they interact with sampling. |
| Technique | Stepped motion changes values or poses instantly, one step at a time, with no in-between frames. It gives the defect a held, jumpy look while the rest of the output can stay smooth. The technique is an upstream reference; this case records SLASH_MY's own implementation of it. |
| Scene role | [Defect to repair](../patterns/Defect%20to%20repair.md): show a recognizable failed relationship, then the actual action that corrects it, then the result. |
| Sequence role | The strike recurs while different mechanisms repair different problems. [Motif development](../patterns/Motif%20development.md) keeps the strike recognizable without repeating the whole shot. |
| Direction | [SLASH_MY's emotional progression](SLASH_MY.md) turns frustration into competent habits. The instability shows the complaint where it occurs and does not become the film's permanent style. |
| Implementation and review | The engine's stepped-time helpers, the visual-grounding scene's event script, and the scene API. Inspect the sharp holds, the strike, the correction, and the completed state the viewer reads. The SLASH_MY case records what was inspected. |

## The consequential interaction

At 60 output fps, the default 12 fps pain clock holds each step for five frames. Every half-frame shutter sample within a frame sees the same stepped state, and the seeded whole-pixel jitter also stays fixed for that step. The instability therefore looks crisp; if each sample drew new offsets, averaging would blur them into vibration. After its strike, the engine switches the pain line from stepped to smooth time. The prop's own clock and repair behavior are set by its scene.

**Reported:** the production's session records in John's workspace log one failure of this clock and its recorded revision. The clock sampled each step at its middle, so a step whose span crossed a sync point revealed the sync point at the step's start: the lock's landed state appeared about 42 ms (three frames, 1700–1702) before its beat. The fix changed the sampling rule and left the clock alone: a step that holds a sync point shows the frame before it until the frame reaches the beat (`aaf52b16`). The seam document (`SEAMS.md`) records the rule as "no hit shows before its beat"; "hit" in that rule means a picture event at the beat.

The visual-grounding source describes a guide that cracks into word underlines and a layout that reflows wrong while the checks keep passing. The scene's named events include `CRACK`, `REFLOW`, `SLAM`, `FUSE`, `SNAP`, and the later pixel-scale inspection. The scene shows a specific defect and a specific process that corrects it. When you inspect this implementation, keep the script's own event times and clock override in view; the slot pattern common to the brief does not explain every local detail.

## Adaptation and inspection

For a chart error, jitter may mislead, because a wrong value can be perfectly stable. Show the wrong relation and its correction directly with a [focused comparison](../patterns/Focused%20comparison.md). For a product demonstration, say that the animation is a simulation, and do not let it imply that it measures how long the repair takes.

Inspect the last pain step, the first strike, the first corrective movement, and the first stable result. Then watch the full slot with sound. Can the viewer identify the defect and the mechanism that fixes it? Does the strike stop the right instability while the carried-over background stays continuous? John's verdict covers [SLASH_MY as a whole](SLASH_MY.md#what-this-case-is).

[Diagnose](../maps/Diagnose.md) · [All scopes](../maps/Scopes.md) · [Home](../Home.md)
