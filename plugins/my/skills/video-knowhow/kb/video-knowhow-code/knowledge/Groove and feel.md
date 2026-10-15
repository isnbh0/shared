# Groove and feel

Two code-built soundtracks set their timing and weight with six techniques: selective swing, velocity accents by beat position, small timing jitter, a snare laid back behind the beat, accelerating snare rolls into a silence, and humanized typing. Groove as a musical choice, such as which pulse a scene gets, belongs to [Musical development](../../video-knowhow-craft/knowledge/Musical%20development.md); the sections below show how the code carries that choice out. The drum and key-click voices are in [Sound sources and voices](Sound%20sources%20and%20voices.md), the kick ducking that the accents sit under is in [Dynamics and spectral carving](Dynamics%20and%20spectral%20carving.md), and the beat grid that picture and score share is in [Audiovisual synchronization](Audiovisual%20synchronization.md). External claims come from the [audio source ledger](../sources/Audio%20sources.md).

SLASH_MY is the production John endorses (audio snapshot `fd543f2a`). The AX DAY reconstruction, a rerender of Stage intro, is kept as a specimen (snapshot `e5ae340d`). Both run at 120 BPM, so a beat is 500 ms and a sixteenth 125 ms. Every random value in both, from jitter to typing gaps, comes from seeded random streams, so unchanged code renders the same samples again on the same setup ([Deterministic rendering](Deterministic%20rendering.md) covers the picture side). The [Soundtrack code case](../cases/Soundtrack%20code.md#groove-and-feel) has the swing and jitter tables, line references, the seeding scheme, and code walk-throughs.

The code values below are starting points for adaptation, and [reading a claim](../Editorial%20notes.md#reading-a-claim) gives what each evidence label means. Every "why it may help" below is an interpretation to audition against the actual mix.

## Selective swing

**Checked:** swing delays every odd sixteenth, the "e" and the "a", so each pair of sixteenths becomes long-short. SLASH_MY sets the amount per section in Roger Linn's convention, where 0.5 is straight and 0.667 puts the off-sixteenth on the triplet. A line swings only if its code calls the swing function `sw`, so a line that skips the call stays straight inside a swung section.

**Interpretation:** Swing the lines that carry the groove, such as hats, bass, percussion, and ornaments. Keep the downbeats, the lead, and any hit the picture cuts to on the grid. The groove loosens while the cut points stay exact.

**Checked:** exec, nav, and reveal swing at 0.54, which delays the off-sixteenths 10 ms. Writing drifts from 0.57 to 0.61 (17.5 → 27.5 ms). The other sections are straight. The swung lines include closed hats, stabs, bass, plucks, congas, and the reveal arp. In writing, the kick's syncopations land 20–27 ms late while its downbeats stay put, and the ghost snares and rims swing with them. Claps, snare backbeats, the lead, open hats, and the vocal stay straight. The AX DAY reconstruction has no swing.

**Source status: supported:** Linn puts the useful range at about 50–70% ([excerpt](../sources/excerpts/roger-linn-swing-range.md)), and SLASH_MY's 0.54–0.61 falls inside it. SLASH_MY's 10 ms is above the ~6 ms timing JND for sixteenths at 120 BPM (Friberg & Sundberg). **Interpretation:** the swing is large enough to be heard as a displacement. The listening studies under [timing jitter](#timing-jitter) tested microtiming deviations, not a swing ratio like this one.

When it fails, inspect:

- A line that should swing but sounds straight: check whether it calls `sw`.
- A section amount that changes nothing: check whether any `sw` call in the window falls on an odd sixteenth. SLASH_MY has one such window: [the 0.56 after beat 92](../cases/Soundtrack%20code.md#the-056-after-beat-92-never-takes-effect).
- Kick and bass flamming: the bass has to read the same swung positions as the kick.
- A hit locked to the picture that lands off its sync point: keep that line straight.

## Velocity accents and bar-end lift

**Checked:** each hit's weight comes from its position in the bar. SLASH_MY's closed-hat sixteenths play pattern accents at full weight, then, in falling order, the beat, the offbeat eighth, and the two remaining sixteenths, quietest on the "e". The bar lifts slightly toward its end, and a small seeded spread varies each hit.

**Interpretation:** a constant sixteenth line at one level sounds programmed. Weighting by position gives it a pulse, and the lift leans each bar into the next downbeat. A line with its own written contour, such as SLASH_MY's writing keys, does not need the curve.

**Checked:** relative to an accent, the beat sits 2.9 dB down and the "e" 7.5 dB down. The lift adds 0.6 dB across the bar, and the spread is about ±0.4 dB. In exec and reveal the accents follow the hook's 3-3-2. The AX DAY reconstruction accents only the offbeat eighth, 5.8 dB over its other sixteenths, with no lift and no spread. SLASH_MY also marks the fourth bar of some phrases with a clap flam instead of a fill: a second clap 22 ms ahead at 0.45× the gain.

No listening test isolates the curve, and the ledger says no credible source gives a velocity-variation percentage. The weights come from the code alone.

When it fails, inspect:

- A sixteenth line that sounds flat: check that the pattern has accents and that the line applies the curve.
- Accents that fight the kick or the hook: compare the accent steps with both patterns.
- Accents lost in the mix: the hats sit under the [kick duck](Dynamics%20and%20spectral%20carving.md#kick-keyed-ducking).
- A spread that sounds random: each hit's spread is drawn independently. Lower it.

## Timing jitter

Humanizing moves hits off the grid in one of two ways. **Independent jitter** draws each hit's offset fresh, as white noise. **Correlated drift** makes each deviation depend on the one before, so the line wanders ahead of the beat and back the way a player does (1/f, or long-range correlated, deviations).

**Checked:** SLASH_MY uses independent jitter. Its `humT` adds a uniform offset within ±2.5 ms to each hit, a standard deviation of 1.44 ms, on hats, rims, congas, the shaker, and nav's mallet hook. Kicks, claps, snare backbeats, bass, stabs, the lead, and plucks get none. The AX DAY reconstruction has no timing jitter on its drums or synths.

**Source status: supported:**

- Hennig et al. (2011) compared only these two kinds of humanizing. They quantized a pop song, then added timing deviations with a standard deviation of 15 ms, once correlated (1/f) and once independent (white noise), with each deviation shifting all tracks together. 39 choir members preferred the correlated version 64% of the time. The quantized original was not among the versions they heard, so the study does not show that humanized timing beats quantized timing. The authors have filed two patents related to the method.
- In the other listening studies the ledger cites, quantized timing rated at least as high as microtiming, and exaggerated deviations rated lower (Senn et al. 2016; Frühauf, Kopiez & Platz 2013; Davies et al. 2013). None found that microtiming raises groove over quantized timing. On that evidence, quantized timing is a sound default.
- The timing JND is about 6 ms for sixteenths and eighths at 120 BPM (Friberg & Sundberg 1995; source status: supported; [excerpt](../sources/excerpts/microtiming-danielsen-hennig.md)). SLASH_MY's largest offsets, 2.5 ms (4 ms on the shaker), fall under it.

SLASH_MY's `humT` is the independent kind, the one Hennig's listeners preferred less. Its 1.44 ms is about a tenth of the 15 ms that study tested, and Hennig says nothing about deviations that small. The same paper measured musicians' own deviations as correlated, with a standard deviation of about 12 ms for the most experienced players. Use that 12 ms as a measure of how players deviate. Do not copy it into a humanize control.

**Interpretation:** Start quantized. Jitter under the JND, like SLASH_MY's, probably changes little that a listener hears as timing, though the JND was measured for one displaced tone and not for an offset on every hit. If a line needs audible humanizing, correlated drift is the kind with listener support over independent jitter. Do not widen the jitter in search of feel: in the studies above, larger deviations rated lower, and none rated above quantized.

**Checked (SLASH_MY):** ±2.5 ms on most of SLASH_MY's hat and percussion lines, ±1 ms on the design hats, ±4 ms on the debrief shaker.

When it fails, inspect:

- Flams between two lines on the same step: each `humT` call draws its own offset. Share one offset or keep one line straight.
- Jitter on a hit the picture cuts to: keep jitter off lines locked to the picture.
- A change in the offset range that makes no audible difference: compare the range with the ~6 ms JND before deciding the code is wrong.
- Other parts changing when a jittered line is added or removed: the draws come from a shared seeded stream. [Seeded random streams](../cases/Soundtrack%20code.md#seeded-random-streams) shows how SLASH_MY keeps parts apart.

## Laid-back snare, ghost notes and a late top voice

**Checked:** one voice plays a fixed amount behind the grid while the parts around it stay on the grid. In writing (beats 76–92), SLASH_MY's half-time snare plays 15 ms late with no jitter. Ghost snares on odd steps sit far below it, darker, swung, and lagged a little further. The keys' top voice, the augmented hook, lands about 20 ms late. The kick downbeats stay on the grid.

**Interpretation:** a calmer section can feel laid back without a tempo change and without moving the grid the picture follows. The on-beat parts have to stay put, since the lag is heard against them.

**Checked:** snare +15 ms, fixed. Ghosts sit 12.6–15.3 dB under the backbeat, low-passed at 2600 Hz, swung 21–27 ms, and then delayed 8 ± 3 ms more, so 26–38 ms behind the grid in all. Key top voice +20–22 ms. The AX DAY reconstruction's backbeats sit exactly on the beat.

**Source status: supported:** at 96 BPM, ten drummers' laid-back snare strokes averaged 17.4 ms behind the click (individual means −4 to +43 ms), about 29 ms later than their own on-beat strokes (Danielsen et al. 2015, computed from Table I; [excerpt](../sources/excerpts/microtiming-danielsen-hennig.md)). SLASH_MY's 15 ms is near that mean. With its kick downbeats on the grid, SLASH_MY's snare trails its own on-beat hits by about half the drummers' 29 ms. The 15 ms is above the ~6 ms JND for sixteenths and near the ~12 ms JND for quarters (Friberg & Sundberg). **Interpretation:** the lag is probably large enough to be heard as late. Whether it sounds laid back or sloppy has not been tested.

When it fails, inspect:

- A laid-back snare that sounds sloppy: check what else hits on its step. A straight hit there turns the lag into a flam.
- Ghosts that pop out: compare their gain with the backbeat's, and check their low-pass.
- A drag that spreads: check that the swing ramp and the top voice's lag are not stacking on the same hits.

## Accelerating snare rolls into a gap

**Checked:** the roll's subdivision doubles as it nears a silence, from eighths to sixteenths to 32nds, while its level rises. It stops one 32nd short of the gap, so no hit lands inside the gap. Both productions build into their drop this way. SLASH_MY also has a shorter roll at the end of the debrief that leads into nav without a gap.

**Interpretation:** the rising density and level announce the drop, and the gap gives it room. [Musical development](../../video-knowhow-craft/knowledge/Musical%20development.md) and [Anticipation to title](../../video-knowhow-craft/cases/Anticipation%20to%20title.md) cover the roll's role in the phrase.

**Checked:** the AX DAY reconstruction's roll rises about 11 dB in a straight line over 3.6 beats at a fixed pitch. It turns to sixteenths on the countdown's "1" and to 32nds one beat before the gap. SLASH_MY's build roll rises 11.5 dB on a squared curve that spends most of its rise in the last two beats. Its pitch climbs from about 210 Hz on the first hit to 390 Hz on the last sixteenth, each 32nd is tuned 3% above the sixteenth before it (about 400 Hz at the top), and the kick and hats thicken under it.

The ledger lists silence before a drop as common practice without an authoritative source, and it has nothing on rolls.

When it fails, inspect:

- A roll that does not build: check the gain curve's shape (a squared curve stays quiet longer than a linear one), whether the tuning rises, and whether the kick and hats thicken with it.
- Hits that land in the gap: the loop must stop before the gap starts, or the pattern's last step must be empty.
- A last hit whose tail is clipped: anything still ringing when the gap starts is cut. For the reverb tail, see [comb and all-pass reverb](Space%20and%20delay.md#comb-and-all-pass-reverb).
- 32nds that smear: in both SLASH_MY rolls each 32nd keeps about the level of the sixteenth before it and sits about 3% higher in pitch, so a long snare decay at the top of the roll blurs them together.

## Humanized typing

**Checked:** key times are random within a range, and each key varies in level and tone. The picture reads the same key times as the sound.

**Interpretation:** a steady machine rate sounds like playback, and uneven gaps and weights sound like a hand. The sound-selection rule from the upstream motion reference applies here: attach a sound to an identified movement, discovery, transition, or completion; keep the same meaning available visually; and reserve repeated cues so that the hierarchy the sound sets up survives.

**Checked:** the AX DAY reconstruction's gaps run 55–105 ms, plus 60 ms after a space, and each key varies its level over about 4 dB and its tone between 1800 and 3200 Hz. SLASH_MY's free-typed gaps run 45–85 ms, plus 40 ms after a space, and each line is compressed to finish before the next starts. Each SLASH_MY key keeps its own cap sound, and each stroke varies ±1.5 dB. Keys timed to the beat sit within ±1.5 ms of it.

**Interpretation:** the free-typed gaps vary by tens of milliseconds, far above the ~6 ms JND, so the unevenness is meant to be heard. The beat-timed keys' ±1.5 ms sits below it. The ledger has no source on typing.

When it fails, inspect:

- Typing that sounds mechanical: check the gap range against its mean, and whether every key reuses one sound.
- Picture and sound out of step: both have to read the same key times.
- A line that runs into the next event: SLASH_MY compresses each line to fit. The AX DAY reconstruction does not, so a longer prompt would push keys past Enter (its current margin is about 0.74 s).
- Doubled keys that flam: when two presses are called at the same moment, SLASH_MY plays the second 4 ms later, with its own seed, on purpose.

## Untested ideas

None of these is part of the guidance above.

- **Correlated drift in place of independent jitter.** Hennig's listeners preferred correlated over independent deviations at a 15 ms standard deviation. Whether that holds at SLASH_MY's 1.44 ms, or at any depth against quantized timing, is untested. Check the authors' patent filings before adopting their method.
- **Parameter automation every few bars, so loops never repeat exactly.** SLASH_MY already drifts some values across a section: writing's swing, exec's stab cutoff, the build's gains and tuning, and a hat autopan once a bar. Apart from the seeded spread, most of its loops still repeat their gains bar to bar. The AX DAY reconstruction's hats and bass repeat identical gains every bar. The ledger has no source for this.
