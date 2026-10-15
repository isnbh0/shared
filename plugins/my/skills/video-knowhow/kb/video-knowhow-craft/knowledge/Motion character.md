# Motion character

Decide what a movement should imply before you tune its curve. An arrival, a recoil, a procedure, instability, and a flexible response each need a different relation among path, motion spacing, timing, and connected parts. The recommendations here connect existing focused notes; values depend on context.

## Coordinate the controls

| Decision | Interaction and possible failure | Principle to keep |
| --- | --- | --- |
| Path and motion spacing | Equal-time positions reveal acceleration. A curved path can have constant speed or a slowing arrival; changing easing does not change the path itself. An eased progress indicator can falsely imply a changing process rate. | Choose the temporal rate of change separately from the spatial path; motion spacing between successive frame positions is what reveals velocity. Deceleration suits an arrival, acceleration an exit, constant rate an elapsed-time or measured-process display. |
| Weight and contact | A forceful arrival needs a readable landing relation. Recoil that begins before contact or moves an unrelated object can read as decorative wobble. Compare a firm stop, a short recoil, and a deliberately light glide. | Judge a spring by when it settles, not when it first touches the target: an underdamped motion can cross the target and keep oscillating, and a library's overshoot argument is not automatically a percentage. |
| Settle and reading | Crossing the target is not settling. Residual oscillation can consume the hold even when the headline has technically arrived. | Budget time after the last required object settles and before the next competing event; compute a group's hold from its last arrival, not its first element. |
| Stagger and group size | The last completion is start + duration + (count − 1) × interval. Longer copy changes the event budget even when each letter's animation is unchanged. | Stagger expresses reading order or group membership; count its total duration before calling an entrance short, and shrink the interval or reveal subgroups as the group grows. |
| Overlap and secondary action | Offsetting connected parts can suggest flexibility; follow-through continues after the main body stops. A supporting underline or dust cue should reinforce the main event without becoming a new focal task. | Keep the offset's meaning straight: stagger sequences similar elements, overlapping action offsets connected parts of one moving object, follow-through continues a part after the body stops. Assign each story beat one primary change with at most small supporting actions. |

## Instability requires a sampling decision

The [SLASH_MY snapshot](../cases/SLASH_MY.md) uses `stepped(u)` and `stepJitter(seed, px, fps)` in `engine.js`. At 60 output fps, the default 12 fps pain clock holds each state for five frames. Because the step clock is aligned to absolute time, every shutter sample inside one output frame sees the same stepped state. That is how the layer can stay sharp inside a scene that otherwise uses motion blur, which lowering the export frame rate alone would not do.

If each subframe drew a new random offset, averaging could soften the instability into a smear. If every layer used the stepped clock, the camera and the repaired state would pick up the defect's motion too. Keep the instability on the thing it stands for, and switch to the continuous clock when the repair begins. The [jitter path](../cases/Jitter%20to%20repair.md) follows this from the scene's purpose to its implementation.

The exact contrast in texture still has to be judged in playback. [D-007](../cases/Comparison%20runs.md) changed one parameter of a composed word arrival. The frames at the exact cue differed, but John found the difference insignificant at speed. Precise timing can support what you mean without being what the viewer mainly perceives.

## Review the movement in context

Inspect equal-time samples for motion spacing, the largest excursion for cropping, and the tail for whether the text is stable enough to read. Then watch the whole passage with sound. Can you name the action and its consequence without its label? Does the secondary action still stay behind the main one? For an interactive result, also decide how new input changes motion already under way. Start from the state currently on screen when that keeps continuity, treat the result state as the one that counts, and keep the immediate response to input separate from actual completion, so that decoration never suggests success before it happens.

[Defect to repair](../patterns/Defect%20to%20repair.md) · [Continuity carriers](../patterns/Continuity%20carriers.md) · [Direction](Direction%20and%20critique.md) · [Home](../Home.md)
