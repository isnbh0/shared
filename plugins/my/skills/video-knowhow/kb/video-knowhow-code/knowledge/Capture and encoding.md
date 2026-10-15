# Capture and encoding

A code-authored video has two separate jobs: draw the intended picture at each time, then turn those pictures and the audio into a playable file. Keeping the jobs separate makes a scene easy to revise and the exported result easy to inspect. In SLASH_MY (checked at `fd543f2a`), `audio.js` writes the score to `score.wav`, and the muxed delivered file opens with a 5 s warning card (`render.js` L14-16), so the drop at film time 56 s plays at 61 s ([Audiovisual synchronization](Audiovisual%20synchronization.md)).

```text
scene code + assets + time t → rendered frame
rendered frames + audio samples → encoded video/audio streams → container file
```

The renderer can be Canvas, WebGL, SVG, HTML/CSS, or a mixture. Whichever it is, the encoder receives only pixels and samples, never the scene's objects or animation rules, and cannot tell renderer drift from an intended change. SLASH_MY's session records log one such difference: repeat GPU renders of the same frame differed by one to ten gray levels, and judged and delivered rendering moved to CPU rasterization ([Deterministic rendering](Deterministic%20rendering.md#a-production-decision-on-raster-mode)). An MP4 file, for example, is a container, while H.264 is a video codec and AAC is an audio codec. [MDN: video processing concepts](https://developer.mozilla.org/en-US/docs/Web/API/WebCodecs_API/Video_processing_concepts)

## Choose how frames enter the encoder

| Route | What it gives you | What to account for |
| --- | --- | --- |
| Render at explicit times and save an image sequence | A visible frame for each chosen time. Easy to inspect, rerender, and feed to FFmpeg. | Storage and readback cost; assets and fonts must have loaded before capture. |
| Render at explicit times and pipe raw frames to FFmpeg | Avoids writing every image to disk. | The pipe must specify dimensions, pixel format, and frame rate; failures need a way to identify the bad frame. |
| `canvas.captureStream()` with `MediaRecorder` | A browser can record a live canvas stream directly. | Capture follows browser painting and recorder scheduling, so validate actual output timestamps and frames. |
| `VideoFrame` with WebCodecs | Each frame can carry a presentation timestamp, then be sent to an encoder. | WebCodecs yields encoded chunks; another component must mux them with audio into a container. |

The first two routes pair naturally with a time-addressable renderer: for a frame index `i` at frame rate `F`, render the scene at `t = i/F`. Specify the image sequence's input rate with FFmpeg's `-framerate`; an output `-r` can **duplicate or drop** frames to reach its requested rate. FFmpeg's `-fps_mode cfr` can also duplicate or drop frames, and `passthrough` forwards frame timestamps unchanged. Use these controls to state the intended timeline, and do not let them hide missing captures. [FFmpeg CLI](https://ffmpeg.org/ffmpeg.html)

Canvas capture offers some manual control: `captureStream(0)` disables automatic frame requests and its track exposes `requestFrame()`. The [W3C capture specification](https://www.w3.org/TR/mediacapture-fromelement/) also says a frame is requested when the track is created, and a requested frame is added when new canvas content is painted. A call to `requestFrame()` therefore asks the browser to sample the painted canvas. It does not promise that a frame with a chosen presentation timestamp has been written to the output file. Use it when a live recording is good enough, and inspect the encoded file when exact cadence matters.

`MediaRecorder` handles encoding and container selection through the browser. You can request a MIME type and test it with `MediaRecorder.isTypeSupported()`, but resource pressure can still make recording fail. Its `timeslice` sets how often data chunks are delivered, which is unrelated to frame boundaries, and chunk intervals can be delayed. [MDN: MediaRecorder configuration](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/MediaRecorder), [MDN: type support](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/isTypeSupported_static), [MDN: data chunks](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/dataavailable_event)

WebCodecs lets an application supply a `VideoFrame` timestamp in microseconds and configure a `VideoEncoder`. The `framerate` setting tells the encoder what rate to expect, while the presentation times still come from the frame timestamps. Query `VideoEncoder.isConfigSupported()` on the machine that will encode. WebCodecs does not write MP4 or WebM structure on its own. [W3C WebCodecs](https://www.w3.org/TR/webcodecs/), [MDN: container handling](https://developer.mozilla.org/en-US/docs/Web/API/WebCodecs_API/Video_processing_concepts), [MDN: encoder support](https://developer.mozilla.org/en-US/docs/Web/API/VideoEncoder/isConfigSupported_static)

## The boundary between rendering and capture

A browser animation preview usually runs on `requestAnimationFrame()`. Its callbacks generally follow display refresh and can pause in a background tab. That makes it a useful preview clock and an unreliable count of export frames. During offline export, render each requested time from the scene's time model. If the preview and the export should show the same composition, drive both from the same scene function. [MDN: requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame)

Capture a complete frame: wait for fonts, images, shaders, and other asynchronous assets; set the intended viewport and pixel dimensions; then read the resulting pixels. In Canvas and WebGL, reset per-frame state on purpose, since drawing state can persist from one frame to the next. All of this is the renderer's job and happens before encoding begins. See [Deterministic rendering](Deterministic%20rendering.md) for repeatability and [Time and motion](Time%20and%20motion.md) for the scene clock.

## Encode for the destination

Choose the video codec, audio codec, container, pixel format, resolution, and quality setting as one delivery profile. An encoder's bitrate or quality control trades file size against lost detail. Busy particles, gradients, grain, and fast motion can expose compression artifacts that do not show in static frames. The audience sees the decoded file, so inspect that file as well as the source frames. [MDN: video codec guide](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Video_codecs)

For an image sequence, a typical FFmpeg shape is:

```sh
ffmpeg -framerate 60 -i 'frame_%05d.png' -i audio.wav \
  -c:v libx264 -pix_fmt yuv420p -c:a aac output.mp4
```

The command shows the shape of the pipeline, and its values change with the destination. Before delivery, check the encoded duration, frame count, audio endpoint, and destination playback. Frame count can go wrong before FFmpeg runs: SLASH_MY's session records log a frame-range tool that rounded each frame time on its own, so float noise duplicated and skipped frames and cut an audio slice late. One shared helper that snaps each span outward to whole frames fixed it (commit `44565e33`, [Verification](Verification.md)). See [Delivery and color](Delivery%20and%20color.md), [Audiovisual synchronization](Audiovisual%20synchronization.md), and [Verification](Verification.md).
