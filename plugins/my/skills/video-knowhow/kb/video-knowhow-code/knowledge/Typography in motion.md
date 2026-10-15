# Typography in motion

Code controls how text is laid out and animated. [Moving-text legibility](../theory/Moving-text%20legibility.md) explains why complete, stable text needs time on screen. [Temporal visual rhythm](../theory/Temporal%20visual%20rhythm.md) explains how that reading time fits among other events.

## Distinguish text's job

Record the text's role in the scene data: title, label, speech caption, quoted line, game dialogue, or graphic object. The role sets starting values for size, width, placement, animation, and time on screen. A title can have an animated entrance and a stable hold. A speech caption has to follow the audio and stay clear of other on-screen text.

In code, one `Text` component can still take a semantic `role` and apply size, width, placement, motion, and timing defaults for that role. Keep the defaults editable, because language, reading speed, delivery size, and scene complexity vary. Netflix's timed-text requirements show that subtitles need their own constraints: usually one line, at most two lines, controlled line breaks, and positions that avoid on-screen text. These are Netflix's delivery rules for subtitles and do not govern all graphic text. [Netflix general timed-text requirements](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements)

## Text has geometry

The same number of characters can take up different widths. A renderer needs the chosen font's measured glyph advances, line height, weight, tracking, and language-specific shaping. Lay text out from its measured bounds; do not estimate width from the character count. Where a line breaks is a design choice, because it changes both the shape of the text and the rhythm of reading it. IBM's type guidance covers alignment and line lengths, and Netflix specifically warns against breaking a grammatical unit, such as a name or a verb phrase, across subtitle lines. [IBM typography basics](https://www.ibm.com/design/language/typography/type-basics/), [Netflix general timed-text requirements](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements)

With Korean, other CJK text, emoji, and combined Unicode characters, a typewriter effect that reveals one code unit at a time can split what the viewer sees as one character. If the effect is meant to reveal text character by character, reveal grapheme clusters or another language-aware unit. This is a technical condition that follows from the Unicode definition of extended grapheme clusters. [Unicode Standard Annex #29: text segmentation](https://www.unicode.org/reports/tr29/)

## Reading time

A text event has at least four parts in time: the entrance, the reading time, a possible emphasis or change, and the exit. Reading time starts when the text is complete and stable enough to read, which can be later than the moment the element first appears. A long animation can use up most of the event's nominal duration while showing only fragments of the text. So the measure to check is how long each unit of text stays visible and stable, viewed alongside the shot and audio timing.

Netflix's subtitle guidelines time subtitles to the audio and the shot, call for a minimum subtitle event of about 0.8 seconds in their 24 fps context, and encourage giving longer text more time. They also require watching the full edit to catch awkward timing. The numbers belong to that production context, but the variables carry over: when the text starts relative to the speech, how long the reading time lasts, and whether a cut interrupts reading. [Netflix subtitle timing guidelines](https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines)

Kinetic typography makes the text itself move on purpose. Adobe describes text properties you can control, including placement, opacity, color, and speed curves. Those controls can support what a word means, a musical accent, or a change of speaker. They can also make the text harder to read when position, scale, rotation, and color all change at once. One way to handle this is to decide which phase of the event gets the expressive motion and which phase lets the viewer read. [Adobe text animation overview](https://www.adobe.com/uk/products/aftereffects/text-animation.html)

## Contrast and background interaction

Text over a flat field can use a known color pair. Text over a moving shader, a particle scene, or a character shot meets contrast that keeps changing. WCAG's web criteria give measurable reference ratios, but rendered text also suffers from compression, antialiasing, thin strokes, small delivery size, and motion. A scene can reserve a calmer region, add a box or an outline, dim the background locally, or hold back a busy visual until the text has been read. Compare those options in the delivered output. [WCAG 2.2 contrast criterion](https://www.w3.org/TR/wcag/#contrast-minimum), [W3C contrast explanation](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum)

When the text is a direct transcription or translation, its accessibility and timing serve one more purpose. W3C treats captions as text alternatives for speech and relevant sound, and a decorative text animation alone may not convey that information. This matters if the piece is published as accessible media. [W3C captions overview](https://www.w3.org/WAI/media/av/captions/)

## Parameters code can expose

| Concern | Controllable parameters | Inspection |
| --- | --- | --- |
| Typography | Family, weight, size, leading, tracking, line width, alignment | Render specimen frames at delivery resolution and view at likely display sizes. |
| Segmentation | Line breaks, grapheme or word reveal units, punctuation pauses | Check awkward breaks and broken Unicode clusters. |
| Timing | In, readable start, hold, out, relation to voice and cuts | Calculate stable exposure; watch with audio for sync and interruption. |
| Animation | Property animated, easing, travel distance, stagger, overshoot | Decide whether words remain readable during the intended reading interval. |
| Contrast | Text color, outline or box, local background dimming | Sample difficult frames, especially behind moving highlights. |
| Collision | Text bounds, subtitle region, other titles and UI | Overlay bounds for the entire event, including transitions. |

## Questions a render can answer

- At what exact moment is the whole phrase readable, and how long does it stay readable?
- Does the line break keep the phrase's meaning and give the text a shape you chose?
- Is the font still clear in the delivered frame, beyond a large editor preview?
- Does the text collide with captions, characters, or interface elements as they animate?
- With the sound muted, does the text still give the necessary information? If the sound conveys information the text lacks, are captions available where needed?
