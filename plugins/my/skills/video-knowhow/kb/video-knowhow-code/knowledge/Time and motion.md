# Time and motion

Code-authored video is a sequence of visual states. A composition defines what a frame contains, and a timeline defines which state appears at each moment. In a fixed-frame render, frame `n` occurs at `n / fps` seconds, and the first frame is numbered zero. A 24-second piece at 60 fps therefore has 1,440 frames, numbered 0–1,439. Because every point in the video has a frame number, a renderer can seek to any of them directly. [Remotion's composition fundamentals](https://www.remotion.dev/docs/the-fundamentals) describe the same four basic properties: width, height, duration in frames, and frame rate.

## The layers of time

| Layer | Question it answers | Useful representation |
| --- | --- | --- |
| Story | What changes, and why now? | Story beats, reveals, pauses, transitions |
| Scene | Which elements exist during this interval? | Start, end, and local time |
| Element | How does a property change? | Keyframes, easing, path, or a state function |
| Render | Which image is produced? | Frame index and frame rate |

Keep these layers apart. A story beat can trigger several visual changes and a sound cue. A scene can contain element motions that overlap. A title may hold still while its background moves. In the end, the render evaluates all of them for one frame.

The [Web Animations API's conceptual model](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API/Web_Animations_API_Concepts) splits the work in two. Its **timing model** finds the progress along a timeline, and its **animation model** decides the visual value at that progress. The same split helps in video code: first decide *when* a reveal is active, then decide *what* it looks like at that time.

## Evaluate state from time

To render frames reproducibly, derive the visible state from the requested frame or time. Conceptually, a position is `x = f(t)` and a reveal is `opacity = g(t)`. Frame 400 then gives the same result whether it is rendered after frame 399 or requested directly. A stateful animation that adds `x += velocity` on each callback depends on which callbacks ran, and it is harder to seek, parallelize, or retry reliably. This is an engineering inference from the frame-based composition model, and no particular library requires it. [Remotion's frame model](https://www.remotion.dev/docs/the-fundamentals) is one concrete implementation.

For a local motion, calculate progress from the motion's own interval:

```text
progress = clamp((time - start) / duration, 0, 1)
value = interpolate(from, to, ease(progress))
```

The motion's duration then stays independent of the overall scene, and the `clamp` makes the before and after states explicit. Some effects overshoot on purpose. For those, do not clamp the *eased output* just because normalized time is clamped. CSS [cubic Bézier easing](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/easing-function/cubic-bezier) allows control-point `y` values outside `0–1`, which produce values past the destination before the motion settles. Properties such as color channels may clip those values.

## Motion has a job

Motion can direct attention, reveal a relationship, keep an object recognizable across a layout change, or emphasize a moment. Material Design describes motion as informative, focused, and expressive, and [its examples](https://m2.material.io/design/motion/understanding-motion/) show how movement can explain parent–child and peer relationships. Microsoft's [connected-motion guidance](https://learn.microsoft.com/en-us/windows/apps/design/motion/) describes following the same element from one state to another. Apple advises [purposeful, brief motion](https://developer.apple.com/design/human-interface-guidelines/motion) that supports the experience without overshadowing it. These sources are about interfaces. Applying their principles of cause and effect to edited video is a design inference, and no fixed cinematic grammar backs it.

In a video scene, ask what the viewer should track. If an element changes role or position, a continuous path can keep it recognizable as the same element. If the move itself adds no information, a fade or a cut may be clearer. If several items appear in sequence, a stagger can show reading order or build a comparison. Elements that move at the same time can signal one shared event, but too many competing changes make the intended focus harder to find.

## Timing, easing, path, and overlap

Each of these is a separate decision:

- **Duration** sets how much viewing time the change takes. It depends on how far the element travels, how large the visual change is, and how much content the viewer must read or understand. [Material's duration guidance](https://m1.material.io/motion/duration-easing.html) states this relationship for interfaces; its millisecond values are UI examples and do not carry over to video as fixed timings.
- **Easing** changes the rate of progress. Deceleration can make an arrival feel settled, and acceleration can move an exit out of the viewer's way. The [CSS easing model](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Easing_functions) includes linear, cubic Bézier, and discrete steps. Pick the curve for the action: linear often suits motion at a constant rate, steps make intentional increments, and shaped curves emphasize the start or the finish.
- **Path** sets where an element comes from and where it goes. A path that follows the spatial logic of the composition helps the viewer track continuity. [Microsoft's directionality guidance](https://learn.microsoft.com/en-us/windows/apps/design/motion/directionality-and-gravity) explains this for interface navigation.
- **Overlap and stagger** decide what appears to cause or follow what. Neighboring events can be offset slightly and still belong to one story beat, and an intentional pause can give the viewer time to read the result. How long an interval needs to be is an editorial choice to inspect at actual playback speed.

Changing one parameter does not fix every timing problem. A title that cannot be read may need a longer *hold*, less competing motion, or fewer words more than it needs a slower entrance. A transition that feels disconnected may need a clearer path or an element that stays on screen across it more than a more ornate easing curve.

## Preview and export use different clocks

A browser's `requestAnimationFrame()` runs before repaints, generally at the display refresh rate, and browsers may pause it in hidden tabs. Animation progress must come from its timestamp. If you count callbacks instead, the speed depends on the display refresh and on dropped frames. [MDN documents these timing behaviors](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame).

A fixed-frame export asks for specific frames at a chosen fps. So the preview can look smooth while the export shows a one-frame pop, or the preview can stutter while the exported sequence is correct. Inspect representative frames, scene boundaries, and the encoded result. For events tied to audio, use one shared event timeline and review the delivered audiovisual file; see [Audiovisual synchronization](Audiovisual%20synchronization.md).

## Readability is part of timing

A frame can be present in the file and still be too brief to perceive. Give the viewer time to recognize an incoming object, to read text after it settles, and to register the result before the next competing change. Text over moving imagery also needs enough contrast at every moment it has to be read. The [W3C media guidance](https://www.w3.org/WAI/media/av/av-content/) calls out the contrast, font, and size of overlay text. [Accessibility and perception](Accessibility%20and%20perception.md) covers the separate checks for video and for interactive previews.
