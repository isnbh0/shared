# Procedural 3D scene

**What it makes.** One continuous shot of an environment places an object in moving water under a lit sky. The inputs are geometry, a camera, a water normal map, sky and sun parameters, surface colors, and time. In the working example the output is a live, moving 3D scene. A code-authored video can sample a scene like this frame by frame once its camera and time follow a defined path.

## Design intent

The water, sky, light direction, reflection, and object need to look as if they share one space. The surrounding surfaces set scale and mood, and the object gives the eye a subject. The viewer should see the object move against stable reference points while the water keeps moving. [Attention and hierarchy](../theory/Attention%20and%20hierarchy.md) helps separate the subject's motion from the background's. [Visual identity and style](../theory/Visual%20identity%20and%20style.md) explains why color and surface treatment need to agree across the frame. How much usable depth the scene has depends on the geometry, materials, and lighting you actually feed it, as [shaders and 3D](../knowledge/Shaders%20and%203D.md) describes.

## Operations and techniques

The combination uses these [operations](../Operations.md):

| Pattern | Input and operation | Concrete technique in the working example |
| --- | --- | --- |
| Represent a source; Combine and reveal layers | Water plane, sky, box, camera, and lighting are assembled into one view. | The [three.js example source](https://github.com/mrdoob/three.js/blob/dev/examples/webgl_shaders_ocean.html) creates a large water plane, sky object, reflective box, perspective camera, and renderer. |
| Bind a role to a visual language; Expose a decision as a parameter | Sun direction, water color, sky scattering, distortion, bloom, and exposure control the appearance together. | The example passes water normals and sun parameters to the water material; the sky and environment use the same sun vector. On-page controls expose several appearance decisions. |
| Evaluate a property at a chosen time | Water and sky change continuously; the box moves and rotates. | The animation loop increments a water `time` uniform, updates sky time, and changes the box pose before rendering each frame. |
| Sample a specified state | A camera view turns the scene into pixels. | The official [live demo](https://threejs.org/examples/webgl_shaders_ocean.html) renders in a browser. A video adaptation must set a reproducible frame time and capture those pixels; see [deterministic rendering](../knowledge/Deterministic%20rendering.md) and [capture and encoding](../knowledge/Capture%20and%20encoding.md). |

## What the example proves

The official demo and its source show the assembled 3D scene. I opened the page in headless Chrome at 1280 × 720 and captured a frame with the sky, the lit water, and the box visible. The source shows the animation loop and the uniforms that change with time. This verifies a working, moving scene in the browser. The example runs on elapsed browser time and interactive camera controls, so a video renderer would need to supply a chosen time for each frame and an authored camera path. [Live demo](https://threejs.org/examples/webgl_shaders_ocean.html), [source](https://github.com/mrdoob/three.js/blob/dev/examples/webgl_shaders_ocean.html).

## A usable starting configuration

Open the [live example](https://threejs.org/examples/webgl_shaders_ocean.html) and adjust sun elevation, water distortion, cloud parameters, bloom, and exposure to see which ingredient changes the shot. The [source](https://github.com/mrdoob/three.js/blob/dev/examples/webgl_shaders_ocean.html) supplies a water plane, sky, box, camera, normal map, and animation loop. For a repeatable video render, choose a duration and frame rate, then use `t = frame / fps` as the scene clock. Set the water and sky time from `t`, compute the subject pose and the camera pose from `t`, render the frame, and encode the captured frames. The live demo's elapsed-time accumulator and mouse orbit are fine for exploring; a defined frame clock and camera path make an export reproducible.

What you can reuse is the combination: a modeled space, light and surfaces that agree, a moving subject, and a sampled camera view. A different shot could swap the box for a modeled product, or the water for another procedural material. After encoding, inspect several moments along the camera path and watch a full-speed playback. The new object or surface has to supply the geometry and appearance information the shot needs, because the shader does not invent it. See [capability boundaries](../knowledge/Capability%20boundaries.md).
