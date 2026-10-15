# Raster, vector, and DOM

Browser graphics can come from three closely related layers: HTML/CSS layout, SVG geometry, and Canvas 2D drawing. They share a browser viewport, but each gives you different control over objects, pixels, and animation. In the end the browser turns the output of all three into painted and composited pixels. [MDN rendering stages](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Animation_performance_and_frame_rate).

## HTML and CSS: layout as a graphics tool

The DOM suits visuals with a lot of text, repeated cards, labels, grids, or familiar layout relationships. CSS controls type, alignment, spacing, stacking, clipping, borders, backgrounds, transforms, and opacity. The browser resolves these rules into geometry, paints the elements, and composites overlapping layers. This lets a scene adapt when text length changes, without recalculating every coordinate by hand. [How browsers work](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work).

A CSS animation specifies keyframes for properties, and the browser interpolates between them. A transform or opacity change can sometimes be handled during compositing, while a change to geometry, such as `width` or `left`, can trigger layout and paint. The difference matters for live playback, especially in scenes with many elements. For offline export, it also changes how much work each sampled frame takes. [Animation performance and frame rate](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/Animation_performance_and_frame_rate).

The Web Animations API exposes animation objects to JavaScript. You can set their `currentTime`, including while they are paused, so you can sample a CSS-like animation at a chosen time. A practical capture system has to account for every animation source in the page, because a CSS animation that runs on its own clock can undermine the renderer's single timeline. [Web Animations API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API/Using_the_Web_Animations_API), [`Animation.currentTime`](https://developer.mozilla.org/en-US/docs/Web/API/Animation/currentTime).

## SVG: resolution-independent shapes

SVG is a document of vector shapes and related elements. Rectangles, circles, paths, text, groups, fills, strokes, gradients, masks, clipping, and filters are all elements and attributes. Its coordinates can be mapped to a viewport, and its elements can be styled with CSS or changed with JavaScript. [SVG tutorial](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorials/SVG_from_scratch), [SVG introduction](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorials/SVG_from_scratch/Introduction).

SVG is especially expressive when the structure of a visual is geometric: a route growing along a path, nodes and connectors, line drawings, an icon being assembled, or labels anchored to shapes. A shape stays a shape until it is rasterized, so the same source can be rendered at different frame sizes. SVG filters add operations such as blur and lighting effects. [Basic shapes](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorials/SVG_from_scratch/Basic_shapes), [filter effects](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorials/SVG_from_scratch/Filter_effects).

SVG text is real text, but how it looks still depends on font selection and metrics. You set its position with coordinates and alignment attributes such as `text-anchor`. Complex paragraph layout often fits HTML better, and lettering along a path or precise labels often fit SVG well. [SVG text](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Texts).

## Canvas 2D: drawing into a bitmap

Canvas 2D offers commands for paths, shapes, text, images, transforms, clipping, compositing, and pixel operations. It suits visuals built from many drawing operations, and programs that need direct access to image data. The canvas stores a bitmap, so once a shape is drawn, moving it means drawing new pixels. A common animation frame clears the canvas, saves state, applies transforms, draws, and restores state. [Canvas tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial), [basic animation steps](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Basic_animations).

A canvas has two sizes to keep apart. Its `width` and `height` attributes define the drawing buffer. CSS can display that buffer at another size, and the browser then scales the image to fit, which can distort it if the aspect ratio differs. A capture pipeline should decide the output pixels it wants and map scene coordinates to that buffer on purpose. [Canvas basic usage](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Basic_usage).

For heavy canvas work, `OffscreenCanvas` lets you draw in a worker and transfer the rendered images to a visible canvas. That can keep the main thread responsive during preview. You still have to decide which time and which size a captured frame represents. [OffscreenCanvas](https://developer.mozilla.org/en-US/docs/Web/API/OffscreenCanvas).

## Shared constraints at capture time

- **Fonts**: text shape and wrapping can change after a font loads. `document.fonts.ready` resolves after font loading and the related layout work are complete. [MDN FontFaceSet](https://developer.mozilla.org/en-US/docs/Web/API/FontFaceSet/ready).
- **Images**: `HTMLImageElement.decode()` resolves when the image data is decoded and ready for use, so a captured frame does not get an empty or late image. [MDN image decode](https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/decode).
- **Cross-origin media**: drawing an image from another origin into a canvas without the right CORS permission taints the canvas, and pixel readback and canvas export methods then fail. [MDN cross-origin images](https://developer.mozilla.org/en-US/docs/Web/HTML/How_to/CORS_enabled_image).
- **Color and transparency**: a canvas can have an alpha channel and a selected color space such as sRGB or Display P3. Export and encoding may require further pixel-format decisions. [Canvas context attributes](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/getContextAttributes), [FFmpeg pixel format](https://ffmpeg.org/ffmpeg.html).

In a mixed scene, HTML can handle typography and layout, SVG can handle precise vector geometry, and Canvas can handle dense procedural pixels. Where one layer ends and the next begins is an implementation choice inside one visual composition. See [Representation models](Representation%20models.md) for the broader model and [Deterministic rendering](Deterministic%20rendering.md) for sampling these layers into frames.
