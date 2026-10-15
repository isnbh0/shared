# Transitions and continuity

Cuts, moves, morphs, and scene boundaries are events that code controls. [Grouping and continuity](../theory/Grouping%20and%20continuity.md) explains what a viewer takes to persist across those boundaries. [Temporal visual rhythm](../theory/Temporal%20visual%20rhythm.md) explains how the duration and placement of a transition affect the pace of a sequence.

## What persists across the boundary?

Continuity can come from several places: the same object moving to a new position, one shape matching another, a color role that stays the same, a camera direction that continues, a sound that bridges a cut, or a repeated layout. Each one tells the viewer something different about identity or relation, so a match transition should keep something that means something in the story. A character portrait that morphs into an unrelated logo may look continuous and still imply a relationship the story does not intend. Heer and Robertson name object constancy as a benefit of animation and false continuity as a risk. [Heer and Robertson](https://sites.stat.columbia.edu/gelman/communication/HeerRobertson2007.pdf)

A hard cut does not have to keep physical identity. It can serve contrast, surprise, rhythm, or a change of location. Dissolves, wipes, zooms, and morphs are alternatives with different effects, and none of them is more sophisticated by default. Whatever the type, a transition should let the viewer understand the next state at the moment you want.

## Staging makes change legible

When position, scale, color, text, and camera all change at once, the viewer may struggle to track what happened. Staging can split a complex change of state into parts: establish the target, move the primary object, then settle the supporting information. Material Design's motion guidance distinguishes informative, focused, and expressive motion. Heer and Robertson describe how animation helps attention, and what it costs when the change is too fast, too complex, or misleading about meaning. [Material motion principles](https://m2.material.io/design/motion/understanding-motion/), [Heer and Robertson](https://sites.stat.columbia.edu/gelman/communication/HeerRobertson2007.pdf)

Transitions do not all have to be slow or sequential. Rapid cuts can work when recognition rests on a strong silhouette, repeated framing, or a sound cue. Inspect whether the viewer can work out what changed and what stayed. The answer depends on the scene and the audience, and no single transition duration fits every case.

## Timing and motion shape

Code can define a transition by its onset, duration, path, easing, overlap, and exit state. Easing changes how the motion speeds up and slows down. Material Design presents it as a way to give motion a coherent feel, so that not every move is linear and mechanical. Choose the path and the easing to match the relation: an object that continues through space tells a different story from an element that pops into existence. [Material duration and easing](https://m1.material.io/motion/duration-easing.html)

Audio can make a transition feel connected even when the picture cuts sharply. A beat, an impact, a silence, or a musical phrase that continues across the cut can mark when the scene changes. In code-authored video, an event timeline can give visual and audio changes the same time reference. That makes the sync reproducible, but it does not tell you whether the beat lands well, so review the rendered video and audio together.

Inspect the first and last frames closely. An element that leaves after the scene changes can leave a ghost, an incoming title might collide with an outgoing particle, and a one-frame luminance spike may be brighter than the states on either side. If you sample only the midpoints of transitions, you miss these problems. Flash frequency is a separate safety concern. WCAG 2.2 limits web content to no more than three flashes in any one-second interval, unless the flashes stay under specified thresholds. That web criterion is a useful warning for strobe-like video effects, though a full assessment of a video depends on the delivery context and the actual rendered frames. [W3C flash guidance](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold)

## Code-controlled vocabulary

| Concern | Controllable parameters | Inspection |
| --- | --- | --- |
| Relation | Persistent object IDs, matched shapes, color roles, camera direction | Does the transition imply the intended relationship? |
| Time | In and out points, overlap, duration, beat offset | Does it complete before the next information needs attention? |
| Motion | Path, distance, easing, scale, rotation, camera movement | Can the eye track the relevant object? |
| Staging | Order and offset of object, text, background, and effects | Does one important event have a clear moment? |
| Boundary | First, middle, last frame; alpha and z order | Are there collisions, missing frames, or unwanted flashes? |
| Sound | Cue position, silence, crossfade, continuation | Does audio reinforce or contradict the scene boundary? |

## Questions a render can answer

- What stays identifiable before, during, and after the transition?
- Does any morph or match suggest a false identity or a false cause-and-effect relation?
- At normal playback speed, can the viewer understand the important change of state without pausing?
- Does the text have enough stable time after the motion ends?
- Are there one-frame visual errors or intense repeated flashes at the boundary?
