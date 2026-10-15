# Authoring approaches

Code-authored video work has three independent parts: **how a scene is described**, **what draws each frame**, and **how the frames and sound become a deliverable**. A project can mix approaches across the three: a React component can host a WebGL scene, and FFmpeg can encode the result.

The tools named on this page are examples on those axes, in no order of preference. Pick the authoring approach from the visual problem and the control over time it needs. Rendering and delivery come after.

## 1. Authoring model: what the code describes

| Model | Core idea | Natural fit | Question to settle |
| --- | --- | --- | --- |
| **Frame function** | Given a frame or time, calculate what should appear. | Parameterized layouts, repeated formats, arbitrary seeking and frame inspection. | Does each frame depend only on declared inputs, or on earlier playback state? |
| **Scene choreography** | Describe objects and a sequence of changes, waits, and transitions. | Explanations whose events follow a script or voiceover. | Can a late timing change propagate through the sequence cleanly? |
| **Live draw loop** | Update state and redraw continuously. | Generative sketches, simulations, reactive visuals. | How will a chosen time or frame be reproduced during offline rendering? |
| **Keyframed properties** | Declare values at points in time and interpolate between them. | Typography, interface motion, transforms, and concise visual gestures. | Which properties can be interpolated, and what happens between keys? |
| **Procedural graph** | Connect operations that generate or alter geometry, materials, or images. | Repeated spatial forms, variation, complex transformations. | Which inputs drive the graph, and when are they evaluated? |
| **Shader program** | Calculate vertices, pixels, or general GPU data in parallel. | Surface effects, distortion, particles, dense procedural imagery. | What higher-level scene and timing system will supply its inputs? |

The **frame function** is explicit in [Remotion's model](https://www.remotion.dev/docs/the-fundamentals): a React component reads the current frame and produces an image. [Motion Canvas](https://motioncanvas.io/docs/) uses TypeScript generators to choreograph animation and provides [time events](https://motioncanvas.io/docs/time-events/) for aligning it to audio. [Manim](https://docs.manim.community/en/stable/tutorials/building_blocks.html) organizes mathematical animation around scenes, objects, and animations. The browser's [CSS animations](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Animations), [SVG animation](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/animate), and [Web Animations API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API) provide different ways to drive properties over time. [p5.js `draw()`](https://p5js.org/reference/p5/draw/) is a recurring draw loop. Blender's [Geometry Nodes](https://docs.blender.org/manual/en/latest/editors/geometry_node.html) express procedural geometry as node groups. [GLSL shaders](https://developer.mozilla.org/en-US/docs/Games/Techniques/3D_on_the_web/GLSL_Shaders) and [WGSL shaders](https://www.w3.org/TR/WGSL/) express work for GPU stages.

The models nest: a frame function can set the time of a shader, a scene can contain a procedural object, and a keyframed camera can view a scene that code generated.

## 2. Rendering substrate: what draws the image

| Substrate | Typical content | Useful boundary |
| --- | --- | --- |
| **Browser DOM, CSS, SVG** ([raster, vector, and DOM](Raster%20vector%20and%20DOM.md)) | Text, layouts, interface elements, vector shapes. | The browser handles typography and layout; capture still has to sample the intended frames. |
| **Canvas 2D** | Immediate drawing of shapes, images, and pixels. | The sketch controls drawing; layout and video export need separate care. |
| **Retained 2D scene graph** | Persistent sprites, text, graphics, masks, and groups. | Nodes make layered transformations convenient; a video timeline is a separate concern. |
| **Real-time 3D scene graph** | Geometry, materials, lights, camera, and spatial motion. | The renderer draws a view of the scene; capture and audio need a surrounding workflow. |
| **Offline 3D renderer** | Spatial scenes with modeled geometry, materials, lighting, and camera. | Scene setup and render cost become part of production planning. |
| **GPU shader pipeline** | Per-vertex, per-pixel, or compute-driven imagery. | Powerful for dense effects, but needs inputs, composition, and output around it. |

Because the renderer is a separate axis, tools at different levels can work together. [PixiJS](https://pixijs.com/8.x/guides/concepts/architecture) supplies a retained 2D scene graph and a GPU renderer. [three.js](https://threejs.org/manual/pages/creating-a-scene.html) renders a 3D scene through a camera. [Blender's Python API](https://docs.blender.org/api/main/info_overview.html) can automate the creation and manipulation of a Blender scene; its node editor can define procedural geometry. [WebGPU](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API) exposes rendering and compute pipelines that can underpin a visual system. None of these choices settles the story structure or the finished file by itself.

## 3. Delivery pipeline: how the work becomes media

The output path may be a directly rendered video, an image sequence for later assembly, or a browser scene that must be captured. [Remotion renders compositions to media or image sequences](https://www.remotion.dev/docs/cli/render). [Motion Canvas renders image sequences](https://motioncanvas.io/docs/rendering/) and offers an [FFmpeg video exporter](https://motioncanvas.io/docs/rendering/video/). [Manim renders scenes to video](https://docs.manim.community/en/stable/tutorials/quickstart.html). [FFmpeg](https://www.ffmpeg.org/ffmpeg.html) reads media streams, applies filters, transcodes, and writes output; its [filtergraphs](https://ffmpeg.org/ffmpeg-filters.html) can combine and transform streams.

Before building a complex scene, specify the delivery contract: frame size and rate, duration, audio tracks and sync points, alpha requirements, codec and container, and whether a frame must render correctly when requested out of order. These choices shape authoring even when the encoder comes last. If frames must render out of order, for instance, the table's question for the frame function needs an answer before building: does each frame depend only on declared inputs, or on earlier playback state? [Deterministic rendering](Deterministic%20rendering.md) covers frames computed from the frame number, and [capture and encoding](Capture%20and%20encoding.md) covers turning the frames and sound into the delivered file.

## Tool map

The table places common tools on the axes. Its fit-and-boundary column holds practical inferences from each tool's documented model and leaves other uses open.

| Tool or technique | Authoring and rendering emphasis | Practical fit and boundary | Official source |
| --- | --- | --- | --- |
| Remotion | React component as a frame function; browser rendering. | Reusable, parameterized layouts and media compositions. Browser rendering behavior shapes the output. | [Fundamentals](https://www.remotion.dev/docs/the-fundamentals) |
| Motion Canvas | Generator choreography over a 2D node scene; editor preview. | Informative vector animation and voiceover timing. Finished video uses its rendering/export path. | [Introduction](https://motioncanvas.io/docs/) |
| Manim | Scene, object, and animation model. | Precise diagrams and mathematical transformations. Scene structure is the main authoring unit. | [Building blocks](https://docs.manim.community/en/stable/tutorials/building_blocks.html) |
| Blender Python and Geometry Nodes | Scripted 3D scene plus procedural geometry graph. | Spatial visuals, materials, lighting, reusable geometry operations. Plan for scene and render work. | [Python API](https://docs.blender.org/api/main/info_overview.html), [Geometry Node Editor](https://docs.blender.org/manual/en/latest/editors/geometry_node.html) |
| p5.js | Immediate draw loop on canvas. | Generative sketches and experiments. Reproducible frame capture and assembly require an explicit path. | [`draw()`](https://p5js.org/reference/p5/draw/) |
| PixiJS | Retained 2D scene graph with GPU rendering. | Sprites, layered graphics, masks, filters. Timing and finished media need additional orchestration. | [Architecture](https://pixijs.com/8.x/guides/concepts/architecture) |
| three.js | 3D scene, camera, renderer. | Real-time spatial scenes. Offline capture and sound need additional orchestration. | [Creating a scene](https://threejs.org/manual/pages/creating-a-scene.html) |
| SVG, CSS, Web Animations API | Browser vector/DOM elements and property animation. | Text, diagrams, interface-like motion. Finished video needs frame capture. | [SVG animation](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/animate), [CSS animations](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Animations), [Web Animations API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API) |
| GLSL, WGSL, WebGPU | GPU vertex, fragment, and compute programs. | Procedural imagery and dense effects inside a larger scene or pipeline. | [GLSL](https://developer.mozilla.org/en-US/docs/Games/Techniques/3D_on_the_web/GLSL_Shaders), [WGSL](https://www.w3.org/TR/WGSL/), [WebGPU](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API) |
| FFmpeg | Stream filtering, encoding, and muxing. | Assemble, transform, and deliver media streams. Visual scene authoring usually happens upstream. | [FFmpeg](https://www.ffmpeg.org/ffmpeg.html), [filters](https://ffmpeg.org/ffmpeg-filters.html) |

For a new piece, first name the kind of picture (layout, diagram, sketch, 2D scene, 3D scene, procedural effect), then choose a time model, then define how a single frame and the delivered file get produced. That order keeps the design problem first and still brings the delivery constraints up early.
