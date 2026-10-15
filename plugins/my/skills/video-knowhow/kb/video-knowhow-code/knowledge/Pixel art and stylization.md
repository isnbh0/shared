# Pixel art and stylization

A code-rendered pixel style depends on raster scale, sprites, palettes, and how source assets are treated. [Visual identity and style](../theory/Visual%20identity%20and%20style.md) explains how these choices work together across scenes. [Grouping and continuity](../theory/Grouping%20and%20continuity.md) explains how a character or interface stays recognizable while it moves.

## The pixel grid is part of the design

A pixel-art scene usually starts with a logical canvas smaller than the delivered frame. You render to that canvas and then scale it up, and the scale factor sets the size of the visible pixels. MDN explains that smoothing can blur pixel art and that `image-rendering: pixelated` can preserve harder edges in browser output. Its canvas guidance also shows why noninteger scaling inside the logical canvas can produce uneven or soft pixels. [MDN: crisp pixel art](https://developer.mozilla.org/en-US/docs/Games/Techniques/Crisp_pixel_art_look), [MDN: image-rendering](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/image-rendering)

The grid matters for motion too. A character that moves by fractions of a logical pixel can jitter or blur, depending on the renderer and the filter. Snapping positions to whole pixels changes the cadence of the motion. Subpixel positions allow smoother motion but may weaken the intentionally discrete look. Godot documents pixel snapping as a rendering choice and exposes integer and subpixel positioning as options. Decide the tradeoff at the scale of the scene. [Godot 2D snapping documentation](https://docs.godotengine.org/en/stable/tutorials/2d/introduction_to_2d.html)

When the resolutions align, an integer upscale gives each logical pixel the same output area. A 320×180 canvas, for example, scales exactly to 1920×1080 at 6×. At a noninteger viewport scale, some pixels may appear wider or taller than others, and MDN notes that this can also happen when CSS pixels and device pixels do not map evenly. A fixed video render can use logical and output resolutions that match, but check browser previews separately. [MDN: crisp pixel art](https://developer.mozilla.org/en-US/docs/Games/Techniques/Crisp_pixel_art_look)

## Style is more than nearest-neighbor scaling

Nearest-neighbor enlargement keeps the source pixels intact. The rest of the result depends on other choices:

- **Shape language**: silhouettes, proportions, repeated angles, and how much detail each object gets.
- **Color organization**: a palette with roles for background, character, highlight, shadow, effects, and UI. A limited palette is an optional design constraint and does not guarantee quality.
- **Cluster design**: groups of adjacent pixels read as edges, contours, and shading. Isolated noise can make a sprite look busy without making its form clearer.
- **Texture treatment**: dithering, outlines, hard-edged shadows, and selective antialiasing each change the perceived material and the period the style refers to.
- **Scale consistency**: sprites, text, effects, and borders need pixel sizes chosen to work together. A low-resolution sprite next to ultra-smooth effects can be an intentional hybrid, but the viewer should be able to see it as one intended choice.
- **Animation vocabulary**: frame stepping, idle loops, squash, screen shake, and particles can each be quantized or smooth. The mix changes the character of the style.

Compare these dimensions in rendered frames. Aseprite's sprite-resize API offers nearest-neighbor resizing next to other filters, which shows that pixel treatment is a production decision you select. [Aseprite SpriteSize API](https://www.aseprite.org/api/command/SpriteSize)

## Separate assets from the system that presents them

Dialogue boxes, menus, bullet patterns, tile fields, transitions, and particle effects have geometry and timing that code can reuse. A distinctive portrait, an animated expression, or an illustrated background may need an artist, an image source, or a different rendering method. In the source chatlog (dialogue line 1332), the assistant reported that the FOXTALE portrait it judged strongest came from converting an existing illustration. Both the visual judgment and the account of the asset are the assistant's report, and neither has been checked independently here. When you evaluate a rendering method, keep the quality of the source art apart from the code that presents it.

Converting an image to pixel art is a separate design step. Downsampling, palette mapping, edge cleanup, and manual correction can bring source images into a shared pixel style. Automatic conversion may leave noisy clusters or inconsistent proportions. In a hybrid pipeline, record the source image and the conversion settings, then judge the resulting sprite at the scale it will be shown.

## Code-controlled vocabulary

| Concern | Controllable parameters | Inspection |
| --- | --- | --- |
| Raster scale | Logical resolution, output resolution, scale factor, letterbox or crop | Are visible pixels uniform and are shapes recognizable at the delivered size? |
| Sampling | Nearest or smooth filtering, pixel snapping, subpixel movement | Do edges stay intentional during camera moves and scaling? |
| Palette | Named colors, role mapping, shade steps, alpha | Do characters separate from backgrounds without relying on hue alone? |
| Sprite structure | Silhouette, tile dimensions, anchor point, frame count, animation step duration | Can the action be read from a small contact sheet? |
| UI and effects | Border thickness, font pixel scale, particle size, shake amplitude | Do effects belong to the same visual world as the assets? |
| Asset sourcing | Original file, generated or hand-drawn source, conversion settings | Can a weak result be traced to source, conversion, layout, or rendering? |

## Questions a render can answer

- Is the logical pixel scale the same across moving sprites, typography, UI, and effects?
- Do silhouettes and poses read when color and small texture details are removed?
- Does the animation show what the character intends, or does it only move a rigid sprite between coordinates?
- Which perceived quality comes from the source art, and which comes from presentation that code controls?
- If a polished asset is replaced with a simple placeholder, do the layout and timing still work?
