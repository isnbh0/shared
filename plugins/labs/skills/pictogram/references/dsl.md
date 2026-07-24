# Pictogram DSL reference

The DSL describes intent, a semantic pose graph, and constrained primitive assemblies. SVG is
compiler output.

## Document

Use namespace `urn:labs:pictogram:1` and profile `aicher-inspired-48-v1`.

```xml
<p:pictogram xmlns:p="urn:labs:pictogram:1"
             id="short-kebab-id"
             profile="aicher-inspired-48-v1">
  <p:metadata>
    <p:title>Short accessible title</p:title>
    <p:description>One-sentence visual description.</p:description>
  </p:metadata>
  <p:intent verb="action-name" direction="left|right|up|down|stationary"/>
  <p:scene>...</p:scene>
  <p:expression>...</p:expression>
</p:pictogram>
```

`metadata`, `intent`, and `scene` are required and ordered. `expression` is optional and last.

## Human pose

Each `actor` has one canonical head and exactly ten named joints:

```xml
<p:actor id="person" facing="left|right|front">
  <p:head x="24" y="8"/>
  <p:pose>
    <p:joint name="shoulder" x="24" y="16"/>
    <p:joint name="hip" x="24" y="26"/>
    <p:joint name="elbow-near" x="30" y="18"/>
    <p:joint name="hand-near" x="36" y="24"/>
    <p:joint name="elbow-far" x="18" y="18"/>
    <p:joint name="hand-far" x="12" y="24"/>
    <p:joint name="knee-near" x="30" y="32"/>
    <p:joint name="foot-near" x="36" y="38"/>
    <p:joint name="knee-far" x="18" y="32"/>
    <p:joint name="foot-far" x="12" y="38"/>
  </p:pose>
</p:actor>
```

The canon supplies bone connections, widths, length ranges, and near/far layers. Coordinates are
integral. Even coordinates lie on the preferred two-unit grid. Prefer horizontal, vertical, and
45-degree vectors; selected 1:2 vectors are controlled deviations.

## Primitive assemblies

Use an `assembly` for equipment or a subject that does not fit the human pose graph:

```xml
<p:assembly id="barbell"
            role="prop"
            layer="near-equipment"
            color-role="figure">
  <p:bar x1="8" y1="14" x2="40" y2="14"/>
  <p:disc cx="8" cy="14" radius="4"/>
  <p:disc cx="40" cy="14" radius="4"/>
</p:assembly>
```

Allowed roles are `prop` and `subject`. Allowed layers are `far-equipment`, `far-limbs`, `torso`,
`near-limbs`, `head`, and `near-equipment`. Allowed color roles are `figure` and `accent`.

Approved primitives:

- `bar`: `x1`, `y1`, `x2`, `y2`; compiled at canonical equipment width
- `disc`: `cx`, `cy`, `radius`
- `ring`: `cx`, `cy`, `radius`; compiled at canonical equipment width
- `box`: `x`, `y`, `width`, `height`
- `wedge`: `x1`, `y1`, `x2`, `y2`, `x3`, `y3`

Use assemblies as a leeway mechanism, not as a verbose imitation of arbitrary SVG. Reduce a
subject to a few decisive components.

## Controlled deviations

The validator derives deviations from geometry and scene complexity. Declare each derived
deviation exactly:

```xml
<p:expression>
  <p:deviation feature="extended-vector"
               target="person:upper-arm-near"
               cost="1"
               reason="The steeper arm angle distinguishes the action."/>
</p:expression>
```

Derived features are:

- `extended-vector`, targeted as `{actor-id}:{bone-role}`, cost 1
- `half-grid`, targeted as an actor or assembly ID, cost 1
- `second-actor`, targeted as `scene`, cost 2
- `custom-assembly`, targeted as the assembly ID, cost 1

The standard profile allows total expression cost 4. The validator rejects missing, extra,
mis-costed, or duplicate declarations.

## Semantics and limits

The compiler guarantees structural consistency, bounded construction, and deterministic SVG. It
does not guarantee recognition. Use `intent` and metadata to state meaning, then inspect the
rendered silhouette at small size.

The profile permits up to two actors, three assemblies, and eight primitives per assembly. If a
request needs more, simplify the scene before changing the canon.
