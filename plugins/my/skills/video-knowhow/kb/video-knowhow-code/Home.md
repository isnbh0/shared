# Video know-how: code

This is the code shelf of the video know-how package: production engineering, reusable operations, and the original case records that the craft shelf links to. Its sibling, [Video know-how: craft](../video-knowhow-craft/Home.md), is the craft shelf, with guidance on components, scenes, sequences, and the direction of a whole piece. Both folders share the `video-knowhow` prefix.

The package relies on two things: practice documented outside the package, and what was learned from SLASH_MY, the skills hype film, the one production John endorses. The chatlog productions and the comparison runs are records of earlier attempts, since superseded, and are kept as evidence and as specimens. [Content lineage](sources/Content%20lineage.md) classifies every page.

Code can place text over a supplied photograph, draw a changing diagram, move a camera through a 3D scene, synthesize a score, and render the result as video. The same small operations can serve an explanation, a stage reveal, or a story turn.

## Start a production

The [starter](starter/README.md) is a runnable skeleton that renders a clip with picture and sound. [Production bootstrap](knowledge/Production%20bootstrap.md) takes it from installation through a first deterministic render to the working pieces a longer film needs. The [samples](samples/README.md) are those pieces, excerpted from the SLASH_MY production.

The [showcase](showcase/README.md) is a runnable 26-second trailer for this package, built in the starter's shape with the samples and the techniques these pages describe. [Watch it on YouTube](https://youtu.be/02laS8NbEbA).

## See the range

- **A countdown gives way to silence and a particle title.** The [Stage intro case](cases/Stage%20intro.md) records a 24-second render with typed text, a keyword tunnel, a countdown, 0.125 seconds of silence, and an “AX DAY” reveal. The original MP4 is unavailable. The AX DAY reconstruction, a local rerender from the recorded source code, is kept as a specimen and described in that case.
- **A fight turns into mercy.** The [FOXTALE case](cases/FOXTALE.md) records a game-style trailer that moves from exploration to battle and then to a mercy choice, with a score that changes at each act. The chatlog documents the render. Its media is not preserved, and the assistant could not audition its music.
- **App screenshots become a moving product film.** In the [31.8-second Maintra video](https://v.redd.it/zxy5l50ex9rh1/CMAF_1080.mp4?source=fallback), inspected frames show app screens inside changing phone views, with short white and gold titles. The creator reports that code made the film, but linked no matching project source. See the [inspection and claim record](sources/Social%20examples.md#supplied-screenshots-in-a-moving-product-film-maintra).
- **A circle explains a sine wave.** A [published Manim video](https://docs.manim.community/en/stable/SineCurveUnitCircle-1.mp4) moves a dot around a circle while a guide traces its height into a growing curve. The [diagram explainer](recipes/Diagram%20explainer.md) links the rendered video and its source code.

## Why this is useful now

Graphics, animation, sound synthesis, and encoding have a long [production lineage](sources/Production%20lineage.md). In the chatlog, the assistant wrote scene code, ran renders, inspected frames, and revised the result; the [stage intro](cases/Stage%20intro.md) and [FOXTALE](cases/FOXTALE.md) cases trace that work. Source art, direction, and review still shape how good the finished piece is. The [capabilities over features](https://wiki.g15e.com/pages/Capabilities%20over%20features.md) principle gives the package its structure: small operations combine into many results. The [recipes](maps/Recipes.md) show combinations that can supply ingredients for a new premise.

## For a specific production question

- **To change what the viewer expects**: [temporal visual rhythm](theory/Temporal%20visual%20rhythm.md), [visual identity](theory/Visual%20identity%20and%20style.md), and [sound as scene structure](maps/Compose%20sound%20and%20synchronization.md) tie a build, pause, reveal, or reversal to the story. The [stage intro](cases/Stage%20intro.md) and [FOXTALE](cases/FOXTALE.md) show two reported combinations.
- **For text that has to appear on time and stay readable**: [moving-text legibility](theory/Moving-text%20legibility.md), [text and layout patterns](Operations.md#describe-and-organize-the-sources), [time patterns](Operations.md#make-change-legible-in-time), and [typography in motion](knowledge/Typography%20in%20motion.md). The [event opener](recipes/Event%20announcement%20opener.md) is one combination you can inspect.
- **For a diagram or chart that changes**: [grouping and continuity](theory/Grouping%20and%20continuity.md), [visual mapping patterns](Operations.md#describe-and-organize-the-sources), [transition patterns](Operations.md#make-change-legible-in-time), and the [diagram](recipes/Diagram%20explainer.md) or [data comparison](recipes/Animated%20data%20comparison.md) examples.
- **For a distinct scene style**: [visual identity and style](theory/Visual%20identity%20and%20style.md), [source and variation patterns](Operations.md#describe-and-organize-the-sources), [pixel art and stylization](knowledge/Pixel%20art%20and%20stylization.md), or [shaders and 3D](knowledge/Shaders%20and%203D.md). The [procedural 3D scene](recipes/Procedural%203D%20scene.md) shows one working result.
- **For a score that sounds produced**: [sound sources and voices](knowledge/Sound%20sources%20and%20voices.md), [dynamics and spectral carving](knowledge/Dynamics%20and%20spectral%20carving.md), [space and delay](knowledge/Space%20and%20delay.md), [groove and feel](knowledge/Groove%20and%20feel.md), and [mastering and delivery](knowledge/Mastering%20and%20delivery.md). [Two soundtracks](../video-knowhow-craft/cases/Two%20soundtracks.md) compares two scores built this way, and the [Soundtrack code case](cases/Soundtrack%20code.md) holds the line references and parameter values behind those pages.
- **For narration over music**: [music under voice-over](knowledge/Music%20under%20voice-over.md) sets how far below the voice the bed sits, how to duck and carve for speech, and what older and hearing-impaired listeners need. [Accessibility and perception](knowledge/Accessibility%20and%20perception.md#audio-content-and-alternatives) covers captions and transcripts.
- **For a dependable delivery file**: [sampling and comparison patterns](Operations.md#turn-the-system-into-evidence), [capture and encoding](knowledge/Capture%20and%20encoding.md), [delivery and color](knowledge/Delivery%20and%20color.md), and [verification](knowledge/Verification.md).

## Browse the parts

- [Theory](maps/Theory.md): how attention, grouping, visual rhythm, legibility, and style affect what a viewer understands.
- [Operations](Operations.md): small visual, temporal, sonic, and capture operations that combine.
- [Techniques and approaches](maps/Techniques%20and%20approaches.md): ways to implement and inspect those operations in different media.
- [Recipes](maps/Recipes.md): combinations with examples you can inspect, plus cases from the chatlog, marked separately.

## Judge scope and explore

- [What can code specify?](maps/What%20can%20code%20specify.md): decide which parts are rules, which are assets, and which are a mix.
- [Untested ideas](maps/Untested%20ideas.md): combinations that still need a test.
- [Capabilities and boundaries](maps/Capabilities%20and%20boundaries.md): where a representation helps and where it needs support.

The [Glossary](Glossary.md) defines recurring terms. The [chatlog index](sources/Chatlog%20index.md) locates passages in the conversation; focused pages link directly to their other sources. [Editorial notes](Editorial%20notes.md) explains how claims are labeled and sourced.
