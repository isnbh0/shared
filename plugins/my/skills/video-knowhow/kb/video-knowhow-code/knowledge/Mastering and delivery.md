# Mastering and delivery

Between the mix bus and the delivered file, two code-built soundtracks handle stereo width, bus compression, a section gain arc, clipping and limiting, loudness, a check on the encoded file, the WAV writer, room tone, and fades. [Audio synthesis](Audio%20synthesis.md) covers the signal path and loudness basics. [Dynamics and spectral carving](Dynamics%20and%20spectral%20carving.md), [Space and delay](Space%20and%20delay.md), and [Sound sources and voices](Sound%20sources%20and%20voices.md) cover the mix itself. [Delivery and color](Delivery%20and%20color.md) covers containers and codecs, and [Verification](Verification.md) keeps numerical checks apart from listening. External claims come from the [audio source ledger](../sources/Audio%20sources.md).

SLASH_MY is the one production John endorses (audio snapshot `fd543f2a`; the WAV writers at `f7f9d199`). The AX DAY reconstruction, a rerender of Stage intro, is kept as a specimen (snapshot `e5ae340d`). The [Soundtrack code case](../cases/Soundtrack%20code.md#mastering-and-delivery) has the code references, parameter tables, loop internals, and full measurement lists.

The measurements come from SLASH_MY's commit messages and its audio run notes (`audio-notes.md`). SLASH_MY measures loudness and true peak with the summary of ffmpeg's `ebur128`, which prints one decimal, in `render.js` and in its qa suite's audio check, qa audio (`qa/audio_qa.py`). It measures true peak a second time with a 4× oversampling meter in qa polish (`qa/polish.py`). Each figure here names its meter, and the [case](../cases/Soundtrack%20code.md#snapshots-and-reading-the-code) lists them. These figures are Reported, not re-measured here. The code's values are starting points for adaptation, and [reading a claim](../Editorial%20notes.md#reading-a-claim) gives what each evidence label means. Every "why it may help" is an interpretation ([what John's endorsement covers](../../video-knowhow-craft/cases/SLASH_MY.md)).

The two master chains, in order:

| Stage | AX DAY reconstruction | SLASH_MY |
| --- | --- | --- |
| Input | dry mix + reverb return ×3 | mix at about −4.4 dB |
| Stereo | none | side mono below 120 Hz; side level per place |
| Tone | none | about +1.5 dB above 10 kHz; 12 Hz DC blocker |
| Bus compression | none | 1.6:1, 30 ms attack, 250 ms release |
| Level automation | none | section arc in dB, after the compressor |
| Clip | `tanh(1.1x)`, no oversampling | clip-room steps, then a 4× soft clip at −0.5 dBFS |
| Limiter | none | 4× true-peak look-ahead limiter at −2 dBFS |
| Level setting | sample peak to about −1.0 dBFS | trim to −14 LUFS |
| Pre-drop gap | linear 5 ms down, no ramp back | half-cosine 5 ms down and up, digital zero between |
| End | linear fade over 2 beats | steepening release, zero one frame early |
| WAV | 16-bit, 44.1 kHz, no dither | 24-bit, 48 kHz, TPDF dither |
| Encode | native AAC 256k, unmeasured | AAC 320k, measured and gated at the mux |

## Mono low end and width by place

**Checked:** SLASH_MY's master splits the signal into mid (the sum) and side (the difference). It high-passes the side at 120 Hz with a fourth-order filter and sets the side's level for each place in the film, gliding to each new value over 50 ms. The mid is never filtered, so everything under 120 Hz sums to the center.

**Interpretation:** a mono low end keeps kick and bass the same on every playback system, mono included. A width per place gives each place its own size without changing the mix inside it. Skip the mono stage when the low end is meant to move in stereo. For vinyl, the ledger's source leaves mono-summing to the cutter.

**Checked (SLASH_MY):** tightloop's wait pulls the side down 8 dB, and design opens it 2 dB. **Reported:** over the film, the side below 120 Hz sits 32 dB under the mid.

**Source status: partly:** mixes often keep the low end mono below roughly 100–125 Hz (iZotope). The ledger has nothing on per-place width.

When it fails, inspect:

- A low end that thins in mono: qa audio flags a section whose low end correlates below 0.9 or loses more than 1 dB when summed to mono. A source panned or detuned in the low end still passes through the mid.
- Width steps you can hear: the 50 ms glide is too short for the jump, or a place boundary falls inside a sustained sound.

## Light bus compression

**Checked:** one linked soft-knee compressor runs over the whole SLASH_MY mix, before the arc and the trim. Its threshold is absolute, so how hard it works depends on the level at which the mix arrives.

**Interpretation:** a low ratio with a slow attack holds the parts together and lets drum transients through. When the upstream level moves, the trim restores the loudness, but the compressor now does a different amount of work, so read its gain reduction again.

**Checked (SLASH_MY):** 1.6:1, 30 ms attack, 250 ms release, threshold about −11 dBFS. No record gives its gain reduction at the snapshot.

**Source status: partly (one example):** one worked example, in a Sound On Sound review, sets gentle mix-bus glue at 2:1 with about 2 dB of gain reduction. SLASH_MY's setting is gentler.

When it fails, inspect:

- Pumping on sustained sections: the release is too short for the tempo, or the threshold too low. Read the log's `bus comp GR` line.
- Flattened kicks: the attack is shorter than the transient.

## Section gain arc after the compressor

**Checked:** SLASH_MY sets the film's level place by place from a list of beat and dB points. The arc runs after the bus compressor, so in the code's words it "moves whole places without changing how the compressor works".

**Interpretation:** contrast between sections comes from a level plan you can read and measure, and the balance inside each place stays as mixed. Level moves inside a place belong to the mix ([Dynamics and spectral carving](Dynamics%20and%20spectral%20carving.md)).

**Checked (SLASH_MY):** the drop at beat 112 sits at −1.5 dB, and writing at −6.6 to −7.7 dB. **Reported:** writing measures −16.9 LUFS and the drop −10.0 LUFS. The ledger has no source for a section arc. The session records (in John's workspace) also show the arc re-tuned after a measured regression. Making the drop the film's peak had taken 0.5–1.5 LU out of the two arrivals after it. The re-tune, checked by measurement, restored the tiering: the peak holds, and the lock at beat 124 sits 1 dB under it (commits `db4b6e4a`, `c893a310`). The [case](../cases/Soundtrack%20code.md#mastering-and-delivery) measures a different event, the second drop at beat 120, which sits 1.7 LU under beat 112 on 3 s short-term loudness.

When it fails, inspect:

- A section too loud against its neighbors: the trim lifts every place together, so the only contrast comes from the arc's steps between places. Re-measure section loudness, not the arc's numbers.
- Limiting concentrated in one place: the arc pushes that place into the limiter. Read the limiter's gain reduction by section.

## Oversampled soft clip before a true-peak limiter

**Checked:** a soft clip at 4× oversampling bends SLASH_MY's tallest crests toward a ceiling they never pass. The clip's correction is filtered back down to 48 kHz, and a hard second pass catches whatever that filter returns over the ceiling. A look-ahead limiter then estimates each sample's true peak at 4× and lowers the gain a few milliseconds ahead of it, releasing over 80 ms.

**Interpretation:** the clip shaves short crests that a limiter would answer with an audible gain dip, so the master reaches its loudness with less limiter movement. Oversampling limits how much of the clip's harmonics fold back. A master that sits well under its ceiling needs neither stage.

**Checked (SLASH_MY):** the limiter ceiling is −2 dBFS, and the clip ceiling sits 1.5 dB above it, so the clip takes only crests that the limiter would pull down by more than 1.5 dB. **Reported:** the largest limiter reduction is 1.9 dB (design) and the largest clip 2.3 dB (the drop). qa polish's 4× meter reads the true peak of `score.wav` at −1.94 dBTP (commit `f7f9d199`), and ffmpeg's `ebur128` reads −1.97 (the audio run notes at `ec61dcd9`). The sample peak sits on the −2 dBFS ceiling, where the master's last clamp holds it.

**Source status: partly:** clipping, often oversampled, ahead of the limiter is a common loudness technique, especially in electronic music (a vendor source, Voxengo). BS.1770 true-peak meters oversample 48 kHz audio 4×. SLASH_MY's estimate uses its own interpolator, so qa re-measures with ffmpeg.

When it fails, inspect:

- Harsh or gritty crests: read the log's clip maximum by section. The arc or the trim is pushing that place.
- Audible gain dips on hits: limiter reduction near 2 dB or more. Lower the place in the arc, or step the mix into the clip there (next section).
- A true peak in qa well over −2 dBTP: the internal estimate missed an inter-sample peak, or a later stage added one.

## Clip room: steps into the clip found by measurement

**Checked:** at every onset, SLASH_MY compares what the soft clip adds with the finished mix over the onset's first 50 ms, band by band in third octaves, and keeps the worst band. Where an onset's clip products come within 20 dB of the mix, the whole mix steps down for a few milliseconds around the onset. The master finds these steps itself, in rounds, and logs them. Three steps are set by hand, and the one on the slam at beat 72 lowers only the band under 400 Hz.

The −20 dB floor is this production's own criterion. No standard or ledger source gives one.

**Interpretation:** keeping the clip's products far under the sound they ride on should stop the clip from coloring onsets. A whole-mix step moves everything together, so, in the code's words, "sound's balance stands". The cost is that the steps follow every upstream change and have to be found again on each render.

**Checked (SLASH_MY):** the floor is −20 dB over a 50 ms window. By construction, the rounds run until every onset sits 20 dB or more under or the budget runs out. **Reported:** at the snapshot all 297 onsets sit 20 dB or more under, and the closest is beat 108 at −20.4 dB. Without the floor, the worst onset sat at −13.3 dB (commit `fa866cb9`). The band-only step at 72 put the slam 1.6 dB over its groove's kicks, where a whole-mix step had left it level with them (commit `edd3024a`). The session records show the decisions behind this. The measured floor replaced a hand-listed set of steps so that one check ran on every onset at once. When the whole-mix step at 72 cost the slam its lead over its own kicks, review caught the side effect before merge, and the band-only dip was the repair that the round's snapshot required.

When it fails, inspect:

- The log line `clip room: N steps found in R rounds …; worst hit X dB at beat (band)`. A worst value over −20 means the rounds ran out. Deep steps mean the arc or the trim is pushing that place into the clip.
- A hit that loses its punch: a whole-mix step held across the hit's body. Try a band-only step, as at 72.

## Loudness trim to the target

**Checked:** SLASH_MY searches for the gain, placed in front of the clip and limiter, that makes the finished film integrate to the target on its own BS.1770-4 meter. The target is one value, `T.LUFS` in `timeline.js`. The trim sits before fixed ceilings, so a new target re-masters the film instead of turning it down: a lower target drives the clip and limiter less.

**Interpretation:** the clip and limiter take some loudness, so a gain set before them has to be found through them. A chain that ends in a plain gain needs no search.

**Checked (SLASH_MY):** the target is −14 LUFS. The trim loop stops once SLASH_MY's meter reads within 0.03 LU of the target or after four passes, so the code alone does not guarantee the target. **Reported:** at the snapshot the trim is +6.3 dB and `score.wav` reached the target; ffmpeg's `ebur128` agrees within 0.1 LU, which checks the meter, not the master. The [Soundtrack code case](../cases/Soundtrack%20code.md#mastering-and-delivery) gives the loop's tolerance and pass count.

When it fails, inspect:

- A trim several dB larger than usual: the mix arrives quieter, and the clip and limiter will work harder at the same target.
- A trim that does not converge: limiting so heavy that gain no longer maps to loudness.
- An ffmpeg reading far from −14 LUFS on `score.wav`: SLASH_MY's meter is wrong, since the trim answers only to it.

## Measuring the encoded file at the mux

**Checked:** `render.js` uses ffmpeg to measure `score.wav` with the warning card joined in front. It sets a small residual gain, adds a look-ahead limiter only if that gain would push true peak past its aim, and encodes AAC at 320 kbit/s. It then measures the encoded file and, if needed, corrects and encodes again, up to three passes in all. The mux measures once more and stops with "audio is out of spec" if true peak is over −1 dBTP or loudness is more than 0.5 LU from the target, so any render that finishes has passed that gate.

**Interpretation:** the encoder raises peaks, so the number that matters is the one measured on the file people receive. Any chain with a lossy encoder after the master needs this check.

**Checked (SLASH_MY):** the delivery maximum is −1 dBTP, and the master's −2 dBFS ceiling leaves 1 dB for the encoder. **Reported (SLASH_MY):** the code's comment reports AudioToolbox's AAC overshooting by about 0.1 dB and ffmpeg's native AAC by 1.1–1.7 dB. **Reported (commit):** according to commit `f7f9d199`, the AAC reads −14.08 LUFS on pyloudnorm and −1.75 dBTP on qa polish's 4× meter, about 0.2 dB over that meter's reading of `score.wav`.

When it fails, inspect:

- "audio is out of spec": read the `audio pass` lines. A limiter that engages on every pass usually means the native encoder is in use.
- A residual gain far from 0 dB: `score.wav` no longer meets `T.LUFS`, or the card's audio is being counted.

## Loudness targets by destination

The target depends on where the piece plays. The ledger gives these figures:

| Destination | Integrated loudness | True peak | Source status |
| --- | --- | --- | --- |
| Spotify | normalizes to about −14 LUFS | below −2 dBTP for masters louder than −14 LUFS; below −1 dBTP for quieter ones | supported |
| YouTube | publishes no target; measurements show playback normalized to about −14 LUFS since 2019, loud uploads turned down, quiet ones not turned up; a separate "stable volume" feature evens out quiet and loud audio | not given | partly |
| EBU R 128 (broadcast) | −23 LUFS | no higher than −1 dBTP during production; distribution limits may be lower | supported |
| ATSC A/85 (US broadcast, without metadata) | −24 LKFS, about ±2 dB | below −2 dBTP | supported |

The two productions measure as follows:

| | Integrated | True peak | Loudness range | Source |
| --- | --- | --- | --- | --- |
| SLASH_MY `score.wav` | −14 LUFS target (pyloudnorm −14.06) | −1.94 dBTP (qa polish) | 5.6 LU (`ebur128`) | commit `f7f9d199`; range from the audio run notes, L32 at `ec61dcd9` |
| SLASH_MY AAC | −14.08 LUFS (pyloudnorm) | −1.75 dBTP (qa polish) | not reported | commit `f7f9d199` |
| AX DAY reconstruction decoded MP4 | about −14.3 LUFS | not reported | 12.2 LU | measured in the reconstruction's sound analysis |

SLASH_MY's AAC meets Spotify's guidance for masters at or below −14 LUFS and stays within R 128's production maximum. Its true peak is above A/85's −2 dBTP, and both broadcast loudness targets sit 9–10 dB lower than the film. The AX DAY reconstruction lands near −14 LUFS without aiming for it, so any comparison of the two soundtracks should match playback loudness first.

When it fails, inspect:

- A delivery for broadcast: changing `T.LUFS` and `T.TP_MAX` re-masters SLASH_MY instead of turning it down. Decide whether you want a turned-down copy of the −14 master or a new master.
- A master that lands even slightly louder than −14 LUFS: Spotify's guidance then asks for true peak below −2 dBTP, which SLASH_MY's −1.75 dBTP misses. The mux gate allows 0.5 LU either side of the target, so it would pass such a file.
- Quiet sections that vanish on a platform: normalization turns a loud master down as a whole, so the quiet parts stay as quiet as mixed.

## Writing the WAV: word length and dither

**Checked:** both productions compute in 64-bit floats and write PCM by scaling and rounding each sample. Plain rounding leaves an error that follows the signal. TPDF dither adds two uniform ±0.5 LSB random draws (2 LSB peak to peak) before rounding, which turns that error into steady noise.

SLASH_MY applies TPDF dither, without noise shaping, when `audio.js` `writeWav` writes the 24-bit `score.wav` and `score-card.wav`. `render.js` does the same when it makes the 16-bit input for the `aac_at` encoder, where ffmpeg's own conversion would round without dither. Each writer draws from its own seeded stream, so renders stay byte-identical. Samples that are exactly zero stay zero. The AX DAY reconstruction writes 16-bit PCM without dither.

Dither here is a correctness fix. At 24 bits you won't hear the difference: rounding error sits near −149 dBFS rms and dithered noise near −144.5 dBFS (computed, not measured). At 16 bits the two sit near −101 and −96 dBFS, and dither can matter in quiet tails and fades. **Reported (commit):** according to commit `f7f9d199`, with dither, the loudness, true peak, and sample peak of `score.wav` are unchanged, and the gap stays digital zero.

**Source status: supported:** dither whenever word length is reduced, including 32-bit float to 24-bit and 24 to 16; TPDF dither of 2 LSB peak-to-peak is the standard choice (Audio Precision; Lipshitz, Wannamaker & Vanderkooy, JAES 1992).

When it fails, inspect:

- Low-level tails and fades at 16 bits: that is where rounding error sits closest to the signal, as in the AX DAY reconstruction's file.
- A hash that changes when nothing else did: the dither streams draw a fixed count per frame, so either the samples or the frame count changed.

## Room tone instead of digital silence

**Checked:** SLASH_MY opens on a quiet band of noise, limited to about 110 Hz–1.8 kHz, with decorrelated channels. It runs as one stream under the 5 s warning card and the film's first six beats. The card's part is written to `score-card.wav` at the film's opening gain and joined in front of `score.wav`. Digital zero remains only in the pre-drop gap (beats 111.75–112) and on the last frame. The card fades in from zero; its first millisecond, under half an LSB, carries the dither's ±1 LSB.

**Interpretation:** a faint room tone makes the opening sound like a real room, and the join from card to film has no step in it. Room tone is a dialogue-editing practice, and using it under a music soundtrack is this production's interpretation. Leave it out where silence is the effect, as in the gap before the drop.

**Checked (SLASH_MY):** the room tone fades out over beats 1–6 under the rising drone. **Reported (commit):** according to commit `b0ab2eff`, it measures about −52 dBFS rms, and the sample step at the card's end fell from 0.0067 to 0.00045, typical of the steps around it. The AX DAY reconstruction has no room tone, and its file starts and ends on digital zero.

**Source status: partly:** in film and video dialogue editing, room tone fills silences: "True digital silence would jar the audience out of the story" (ProVideo Coalition). The source is about dialogue, not music.

When it fails, inspect:

- A click at the card's end: SLASH_MY's part has a fade-in, draws from another stream, or the card's gain no longer matches SLASH_MY's first frame.
- Audible hiss: the level is too high for the playback system. Measure rms per 250 ms; do not trust the gain setting.
- Exact zeros at the start: qa audio's hole check.

## Shaped fades, the pre-drop gap and the end release

**Checked:** SLASH_MY shapes every edge with a raised cosine, which starts and ends at zero slope. Events fade in over 2 ms and out over 4 ms, and an event that the arrangement cuts short fades at the cut. The pre-drop gap ramps down over 5 ms, holds digital zero to beat 112, and ramps back up over 5 ms; the build's snare roll runs into it ([accelerating snare rolls](Groove%20and%20feel.md#accelerating-snare-rolls-into-a-gap)). The end release steepens over the last two beats and reaches zero one frame early, and the picture's end fade reads the same curve.

**Interpretation:** zero-slope edges should not click, and one end curve shared by sound and picture lets them finish together. A silence before a drop is clean only if the sound also comes back without a step.

**Checked (SLASH_MY):** event edges 2 ms in and 4 ms out; gap ramps 5 ms; end release 24 dB over two beats on a squared curve. **Reported (commit):** according to commit `31d73916`, the tail crosses −60 dBFS at beat 135.92, and the last frame is silent and black. The ledger lists silence before a drop as common practice with no authoritative source.

When it fails, inspect:

- Clicks at cuts or event ends: qa audio's click and hole checks. A fade shorter than one cycle of the sound's lowest partial will still thump.
- A drop that enters with a step: no ramp back after the gap (the AX DAY reconstruction's gate jumps back to full level), or a reverb tail resuming at full level (see [comb and all-pass reverb](Space%20and%20delay.md#comb-and-all-pass-reverb)).
- Sound outlasting the picture, or the reverse: the audio and picture fades read different curves.

## The AX DAY reconstruction's simple master

The reconstruction masters in one loop: it sums the dry mix with the reverb return at ×3, applies `tanh(1.1x)` to each channel, applies the gap gate and the end fade, and normalizes the sample peak to 0.89. It writes 16-bit PCM without dither and encodes AAC without measuring it.

**Checked:** `tanh(1.1x)` is close to a 1.1× gain for small signals and bends progressively toward 1 as level rises. At the sample rate its harmonics are not band-limited, and the aliasing was not measured. Peak normalization sets the level by the single loudest sample, not by loudness, and it leaves true peak unknown.

**Reported:** the reconstruction's sound analysis measures its decoded MP4 at about −14.3 LUFS with a loudness range of 12.2 LU. **Interpretation:** a short chain can land near a streaming loudness on its mix alone. Control comes from the longer chain, which sets loudness and true peak and checks what the encoder delivered.

When it fails, inspect:

- A level that moves with every mix change: peak normalization follows the loudest sample, wherever it falls.
- Distortion on dense passages: the `tanh` drive acts on the whole mix, and the ×3 reverb return feeds it.

## Untested ideas

- **Untested idea:** TPDF dither at the AX DAY reconstruction's WAV writer. SLASH_MY dithers at both of its writers from seeded streams and stays deterministic ([writing the WAV](#writing-the-wav-word-length-and-dither)). The reconstruction's 16-bit writer rounds plainly. Adding two uniform ±0.5 LSB draws before rounding would change its bytes once.
- **Untested idea:** an independent loudness and true-peak check for the AX DAY reconstruction. SLASH_MY measures its encoded and muxed files with ffmpeg and stops on an out-of-spec file. The same step would give the reconstruction's true peak, which no record reports.
- **Untested idea:** a matched-loudness reference A/B. No listening test has isolated any stage on this page. Matching playback loudness, then toggling one stage at a time (bus compression, the clip room, width) or comparing against a reference track, would test the interpretations above. The ledger has no source on reference listening.
- **Untested idea:** phone and laptop translation, including bass harmonics. No check simulates a small speaker. The ledger supports the claim that on small speakers the ear infers a missing bass fundamental from its harmonics, so adding harmonics helps bass translate (Sound On Sound). SLASH_MY's drum-bus clip ([low-band drum saturation](Dynamics%20and%20spectral%20carving.md#low-band-drum-saturation-through-a-crossover)) and the AX DAY reconstruction's `tanh` both add harmonics. A preview that high-passes and sums to mono at a device's low limit, measured per section, would show what survives.
