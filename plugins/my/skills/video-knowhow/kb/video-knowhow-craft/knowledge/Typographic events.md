# Execute a typographic event

A title event has a place to land, an entrance, an emphasis, a readable state, and an exit, and the craft is in how these relate. This worked account follows the AX DAY reconstruction's closing title as written in its source; it is a reading of the code, with no new playback or listening review.

## Worked event and source version

Snapshot: `e5ae340d` (the reconstruction's files are byte-identical at `32dec413`, inspected for the package on 2026-10-02) in John's workspace, which holds the reconstruction's visual source (`index.html`), timeline (`timeline.js`), and score (`audio.js`). The reconstruction is kept as a specimen, and the implementation facts below are read from that source.

The timeline runs at 120 BPM, so one beat is 0.5 seconds. The timings below are the settings this example uses.

### Layout before movement

`window.ready` waits for fonts before `buildParticles()`. `TITLE_FONT` is a 900-weight, 330 px sans face on a 1920×1080 canvas. The code measures `AX DAY`, centers its measured width, and derives `titleSplitX` from the measured `AX ` prefix. Both particle targets and solid letters use that geometry at `TITLE_Y = H / 2 - 40`.

If the target mask and the solid lettering used different metrics, the particles would seem to miss the title as they assemble. Changing the wording or the font means recomputing the target points, the width, the split, the underline, and where the supporting copy sits. Spacing in the layout is part of the component's geometry and is settled with it, before animation.

### Entrance emphasis and reading state

| Film beats and seconds | Source behavior | Relationship to inspect |
| --- | --- | --- |
| 22–31.75; 11–15.875 s | `drawParticles()` brings in an orbiting field, then moves particles toward sampled glyph targets from beat 29.5 with individual delays. | The dispersed material starts belonging to the future word before it becomes solid. |
| 31.75–32; 15.875–16 s | `scene()` returns after filling ink. The audio master gates the complete mix, including the reverb return, down over 5 ms at the start of the 0.125 s gap. | The intended pause interrupts the build. The visual post pass still adds grain; this source's gap is not mathematically pure black. |
| 32; 16 s | Particles burst and spring toward their targets. Camera shake begins at 28 px times an exponential decay; flash and shockwaves emphasize the drop. The score calls `kick(t, 1.2)`, a low impact, noise, and an opening filtered `supersaw` chord. | The impact marks arrival before the reading state is complete. Immediate peak brightness is not the moment to demand detailed reading. |
| 32.6–34.2; 16.3–17.1 s | `actReveal()` fades in solid type using `outCubic`; particle opacity thins over beats 33–36. The underline grows over 33.2–34.4. | The letter bodies take over while residual particles disappear. The scene calls `drawParticles()` before `actReveal()`, so the solid title is drawn over the particle layer despite the source comment saying “under.” |
| From 34 and 36; 17 and 18 s | `staggerText()` begins the English and Korean supporting lines, with different per-character offsets. The arpeggio begins at 34; corner information follows at 38. | The supporting information arrives after the main arrival. Its reading time starts once its own last character settles. |
| 39.5–41.5; 19.75–20.75 s | A gradient is painted through the title glyphs once. A chime starts at 39.5. | The sheen renews attention on an already readable title; the chime shares the sweep's start, which may or may not coincide with the sweep's visually brightest crossing. |
| 46–48; 23–24 s | `finish()` fades the picture to black with `inCubic`; the audio master applies a linear end fade. | The title exits as a held composition. The two fades share endpoints but follow different curves, which give different perceptual envelopes. |

The slow push on the title starts at beat 33 and reaches 5% enlargement by the end. It keeps the composition moving while the wording stays fixed. The main title is fully opaque from beat 34.2, but the card keeps gaining supporting information after that, so do not count all the remaining time as undisturbed reading time for every line.

### Compositing order changes the result

`window.draw(frame, samples = 4)` evaluates four scene times within a half-frame shutter. It combines the opaque samples with `globalAlpha = 1 / (i + 1)`, which gives each sample equal weight by incremental averaging. `finish()` then applies slice displacement and RGB split, vignette, grain that changes each frame, and the fade. So geometry and camera motion blur together, while grain is applied once per output frame and stays crisp over time. This Canvas path differs from the linear-light float accumulation in the later SLASH_MY source.

The drop glitch decays over beats 32–32.7, and solid type begins at 32.6, so most of the reading of the letters happens after the strongest displacement. If the glitch ran on through the supporting lines, the event would stop being an emphasized arrival and become a lasting obstacle to reading.

## Contrasting failures and alternatives

**Everything lands together**: subtitle, flash, ring, title, and credit compete on one frame. Separate discovery from explanation, and stagger by role instead of staggering every glyph out of habit. **Everything keeps settling**: an elastic title never holds still long enough to read. Shorten the motion tail or keep the elasticity on a decorative layer. **The event goes quiet too early**: a required title is visible, but it does not read strongly as the answer. Check its setup and scale before adding another impact.

For a technical explainer, a short mask reveal into a fixed phrase can suit better than particles and shockwaves. Keep the shared end geometry and the hold on the completed state, shrink the entrance, and put a cue only on the arrival that matters to the meaning. Animate the unit of text the audience reads: a word or phrase for a definition, single characters only for a short title. Time the stagger from the last element's completion.

For another interaction, the [SLASH_MY case](../cases/SLASH_MY.md) links `FINISH.sheen`, `SHEENS`, and `HEAD_RAMP`: near-white letters need highlight headroom before a sweep can be seen crossing their faces. Raising bloom alone can just enlarge their halo. That implementation is an example supported by the source.

**Evaluate**: play the event with its sound, then inspect the cue frame, the strongest distortion, the first complete phrase, the last supporting arrival, and the exit. Can a new viewer read the title and get its meaning without replaying? Does removing the sheen or delaying the subtitle make that easier? Review the encoded result at delivery size.

The reconstruction's sound analysis reports that John preferred the AX DAY reconstruction to A/B and offers candidate causes; [the comparison runs](../cases/Comparison%20runs.md) summarize its findings. In [D-007](../cases/Comparison%20runs.md), an onset change at the exact frame read as equivalent at playback speed, so precise timing supports what you mean without being what the viewer mainly perceives.

[Anticipation to title](../cases/Anticipation%20to%20title.md) · [Meaningful reveal](../patterns/Meaningful%20reveal.md) · [Sound production](Sound%20production.md) · [Home](../Home.md)
