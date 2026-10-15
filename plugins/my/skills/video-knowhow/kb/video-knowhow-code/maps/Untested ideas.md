# Untested ideas

Small picture, timing, sound, and capture operations can serve a wider range of work when the output of one becomes the input of another. The combinations below are hypotheses. Each starts from something observed and names the next result that would make the idea more concrete. The chatlog also raised several of these [open directions](../sources/Chatlog%20index.md#c-1463).

## One world, a trailer and a playable scene

The [FOXTALE case](../cases/FOXTALE.md) records a timed game-style trailer and a browser playback page. It does not record combat that a player controls. A next test could put the same characters, battle layout, dialogue, and sound cues into a playable encounter, then render a trailer from that scene. The result would show whether one scene model can support both a player's pacing and an edited story turn.

## Stage visuals that respond to the event

The [Stage intro case](../cases/Stage%20intro.md) records an offline sequence built around 120 BPM, and the [procedural 3D example](../recipes/Procedural%203D%20scene.md) shows a live browser scene. A next test could feed a live BPM, a show trigger, or a data value into visuals built from the same [time and sound operations](../Operations.md#make-and-relate-sound). The result would need to show how the graphics cope when triggers change, and whether they read on the actual stage display.

## Sound techniques that still need a test

Each audio technique page ends with options that have not been built or heard:

- [Sound sources and voices](../knowledge/Sound%20sources%20and%20voices.md#untested-ideas): sample-layered drum transients and recorded one-shots, a longer line for the formant vocal, a supersaw high-pass that tracks pitch, and string damping that compensates for pitch.
- [Dynamics and spectral carving](../knowledge/Dynamics%20and%20spectral%20carving.md#untested-ideas): transient shaping on the drum bus, a listening check of the drop's strike carves for pumping, and release times derived from the tempo.
- [Space and delay](../knowledge/Space%20and%20delay.md#untested-ideas): convolution reverb with recorded impulse responses, delay settings per place, mid/side treatment of reverb returns, and a mono-sum check of the opposite-panned doubles.
- [Groove and feel](../knowledge/Groove%20and%20feel.md#untested-ideas): correlated drift in place of independent jitter, and parameter automation every few bars so loops never repeat exactly.
- [Mastering and delivery](../knowledge/Mastering%20and%20delivery.md#untested-ideas): TPDF dither at the AX DAY reconstruction's WAV writer, an independent loudness and true-peak check for the AX DAY reconstruction, a matched-loudness reference A/B, and phone and laptop translation, including bass harmonics.
- [Music under voice-over](../knowledge/Music%20under%20voice-over.md#untested-ideas): spoken lines driving the score, the level difference checked in the build, detected versus scheduled band ducking, and a listening check with older viewers and the picture.

[Two soundtracks](../../video-knowhow-craft/cases/Two%20soundtracks.md) sets out the next result these share: whether a listener can tell, at matched loudness, that one choice was reverted.

## A video shaped by its source records

The [event opener](../recipes/Event%20announcement%20opener.md) accepts named fields, and the [animated chart](../recipes/Animated%20data%20comparison.md) maps data records to bars and labels. A series built from checked event or data records could combine the two. The test is whether long names, other languages, unusual values, and different aspect ratios stay clear across a whole batch. [Iteration and parameterization](../knowledge/Iteration%20and%20parameterization.md) explains what can vary and what has to be inspected again.

## Prepared art inside authored motion

The inspected [Maintra video](../sources/Social%20examples.md#supplied-screenshots-in-a-moving-product-film-maintra) places supplied app screens inside moving phone views. The creator reports a code-based process, but no matching project source was linked. A new piece could combine prepared illustration, recorded footage, or generated imagery with type, camera motion, and score authored in code. The test is whether the parts share one visual world and whether each part's origin and permissions stay clear. See [assets and provenance](../knowledge/Assets%20and%20provenance.md).

## Shader shots that expose different limits

The chatlog proposed a chrome logo, rain on glass, and a fractal zoom as separate [shader tests](../sources/Chatlog%20index.md#c-863). It did not record that any were finished. A chrome logo would test moving reflections and the environment they reflect. Rain on glass would test droplet motion, refraction, and the background behind it. A fractal zoom would test sustained detail, camera motion, and render cost. Compare each rendered shot with the look you intended; [capability boundaries](../knowledge/Capability%20boundaries.md) helps you find whether source detail, rules, or review is missing.
