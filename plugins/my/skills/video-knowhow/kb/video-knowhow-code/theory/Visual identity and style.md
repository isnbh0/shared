# Visual identity and style across scenes

A video's style is a set of related decisions the viewer meets again and again: palette, type, shape language, texture, lighting, motion, and sound. Consistency comes from how those decisions relate to each other. Applying the same effect everywhere does not produce it. Static design builds style from roles. A portable style keeps three things apart: structure (what a component does and what parts it has), variant axes (alternatives that mean something, such as hierarchy level or semantic context), and tokens (named values that move between tools). A color belongs in the system when it does a recurring job under representative conditions, meaning its neighbors, area, frequency, background, and state. Filling out a swatch scale or matching a mood label is not enough reason to add one. In code-authored video those roles also have to survive changes of scene, renderer, and time.

## Invariants and variation

An **invariant** is a recurring rule the viewer can learn: a character's silhouette, a warning color, the shape of a dialogue box, the timing of a menu cursor, or a title's alignment. **Variation** lets the sequence show different moods and events and still keep its identity. Too little variation can flatten dramatic differences; too many unrelated variations can make the piece feel assembled from separate demos. Where the balance sits is a design judgment, and you test it with a montage or a contact sheet of the scenes.

Style can be written as named roles instead of colors and sizes hard-coded throughout a program. The Design Tokens Community Group format describes typed tokens, and references between them, that can move between tools. In video a token may be static (`text.primary`) or the starting value of a role that changes over time (`accent.warning` during an encounter). A token system makes each choice traceable. It does not decide whether the palette or the set of motions you chose hangs together. [Design Tokens Format Module](https://www.w3.org/community/reports/design-tokens/CG-FINAL-format-20251028/)

## Style lives at more than one scale

At the large scale, style covers scene layout, pacing, and how much of the piece is quiet against how much is intense. At the middle scale it covers typography, sprites, UI, particles, and transitions. At the small scale it covers pixel edges, stroke widths, easing curves, and sound envelopes. A scene may pass at one scale and fail at another: the palette can be consistent while the sprites are drawn at mismatched scales, or matching sprites can sit inside transitions that move with a different character.

Pixel art shows this clearly. Nearest-neighbor scaling gives hard edges, but it does nothing to align silhouettes, palette roles, text treatment, and the scale of effects. MDN presents pixel scaling as a rendering method. [MDN: crisp pixel art](https://developer.mozilla.org/en-US/docs/Games/Techniques/Crisp_pixel_art_look) See [Pixel art and stylization](../knowledge/Pixel%20art%20and%20stylization.md) for the dimensions you control.

## Material and presentation are separate

An imported illustration, a generated sprite, a shader, a font, and a code-drawn interface can share one video. When you evaluate the method, it matters where each came from and how it was transformed: a convincing portrait may owe more to the source art than to a pixelation pass, and a convincing trailer rhythm may owe more to staging than to the art. Name which layer contributes which quality, so the style system does not turn into a vague claim that "code made everything."

A practical style check uses a contact sheet of the scenes, several motion clips, and the audio in context. Ask which invariants show in every scene, which variations tell the story, and which elements look as if they came from a different visual world. [Visual hierarchy and composition](../knowledge/Visual%20hierarchy%20and%20composition.md) covers controls within a frame; [Transitions and continuity](../knowledge/Transitions%20and%20continuity.md) covers style across scene boundaries.
