# Capability boundaries

Code-authored video **specifies images over time and renders them**. How far it reaches depends on three things: the information available to the renderer, the form that information takes, and the quality the finished image must meet. Code can place a character exactly, control a camera, calculate light, and repeat a motion. Naming a convincing character design, an unseen side view, or a subtle facial performance in a prompt does not make the code supply it. In the chatlog's six boundary tests, the assistant described a cat gait as stiff and a fox head turn as weak ([Chatlog C-846](../sources/Chatlog%20index.md#c-846)).

So for each shot, ask: **What must be represented for this shot to work, and where will that representation come from?** The answer changes as images, models, motion capture, shaders, simulation, generated footage, and human artwork enter the composition.

## Compose a small set of capabilities

The [“Capabilities over features” principle](https://wiki.g15e.com/pages/Capabilities%20over%20features.md) distinguishes the range of possible outcomes from the number of functions a product exposes. It favors a few functions that each do a distinct job and can be combined. Here, an image filter alters a source, a timeline changes it over time, and a renderer turns the result into frames. The three are useful because each does one job that the next builds on.

| Capability | Input | Transformation | Output and next connection |
| --- | --- | --- | --- |
| **Represent a visual source** | Data, paths, pixels, geometry, or footage. | Make an image or object available to the scene. | A layer or object that can be placed and timed. |
| **Map time to a property** | A clock, event, or frame plus a property. | Evaluate a curve, keyframe, rule, or state update. | A value that can drive any compatible layer, camera, shader, or sound cue. |
| **Transform an object** | A source and spatial or appearance parameters. | Place, crop, deform, shade, recolor, or change viewpoint. | A revised source that can be combined with other sources. |
| **Combine sources** | Two or more layers, scenes, or audio streams. | Composite, mask, mix, and order them. | A scene or soundtrack that remains available for further transformation. |
| **Sample and deliver** | A scene and a time, then a frame and audio stream. | Render, capture, encode, or present live. | A still, video file, or interactive output. |

Each row's output can feed the next. In a title scene, a font supplies the letterforms, the scene places the text on screen, a time rule changes its opacity and position, and the renderer produces the frames. Different tools can do each job, and [authoring approaches](Authoring%20approaches.md) places them on its axes.

## The control surface

A renderer gives direct control over the properties it exposes:

| Property | Examples of direct control | What still needs to be supplied or solved |
| --- | --- | --- |
| Time | Start, end, duration, easing, synchronization, repeated motion. | The dramatic sense of a pause or transition. |
| Composition | Position, scale, hierarchy, camera framing, crop, layers. | Good visual judgment about balance and emphasis. |
| Text and data | Exact strings, values, chart geometry, interface states. | Correct source data, readable typography, meaningful labels. |
| Geometry | Paths, meshes, procedural forms, camera movement. | Appropriate shape design and detail for the desired style. |
| Surface and light | Colors, textures, materials, illumination, postprocessing. | Materials, lighting design, and enough geometry or texture information. |
| Performance | Poses, trajectories, rigs, blend shapes, motion curves. | A good rig and well-authored acting or motion data. |
| Sound | Timed cues, synthesis parameters, track placement. | Musical composition, sound selection, and listening judgment. |

Canvas, SVG, and DOM can calculate shapes, pixels, and layouts; [WebGL exposes GPU rendering of 2D and 3D graphics](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API). A 3D renderer adds cameras, models, lighting, and material interactions. For example, Blender's animation system includes armatures, constraints, and shape keys for controlled deformation, while its Cycles renderer traces reflection, transmission, and shadow paths. These systems widen what you can express and ask for more authored input in return. [Blender animation and rigging](https://docs.blender.org/manual/en/latest/animation/introduction.html); [Cycles light paths](https://docs.blender.org/manual/en/4.5/render/cycles/render_settings/light_paths.html).

The chatlog's Stage intro was a strong fit: typography, tunnel movement, a countdown, particle convergence, and a musical drop could share one precise time plan. The reported output was a 24-second video with coded visuals and audio. The same report states that its sound was checked by levels, not by listening. [Chatlog C-513](../sources/Chatlog%20index.md#c-513). FOXTALE used low-resolution visuals, menu and dialogue states, scripted movement, and patterned projectiles. Its reported trailer shows a different strong fit, one built on rules and timing. [Chatlog C-1146](../sources/Chatlog%20index.md#c-1146).

## Detail, not a realism switch

“Photorealistic versus stylized” is too coarse a boundary. A clean infographic can demand very exact data and typography and ask little of anatomy. A hand-drawn character can be highly stylized and still demand complex anatomy, line quality, posing, and expression. A chrome logo may look realistic with simple geometry because its material and environment supply much of the appearance. A human face seen from changing angles needs a plausible volume, surface, illumination, and performance.

Consider these dimensions separately:

- **Spatial information**: Does the shot require only a flat image, layered depth, a 3D object, or a changing viewpoint into unseen surfaces?
- **Temporal information**: Is motion a known curve, a set of poses, a simulation, or nuanced acting that must be authored or captured?
- **Surface information**: Are simple colors enough, or are material variation, texture, translucency, and lighting central to the result?
- **Specificity**: Must text, UI, data, and exact object identity remain unchanged, or is visual variation acceptable?
- **Scale**: Is the need one hero image or a large cast and many environments that must share a coherent design language?
- **Tolerance**: Is an illustrative approximation adequate, or will the audience scrutinize close-up realism and motion?

These questions help read the chatlog's six boundary tests. In its closing assessment, the assistant reported an accurate data chart after a drawing-state fix. It judged motion in a photo's existing water and lights as natural, but an added boat as visibly pasted in. It described the cat gait as stiff, the fox head turn as weak, and the sunset sea shader as game-like rather than cinematic. These are the assistant's assessments after one creation pass and one revision per scene. The need for missing poses, views, or surface detail is an inference from those reports. [Chatlog C-846](../sources/Chatlog%20index.md#c-846).

## What a shader, simulation, or 3D scene changes

A shader computes color or geometry from inputs such as coordinates, time, textures, lights, and camera position. That suits it to repeating detail and continuous effects: waves, distortion, atmospheric gradients, stars, procedural surfaces, and stylized fire. A more elaborate shader can model complicated optical behavior, but its output is only as good as its model and inputs. The shader does not infer an unseen character pose from a still image. [WebGL shader introduction](https://developer.mozilla.org/en-US/docs/Games/Techniques/3D_on_the_web/GLSL_Shaders); [WGSL specification](https://www.w3.org/TR/WGSL/).

A 3D scene gives the renderer a representation of surfaces behind the initial image plane. It can support a moving camera and new views, provided the model, rig, textures, lighting, and motion are suitable. Shape keys can encode target facial shapes and expressions; a skeletal rig can coordinate articulated motion. Because these tools exist, do not declare code incapable of character animation. The hard work moves into the model, the rig, the performance, and look development. The chatlog's stiff cat gait may sit in this territory, though reading it as a rig or performance gap is an inference from the assistant's report ([Chatlog C-846](../sources/Chatlog%20index.md#c-846)). [Blender shape keys](https://docs.blender.org/manual/en/latest/animation/shape_keys/introduction.html); [Blender rigging](https://docs.blender.org/manual/en/latest/animation/introduction.html).

Simulation supplies motion from rules and initial conditions. It can give cloth, particles, fluids, and rigid objects complex behavior without writing every position by hand. It also introduces state: a frame may depend on earlier frames. Blender describes simulation zones this way and supports baking them so frames can later be rendered out of order. [Blender simulation nodes](https://docs.blender.org/manual/en/latest/physics/simulation_nodes.html). Simulation may make motion richer, but a plausible simulation can still be the wrong gesture for a scene.

## A useful boundary model

For each difficult visual, locate the missing information:

1. **Rule missing**: The assets exist, but the timing, positioning, or transformation is poorly specified. Code and iteration can often resolve this.
2. **View or shape missing**: Only a single image exists, while the shot requires a new angle or deformation. Add another view, a layered cutout, a rig, a model, or generated imagery.
3. **Appearance missing**: Geometry exists, but texture, material, lighting, or artistic treatment carries the style. Supply those inputs or use a renderer designed for them.
4. **Performance missing**: The system can move an object but lacks expressive poses, rhythm, and intent. The work shifts to authored animation, reference footage, capture, or rounds of direction.
5. **Evaluation missing**: The mechanism works, but nobody has judged the actual result at the delivery size and with sound. The chatlog's Stage intro was in this state at the time of the report ([Chatlog C-513](../sources/Chatlog%20index.md#c-513)).

A scene can mix code-controlled typography, a designed illustration, a rigged character, generated footage, and recorded or synthesized sound. The code then controls how those ingredients relate to one another. The chatlog's later reflection moved in this direction: the strongest FOXTALE portrait came from an existing illustration converted to pixel art, and the hand-authored sprites were closer to prototype art. [Chatlog C-1332](../sources/Chatlog%20index.md#c-1332).

The chatlog records a few **composed outcomes**, each built from replaceable parts: a timed title and particle reveal assembled from text, procedural graphics, shared beats, and synthesized audio; a pixel-game scene assembled from sprites, a converted portrait, dialogue UI, scripted movement, and music; and a photo animation that the assistant reported as effective for details already present in the still. [Chatlog C-513](../sources/Chatlog%20index.md#c-513); [Chatlog C-1146](../sources/Chatlog%20index.md#c-1146); [Chatlog C-846](../sources/Chatlog%20index.md#c-846).

The six boundary tests show where one representation ran into friction at that level of effort. To predict how another project will go, you need the target shot, the available ingredients, the time to author them, and the standard of finish you will accept.
