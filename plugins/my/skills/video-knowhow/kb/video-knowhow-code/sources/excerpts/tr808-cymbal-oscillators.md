# TR-808 cymbal circuit — the six shared oscillators (Werner, Abel & Smith 2014)

- **Source:** K. Werner, J. S. Abel, & J. O. Smith, "The TR-808 Cymbal: a Physically-Informed, Circuit-Bendable, Digital Model," ICMC/SMC 2014.
- **URL:** https://speech.di.uoa.gr/ICMC-SMC-2014/images/VOL_2/1453.pdf
- **Checked:** 2026-10-14.

## The passage

"The six oscillators have nominal frequencies (or ranges) of 205.3, 369.6, 304.4, 522.7, 359.4–1149.9, and 254.3–627.2 Hz. Oscillators #5–6 have internal trimpots (TM2 and TM1) in series with their resistor, for factory tuning to specific frequencies (800 and 540 Hz, respectively)." The paper models the six square-ish waves (about a 48% duty cycle, not exactly 50%) feeding two band-pass filters centered near 3.4 and 7.1 kHz; the same six-oscillator family is shared by the cowbell, cymbal, open hi-hat, and closed hi-hat, all on one HD14584 hex Schmitt-trigger chip. Units before serial #000300 used different component values for oscillators 5 and 6.

## Where it is relied on

[Sound sources and voices](../../knowledge/Sound%20sources%20and%20voices.md) identifies the six factory frequencies as the origin of SLASH_MY's `HAT_F` base list (205.3, 304.4, 369.6, 522.7, 540, 800 Hz). It gives SLASH_MY's differences as SLASH_MY's own case values: ×1.9 for hats, a further ×2.3 for crash and cymbal, one SVF instead of two band-passes, and 50% duty. The [Soundtrack code case](../../cases/Soundtrack%20code.md) makes the same comparison in its hats-and-cymbals section.
