# Case: stage intro built from code

The [starter](../starter/README.md)'s scaffold comes from this earlier production: one beat clock, headless Chrome, and ffmpeg, which the starter reduces to a small skeleton. The recorded source was later recovered and rerendered as the AX DAY reconstruction, a specimen kept for study in John's workspace and summarized here.

**Result.** The chatlog records a completed 24-second, 1920×1080, 60 fps H.264/AAC intro, at the time named `ax-day/intro/ax_day_intro.mp4`. The output ffmpeg printed on completion confirms the file and its duration, and the assistant reports reviewing a contact sheet from the finished video. The audio was generated and measured, but the assistant could not listen to it. [C-493](../sources/Chatlog%20index.md#c-493), [C-499](../sources/Chatlog%20index.md#c-499), [C-513](../sources/Chatlog%20index.md#c-513)

**New reconstruction.** The raw chatlog file also contains the complete initial source files and the later edits. They were recovered and rerendered, and the new render's 1,440 frames and audio decode cleanly. The reconstruction's reproduction notes, contact sheet, and implementation stay in John's workspace. The original MP4 is unavailable, so the new render is checked for internal consistency and is described here from the reconstruction's written notes.

## What the piece does

John's brief was an intro for the moment before a stage event begins. [C-245](../sources/Chatlog%20index.md#c-245) The finished sequence runs a typed terminal prompt, a four-part Korean claim, a fast tunnel of keywords, a progress and countdown build, 0.125 seconds of silence, and then a flash and a particle reveal of “AX DAY.” It closes with a subtitle, the organization name, and a fade. The assistant chose those exact words and the event date during the session, and the chatlog does not show them being approved as official event copy. [C-313](../sources/Chatlog%20index.md#c-313), [C-513](../sources/Chatlog%20index.md#c-513)

## Mechanism

The shared `timeline.js` sets 120 BPM, 48 beats, 24 seconds, 60 fps, and 1920×1080 output. It places visual and audio events in beats: Enter at beat 8, slow words at beats 8–14, fast words at 16–23, the countdown at 26/28/30, silence from 31.75 to 32, then the reveal. Seeded random timing gives the prompt a human typing rhythm, and every rerender repeats it exactly. [C-313](../sources/Chatlog%20index.md#c-313)

An HTML/Canvas scene draws each frame. A Puppeteer renderer opens headless Chrome, calls `window.draw(frame)`, captures each frame as a PNG, and streams the PNGs into ffmpeg, which encodes H.264 and muxes in the separately synthesized WAV as AAC. The renderer also has a still-export mode for chosen frame numbers. The whole piece is a program that specifies every frame exactly: text, particles, and timing are source data you can edit and render again. [C-329](../sources/Chatlog%20index.md#c-329), [C-346](../sources/Chatlog%20index.md#c-346)

`audio.js` allocates 44.1 kHz stereo buffers and writes PCM WAV. Its score uses an Am–F–C–G chord loop, a low drone, synthetic typing and Enter sounds, a pitched kick, filtered-noise hats and snare, offbeat bass, detuned saw chords, a noise-and-sweep riser, and an impact and arpeggio after the drop. A ducking function triggered by the kick lowers the melodic layers. Separate reverb sends, soft clipping, fades, and peak normalization finish the mix. A hard gate around the drop makes the 0.125-second gap. All of this is read from the code. [C-313](../sources/Chatlog%20index.md#c-313), [C-424](../sources/Chatlog%20index.md#c-424), [C-444](../sources/Chatlog%20index.md#c-444)

The reconstruction's audio code, with line references and values, is set beside SLASH_MY's in the [Soundtrack code case](Soundtrack%20code.md).

## Verification and limits of evidence

- **Reported (chatlog):** stills were rendered and read, a visual correction was made, the WAV generator completed, beat-window level measurements were printed, and the MP4 render completed with a 24-second duration. [C-347](../sources/Chatlog%20index.md#c-347), [C-398](../sources/Chatlog%20index.md#c-398), [C-413](../sources/Chatlog%20index.md#c-413), [C-444](../sources/Chatlog%20index.md#c-444), [C-459](../sources/Chatlog%20index.md#c-459), [C-493](../sources/Chatlog%20index.md#c-493)
- **Reported (chatlog):** the assistant reports that ten moments in the finished video were checked by eye, and the soundtrack was checked by measured levels because the assistant could not hear it. Its last message gives the scene synopsis and warns that the event copy was provisional. [C-513](../sources/Chatlog%20index.md#c-513)
- **Interpretation:** a timeline indexed by beats lets the score, the cut points, and the visual events share one set of coordinates. Reviewing stills is useful before paying for a full render. The chatlog supports frame accuracy and ease of editing. [C-313](../sources/Chatlog%20index.md#c-313), [C-346](../sources/Chatlog%20index.md#c-346), [C-398](../sources/Chatlog%20index.md#c-398), [C-424](../sources/Chatlog%20index.md#c-424)

This example suits work whose main material is text, geometry, particles, timing, and synthesized effects. Its reported file size was large, 126 MB, and came with the grain-heavy encoding used here. [C-513](../sources/Chatlog%20index.md#c-513)
