# Representation models

A code-authored video is a timed sequence of images and audio. Code may describe a scene, calculate geometry, animate existing elements, combine media, or produce pixels directly. The renderer turns that description into images, and an encoder and a container turn the images and audio into a video file. The distinction that helps most is **what the code represents before it becomes pixels**. [Remotion describes video as images over time](https://www.remotion.dev/docs/the-fundamentals); [WebCodecs distinguishes raw frames from encoded chunks](https://developer.mozilla.org/en-US/docs/Web/API/WebCodecs_API).

## Four common representations

| Representation | What code holds | What produces pixels | Natural uses |
| --- | --- | --- | --- |
| Document and styles | HTML elements, text, CSS rules, SVG nodes | Browser layout, paint, and compositing | Typography, diagrams, interface-like scenes, vector graphics |
| Drawing commands | Shapes, paths, images, and operations issued to a canvas | Canvas 2D rasterizer | Custom 2D graphics, plots, particles, image manipulation |
| 3D scene | Objects, geometry, cameras, lights, materials, textures | 3D renderer and GPU | Spatial scenes, camera moves, lighting, depth, 3D effects |
| Image or media layers | Existing images/video with transforms, masks, timing, and blend operations | Compositor or media filtergraph | Collage, editing, overlays, transitions |

The four combine. A browser page can place text and SVG over a WebGL canvas, a 3D renderer can draw into a texture that another scene uses, and FFmpeg can overlay a generated graphic on recorded footage. The representation decides which relationships stay editable and which operations come naturally, and the delivered raster image can combine several representations. [Browser animation forms](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Animation_performance_and_frame_rate), [three.js render targets](https://threejs.org/manual/pages/rendertargets.html), [FFmpeg filtergraphs](https://ffmpeg.org/ffmpeg-filters.html).

### Document and scene descriptions

A **retained** representation keeps objects after they are created. In HTML/SVG, an element goes on existing, and it can be restyled, moved, queried, and composited. SVG specifies vector shapes, paths, text, transformations, gradients, and filters as document elements. A three.js scene likewise holds a hierarchy of objects, each with its own local coordinate system. Code changes object properties, and the browser or 3D engine renders their current state. [SVG introduction](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorials/SVG_from_scratch/Introduction), [three.js scene graph](https://threejs.org/manual/pages/scenegraph.html).

A **drawing-command** representation issues operations to a bitmap. In Canvas 2D, drawing a rectangle changes the canvas pixels, and the API has no separate rectangle object to move afterward. To animate it, code usually clears the old image and draws a new frame. The application may keep its own object model on top of the canvas, but Canvas itself stores the rendered result. [MDN Canvas animation](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Basic_animations).

The difference shows up when you edit. Retained objects tend to make it easier to change one caption, rearrange a group, or inspect a layer. Drawing commands tend to make arbitrary per-pixel effects and high-volume procedural effects straightforward, but the program then has to manage its own scene state, and its own hit testing if it needs any.

### Geometry, pixels, and samples

Vector graphics describe shapes mathematically, and raster graphics describe samples on a pixel grid. SVG can be enlarged and rasterized again for a new output size. Canvas and video frames have a fixed pixel width and height, so scaling their existing pixels can soften edges. A browser canvas also has a backing-store size separate from its CSS display size, and if their proportions differ, the result is distorted. [SVG shapes](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorials/SVG_from_scratch/Basic_shapes), [Canvas sizing](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Basic_usage).

The output frame is always raster, even when the source is vector or 3D. A vector title and a 3D object are both sampled into pixels at the chosen resolution and then encoded. Resolution, pixel ratio, antialiasing, and color handling therefore affect the delivered image whatever the source representation is. [Playwright screenshot scale](https://playwright.dev/docs/api/class-page), [three.js renderer drawing-buffer size](https://threejs.org/docs/pages/WebGLRenderer.html), [FFmpeg pixel format](https://ffmpeg.org/ffmpeg.html).

## Time is another representation

Motion can be represented as keyframes, as a function of time, as simulation state, or as a recorded stream. CSS keyframes and the Web Animations API let a browser interpolate an element's appearance between specified states. A frame-addressed composition calculates the appearance for one particular frame number. A real-time animation loop updates in step with the display refresh. [Web Animations concepts](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API/Web_Animations_API_Concepts), [Remotion timing](https://www.remotion.dev/docs/timing), [`requestAnimationFrame`](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame).

How time is represented matters when frames are rendered out of order. A title position computed directly from `t = frame / fps` can be sampled at frame 900 without first visiting frames 0–899. A simulation that repeatedly updates `position += velocity * delta` depends on the previous steps, unless its state is reconstructed, cached, or evaluated analytically. Frame addressing is especially useful when rendering workers split a video into independent segments. Remotion's documentation gives a concrete example: unseeded random values differ between parallel browser instances. [Using randomness](https://www.remotion.dev/docs/using-randomness).

See [Deterministic rendering](Deterministic%20rendering.md) for frame seeking and capture, [Raster, vector, and DOM](Raster%20vector%20and%20DOM.md) for 2D browser representations, and [Shaders and 3D](Shaders%20and%203D.md) for GPU-based scenes.
