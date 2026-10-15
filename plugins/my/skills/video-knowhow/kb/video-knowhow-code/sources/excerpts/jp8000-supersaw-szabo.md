# The Roland JP-8000 supersaw, measured (Szabo 2010)

- **Source:** Adam Szabo, *How to Emulate the Super Saw*, KTH Royal Institute of Technology bachelor's thesis, 2010.
- **URL:** https://www.nada.kth.se/utbildning/grukth/exjobb/rapportlistor/2010/rapporter10/szabo_adam_10131.pdf (archived: http://web.archive.org/web/20160310085410/http://www.nada.kth.se/utbildning/grukth/exjobb/rapportlistor/2010/rapporter10/szabo_adam_10131.pdf)
- **Checked:** 2026-10-14.

## The passages

**Table 1 (detune offsets at maximum detune), read against a 523.3572 Hz center:** "523.3572 / 523.3572 = 1" for the center voice, and the six side voices at ratios 0.88997686, 0.93711561, 0.98047644, 1.01991221, 1.06216538, 1.10745242 — i.e. offsets of −0.11002313, −0.06288439, −0.01952356, 0, +0.01991221, +0.06216538 and +0.10745242 of the center frequency. The spacing is uneven: about −201.8, −112.4, −34.1, 0, +34.1, +104.6 and +176.6 cents at full detune.

**On phases:** "The phases of the oscillators are strictly random, meaning the oscillators are free running."

**On the detune knob:** the JP-8000 maps its detune knob to the offset multiplier through an 11th-order polynomial in x = knob/127 (Szabo's Table 2 interpolates the curve).

**On spectrum shaping:** the JP-8000 applies a high-pass at each voice's fundamental that tracks pitch, and the voice mix — center level falling, side levels rising along a curve — makes center and sides equal at mix value 95 (0.75).

## Where it is relied on

[Sound sources and voices](../../knowledge/Sound%20sources%20and%20voices.md) compares SLASH_MY's supersaw with these measurements. Its `SS_DET` table equals Szabo's Table 1 exactly, and its phases are random per voice. The page gives the differences (a fixed 150 Hz high-pass and fixed 1/0.75 center-side weights) as SLASH_MY's own case values. The [Soundtrack code case](../../cases/Soundtrack%20code.md) makes the same comparison in detail, including the interpolated knob position for SLASH_MY's `det` 0.12 (knob ≈ 0.555, MIDI ≈ 70).
