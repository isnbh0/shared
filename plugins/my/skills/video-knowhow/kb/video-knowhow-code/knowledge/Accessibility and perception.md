# Accessibility and perception

People watch a code-authored video at playback speed, often on a screen and speakers unlike the ones it was made on. Accessibility checks therefore belong in the visual and audio design and in the review of the delivered encoded file. A browser preview can adapt to the viewer's settings; an exported file plays the same for everyone.

## Readable information

Text needs enough size, contrast, space, and stable screen time to be read. A label over a changing background can become unreadable for part of its appearance even when one still frame looks clear. [W3C's audio/video production guidance](https://www.w3.org/WAI/media/av/av-content/) specifically calls out overlay-text font, size, and contrast. [WCAG 2.1](https://www.w3.org/TR/WCAG21/) gives Level AA contrast minimums of 4.5:1 for normal text and 3:1 for large text, with defined exceptions. The ratios are a useful reference for text in a rendered video, though whether WCAG conformance applies to a particular standalone video depends on where and how it is delivered.

Motion can also compete with reading: a brief title may need a longer hold even when its font is large. Check the text at the real output size and playback speed, with sample frames across each moving background. Calming the motion while text is on screen, or putting a backing panel behind the text, can work better than heavier type alone.

## Flash and motion sensitivity

The [W3C media guide](https://www.w3.org/WAI/media/av/av-content/) advises avoiding more than three flashes in any one-second period. The underlying [WCAG 2.2 criterion](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold) also defines general-flash and red-flash thresholds. The three-flash rule is the simple way to comply and covers only part of the criterion. Review rapid cuts, strobe-like accents, repeated loops, and saturated-red changes in the exported result. A transition can produce a flash even when no layer was built as one.

Large pans, zooms, scaling, parallax, and sustained oscillation can cause discomfort or distraction for some viewers. [MDN's reduced-motion guidance](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion) calls out large scaling and panning as possible vestibular triggers. [Apple's motion guidance](https://developer.apple.com/design/human-interface-guidelines/motion) advises purposeful motion and alternatives for important signals. Keep a stable frame of reference where you can, and move things only when the movement helps tell the scene.

An interactive web preview can query `prefers-reduced-motion` and remove, reduce, or replace nonessential animation ([MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion)). [WCAG's animation-from-interactions guidance](https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions) addresses motion triggered by user interaction on web pages. An exported video file cannot respond to that setting after encoding. SLASH_MY's delivered file, for example, plays its flashing reveal for every viewer and opens with a 5 s photosensitivity warning card, described below. Where accessible distribution calls for more, provide player controls or an alternative presentation.

## Flash warnings that follow the flash check

Besides saying that a film flashes, a warning card can say where the flashing is strongest. That second claim describes the picture, so it holds only while a flash check of the delivered file agrees with it.

SLASH_MY is cited here at snapshot `d0ed8468`. It runs at 120 BPM, so a beat is 0.5 s of film. Its delivered file opens with a 5 s warning card (`timeline.js` L23), so delivered time is film time plus 5 s.

**Checked (SLASH_MY):** the production's flash check (`qa/flash.py`) approximates WCAG 2.3.1 on the encoded file by counting flashes as areas of cells that reverse together (snapshot `1fdc6435`). It decodes each frame at 960×540, converts sRGB to linear light, and averages relative luminance (Y = 0.2126 R + 0.7152 G + 0.0722 B) over a 96×54 grid of cells about 0.1° wide. A zigzag with hysteresis splits each cell's signal into monotone legs; a general leg changes Y by at least 0.1 and has its darker end below 0.80, and a red leg changes the red value, 320 × (R − G − B) on saturated red (R/(R+G+B) ≥ 0.8), by more than 20. A cell is moving at a frame pair when it advances inside a qualifying leg by more than 4% of the threshold in that pair. Every pair where more than 25% of the field is moving starts an area, and that area's next transition registers at the first later pair where its own cells, advancing on their next legs, again cover more than 25% of the field. Each transition of an area is its own cells reversing together, two transitions in a row are one flash, and a 1 s window (60 frames) fails above three flashes. Cells that brighten while others darken add up, so an inverting checkerboard counts. In a page scroll, each cell reverses only when the next text edge reaches it, so an area's cells fall out of step within a transition or two and the scroll produces no flash. The whole frame stands in for WCAG's 10° field; `--field 0.5` or `--field 0.333` is stricter, for a large screen. Its self-test generates synthetic clips — full-frame and partial-area strobes, saturated red, a slow sine, scrolling bars, scrolling text, an inverting checkerboard, plus lossless cuts of the film's own scroll and reveal — and checks their verdicts. The tool calls itself a QA proxy, not a certified analyzer such as Harding FPA or PEAT. It is not part of the qa suite's full run, and the film's brief calls it advisory (`BRIEF.md` L65).

**Reported (SLASH_MY):** on the delivered file rendered from `d0ed8468`, the current meter passes: general flash reads at most 2 flashes (4 transitions) in any 1 s window, and red flash reads none (`qa/out/20261014-151147-flash-skill-hype/report.md`). Its worst windows:

| Window from beat | Section | Flashes in 1 s | Transitions, share of field | Film time | Delivered time |
| --- | --- | --- | --- | --- | --- |
| 103.60 | build, spex | 2 | ↑55% ↓34% ↑35% ↓28% | 51.80 s | 56.80 s |
| 111.60 | reveal, the drop | 2 | ↑68% ↓49% ↑49% ↓25% | 55.80 s | 60.80 s |
| 119.03 | reveal | 1.5 | ↓91% ↑56% ↓26% | 59.52 s | 64.52 s |

Writing's page scroll reads 0.5 flashes at its worst and passes, because the meter counts areas of cells reversing together and a scroll's cells fall out of step.

**Reported (SLASH_MY):** in a cross-check, an IRIS photosensitivity analyzer, built from Electronic Arts' published source (github.com/electronicarts/IRIS) and run on the same file and on synthetic controls, agrees with the meter on the film. It records 0 transitions in the scroll's windows, places transitions in the reveal where the meter does, and scores the whole film PassWithWarning. On the controls — full-frame and partial-area black/white strobes at 2 and 5 Hz, saturated red, a 4 Hz sine, slow fades — the two count the same flashes. They part where their tests differ: IRIS also runs spatial-pattern and stricter small-area tests the meter lacks, so it fails some fine-pattern and small-box controls the meter passes, and on a 42%-area checkerboard the meter fails where IRIS's transition count alone would pass. Agreement with an analyzer of this class on the film's scroll and reveal supports using the meter as the source of a card claim. The divergences on synthetic patterns are one reason the meter stays a QA proxy.

**Checked (SLASH_MY):** the card's text is in `copy.js` (L35–36):

```js
warning: ['PHOTOSENSITIVITY WARNING', 'This film contains flashing lights, strobe effects and moving patterns.',
  'Strongest in the final {s} seconds.'],
```

`drawCard` (`engine.js` L1386) replaces `{s}` with the film's seconds from the reveal's drop (beat 112, `timeline.js` L128) to the end (L1389). That span is film 56–68 s, delivered 61–73 s, so the card reads "Strongest in the final 12 seconds." The timeline computes the number. No code chooses the reveal as the place where flashing is strongest. The meter's output is what supports that choice.

**Interpretation (SLASH_MY):** the claim holds for intensity, not as a strict count of windows. The film's intense flashing is the reveal: the largest flash areas (68–91% of the field), the largest swings (median ΔY 0.45–0.52), and most of the film's transitions, all delivered 60.8–65.1 s. That sits inside the span the card names, except that the drop's first transitions land about 0.2 s before the span opens. One window elsewhere ties the count: build's 2-flash window at delivered 56.8 s, outside the span, at less than half the area and swing. The line therefore tells a viewer where the flashing is most intense. Build's tie also argues for generating card copy from the meter output, or for leaving timing claims out of the copy, so the text cannot drift from the picture.

**Interpretation:** when a warning names a time or place, take it from the latest flash check of the delivered file, and rerun the check after every picture change. Generate the card copy from the meter output, or keep it free of timing claims. SLASH_MY's card is partway there: the timeline computes its 12 seconds, but the choice of the reveal is supported by the meter's output, not generated from it. A warning informs the viewer and leaves a failing window failing, since the criterion makes no exception for warnings. A certified analyzer that ranks the windows differently would challenge the meter as the source of the claim.

When it fails, inspect:

- The card against the latest report. Every time or place the card names should match the report's worst windows. The report's `t` column is delivered time; its beats exclude the card.
- The frame mean across a failing window. Light changing over a large area moves the mean. A scroll keeps it nearly flat.
- The transition list. One area reversing with a steady, substantial field share is flashing; a share that shrinks toward the 25% threshold as cells fall out of step is detail moving, not light changing.
- The frames themselves, at delivery size, through the window. Look for a scroll, pan or texture moving across high-contrast detail.
- The field. The whole-frame default is lenient for a screen that fills more than 10° of view. Rerun with `--field 0.5` before calling a stage or cinema version a pass.
- The red test. The meter computes WCAG 2.0's red value, not WCAG 2.2's chromaticity test.

**Source status: supported:** [WCAG 2.2 SC 2.3.1](https://www.w3.org/TR/WCAG22/#three-flashes-or-below-threshold) (Level A; [excerpt](../sources/excerpts/wcag-231-flash-thresholds.md)): "Web pages do not contain anything that flashes more than three times in any one second period, or the flash is below the general flash and red flash thresholds." A [flash](https://www.w3.org/TR/WCAG22/#dfn-flashes) is "a pair of opposing changes in relative luminance that can cause seizures in some people if it is large enough and in the right frequency range". The [thresholds](https://www.w3.org/TR/WCAG22/#dfn-general-flash-and-red-flash-thresholds) are met where "there are no more than three general flashes and / or no more than three red flashes within any one-second period; or the combined area of flashes occurring concurrently occupies no more than a total of .006 steradians within any 10 degree visual field on the screen (25% of any 10 degree visual field on the screen) at typical viewing distance". A general flash is "a pair of opposing changes in relative luminance of 10% or more of the maximum relative luminance (1.0) where the relative luminance of the darker image is below 0.80". "A transition is the change in relative luminance (or relative luminance/color for red flashing) between adjacent peaks and valleys in a plot of relative luminance (or relative luminance/color for red flashing) measurement against time. A flash consists of two opposing transitions."

**Source status: supported:** the meter's red test matches [WCAG 2.0's](https://www.w3.org/TR/WCAG20/#general-thresholddef): "R/(R+ G + B) >= 0.8, and the change in the value of (R-G-B)x320 is > 20 (negative values of (R-G-B)x320 are set to zero) for both transitions". WCAG 2.2 gives a newer working definition, in which "the difference between states is more than 0.2 (unitless) in the CIE 1976 UCS chromaticity diagram".

**Source status: supported:** [Understanding 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold): "The combined area of flashes occurring concurrently and contiguously means the total area that is actually flashing at the same time. It is calculated by adding up the contiguous area that is flashing simultaneously within any 10 degree angle of view." "Content should be analyzed at the largest scale at which a user may view the content … with a video that may play in an area of a web page and also at full screen, the video should be analyzed for risks at full screen." Flashing "cannot be allowed even for a second or it could cause a seizure. And turning the flash off is also not an option since the seizure could occur faster than most users could turn it off."

## Audio content and alternatives

Speech, lyrics, and sound cues can hold information the viewer needs. [W3C WAI's media guidance](https://www.w3.org/WAI/media/av/) distinguishes:

- **Captions**: timed text for speech and meaningful non-speech audio.
- **Transcript**: text for the audio content; a descriptive transcript also includes meaningful visual information.
- **Audio description**: spoken description of important visual content that the main audio does not convey.

Each serves a different access need: a title card visible on screen but never spoken may require description or a descriptive transcript. A procedural alert sound that signals success or failure may need a caption if its meaning is not otherwise available. [WAI explains when visual description is needed](https://www.w3.org/WAI/media/av/description/), and the [WCAG explanation of prerecorded captions](https://www.w3.org/WAI/WCAG21/Understanding/captions-prerecorded) specifies the relevant synchronized-media criterion. Requirements depend on how and where the video is published, and the aim is that important information does not depend on one sense alone.

## Review the delivered experience

Inspect the encoded video at its expected viewing size and speed. Read every displayed phrase, watch transitions and any loop points for rapid flashes, and listen to narration with music and effects in place. Check that captions stay readable over the moving image and stay in time with the sound they represent. Technical metrics support this review, but they cannot establish that a viewer has enough time to understand a scene.

See [Time and motion](Time%20and%20motion.md) for timing decisions and [Audio synthesis](Audio%20synthesis.md) for mix and loudness concepts.
