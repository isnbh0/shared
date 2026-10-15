# Code-video starter

A small skeleton for making a video with code. One HTML page draws each frame of a 1920×1080 canvas from the frame number. A Node script writes the soundtrack from the same beat clock. A second script captures the page frame by frame in headless Chrome and encodes an MP4 with picture and sound. Copy this folder and render it, then replace the placeholder scene and score with your own film.

## Run it

You need Node 22.12 or later and an installed Chrome or Chromium. ffmpeg comes with `npm install` (ffmpeg-static).

```sh
npm install
export CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"   # macOS
npm run render                        # score.wav, then out/clip.mp4: the whole 8-second clip
npm run render -- --frames 0-90       # the first 3 seconds only
npm run preview                       # live preview at http://localhost:8000/
```

On Linux, point `CHROME_PATH` at Chrome or Chromium, for example `export CHROME_PATH="$(command -v chromium)"`. If the variable is not set, `render.js` stops before opening a browser and prints the variable's name.

`render.js` takes three options (`--help` prints them):

| Option | Default | Meaning |
| --- | --- | --- |
| `--frames a-b` | the whole clip | Frames `a` to `b − 1` at the render's frame rate. The sound is cut to the same span, so both start together. |
| `--fps n` | 30 (`FPS` in `timeline.js`) | The render's frame rate. Frame `n` shows time `n / fps`. |
| `--out file` | `out/clip.mp4` | The output path. An existing file is replaced. |

In the preview, click the page to start the sound; from then on the picture follows the audio clock. Space pauses and R restarts. Set `PORT` to use another port.

## Files

| File | Part | What it holds |
| --- | --- | --- |
| `index.html` | Stage | The canvas `#c`, `window.draw` with a four-sample half-frame shutter (motion blur), `window.ready`, and the preview loop. |
| `timeline.js` | Clock | Tempo, clip length, frame rate, conversions between beats, seconds, and frames, the event times that picture and sound share (`T.CUES`), and the seeded random stream `T.rng`. Picture and sound both read it. |
| `tokens.js` | Tokens | Palette, safe area, and type, defined once. |
| `scene.js` | Scene | `scene(ctx, t)`, the placeholder picture: dots, a circle, and four squares move on the beat, and one line of text rises into place at `T.CUES.text`. |
| `audio.js` | Sound | Writes `score.wav` (48 kHz, 16-bit stereo): a click on each beat, a seeded noise tick on each offbeat, and a chord at `T.CUES.text`. |
| `render.js` | Render | Headless Chrome through puppeteer-core, PNG frames piped to ffmpeg, H.264 and AAC muxed into an MP4. |
| `preview.js` | Preview | A local static server for the live preview. It serves byte ranges, so the browser can seek the sound. |
| `package.json` | Package | `npm run render`, `npm run preview`, and `npm run sound`. `package-lock.json` pins puppeteer-core and ffmpeg-static. |

`out/`, `score.wav`, and `node_modules/` are generated, and `.gitignore` leaves them out.

## The page contract

`render.js` and the page connect through three names. SLASH_MY uses the same names (`openPage` and `grabber` in its renderer, `window.draw` and `window.ready` in its engine, the preview loop in its page), so a scene can move between the starter and SLASH_MY.

- **`index.html?render`** puts the page in render mode: it draws nothing by itself and waits for `render.js`. The starter adds `&fps=N` for the render's frame rate. Without `?render`, the page previews itself with `requestAnimationFrame`.
- **`await window.ready`** resolves once the fonts are loaded and a frame can be drawn. Anything the first frame needs goes into this promise: font loads, decoded images, precomputed tables.
- **`window.draw(frame, samples)`** draws frame `frame`, at time `frame / fps`, into `canvas#c`. `samples` is the number of sub-frames averaged across a half-frame shutter: 4 when `render.js` calls it, 1 in the preview. `render.js` then reads the canvas with `toDataURL('image/png')`.

Time comes from the frame number, never from the wall clock. The preview uses real time only to pick which frame to draw. So a scene:

- computes everything from the `t` it is given, so any frame can be drawn on its own and in any order;
- takes every random choice from `T.rng(seed)`, never from `Math.random`, `Date` or `performance.now`;
- fills every pixel, because each sub-frame replaces or averages into the one before.

An effect that keeps state, such as a particle simulation or a trail that builds up, is recomputed from `t` or stepped in fixed steps from a seeded start state. It never keeps state from the previous call.

## Build on it

One workable order:

1. Set the tempo, length, and frame rate in `timeline.js`, and add your event times to `T.CUES` there, in beats.
2. Replace `scene.js`. As it grows, split it into more files and add their `<script>` tags to `index.html`.
3. Replace the parts of `audio.js`. Place each sound with `T.beatToSec` at the same `T.CUES` times the picture uses.
4. Keep the preview open while you write, and render a short `--frames` range to check picture and sound together.

## Reproducibility

`render.js` rasterizes the 2D canvas on the CPU (`--disable-gpu-rasterization`, `--disable-accelerated-2d-canvas`), because GPU rasterization can differ by a few code values from one run to the next.

**Checked:** on one Mac (macOS 26.7, Chrome 155, puppeteer-core 25.13.0, ffmpeg-static 5.3.0), two 3-second renders produced byte-identical MP4 files with identical decoded frame hashes; one frame drawn in two separate Chrome launches gave the same PNG bytes; and two runs of `audio.js` wrote byte-identical WAV files. The video and audio streams were both 3.000 s. On another machine, a different Chrome, a different ffmpeg, or different installed fonts can change the pixels; the font stack in `tokens.js`, for one, resolves differently on each OS.

To compare two renders frame by frame, hash the decoded frames of each:

```sh
node_modules/ffmpeg-static/ffmpeg -v error -i out/clip.mp4 -map 0:v -f framemd5 -
```

## Where to go next

The starter has one browser draw one frame at a time, and its score is neither loudness-normalized nor dithered. These pages take it further:

- [Production bootstrap](../knowledge/Production%20bootstrap.md) leads from this starter to a produced film.
- [Samples](../samples/README.md) collects working pieces of SLASH_MY to add as your film needs them, such as chunked parallel rendering, the loudness gate, and dither.
- [Deterministic rendering](../knowledge/Deterministic%20rendering.md), [Audiovisual synchronization](../knowledge/Audiovisual%20synchronization.md), [Capture and encoding](../knowledge/Capture%20and%20encoding.md), and [Mastering and delivery](../knowledge/Mastering%20and%20delivery.md) explain the choices behind it.
