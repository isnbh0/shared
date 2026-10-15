# Verification

Verification asks whether the delivered file contains the intended sequence, at the intended timing and quality, in a form that actually plays. It covers the file itself, the timeline, the rendered content, the sound, and the target player, and each needs its own check. A valid MP4 header shows that the file opens. Only the rendered frames show whether the title is legible, and only playback shows whether the drop lands on the beat.

## Evidence by question

| Question | Useful evidence | Typical fault exposed |
| --- | --- | --- |
| Does the file decode and contain the expected tracks? | Full decode plus stream metadata from `ffprobe`. | Truncated file, missing audio, unexpected dimensions or codecs. |
| Does the timeline contain the expected frames? | Count decoded frames and inspect presentation timestamps, especially first and last. | Missing, duplicate, irregular, or shifted frames. |
| Do transitions and important images look right? | Contact sheet and full playback of the decoded export. | Clipping, stale canvas state, unreadable type, broken compositing, accidental flashes. |
| Is the sound right? | Listen through the export; use loudness, peak, and silence measurements for diagnosis. | Muted track, clipping, abrupt endpoint, imbalance, beat drift. |
| Does the destination play it correctly? | Open the delivered file in the actual target player or a close equivalent. | Unsupported codec/profile, unexpected color or scale, playback failure. |

`ffprobe` can report format and stream properties, count frames, and write per-frame data as JSON. For a concrete export:

```sh
ffprobe -v error -of json \
  -show_entries format=duration:stream=index,codec_type,codec_name,width,height,pix_fmt,avg_frame_rate,sample_rate,channels,color_space,color_primaries,color_transfer,color_range \
  output.mp4

ffprobe -v error -select_streams v:0 -count_frames \
  -show_entries stream=nb_read_frames -of default=noprint_wrappers=1 output.mp4
```

These commands inspect the *decoded file*. They do not report the frame count the renderer planned. In a fixed-rate sequence of `N` frames at `F` frames per second, frame `i` belongs at `i/F`: the first frame is at zero, and the last starts at `(N−1)/F`. The container duration can include the display duration of the last frame and the end of the audio, so compare the actual timestamps and track lengths, and do not expect every reported duration field to agree. FFmpeg documents the rational time base it uses for timestamps, and how constant-rate conversion duplicates and drops frames. [ffprobe documentation](https://ffmpeg.org/ffprobe.html), [FFmpeg CLI](https://ffmpeg.org/ffmpeg.html), [FFmpeg codec time base](https://ffmpeg.org/ffmpeg-codecs.html)

## Review the picture at the times that matter

A contact sheet should show each scene's first frame, a representative middle frame, and its last frame, plus both sides of each cut, sync point, and text change, and any unusually fast motion. It catches broad errors of composition and sequence quickly. Rhythm, flicker, and visual continuity still need full-speed playback, because a still image cannot show them. Inspect the decoded export, because compression and color conversion can change fine detail. For small text or pixel art, inspect at the actual display scale as well as at full resolution.

FFmpeg's `blackdetect` and `freezedetect` filters find long black or unchanging stretches, and `silencedetect` finds silent stretches of audio. What they report are candidates for review, since an intentional fade, hold, or pause can produce the same signal. FFmpeg's PSNR, SSIM, and VMAF filters compare an output with a **reference**. They help judge encoding changes when content and timing are aligned, and they cannot score whether a newly designed scene communicates well. [FFmpeg filter reference](https://ffmpeg.org/ffmpeg-filters.html), [Netflix VMAF tool](https://github.com/Netflix/vmaf/blob/master/libvmaf/tools/README.md)

## Keep the render reproducible enough to debug

For each delivered file, keep the source scene, the audio assets or the code that generates them, the fonts, the render dimensions, the frame rate, the seed values, and the versions of the renderer and encoder that produced it. Hashes of the source inputs and of the decoded frames can tell a changed input apart from a changed encoding environment, and FFmpeg's `framehash` muxer produces per-frame hashes. An exact screenshot comparison also depends on the browser, OS, fonts, hardware, and settings, so compare against a reference screenshot made in the same environment. [FFmpeg hash muxers](https://ffmpeg.org/ffmpeg-all.html), [Playwright visual comparisons](https://playwright.dev/docs/test-snapshots)

A waveform or a loudness report finds silence and peaks. Listening tells you whether the effects, the music, the transitions, and the ending feel right. A claim that the sound was verified should say which of these checks actually happened. See [Deterministic rendering](Deterministic%20rendering.md) and [Audiovisual synchronization](Audiovisual%20synchronization.md).

## The review tools get verified too

**Reported (SLASH_MY):** the SLASH_MY production's session records (held in John's workspace) log two defects in the review setup itself, and each came to light through the verdicts of its own check. The frame-range tool rounded each frame time on its own, so float noise rounded some frames up and others down. The result was duplicated and skipped frames, and an audio slice cut late. One shared helper fixed it everywhere: it snaps each span outward to whole frames, and every tool reads that one rule (commit `44565e33`). In the second defect, a review clip assembled by hand played out of alignment with its reference audio, and the misalignment looked like a sync defect in the film. The flipbook tool then gained automatic alignment of any full-length audio against any clip, using an offset derived from the beat, so an error in the viewing setup no longer passes for a film defect (commit `4928cc9e`). The round discipline adds a locality check in the same spirit: each fix is checked against its neighbors. The recorded rule is that a film is done when a full review finds no new defect and no fix creates a seam problem within two beats of where it was made ([convergence](../../video-knowhow-craft/knowledge/Convergence.md)).
