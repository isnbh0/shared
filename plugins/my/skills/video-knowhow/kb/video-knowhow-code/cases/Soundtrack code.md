# Case: soundtrack code in SLASH_MY and the AX DAY reconstruction

**Result.** This case holds the code behind the audio technique pages: where in the source each technique is, its parameter tables, its note and onset counts, and the measurements its commits report. The technique pages explain how each technique works and give its case values. It covers two soundtracks: SLASH_MY, which John endorses and whose code was inspected in John's workspace, and the AX DAY reconstruction, a rebuild of [Stage intro](Stage%20intro.md) from its chatlog, rerendered as a specimen. The original Stage intro source is unavailable. John preferred SLASH_MY over the AX DAY reconstruction as a whole film, so the values here are case values, and each "why it works" is on the technique pages, labeled as an interpretation.

## Snapshots and reading the code

SLASH_MY is cited at `fd543f2a`. Its WAV writers and the 16-bit encoder input are cited at `f7f9d199`, the next commit, which changed only dithering. The loudness and true-peak readings in the audio run notes (`audio-notes.md`), section "Measured" (L32), are cited at `ec61dcd9`, where the line names its meters. The AX DAY reconstruction is cited at `e5ae340d`. Line numbers refer to those commits. The snapshots are in John's workspace, where the full source was inspected. One mix fix changed between the picture and audio snapshots. SLASH_MY's picture snapshot `32dec413` still has the whole-mix form of the beat-72 clip step. Commit `edd3024a`, which comes before this page's audio snapshot, replaced it with the band-only dip. Each page's values match the snapshot it names. A SLASH_MY line number with no file named is in `audio.js`.

The SLASH_MY files read at `fd543f2a`: `audio.js` (the score, the mastering, the loudness trim), `sfx.js` (impacts, risers, whooshes), `timeline.js` (the beat clock and the seeded stream), `engine.js` (the picture, and the score-event consumer), `score-events.json` (the score's record of what it played), `render.js` (encoding, the loudness gate, the 16-bit dithered cut), `finish.js` (the WebGL2 post pass), the qa suite (the delivered-file checks), and the audio run notes (the measured-values log). The WAV writers and the 16-bit cut are read at `f7f9d199`. The AX DAY reconstruction files read at `e5ae340d`: `audio.js`, `timeline.js`, `index.html` (the picture), and `render.js`.

Both scores run at 120 BPM, so a beat is 500 ms and a sixteenth 125 ms. SLASH_MY's beats: intro 0–16, brand 16–24, exec 24–56, design 56–76, writing 76–96, nav 96–104, build 104–112, reveal from 112. The reveal opens with the film's one silence (111.75–112) and the drop at 112, then the wall at 116, the breath at 119, the second drop at 120, the lock at 124 and the outro from 128. The AX DAY reconstruction's drop is at beat 32.

Evidence labels follow the code shelf's [Editorial notes](../Editorial%20notes.md#reading-a-claim). Here a [Checked](../Glossary.md#checked) claim was read in the code at the snapshot cited, and a [Reported](../Glossary.md#reported) claim is a measurement stated in a commit message, cited by hash, or in the "Measured" section of SLASH_MY's audio run notes. That section gives the command as `uv run qa/qa.py audio score.wav`, with the mux made by `render.js --audio-test`. Decibel figures marked "computed here" are arithmetic on the code's formulas, not measurements of the render.

Meters disagree in the last digits, so each loudness and true-peak figure names its meter. qa audio (`qa/audio_qa.py`) and `render.js` read the summary of ffmpeg's `ebur128=peak=true`, which prints one decimal. qa polish (`qa/polish.py` L109–118) estimates true peak by oversampling 4× with scipy's `resample_poly`. SLASH_MY's tools do not include pyloudnorm, but the integrated loudness of `score.wav` that commit `f7f9d199` reports (−14.063 LUFS) is a pyloudnorm reading.

## Sound sources and voices

Technique page: [sound sources and voices](../knowledge/Sound%20sources%20and%20voices.md).

### PolyBLEP saw

**Checked (SLASH_MY):** `audio.js` `blep()` L52–56 and `class Saw` L57–60. The phase advances by `dt = f/SR`. `tick()` returns `2·ph − 1 − blep(ph, dt)`, where `blep` applies a quadratic correction to the sample before and the sample after the wrap. Each `Saw` takes its starting phase from the `rPh` stream (seed 303, L31) unless the caller passes one. The code's comment calls it "bright without the MIDI-ish alias fizz". `sfx.js` receives the same `Saw` through its context (L146) for its risers, drop stab and swells.

In the code: in SLASH_MY, every saw in `audio.js` (supersaw, lead, pad, bass, pluck body, drone, vocal source) and in `sfx.js`. The AX DAY reconstruction has no PolyBLEP; its saws are naive `2·frac(ph + f·u) − 1` (supersaw L103–115, bass L93–100).

Pitch-modulated voices such as the lead and the vocal pass a new `f` every tick, so `dt` follows the instantaneous frequency.

### Supersaw

**Checked (SLASH_MY):** `audio.js` `supersaw()` L403–429, table `SS_DET` L399, double settings `DBL` L402.

| Part | SLASH_MY value |
| --- | --- |
| Voices | 7 per note, `f·(1 + SS_DET[k]·det)`, `det` 0.12 → about ±4, ±13, ±22–23 cents |
| `SS_DET` | `[−0.11002313, −0.06288439, −0.01952356, 0, 0.01991221, 0.06216538, 0.10745242]` (outer steps wider than inner) |
| Phases | Random per voice from `rPh` (`new Saw(ph())`) |
| Drift | ±0.25 % (about ±4.3 cents) sine per voice at 0.07–0.27 Hz, random phase |
| Level | Center voice 1, side voices 0.75, sum × 1.2/√n |
| Stereo | Voice k at `(k−3)/3·width`, width 0.85, equal-power |
| Filter | Stereo SVF low-pass, `fc = cut 1800 + env 2500·e^(−12u) + open·smooth(u/openT)`, Q 0.9 |
| High-pass | Fixed `hp` 150 Hz (two-pole SVF in `put()`), not pitch-tracked; the outro passes 60 |
| Duck | 0.5 by default |
| Mud cut | Optional bell at 400 Hz, Q 0.55, used on the reveal's stabs |
| Double | `dbl` gain, 12 ms late, +7 cents, detune × 1.4, pan mirrored, dry, phases from its own stream `rDbl` (seed 505) |

The double's comment says its phases come "from their own stream, so adding one moves no other part's": turning it on does not re-roll the random draws of anything rendered after it. The exec section's stabs use `dbl` 0.35 except slot 3, and alternate sides via `stabPan` (L1059–1060, L897).

**Checked (AX DAY reconstruction):** `audio.js` `supersaw()` L103–115. Seven naive saws per note at `f·(1 + d·0.0035)`, `d` = −3…3, a linear spread of about ±6, ±12 and ±18 cents. Random phases come from the single `rnd` stream. A one-pole low-pass runs at `cutoff + open·min(1, u/dur)`. There is no high-pass, no drift and no double. The voices sum to one mono signal placed at the event's pan, so there is no voice-by-voice stereo spread. The supersaw is ducked under the kick. The chatlog's own phrase for the original, quoted in the reconstruction's sound analysis, is "seven slightly detuned saw voices *per note*".

**Reported:** commit `8a6b436f` gave the stabs of spex (exec's first skill) "width .9 with a light detuned double (own phase stream) and a short offset on the other side" in the same change as other width moves, and reports "spex corr .98 -> .69". The correlation drop belongs to the combined change, not to the double alone.

**Comparison with Szabo's JP-8000 measurements** ([Szabo 2010](http://web.archive.org/web/20160310085410/http://www.nada.kth.se/utbildning/grukth/exjobb/rapportlistor/2010/rapporter10/szabo_adam_10131.pdf); [excerpt](../sources/excerpts/jp8000-supersaw-szabo.md)). **Source status: supported:** Szabo's figures below come from the paper. **Checked:** SLASH_MY's values below are read from its code.

- `SS_DET` equals Szabo's Table 1 exactly: at maximum detune, the seven voices sit at 1 + offset times the center frequency, with offsets −0.11002313, −0.06288439, −0.01952356, 0, +0.01991221, +0.06216538 and +0.10745242. At full detune that is about −201.8, −112.4, −34.1, 0, +34.1, +104.6 and +176.6 cents (computed from the table).
- SLASH_MY scales the table linearly by `det`. Szabo maps the JP-8000's detune knob to the offset multiplier through an 11th-order polynomial in x = knob/127. On that curve, SLASH_MY's `det` 0.12 corresponds to a knob near x ≈ 0.555, or MIDI ≈ 70 (interpolated from Szabo's Table 2).
- SLASH_MY uses a fixed 150 Hz high-pass. Szabo describes a high-pass at each voice's fundamental that tracks pitch.
- SLASH_MY weights the center voice 1 and the sides 0.75. On Szabo's mix curves the center falls linearly and the sides rise along a parabola as the mix knob rises; they are equal only at mix value 95 (0.75).
- Both use random phases per note-on (Szabo: "the oscillators are free running").

### Lead articulation

**Checked (SLASH_MY):** `audio.js` `lead()` L491–524 renders one continuous voice per phrase: the oscillators run through the whole phrase and only control values change per note.

| Control | SLASH_MY value |
| --- | --- |
| Source | 7 PolyBLEP saws, `SS_DET·det` with `det` 0.1 (about ±3, ±11, ±19 cents), width 0.7, drift ±0.2 % at 0.08–0.28 Hz |
| Glide | One-pole on MIDI pitch, time constant 25 ms |
| Vibrato | 0.12 semitone at 5.6 Hz, faded in by `smooth((du − 0.15)/0.2)`: nothing for 150 ms, full by 350 ms |
| Filter | `fc = 900 + 4200·e^(−7·du)·acc`, Q 0.9; phrases set `acc` 1.3 on their first note (L1472–1474) |
| Legato dip | `e = 0.72 + 0.28·smooth(du/0.006)`: each note starts 2.9 dB down and recovers over 6 ms |
| Release | Last note only: exponential, τ 0.18 s, after 94 % of its length |
| Bus | `put` options at L523: `duck: 0.3`, `hp: 160`, `to: 'lead'`; a 3.2 kHz carve keyed on the kick is in [lead dip under the kick](../knowledge/Dynamics%20and%20spectral%20carving.md#lead-dip-under-the-kick) |

These bus values are hard-coded in `lead()`. The voice with duck 0.4 and a 150 Hz high-pass is `acid()` (L643).

The single call site is L1480 (`g` 0.3, carve 1.4). Phrase 30 plays an octave down at `DROP2_LEAD` −4 dB.

The filter is the Zavalishin TPT state-variable form (`class SVF` L36–51), which tolerates per-sample modulation.

The AX DAY reconstruction has no lead voice. Its melodic top lines are short supersaw stabs and, in the drop, an arpeggio of sines with a second harmonic panned ±0.6 (L159–177).

### Layered kick

**Checked (SLASH_MY):** `audio.js` `kick()` L300–316.

| Layer | SLASH_MY value |
| --- | --- |
| Body | Phase-integrated sweep `f0` 150 → `f1` 47 Hz at rate `pd` 30; held at full level for 25 ms, then `e^(−dec·(u − 0.025))`, `dec` 7 |
| Drive | `tanh(1.8·sin)/tanh(1.8)` (normalized so peak stays 1) |
| Knock | `0.75·sin` sweeping 230 → 185 Hz (rate 60), `e^(−35u)` (about 30 ms) |
| Click | `e^(−380u)·(0.3·sin(cf) + 0.18·noise) + 0.9·HP5k(noise)·e^(−450u)` |
| Click shaping | Raised-cosine ease over 0.6 ms, then two cascaded SVF low-passes at 9 kHz (Q 0.54 and 1.31, fourth order) |
| Per-hit variation | Tail pitch `f1 × (1 + hum(0.012))` (±1.2 %); click tone `cf` 3.6–4.6 kHz from `rHum` |
| Length | 0.55 s, 30 ms fade-out, to the drum bus |

The code's comment says the ease and low-pass leave the click "no step and no sample-to-sample spikes for the drum clip to sharpen".

Callers change the starting values per role:

- Impacts (`impact()` L1004–1008): `dec` 5, `f0` 190, `g` 0.95 or 1.05.
- The build's first hit (`BUILD_HIT` L1321): `dec` 3, `f0` 190, click and knock scaled down as the lows go up 1.5 dB.
- The build's kicks shorten from 0.4 to 0.15 s and `dec` goes 10 → 20 from beat 108 (L1341–1342).
- The reveal's kicks use `f0` 120, `pd` 45, click 1.4 (L1408).

`K()` (L294–298) keeps one kick per grid position, letting an impact kick replace the groove kick on the same beat.

**Checked (AX DAY reconstruction):** `audio.js` `kick(t, g)` L60–64: `tanh(1.6·sin(155 → 45 Hz, rate 30))·e^(−7u)` plus 4 ms of raw noise at 0.5, switched on and off without a ramp, for 0.5 s. There is no knock, no click filtering and no per-hit variation. `kick()` applies `gain: 0.9·g`, so the effective gains are:

| Kicks | Call | Effective gain |
| --- | --- | --- |
| Beats 8–31 (before the drop) | `kick(t)` (L65) | 0.9 |
| After the drop, every second beat 34–38 | `kick(t, 0.8)` (L66) | 0.72 |
| The drop hit, beat 32 | `kick(t, 1.2)` (drop block, L161) | 1.08 |

The two loops test `t < T.DROP·B` and `t > T.DROP·B`, so the kick on the drop beat comes only from the drop block. The reconstruction's sound analysis records the chatlog's phrase for this kick: "rapid pitch fall and a short noise attack".

**Reported:** commit `f1f6d6c1` lists "kick click eased and band-limited" with the note "(polish 0 glitches)" alongside other mix changes in the same commit.

### Multi-burst clap

**Checked (SLASH_MY):** `audio.js` `clap()` L317–327.

- One SVF on one noise source at 1300 Hz, Q 1.3.
- Envelope peaks at offsets `[0, 0.011 ± 0.002, 0.021 ± 0.002, 0.030]` s, each decaying `e^(−240d)`; the last peak at 1, the others at 0.65. The two middle offsets jitter per hit from `hum`.
- After 30 ms, a tail `0.5·e^(−12(u − 0.03))`.
- Output `bp·(e + tail)·1.7 + hp·e·0.25`; 0.42 s, `hp` 180, `MIX.clap` 2.1.
- `clapAt()` (L908–911) adds a flam on phrase-ending bars (`PHRASE_END` {9, 13, 17, 31}, L898): a second clap 22 ms early at 0.45 gain, pan −0.12, tail 0.3.

The AX DAY reconstruction plays its backbeats on a snare and has no clap.

**Reported:** commit `71791016` introduces clap flams with swing and velocity curves in one change.

### Noise snare

**Checked (SLASH_MY):** `audio.js` `snare()` L328–337.

- Body `0.55·sin` sweeping `tone + 70 → tone` (rate 40), `e^(−26u)`, `tone` 190 Hz.
- Noise through SVF 3600 Hz, Q 0.7, mixed `bp·1.1 + hp·0.45`, `e^(−dec·u)` with `dec` 15.
- 0.32 s, `hp` 120.
- The writing section uses `tone` 175, `dec` 11, and ghost notes with `dec` 20 and a 2600 Hz low-pass (around L1227–1229).
- The build roll (L1343–1349) tunes the shell from 190 Hz toward 400 Hz across the build, and the debrief roll from 180 toward 290 Hz. The comment says the roll's drum is "tuned up as it tightens". Their timing, gain and tuning are tabled in [accelerating snare rolls](../knowledge/Groove%20and%20feel.md#accelerating-snare-rolls-into-a-gap).

**Checked (AX DAY reconstruction):** `audio.js` `snare()` L75–90: a one-pole band `lp5000 − lp300` on noise, `e^(−14u)`, plus `0.5·sin(190 Hz)` at a fixed pitch, `e^(−30u)`. Backbeats at 17–27 play at 0.5. Its roll from beat 28 keeps the shell at a fixed pitch.

### Hats and cymbals

**Checked (SLASH_MY):** `audio.js` `hat()` L338–350.

- Six square partials, `HAT_F = [205.3, 304.4, 369.6, 522.7, 540, 800] × 1.9` (L338), with random phases per hit from `rPh`, summed at 0.1.
- Noise at 0.5.
- Through SVF 7600 Hz, Q 0.9; output `hp + 0.35·bp`.
- Decay rate 65 closed and 8 open; length 0.09 s closed and 0.5 s open.
- Default pan 0.22; `MIX.hat` 3.0, `MIX.ohat` 2.1.
- `autoPan` (L895) moves closed hats by `0.1 + 0.32·sin(2π(b − 0.5)/4)`, one cycle per bar.
- `crash()` (L375–384) reuses the frequencies as sines at `HAT_F × 2.3`.
- `sfx.js` `cymbal()` (around L1341–1343) uses the same base list `× 1.9 × 2.3` with ±2 % random spread, so hats and cymbals share one partial family.

**Comparison with the TR-808** ([Werner, Abel & Smith 2014](https://speech.di.uoa.gr/ICMC-SMC-2014/images/VOL_2/1453.pdf); [excerpt](../sources/excerpts/tr808-cymbal-oscillators.md)). **Source status: supported:** the TR-808's cowbell, cymbal, open hi-hat and closed hi-hat share six rectangular-wave oscillators on one HD14584 hex Schmitt-trigger chip. Four are fixed at 205.3, 304.4, 369.6 and 522.7 Hz; the other two have trimpots and are factory-tuned to 540 and 800 Hz, within ranges of 254.3–627.2 Hz and 359.4–1149.9 Hz. **Checked:** `HAT_F`'s base list is exactly these six frequencies. SLASH_MY differs in these ways:

- It multiplies them by 1.9 for the hats (390–1520 Hz) and by a further 2.3 for the crash and the `sfx.js` cymbal.
- Its square waves have a 50 % duty cycle; the paper models the 808's at 47.98 %.
- It filters through one SVF at 7.6 kHz; the 808 has two band-pass filters centered near 3440 Hz and 7100 Hz.
- The paper notes that units before serial #000300 used different component values for oscillators 5 and 6.

The SLASH_MY code does not name the 808 as the source of the list.

**Checked (AX DAY reconstruction):** `audio.js` `hat()` L68–73: noise minus a 7 kHz one-pole low-pass, `e^(−90u)` for 0.06 s closed or `e^(−18u)` for 0.25 s open, fixed pan 0.25.

### Bass

**Checked (SLASH_MY):** `audio.js` `bassNote()` L387–397.

- Two PolyBLEP saws at `f × 1.004` and `f × 0.996`, averaged.
- SVF low-pass `cut 360 + env 1500·(1 + 0.7·acc)·e^(−9u)`, Q 1.2.
- A sine at the fundamental (`sub` 0.75) added before `tanh(drive 1.4·(0.8·lp + sub))`.
- 45 ms linear release after the gate; duck 0.75 by default.

**Checked (AX DAY reconstruction):** `audio.js` L93–100, offbeat eighths: a naive saw plus `0.6·sin(f·0.5)`, a sine one octave below the root. `ROOTS` are MIDI `[33, 29, 36, 31]` (44–65 Hz), which puts this sine at 22–33 Hz. A one-pole low-pass sits at 400 Hz before beat 16 and 700 Hz after; 5 ms attack, `e^(−4u)`, ducked, gain 0.45; no saturation.

**Reported:** commit `f13f69d2` raises the brand section's bass duck 0.72 → 1.2 and reports the bass going "2.0 -> 4.2 dB under the kick, <120 Hz". The ducking itself belongs to [kick-keyed ducking](../knowledge/Dynamics%20and%20spectral%20carving.md#kick-keyed-ducking).

### Drone and room tone

**Checked (SLASH_MY):** `audio.js` L935–953, inline in the intro.

- Pedal MIDI A1 (33) → F1 (29) at beat 8 → E1 (28) at 12 → A1 at 16, glided by a one-pole with a 90 ms time constant.
- Two PolyBLEP saws an octave above the pedal at `× 1.003` and `× 0.997`, one per channel, each through its own SVF low-pass, Q 1.4, with cutoff `expRamp(140, 1000, b/16)` and ±20 % wobble at 0.13 Hz.
- A sine at the pedal pitch at 0.35 in both channels.
- Level rises over 3 s and falls over 2.5 beats after beat 16.
- Gain 0.13, reverb send 0.3, duck 0.45.

A separate room tone (L954–971) runs under the 5 s warning card and SLASH_MY's first six beats. Commit `b0ab2eff` reports it at −52 dBFS rms (Reported; [room tone](../knowledge/Mastering%20and%20delivery.md#room-tone-instead-of-digital-silence)).

**Checked (AX DAY reconstruction):** `audio.js` L45–50: sines at MIDI `[45, 52, 57, 60, 64]` with amplitudes `[1, .6, .5, .35, .25]`, a small phase wobble `0.3·sin(0.7u + m)`, 2.5 s fade-in, decay after 3.9 s, tremolo `0.8 + 0.2·sin(3u)`, gain 0.07, reverb send 0.5, not ducked.

### Karplus-Strong pluck and keys

**Checked (SLASH_MY):** `audio.js` `ksLen()` L64 and `ksBuffer()` L65–90 (the comment above them starts at L62).

| Part | SLASH_MY value |
| --- | --- |
| Integer length | `L = floor(SR/f − damp − 0.15)` |
| Fractional tuning | Remaining delay `d = SR/f − L − damp` (0.15–1.15 samples) through a first-order allpass, `C = (1 − d)/(1 + d)` |
| Exciter | Noise through a one-pole low-pass at `250 + 9000·bright` Hz, from the shared noise stream |
| Pick position | Once on excitation: `buf = ex − 0.85·ex[i − round(pick·L)]`; DC removed, normalized |
| Loop filter | `((1 − damp)·cur + damp·prev)·decay` |
| Pitch-dependent loop gain | `decay = 10^(−3/(t60·f))` per period, so the nominal T60 is the same at every pitch (holds by construction) |
| Defaults | `bright` 0.5, `t60` 1.2 s, `damp` 0.4, `pick` 0.17 |

The damping average is not pitch-compensated, so it removes more per second on high notes. At 880 Hz with `damp` 0.32 and `t60` 1.1, the fundamental's T60 works out to about 0.92 s, and upper partials die faster still (Checked, calculated from the loop filter, not measured). `sfx.js` `ks()` L1646–1667 is the same algorithm on its own seed.

Voices built on it:

- `pluck()` L449–461: `PLUCK_DAMP` 0.32, `bright` 0.6, `t60` 1.1; mix `0.75·KS + 0.35·saw`, where the saw runs through SVF low-pass `700 + 4200·e^(−16u)`, Q 1.2, times `e^(−5u)`; `hp` 150, duck 0.3. The intro's pre-echo plucks (L932) drop the saw and use `bright` 0.3, `damp` 0.5 and a low-pass rising 650 → 1500 Hz.
- `keyNote()` L466–488: KS (`bright 0.22 + 0.3·vel`, `t60` 1.8, `damp` 0.45, `pick` 0.13) at 0.6 plus an FM tine at 0.5 (index `1.4·vel·e^(−10u)`, amplitude `e^(−2.4u)`); autopan 2.6 Hz, depth 0.28; optional chorus of two taps at 8 ± 2.5 ms swept in antiphase at 0.6 Hz; duck 0.25, `hp` 140.

The AX DAY reconstruction has no plucked, keys or physical-model voice. Its key sounds (L52–56) are typing ticks of high-passed noise and a sine.

**Attribution.** Karplus & Strong introduced the plucked-string and drum algorithm ([CMJ 1983, doi:10.2307/3680062](https://doi.org/10.2307/3680062)). Their patent ([US Patent 4,649,783](https://patents.google.com/patent/US4649783A/en), priority 1983-02-02; [excerpt](../sources/excerpts/karplus-strong-patent.md)) describes decay stretching: "Each of the decay algorithms allows decay stretching during the decay operation with the stretching factor, s, equal to 1, 2, 4, 8, 16, 32, 64, or infinity. The factor s (which equals 1/d) multiplies the unstretched decay time by the value of s." The stretching is probabilistic. The ledger gives this claim source status: partly. The CMJ paper is not online and was not checked. Jaffe & Smith added fractional-delay tuning with an allpass filter and pick-position comb filtering ([CMJ 1983, doi:10.2307/3680063](https://doi.org/10.2307/3680063)). SLASH_MY's loop filter has the deterministic weighted two-tap form `(1 − S)·y[n−N] + S·y[n−N−1]`, with S = `damp`. Only secondary course notes credit that form to Jaffe & Smith, so its attribution stays open. The CCRMA PASP pages on Karplus-Strong and Extended Karplus-Strong do not mention decay stretching. No checked source covers SLASH_MY's per-pitch loop gain.

### Formant vocal and stacked takes

**Checked (SLASH_MY):** `audio.js` L526–611: formant tables L536–553, level matching L553–576, `my()` L580–611.

| Part | SLASH_MY value |
| --- | --- |
| Source | PolyBLEP saw; per take ±3 cents random detune, vibrato rate 5.2–5.8 Hz |
| Pitch | Scoop of −0.9 semitone decaying with τ 35 ms; vibrato 0.22 semitone, delayed `smooth((u − 0.15)/0.2)` |
| Formants | `VOWEL` /m/ [280, 1150, 2400], /a/ [780, 1180, 2800], /i/ [290, 2250, 3000] Hz; Q `[3.5, 5, 7]`; weights `[1, 0.6, 0.22]·4/Q` |
| /m/ | `M` = 25 ms; the lips blend a nasal SVF low-pass (380 Hz × formant scale, Q 0.7) into the raw saw over 15–35 ms |
| Vowel motion | /m/ → /a/ over the first 25 ms; a full word glides to /i/ from 55 % to 95 % of its length; fragments (`kind 'frag'`) stop short, with `open` capping how far the lips and vowel open |
| Breath | Noise band-pass 1900 Hz, Q 0.9, at 0.05 decaying `e^(−18(u − M))` as the lips open; lead take only |
| Envelope | 6 ms attack, 50 ms release; fragments decay `e^(−4u)` |
| Level match | `vowelGain()` and `voicing()` scale each note to how E5 (MIDI 76) passes the same formants (the /a/ match capped at 2×), so a note sounds at its set level whatever its pitch (holds by construction) |
| Pair (`dbl`) | Second take 8 ms late, +7 cents, pan +0.38 at 0.8, lead take at −0.22 |
| Stack (`stack`) | Center lead take plus `MY_STACK` `[onset s, cents, formant ×, pan, dB]`: `[0.014, 11, 1.025, −0.45, −7]`, `[−0.012, −11, 0.975, 0.45, −7]`, `[0.022, −12, 1.03, −0.8, −9]`, `[−0.018, 12, 0.97, 0.8, −9]` |
| Bus | `hp` 170, to `'vox'`, duck `VOX_DUCK` 0.5 from the drop, 0.2 before |

Stack doubles stay silent through their own /m/ and until the lead take's lips open, so the consonant is the lead's alone, and they add no breath. The comment says the doubles sum to "+2.2 dB over the lead alone". The first double draws from the shared streams; the others draw from `rStack` (seed 606), so adding the stack does not re-roll later parts.

In the code: `score-events.json` `vox` lists fragments from beat 19.75 to 111.625 and whole words from 115.5 to 124. Call sites:

- Fragments: L1021, L1131, L1189, L1273, L1370 (the build's run 110.5–111.625).
- The stacked first word at 115.5 (L1485).
- The breath's pickups as a pair (L1486).
- The hook at 120 as a stack (L1487).
- The long word on the lock at 124, 2.5 beats, stacked (L1488).

The AX DAY reconstruction has no vocal voice.

**Reported:** commit `059ff33a` describes the stack as one centered lead take with four doubles 7 and 9 dB under it, panned ±0.45 and ±0.8, 12–22 ms off the lead, and 11–12 cents and 2.5–3 % of formant away from it. The fragments stay single, and the breath's pickups are a pair.

### Composite impacts and drop layers

**Checked (SLASH_MY):** `sfx.js` `IMPACT` L1331–1340 (entries for beats 16, `BURST_AT` 104, 112, 120 and 128) and `renderImpact()` L1376–1508.

| Layer | SLASH_MY value |
| --- | --- |
| Membrane | Modes `[1, 1.59, 2.14, 2.3, 2.65, 2.92, 3.16, 3.5]` on the root's fifth (the root on drops), folded into 55–100 Hz; drops bend pitch by `1 + drop·e^(−t/0.05)` |
| Blast | Noise low-pass sweeping 2400 → 90 Hz over 0.5 s, drive 2.5 |
| Plate | 10 modes on root + 12, spread ±0.7 |
| Crack | High-passed (1200 Hz) burst and tick into a small room (T60 0.3 s) |
| Cymbal, downlifter, debris | Seeded `cymbal()`; `downlifterBuf()` band-passed noise falling to 260 Hz; up to 90 modal grains at 1.8–6 kHz |
| Shockwave | Mid/side noise low-pass 6000 → 160 Hz with width opening over 250 ms |
| Ring (120) | Split-doublet modes on root + 36 and 26 sparks |
| Tuned sub | Root folded into 40–80 Hz, pitch `1 + 0.5·e^(−t/0.06) + subDrop·e^(−t/0.18)`, starting 4 ms late with a 25 ms ramp, drive 1.6 |
| Bus | Shared space, high release above 2 kHz per hit (`hiRel`), compression, EQ, knee and limit, then `LV.impact` −8.0 dB plus a per-hit offset |

`sfx.js` `impact()` L1509–1514 adds the inhale and, where the table asks, the drop stab. The drum-side kick is added separately by `audio.js` `impact()` L1004–1008 (beats 16, 112 via L1382, 120 via L1384).

Other drop layers in SLASH_MY:

- `dropStab()` L1522–1539: PolyBLEP saws on the root + `[24, 31, 36, 43, 48]` semitones at ±9 cents and ±3 cents left/right, low-pass 7 kHz → 900 Hz over 0.3 s, high-pass 300 Hz, a noise burst 1–10 kHz decaying with τ 50 ms, swelling in over 20 ms. Used on 112.
- `inhaleSwell()` L1544–1554 with `INHALE` L1543 (−10 dB, hold 8 ms): band-passed noise, Q 1.4, sweeping 900 → 5500 Hz (right channel × 1.05), amplitude `p³`, the side signal closing toward the center. It crests 8 ms before the hit and closes by half-cosine, so the burst's front lands on a gap. Used before `BURST_AT` (inhale window 103.87–104).
- `subBoom()` L1642–1645: sine 85 → 34 Hz through `tanh(2·)`, decay rate 1.6, a 40 ms fade-in "under the kick transient". The outro uses it at `bt(128) + 0.004`, 110 → 55 Hz, decay 1.9 (`audio.js` L1508).
- `chime()` L2177: bell partials `[1, 2, 2.76, 4.07, 5.4, 6.8]` as split doublets (+0.4–1.6 Hz) per note, notes `[81, 88, 93, 95, 100]` struck left to right, a 6–14 kHz noise shimmer; called at the outro's sheen (`audio.js` L1518). `glass()` L1094 uses `[1, 2.32, 4.25, 6.63, 9.38]` with beating pairs.
- `impactSoft()` L1555 (beats 56 and 96): cymbal plus downlifter (`downlifterBuf()`, L1561) plus a sonar whomp or glass ring.

**Checked (AX DAY reconstruction):** drop block L159–177, all starting on the same sample:

- `kick(t, 1.2)`, an effective gain of 1.08 (see the kick section).
- A sub `tanh(2·sin(92 → 32 Hz, rate 8))·e^(−1.3u)` for 3 s at 0.7.
- A noise crash `(n − 0.7·lp4000(n))·e^(−1.6u)` for 3.5 s at 0.3, reverb send 0.5.
- A supersaw chord `[45, 57, 60, 64, 71, 76]` at 0.16, cutoff 1200 opening by 3000, release 2.5 s.
- An arpeggio `[81, 84, 88, 83, 86, 88, 91, 88]` over beats 34–44.
- A chime at beat 39.5, `880·[1, 2.76, 5.4]` with decay `e^(−(2 + 2k)u)` and amplitude `1/(k + 1)`.
- A 55 Hz note at 44.

The countdown (L152–156) is a 140 → 60 Hz sine plus bells at 1047/1175/1320 Hz with a 2.01 partial. There is no inhale and no stab, and the sub starts with the kick rather than after it.

**Reported:**

- Commit `74df504b` adds the drop stab so that "112 reads as the biggest hit on small speakers too", with the noise front and the sub lowered to `subG` 0.35.
- Commit `1338eea5` sets impacts per hit: 112's crash and debris released fast, with the band above 2 kHz 6 dB down by 0.35 s; 120's top 8 dB down by 0.35 s; 16 compact. It reports the full mix below 120 Hz over 400 ms at −12.7 (112), −14.0 (120) and −17.5 (16).
- Commit `30c1df7a` introduces "the 104 burst with one inhale".

### Risers and whooshes

**Checked (SLASH_MY):** `sfx.js`.

| Source | Lines | Recipe |
| --- | --- | --- |
| `riser()` | L1576–1593 | Two band-passed noises (Q 2, left and right × 1.05) sweeping `f0 → f1` exponentially; two PolyBLEP saws 0.15 semitone apart gliding `m0 → m1` along `p²` through a low-pass capped at 6 kHz; amplitude `p^curve`; 4 ms end fade; high-pass 150 Hz |
| `grainRiser()` | L1598–1622 | Grains on A minor pentatonic at density `5·60^(p^1.3)` per second, 25 % noise grains; normalized over its last 600 ms; 5 ms end fade |
| `revCymbal()` | L1623–1633 | A seeded crash played backwards, sweeping right to left into the downbeat |
| `reverseSwell()` | L1669–1690 | Reversed saw-chord swells into beat 16 (`audio.js` L989), a reverse pluck into 24 (L1020), reverse keys into 84 (L1268) |
| `whooshRender()` | L762–920 | Kinds `air` (low-pass sweep, Doppler band-pass, jet flange comb 0.3–2.5 ms), `tape`, `slide`, `sonar`; `WHOOSH_FLAVOR` L924–937 maps sections to flavors |
| `whoosh()`, `rush()` | L946–957, L961–967 | `whoosh()` picks the section's kind and peaks on the `WHOOSH_EXIT` entry for that beat when one exists; `rush()` renders one `air` whoosh through `RUSH.peak`, the camera's rush into 16 (`audio.js` L1009) |

Calls in `audio.js`: `riser(12, 16)` (L988), `riser(46, 48)` and `riser(52, 56)` (L1132–1134), `revCymbal(56, 2)` (L1133), `grainRiser(96, GAP_START)` (L1355).

`downlifter()` (`sfx.js` L1634) is defined and exported but never called. Only `downlifterBuf()` is used, inside `renderImpact()` (L1436) and `impactSoft()` (L1561).

**Checked (AX DAY reconstruction):** one riser (L142–151) over beats 24 → 31.75: a noise band `y − y2` with `fc = 300 + 7000·p²`, a chirp 150 → 1050 Hz, amplitude `p²`, gain 0.55. Word whooshes (L125–135): one-pole noise with cutoff `500 + 5000·sin`, a half-sine of 0.55 s starting 0.18 s before each slow word. Fast words get short ticks (L136–139).

## Dynamics and spectral carving

Technique page: [dynamics and spectral carving](../knowledge/Dynamics%20and%20spectral%20carving.md).

### Kick-keyed ducking in SLASH_MY

**Checked:**

- One curve for SLASH_MY: `DUCK` (L97), where 1 means open.
- `addDuck(t, depth, rel, att = 0.004)` (L136–145) writes a raised-cosine dip over `att`, then an exponential return with time constant `rel`, for `att + 6·rel` seconds. Overlapping dips combine by minimum: the deeper one wins, and they do not stack.
- Render order (L1695–1697): every kick's dip is written first, `pre` seconds early, then every queued voice renders (`Q`), then the kicks play. Each voice therefore reads a complete curve.
- In `put` (L129) a voice with amount `duck` applies `e *= 1 − duck·(1 − DUCK[i])`. This happens before its sends (L132–133), so its reverb and delay sends carry the ducked signal. At the output (L2222) the music and vocal returns are ducked again: the reverb by `1 − 0.5·(1 − DUCK)`, the delay by `1 − 0.3·(1 − DUCK)`.
- `duckOnly` entries write a dip without playing a kick: the exec wait (L1035–1036), the slams (`slamHit`, L1548) and the outro's pulse at 128 (L1507).
- Nothing clamps the product. Where amount × depth exceeds 1, the gain goes negative at the bottom of the dip and the voice flips polarity. Brand's bass (amount 1.2) on beat 16, under the 0.85 impact, reaches 1 − 1.02 = −0.02.
- Releases are fixed seconds. None is derived from the tempo.

**Ducks that open before the hit.** A kick's `pre` moves its dip earlier. The reveal kicks use `pre: 0.004` (L1408), so the 4 ms attack is complete on the beat. Every other kick's dip starts on the beat and reaches depth 4 ms later. The carves, strike carves and bed dips open further ahead.

Kicks:

| Kicks | Depth | `rel` (s) | Line |
| --- | --- | --- | --- |
| Intro 8–16 | 0.15 → 0.35 | 0.1 | L983 |
| Impacts 16, 112, 120 | 0.85 | 0.3 | L1005; L1382, L1384 |
| Brand, exec and nav grooves | 0.6 (default) | 0.1 | L1014, L1041, L1282; default at L1695 |
| Exec wait (duck only) | 0.6 × −6 dB ≈ 0.30 | 0.1 | L1035–1036 |
| Design | 0.8 | 0.11 | L1145 |
| Writing 76–92 (swung kicks) | 0.4 | 0.1 | L1226 |
| Debrief 92–96 | 0.5 | 0.1 | L1243 |
| Build hit 104 | 0.85 | 0.3 | L1321 |
| Build 104–112 | 0.55 → 0.3 | 0.1 | L1342 |
| Reveal | 0.65, `pre` 4 ms | 0.1 | L1408 |
| Slams (duck only) | 0.35 | 0.16 | L1548 |
| Outro pulse at 128 (duck only) | 0.6 | 0.4 | L1507 |

Voice amounts:

| Voice | Amount | Line |
| --- | --- | --- |
| Bass (`bassNote`) | 0.75 default; exec 1.3, brand 1.2; design 0.92; writing 0.45; debrief 0.6 | L387; L1117; L1175; L1239; L1254 |
| Bass line (`bassLine`) | 0.45 | L716 |
| Supersaw | 0.5 default; exec stabs 0.4; design stabs 0.15; reveal stabs 0.25 and 0.4; reveal chord bed 0.9; outro 0 | L405; L1059; L1155; L1422, L1430; L1447; L1510 |
| Pad | 0.5 default; reveal 0.6; outro 0 | L432; L1424; L1513 |
| Lead | 0.3 | L523 |
| Acid line (`acid`) | 0.4 | L643 |
| Mallet | 0.3 | L620 |
| Pluck | 0.3 | L451 |
| Keys | 0.25 | L487 |
| Gayageum | 0.2 | L677 |
| Vocal | 0.2 before 112; `VOX_DUCK` 0.5 from 112 | L579–581 |

At full depth (computed here): exec bass −13.2 dB, design bass −11.6 dB, the reveal chord bed −7.6 dB, the reveal vocal −3.4 dB, a default pad under a groove kick −3.1 dB, writing's bass −1.7 dB. Recovery: a default kick (0.6, τ 0.1 s) leaves −0.44 dB on a fully ducked voice by 0.25 s, the next eighth. An impact (0.85, τ 0.3 s) is still −4 dB at 0.25 s and −1.5 dB at 0.5 s, the next beat.

**Reported:** `f13f69d2` raised brand's bass amount from 0.72 to 1.2 and reports its dip under the kick, below 120 Hz, going from 2.0 to 4.2 dB. `72d00e0c` raised exec's from 0.72 to 1.3 and reports exec's bass dip going from −2.1 to −4.6 dB (design's: −4.7).

### Kick-keyed ducking in the AX DAY reconstruction

**Checked:** `audio.js` L29–37. `kicks` lists every beat from 8 to 31, then every second beat from 32 to 38. `duck(t) = 1 − 0.7·exp(−(t − k)/0.11)`, where `k` is the latest kick at or before `t`. There is one depth for every voice that uses it, no attack and no pre: the gain steps to 0.3 (−10.5 dB) on the kick's sample. The same list plays the kicks (L65–66; the drop kick at 32 is L161).

Only two voices multiply by `duck`: the bass (L98) and the supersaw (L113). The supersaw carries the pad over 8–16 (L117), the offbeat stabs (L119–122) and the drop chord from 32 (L166). The comment at L29 says "everything melodic ducks under the kick", but the drone, keys, arpeggio, chime, drop sub, crash, drums, word ticks and the reverb return do not.

The bass and the stabs sit on the offbeat eighths and end before the next kick, so they meet only the curve's tail: −0.65 dB at their onset, 0.25 s after the kick, and about −0.1 dB by their end (computed here). The full step falls on the sustained pad and the drop chord, so in effect the chords pump. The reconstruction's sound analysis records the same reading.

### Carve keys and the carve table

**Checked (SLASH_MY):** `keyCurve(beats, db, hold, rel, att = 0.003)` (L1739–1750) turns key times into gain curves. Each key fades in over `att` before the event (a smoothstep), holds, and returns exponentially, for `att + hold + 5·rel` seconds. Overlapping keys combine by minimum. A cut applies the curve to one band of a target bus in one of two shapes:

- Bell: `X −= (1 − key)·k·bp` on a state-variable filter (`k = 1/Q`). A fully closed key is a notch at `hz`.
- Above a corner: `X −= (1 − key)·(X − lp)`, which scales everything above a 2-pole low-pass corner by `key`.

`PAD_DIP` is the one level-keyed carve: it follows the vocal's and lead's level in their own band, like a dynamic EQ with a sidechain.

| Carve | Key | Target | Band | Depth | Timing | Line |
| --- | --- | --- | --- | --- | --- | --- |
| `CARVE_DB` | exec and design hook stabs | drums | bell 1.7 kHz, Q 0.8 | 5 dB | hold 0.16 s, rel 0.06 s | L1966–1976 |
| `LEAD_CARVE_DB` | reveal lead notes 112–119, not on strikes | FX bus | bell 1.7 kHz, Q 0.8 | 4 dB | hold 0.16 s, rel 0.06 s | L2050–2062 |
| `STRIKE_ROOM.ring` | the drop's strikes 112–116 | lead | bell 1.3 kHz, Q 1.4 | 4 dB | hold 0.1 s, rel 0.02 s | L853, L1779–1787 |
| `SEAT_ROOM` | writing's answers as they seat | bed | bell 363 Hz, Q 1.9 | 3 dB | att 5 ms, hold 80 ms, rel 30 ms | L871, L2002–2009 |
| `EXEC_BAND` | four exec picture events | bed | bells 800 Hz Q 0.7; 2 kHz Q 1.2; 560 Hz Q 0.8; 530 Hz Q 1.8 | 6; 6; 10; 4 dB | att 10 ms, hold 150/150/80/80 ms, rel 30 ms | L2010–2029 |
| `MY_POCKET` | the sung "my" 112–116 | bed | bell 1.1 kHz, Q 0.6 | 4 dB | the word's length, att 10 ms, rel 50 ms | L2035, L2037–2049 |
| `LOCK_POCKET` | sung words 120–128 | bed | bell 2.24 kHz, Q 0.25 | 10 dB | the word's length, att 10 ms, rel 50 ms | L2036–2049 |
| `PAD_DIP` | vocal + lead band-passed at 2.2 kHz; envelope 5 ms / 150 ms | pads | bell 2.2 kHz, Q 0.7 | half the key's dB over `PAD_DIP_THR` (0.01), at most 4 dB | follows the envelope | L1788–1809 |

Four further keys dip the pads full band rather than in a band: `STAB_KEY` 3 dB on the reveal's stabs, `STRIKE_KEY` 3.5 dB on the drop's strikes, `BLIP_KEY` 4 dB on the build's blips before 108 and `BLIP_FAST` 7 dB from 108 (L1758–1762). `STRIKE_KEY` also scales the music returns (L2222).

**Reported:** `70c9dfe5` reports the voice over the rest of the mix at 500–2500 Hz, in the word's first 0.3 beat, going from −0.5 to +1.4 dB with `MY_POCKET`. `d7aeae3d` deepened `LOCK_POCKET` from 6 to 10 dB and reports the vocal against the rest at 1–5 kHz going from −7.2 to −5.6 dB.

**AX DAY reconstruction**: no band carves. Its voices use one-pole low-passes as tone filters only.

**Interpretation:** no source gives fixed carve bands (source status: partly, for keyed dynamic EQ in general). Every band in the table is a case value found for SLASH_MY's own parts.

### Lead dip under the kick

**Checked (SLASH_MY):** `lead()` (L515–521) reads the shared kick curve: `d = min(1, carve·(1 − DUCK))`, then subtracts `d·k·bp` of a state-variable bell at 3.2 kHz, Q 0.6, from each channel. Because it reads `DUCK`, the dip opens with the reveal kicks' 4 ms pre-duck and releases with them. Only the reveal's lead uses it, with `carve: 1.4` (L1480). Under a reveal kick (0.65) `d` reaches 0.91, about −21 dB at 3.2 kHz (computed here). Under the 0.85 impacts at 112 and 120, `d` clamps at 1, a full notch.

**Comment versus code**: the comment in `lead()` says the carve covers "2-5 kHz"; the code's band is a single bell centered at 3.2 kHz, Q 0.6.

`LEAD_CARVE_DB` (L2053; block L2050–2062) is a separate carve, in which the lead's notes cut the FX bus 4 dB at 1.7 kHz (see the carve table).

**Reported:** `e099d948` added this dip together with the reveal kicks' 4 ms pre-duck and a ×2 click. It reports the click against the rest in the first 10 ms going from −4.9 to +3.6 dB, and the click's peak landing within 5 ms of the beat on 15 of 15 kicks (was 10 of 15). The click is now 1.4 (`5c8bcda8`), so these figures do not describe the current render.

### Low band keyed to the kick

**Checked (SLASH_MY):** L1862–1897. `SUB_KEY` sets two keys over the reveal's kicks (112–128): the FX bus dips 10 dB, held 0.04 s, back over 0.2 s; the bed dips 18 dB, held 0.2 s, back over 0.08 s. The FX key skips the impact kicks, whose kick and boom are one hit. The FX bus also takes `DROP_SUB_DIP` 9 dB on its low band at 112 and 120, easing back with a 0.5 s time constant. Each bus runs through a Linkwitz-Riley split at 150 Hz (two cascaded 2-pole state-variable low-passes, and two high-passes) from `GAP_START` (111.75) to the end. Its low band is multiplied by the key and summed back with the high band. The reveal's rolling bass also rests on the kick's sixteenth by its pattern (L1448).

The build's hit at 104 takes the same 9 dB easing dip on the FX bus's low band, but through `lowZP` instead of a split (L1868–1876). `lowZP` (L1730–1737) runs a 2-pole low-pass at 150 Hz forward and then backward, which gives a zero-phase low band, and subtracts a share of it.

**Reported:** `72d00e0c` introduced `SUB_KEY`, with the bed key then at 6 dB (now 18). It reports the delivered kick over the low floor below 120 Hz going from 6.7 to 11.9 dB at 114, 4.5 to 8.3 at 115 and 8.1 to 9.9 at 116. `c893a310` moved the build hit's dip to the zero-phase band because "a split moved the build's peaks: clip 2.6 -> 3.7", and reports the burst's sub against the kick at 45–70 Hz going from −4 to −11 dB.

### Strike carves

**Checked (SLASH_MY):** `STRIKE_ROOM` (L851–854), applied at L1978–2001. Each carve is a `keyCurve` held 0.15 beat (75 ms) and released over 0.03 s, cut with the "above a corner" shape on the bed and drum buses. Overlapping carves combine by minimum.

| Strokes | Target | Cut | Opens |
| --- | --- | --- | --- |
| Exec and design slot strokes (`EXEC_STRUCK`, `DESIGN_STRUCK`) | bed, drums | 6 dB above 1.3 kHz | 3 ms ahead |
| The drop's strokes 112–116 (`REVEAL_STRIKES`) | bed, drums | 10 dB above 1.6 kHz | 0.3 beat (150 ms) ahead |
| The drop's stroke on a reveal kick (114) | bed, drums | 12 dB above 1.6 kHz (`top.db − STRIKE_ON_KICK`, L1389); the kick itself −5 dB (L1408) | 150 ms ahead |
| Lone strokes (`LONE_STRUCK`: the intro's complaints, writing's 78) | bed, drums | 10 dB above 1.6 kHz | 3 ms ahead |
| A drop stroke on a sung word (115.5) | vocal | 6 dB above 1.3 kHz | 3 ms ahead |

The drop's strokes also take the lead's ring bell and the pads' `STRIKE_KEY` (see the carve table). The drop impact's tail on the FX bus takes the same 10 dB above 1.6 kHz, opened 0.3 beat ahead, under each drop stroke, cut on the sound effect itself (`strokeTopCut`, L876, applied by `sfxCut` at L1381–1382). Under the first stroke it also loses 10 dB in a bell at 4.9 kHz, Q 0.5 (`strokeCut`, L874; `STRIKE_ROOM.top.tail`).

**Reported:** `fff4099e` introduced the 10 dB strike carve above 1.6 kHz. It reports the drop's five strokes at +5.6, +4.4, +6.5, +5.2 and +5.4 dB over the mix at the master (were +2.1, +1.9, +5.3, +1.9, +2.9). It also reports the music's 2–12 kHz band 7–9 dB down under each stroke and back within 1 dB by 120–130 ms, and the music as a whole at most 0.6 dB down and back within 0.5 dB by 55–80 ms. `02802d8d` added the 0.3-beat look-ahead and the kick's −5 dB step. It reports 114's 2–12 kHz rise over the 60 ms before it going from −2.4 to +3.5 dB, and the strokes over the bed at 4, 15.5 and 78 going from −1.7/−0.7/+0.2 to +3.5/+5.7/+8.9 dB. `00e16446` halved the exec-style strike carve (`STRIKE_ROOM.db`) from 12 to 6 dB after a spectrogram showed a dark hole where the lead's harmonics above 1.3 kHz had been.

### Delay-throw carve

**Checked (SLASH_MY):** L1830–1840. For each throw beat `tb` in `EV.throws`, a window runs from the first echo (`tb + 0.75` beat, less 30 ms) to past the fourth (`tb + 3` beats, plus 150 ms), capped at the build's start (104), with 60 ms smooth ramps at both ends. Inside the window the bed loses its 2-pole high-pass band above 300 Hz by `THROW_DB`: 6 dB in nav, 4 dB elsewhere (L906). The window is fixed in time, not keyed to the echoes' level. Writing's thrown notes are also let go by `THROW_END` (0.6 beat) after the throw (L1216), so the first echo lands in a gap. The throws themselves are in [delay throws into gaps](../knowledge/Space%20and%20delay.md#delay-throws-into-gaps).

**Reported:** `d7aeae3d` set `THROW_END` and nav's 6 dB and reports "onsets 83 +11.7, 91 +11.6, 98.75 +13.4, 102.75 +11.5" dB. The commit does not name the reference those figures are measured against.

### Static cuts and mud bells

**Checked (SLASH_MY):**

- Per-voice high-passes in `put`: supersaw 150 Hz (L405), pad 140 Hz (L432), keys 140 Hz (L487), lead 160 Hz (L523), mallet 160 Hz (L620), acid line 150 Hz (L643), vocal 170 Hz (L609), gayageum 110 Hz (L677).
- The supersaw's `mud` option (L403–425) subtracts a bell at 400 Hz, Q 0.55. The comment says it covers 200–800 Hz. The reveal's stabs use 3.5 dB (L1422, L1430). One exec stab, under spex's stamp, uses 15 dB (`SPEX_STAMP`, L1034, L1060).
- `BOX_DB` and `MUD_DB` (L1763–1777) switch on from 112 to 128 only, with a 20 ms glide. The pads and the lead lose 3.5 dB in a bell at 700 Hz, Q 1.2. The pads also lose 2 dB at 400 Hz, Q 0.55.

Commit `df1dd2ad` introduced `MUD_DB` and `4393a7ea` the 700 Hz box cut on the pads, and neither records a measurement of the cut itself.

**AX DAY reconstruction**: no high-passes on the bed and no mud cut. The voices use one-pole low-passes as tone filters, for example the bass at 400 then 700 Hz (L95).

**Interpretation:** the mud source gives a range ("broadly speaking, around 250‑500 Hz", source status: supported). SLASH_MY's 400 Hz bells and the 363 Hz seat carve fall inside it, and the 700 Hz box cut falls above it. The source does not set any of these centers.

### Drum glue compression

**Checked (SLASH_MY):** `compress()` (L2068–2084) is feed-forward and stereo-linked. Its detector is the peak (by default) or RMS of both channels, smoothed by one-pole attack and release, with a quadratic soft knee (6 dB by default) and static makeup. The drum bus is trimmed by `DRUM_IN` 0.5 first (L2067). The glue (L2085) runs at threshold `0.45·DRUM_IN` (−13 dB re the bus's full scale), ratio 3, attack 8 ms, release 120 ms, knee 6 dB, makeup 1, peak detection. Thresholds follow `DRUM_IN`, so the trim changes the bus's level without changing how the compressor acts (comment L2064–2065).

The render prints the glue's maximum and average gain reduction (L2649), but no commit reports a value.

**AX DAY reconstruction**: no drum bus. Drums sum into the dry bus with everything else.

### Parallel crush

**Checked (SLASH_MY):** L2086–2102. The copy is taken after the glue. It is compressed at threshold `0.1·DRUM_IN` (−26 dB re the bus's full scale), ratio 8, attack 1 ms, release 70 ms, knee 3 dB, makeup `PAR_MAKEUP` 3.75. The copy is then band-limited by a 2-pole high-pass at 50 Hz and a 2-pole low-pass at 10 kHz, and added to the dry bus at blend `a`, which glides over 20 ms between per-section values (`PAR`, L2089–2090). The whole bus is then scaled by `DRUM_OUT` 1.35 (L2103). The render prints the copy's gain reduction (L2648).

**Comment versus code**: `PAR_MAKEUP = 3.75` is 20·log10(3.75) ≈ +11.5 dB; the comment at L2086 says +9.5 dB.

| From beat | 0 | 16 | 24 | 56 | 76 | 96 | 108 | 112 | 128 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Blend | 0.1 | 0.45 | 0.45 | 0.4 | 0.25 | 0.45 | 0 | 0.5 | 0.25 |

The blend is 0 over the build's last bar (108–112), "so the drop keeps its jump" (comment L2088).

After the compressors, `SLOT_HIT.pickup` steps the kick pickups between a design or writing slot's start and its slam 3 dB down (L2104–2121). It comes after the compressors so that they do not undo the trim.

Commit `f1f6d6c1` introduced the crush, and no record reports on it.

### Low-band drum saturation through a crossover

**Checked (SLASH_MY):** L2196–2238. After the section tilt and the air shelf, each drum channel is split by a Linkwitz-Riley crossover at `DRUM_XO` 1500 Hz: two cascaded 2-pole state-variable low-passes for the low band, two cascaded high-passes for the high band (L2233–2234). The low band passes linearly below `ct = 0.94·0.62` and is shaped by a `tanh` knee approaching `DRUM_CLIP` 0.94 above it (L2235–2236). It is then summed with the untouched high band. The comment puts the clip at about −5 dBFS after the master gain. The whole drum bus goes through the split, clipping or not. No unfiltered copy of the drums is summed back with the split bands; the reverb and delay returns join only as wet signals. In the reveal (`GAP_START`–128) the drums sit `REVEAL_DRUM` 2.5 dB lower after the clip (L2203, L2226).

**Reported:** `5c8bcda8` introduced the split. On the reveal kicks' first 30 ms it reports peak reduction (max/mean) going from 7.1/5.6 to 2.8/1.5 dB, and the loss above 3 kHz from −2.0 to 0.0 dB. It reports drum-clip distortion over its masking proxy going from 107 frames (max +8.8 dB) to 2 (+1.7 dB).

**AX DAY reconstruction**: no drum bus. Its kick is shaped by a `tanh` inside the voice (L62); see [layered kick](../knowledge/Sound%20sources%20and%20voices.md#layered-kick). Its master `tanh` belongs to [the AX DAY reconstruction's simple master](../knowledge/Mastering%20and%20delivery.md#the-ax-day-reconstructions-simple-master).

### Air shelf that leaves after the drop

**Checked (SLASH_MY):** L2196–2228. `AIR_DB` 2.5 adds a 2-pole 8 kHz high-pass band at `10^(2.5/20) − 1` (`x + gA·hp`), on the music path and the drum path but not the vocal. It is on before 112, stays on through 112's hit and fades out over `AIR_OFF` 0.5 beat after it (L2225). It returns for the wall (116–119), is off again from the breath (119) to 128, and is back from the outro. Gains glide over 20 ms.

Commit `df1dd2ad` introduced `AIR_DB` and `e2cc3614` introduced `AIR_OFF`, and no record reports on the air level.

### Bed dips before hits

**Checked (SLASH_MY):** `BED_GAIN` (L831) collects gain functions, and their product scales the bed (L1829).

| Dip | Where | Depth | Shape | Line |
| --- | --- | --- | --- | --- |
| Pain | an 8-beat slot's start to its slam | 6 dB | eases in over 0.5 beat, back over the 60 ms before the slam; design's slams hold through the slam, then 0.4 s, back over 1.2 s (`DESIGN_TAIL`) | L1652–1665 |
| `EXEC_ROOM` | exec's slams, slot by slot | 0, 2, 3, 4 dB | opens 0.06 s ahead, hold 0.08 s, back over 0.1 s | L1667–1676 |
| `SLOT_HIT` | last 0.5 beat before design's and writing's slams | 4 dB | in over 0.02 s, back in 5 ms (raised cosine) on the slam | L864, L1678–1692 |
| `DEPUTY_IN` | the quarter beat into deputy's slam (42) | 4 dB | as `SLOT_HIT` | L1683–1692 |
| `INHALE_ROOM` | under the nav core's inhale, into the burst at 104 | 6 dB | as `SLOT_HIT` | L1683–1692 |
| `WALL_IN` | last 0.5 beat before the wall (116) | 6 dB, plus 4 dB over the last 0.15 beat on bed and vocal | eases in, back in 5 ms on the hit | L1904–1914 |
| `HIT_ROOM` | from the drop at 112 | 6 dB | hold 0.1 beat, back over 0.15 beat | L1918–1926 |

The `WALL_IN` duck stops short of silence, so 111.75–112 stays SLASH_MY's one silence (comment L1903). These dips leave the FX and the returns untouched.

**Reported:** `d7aeae3d` reports `SLOT_HIT` at 58 going from −0.6 to +2.1 and at 66 from −0.2 to +1.7, without naming the measure. It reports `INHALE_ROOM`'s dip going from 2.6 to 4.5 dB with the burst unchanged at +11.8 dB.

**AX DAY reconstruction**: absent. Its level moves only by note gains, the gate before the drop and the fade. The gate (L203–207) cuts back in with no fade.

### Section tilt shelves

**Checked (SLASH_MY):** `TILT` (L2204–2205). Shelves are built as `x + (g − 1)·lp` and `x + (g − 1)·hp` on 2-pole state-variable filters (L2216–2219), with gains gliding over 20 ms. The drums take the tilt on their own path, before their clip. In the reveal (`GAP_START`–128) `REVEAL_LOW` adds 3.5 dB below 100 Hz to the drums and the bed only (L2215).

| From | Low @ 250 Hz | High @ 5 kHz |
| --- | --- | --- |
| Intro (0) | 0 | 0 |
| Exec (24) | 0 | −2 |
| Design (56) | 0 | +5.5 |
| Writing (76, `TAPE0`) | +1.2 | −1.5 |
| Nav (96) | +0.5 | −1 |
| Drop (112) | 0 | +2 |
| Wall (116) | 0 | +3.5 |
| Breath (119) | 0 | +2 |
| Second drop (120) | +1 | +2.5 |
| Lock (124) | 0 | +3 |
| Outro (128) | 0 | +1.5 |

`DESIGN_SUB` (L2111–2129) is a section cut of the same kind: over design (56–76) the bed and the drums lose a 4 dB share of their zero-phase low band under 60 Hz (eased over 30 ms), so design's sub stays under the drop's.

**Reported:** `d7aeae3d` reports `DESIGN_SUB` moving figures at grounding (−16.9 → −19.0) and vis (−18.3 → −20.3), without naming the measure. `f1f6d6c1` introduced the tilt, without a measurement of it.

### Transient shaper in sfx.js

SLASH_MY already has a transient shaper, `punch()` in `sfx.js` (L351–363), which compares a fast and a slow envelope. It is used only on the exec slams (`slamExec`, L1077), not on the drum bus.

## Space and delay

Technique page: [space and delay](../knowledge/Space%20and%20delay.md).

### Reverb network: comb and all-pass internals

**Checked:** both soundtracks use a Freeverb-style network (the AX DAY reconstruction's comment uses that name). Each comb is a delay line. Its output goes back into the line at gain `room` after a one-pole low-pass, `f = y·(1−damp) + f·damp`. The damping therefore shortens the decay of the top and leaves the low end at full feedback. The comb outputs are summed and passed through all-passes with gain 0.5. Left and right run separate networks, and every right-channel comb and all-pass is 23 samples longer. Sends are tapped after the pan, so each channel's network hears only that channel's share of a source.

| | AX DAY reconstruction | SLASH_MY |
| --- | --- | --- |
| Combs | 6, 1116–1491 samples | 8, 1116–1617 samples (`COMBS`), scaled by `SR/44100` and `size` |
| All-passes | 3: 556, 441, 341 | 4: 556, 441, 341, 225 |
| Comb feedback (`room`) | 0.86 throughout | 0.74–0.92 by room |
| Damping | 0.3 throughout | 0.12–0.55 by room |
| Right-channel offset | +23 samples | +23 samples, scaled with the lines |
| Input gain | 0.02 | 0.008–0.026 by room |
| Return level | ×3, summed before the master `tanh` | ×2.6, ducked by `1 − 0.5·(1 − DUCK)` |
| Predelay, send high-pass, width, output low-pass | none | per room |
| Low-end RT60 | ≈1.36 s (computed with SLASH_MY's formula; not exported or measured) | 0.50–3.09 s, computed by the same formula and exported per room |

In the code:

- AX DAY reconstruction: `audio.js` `reverb` L180–194; `reverb(RL, 0)` and `reverb(RR, 23)` L195; return summed at L202.
- SLASH_MY: `audio.js` `COMBS`, `rt60` and `freeverb` L739–781; music and vocal returns summed at L2222–2228. The music returns also pass through the kick duck, the strike carve (`STRIKE_KEY`) and the place tilt. Those belong to [kick-keyed ducking](../knowledge/Dynamics%20and%20spectral%20carving.md#kick-keyed-ducking), [dynamic band carves](../knowledge/Dynamics%20and%20spectral%20carving.md#dynamic-band-carves) and [section tilt shelves](../knowledge/Dynamics%20and%20spectral%20carving.md#section-tilt-shelves).
- SLASH_MY also bakes a different reverb into some sound effects before they reach the mix: `sfx.js` `diffuse`, `fdn` (an 8-line Hadamard feedback delay network) and `space` L268–299, used for example by the impact's "big space" L1476–1477. That room is part of the cue's own sound; see [composite impacts and drop layers](../knowledge/Sound%20sources%20and%20voices.md#composite-impacts-and-drop-layers).

**Source status: open:** the ledger has no source on comb and all-pass design. The reconstruction's sound analysis describes the result: "Its reverb sends pass through comb and all-pass filters, and the left and right returns differ slightly".

### Reverb state across the pre-drop gap

**Checked:** SLASH_MY clears its comb and all-pass buffers at the pre-drop gap (`resets: [gapI]`), so the build's tail does not resume after the silence. The AX DAY reconstruction's gate mutes the summed mix, reverb included, from beat 31.75 (L203–207), but the reverb's state keeps running.

**Interpretation:** the build's tail therefore returns with the AX DAY reconstruction's drop at beat 32, roughly 5–6 dB lower after the 0.125 s gap. The figure is derived from the computed ≈1.36 s low-end RT60 (60 dB × 0.125 / 1.36 ≈ 5.5 dB), not measured.

### Reverb send routing and per-role sends

**Checked:** `put` adds `send × sample` to a send bus after the pan and the envelope. The AX DAY reconstruction has one `send`. SLASH_MY has `rev` and `dly`, and `to: 'vox'` sends the vocal to its own buses (VR, VD) instead of the music's (RV, DL). SLASH_MY's sound effects enter through `sfx.js` `play` with their own `rev` and `dly`, and `sfxSend(db, …)` scales one cue's room send; design's slams use it to send 6 dB more (`DESIGN_SLAM_SEND`). The music delay's return also feeds the room send at 0.3, so echoes take the current place's reverb. The vocal delay feeds the vocal plate the same way.

| Role | AX DAY reconstruction `send` | SLASH_MY `rev` / `dly` (defaults unless noted) |
| --- | --- | --- |
| Kick | 0 | 0 / 0 |
| Bass and sub | 0 (bass, drop sub, countdown thump) | 0 / 0 |
| Snare, clap | snare 0.25 | snare 0.16, clap 0.2 / 0 |
| Hats | 0.05 | closed 0.03, open 0.08 / 0 |
| Chords | supersaw 0.4, stabs 0.3, drop chord 0.6 | supersaw 0.3, pad 0.5, outro pads 0.6–0.7 / 0 |
| Hook voices | — | pluck 0.3 / 0.3 ×2.5; lead 0.35 / 0.16 ×2.5; keys 0.35 / 0.1 |
| Ornaments | arpeggio 0.7, chime 0.8, countdown bell 0.6, word ticks 0.4 | mallet 0.25 / 0.15; tick 0.2 / 0.12 |
| Transitions and FX | whoosh 0.3, riser 0.3, crash 0.5 | per cue through `play`, e.g. strike 0.08 / 0 |
| Vocal | — (no vocal) | 0.3 / 0.2, to its own plate and delay |

SLASH_MY multiplies the pluck's and the lead's delay send by `ECHO = 2.5` (L285). The code's comment gives the reason: "the dotted-eighth ping-pong is part of the hook."

In the code:

- AX DAY reconstruction: `put` L17–25; the send is set at each call, L45–176.
- SLASH_MY: `put` L107–134 (send routing L119). Defaults sit in each voice: `kick` L300, `bassNote` L387, `supersaw` L403, `pad` L431, `pluck` L450, `keyNote` L466, `lead` L491, `my` L580, `mallet` L614. Also `sfxSend` L822, `DESIGN_SLAM_SEND` L1546, delay into the room L2138, and `sfx.js` `play` L392–396.

### Rooms per place in SLASH_MY

**Checked:** `T.ROOMS` names the seam beats, and picture and score both read it. `ROOMS` pairs each seam with a setting, and the loop renders one `freeverb` per room. Each room receives the shared send only inside its own window, with a 5 ms raised-cosine switch at each seam. The code comment calls this "a 5 ms switch on the send, never a crossfade of returns". The room's output then runs on for up to 5 s (`TAIL`) after its window closes, so the old room's tail rings out under the new one. Design's room (`tape: true`) slows with the tape-stop and is gone at its end, beat 76; writing's room takes the send from the tape-stop's start, 75.5. The other parameters:

- `size` scales every comb and all-pass length.
- `width` scales the side of the return and leaves the mid untouched. Below 1 it folds the sides together; above 1 it spreads them.
- `lpOut` low-passes the return. Only nav uses it.

**Checked:** `rt60` (L740) is the combs' mean loop time at the room's feedback, `−3·size·mean(COMBS)/44100/log10(room)`, which is the low-end decay. `score-events.json` exports it as `rooms`. The exported values are this formula's output by construction, not measurements. The formula leaves out damping (the top decays sooner), predelay and the send high-pass. No commit measures the rooms on their own.

| Beat | Place | `room` | `damp` | Predelay | `size` | `width` | Input gain | Send HPF | `lpOut` | RT60, computed (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | hall (intro, brand) | 0.86 | 0.28 | 18 ms | 1 | 1 | 0.015 | 180 Hz | — | 1.4311 |
| 24 | exec | 0.74 | 0.5 | 6 ms | 0.7 | 1 | 0.011 | 180 Hz | — | 0.5018 |
| 56 | design | 0.89 | 0.12 | 32 ms | 1.2 | 1.4 | 0.015 | 320 Hz | — | 2.2227 |
| 75.5 | writing | 0.84 | 0.5 | 42 ms | 1.05 | 1.5 | 0.008 | 220 Hz | — | 1.2999 |
| 96 | nav | 0.92 | 0.55 | 26 ms | 1.15 | 0.9 | 0.022 | 180 Hz | 4500 Hz | 2.977 |
| 112 | reveal (strikes) | 0.8 | 0.35 | 12 ms | 0.85 | 1 | 0.015 | 180 Hz | — | 0.8222 |
| 116 | wall | 0.9 | 0.2 | 30 ms | 1.3 | 1 | 0.015 | 180 Hz | — | 2.6633 |
| 120 | second drop | 0.9 | 0.18 | 30 ms | 1.3 | 1.4 | 0.026 | 180 Hz | — | 2.6633 |
| 124 | lock | 0.91 | 0.16 | 30 ms | 1.35 | 1.45 | 0.015 | 180 Hz | — | 3.0897 |
| 128 | outro (hall) | 0.9 | 0.3 | 18 ms | 1 | 1 | 0.016 | 180 Hz | — | 2.0487 |

In the code: SLASH_MY `timeline.js` `ROOMS` L155–159; `audio.js` `ROOMS` L2139–2153, the room loop L2154–2172, export L2496. AX DAY reconstruction: absent; one network runs for all 24 seconds.

Commit `ab80223f` adds the RT60 export; how the picture uses it is in [sound and picture on one beat grid](../knowledge/Audiovisual%20synchronization.md#sound-and-picture-on-one-beat-grid).

### Predelay and send high-pass values

**Checked:** `freeverb` reads its input `predelay·SR` samples late, then runs it through a two-pole state-variable high-pass at `hpIn` (Q 0.7, 12 dB/octave) before the combs (L749–757). The default `hpIn` is 180 Hz; design uses 320 Hz and writing 220 Hz. Predelays run from 6 ms (exec) to 42 ms (writing), and the vocal plate uses 30 ms.

Further filtering comes before the send. Pitched voices carry their own high-pass in `put`, which filters dry signal and send together: supersaw 150 Hz, pluck 150, pad 140, keys 140, lead 160, vocal 170. The delay's input is high-passed at 260 Hz (`pingpong` L791).

Against the ledger ([audio source ledger](../sources/Audio%20sources.md), status partly): Sound On Sound says "try putting a 200Hz 12 or 18 dB/octave filter before or after the reverb". SLASH_MY's filter sits before the reverb, at 12 dB/octave. Its 180 Hz default and writing's 220 Hz are close to that 200 Hz; design's 320 Hz is well above it, and the source does not cover that choice. The 30 ms vocal predelay falls within the ledger's "roughly 20–80 ms predelay on vocals". The music predelays are set per place, not per instrument, so the drums and pads in one room share a predelay.

### Vocal plate settings

**Checked:** `my` renders with `to: 'vox'` (L580–612), so `put` routes its `rev` and `dly` (defaults 0.3 and 0.2) to VR and VD (L119). The voice is high-passed at 170 Hz. VD runs through its own `pingpong`, and that echo feeds VR at 0.3. VR then runs through `freeverb` with `VOX_PLATE = { room: 0.8, damp: 0.18, gain: 0.015, predelay: 0.03 }` (L2175–2178). Size, width and the 180 Hz send high-pass stay at their defaults. Both returns join the output at the music returns' levels and with their kick duck (plate ×2.6, echo ×0.55). They bypass the place tilt and the breath cut (L2227), so the plate and echo "ring through the breath" (comment L2173) at beats 119–120, after the music stops.

**Checked:** the plate's formula RT60 is 0.9673 s (`score-events.json` `voxPlate`, L2497), computed by `rt60` from `room` 0.8 and the default size, not measured. It is shorter than every music room except exec (0.5018 s) and the reveal (0.8222 s). Its damping of 0.18 is among the brightest: only design (0.12) and the lock (0.16) damp less, and the second drop matches it.

### Ping-pong delay internals

**Checked:** `pingpong` (L782–799) takes the mono sum `(L+R)/2` through a 260 Hz high-pass into two delay lines, each `ENGINE.ECHO.gap` = 0.75 beat long (375 ms at 120 BPM; `engine.js` L115). The left line takes the input plus 0.45 × the right output through a 4.2 kHz low-pass. The right line takes the left output through a 4.6 kHz low-pass. The first echo sounds on the left at 0.75 beat and the second on the right at 1.5 beats at about the same level. Each later left–right pair is 0.45 (about −7 dB) of the one before, and darker.

- Resets: the music delay is cleared at the pre-drop gap and at the tape-stop restart, and it slows with the tape (L2133–2137). The vocal delay is cleared only at the gap.
- Returns: both delay returns enter the output at ×0.55, ducked by `1 − 0.3·(1 − DUCK)` (L2222), and feed their reverb at 0.3.
- Tempo: SLASH_MY's tempo is fixed at 120 BPM, so one delay time serves the whole film.

**Reported:** commit `683c2215` concerns the throw at beat 39.5, which had sent the swung copy of the note, 135 ms behind the grid. After the change, "on the grid (40.25 + 0.75k) the four echoes now sit +12/+16/+13/+3 dB over the bed before the throw, were -2/+2/+1/-8". Swing itself is covered in [selective swing](../knowledge/Groove%20and%20feel.md#selective-swing).

### Delay throws: list and timing

**Checked:** the throw beats are listed in `ENGINE.ECHO.at` (`engine.js` L115) and become `THROWS` in `audio.js` (L905). `thr(b, d, to)` (L907) returns the throw send `to` on a throw beat and the ordinary send `d` otherwise, and records the beat as a throw in `score-events.json`. `engine.js` refuses to load a score whose throws differ from `ECHO.at` (L245–246).

| Beat | Section | Thrown voice | Ordinary → throw `dly` | Line |
| --- | --- | --- | --- | --- |
| 23.5 | brand | pluck | 0.3 → 0.9, both ×2.5 | L1126 |
| 39.5 | exec | pluck, the canon's on-beat left copy | 0.1 → 0.9, both ×2.5 | L1080 |
| 47.5 | exec | pluck | 0.35 → 0.9, both ×2.5 | L1065 |
| 63.5 | design | supersaw stab | 0.12 → 1.5 | L1155 |
| 83, 91 | writing | keys, top voice | 0.16 → 0.8 | L1218 |
| 98.75, 102.75 | nav | mallet (note 0.23 instead of 0.2) | 0.15 → 1.1 | L1291 |

Two changes around a throw make room for its echoes:

- **The dry note is cut** (`THROW_END = 0.6`, L906; call L1216–1218). Writing's thrown top notes hold for 0.5 beat less 20 ms, then fall 20 dB over 0.1 beat (release rate `ln 10 / 0.1 beat`). By 0.6 beat they are 20 dB down, and they are still falling when the first echo arrives at 0.75 beat. An ordinary top note holds 4–6 sixteenths × 0.95, past the point where that echo would land. The other throws are not shortened: the design stab already lasts 0.7 of a sixteenth, and the plucks and mallet decay as struck sounds.
- **The bed steps back** (`THROW_DB = { nav: 6, other: 4 }`, L906; applied in the throw-window block L1830–1840): from just before the first echo to just past the fourth, the bed above 300 Hz drops 4 dB (6 dB in nav). The window and its ramps are in [delay-throw carve](../knowledge/Dynamics%20and%20spectral%20carving.md#delay-throw-carve).

**Reported:** `683c2215` measured the 39.5 throw's four echoes at "+12/+16/+13/+3 dB over the bed before the throw". `cc2b0a26` reports the 63.5 throw's "first echo at ~-12" dB under its note.

**Source status: practice:** the ledger lists "delay throws timed into gaps" as common practice with no authoritative source ([audio source ledger](../sources/Audio%20sources.md#practice-without-a-source)).

### Low-end routing

**Checked (SLASH_MY):** `kick` (L300–316), `bassNote` (L387–397) and `bassLine` (L715–732) call `put` with pan 0 and no `rev` or `dly`. The impact renderer adds its tuned sub after the impact's own baked room, at pan 0 (`sfx.js` L1476–1492). Every send that reaches a room is high-passed at 180 Hz or above, and the delay's input at 260 Hz. Pitched voices also carry their own 140–170 Hz high-pass.

**Checked (AX DAY reconstruction):** the kick, the offbeat bass, the drop's falling sub and the countdown thump are centered and send nothing. Three low parts do reach the reverb, which has no high-pass: the opening drone (root A2, 110 Hz) sends 0.5, the drop chord (root A2) 0.6, and the closing 55 Hz note 0.3 (L45–50, L166, L176). Damping shortens only the top, so their lows ring for the full computed ≈1.36 s. The reconstruction's master has no mid/side stage.

### Mono-sum candidates: the doubles

**Checked:** SLASH_MY's `dbl` (`DBL` L402, used at L406) adds a dry copy of the supersaw at the opposite pan: 12 ms late, 7 cents sharp, with 1.4× the detune. Exec's stabs use it at 0.35 (L1059–1060). The vocal's double (8 ms, +7 cents) and its stack, panned in opposite pairs at ±0.45 and ±0.8, are built the same way.

**Interpretation:** summed to mono, a copy 12 ms late can comb-filter. Its detune and independent phases should keep any notches moving. No mono fold of these passages has been rendered or measured.

## Groove and feel

Technique page: [groove and feel](../knowledge/Groove%20and%20feel.md).

The AX DAY reconstruction has no swing and no timing jitter on its drums or synths. Every musical note sits exactly on `b * B`. Only the reconstruction's typing is randomized. The swing and jitter note counts below come from a run of SLASH_MY's arrangement with every `sw` and `humT` call logged. That instrumented copy is not in the repository.

### Selective swing: `swAmt` and `sw`

**Checked:** `swAmt(b)` returns the section's amount. `sw(b)` moves a beat position that falls on an odd sixteenth later by `(swAmt − 0.5) × 0.5` beat and returns every other position unchanged. This follows the Linn convention: at 0.5 the off-sixteenth sits halfway through its eighth, and at 0.667 it sits on the triplet. A line swings only if it calls `sw`, so the section sets the amount and each line opts in. In writing the amount drifts by beat: `lerp(0.57, 0.61, (b − 76) / 16)` before beat 92, then 0.56. Jitter, where a line has it, is added after swing (`humT(sw(b))`). `sw` moves only positions within 1e-6 of an odd sixteenth, so quintuplets and 32nds pass through unchanged.

| Section (beats) | `swAmt` | Odd-sixteenth delay | Lines that call `sw` (notes moved / notes) |
| --- | --- | --- | --- |
| intro 0–16, brand 16–24, design 56–76, build 104–112 | 0.5 | 0 | none move |
| exec 24–56 | 0.54 | 10 ms | closed hats 49/102, stabs 3/28, deputy-response plucks 4/6, space-race canon plucks 10/20, tightloop acid 12/24, bass 16/48 |
| writing 76–92 | 0.57 → 0.61 | 17.5 → 27.5 ms | kick syncopations 5/14 (20.5–27.0 ms), round bass 5/15, ghost snares 8/8 (21.1–27.3 ms), rims 7/11, the gayageum at 90.25 (26.4 ms) |
| writing, under the debrief 92–96 | 0.56 | 15 ms | no line calls `sw` |
| nav 96–104 | 0.54 | 10 ms | congas 7/11, closed hats 16/32; bar 25's stabs call `sw` but sit on even steps |
| reveal 112–136 | 0.54 | 10 ms | closed hats 29/58, stabs 8/21, rolling bass 30/45, sparkle arp 16/16 |

Lines that stay straight include claps, snare backbeats and fills, the lead, open hats, the vocal, the brand bass (`brand ? b : sw(b)`, L1110), nav's kick, clave, mallet hook and bass, and the writing keys. The keys play a cinquillo on steps 0, 4, 6, 10 and 12 and never call `sw`.

#### Writing's swung kick

Writing's kick is swung only off the beat. Its bars alternate `kickA` `X.....x...x.....` (all even steps), `kickB` `X..x......x..x..` and, in bar 21, `kickC` `X.....x...x..x..` (patterns L225). `K(sw(b), …)` (L1226) leaves the downbeats and even steps alone and pushes steps 3 and 13 late, by 20.5, 22.0, 24.5, 25.5 and 27.0 ms across bars 20–22. score-events.json's kick list shows them at beats 80.7909, 83.2941, 87.2991, 88.8009 and 91.3041. The four bars' patterns hold 15 kicks, but bar 19 is the fade-in and its kick skips the downbeat at 76 (`if (!fadeIn || b >= 77.5)`, L1226), so 14 play and 5 of them move. score-events.json lists 14 kicks from 76 to 92, the first at 77.5. The round bass reads the same swung positions (L1237–1238), so it stays with the kick. It has no fade-in skip and plays all 15 notes, 76 included.

**Comment versus code**: the comment at L1224 describes this ("the kick's downbeats straight, its syncopations late"). The comment at L882–883 names only "hats, bass and stabs" and says kicks "on the beat" stay straight, so the code swings more lines than that comment lists.

#### The 0.56 after beat 92 never takes effect

**Checked:** `swAmt` returns 0.56 from beat 92 to 96, but no line in that window calls `sw`. The debrief's kick, clap, open hats, snare build, shaker and bass are all straight. The "lighter under debrief" swing in the L886 comment does not happen in the render.

#### In the code

- SLASH_MY: `audio.js` `swAmt` L884–888 and `sw` L889. Callers: exec L1043, L1054, L1063, L1078, L1094, L1110; writing L1226, L1229, L1230, L1237–1238, L1272; nav L1294, L1295, L1297; reveal L1412, L1419, L1461, L1492. Section bounds come from `timeline.js` L33–41.
- AX DAY reconstruction: absent. There is no swing function, and every musical note is placed at `b * B`.

**Source status: supported:** Roger Linn: 50% is straight, 66% a triplet, and the useful range is about 50–70% ([excerpt](../sources/excerpts/roger-linn-swing-range.md)). SLASH_MY's amounts, 0.54–0.61, fall inside that range. Its 10 ms delay in exec, nav and reveal is above the ~6 ms timing JND that Friberg & Sundberg give for sixteenths at 120 BPM. [Musical development](../../video-knowhow-craft/knowledge/Musical%20development.md) notes the writing section's pairing of half-time and swing.

### Velocity curve and accents

**Checked:** SLASH_MY's closed-hat sixteenth lines take their weight from `vel = (acc ? 1 : [0.72, 0.42, 0.6, 0.48][s % 4]) × (0.93 + 0.07 × s / 15) × (1 + hum(0.05))`, with `s` the step 0–15 and `acc` an upper-case step in the pattern. The line's base gain (0.13–0.15) multiplies the result.

| Position | Factor | Relative to an accent |
| --- | --- | --- |
| accent (upper-case step) | 1 | 0 dB |
| beat (step mod 4 = 0) | 0.72 | −2.9 dB |
| first sixteenth, "e" (1) | 0.42 | −7.5 dB |
| offbeat eighth, "&" (2) | 0.6 | −4.4 dB |
| last sixteenth, "a" (3) | 0.48 | −6.4 dB |
| bar lift, step 0 → 15 | 0.93 → 1.0 | +0.63 dB |
| seeded spread | 1 ± 0.05 | about ±0.4 dB |

Brand's bar 5, exec and reveal use `XxxXxxXxXxxXxxXx`, which accents steps 0, 3, 6, 8, 11 and 14, the hook's 3-3-2. Nav and the second half of design use `xxXxxxXxxxXxxxXx`, which accents the offbeat eighths. Brand's bar 5 also fades in under `lerp(0.5, 1, (b − 20) / 4)`. Open hats, the build hats and the rims take fixed or ramped gains, not `vel`.

Other accented lines in SLASH_MY:

- Exec stabs (L1055): step 0 at 1, the others at `0.86 + 0.06 × s / 16 + hum(0.03)`, which gives a downbeat accent and a lift.
- Writing keys (L1201): a fixed contour across the five cinquillo hits, `[0.95, 0.6, 0.78, 0.62, 0.82]`, each with ±5% spread (L1213).
- Phrase-end clap flam (`clapAt` L908–911): on bars 9, 13, 17 and 31 (`PHRASE_END` L898), a second clap sounds 22 ms ahead at 0.45× the gain, panned −0.12.

The AX DAY reconstruction accents only the offbeat (L68–73). Beats 16–24 carry open hats on the offbeats at 0.35. From beat 24 to the gap, closed hats run in sixteenths at 0.18, with the offbeat eighth at 0.35 (+5.8 dB). It has no further hierarchy by position, no lift, no spread, and a fixed hat pan of 0.25. Its snare backbeats all play at 0.5.

**Reported (commit):** according to commit `71791016` ("score tier 2"), the curve entered together with per-section swing, clap flams and the hook-step typing accents, so no record isolates the curve's effect from theirs.

### Timing jitter: `humT` ranges

**Checked:** `humT(b, a = 0.0025) = bt(b) + hum(a)` (L833), and `hum(a) = (rHum() × 2 − 1) × a` (L33), a uniform offset within ±a seconds, drawn independently for each call. At ±2.5 ms the standard deviation is 2.5/√3 ≈ 1.44 ms. In the logged arrangement, 403 `humT` calls had a standard deviation of 1.42 ms.

| Range | Lines |
| --- | --- |
| ±2.5 ms | intro open hats (L986); brand open hats and bar-5 closed hats (L1016–1017); exec closed and open hats (L1043–1044); writing rims (L1230); debrief open hats (L1245); the rim at 95.5 (L1278); nav rims (L1284), mallet hook (L1291), congas (L1294) and hats (L1295); build hats (L1350); reveal hats, open hats and rims (L1412, L1413, L1442) |
| ±1 ms | tightloop quintuplet hats (L1085); design hats (L1148) |
| ±4 ms | debrief shaker (L1251) |

Some lines take other offsets. Writing's ghost snares sit 8 ± 3 ms behind their swung positions (L1229). The keys' three chord notes land 0–2, 6–8 and 12–14 ms late by voice (L1213), and their top voice 20–22 ms late (L1218). The clap's internal bursts sit at 0, 11 ± 2, 21 ± 2 and 30 ms (L319).

Kicks, claps, snares (backbeats, fills and rolls), bass, stabs, the lead and plucks have no timing jitter. Kicks vary per hit in tone instead: pitch × (1 ± 0.012) and a click centered between 3600 and 4600 Hz (L302). The AX DAY reconstruction's drums and synths have no timing jitter.

**Source status: supported:** Friberg & Sundberg's ~6 ms JND ([excerpt](../sources/excerpts/microtiming-danielsen-hennig.md)) was measured for one displaced tone in an otherwise regular sequence. Hennig et al. 2011 tested white-noise and 1/f humanizing at σ 15 ms, about ten times SLASH_MY's 1.44 ms. **Interpretation:** the JND does not address a small offset on every hit, and Hennig et al. say nothing about deviations as small as SLASH_MY's.

### Laid-back snare: the writing bar loop

**Checked:** in writing, bars 19–22 (beats 76–92), `snare(bt(b) + 0.015, fadeIn ? 0.26 : 0.32, { tone: 175, dec: 11, rev: 0.3 })` (L1227) plays on the pattern `........X.......`, with no jitter. Ghost notes (L1229) fall on odd steps: bar 20 on 7 and 15, bar 21 on 7, 13 and 15, bar 22 on 5, 7 and 15. Each is swung with the section, by 21.1 ms at beat 81.75 rising to 27.3 ms at 91.75, then moved 8 ± 3 ms later, so the ghosts land 26–38 ms behind the grid. They play at 0.075 on step 7 and 0.055 elsewhere, 12.6 and 15.3 dB under the backbeat, with a longer decay (`dec` 20), a 2600 Hz low-pass and less reverb (0.12). The keys strum their three chord notes 6 ms apart, and each lands a further 0–2 ms late (L1213). The top voice, the augmented hook, lands 20–22 ms late (L1218).

| Hit | Offset from the grid |
| --- | --- |
| backbeat snare (step 8) | +15 ms, fixed |
| ghost snares (odd steps) | swing 21.1–27.3 ms, then +8 ± 3 ms: 26–38 ms in all |
| key chord notes | 0, 6, 12 ms by voice, each +0–2 ms |
| key top voice | +20–22 ms |
| kick downbeats, even-step kicks | 0 |
| kicks on steps 3 and 13 | swing 20.5–27.0 ms |

In the code:

- SLASH_MY: `audio.js` writing bar loop L1196–1240; snare L1227, ghosts L1228–1229, keys L1213 and L1218.
- AX DAY reconstruction: absent. Its backbeats sit exactly on beats 17, 19, 21, 23, 25 and 27 (L82).

**Source status: supported:** Danielsen et al. (computed from Table I): at 96 BPM, laid-back snare strokes averaged 17.4 ms behind the click across 10 drummers (individual means −4 to +43 ms), about 29 ms later than their own on-beat strokes. SLASH_MY's 15 ms, at 120 BPM, is near that mean and inside the drummers' range. The kick's downbeats sit at 0 ms, so the snare trails SLASH_MY's own on-beat hits by about 15 ms, half the drummers' 29 ms. Against Friberg & Sundberg's figures, 15 ms is above the ~6 ms JND for sixteenths and near the ~12 ms for quarters.

### Snare rolls: subdivision, gain and tuning

**Checked:** the AX DAY reconstruction steps its own beat counter: 0.5 beat before beat 30, 0.25 before 31, then 0.125 until `GAP_START`. SLASH_MY writes the roll as patterns (`build.snare` `['....x...x.x.x.x.', 'xxxxxxxxxxxxxxx.']`, debrief `'........x.x.xxxx'`) and adds a second hit 0.125 beat after each sixteenth for the 32nds.

| | AX DAY reconstruction | SLASH_MY build | SLASH_MY debrief build |
| --- | --- | --- | --- |
| Beats | 28–31.625 | 105–111.625 | 94–95.875 |
| Subdivision | eighths from 28, sixteenths from 30, 32nds from 31 | quarter at 105, eighths 106–107.5, sixteenths from 108, 32nds from 110 | eighths 94–95, sixteenths from 95, 32nds from 95 |
| Hits | 14 | 27 | 10 |
| Gain | `0.15 + 0.4p`, p = (b − 28) / 3.75: 0.15 → 0.537 (+11 dB) | `lerp(0.12, 0.5, p²)`, p = (b − 104) / 7.75: 0.126 → 0.476 (+11.5 dB); the hits at 106 and 108–110.25, on roll-call blips, 2 dB down (`HOT_HITS`); each 32nd takes its sixteenth's gain without that cut, so 111.5 and 111.625 both play 0.476 | `lerp(0.15, 0.5, p)`, p = (b − 94) / 2: 0.15 → 0.477 (+10 dB); each 32nd reads p + 0.06, so the last sixteenth (95.75) plays 0.456 and the 32nd after it (95.875) 0.477 |
| Tuning | fixed (190 Hz body) | `expRamp(190, 400, p)`: 209 Hz at 105 → 390 Hz at 111.5; each 32nd 3% above its sixteenth, 402 Hz at 111.625 | `expRamp(180, 290, p)`, 32nds at p + 0.06: 180 Hz at 94 → 273 Hz at 95.75, 281 Hz on the 32nd at 95.875 |
| Under it | countdown "3" at 26, "2" at 28, "1" at 30 | kick quarters → eighths → sixteenths, sixteenth hats rising 0.04 → 0.12, bass | kick whose low-pass opens 300 → 2400 Hz |
| Then | silence 31.75–32, drop at 32 | silence 111.75–112, drop at 112 | nav at 96, no gap |

In the AX DAY reconstruction the roll starts on the countdown's "2", turns to sixteenths on "1" and to 32nds one beat before the gap. SLASH_MY's p² curve holds the build's level down early and spends most of its rise in the last two beats. The AX DAY reconstruction's rise is linear. Both stop one 32nd short of the gap: the AX DAY reconstruction's loop runs `while (b < T.GAP_START)`, and SLASH_MY's last pattern step is empty. SLASH_MY's two rolls derive their 32nds differently. In the build (L1348), each 32nd takes the gain of the sixteenth before it at the same p, without that sixteenth's `HOT_HITS` cut, and its tone × 1.03. The 32nds after the hot sixteenths at 110 and 110.25 therefore play 2 dB over them. In the debrief (L1249), each 32nd reads both curves at p + 0.06, close to its own place on them (p + 0.0625), so it plays 0.021 higher in gain (0.4–0.5 dB) and 2.9% higher in pitch than the sixteenth before it.

In the code:

- AX DAY reconstruction: `audio.js` snare L75–81, backbeats L82, roll L83–90; `timeline.js` `GAP_START` and `DROP` L48–49.
- SLASH_MY: `audio.js` build snare L1343–1349, kick L1341–1342, hats L1350, `HOT_HITS` L1329–1330, patterns L234–236; debrief snare L1246–1250; `timeline.js` `GAP_START` and `DROP` L127–128.

The reconstruction's sound analysis describes the AX DAY reconstruction's "accelerating roll, a hard 0.125-second silence".

### Typing: timing and per-key sound

**Checked (AX DAY reconstruction):**

- Times (`timeline.js` L24–33): starting at `TYPE_START` 0.9 s, each gap is `0.055 + r() × 0.05` s, plus 0.06 s after a space, from `rng(7)`. Computed from the code: 27 keys, gaps 55.6–158.9 ms (mean 87.6 ms), last key at 3.177 s. The Enter sound plays at `ENTER − 0.08` = 3.92 s (beat 8 is 4.0 s), about 0.74 s after the last key. The keys are off the beat grid. The picture reads the same `T.keyTimes` (`index.html` L149, L163).
- Per key (`audio.js` L52–56): gain 0.25–0.40 (a range of about 4.1 dB), a sine at 1800–3200 Hz over high-passed noise (the noise minus its 2500 Hz low-pass), decaying as `exp(−160u)` over 50 ms, panned within ±0.2, with a 0.15 reverb send. All of it comes from the single stream `rnd`.

**Checked (SLASH_MY):**

- Complaint lines 1–4 (`timeline.js` L81–92): each gap is `0.045 + r() × 0.04` s, plus 0.04 s after a space, from `rng(7)`. A line is compressed by a factor `k ≤ 1` so it finishes 0.4 beat before the next line starts (L83–85). Line 1 pauses after its first word and rattles out the rest (`HOLD` L69).
- Line 5 (`HOOK_TYPING` L60–65) is typed on the hook steps in 32nds, and the first key on each step is an accent.
- Per key (`sfx.js` `keyClick` L605–622, `renderKey` L548). Cap constants come from `rngOf('keycap', key.name)`, so a given key always sounds like the same cap. Each stroke varies through `rngOf('keystroke', seed)`, where the seed is the key's time. Weight varies ±1.5 dB through `rngOf('keyvel', seed)` and is ×1.25 (+1.9 dB) on accent keys. A second call at the same time becomes a second press 4 ms later with its own seed. A call with `g < 1` is also darker: a 3500 Hz high shelf cuts by `5 × log10(g)` dB, at most 6 dB.
- Intro placement (`audio.js` L912–921): pan runs −0.45 → +0.45 along the line, and `keyClick` scales it by 0.6, to ±0.27. Accent keys are doubled and carry the hook's note as a short pitched tick.
- Pain keys (`audio.js` L1611–1621) are timed from beat positions, under `PAIN_KEY = { g: 0.65, jit: 0.0015, vel: 2 }`. A step's first key lands 0 to +1.5 ms late, never early. Later keys land within ±1.5 ms. Weight varies ±2 dB, and pan runs −0.4 → +0.4 along the line (±0.24 after scaling). Each key draws from its own stream, `T.rng(9000 + Math.round(k.b × 1000) + k.i)`.

### Seeded random streams

Every random value in both soundtracks comes from a seeded generator, so a render with unchanged code produces the same samples. SLASH_MY splits its draws across several seeded streams so that editing one part does not re-roll the others, and the AX DAY reconstruction seeds its typing times and its audio separately. **Interpretation:** with the draws fixed, a render that changes after an edit points to that edit, and a render that stays the same after a refactor confirms that the refactor changed no sound.

**Checked:** both timelines define `rng(seed)`, a mulberry32 generator (SLASH_MY `timeline.js` L11–20; AX DAY reconstruction `timeline.js` L14–23). Both seed the typing times with `rng(7)`.

SLASH_MY divides its draws into four kinds of stream:

| Kind | Streams | What they feed |
| --- | --- | --- |
| Shared, by purpose (`audio.js` L30–33, "Separate seeded streams, so editing one part does not reshuffle the others") | `rNoise` 101, `rHum` 202, `rPh` 303, `rDbl` 505 | noise; humanizing (`hum`, `humT`, `vel`); oscillator phases; doubles |
| Own stream per later part | room tone `rT` 404 (L961, "own stream: the rest re-roll nothing"), vocal stack `rStack` 606 (L536), wait bass `rWait` 707 (L1037) | that part only |
| Keyed per event | pain keys `T.rng(9000 + round(b × 1000) + i)` (L1619); sound effects `rngOf(...k) = T.rng(fnv(k.join('|')))` (`sfx.js` L149–150), FNV-1a of a name and a beat, key or seed, at about 40 call sites | one event; depends only on its key |
| Timeline | `rng(7)` for typing | key times, shared with the picture |

Within a shared stream, a value depends on draw order. SLASH_MY draws in the arrangement code first, then runs the queued closures in push order (`for (const fn of Q) fn()`, L1696), then renders the kicks (L1697), and the wait kicks last (L1698, "their seeded draws (rNoise, rHum) reshuffle nothing else"). Adding a draw early in a shared stream shifts every later draw on it. Where writing's click layer was removed, its draws are kept as dummy calls (`hitsOf('x.xx.xx.x.xx.xx.').forEach(() => hum(0.003))`, L1233) "so everything scored after it is unchanged". A keyed event re-rolls only when its key changes, as when its beat moves.

The AX DAY reconstruction's audio uses one stream, `rnd = T.rng(2026)` (`audio.js` L12), for per-sample noise (L27), key-click parameters (L53–55) and supersaw phases (L105), in code order. Its typing times come from the timeline's `rng(7)`. **Interpretation:** any added draw on `rnd` changes the noise and phases of everything rendered after it. The file then differs even where the music did not change. This has not been tested.

**Reported (commit):** from SLASH_MY's commit messages:

- `46c985eb`, a refactor in which audio.js reads a value from reveal.js: "score.wav sample-identical".
- `31d73916`, a change to the end release: "score.wav SHA-1 25eac6cf -> 32213b3a, byte-identical up to 135.9169".
- `b0ab2eff`, a room-tone change: "score.wav changes only under the room tone (beats 0-5.9, a new noise draw; below -130 dBFS elsewhere)". The difference elsewhere was below −130 dBFS, not zero.

**Interpretation:** these comparisons were made between renders on one setup. Seeds fix the random draws. They do not fix floating-point results from `Math.sin`, `Math.exp` and similar functions under a different JavaScript engine version (untested). Pin the Node version when a byte-identical file matters. For encoded deliverables, see [measuring the encoded file at the mux](../knowledge/Mastering%20and%20delivery.md#measuring-the-encoded-file-at-the-mux) and [Deterministic rendering](../knowledge/Deterministic%20rendering.md).

With no ledger source on seeding, this section draws only on the code and the commits.

When it fails, inspect:

- An unrelated part that changed after an edit: the edit added or removed draws on a shared stream ahead of it. Give the new part its own stream, as the room tone, vocal stack and wait bass have, or keep the removed draws as dummies.
- A sound effect that changed when it moved: keyed streams include the beat, so moving a cue re-rolls it.
- A file that differs on another machine with no code change: compare Node versions before suspecting the seeds.
- Locating a change: hash score.wav, then find the first differing sample and its level, as `31d73916` reports.

### Parameter automation already in the scores

SLASH_MY moves some parameters across a section: the writing swing drifts from 0.57 to 0.61, exec's stab cutoff sweeps (`expRamp(1700, 2400, …)` in its first slot, `expRamp(2200, 5500, …)` in its last, L1057), the build ramps gains and tuning, and hats sweep across the stereo field once a bar (`autoPan`). Most of its loops still repeat their pattern gains bar to bar, apart from the seeded spread. The AX DAY reconstruction raises its offbeat stabs' cutoff by 150 Hz a beat (`1800 + (b − 16) × 150`, L121), but its hats and bass repeat identical gains every bar.

## Mastering and delivery

Technique page: [mastering and delivery](../knowledge/Mastering%20and%20delivery.md).

### The two master chains in full

| Stage | AX DAY reconstruction | SLASH_MY |
| --- | --- | --- |
| Input | dry mix + reverb return ×3 | mix × `MASTER_GAIN` 0.6 (about −4.4 dB) |
| Stereo | none | side high-passed at 120 Hz; side gain per place (`WIDTH`) |
| Tone and DC | none | about +1.5 dB above ~10 kHz; 12 Hz DC blocker |
| Bus compression | none | 1.6:1, 30 ms / 250 ms, stereo-linked |
| Level automation | none | section `ARC` in dB, after the compressor |
| Clip | `tanh(1.1x)` on every sample, no oversampling | clip-room steps, then a 4× `tanh` knee and a hard second pass at −0.5 dBFS |
| Limiter | none | 4× true-peak look-ahead limiter at −2 dBFS |
| Level setting | sample peak normalized to 0.89 (about −1.0 dBFS) | trim to −14 LUFS by its own BS.1770-4 meter |
| Pre-drop gap | linear 5 ms down, no ramp back | half-cosine 5 ms down and up, digital zero between |
| End | linear fade over the last 2 beats | `T.END.gain`: x² release, then a half-cosine to zero one frame early |
| WAV | 16-bit, 44.1 kHz, rounded, no dither | 24-bit, 48 kHz, TPDF dither before rounding (`f7f9d199`) |
| Encode | native AAC 256k, unmeasured | AAC 320k, measured, re-encoded until in spec, gated at the mux |

### Mid/side width stage in SLASH_MY

**Checked:** `mid = (l + r) / 2` and `side = (l − r) / 2`. The side passes through two cascaded state-variable high-passes at 120 Hz, Q 0.707 (fourth order, about −6 dB at 120 Hz). The filtered side is scaled by `1 + kw`, where `kw = 10^(all/20) − 1`, and in writing a 1–6 kHz band of the side (high-pass 1 kHz into low-pass 6 kHz) is added at `km = 10^(3/20) − 1`. Both targets glide to each place's value with a 50 ms one-pole. Left and right are rebuilt as `mid ± side`. The same block then adds `0.19 × high-pass(10 kHz, Q 0.6)` per channel (about +1.5 dB of air) and runs a 12 Hz DC blocker.

In the code: `audio.js` `MASTER_GAIN` L2244, `EXEC_WIDTH`, `WAIT_WIDTH`, `DESIGN_WIDTH` L2250, `WIDTH` L2251, the M/S, air and DC block L2254–2275. The check is qa audio's per-section stereo table (L115–141): it flags a section whose low end under 120 Hz correlates below 0.9 or loses more than 1 dB when summed to mono. The AX DAY reconstruction has no master stereo stage; its low end is as mono as its sources and reverb returns make it, and nothing at the master enforces it.

Width by place (SLASH_MY, dB on the side above 120 Hz):

| Place | All of the side | Side 1–6 kHz |
| --- | --- | --- |
| intro, brand | 0 | 0 |
| exec, one step per slot | 0, +0.3, +1.6, +2.5 | 0 |
| tightloop's wait (from a quarter beat after `TIGHT.beat` to the slam) | −8 | 0 |
| design | +2 | 0 |
| writing | 0 | +3 |
| nav to the end | 0 | 0 |

The reveal's width comes from its arrangement, and the master leaves its side at unity.

**Reported (run notes):** from the audio run notes' "Measured" section at `fd543f2a`, side over mid per half second, exec by slot −16.7, −15.6, −15.1, −14.9 dB; grounding −14.1; drop −11.0, wall −10.8, second drop −9.0, lock −8.4. Over the whole film the side below 120 Hz sits 32 dB under the mid, and qa audio flags no section.

### Bus compressor in SLASH_MY

**Checked:** `compress` follows the per-sample stereo magnitude `√((L² + R²)/2)` with a one-pole envelope, so both channels get the same gain. The option is named `'rms'`, but it follows magnitude, not averaged power. Gain reduction has a quadratic soft knee: zero below `−knee/2` dB over threshold, `(1 − 1/ratio) × (over + knee/2)² / (2 × knee)` inside the knee, and `over × (1 − 1/ratio)` above it. The compressor sits before the trim, so its threshold is relative to the pre-trim mix. A change in `MASTER_GAIN` or in the mix level changes how hard it works, and the trim then restores the delivered loudness.

In the code: `audio.js` `compress` L2068–2084 (shared with the drum bus); the bus call `busGR` L2276. The log prints its gain reduction (max and average) at L2649. The AX DAY reconstruction has none; its `tanh` is the only stage that acts on level.

Values: threshold 0.28 (about −11 dBFS on the mix after `MASTER_GAIN` and the width stage), ratio 1.6, attack 30 ms, release 250 ms, knee 8 dB, makeup 1. No commit or note records the bus compressor's gain reduction at the snapshot.

The ledger's worked example (Sound On Sound's review of Cytomic The Glue) uses 2:1, 10 ms attack, auto release and about 2 dB of gain reduction.

### Section arc in SLASH_MY

**Checked:** `ARC` is a list of `[beat, dB]` points. Gain is linear in dB between points and applied per sample, after the bus compressor. Every point before beat 112 takes a further `BODY_DB` (−1.2 dB), so the body sits under the reveal by that much more without moving the points inside the reveal. Exec's steps are each taken in the quarter beat before their slot.

In the code: `audio.js` `EXEC_ARC` L2298, the named constants L2299, `ARC` L2300, the gain loop L2309–2317. The AX DAY reconstruction has none; its only level automation is the end fade.

Arc values (dB as written; before 112 each sits a further 1.2 dB down):

| Place (beats) | Arc |
| --- | --- |
| intro (0–14) | 0 |
| brand (16–22) | −4.85 |
| exec slots | −6.40, −5.50, −3.85, −4.00 |
| design (56–75.5) | −3.5 |
| writing (76–96) | −6.6, −7.4 from 84, −7.7 at 92, −7.4 at 96 |
| nav | climbing to −5.1 at 103.75 |
| build | −4 at 104, −3.2, −2.2, −2 from 108 to 111, −1.6 at 111.75 |
| drop (112) | −1.5 |
| wall | −3 |
| breath | −5.5 |
| second drop | −4, then 1 dB down by 121, 2 dB more over 122–122.75, 2.5 dB more in the stop at 123.5–124 |
| lock | −4.5 |
| outro | −6.2 |

**Reported (run notes):** from the audio run notes' "Measured" section at `fd543f2a`, section loudness intro −16.3 LUFS, brand −14.1, exec −14.1, design −14.3, writing −16.9, nav −14.6, build −13.4, drop −10.0, wall −10.6, second drop −11.8, lock −11.6, outro −14.1. The reveal (112–128) sits 2.9 LU over exec and the drop 4.1 LU over it; the second drop sits 1.7 LU under 112 (3 s short-term). Commit `e0cce02b` reports that the terraced `EXEC_ARC` steps exec's slams (loudest 400 ms) by +2.2, +1.0 and +1.1 dB. Commit `52f64c5e` reports that the build's arc halves the limiting on its opening hit at 104 (2.05 to 1.04 dB).

### Soft clip and true-peak limiter internals in SLASH_MY

**Checked:**

- The clip works at 4×. For samples near the knee, three in-between points are interpolated with a 32-tap Hann-windowed sinc. Above the knee `t` each point is bent to `y = t + (c − t)·tanh((|u| − t)/(c − t))`, which approaches `c` and never passes it. Only the correction (the bent point less the original) is kept, and it comes back to 48 kHz through a 97-tap Hann-windowed sinc low-pass at 20 kHz. A second pass, hard at `c`, catches what the low-pass gave back. Stretches well under the knee (below 0.67 of it) are skipped. `clipCorr`, the clipped signal less the unclipped one, is kept for the clip room.
- The limiter estimates each sample's true peak at 4× with the same interpolator wherever a sample reaches half the ceiling. It computes the gain needed to bring that peak to the ceiling, takes the minimum of that gain over ±3 ms, and box-averages the result over ±3 ms. Gain therefore starts falling 6 ms before a peak and reaches the full reduction on it. Release is a one-pole at 80 ms, and the applied gain never exceeds the box average.
- After the pre-drop gap and the end release, both channels are clamped to ±`CEIL`.

In the code: `audio.js` `CEIL` L2348, `MCLIP` and `MCLIP_KNEE` L2375, `master` L2381–2484 (interpolator and clip L2389–2433, true-peak estimate and limiter L2434–2468, end release, gap and clamp L2469–2483). AX DAY reconstruction: `tanh(1.1x)` on the summed mix at the sample rate, with no oversampling and no limiter (`audio.js` L209).

Values: limiter ceiling `CEIL` −2 dBFS; clip ceiling `MCLIP` 1.5 dB above it (−0.5 dBFS); knee at 0.7 of `MCLIP` (about −3.6 dBFS); look-ahead and averaging ±3 ms; release 80 ms.

**Reported (run notes):** from the audio run notes' "Measured" section at `fd543f2a`, limiter gain reduction max (average) in dB: intro 0.9 (0), brand 1.1 (0.05), exec 1.7 (0.05), design 1.9 (0.2), writing 0, nav 1.1 (0.05), build 1.5 (0.35), drop 1.7 (0.65), wall 1.6 (0.35), second drop 1.7 (0.2), lock 1.6 (0.2), outro 0.2 (0); on the reveal's hits 112–124 at most 1.75. Soft clip max in dB: exec, design and build 1.5, drop 2.3, wall 2.2, second drop 2.1, lock 1.2, outro 0. Commit `cc2b0a26` reports limiter gain reduction of at most 2.6 dB (average at most 0.8) with the 4× clip in place.

True peak of `score.wav`: ffmpeg's `ebur128` reads −1.97 dBTP, which its one-decimal summary prints as −2.0 (the audio run notes' "Measured" section, L32 at `ec61dcd9`). qa polish's meter reads −1.940 dBTP (commit `f7f9d199`, before dither and again after it; no audio commit lies between the snapshots). The sample peak sits on the −2 dBFS ceiling (−2.000 dBFS, commit `f7f9d199`), where the last clamp to ±`CEIL` holds it. True peak reads a few hundredths of a dB over it on both meters.

### Clip-room loop in SLASH_MY

SLASH_MY defined the −20 dB criterion for itself. No published standard or ledger source gives a floor for clip products per third octave.

**Checked:**

- **Onsets**: every onset `score-events.json` carries, plus every onset of the clip's own work (clip correction above 1e−4 after at least 30 ms without it).
- **Margin**: for each onset, over `[onset, onset + 50 ms]`, the energy of `clipCorr` (the clip's products, before the limiter) over the energy of the finished mix, in each of 26 third-octave bands from 39.4 Hz to 16 kHz (edges `1000 × 2^((k − 14)/3)` Hz; eighth-order Butterworth band-passes run forward and backward, padded up to 100 ms). The onset's margin is its worst band.
- **Steps**: a step lowers the whole mix from 5 ms before the clip's first sample in the onset's window to 10 ms after its last, and comes back over 40 ms, with smoothstep edges. Steps act on the mix as it reaches the master, after the arc and before the trim. Where whole-mix steps overlap, the deeper one holds.
- **Rounds**: each onset over the floor deepens its step (or opens one) by `0.25 dB × ceil(excess / 6 / 0.25)`, at least 0.25 dB. The 6 is the code's `slope`, the dB of margin a dB of step buys, which the comment reports measuring at 5–6. After each round only the onsets within 250 ms of a moved step are re-measured. When a set of rounds ends the trim is found again, since the steps cost a little loudness, and every onset is re-measured. Twelve rounds are the shared budget.
- **Set steps**: three steps are written in code (`CLIP_SET`) and apply before any round. All others are found at run time, so the list changes when the mix changes.

| Set step (beat) | What steps | Depth, hold, release | The code's reason |
| --- | --- | --- | --- |
| 115.61, the split's hop (simple-now's strike + `reveal.js` `SPLIT_AT`) | whole mix | 3 dB, 10 ms, 40 ms | its limiting stays under 112's, and the limiter's hold on the "my" under it shrinks |
| 112, the drop's front | whole mix | 2 dB, 40 ms, 40 ms | the span where the impact's crack and the kick drive the clip |
| 72, simple-now's slam | the band under 400 Hz only: the mix less (1 − 10^(−6/20)) of its zero-phase low-pass | 6 dB, 8 ms, 10 ms | the attack's lows drive the clip, and a whole-mix step held through the body would cost the slam its lead over its kicks |

In the code: `audio.js` `SPLIT_HOP` L2333, `CLIP_ROOM` L2335, `CLIP_SET` L2338, `CLIP_BANDS` L2511, `bandEnergy` L2524, `clipMargins` L2548, `applyRoom` L2575, `findTrim` L2591–2599, the rounds L2600–2621, the log line L2653; `lowZP` (zero-phase low-pass) L1732. The AX DAY reconstruction has none.

Values: floor −20 dB, window 50 ms, slope 6, step 0.25 dB, 12 rounds, attack 5 ms, hold 10 ms, release 40 ms.

**Checked:** by construction, the rounds run until every onset sits 20 dB or more under or the budget runs out.

**Reported (run notes):** in the audio run notes' "Measured" section, at the snapshot all 297 onsets sit 20 dB or more under. The closest are 108 (−20.4, 2–2.5 kHz), 42 (−20.5) and 69.5 (−20.6); 72 sits at −26.6, the drop's front at −22.4 (3.2–4 kHz), and the reveal's onsets from −21.0 (116) to −84.7. The found steps the notes list: 42 1.5 dB, 50 0.75, 75.5 0.75, 106 1, 108 1.5, 109 0.25, 110 1.25, 110.25 1, 110.5 0.75, 113 0.5, 115 1.5, 120.32 1.

**Reported:**

- Commit `fa866cb9`: before the floor applied, 299 onsets, the worst at −13.3 dB (beat 72) and 18 over −20; with it, the worst at −20.1 (beat 108) and none over.
- Commit `edd3024a`: with 72's band-only step in place of a whole-mix step, 72's first 100 ms stand 1.6 dB over its groove's kicks (0.0 before) and its margin goes from −20.6 to −26.6 dB.

### Loudness trim and its convergence in SLASH_MY

**Checked:** `loudness` is a BS.1770-4 integrated meter (K-weighting at 48 kHz, 400 ms blocks every 100 ms, absolute gate −70 LUFS, relative gate 10 LU under the mean). `findTrim` runs `master(trim)`, measures, scales the trim by the error, and repeats up to four passes or until the error is under 0.03 LU. The target is one value, `T.LUFS` in `timeline.js`, read by `audio.js` and `render.js`; qa audio's default restates it (commit `7341a174`).

In the code: `audio.js` `loudness` L2349–2369, `findTrim` L2591–2599; `timeline.js` `LUFS` L25. AX DAY reconstruction: `audio.js` L212 normalizes the sample peak to 0.89 (about −1.0 dBFS).

Values: target −14 LUFS integrated; tolerance 0.03 LU; four passes at most.

**Checked:** `findTrim` stops once the error is under 0.03 LU or after its fourth pass, whichever comes first, so the code alone does not guarantee that `score.wav` reaches the target.

**Reported:** at the snapshot the trim reached the target. For the same audio ffmpeg's `ebur128` reads −14.03 LUFS, −14.0 in its summary (the audio run notes' "Measured" section, L32 at `ec61dcd9`), and pyloudnorm −14.063 LUFS (commit `f7f9d199`, before and after dither). Master trim +6.3 dB (the audio run notes; commit `fa866cb9` gives 6.30 dB).

**Reported (run notes):** the audio run notes' "Measured" section (L32 at `ec61dcd9`) gives a loudness range of 5.6 LU (`ebur128`).

### Encode, measure and mux gate in SLASH_MY

**Checked:**

- `loudness(file)` runs ffmpeg's `ebur128=peak=true` on the decoded first audio stream and returns integrated loudness and true peak as its summary prints them, to one decimal.
- `masterAudio` measures `score.wav` (with `score-card.wav` joined in front when the warning card is on), sets a residual gain to the target, and encodes AAC at 320 kbit/s, 48 kHz stereo. A look-ahead limiter (`alimiter` at 192 kHz, attack 2 ms, release 80 ms) goes in only when the score's true peak plus that gain would cross the ceiling, which is the aim less the encoder's expected overshoot. It measures the encoded file and repeats, up to three passes, correcting the gain by the loudness error and the ceiling by any true-peak excess, until true peak is at most −1.2 dBTP and loudness is within 0.05 LU.
- `mux` stream-copies that AAC under the picture, measures the muxed file again, and stops with "audio is out of spec" if true peak is over −1 dBTP or loudness is more than 0.5 LU from the target.
- qa audio re-measures any file with the same `ebur128` summary; its report shows the one-decimal true peak with two decimals. On a muxed file it flags loudness more than 1 LU from the target or true peak over the maximum; on `score.wav` those are notes, since the mux normalizes.

In the code: `render.js` `TP_AIM` and the encoder choice L323–325, `loudness` L326, `masterAudio` L348–364, `mux` L366–374; `timeline.js` `TP_MAX` L27; qa audio's `ebur128` L31 and its flags L73–78. AX DAY reconstruction: `render.js` L37–39 encodes native AAC at 256 kbit/s with `-shortest`; nothing measures the result.

Values: delivery true-peak maximum −1 dBTP (`T.TP_MAX`); aim −1.2 dBTP; expected overshoot 0.3 dB for AudioToolbox (`aac_at`, CBR) and 1.2 dB for ffmpeg's native AAC. The code's comment reports that AudioToolbox overshoots about 0.1 dB and native AAC 1.1–1.7 dB, erratically. The master's own ceiling (−2 dBFS) sits 1 dB under the delivery maximum.

**Reported:**

- The audio run notes ("Master", `fd543f2a`): `render.js` "trims about 0 dB and its limiter does not engage".
- Commits `31d73916` and `b0ab2eff`, before the clip-room commits: the delivered AAC at −14 LUFS and −1.7 dBTP on `render.js`'s `ebur128` summary, against −2.00 dBTP in `score.wav` on qa audio, 0.3 dB of overshoot.
- Commit `f7f9d199`, at the current audio: the AAC from `render.js --audio-test` reads −14.08 LUFS on pyloudnorm, and true peak −1.743 dBTP before dither and −1.752 after on qa polish's meter, against that meter's −1.940 dBTP in `score.wav`.

The −14.08 LUFS is pyloudnorm's reading, not the loop's. `masterAudio` tests the one-decimal `ebur128` summary against its 0.05 LU tolerance, so the loop stops once that summary prints −14.0 with true peak under the aim. The commit does not report how many passes ran.

### WAV writers and dither

Cited at `f7f9d199` for SLASH_MY.

**Checked:**

- SLASH_MY: `audio.js` `writeWav` writes 24-bit, 48 kHz stereo as `round(x × 8388607 + d)`. `d` is TPDF dither of 2 LSB peak-to-peak: the sum of two uniform ±0.5 LSB draws, with no noise shaping. Each file draws from its own seeded stream (`DITHER`: `T.rng(808)` for `score.wav`, `T.rng(909)` for `score-card.wav`), four draws a frame whatever the sample holds. Other textures do not re-roll, and two renders are byte-identical. A sample that is exactly zero has no rounding error and is written as zero, so the gap and the last frame stay digital zero. The dithered word is clamped to the 24-bit range, so nothing wraps at full scale; `master` has already clamped to ±`CEIL`.
- SLASH_MY's encoder input: AudioToolbox's AAC (`aac_at`) takes only 16-bit PCM, and ffmpeg's own conversion to it rounds without dither. For that encoder, `render.js` `pcm16` decodes the joined, gained and limited score to float and cuts it to 16 bits the same way (`DITHER16`, `T.rng(1010)`, exact zeros kept, clamped, at ffmpeg's ×32768 scale). `scoreAudio` hands the encoder that raw file. ffmpeg's native AAC takes float, so nothing is cut there.
- AX DAY reconstruction: 16-bit, 44.1 kHz stereo as `Math.round(clamp(x × norm, −1, 1) × 32767)`, written to `intro_audio.wav` without dither.

In the code: SLASH_MY `audio.js` `DITHER` L2632 and `writeWav` L2633–2650; `score.wav` L2652; `score-card.wav` L2655; `render.js` the `aac_at` choice (`s16`) L324, `DITHER16` L344, `scoreAudio` L345–354, `pcm16` L355–368. AX DAY reconstruction `audio.js` L213–222.

Error scale (computed here, not measured): plain rounding leaves an error of about −149 dBFS rms at 24 bits and about −101 dBFS rms at 16 bits. With TPDF dither the total error is about −144.5 dBFS rms at 24 bits and −96.3 dBFS at 16 bits.

**Reported (commit):** commit `f7f9d199` reports that `score.wav` measures −14.063 LUFS integrated (pyloudnorm), −1.940 dBTP (qa polish's meter) and −2.000 dBFS sample peak with and without dither. The dithered words differ from the plainly rounded ones by 0.58 LSB rms (−143.3 dBFS), uncorrelated between left and right, and the gap stays 100% digital zero. The delivered AAC stays at −14.08 LUFS (pyloudnorm), with true peak −1.743 → −1.752 dBTP (qa polish's meter). Two `node audio.js` runs are byte-identical, and two `--audio-test` runs give identical audio md5.

### Room tone in SLASH_MY

**Checked:** white noise from its own seeded stream (`T.rng(404)`, separate so other textures do not re-roll) passes per channel through a state-variable low-pass at 1.8 kHz (Q 0.5) and a high-pass at 110 Hz (Q 0.6). The channels take alternate draws, so they are decorrelated. The card's part (`CARD`, `T.CARD_S` = 5 s) fades in over 0.5 s with a smoothstep and is written as `score-card.wav` at the gain SLASH_MY has at frame 0 (`MASTER_GAIN × trim × 10^(ARC[0]/20)`). SLASH_MY's part continues the same stream and filter state from the next sample. It is put with `fin: 0` (no fade-in), holds full level to beat 1, and fades as `1 − smoothstep((b − 1)/5)`, gone by beat 6 under the rising drone. `render.js` joins the two files with ffmpeg's `concat` ahead of the encode.

In the code: `audio.js` `ROOM` and the room tone L954–971; `put`'s `fin: 0` rule L118; `render.js` `scoreAudio`. The AX DAY reconstruction has none: its drone rises linearly from zero over 2.5 s (`audio.js` L45–50), so the file starts on digital zero, and the end fade reaches zero.

Values: gain 0.028 before the master; card fade-in 0.5 s; film fade from beat 1 to beat 6. The code comment and notes put the level at about −50 dBFS; commit `b0ab2eff` measured −52 dBFS rms per 250 ms.

**Reported:**

- Commit `b0ab2eff` (before dither): exact zeros in the first 4 s fall from 100% to 0.03% (the first millisecond). The sample step at the card's end (5.000 s) falls from 0.0067 to 0.00045, the 46th percentile of the local sample steps. The `concat` is bit-exact with card plus score, and the delivered AAC measures −14 LUFS and −1.7 dBTP.
- With dither (`f7f9d199`, reported in commit `a1ce562a`): the card's first millisecond, under half an LSB, carries the dither's ±1 LSB; exact zeros there fall from 99% to 65%, and the first nonzero sample moves from 47 to 3.

### Fades, the pre-drop gap and the end release

**Checked (SLASH_MY):**

- **Events**: `put` gives every event a raised-cosine fade-in (2 ms by default) and fade-out (4 ms). An event cut short by a cut in the arrangement (the tape stop, the gap, the breath) fades out at the cut. `fin: 0` means full level from the first sample; only the room tone uses it.
- **Sound effects**: `sfx.js` `finish` high-passes at 25 Hz, trims the tail where it falls 66 dB under the cue's peak, fades the new end over 8 ms with a half-cosine, fades in over 0.3 ms, and sets the cue's loudness. `play` adds 0.1 ms in and 2 ms out.
- **Pre-drop gap**: a 5 ms half-cosine down ending at beat 111.75, digital zero to 112, and a 5 ms half-cosine back up.
- **End release**: `T.END.gain` lowers the gain by `24 × x²` dB over the last two beats (`x` from 0 to 1), then a 0.05-beat half-cosine takes it to zero one frame before beat 136. `finish.js` `fadeGain` reads the same curve, so the last frame is black and the score silent under it.

In the code: `audio.js` `put` L107–135 (defaults L108–109), the end release and gap L2469–2483; `sfx.js` `finish` L377, `play` L392; `timeline.js` `END` L137–145; `finish.js` `fadeGain` L837–840.

AX DAY reconstruction: `put` (`audio.js` L17–25) has no edge ramps; each voice's own envelope shapes its edges. The gap's gate (L203–207) falls linearly to zero over 5 ms from beat 31.75 and holds zero until 32 (L207 also forces the last 2 ms to zero, which changes nothing), then jumps back to full at 32. The comment says "(5ms ramps)", but there is no ramp back. The end fades linearly over beats 46–48 (L208).

**Reported (commit):** according to commit `31d73916`, the tail crosses −60 dBFS at beat 135.92; frame 4079 is silent and black; −14.00 LUFS, −2.00 dBTP in qa, delivered −14 LUFS and −1.7 dBTP.

### The AX DAY reconstruction's master

`audio.js` master L196–222: the loop L199–211 sums the dry mix with the reverb return at ×3, applies `tanh(1.1x)` per channel, and multiplies by the gap gate and the end fade; `norm` L212 scales the sample peak to 0.89; the writer is L213–222. `render.js` L37–39 encodes native AAC at 256 kbit/s with `-shortest`. The reconstruction's sound analysis measures the decoded MP4 at about −14.3 LUFS integrated with a loudness range of 12.2 LU; true peak is not reported there.

### Further failure checks

These checks apply to SLASH_MY unless marked otherwise.

- A negative left/right correlation flag in qa audio's stereo table: something is out of polarity, often a wide double or a delay.
- A different master after a level change upstream: the bus compressor's threshold is absolute, so re-read its gain reduction whenever `MASTER_GAIN` or the mix level moves.
- An audible ramp in the section arc: two points too close together with a large step between them, outside a cut or a silence.
- Clip-room steps that keep moving between runs: they depend on every upstream change, so read them only against one snapshot of the mix.
- A sample over full scale: SLASH_MY's writers clamp the dithered word, so a gain applied after `master` (as for `score-card.wav`) clips at full scale rather than wrapping.
- The AX DAY reconstruction's gap holds digital zero, and its file starts and ends on zero.

### Notes behind the untested ideas

- An independent check for the AX DAY reconstruction would reuse SLASH_MY's `render.js` `masterAudio` and `mux` and qa audio, which measure with ffmpeg's `ebur128`.
- The reconstruction's sound analysis names playback loudness as the variable to match first when the two soundtracks are compared.
- qa audio checks mono safety under 120 Hz and left/right correlation, nothing else about playback systems. Neither SLASH_MY's drum-bus clip nor the AX DAY reconstruction's `tanh` has been checked for what survives on a small speaker. The ledger's small-speaker row says adding harmonics or distortion helps bass translate.

## Music under voice-over

Technique page: [music under voice-over](../knowledge/Music%20under%20voice-over.md). Neither soundtrack has speech, and none of this code has run under narration. The list below gives the SLASH_MY parts that page links to, with their places in the code.

### Carry-over code in SLASH_MY

- **Loudness meter.** `loudness` (L2349–2369) is a BS.1770-4 integrated meter. It runs only on the master, through `findTrim` (L2591–2599); nothing measures a stem alone. See [loudness trim and its convergence in SLASH_MY](#loudness-trim-and-its-convergence-in-slash_my).
- **Kick-keyed duck.** `addDuck` (L136–145) writes each dip from the kick's onset: a 4 ms raised-cosine attack, no hold, then an exponential return. Overlapping dips combine by minimum. See [kick-keyed ducking in SLASH_MY](#kick-keyed-ducking-in-slash_my).
- **Scheduled key.** `keyCurve` (L1739–1750) starts its attack `att` before the key time, so full depth lands on the event, then holds and returns exponentially. Overlapping keys combine by minimum. Its lead and hold are the shape a speech duck needs. See [carve keys and the carve table](#carve-keys-and-the-carve-table).
- **The vocal on the kick's curve.** `my()` takes `duck` from the kick's sidechain: 0.2 before the drop, `VOX_DUCK` 0.5 from it (comment L577–578, constant L579, default at L581). The sung word dips on the beat on purpose; a narrator should not.
- **Word pockets.** The pocket block (L2030–2049) keys a bell cut on the bed for each sung word's length. The bed includes the lead, which is summed into it at L1807. `MY_POCKET` (L2035) cuts 4 dB at 1.1 kHz, Q 0.6, for the words from the drop to the wall (112–116). `LOCK_POCKET` (L2036) cuts 10 dB at 2.24 kHz, Q 0.25, for the words from the second drop to the outro (120–128); the code comment places that band at 1–5 kHz. Both use a 10 ms attack and a 50 ms release. Measurements for both are under [carve keys and the carve table](#carve-keys-and-the-carve-table).
- **Pad dip.** `PAD_DIP` (L1788–1809) band-passes the vocal and lead buses at 2.2 kHz, follows them with a 5 ms attack and a 150 ms release, and cuts the pads at 2.2 kHz by up to 4 dB. It is SLASH_MY's one level-keyed carve.
