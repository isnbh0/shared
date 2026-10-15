# Diagram explainer

**What it makes.** A short diagram shows a relationship that is hard to grasp from two finished stills. The example starts with axes and a unit circle. A dot moves around the circle, and a guide line carries its vertical position across to a growing sine curve. The input is a defined relationship and the geometry needed to show it. The output is an animation in which the viewer can follow cause and result in the same frame.

## Design intent

The circle, the moving dot, the guide, and the curve should read as one explanation. [Grouping and continuity](../theory/Grouping%20and%20continuity.md) explains why a dot that stays on screen and a guide that connects it help the viewer track what corresponds from frame to frame. The axes stay still while one point moves, which makes the change easier to find. [Attention and hierarchy](../theory/Attention%20and%20hierarchy.md) explains how color and motion can draw the eye to that point. The curve needs enough time to build up into a shape the viewer recognizes; see [temporal visual rhythm](../theory/Temporal%20visual%20rhythm.md).

## Operations and techniques

The combination uses these [operations](../Operations.md):

| Pattern | Input and operation | Concrete technique in the working example |
| --- | --- | --- |
| Represent a source; Relate elements in space | Axes, circle, moving point, connector, and curve become distinct graphical objects with defined spatial relationships. | Manim's [SineCurveUnitCircle source](https://docs.manim.community/en/stable/examples.html#sinecurveunitcircle) creates line axes, a circle, a dot, and π labels. |
| Encode meaning in a visual property | The dot's vertical position becomes the curve's height at the corresponding horizontal position. | The example computes a connector endpoint from the current dot position and appends line segments to the curve. The graph is tied to the orbit. |
| Evaluate a property at a chosen time; Carry or break correspondence between states | The dot advances around the circle while the guide and curve respond to it. | A time-step updater moves the dot. `always_redraw` rebuilds the radial and horizontal guides; the curve callback appends new segments to a persistent `VGroup`. The source is a sequential animation; it does not promise arbitrary-frame seeking. |
| Sample a specified state | The scene becomes a video that can be watched at normal speed. | The Manim documentation pairs the [source](https://docs.manim.community/en/stable/examples.html#sinecurveunitcircle) with its [rendered MP4](https://docs.manim.community/en/stable/SineCurveUnitCircle-1.mp4). |

## What the example proves

The official Manim gallery publishes both the code and a 9.5-second, 854 × 480 video. I downloaded the MP4 and inspected frames throughout it: the point goes around the circle repeatedly while the traced wave grows across the axes. This confirms the combined motion and the visible link between the two shapes. It does not show that a viewer will understand the mathematics without narration or labels beyond those shown. [Gallery example](https://docs.manim.community/en/stable/examples.html#sinecurveunitcircle), [MP4](https://docs.manim.community/en/stable/SineCurveUnitCircle-1.mp4).

## A usable starting configuration

The [gallery source](https://docs.manim.community/en/stable/examples.html#sinecurveunitcircle) is a complete scene: it defines axes and labels, a circle, a moving dot, a guide, and an 8.5-second drawing interval before a hold. Copy that scene into a Manim project to render an MP4, or build the same object relationships in SVG or Canvas. For a new subject, name the quantity that changes, pick the fixed reference, and draw the connection that makes the mapping visible. A point traveling through a network, for example, could light up the route it has finished.

Check the mapping against the concept it comes from, then review whether the viewer can follow the moving point and still keep the result that has built up in view. The input relationship has to be accurate, because smooth motion cannot fix a misleading mapping. See [visual hierarchy and composition](../knowledge/Visual%20hierarchy%20and%20composition.md) and [verification](../knowledge/Verification.md).
