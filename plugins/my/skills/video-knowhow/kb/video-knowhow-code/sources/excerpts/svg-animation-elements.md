# SVG 1.1 animation — values, pacing, and motion paths (2003)

- **Source:** W3C, Scalable Vector Graphics (SVG) 1.1 Specification, chapter 19 "Animation", W3C Recommendation 14 January 2003 (developed with the SMIL Animation specification).
- **URL:** https://www.w3.org/TR/2003/REC-SVG11-20030114/animate.html
- **Checked:** 2026-10-14.

## The passages

**The four animation elements:** "'animate' allows scalar attributes and properties to be assigned different values over time"; "'set' [is] a convenient shorthand for 'animate', which is useful for assigning animation values to non-numeric attributes and properties, such as the visibility property"; "'animateMotion' moves an element along a motion path"; "'animateColor' modifies the color value of particular attributes or properties over time". SVG adds "'animateTransform' modifies one of SVG's transformation attributes over time, such as the transform attribute".

**On interval pacing (calcMode spline, keyTimes, keySplines):** "`spline` — Interpolates from one value in the values list to the next according to a time function defined by a cubic Bézier spline. The points of the spline are defined in the keyTimes attribute, and the control points for each interval are defined in the keySplines attribute." And: "keySplines = '<list>' — A set of Bézier control points associated with the keyTimes list, defining a cubic Bézier function that controls interval pacing. … The keyTimes values that define the associated segment are the Bézier 'anchor points', and the keySplines values are the control points."

**On additive animation:** the `additive` attribute controls "whether animations are additive", with `additive="sum"` stacking the animation's effect on the underlying value (illustrated in the spec's anim01 example, where a scale animation adds to a rotation on the same transform attribute).

## Where it is relied on

[Production lineage](../Production%20lineage.md) cites the 2003 SVG animation specification as the documented origin of specifying the interval, property, start and end values, interpolation, and path separately, which is where "evaluate a property at a chosen time" in [Operations](../../Operations.md) comes from. It also cites the specification's section on groups, symbols, and reuse for keeping named object structure.
