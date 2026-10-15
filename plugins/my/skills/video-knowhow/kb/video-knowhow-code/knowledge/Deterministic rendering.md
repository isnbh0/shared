# Deterministic rendering

Deterministic rendering means that asking for the same frame with the same inputs produces the same intended scene, regardless of when or where that frame is rendered. That property supports exact-duration exports, previews that match the delivered output, retries, and rendering segments in parallel. The central design choice is to compute the visual state from the frame number or timestamp. [Remotion's frame model](https://www.remotion.dev/docs/the-fundamentals), [Remotion's parallel-rendering randomness example](https://www.remotion.dev/docs/using-randomness).

## One output clock

A video composition has a frame size, frame rate, and duration. For constant frame rate, frame `n` represents a sample at `t = n / fps` seconds. All animated properties—positions, opacity, masks, shader uniforms, camera parameters, media trims—should derive from the same time coordinate or be synchronized to it. Remotion exposes the frame number and composition settings, and a Web Animations API object can be sought by setting its `currentTime`. [Remotion fundamentals](https://www.remotion.dev/docs/the-fundamentals), [timing and trimming](https://www.remotion.dev/docs/timing), [Animation.currentTime](https://developer.mozilla.org/en-US/docs/Web/API/Animation/currentTime).

A live browser loop runs on a different clock. `requestAnimationFrame()` is scheduled before display refresh, follows the display's rate, and may pause in background tabs, which suits interactive preview. Timing by the wall clock, or assuming 60 fps, can give different sample times on different devices or under load. When rendering to a file, let the requested frame number decide the picture, even if drawing that frame takes longer than one frame interval. [`requestAnimationFrame`](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame).

## Seekable state

An animation is **seekable** when its appearance at time `t` can be calculated without replaying every earlier preview frame. Keyframe interpolation, easing curves, and analytic paths are naturally seekable: position is a function of `t`. Stateful systems—particle simulations, spring integration, fluid effects, accumulated trails—need a defined strategy if frames may be requested out of order. They can be evaluated from an initial state with fixed steps, checkpointed, precomputed, or replaced with a time-based expression when that gives the desired appearance. [Representation models](Representation%20models.md) gives the contrast: a title position computed from `t = frame / fps` can be sampled at frame 900 without visiting frames 0–899, while a simulation that updates `position += velocity * delta` depends on the previous steps unless its state is reconstructed, cached, or evaluated analytically. [Web Animations timing model](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API/Web_Animations_API_Concepts), [Remotion frame timing](https://www.remotion.dev/docs/timing).

Randomness is another input. When each render worker draws its own random numbers, objects can shift between frames, and a stable seed tied to a specific element and purpose makes the scene reproducible. Remotion documents this failure mode and supplies a seeded `random()` function. [Remotion randomness](https://www.remotion.dev/docs/using-randomness).

## Readiness before sampling

Before sampling a frame, the renderer must wait for everything the scene needs at that frame. Fonts alter text metrics and wrapping; `document.fonts.ready` resolves after fonts and related layout complete. Images may require decoding; `HTMLImageElement.decode()` exposes readiness. A 3D renderer can stall on first use while shaders compile or textures upload, and three.js exposes precompilation and texture initialization methods. Data fetched asynchronously must also finish before a frame is captured; Remotion's `delayRender()` is one framework-specific way to express that gate. [Fonts](https://developer.mozilla.org/en-US/docs/Web/API/FontFaceSet/ready), [images](https://developer.mozilla.org/en-US/docs/Web/API/HTMLImageElement/decode), [three.js renderer](https://threejs.org/docs/pages/WebGLRenderer.html), [Remotion delayRender](https://www.remotion.dev/docs/delay-render).

Capture parameters are inputs too. Fix the viewport, canvas backing-store size, device scale factor, and output color space, so that layout and raster differences are not mistaken for animation changes. Playwright's screenshot options choose between one pixel per CSS pixel and one per device pixel, and canvas contexts expose color-space and alpha settings. [Playwright screenshots](https://playwright.dev/docs/api/class-page), [Canvas sizing](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Basic_usage), [Canvas context attributes](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/getContextAttributes).

## From scene to file

The capture paths differ in timing:

| Path | What is captured | Timing character |
| --- | --- | --- |
| Browser screenshot or pixel readback | A deliberately prepared scene at a requested time | Frame-addressed; each image can be checked or retried |
| `canvas.captureStream()` and `MediaRecorder` | A real-time stream of canvas changes | Tied to capture/playback scheduling; convenient for live recording |
| `VideoFrame` and WebCodecs `VideoEncoder` | Explicit raw frames with timestamps | Frame-addressed encoding; caller handles the file container |

The table draws on [Playwright screenshots](https://playwright.dev/docs/api/class-page), [canvas capture](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/captureStream), [MediaRecorder](https://developer.mozilla.org/en-US/docs/Web/API/MediaStream_Recording_API), and [WebCodecs](https://developer.mozilla.org/en-US/docs/Web/API/WebCodecs_API/Using_the_WebCodecs_API). A `VideoFrame` timestamp is in microseconds; WebCodecs produces encoded chunks but does not itself mux them into a video file. [WebCodecs video processing concepts](https://developer.mozilla.org/en-US/docs/Web/API/WebCodecs_API/Video_processing_concepts).

Numbered image files are another frame-addressed intermediate. FFmpeg's `image2` demuxer reads a sequence, and input `-framerate` determines the sequence's timestamps. Output `-r` may instead duplicate or drop frames to reach a requested output frame rate, so keep the two apart when checking duration and motion cadence. [FFmpeg formats](https://ffmpeg.org/ffmpeg-formats.html), [FFmpeg command manual](https://ffmpeg.org/ffmpeg.html).

Audio has its own samples and timestamps. It must be trimmed, placed, mixed, and muxed against the video timeline as its own stream, apart from the image. FFmpeg filtergraphs include audio mixing and fades, while video filters handle overlays and other visual operations. The finished file's streams, duration, and frame properties can be inspected with `ffprobe`. [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html), [ffprobe](https://ffmpeg.org/ffprobe.html).

## A production decision on raster mode

**Reported (SLASH_MY):** the SLASH_MY production's session records (held in John's workspace) record the decision that made its review rounds comparable. Repeat renders of the same frame differed because the browser rasterizes the canvas on the GPU, with run-to-run differences of one to ten gray levels that grow under load. Judged and delivered rendering moved to CPU rasterization, about twelve times slower; quick previews stayed on the GPU and were labeled "GPU raster, not reproducible"; the render cache never mixes modes; and a determinism check compares repeated frames. The production paid the slowdown where judgments and delivery need like-for-like frames, and kept it out of the iteration loop, where speed matters. The round discipline this served is the craft shelf's [convergence](../../video-knowhow-craft/knowledge/Convergence.md) system. The change is in commits `be27da90`, `3175d0bd`, `247398bf`, and `b6e1028a`.

Determinism means controlling scene inputs and frame times. Byte-identical encoded files are a separate matter, because encoding settings and implementations also affect the file. See [Representation models](Representation%20models.md) for how scenes are described, [Raster, vector, and DOM](Raster%20vector%20and%20DOM.md) for browser capture inputs, and [Shaders and 3D](Shaders%20and%203D.md) for GPU rendering.
