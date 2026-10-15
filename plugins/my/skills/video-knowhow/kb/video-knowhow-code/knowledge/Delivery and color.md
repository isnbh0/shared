# Delivery and color

The delivered file is an encoded copy of the rendered frames, and what the viewer sees and hears depends on the codec, pixel format, color conversion, audio format, and player support. When a piece may need more than one delivery format, keep a high-quality render or the source frames.

## Describe a delivery profile precisely

A file extension alone says too little. Record these properties for each deliverable:

| Property | Decision it captures |
| --- | --- |
| Container | How video, audio, timestamps, and metadata are packaged, such as MP4 or WebM. |
| Video codec and profile | How pictures are compressed and what a decoder must support. |
| Audio codec | How sound is compressed; its support is separate from video support. |
| Width, height, and display aspect | The encoded picture and its intended display shape. |
| Frame rate and timestamp mode | Constant or variable presentation cadence. |
| Pixel format and bit depth | Pixel channels, chroma resolution, and precision. |
| Color primaries, transfer, matrix, and range | How stored values should become displayed colors. |
| Alpha policy | Whether transparency is preserved, composited, or discarded. |

For broad browser playback, MP4 with H.264/AVC video and AAC audio is a common delivery choice, and WebM with AV1 and Opus is another where the target players support it. Test either profile on those players: a container can hold several codecs, support varies by browser and operating system, and not every device accepts every encoding option. [MDN: web video codec guide](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Video_codecs), [MDN: video processing concepts](https://developer.mozilla.org/en-US/docs/Web/API/WebCodecs_API/Video_processing_concepts), [Playwright: browser and platform differences](https://playwright.dev/docs/browsers)

## Follow the pixels through color conversion

A browser canvas may render in sRGB or Display P3. In the WebCodecs model, color description has four separate fields: **primaries** define the gamut, **transfer** maps coded values to light, **matrix** relates RGB and luma/chroma values, and **range** says whether code values span the full or limited range. Its definitions of sRGB and Rec. 709 differ in transfer, matrix, and range even though both use BT.709 primaries. [MDN: canvas context color space](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/getContext), [W3C WebCodecs: VideoColorSpace](https://www.w3.org/TR/webcodecs/)

When the renderer's RGB pixels become a delivery codec's YUV samples, the conversion and the signaled metadata must agree. If the pixels were converted under the wrong assumptions, changing the color tag alone cannot repair them. FFmpeg exposes color primaries, transfer, matrix, and range as separate codec parameters, and its `colorspace` filter converts among them once the input properties are known. [FFmpeg codec options](https://ffmpeg.org/ffmpeg-codecs.html), [FFmpeg colorspace filter](https://ffmpeg.org/ffmpeg-filters.html)

Chroma subsampling matters in graphic work. `yuv420p` stores one pair of chroma samples for each 2×2 group of luma samples, which saves data and works on common delivery paths, but saturated one-pixel edges, tiny colored type, and pixel art can change after encoding. Check those details in decoded frames at the intended size. When other exports may be needed later, keep a source render with higher chroma precision. [FFmpeg pixel formats](https://ffmpeg.org/ffmpeg-codecs.html), [MDN: codec guide and chroma formats](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Video_codecs)

Decide explicitly what happens to alpha. A transparent source frame may become opaque if the target encoder or container does not preserve alpha. WebCodecs' encoder option discards alpha by default. If the deliverable does not need transparency, composite against the intended background before judging the result. [W3C WebCodecs: encoder alpha option](https://www.w3.org/TR/webcodecs/)

## Quality and playback

The resolution and bitrate a piece needs depend on its content. Grain, motion, fine linework, and gradients may need more bits than large flat shapes at the same dimensions. A larger file does not prove the picture looks better, any more than a technically valid file proves the type is readable or the motion clean. Inspect the **decoded export** on the expected screen or projection setup, including any scaling performed by the player. [MDN: factors affecting encoded video](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Video_codecs)

Audio has its own sample rate, channel layout, codec, loudness, and endpoint. A video can have a valid video stream while the sound is missing, cut short, silent, or poorly balanced. See [Audiovisual synchronization](Audiovisual%20synchronization.md) and [Verification](Verification.md).
