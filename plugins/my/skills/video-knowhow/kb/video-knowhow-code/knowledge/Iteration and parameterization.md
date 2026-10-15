# Iteration and parameterization

In code-authored video, a scene is a program you can run again and again. Text, timing, geometry, palette, camera, motion, and sound can each become a parameter. A change then stays local and is easy to compare: move a label or a beat position, render again, and inspect the frames it affects. How much this helps depends on how the scene is structured and on whether the render is reproducible.

## Small capabilities that compose

The [“Capabilities over features” principle](https://wiki.g15e.com/pages/Capabilities%20over%20features.md) favors a small set of functions that each do a distinct job and can be combined. The same idea applies to revision: name the title, color, or tempo as an input, have the scene read that input at each frame, let the renderer show the result, and compare two versions.

| Capability | Input | Transformation | Output |
| --- | --- | --- | --- |
| **Expose a parameter** | An authored decision such as title, tempo, palette, or camera distance. | Give the value a stable name and scope. | A changeable input shared by dependent elements. |
| **Evaluate at a chosen time** | Parameters and a frame or timestamp. | Calculate the visual and audio state for that instant. | A scene state that can be rendered or inspected. |
| **Render a sample** | A scene state and output settings. | Draw a frame, section, or finished sequence. | Evidence of what the system actually produced. |
| **Compare and revise** | Two samples and a desired criterion. | Locate a mismatch and change the relevant source or parameter. | A new version of the same composition. |

The same four steps work for typography, charts, pixel scenes, 3D animation, and sound. For example, changing the title color means changing one named input, rendering the frames where the title appears, and checking that the new color remains readable over the background.

## What parameterization buys

A useful parameter has a clear meaning in the finished piece. Examples include the title string, color palette, duration, beat position of a reveal, number of chart bars, camera distance, particle density, and music tempo. Parameters like these support:

- **Revision**: change one decision without redrawing every frame.
- **Variants**: produce versions for different aspect ratios, languages, data sets, or events.
- **Consistency**: keep repeated components aligned by sharing a rule or source value.
- **Exploration**: compare several values while holding the rest of the scene steady.
- **Interactivity**: connect the same scene representation to user input or live data, if its timing model supports it.

Writing a scene in code does not by itself deliver these benefits. Hard-coded coordinates scattered through the scene code may make revision slow, and even a single well-named parameter can have unintended effects on layout, collision, rhythm, or legibility, so the output still needs inspection.

The chatlog's Stage intro shows shared parameters doing real work: a 120 BPM, 48-beat plan aligned visual events and sound cues, including a countdown, a short silence, and the title reveal. [Chatlog C-513](../sources/Chatlog%20index.md#c-513).

## Reproducibility has conditions

Reproducibility is strongest with a frame function: given the same frame number, parameters, assets, and environment, it returns the same intended image. That allows direct seeking, parallel frame rendering, and exact comparison. Two common tools make time-dependent properties explicit this way: Remotion describes a composition in terms of the current frame, and After Effects expressions expose composition time and allow seeded random values. [Remotion fundamentals](https://www.remotion.dev/docs/the-fundamentals); [After Effects expression reference](https://helpx.adobe.com/after-effects/desktop/work-with-expressions/expression-language-reference/expression-language-reference.html).

**Code does not guarantee identical output.** Random values without a stable seed, system time, asynchronous asset loading, browser or font differences, GPU floating-point behavior, variable input data, and state carried from previous frames can change results. Even a deterministic scene may produce different encoded bytes when export settings or encoders differ. What code does give is narrower: its dependencies and rules can be inspected, and once those dependencies are fixed, it offers a way to rerun under control.

Stateful simulation has a different time model. The result at frame 200 may depend on all earlier updates, so evaluating frame 200 directly can be wrong or impossible. Baking stores simulation results for later access; Blender's simulation-node documentation specifically notes that a baked simulation can be rendered in nonsequential order. [Blender simulation nodes](https://docs.blender.org/manual/en/latest/physics/simulation_nodes.html). The same distinction applies to hand-written particle systems, game loops, and audio-reactive state: either derive state from requested time or preserve a known simulation history.

## Failure patterns are inspectable

When a rule is wrong, the same error can repeat in every frame that uses it. The chatlog records a code edit that resets Canvas `textAlign` and `globalAlpha` at the start of drawing, with a comment that Canvas state had leaked between frames. [Chatlog C-794](../sources/Chatlog%20index.md#c-794). The assistant later reported that this one change to the shared drawing rule fixed clipped chart titles. [Chatlog C-846](../sources/Chatlog%20index.md#c-846).

Other common failure classes follow from the representation:

| Failure class | Typical symptom | Underlying cause |
| --- | --- | --- |
| Hidden drawing state | Later objects use an unintended alignment, blend mode, transform, or opacity. | A previous operation changed renderer state without restoring it. |
| Timing mismatch | An event lands between expected beats or before the preceding event finishes. | Multiple clocks, rounding, or a changed duration without dependent adjustments. |
| Layout collision | Text overlaps or clips in another language or aspect ratio. | Parameters changed, but the layout has no responsive constraints. |
| Asset dependency | Missing font, image, or sound changes the render. | External input was unavailable, loaded late, or replaced. |
| View or pose gap | A warped still looks like a flat cutout. | The source contains one view but the motion requests another. |
| Simulation history | A frame differs depending on render order. | Stateful updates lack a fixed initial state or bake. |
| Aesthetic convergence | Technically correct scenes feel interchangeable. | Repeated composition defaults or insufficient visual direction. |

The FOXTALE trailer needed revisions to projectile timing, drawing order, and font sizing. Those were found in review, and the assistant checked the hit and the ring gap frame by frame in the finished video. [Chatlog C-1146](../sources/Chatlog%20index.md#c-1146). Its browser version later failed under `file://` because of image-origin rules, while the video renderer's local-server route worked, so the page needed a check in its export context on top of frame inspection. [Chatlog C-1319](../sources/Chatlog%20index.md#c-1319).

## The feedback loop

The loop draws on five kinds of evidence:

1. **Structural checks**: files load, expected frames are produced, audio duration and dimensions match, data values are correct.
2. **Frame checks**: selected stills reveal layout, drawing-order, typography, and visual continuity problems.
3. **Motion checks**: adjacent frames or playback reveal stiffness, unintended collisions, easing problems, and pacing.
4. **Sound checks**: listening reveals timbre, balance, musical fit, and whether the impact feels synchronized. Waveform or loudness measurements can confirm timing and level, and listening still has to judge the rest.
5. **Delivery checks**: the actual encoded file or live page works in its intended player, size, and environment.

The chatlog repeatedly used still frames and numerical audio checks. It also explicitly acknowledged that the assistant had not listened to the finished audio, which makes the visual findings stronger than any claim about musical quality. [Chatlog C-513](../sources/Chatlog%20index.md#c-513); [Chatlog C-1146](../sources/Chatlog%20index.md#c-1146).

This loop is why “one prompt” is an incomplete description of many code-authored videos. In the opening investigation, the assistant found both terse prompt claims and examples with long briefs, references, and substantial agent iteration. It had inspected only post text and creator descriptions. [Chatlog C-231](../sources/Chatlog%20index.md#c-231). Authored rules can be revised and rerun, and the quality of any one result still depends on direction, ingredients, implementation, and review.

## The loop with recovery built in

**Reported (SLASH_MY):** the SLASH_MY production's session records (held in John's workspace) record how this loop was made to survive failures. Each thing under review is a named snapshot pair, so a round's judgments attach to an exact picture and score. After one render was lost to a single missing file that had been copied by hand, the pipeline was rebuilt around three pieces: input checks that stop a mis-assembled render before it starts; chunked rendering that resumes after a failure, with a killed run and its resumed rerun decoding to byte-identical frames; and one command that assembles a round's snapshot. After a session interruption destroyed uncommitted fixes, the practice became to commit each fix as soon as it passes. The rule the records keep: expensive steps are checked up front, a failed step resumes, and a procedure repeated by hand gets scripted. The rounds this loop serves are the review rounds of the craft shelf's [convergence](../../video-knowhow-craft/knowledge/Convergence.md) system.
