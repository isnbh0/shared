# Audiovisual synchronization

Sound and picture are in sync when the viewer takes a sound and its visual event to be one moment. Code-authored video keeps time in several coordinates at once. Giving each event one shared time is more reliable than working out one medium's timing from the other's callbacks.

## The clocks

| Clock | Coordinate | What it controls |
| --- | --- | --- |
| Narrative timeline | Seconds or beats from video start | Intended cue and scene positions |
| Video frame timeline | Integer frame index at a chosen fps | Which image is rendered |
| Audio sample timeline | Integer sample index at a chosen sample rate | Which waveform sample is rendered |
| Browser display clock | `requestAnimationFrame` timestamp | When a preview is repainted |
| Browser audio clock | `AudioContext.currentTime` | When live sound is scheduled |

At 60 fps one frame lasts about 16.67 ms, and at 48 kHz one audio sample lasts about 20.8 μs. People do not judge sync to the sample, but the smaller unit lets you place a sound's onset more finely than the picture's frame boundaries allow. A cue at time `t` falls near video frame `round(t × fps)` and audio sample `round(t × sampleRate)`. Whether to round, floor, or snap the cue to a frame start is a production choice. Write the choice down so that edits do not drift.

[Remotion's fundamentals](https://www.remotion.dev/docs/the-fundamentals) document the fixed-frame video model, and the [Web Audio specification](https://www.w3.org/TR/webaudio/) has `OfflineAudioContext` take its output length in audio sample frames. The conversion above follows from those two definitions.

## Use one event list

A shared list holds events such as `reveal at 4.0 s`, `impact at 4.5 s`, or `scene change at beat 16`. The visual renderer reads it to animate or switch frames, and the audio renderer reads it to schedule sounds. Convert a musical grid to seconds with `secondsPerBeat = 60 / bpm`, and keep continuous time for events that should fall between beats. The shared list is an architectural inference from two designs: the [Web Audio sequencer tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Advanced_techniques) schedules notes at explicit times and keeps a queue for the visuals, and [Remotion](https://www.remotion.dev/docs/the-fundamentals) renders whichever frame is requested. With one list, a timing change is made in one place, where a reviewer can see it.

A sound's **trigger time** and its **audible onset** are different moments. A sample may open with silence, a swell may have a slow attack, and a cue with reverb may peak after it starts. A visual transition may likewise begin before the frame where the impact becomes recognizable. Align the sync landmarks a person perceives, and do not assume that the start of each file is the event. This is a practical design inference, and it asserts no universal offset.

## Live browser preview

`requestAnimationFrame()` runs around display repaints, may vary with the refresh rate, and can pause in hidden tabs. Compute visual progress from its timestamps instead of counting callbacks ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame)). Audio is scheduled on `AudioContext.currentTime`. A look-ahead scheduler queues sounds a little before they are due, so variation in JavaScript timers does not shift each onset directly ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Advanced_techniques)).

The live audio clock and the visual performance clock are separate. `AudioContext.getOutputTimestamp()` returns an estimate of which `performance.now()` time matches an audio-context time, for a sample reaching the output device ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/AudioContext/getOutputTimestamp)). That estimate can support a visualizer or live sync, though display presentation and device latency still have to be checked in practice. `requestAnimationFrame` gives no sample-accurate audio trigger of its own.

## Fixed export

For export, derive both the frames and the audio from the same event times, and declare the fps, sample rate, duration, and media offsets. `OfflineAudioContext` renders a buffer without depending on device playback timing ([W3C](https://www.w3.org/TR/webaudio/)). The audio buffer may need to run past the last visual action so that tails survive, and the encoded video's total duration should be set on purpose. For repeatable results, use stable random seeds for both generated sound and time-derived animation.

Inspect the **muxed, encoded file**. Encoding, trimming, and combining the streams produce the audio and frames the viewer actually gets. Scrub exact cuts for one-frame visual gaps, and listen around impact points, scene joins, and the ending. Waveform peaks can point to possible timing errors, but you still have to hear and watch the result together. Do not declare sync from timestamps in the source code alone.

## Common drift mechanisms

- Counting render callbacks instead of using elapsed time ties preview speed to the refresh rate or to dropped callbacks. [MDN warns about this](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame).
- Scheduling each note when a JavaScript timeout fires lets timer jitter shift audio events. The [Web Audio look-ahead pattern](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Advanced_techniques) schedules against the audio clock instead.
- Changing fps, sample rate, clip start, or trim offset without recomputing the mappings can move an event against the exported picture.
- Rendering sound with unseeded randomness, or visuals with accumulated mutable state, can make a later export differ from the reviewed version.

A shared value ties parts together, so a change to one part can move parts that look unrelated. When a sound takes its pitch from a shape, or a motion takes its timing from the score, a fix made for one reason changes everything that reads from what was fixed. After a change, recheck every part that reads from it, not just the part you meant to fix. **Reported (SLASH_MY):** a picture fix changed the length of one shape to make its flash smaller (commit `027f2127`). A sound took its pitch from that length, so its pitch jumped from 389 to 1829 Hz. A review across both crafts caught it, asked for the old sound back, and kept the smaller flash.

Sync is also a design decision. A sound before a reveal may build anticipation, a sound at its visible peak may punctuate it, and a sound after it may signal consequence. Choose that relationship when you design the cue. The clocks and the export should then preserve it.

## Sound and picture on one beat grid

Both audio case productions put sound and picture on one narrative timeline counted in beats at 120 BPM, so `secondsPerBeat = 0.5`. The AX DAY reconstruction is a rerender of Stage intro rebuilt from the chatlog and kept as a specimen; its sound was checked for presence and decoding. The [source ledger](../sources/Audio%20sources.md) records these as common practice with no authoritative source found: syncing sound events to the picture's beat grid, silence before a drop, pre-roll whooshes and risers, layered impacts, and delay throws. The case values are starting points for adaptation. The [two-soundtrack case](../../video-knowhow-craft/cases/Two%20soundtracks.md) compares the rest of the two scores. The sources cited below were inspected in John's workspace: the reconstruction's `timeline.js`, `index.html`, and `audio.js` at `e5ae340d`, and SLASH_MY's `timeline.js`, `audio.js`, `sfx.js`, `score-events.json`, `engine.js`, `finish.js`, `render.js`, and `scenes/reveal.js` at `fd543f2a`.

**Shared constants (AX DAY reconstruction).** **Checked:** `timeline.js` holds the beat constants (words, countdown, `GAP_START` 31.75, `DROP` 32, `FADE` 46). `index.html` loads it with a script tag (L13), and `audio.js` requires it (L5). Each side computes its own event times from those constants, and an event derived on one side is not shared with the other. The picture's beat glow, `exp(−5·frac(b))` from beat 8 to the drop, lines up with the kicks only because both happen to sit on whole beats, and nothing checks that they agree. The end fade shares its endpoints but not its curve: it is linear in the audio and `inCubic` in the picture. The slow-word whoosh starts 0.18 s before each word beat, and the word's letters start 0.18 beat after it. The same number appears in seconds in one file and in beats in the other.

**Exported events (SLASH_MY).** **Checked:** `audio.js` writes `score-events.json` along with `score.wav` (`ev`, L2487-2498). The file records what was played, in beats: 135 kicks, including the writing section's swung kicks such as 80.7909; slams, strikes, hook notes, vocal onsets, and delay throws; and the computed decay time of each room and of the vocal plate. `render.js` inlines the file into the page (L170), and `engine.js` loads it (`useScore`, L248). `agree()` (L240) stops the page if its fallback kick table differs from the score's kicks by 0.1 beat or more, or if its echo beats differ from the score's throws. The picture then follows the score. The world's pulse reads the latest kick (`lastKick`, L258). An impact's flash decays at a rate scaled by the hall's decay time over its room's (`finish.js` `flashRate`, L826). Light in the reveal falls with the decay times of the vocal plate and the rooms (`scenes/reveal.js` `breathLifts`, L559, and `lightOf`). These decay times are formula values computed from the reverb's comb lengths and feedback (`rt60()`, `audio.js` L740), not measurements of the render. Some values flow the other way, from picture to score: the throw beats come from `engine.js` (`ECHO.at`, L115), and `sfx.js` reads the scene exits and the nav scene's inhale timing. **Interpretation:** exporting what was played captures values nobody would type into a picture table, such as a swung kick, and a mismatch stops the page where it would otherwise drift unnoticed. **Reported:** the picture-to-score direction shows in a revision. Reordering the strikes so the sung word landed on its beat meant regenerating `score-events.json`, because the score reads its triggers from the events the picture exports (commit `67d1245`). The inhale and rush triggers entered the score the same way (`f970b549`, `b5a2b9c1`).

**Sounds that lead the picture.** Each cue's trigger time is worked back from the sync landmark it has to meet.

| Cue | Sound landmark | Picture landmark | Mechanism |
| --- | --- | --- | --- |
| AX DAY reconstruction slow-word whoosh | Starts 0.18 s before the word beat; its sine envelope peaks about 0.095 s after it (`audio.js` L124-134) | The wipe starts on the beat; letters start 0.09 s after it (`index.html` L187, L197) | Hand-set in two files |
| AX DAY reconstruction riser | Beat 24 to 31.75, amplitude rising as `p²` (L142-151) | Progress bar over the same span (`index.html` L238) | Shared constants |
| SLASH_MY seam whoosh | Starts at the exit's start and peaks on its fastest frame, `play(bt(pk) − pre)` (`sfx.js` `whoosh`, L946-957) | The scene's exit (`WHOOSH_EXIT`, L117) | Picture-owned beats read by the score |
| SLASH_MY inhale | Crests 8 ms before the burst at beat 104 and closes there (`inhaleSwell`, L1544-1554) | The burst (`findable.js` `INHALE`, `tractatus.js` `BURST`) | Picture-owned beats read by the score |
| SLASH_MY strike carve | The bed's carve opens 0.3 beat before each of the drop's strokes (`STRIKE_ROOM.pre`, `audio.js` L851; [strike carves](Dynamics%20and%20spectral%20carving.md#strike-carves)) | The stroke | Played by the score and exported as `strikes` (`strikeAt`, L880) |

**Reported:** according to commit `02802d8d`, the strike carve's look-ahead moved beat 114's 2–12 kHz rise over the 60 ms before it from −2.4 to +3.5 dB. **Interpretation:** a lead of a chosen length prepares attention for the visible event, and a carve that opens early has cleared the band before the transient arrives.

**Gap blanking.** **Checked:** both productions blank sound and picture between the same two constants. The AX DAY reconstruction's master ramps linearly to zero over 5 ms from `GAP_START`, holds zero to `DROP`, and has no ramp back in, despite its "(5ms ramps)" comment (`audio.js` L203-207). The gate mutes the output, reverb return included, but the reverb keeps running underneath, so the build's tail resumes after the gap ([comb and all-pass reverb](Space%20and%20delay.md#comb-and-all-pass-reverb)). Its picture's `scene()` returns during the gap (`index.html` L359), but the grain pass still draws, so the gap is not pure black. SLASH_MY applies 5 ms half-cosine ramps on both sides after the limiter (`audio.js` L2473-2481; [shaped fades and the gap](Mastering%20and%20delivery.md#shaped-fades-the-pre-drop-gap-and-the-end-release)), and it clears its delay and reverb buffers at the gap's first sample (`resets: [gapI]`, L2135-2178). `finish.js` passes the gap through as true black (L923-925). **Untested idea:** the AX DAY reconstruction's unramped return at 16.000 s may click; no one has auditioned it.

**Inspect when it fails.** Check the muxed file in delivered time. SLASH_MY's delivered file opens with a 5 s warning card (`render.js` L14-16), so its drop at film time 56 s plays at 61 s. If the picture's pulse and the kicks disagree, check that `score-events.json` was regenerated along with `score.wav`; `agree()` reports only disagreements of 0.1 beat or more. If a flash or lift outlasts its room's reverb, remember that the exported decay time models only the low end. A damping change alters how fast the real top decays and leaves the exported figure unchanged. In the AX DAY reconstruction, a beat constant changed on one side moves only that side, and no check reports it.
