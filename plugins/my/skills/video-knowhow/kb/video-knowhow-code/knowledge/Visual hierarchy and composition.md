# Visual hierarchy and composition

Code controls the layout of a rendered frame. [Attention and hierarchy](../theory/Attention%20and%20hierarchy.md) explains how size, contrast, motion, and other signals compete for the viewer's eye. [Visual identity and style](../theory/Visual%20identity%20and%20style.md) explains how layout and color choices recur across scenes.

## A frame has a reading order

A scene description can give each element a role: primary message, supporting evidence, context, decoration, or persistent interface. The roles then set defaults for size, contrast, and animation. IBM's layout guidance uses typographic contrast, position, and space to define a reading path. [IBM layout guidance](https://www.ibm.com/design/language/layout/tips-and-techniques/) ([excerpt](../sources/excerpts/ibm-layout-reading-path.md))

The scene data can also name a `focus` target for each interval. The renderer can then lower contrast or motion around that target, dim an area behind text, or keep a region empty for an entrance. To check the reading order that results, sample frames before, during, and after each change of focus.

## Structure: live area, alignment, and negative space

An internal grid gives every coordinate a common reference: the frame inset, columns, gutters, a baseline or spacing unit, and anchors. IBM documents a video use of its 2x Grid at 1920×1080, with an eight-column structure and 30-pixel increments. Those numbers belong to that design system and are not a standard for every video. What carries over is the practice: choose a coordinate structure and use it consistently enough that departures from it look intended. [IBM 2x Grid](https://www.ibm.com/design/language/2x-grid/)

Negative space separates groups and gives a focal point room. It can also hold motion that comes later: a character can enter the empty space, a title can expand into it, or particles can gather there. A densely filled frame leaves fewer of these options. In a code-authored sequence, you can represent the live area as regions with bounds and priorities, and then check subject and text bounds at several points in time for overlap, clipping at the edges, and shifting margins. IBM names white space and consistent alignment as tools for legibility and grouping. [IBM layout guidance](https://www.ibm.com/design/language/layout/tips-and-techniques/), [IBM typography basics](https://www.ibm.com/design/language/typography/type-basics/)

For a centered reveal, keep the main title and the subject on one shared axis. For an explanation beside a character, put the character and the text in separate regions and leave the text room to grow. IBM documents grids and asymmetry as ways to plan these layouts. [IBM layout guidance](https://www.ibm.com/design/language/layout/tips-and-techniques/)

## Color as a role system

A palette helps most when each color has a role: canvas, foreground text, secondary text, accent, warning, interactive selection, character identity, or transient effect. You can store those roles as named tokens, so that a scene's colors change together when a role changes. The Design Tokens Community Group specifies a format in which named tokens hold typed values and references, which makes a style system inspectable and reusable across renderers. [Design Tokens Format Module](https://www.w3.org/community/reports/design-tokens/CG-FINAL-format-20251028/)

Color can signal meaning, but when accurate recognition matters, show the meaning through shape, label, pattern, or position as well. W3C's color-use guidance is written for web content, yet its perceptual concern applies to a rendered video too: two otherwise identical choices told apart only by red and green are easy to confuse. For technical diagrams, IBM likewise calls for a legend and a second visual signal alongside color. [W3C: use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color), [IBM technical diagrams](https://www.ibm.com/design/language/infographics/technical-diagrams/design/)

For informational text, you can compute contrast from the actual foreground and background colors. WCAG 2.2 specifies 4.5:1 for ordinary text and 3:1 for large text on web pages. These are useful reference thresholds when you design video frames, but passing them does not guarantee readability after scaling, compression, motion, or viewing on a small screen. Check text over moving imagery against the whole range of backgrounds it crosses. [WCAG 2.2 contrast criterion](https://www.w3.org/TR/wcag/#contrast-minimum), [W3C contrast explanation](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum)

## Parameters code can expose

| Concern | Controllable parameters | Useful inspection |
| --- | --- | --- |
| Frame structure | Insets, columns, gutters, anchor points, scene regions | Overlay bounds and grid on sampled frames; look for clipping and accidental misalignment. |
| Emphasis | Subject scale, luminance, saturation, blur, opacity, motion amplitude | At normal viewing size, identify what draws attention first and whether it is the intended subject. |
| Layering | Z order, overlap, vignette, masks, depth or parallax | Check whether foreground effects hide text or character details. |
| Color roles | Named palette tokens, role assignments, contrast pairs | Generate a palette sheet and calculate contrast for expected adjacent pairs. |
| Dynamic layout | Region ownership over time, entrance paths, caption reservations | Inspect entry, midpoint, and exit frames, including overlap during transitions. |

Use these controls to render alternatives and compare them. A numeric salience score could help flag extreme cases, but the reading order, which depends on meaning, still needs a person to watch the actual sequence.

## Questions a render can answer

- Which object is meant to be the focal point at this moment, and which object actually catches the eye first?
- Can the main message be read at the delivery size while the background moves?
- Do margins, baselines, and groupings hold together through the animation, or only in the still frame?
- Does a color's meaning survive in grayscale, or when the color names are removed?
- Does the negative space do a job, such as focus, timing, or room for an upcoming entrance?
