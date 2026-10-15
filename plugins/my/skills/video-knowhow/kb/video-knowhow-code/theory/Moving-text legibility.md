# Moving-text legibility

Text in video has limited reading time. A viewer has to find it, see whole glyphs and words, and understand it before it changes or leaves. Static design uses typographic differences to show what role a piece of text plays. A small set of choices in size, weight, value, case, position, and spacing, tried out across representative screens, lets readers recognize relationships that recur, such as section and item or label and value. Distinctive letterforms cost space, attention, and reading speed, so they go where the role can afford them: short display text takes stronger formal signals than body copy or dense data. Video adds one more problem. The role and the form have to stay readable through time, motion, and changing backgrounds.

## Reading time is shorter than screen time

A title may be on screen for three seconds but spend one second entering and one second leaving, which leaves a reading time closer to one second. A typewriter effect reveals words one after another, so if the whole phrase exits at once, the last words are seen for less time than the first. A timing model can therefore separate `in`, `fully_visible`, and `out`, and count only the fully visible part as reading time.

How long text needs depends on how much of it there is, its language, its sentence structure, the font metrics, what else competes for the eye, and the size it will be seen at. Netflix's subtitle rules are one example of professional constraints: they control line count and line breaks, time subtitles close to speech and shot changes, and require review in full playback. Their numbers govern Netflix timed text. For other kinds of video, treat them as evidence from a related context. [Netflix general requirements](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements), [Netflix subtitle timing](https://partnerhelp.netflixstudios.com/hc/en-us/articles/360051554394-Timed-Text-Style-Guide-Subtitle-Timing-Guidelines)

## Motion changes the text's effective form

Animation can stress a word, mark who is speaking, or make an idea feel physical. It can also alter the letterforms during the very interval when the viewer needs to read them. Check translation, scaling, rotation, blur, masks, and opacity changes against the moments when you expect the viewer to read. Adobe describes these as controllable dimensions of kinetic typography. What matters is how their combined motion affects recognition in the delivered sequence. [Adobe text animation overview](https://www.adobe.com/uk/products/aftereffects/text-animation.html)

A moving background changes contrast and adds competition for the eye. WCAG's contrast ratios are formal web criteria and useful measurements for planned color pairs, but on their own they do not show that compressed moving text is readable at a given viewing size. [WCAG contrast criterion](https://www.w3.org/TR/wcag/#contrast-minimum)

## What code makes inspectable

From a render you can inspect measured text bounds, reveal units that respect graphemes, how long each piece of text stays fully visible, contrast against sampled backgrounds, and collisions with other objects. Extended grapheme clusters approximate the characters a user perceives, so revealing by cluster avoids showing half of a combined character or emoji. [Unicode text segmentation](https://www.unicode.org/reports/tr29/)

See [Typography in motion](../knowledge/Typography%20in%20motion.md) for typography controls, caption treatment, and render questions. A paused frame checks shape and contrast; playback at normal speed checks whether there is enough time to read.
