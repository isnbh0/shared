# Assets and provenance

A code-authored video can compute every frame and still lean heavily on assets: the font that sets a title's character, the illustration that sets a portrait's quality, the texture that gives a surface its detail, the model that gives a camera move its geometry, and the recording that supplies a voice or a performance. **Assembling a video in code does not mean code created every ingredient.**

Keep **what the source asset provides** apart from **what the scene code does to it**. The asset brings information and artistic quality, and the code does placement, transformation, timing, layering, and output.

## The source-to-scene capability

An asset enters a scene in five steps: **obtain the file → load it → alter or select part of it → place it in the scene → record where it came from**. The same steps apply to a font, photograph, model, voice track, or generated video clip. The steps follow the idea of [distinct functions that can be combined](https://wiki.g15e.com/pages/Capabilities%20over%20features.md).

What you do to an asset decides what information it holds afterward. Cropping and recoloring rework information already in the source. Palette reduction throws color detail away. Modeling adds geometry that was not there, a rig adds controls for posing it, and a generated asset or new artwork can add a view or a shape that the earlier source lacked. For example, code can turn an illustration into a limited-color portrait, place it beside a dialogue box, and then animate the box.

## Asset roles

| Ingredient | Information it contributes | What code can readily control | Common missing information |
| --- | --- | --- | --- |
| Still image | One rendered view, color, texture, design. | Crop, pan, zoom, warp, masks, color adjustment, layered motion. | Hidden sides, occluded parts, new expressions. |
| Layered illustration | Separate foreground, limbs, face, background, and effects. | Parallax, independent motion, simple deformation. | Anatomy for large angle changes; unpainted regions. |
| Sprite sheet | Authored poses and transitions at a chosen resolution. | Frame selection, speed, facing, position, palette. | Poses or actions absent from the sheet. |
| Vector artwork | Paths, fills, strokes, groups. | Recolor, transform, morph compatible paths, restyle. | Painterly surface and complex form outside the paths. |
| 3D model and rig | Surfaces, depth, articulation, sometimes materials. | Camera, pose, light, material values, animation curves. | High-quality motion, textures, corrective shapes. |
| Video footage | Captured or generated appearance and motion over time. | Edit, retime, crop, composite, overlay. | New viewpoint or actions not in the footage. |
| Audio, voice, music | Timbre, performance, language, musical structure. | Placement, cuts, gain, effects, synchronization. | A new performance or a convincing missing sound. |
| Font | Letterforms, metrics, weight, language coverage. | Size, color, tracking, animation, layout. | Glyphs the font does not include; licensing for the use. |

A transformation keeps only what the source, or a model added to it, supports. Enlarging a still photograph does not show its back side. A 2D cutout can turn a head a little if enough shapes were prepared; a large turn calls for new art or a 3D form. The chatlog's boundary tests fit this limit: the assistant judged motion in a photo's existing water and light as natural, an inserted boat as visibly pasted in, and a fox head turn as weak. By themselves those reports do not measure how far another asset or method could go. [Chatlog C-846](../sources/Chatlog%20index.md#c-846).

Pixel art shows the split between asset and code especially clearly. Its low resolution leaves fewer visual decisions to make, but someone still has to direct them. FOXTALE paired small code-authored sprites with a portrait derived from an existing fox illustration, and the chatlog later judged the converted portrait more polished than the hand-coded sprites. Part of the portrait's style and quality came from the input image, while code supplied the conversion, motion, UI, and timing. [Chatlog C-1146](../sources/Chatlog%20index.md#c-1146); [Chatlog C-1332](../sources/Chatlog%20index.md#c-1332).

The chatlog shows this chain once: **illustration → reduced palette and pixel scale → portrait layer → timed dialogue scene**. A different illustration could enter at the first step without changing the dialogue and timing system.

## Composition is a chain of ingredients

The term *provenance* means the history of a media asset: where its ingredients came from and how the asset was transformed. C2PA formalizes this with assertions about origins, actions, ingredients, and content bindings. The model helps even when you emit no C2PA manifest: you can treat a delivered render as a chain of sources and transformations. [C2PA explainer](https://spec.c2pa.org/specifications/specifications/2.2/explainer/Explainer.html); [ingredient specification](https://spec.c2pa.org/specifications/specifications/2.4/specs/ContentCredentials.html#_adding_ingredients).

For a practical project, keep enough information to answer:

- Which images, models, fonts, recordings, and generated outputs appear in the delivered piece?
- Who or what made each one, and where was it obtained?
- What version or source file was used?
- What transformations were applied, such as crop, recolor, pixel conversion, retiming, or compositing?
- What terms govern redistribution, adaptation, attribution, or commercial use?

Match the detail to the work: a simple list may do for one short experiment, while a public release with many contributors needs a reliable asset record.

**Provenance records history, and a license grants permission.** A cryptographically bound provenance record can help show that a claim and its ingredient history have not been altered, but it gives no right to use a source. A properly licensed asset, for its part, may carry no machine-readable provenance at all. C2PA explicitly describes provenance as statements about asset history, while Creative Commons licenses describe conditions such as attribution and whether adaptations or commercial reuse are allowed. [C2PA specification](https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html); [Creative Commons license overview](https://creativecommons.org/share-your-work/use-remix/cc-licenses/).

## Asset boundaries in browser rendering

A source file can sit on disk and still be out of reach of a browser renderer in the way you need. For example, drawing an image from another origin into a canvas can make the canvas **tainted**, preventing pixel reads and export operations such as `getImageData()`, `toBlob()`, and `captureStream()` unless the source permits cross-origin use. Local `file://` pages can also have opaque origins; an HTTP server or correctly embedded assets can change the loading behavior. [MDN on canvas and cross-origin images](https://developer.mozilla.org/en-US/docs/Web/HTML/How_to/CORS_enabled_image); [MDN on WebGL textures](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/Tutorial/Using_textures_in_WebGL).

The FOXTALE browser page ran into this in the chatlog. Its local HTML tried to read an image's pixels for conversion and failed under `file://`, although the video-render path had used a local server. A later single-file HTML that embedded the ingredients opened successfully. The cause was the browser's origin rules, which say nothing about what pixel conversion can do artistically. [Chatlog C-1319](../sources/Chatlog%20index.md#c-1319).

## What “made with code” communicates

That phrase can mean several things: code drew every pixel; code assembled supplied images and audio; code drove a 3D scene; or an agent wrote and ran all the code with external tools. The chatlog's opening investigation described browser drawing, frame capture, sound synthesis, and FFmpeg assembly. It also noted that claims such as “made with the model alone” often meant no separate generative video service was used, not that no software or source material was involved. That investigation read the posts as text and did not directly inspect their videos. [Chatlog C-231](../sources/Chatlog%20index.md#c-231).

To describe an output, name the kinds of ingredients and what code did with each. For example: “The fox portrait came from a supplied illustration; code reduced its palette and placed it in a timed, rendered scene.” From that sentence a future maker can tell what to reuse, replace, or improve, and that the renderer did not invent the source artwork.
