# Dynamics and spectral carving

Two code-built soundtracks make room in the mix with these tools: kick-keyed ducking, band carves keyed to events, static cuts in the low mids, a drum bus (glue, a parallel crush, a clip on the low band), and arrangement moves that do a mix's work (an air shelf, bed dips before hits, section tilts). The voices are in [Sound sources and voices](Sound%20sources%20and%20voices.md), reverb and delay in [Space and delay](Space%20and%20delay.md), master-bus processing and loudness in [Mastering and delivery](Mastering%20and%20delivery.md), and filter types in [Audio synthesis](Audio%20synthesis.md). External claims come from the [audio source ledger](../sources/Audio%20sources.md).

SLASH_MY is the one production John endorses; its code is cited at `fd543f2a`. The AX DAY reconstruction is a rerender of Stage intro, kept as a specimen and cited at `e5ae340d`. Both run at 120 BPM (0.5 s per beat), and the times below are in beats. In SLASH_MY, exec runs 24–56, design 56–76, writing 76–96, nav 96–104, and the build 104–112. The reveal drops at 112, after the film's one silence (111.75–112), reaches the wall at 116, and drops again at 120. Line references, parameter tables, and the commits' measurements are in the [Soundtrack code case](../cases/Soundtrack%20code.md#dynamics-and-spectral-carving).

The code values below are starting points for adaptation, and [reading a claim](../Editorial%20notes.md#reading-a-claim) gives what each evidence label means. Advice on when to use a technique is interpretation ([what John's endorsement covers](../../video-knowhow-craft/cases/SLASH_MY.md)); check it by ear against the actual mix. Figures marked "computed here" are arithmetic on the code's formulas, not measurements of the render. Of these techniques, the AX DAY reconstruction has only kick ducking. Where a section does not mention the reconstruction, the reconstruction lacks the technique.

## Kick-keyed ducking

Each kick dips one shared gain curve, and each voice follows that curve by its own amount, so the bed drops on the beat and recovers before the next one.

**Checked:** SLASH_MY's `addDuck` (`audio.js` L136–145) gives each dip a 4 ms attack and an exponential release. Where dips overlap, the deeper one wins. Voices duck before their sends, and the reverb and delay returns duck again. Nothing clamps the product, so a voice whose amount times the kick's depth goes past 1 flips polarity at the bottom of the dip. The AX DAY reconstruction's `duck()` (L29–37) steps the gain to 0.3 (−10.5 dB) on the kick, with no attack. Only its bass and supersaw use it, though the comment says everything melodic ducks, and the offbeat bass loses less than 1 dB. As the reconstruction's sound analysis records, only the pad and the drop chord audibly pump.

**Interpretation:** Use it when a sustained bed or bass sits on the kick's beat. The kick comes through without being raised, and the swell between kicks adds a pulse. Parts that start after the dip gain little. A deep, slow duck is heard as pumping; that is a style, and it fixes nothing.

**Checked (SLASH_MY):** a groove kick ducks at depth 0.6 with a 0.1 s release, and an impact at 0.85 with 0.3 s. The bass follows by 0.75 (1.3 in exec), the pad by 0.5, and the lead by 0.3. A default pad dips about 3 dB under a groove kick (computed here). **Reported:** raising exec's bass amount from 0.72 to 1.3 deepened its measured dip under the kick from 2.1 to 4.6 dB (`72d00e0c`).

**Source status: supported:** the ledger's sources give "a fast attack time (1-5 ms)" and a release synced "with the tempo of your track" ([Mastering The Mix](https://www.masteringthemix.com/blogs/learn/achieving-the-pump-effect-in-music-production), [Sound On Sound](https://www.soundonsound.com/techniques/live-side-chain-compression)). SLASH_MY's attack fits. Neither production syncs its release to the tempo.

On failure, inspect:

- A voice that never ducks: whether it multiplies the curve at all, and whether it sounds while the curve is down.
- A click on each kick in a sustained voice: a step with no attack.
- A low end that turns hollow on the beat: amount × depth near or above 1.
- A bed that never recovers: a release longer than the gap between kicks.
- Reverb or delay swelling between kicks: the returns are not ducked, or the sends are tapped before the duck.

## Dynamic band carves

A carve takes one band out of one part, and only while another part is sounding in that band.

**Checked (SLASH_MY):** most carves are scheduled, not detected. Their keys are event times the score already holds, such as kicks, strikes, stabs, and sung words. `keyCurve` (L1739–1750) eases each key in just before its event, holds it, and releases it. Overlapping keys combine by minimum. The cut is either a bell or everything above a corner. One carve, `PAD_DIP`, follows the level of the vocal and the lead in their band instead, like a sidechained dynamic EQ.

**Interpretation:** Use it when a sustained part masks a short foreground sound in a known band. The foreground comes through without being raised, and the carved part keeps its full spectrum between keys. Schedule the keys when the score knows its event times. Key from level when a part's level moves.

**Checked (SLASH_MY):** under the sung "my" at the drop, the bed loses 4 dB in a bell at 1.1 kHz (`MY_POCKET`). Under the hook stabs in exec and design, the drums lose 5 dB at 1.7 kHz (`CARVE_DB`). **Reported:** with `MY_POCKET`, the voice's level over the rest of the mix at 500–2500 Hz went from −0.5 to +1.4 dB in the word's first 0.3 beat (`70c9dfe5`).

**Source status: partly:** a dynamic EQ keyed from another part can "duck just the masking bass frequencies and nothing else" ([iZotope](https://www.izotope.com/community/blog/5-ways-to-use-dynamic-eq-with-sidechain), [Sound On Sound](https://www.soundonsound.com/techniques/cubase-frequency-2s-dynamic-eq)). No source gives fixed carve bands. **Interpretation:** every carve band on this page was found for SLASH_MY's own parts and is not a standard.

On failure, inspect:

- A part that sounds hollow after each key: the depth, or a hold too long for the gap it opens.
- A key that lands off its sound: the key is the event time, which can differ from the audible onset. See [sound and picture on one beat grid](Audiovisual%20synchronization.md#sound-and-picture-on-one-beat-grid).
- A carve that does nothing: the clash is in another band, or on another bus.
- Overlapping keys that seem shallow: the deeper key wins, and keys do not add.

## Lead dip under the kick

The lead cuts a band out of itself whenever the kick's duck is down, so the kick's click comes through it.

**Checked (SLASH_MY):** `lead()` (L515–521) scales the shared kick curve by the voice's `carve` amount, capped at 1, and subtracts that share of a bell at 3.2 kHz. Only the reveal's lead uses it. `LEAD_CARVE_DB` is a separate cut in the other direction: the lead's notes cut the FX bus 4 dB at 1.7 kHz.

**Interpretation:** Use it when a loud, bright lead sits in the kick's click band. The lead can stay loud between kicks.

**Checked (SLASH_MY):** `carve: 1.4`, which makes the dip about −21 dB at 3.2 kHz under a reveal kick (computed here) and a full notch under the impacts. **Reported:** the commit that added the dip also raised the click and pre-ducked the reveal kicks, so its measurement does not isolate the dip (`e099d948`). The dynamic-EQ claim is the nearest source (source status: partly), and no source gives the band.

On failure, inspect:

- A kick that still smears into the lead: look at a spectrum to find where the click and the top of the lead actually sit, before you choose the center.
- A lead that flutters with the beat: the dip's depth, which can reach a full notch on every kick.

## Low band keyed to the kick

In the reveal, the kick takes the lowest band for itself. The FX bus and the bed are split at 150 Hz, and only their low band dips on each kick.

**Checked (SLASH_MY):** `SUB_KEY` (L1862–1897) takes each bus's low band from a Linkwitz-Riley split, multiplies it by a key on the reveal's kicks, and sums it back with the high band. The FX key skips the impact kicks, whose kick and boom are one hit. The build's hit at 104 dips through a zero-phase low band instead of a split.

**Interpretation:** Use it when the kick shares the sub with impact booms or a rolling bass. The kick's weight stands clear, and neither part thins above the split.

**Checked (SLASH_MY):** the bed's low band dips 18 dB on each reveal kick, and the FX bus's dips 10 dB. **Reported:** with the bed key at 6 dB, the kick's level over the floor below 120 Hz rose from 6.7 to 11.9 dB at 114 (`72d00e0c`).

**Source status: partly:** keying only the clashing band is the dynamic-EQ claim. **Source status: supported:** "A Linkwitz-Riley crossover alignment is not linear phase" ([RaneNote 160](https://www.ranecommercial.com/legacy/pdf/ranenotes/Linkwitz_Riley_Crossovers_Primer.pdf)), so the split shifts the phase around 150 Hz for the whole bus, even while the key is open.

On failure, inspect:

- Peaks that move or grow after a split is added: use a zero-phase low band and subtract a share of it. The build's hit gave up its split for this reason (`c893a310`).
- An impact's boom thinned by its own kick: skip the impact's kicks on the bus that carries the boom.
- A floor that pumps audibly: the depth and hold against the rests in the bass pattern.
- The low end's width and dryness: see [lows centered and dry](Space%20and%20delay.md#lows-centered-and-dry).

## Strike carves

Under each struck stroke, the bed and the drums step back above a corner frequency for a fraction of a beat, so the top of the stroke comes through over the music.

**Checked (SLASH_MY):** `STRIKE_ROOM` (L851–854) holds each carve for 75 ms and releases it over 30 ms, cutting everything above a corner on the bed and drum buses. The drop's strokes also dip the lead, the pads, and the tail of the drop impact.

**Interpretation:** Use it when a short struck sound must come through a full mix without being raised into the limiter. In dense music, open the carve ahead of the stroke.

**Checked (SLASH_MY):** the strokes in exec and design take 6 dB above 1.3 kHz. The drop's strokes take 10 dB above 1.6 kHz, opened 150 ms ahead; on the kick at 114 the carve is 12 dB and the kick steps 5 dB down. **Reported:** with the 10 dB carve, the drop's five strokes measured +4.4 to +6.5 dB over the mix, up from +1.9 to +5.3 (`fff4099e`). The session records (held in John's workspace) hold the assignment decision behind the carves. The strokes sat buried under their slams yet drove the limiter, so the decision carved the slams, about 4 dB at 1–4 kHz for about 60 ms, and explicitly declined to raise the strikes.

**Source status: partly:** the dynamic-EQ claim. No source gives the corners or the depths.

On failure, inspect:

- A dark hole in the lead or the bed after each stroke: the depth is too great or the corner too low. The exec carve was halved from 12 to 6 dB after a spectrogram showed this (`00e16446`).
- A stroke still masked: find where its energy sits before you choose the corner.
- A stroke on a kick that drives the limiter: step the kick back under it.
- Reverb and delay still covering the stroke: the carves cut the dry buses, and the returns take only a full-band dip.

## Delay-throw carve

While a thrown note's echoes play, the bed above 300 Hz steps back, so the echoes land in a cleared space. The throws themselves are in [delay throws into gaps](Space%20and%20delay.md#delay-throws-into-gaps).

**Checked (SLASH_MY):** for each throw, a window (L1830–1841) runs from just before the first echo to just past the fourth, with smooth ramps, and stops at the build. The window is fixed in time and does not follow the echoes' level.

**Interpretation:** Use it when a throw should be heard as a gesture without raising the delay return.

**Checked (SLASH_MY):** 4 dB, and 6 dB in nav. Writing also cuts its thrown notes 0.6 beat after the throw, so the first echo lands in a gap. **Reported:** `d7aeae3d` reports onset figures for four throws without naming what they are measured against.

**Source status: practice:** throws timed into gaps are common practice without an authoritative source.

On failure, inspect:

- Echoes still buried: compare the window's start with the actual first echo.
- A bed that sags audibly for two beats: the depth is too great for the passage.
- A carve that runs into the next section: the cap at the boundary.

## Static cuts and mud bells

Fixed cuts, and cuts that switch by section, keep the low mids clear for the kick and the bass.

**Checked (SLASH_MY):** most voices high-pass between 110 and 170 Hz, and the supersaw can subtract a 400 Hz bell. From 112 to 128 only, `BOX_DB` and `MUD_DB` (L1763–1777) switch in a 700 Hz cut on the pads and the lead and a 400 Hz cut on the pads.

**Interpretation:** Use it when stacked chords and pads build up in the low mids. The chords and pads stay full without crowding the kick and the bass. A switched cut suits a passage that is denser than the rest.

**Checked (SLASH_MY):** the supersaw high-passes at 150 Hz and the pad at 140 Hz. The reveal's stabs take 3.5 dB at 400 Hz, and from 112 the pads and the lead lose 3.5 dB at 700 Hz. No production record reports on these cuts.

**Source status: supported:** mud "usually" lives in the low mids, "broadly speaking, around 250‑500 Hz" ([Sound On Sound](https://www.soundonsound.com/techniques/cubase-managing-low-mids-frequency-2)). SLASH_MY's 400 Hz bells sit in that range, and the 700 Hz box cut sits above it. The source gives a range and does not give a center for any voice.

On failure, inspect:

- Low-mid build-up when many voices play: which voices lack a high-pass.
- Thin pads in the reveal: the box and mud cuts against the pads' level.
- A switch heard at a section boundary: the glide time.

## Drum glue compression

All the drums pass through one compressor before the parallel crush.

**Checked (SLASH_MY):** `compress()` (L2068–2084) is feed-forward and stereo-linked, with a soft knee. Its thresholds follow the drum bus's input trim, so changing the trim changes the level and leaves the compression the same.

**Interpretation:** Use it when drum voices built separately sound like loose parts. A gentle compressor may make them move together.

**Checked (SLASH_MY):** ratio 3, attack 8 ms, release 120 ms, threshold −13 dB re the bus's full scale. The render prints the gain reduction, but no commit reports it, so how hard the glue works is unknown.

**Source status: partly (one example):** one worked example starts mix-bus glue at "a ratio of 2:1, 10ms attack, auto‑release and about 2dB of compression" ([Sound On Sound: Cytomic The Glue](https://www.soundonsound.com/reviews/cytomic-glue)). That example is for a mix bus, not a drum bus.

On failure, inspect:

- Kick fronts flattened: the attack is too fast or the threshold too low. Read the printed gain reduction.
- Hats and claps pumping after each kick: the release against the tempo.
- A trim that changes the compression: the thresholds are not tied to the trim.

## Parallel crush

A heavily compressed copy of the drum bus is blended in under the dry bus.

**Checked (SLASH_MY):** L2086–2102. The copy is taken after the glue, crushed, band-limited to 50 Hz–10 kHz, and added back at a blend set for each section.

**Interpretation:** Use it when the drums need density between the hits. The copy lifts tails, ghost notes, and claps while the dry hits keep their fronts. Pulling the blend out before a drop makes the drop jump.

**Checked (SLASH_MY):** ratio 8, attack 1 ms, makeup `PAR_MAKEUP` 3.75 (about +11.5 dB). The blend is 0.45 in most grooves, 0 over the last bar of the build "so the drop keeps its jump", and 0.5 in the reveal. No production record reports on the crush.

**Source status: supported:** parallel ("New York") compression blends a heavily compressed copy with the dry signal ([Yamaha Hub](https://hub.yamaha.com/proaudio/recording/the-advantages-of-parallel-processing/)). No source gives the blend or the makeup.

On failure, inspect:

- A level jump when the blend changes: the makeup's real gain, and the glide.
- Smeared or swelling room noise: the threshold, the ratio, and the copy's band limits.
- A drop that arrives flat: the blend over the bar before it.

## Low-band drum saturation through a crossover

The drum bus is split at 1.5 kHz, and only the low band goes through a soft clip.

**Checked (SLASH_MY):** L2196–2238. After the tilt and the air shelf, a Linkwitz-Riley crossover splits each drum channel. The low band passes unchanged up to a knee, bends through a `tanh` toward a ceiling, and rejoins the untouched high band. No unfiltered copy joins them. The AX DAY reconstruction bends its kick inside the voice instead; see [layered kick](Sound%20sources%20and%20voices.md#layered-kick).

**Interpretation:** Use it when the kick's body should be clipped for density but a hat or clap on the same hit should stay clean.

**Checked (SLASH_MY):** crossover 1500 Hz, ceiling 0.94, knee at 62% of the ceiling. **Reported:** over the first 30 ms of the reveal kicks, the split cut the maximum peak reduction from 7.1 to 2.8 dB and the loss above 3 kHz from 2.0 to 0 dB (`5c8bcda8`).

**Source status: supported:** LR4 bands recombine cleanly with each other but not with an unfiltered parallel copy, and "a Linkwitz-Riley crossover alignment is not linear phase" ([RaneNote 160](https://www.ranecommercial.com/legacy/pdf/ranenotes/Linkwitz_Riley_Crossovers_Primer.pdf)). Transients near 1.5 kHz shift in phase.

On failure, inspect:

- Comb filtering or a hollow band near the crossover: an unfiltered copy summed with the bands.
- Peaks that move or grow after the split: the phase shift. Compare against a zero-phase low band.
- Clipped hats or claps: the crossover is too high.
- A shelf after the clip that rebuilds the shaved peaks: keep the clip after the tilt.

## Air shelf that leaves after the drop

A high shelf adds air to the whole mix before the drop and through its first hit, then goes away.

**Checked (SLASH_MY):** `AIR_DB` (L2196–2228) adds a high shelf above 8 kHz on the music and drum paths, and leaves the vocal alone. It fades out after the drop's hit, returns for the wall (116–119), is off again until 128, and is back for the outro.

**Interpretation:** Use it when the biggest hit should open up the top and then settle, so the body of the drop carries the section.

**Checked (SLASH_MY):** +2.5 dB above 8 kHz, faded out over 0.5 beat after 112. There is no Reported measurement and no source in the ledger.

On failure, inspect:

- Hiss or harshness: the shelf's corner and gain on noisy sources.
- An audible switch: the fade and glide times.

## Bed dips before hits

The bed steps down just before a hit and is back up on it, so the hit lands from a lower floor.

**Checked (SLASH_MY):** `BED_GAIN` (L831) multiplies its gain functions into the bed and leaves the FX and the returns alone. The dip before the wall stops short of silence, so the gap before the drop stays the film's one silence. In the AX DAY reconstruction, the level moves only through note gains, the fade, and a gate before the drop that cuts back in with no fade.

**Interpretation:** A hit can sound bigger without being raised. Place the dip where the hit masks its own return. The nearest source, which is about arrangement in general and not about dips before hits, says "there's little that processing can do to compensate" for an arrangement problem (source status: partly; [Sound On Sound: Mix Rescue](https://www.soundonsound.com/techniques/mix-rescue-free-radicals)).

**Checked (SLASH_MY):** `SLOT_HIT` takes the bed 4 dB down over the last half beat before the slams in design and writing, and brings it back in 5 ms on the slam. `WALL_IN` takes it 6 dB down before the wall. **Reported:** `d7aeae3d` reports figures for these dips without naming the measure.

On failure, inspect:

- A dip heard as a gap or a hiccup: the depth and the length of the lead-in against the passage.
- A hit that swells in instead of landing: a late or slow return.
- Dips that compound: `BED_GAIN` multiplies them, so two at once go deeper than either one.

## Section tilt shelves

Each section sets a low shelf at 250 Hz and a high shelf at 5 kHz on the music and drum paths, so each place has its own tonal balance. The vocal bypasses them.

**Checked (SLASH_MY):** `TILT` (L2204–2205), with the gains gliding over 20 ms. The drums take the tilt on their own path, before their clip. In the reveal the drums and the bed also gain 3.5 dB below 100 Hz. Over design, a separate cut takes 4 dB off the sub below 60 Hz, so the sub in design stays under the drop's.

**Interpretation:** A tilt can mark a change of place, and can hold back brightness until the drop.

**Checked (SLASH_MY):** the high shelf is −2 dB in exec, +5.5 dB in design, +2 dB at the drop, and +3.5 dB at the wall. The low shelf moves at most 1.2 dB. No Reported measurement covers the tilt, and the ledger has no source for it.

On failure, inspect:

- A section that sounds dull or harsh only on a small speaker: the shelf gains against the playback system.
- A tilt change heard as a click or a jump: the glide time, and whether the shelf sits before or after a clip.

## Untested ideas

- **Untested idea:** transient shaping on the drum bus, separate from compression. The ledger has no source for it. SLASH_MY already has a transient shaper, `punch()` in `sfx.js`, but uses it only on the exec slams.
- **Untested idea:** a listening check of the drop's strike carves for pumping in the top. The 10 dB step (12 dB on 114) is deep. `fff4099e` measured how fast the music returns, but no one has listened for pumping. **Interpretation:** the idea that this depth may pump comes from reading the numbers, and no source gives a correct depth.
- **Untested idea:** release times derived from the tempo. The ledger's ducking source says to sync the release "with the tempo of your track" (supported). Both productions use fixed seconds.
