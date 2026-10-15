# Sound sources and voices

Two code-built soundtracks make their music and effects from these voices: band-limited and stacked saws, a legato lead, synthesized drums, a bass, a drone, plucked strings, a formant vocal, layered impacts, and risers and whooshes. The signal path, envelopes, and rendering are in [Audio synthesis](Audio%20synthesis.md); ducking and carving in [Dynamics and spectral carving](Dynamics%20and%20spectral%20carving.md); reverb and stereo in [Space and delay](Space%20and%20delay.md); timing and velocity in [Groove and feel](Groove%20and%20feel.md); loudness in [Mastering and delivery](Mastering%20and%20delivery.md); and placement against the picture in [Audiovisual synchronization](Audiovisual%20synchronization.md). External claims come from the [audio source ledger](../sources/Audio%20sources.md).

SLASH_MY is the one production John endorses; its code is cited at `fd543f2a`. The AX DAY reconstruction is a rerender of Stage intro, rebuilt from the chatlog, kept as a specimen, and cited at `e5ae340d`. Both run at 120 BPM, and the times below are in beats. Parameter tables, line references, call sites, and the commits' measurements are in the [Soundtrack code case](../cases/Soundtrack%20code.md#sound-sources-and-voices).

The code values below are starting points for adaptation, and [reading a claim](../Editorial%20notes.md#reading-a-claim) gives what each evidence label means. Every piece of advice on when to use a voice is an interpretation; check it by ear against the actual mix.

## Band-limited saw (PolyBLEP)

A naive sawtooth jumps from +1 to −1 in one sample. That step has energy above the Nyquist frequency, and the energy folds back as inharmonic aliasing, which is most audible on high notes and on many detuned saws summed together. PolyBLEP rounds off the samples on either side of each jump with a short polynomial, so the step comes close to band-limited at almost no cost.

**Checked:** SLASH_MY's `Saw` (`audio.js` L52–60) corrects the sample before and the sample after each wrap. Every saw in SLASH_MY uses it, in the music and in the sound effects. The AX DAY reconstruction's saws are naive.

**Interpretation:** Use it when a saw plays high, sweeps, or is stacked. A naive saw does the least harm on low notes under a low-pass.

**Source status: supported:** the ledger's sources describe PolyBLEP as "a cheap polynomial approximation of band-limited step correction for virtual-analog oscillators" ([Välimäki & Huovilainen 2007](https://doi.org/10.1109/MSP.2007.323276); [Välimäki, Pekonen & Nam 2012](https://doi.org/10.1121/1.3651227); [excerpt](../sources/excerpts/polyblep-valimaki.md)).

On failure, inspect:

- Whistles that move against the pitch on high or swept notes: whether the phase step comes from the current sample's frequency, and whether it stays below half a cycle per sample.
- Some aliasing left on very high notes: a two-point correction leaves a residue. Low-pass the voice or oversample.

## Supersaw

A supersaw stacks seven saws per note at slightly different pitches. The saws beat against each other, which thickens one note into a band of sound like a chorus.

**Checked:** SLASH_MY's `supersaw()` (`audio.js` L403–429) detunes the seven voices by a fixed, uneven table, `SS_DET`, scaled by one `det` amount. Each voice starts at a random phase and drifts slowly in pitch. The voices spread across the stereo field, then pass through a filter envelope and a fixed high-pass. An optional double, a few milliseconds late on the other side, widens stabs. The AX DAY reconstruction's seven naive saws sit at even pitch steps and sum to mono.

**Interpretation:** Use it when a pad, stab, or lead should sound wide and thick from a single note. Random phases avoid the same click-like peak on every note-on, and the drift keeps the beating from repeating. The high-pass keeps a wide stack out of the range of the kick and the bass. Avoid it where a part must stay narrow or survive a mono sum.

**Checked:** SLASH_MY's `det` of 0.12 gives about ±4, ±13, and ±22–23 cents, over a 150 Hz high-pass. The AX DAY reconstruction's even steps give ±6, ±12, and ±18 cents. **Reported:** adding a light double to the stabs of exec's first skill, together with other width changes, took their stereo correlation from 0.98 to 0.69 (`8a6b436f`). The figure covers the combined change.

**Source status: supported:** the JP-8000 supersaw is seven free-running saws with random phases, a non-linear detune curve, and a high-pass that tracks the fundamental ([Szabo 2010](http://web.archive.org/web/20160310085410/http://www.nada.kth.se/utbildning/grukth/exjobb/rapportlistor/2010/rapporter10/szabo_adam_10131.pdf); [excerpt](../sources/excerpts/jp8000-supersaw-szabo.md)). `SS_DET` matches exactly the seven detune offsets Szabo measured on the JP-8000 at maximum detune, from −0.11002313 to +0.10745242 (Szabo 2010, Table 1). SLASH_MY differs in two ways. Its high-pass is fixed and does not track the pitch. It also fixes the center voice at 1 and the sides at 0.75, where on the JP-8000 the mix knob moves that balance.

On failure, inspect:

- A hollow attack that sounds the same on every note: the phase source.
- A static, frozen chorus: the drift is off or too slow.
- Muddy lows: the high-pass against the lowest note. A fixed 150 Hz cuts the fundamental of notes below about D3.
- A thin mono sum: the spread and a mirrored double can cancel.
- A chord that sounds out of tune instead of wide: lower `det`.

## Lead articulation

A synth lead sounds played when its notes connect. The pitch glides between notes, vibrato arrives after the note settles, the accent brightens the note, and a new note dips slightly instead of retriggering.

**Checked:** SLASH_MY's `lead()` (`audio.js` L491–524) renders each phrase as one continuous seven-saw voice, and only the control values change from note to note. A one-pole glide follows the pitch, vibrato fades in after each note starts, and the filter envelope peaks harder on accented notes. Each new note starts about 3 dB down and recovers within 6 ms. The state-variable filter tolerates cutoff changes on every sample. The AX DAY reconstruction has no lead; its top lines are supersaw stabs and a sine arpeggio.

**Interpretation:** Use it when a melodic line carries a section. Delayed vibrato copies the way singers and players settle a pitch before they modulate it. Tying brightness to the accent lets a downbeat stand out without a change in level.

**Checked (SLASH_MY):** a 25 ms glide time constant, and vibrato of 0.12 semitone at 5.6 Hz that is absent for the first 150 ms and full by 350 ms.

On failure, inspect:

- Smeared fast passages: the glide against the note spacing. 25 ms suits eighths at 120 BPM.
- Wobble on short notes: the vibrato delay is shorter than the notes.
- Clicks at note changes: a gain step where a smoothed dip should be, or a filter that cannot follow cutoff changes on every sample.

## Layered kick

A kick built from one swept sine sounds thin on small speakers and identical on every hit. SLASH_MY sums three layers and varies a few values on each hit.

**Checked:** SLASH_MY's `kick()` (`audio.js` L300–316) sums three layers: a pitch-swept body saturated by `tanh`, a short knock in the low mids, and a click that is eased in and low-passed so it has no step at its onset. Each hit varies the tail pitch slightly and the tone of the click, and the code that calls it varies the sweep and the decay by role. The AX DAY reconstruction's kick is one driven sine sweep plus 4 ms of raw noise, switched on with no ramp and identical on every hit.

**Interpretation:** Use it when the kick must carry on phones and laptops. The drive and the knock put energy above the sub tail, where small speakers can play it. Variation from hit to hit matters most on repeated hits and rolls.

**Checked:** SLASH_MY's body sweeps 150 → 47 Hz and its knock 230 → 185 Hz. The AX DAY reconstruction's sweeps 155 → 45 Hz. Its effective kick gain is 0.9 before the drop, 1.08 on the drop hit, and 0.72 after it. **Reported:** the click was eased and band-limited in a commit that reports "polish 0 glitches" for several mix changes together (`f1f6d6c1`).

**Source status: supported:** on small speakers the ear infers a missing fundamental from its harmonics, so adding harmonics or distortion helps bass translate ([Sound On Sound](https://www.soundonsound.com/techniques/getting-more-bass-your-mix)). **Interpretation:** the kick's drive and knock apply that idea here.

On failure, inspect:

- Harsh clicks after limiting: a step at the start or end of the click, or content near Nyquist.
- A kick that vanishes on a phone: too little above 100 Hz. Raise the knock or the drive.
- A machine-gun feel on rolls: no variation from hit to hit, too small a range, or the same seed on every hit.
- A pitch "boing": a sweep too slow for the decay.

## Multi-burst clap

A real clap is several hands striking a few milliseconds apart, followed by the sound of the room.

**Checked:** SLASH_MY's `clap()` (`audio.js` L317–327) gates one band-passed noise with four quick peaks at uneven spacing, with the middle two jittered on each hit, then a short tail. Bars that end a phrase add a quieter flam just ahead of the clap. The AX DAY reconstruction has no clap; its backbeats are snares.

**Interpretation:** Use it when a backbeat should sound like hands. The flam marks the end of a phrase without a fill.

**Checked (SLASH_MY):** peaks at 0, about 11, about 21, and 30 ms through a 1300 Hz band-pass. The flam lands 22 ms early at 0.45 gain.

On failure, inspect:

- A clap that sounds like one noise burst: the offsets have collapsed, or the early peaks are too low.
- A buzzy, tonal clap: evenly spaced, close peaks form a comb. Keep the spacing uneven.
- A clap with no body: the band-pass center is too high or its Q too narrow.

## Noise snare

A snare is a short pitched shell plus a burst of filtered noise for the wires.

**Checked:** SLASH_MY's `snare()` (`audio.js` L328–337) sweeps a sine shell down slightly and shapes the noise with a band-pass and a high-pass. In the build roll, the shell's pitch rises as the roll tightens. The AX DAY reconstruction's shell has a fixed pitch, in its roll too. The timing of the rolls is in [accelerating snare rolls](Groove%20and%20feel.md#accelerating-snare-rolls-into-a-gap).

**Interpretation:** A shell that rises with the roll adds tension as the notes get denser.

**Checked (SLASH_MY):** a 190 Hz shell over noise centered near 3.6 kHz. The build roll tunes the shell from 190 Hz toward 400 Hz.

On failure, inspect:

- A snare that sounds like a hi-hat: too little body, or noise filtered too high.
- A roll that blurs into noise: the decay outlasts the step. Shorten the decay as the step shrinks.
- A roll that stays flat in pitch while it speeds up: the shell's pitch is not tied to the roll's progress.

## Hats

Hats need a metallic, inharmonic shimmer.

**Checked:** SLASH_MY's `hat()` (`audio.js` L338–350) sums six square waves at unrelated frequencies (`HAT_F`) with noise and high-passes the result. Closed hats pan back and forth once a bar. The crash and the cymbal in the sound effects reuse the same frequencies, scaled up, so the hats and cymbals share one family of partials. The AX DAY reconstruction's hat is high-passed noise alone, at a fixed pan.

**Interpretation:** Use it when the hats should ring like metal. Noise alone suits a softer, airier top.

**Checked (SLASH_MY):** the partials enter at 0.1 against noise at 0.5. A closed hat lasts 0.09 s and an open one 0.5 s.

**Source status: supported:** the six base frequencies in `HAT_F` are the TR-808's cymbal and hi-hat oscillators: four fixed at 205.3, 304.4, 369.6, and 522.7 Hz, and two factory-trimmed to 540 and 800 Hz ([Werner, Abel & Smith 2014](https://speech.di.uoa.gr/ICMC-SMC-2014/images/VOL_2/1453.pdf); [excerpt](../sources/excerpts/tr808-cymbal-oscillators.md)). SLASH_MY differs in three ways: it scales them by 1.9 for the hats; its square waves are symmetric where the 808's are slightly rectangular; and it filters through one 7.6 kHz filter where the 808 has two band-passes near 3.4 and 7.1 kHz.

On failure, inspect:

- A hat that sounds like static: no tonal partials, or partials too quiet against the noise.
- A hat that rings like a bell: the partials are too loud, or the high-pass is too low.
- Hats pinned to one side over a long section: no pan movement.

## Bass

A short bass note has to be felt on large speakers and heard on small ones.

**Checked:** SLASH_MY's `bassNote()` (`audio.js` L387–397) averages two slightly detuned saws through a resonant, enveloped low-pass, adds a sine at the fundamental, and saturates the sum. The AX DAY reconstruction's bass is a naive saw plus a sine an octave below, with no saturation.

**Interpretation:** Saturating the saw and the sine together adds harmonics that carry the note where the fundamental cannot be reproduced. This is the missing-fundamental effect cited under [layered kick](#layered-kick). A sub-octave in the low 20s Hz, as in the AX DAY reconstruction, sits below what small speakers play and uses up headroom.

**Checked:** SLASH_MY's saws sit 0.4 % either side of the note, under a low-pass that starts at 360 Hz. The AX DAY reconstruction's sub-octave sine lands at 22–33 Hz. **Reported:** raising the brand section's bass duck from 0.72 to 1.2 took the bass from 2.0 to 4.2 dB under the kick, below 120 Hz (`f13f69d2`). The ducking is described in [kick-keyed ducking](Dynamics%20and%20spectral%20carving.md#kick-keyed-ducking).

On failure, inspect:

- Bass that disappears on a laptop: too little above 100 Hz. Add drive or raise the filter floor.
- Bass that fights the kick: the ducking, on the dynamics page.
- Flabby notes: the release outlasts the note spacing.

## Drone

An intro drone holds a tonal floor before the beat arrives.

**Checked:** SLASH_MY's intro drone (`audio.js` L935–953) glides a low pedal through a short progression, A1 → F1 → E1 → A1. Two saws an octave above it pass through a low-pass that opens across the intro. The drone is ducked under the kick and hands over to the bass at beat 16. The AX DAY reconstruction holds a static chord of five sines with a slow tremolo, and does not duck it.

**Interpretation:** A pedal that moves with the harmony, under a filter that opens, gives the first bars a direction before any drum enters. A static chord gives a bed with no motion.

**Checked (SLASH_MY):** the filter opens from 140 to 1000 Hz over 16 beats, and the pedal glides with a 90 ms time constant. A separate [room tone](Mastering%20and%20delivery.md#room-tone-instead-of-digital-silence) runs under the opening card.

On failure, inspect:

- A drone that masks the first kick: it is not ducked, or its lows are too loud.
- Zipper steps: the pitch or cutoff changes once per block when it should change every sample, or the glide is too short.

## Karplus-Strong pluck and keys

Karplus-Strong excites a short delay line with a burst of noise and feeds it back through a low-pass. The result is a plucked-string tone whose brightness decays naturally.

**Checked:** SLASH_MY's `ksLen()` and `ksBuffer()` (`audio.js` L64–90) add fractional tuning through an allpass, a pick-position comb applied once to the excitation, and a loop gain set for each pitch. The loop gain makes the nominal decay time the same at every pitch; that holds by construction. The loop filter's damping is not compensated, so high notes still die faster. The pluck layers the string with a filtered saw, and the keys layer it with an FM tine. The AX DAY reconstruction has no plucked voice and no keys voice.

**Interpretation:** Use it when plucked hooks, arpeggios, and keys should decay like a string and differ slightly from note to note. It costs little to compute.

**Checked (SLASH_MY):** the pluck asks for a 1.1 s T60 (the time to fall 60 dB) with damping 0.32. At 880 Hz the T60 of its fundamental comes out at about 0.92 s (computed from the loop filter, not measured).

**Source status: partly:** Karplus & Strong introduced the plucked-string and drum algorithm. Their patent describes decay stretching, which multiplies the decay time by a factor s of 1, 2, 4 … 64 or infinity, applied probabilistically ([Karplus & Strong 1983](https://doi.org/10.2307/3680062), [US Patent 4,649,783](https://patents.google.com/patent/US4649783A/en); [excerpt](../sources/excerpts/karplus-strong-patent.md)). **Source status: supported:** Jaffe & Smith added fractional-delay tuning with an allpass filter, and pick-position comb filtering ([Jaffe & Smith 1983](https://doi.org/10.2307/3680063)). No checked source covers SLASH_MY's per-pitch loop gain or the weighted form of its loop filter.

On failure, inspect:

- Out-of-tune high notes: the integer delay alone is too coarse. The allpass must take the remaining fraction, including the loop filter's own delay.
- High notes that die much faster than low ones: uncompensated damping. Lower the damping with pitch, or accept it.
- A thin, hollow tone: a pick position near a simple fraction of the string, which cancels many harmonics.
- Repeated notes that sound identical: the exciter reuses the same noise. Draw fresh noise for each note.

## Formant vocal and stacked takes

You can synthesize a sung syllable by passing a saw through band-pass filters at the vowel's formant frequencies and moving those frequencies through the word.

**Checked:** SLASH_MY's `my()` (`audio.js` L580–611) sings "my" as /m/ → /a/ → /i/. A nasal low-pass stands in for the closed lips, three band-passes carry the formants, and each note scoops up into pitch before a delayed vibrato. Each note is scaled against a reference pitch through the same formants, so it sounds at its set level whatever its pitch; that holds by construction. From the drop on, the word is a stack: a centered lead take and four quieter doubles, offset in onset, pitch, formant, and pan. The doubles stay silent through the /m/. The AX DAY reconstruction has no vocal.

**Interpretation:** Use it when the word serves as a short hook or a texture. Small offsets between takes imitate doubles sung separately, and keeping the consonant on one take avoids a smeared /m/.

**Checked (SLASH_MY):** /a/ formants at 780, 1180, and 2800 Hz. The doubles sit 7 and 9 dB under the lead take, 12–22 ms off it, 11–12 cents and 2.5–3 % of formant apart, panned ±0.45 and ±0.8.

On failure, inspect:

- A vowel whose loudness changes with the note: the level matching is off, or the formant gains are not normalized by Q.
- A word that sounds like a filter sweep: the formants move too slowly, or the /m/ is too long.
- A stack that phases or flams: the onset offsets are too large, or all the doubles sit on one side.
- A buzzy, synthetic edge: the saw's upper harmonics get past the third formant. Low-pass the take.

## Composite impacts and drop layers

A big hit is several sources lined up on one moment, each covering its own band and its own stretch of time: a tuned body and sub for weight, noise and crack for the front, metal and debris for the top, and a tail.

**Checked:** SLASH_MY renders each impact from a table with one entry per hit (`sfx.js` `IMPACT` and `renderImpact()`, L1331–1508): a tuned membrane, a noise blast, a plate, a crack, a cymbal with falling noise and debris, a stereo shockwave, and a tuned sub that starts a few milliseconds late. The biggest drop adds a saw stab in the mids. Before the build's burst, an inhale of rising noise closes just ahead of the hit. The AX DAY reconstruction's drop starts a kick, a sub sweep, a noise crash, and a supersaw chord on the same sample.

**Interpretation:** Use it for the few hits that should land hardest. Starting the sub after the kick keeps two low onsets from summing into one peak, and a short gap before the hit makes its front more distinct. A hit that must come through on phones needs body above 100 Hz as well as sub.

**Checked (SLASH_MY):** the tuned sub starts 4 ms late with a 25 ms ramp, and the inhale crests 8 ms before the hit. **Reported:** the drop stab was added so that "112 reads as the biggest hit on small speakers too" (`74df504b`).

**Source status: open:** the ledger has no source for layered impacts or for a silence before a hit; those come from the code alone.

On failure, inspect:

- An impact that is loud but sounds small on phones: all its weight is below 80 Hz. Add a mid-band body or a stab.
- An impact that clips the master: the low layers start together. Offset or ramp the sub.
- A smeared front: too many layers peak at different times. Align their peaks or remove layers.
- A tail that buries what follows: release the top band early, as SLASH_MY's high release for each hit does.

## Risers and whooshes as sources

Risers build tension into a downbeat, and whooshes mark motion across a cut. As sources, both are noise and tone shaped by sweeping filters and amplitude curves. Where their peaks sit against the picture is covered in [sound and picture on one beat grid](Audiovisual%20synchronization.md#sound-and-picture-on-one-beat-grid).

**Checked:** SLASH_MY's `sfx.js` has a riser of band-passed noise plus two gliding saws, a grain riser whose density climbs on a pentatonic scale, a reversed cymbal, reversed swells, and a whoosh renderer with four kinds (`air`, `tape`, `slide`, `sonar`) chosen by section. The AX DAY reconstruction has one riser, a noise band plus a chirp, and soft noise whooshes on its words.

**Interpretation:** A tonal layer keeps a riser from sounding like hiss. A steep amplitude curve holds the peak back for the downbeat. Changing the whoosh from section to section keeps the cuts from sounding alike.

**Checked:** SLASH_MY's riser ends with a 4 ms fade. The AX DAY reconstruction's riser sweeps a noise band from 300 to 7300 Hz along `p²`, with a chirp from 150 to 1050 Hz.

On failure, inspect:

- A riser that sounds like hiss: no tonal layer. Add saws or pitched grains.
- A riser that peaks early: the amplitude curve is too shallow (`p` where `p²` or steeper is needed).
- A click at the downbeat: no end fade, or a cut in the middle of a cycle.
- A whoosh that sounds the same at every cut: one kind of whoosh serves every section.

## Untested ideas

- **Sample-layered drum transients and recorded one-shots** (untested idea). Both productions synthesize every drum. **Interpretation:** in either soundtrack, the fully synthesized drums may be the clearest sign that the track is programmed; no source or listening test backs this. Layering a recorded transient under the kick, clap, or snare, or replacing the hats with recorded one-shots, is untested. [Audio synthesis](Audio%20synthesis.md#sources-tone-noise-and-samples) covers sample playback.
- **A longer line for the formant vocal** (untested idea). SLASH_MY uses "my" as fragments and as a short stacked hook. **Interpretation:** three fixed formants on a saw hold up as a texture and a hook, but may expose their synthetic edge over sustained phrases. Untested.
- **Pitch-tracked supersaw high-pass** (untested idea). The JP-8000's high-pass tracks the fundamental ([Szabo 2010](http://web.archive.org/web/20160310085410/http://www.nada.kth.se/utbildning/grukth/exjobb/rapportlistor/2010/rapporter10/szabo_adam_10131.pdf)), and SLASH_MY's is fixed at 150 Hz. Tracking it would remove energy below the fundamental from low chords without thinning high ones. Untested.
- **Pitch-compensated string damping** (untested idea). SLASH_MY's Karplus-Strong equalizes the nominal decay time across pitch, but its loop filter still takes more from high notes. Lowering the damping with pitch, or using the decay stretching from Karplus & Strong's patent, could even this out. Whether it matters in the register the film's pluck plays in is untested.
