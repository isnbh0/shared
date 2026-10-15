# Space and delay

Two code-built soundtracks place their sounds in depth with these tools: a comb and all-pass reverb, send amounts set by each voice's role, a room for each scene, predelay and high-passed sends, a separate vocal plate, a dotted-eighth ping-pong delay, delay throws into gaps, and a low end kept centered and dry. [Audio synthesis](Audio%20synthesis.md) covers the signal path and offline rendering. [Dynamics and spectral carving](Dynamics%20and%20spectral%20carving.md) covers the ducking and band carves that act on these returns. Stereo width at the master and room tone are in [Mastering and delivery](Mastering%20and%20delivery.md). [Audiovisual synchronization](Audiovisual%20synchronization.md) explains how the exported reverb times drive the glow in the picture. External claims come from the [audio source ledger](../sources/Audio%20sources.md).

SLASH_MY is the one production John endorses (audio snapshot `fd543f2a`). The AX DAY reconstruction is a rerender of Stage intro, kept as a specimen (snapshot `e5ae340d`). Parameter tables, values for each voice, line references, and walk-throughs of the code are in the [Soundtrack code case](../cases/Soundtrack%20code.md#space-and-delay).

The code values below are starting points for adaptation, and [reading a claim](../Editorial%20notes.md#reading-a-claim) gives what each evidence label means. Each "why it may help" below is an interpretation; check it by ear against the actual mix.

## Comb and all-pass reverb

Both soundtracks build their reverb in code from a Freeverb-style network. **Checked:** parallel feedback combs (delay lines that feed back into themselves) run into a chain of all-passes, which smear the comb echoes into a dense tail. Each comb's feedback passes through a low-pass, so the highs die sooner than the lows. The right channel's lines are slightly longer than the left's, so the two returns differ even when the input is the same.

**Interpretation:** a few delay lines give a dense tail without an impulse-response file, and the tail is identical on every render. That suits a synthetic score that is built and rebuilt from code. It fits poorly when the tail must sound like a particular real room; see [untested ideas](#untested-ideas).

**Checked:** the AX DAY reconstruction runs six combs at feedback 0.86 and damping 0.3 for the whole piece. SLASH_MY runs eight and sets feedback (0.74–0.92) and damping (0.12–0.55) for each room.

The two handle silence differently. SLASH_MY clears the reverb at the gap before the drop, so the tail of the build does not come back after it. The AX DAY reconstruction's gate mutes the output, reverb included, while the reverb keeps running underneath, so the build's tail returns with the drop roughly 5–6 dB lower (**Interpretation:** derived from the computed decay, not measured).

The ledger has no source on comb and all-pass design, so this section is based on the code alone.

When it fails, inspect:

- A metallic or fluttering tail: comb lines too short, or feedback near 1.
- A tail identical in both channels: the right-channel offset is missing, or a room `width` below 1 has folded the sides together.
- A decay you hear that does not match the exported decay time: the formula gives only the low-end decay. If the number drives something, measure an impulse through the return.
- A tail that runs into a silence or across a cut: check whether the network is cleared there.

## Send amounts by role

**Checked:** each voice sets its own send to the reverb (and in SLASH_MY, to the delay), taken after the pan and the envelope. How deep a voice sits follows its role.

**Interpretation:** a dry kick and bass keep the beat close, while pads, ornaments, and transitions take the space and sit behind it.

**Checked:** the kick and bass send nothing in either production. The AX DAY reconstruction's chime sends 0.8 and its arpeggio 0.7. SLASH_MY's pad sends 0.5 and its closed hat 0.03. SLASH_MY also multiplies the delay send of the pluck and the lead by 2.5, because, in the code's words, "the dotted-eighth ping-pong is part of the hook."

When it fails, inspect:

- A part that sounds too distant: its own send first, then the room's input gain.
- A hard-panned part whose reverb stays on its side: sends are post-pan and each channel has its own network, so only a room `width` below 1 moves the reverb across.
- Low end in the tail: see [lows centered and dry](#lows-centered-and-dry).

## A room per scene

SLASH_MY gives each place in the film its own reverb settings. The AX DAY reconstruction runs one room for all 24 seconds. **Checked:** at each seam the send switches to the next room within 5 ms, and the old room keeps ringing under the new one. The returns are never crossfaded. Picture and score read one seam list, so the room changes on the cut.

**Interpretation:** the listener can hear a cut as a change of place. Exec is tight and dry, design wide and airy, nav long and dark, and the reveal opens out in four steps. A piece that stays in one place, like the AX DAY reconstruction, needs only one room.

**Checked:** the rooms' decay times run from about 0.5 s (exec, marked "tight, dry" in the code) to about 3.1 s (the lock). By construction, the design formula computes these from comb lengths and feedback, and they are exported to `score-events.json`. They are not measured, and they leave out damping, predelay, and the send high-pass.

When it fails, inspect:

- A click or a chopped tail at a seam: switch the send and let the old room ring; don't crossfade the returns.
- A long room's tail clipped: each room's render window (5 s) must outlast the longest decay.
- A room change that misses the cut in the picture: both media must read the same seam list.
- A busy section blurred: compare the room's decay with how dense the section's notes are.

## Predelay and high-passed sends

In SLASH_MY, each room's send waits a few milliseconds before it enters the reverb and is high-passed at 12 dB/octave on the way in. The AX DAY reconstruction has neither. **Interpretation:** the predelay keeps a dry attack clear of its own reverb, and the high-pass keeps lows out of a tail where they would thicken the low mids.

**Source status: partly:** the practical guidance is to high-pass the reverb around 200 Hz and use roughly 20–80 ms of predelay on vocals, shorter on drums. Sound On Sound suggests "a 200Hz 12 or 18 dB/octave filter before or after the reverb" ([audio source ledger](../sources/Audio%20sources.md)).

**Checked (SLASH_MY):** SLASH_MY's default send high-pass is 180 Hz, close to that guidance. Design's room uses 320 Hz, well above what the source suggests. The vocal plate's 30 ms predelay falls inside the vocal range. The music predelays (6 ms in exec up to 42 ms in writing) are set for each place, so drums and pads in one room get the same predelay.

When it fails, inspect:

- Attacks smeared by their own reverb: predelay too short for the part.
- A gap between the dry sound and its tail, like a slap-back: predelay too long.
- A thin or hollow room: send high-pass set too high.
- A low-mid wash on bass-heavy passages: high-pass too low, or a low voice sending (see [lows centered and dry](#lows-centered-and-dry)).

## Vocal plate

The SLASH_MY vocal sends only to its own short, bright reverb and its own echo, kept apart from the music rooms. The AX DAY reconstruction has no vocal. **Checked:** "plate" is the name of the setting and does not mean a plate model; it is the same comb and all-pass network with fixed settings. Its returns skip the place tilt and the breath cut, so the vocal's tail rings on through the breath after the music stops.

**Interpretation:** the vocal stays in one space while the music changes rooms around it, and its tail does not jump at the scene seams. If the vocal should move with the scenes, put it on the room sends instead.

**Checked (SLASH_MY):** a computed decay of about 1 s, from the same design formula as the rooms and not measured. That is shorter than every music room except exec and the reveal. Its damping of 0.18 is among the brightest of SLASH_MY's settings, and its predelay is 30 ms.

When it fails, inspect:

- The vocal sounding in two spaces: it should send only to its own buses.
- A harsh or sibilant tail: damping too low.
- Words smeared together: the predelay or the plate's length.
- A tail cut off at the breath: the vocal returns must stay outside the breath gate.

## Dotted-eighth ping-pong delay

SLASH_MY has two stereo delays, one for the music and one for the vocal. The AX DAY reconstruction has none. **Checked:** each delay sums its input to mono, high-passes it, and returns echoes that alternate left and right a dotted eighth apart. Each repeat passes through a low-pass on the way back, so later echoes are quieter and darker. The echoes also feed the reverb, so they sit in the current room. Both delays are cleared at the gap before the drop.

**Interpretation:** the echo time falls on the sixteenth grid, so the repeats add rhythm. SLASH_MY's tempo is fixed, so one time value covers the whole film.

**Checked (SLASH_MY):** 0.75 beat (375 ms at 120 BPM), with each later left–right pair about 7 dB below the one before. **Reported:** a throw at beat 39.5 had sent the swung copy of its note, 135 ms behind the grid, so every echo was late. Commit `683c2215` sent the on-grid copy instead.

When it fails, inspect:

- Echoes off the grid: check what was sent. A swung or humanized copy moves every echo with it.
- Echoes building into a wash: the feedback amount.
- Harsh repeats: the feedback low-passes.
- Low thump in the echoes: the input high-pass.
- Echoes ringing across a cut or a silence: the delay resets.

## Delay throws into gaps

On the last hook note of a phrase, SLASH_MY raises that one note's delay send, so its echoes carry into the gap that follows. **Checked:** the bed above 300 Hz steps back while the echoes ring ([delay-throw carve](Dynamics%20and%20spectral%20carving.md#delay-throw-carve)). Where a thrown note would still be sounding when its first echo arrives, as with the held keys in writing, the dry note is cut short. Picture and score share one throw list, and the engine refuses a score whose throws differ from it. The AX DAY reconstruction has no throws.

**Interpretation:** ordinary sends stay low, and an echo appears only where the phrase leaves room, so each echo is placed on purpose. The ledger lists delay throws timed into gaps as common practice with no authoritative source, so this section cites only the production.

**Checked (SLASH_MY):** the design stab at beat 63.5 jumps from a delay send of 0.12 to 1.5, and the bed dips 4 dB (6 dB in nav). **Reported:** after the fix to the throw at 39.5, commit `683c2215` measured its four echoes at +12, +16, +13, and +3 dB over the bed before the throw.

When it fails, inspect:

- A first echo buried in its own note: the dry note's hold and release.
- Echoes buried in the bed: the throw send and the timing of the dip.
- A dip heard as a hole in the bed: dip depth and ramps. Only the band above 300 Hz should move.
- The picture's throw list disagreeing with the score: compare the engine's throw list with `score-events.json`.

## Lows centered and dry

The kick, the bass, and the sub sit in the middle with no reverb or delay send, and filters keep lows out of the sends from the other voices. **Interpretation:** a low end with no tail stays tight under the kick and keeps its level when the mix is summed to mono.

**Checked (SLASH_MY):** the kick, bass, and impact sub are centered and send nothing. Every room send is high-passed at 180 Hz or above and the delay's input at 260 Hz, and the pitched voices have their own high-pass as well. The width comes from detuned voices and from doubles spread across the pan, and the low end adds none. The master also narrows the side below 120 Hz; see [mono low end and width by place](Mastering%20and%20delivery.md#mono-low-end-and-width-by-place).

**Checked (AX DAY reconstruction):** the kick, bass, and sub are centered and dry. Three low parts, though, reach a reverb that has no high-pass: the opening drone sends 0.5, the drop chord 0.6, and the closing 55 Hz note 0.3. Damping shortens only the top, so their lows ring for the full decay.

**Source status: partly:** "Mixes often keep the low end mono below roughly 100–125 Hz" ([iZotope](https://izotope.com/en/learn/mono-vs-stereo)). **Source status: supported:** "Mud usually lives in the low mids, around 250–500 Hz" ([Sound On Sound](https://www.soundonsound.com/techniques/cubase-managing-low-mids-frequency-2)).

When it fails, inspect:

- Low end lost or changed when folded to mono: a panned or doubled low part. Check the correlation below about 120 Hz.
- A boomy or blurred low end after hits: lows in a send. Check the send high-pass and which low voices send.
- The low end changing at a room switch: a room with a lower send high-pass.

## Untested ideas

- **Convolution reverb with recorded impulse responses.** Neither production uses convolution. A recorded response would replace the comb network's decay and color with those of a real room or plate. The cost is an asset whose provenance and license must be tracked (see [Assets and provenance](Assets%20and%20provenance.md)), and the exported decay times would then have to be measured from the response. The ledger has no source for this.
- **Delay settings per place.** SLASH_MY runs one tempo-synced time with low-passed feedback for the whole film. Other note values, feedback amounts, filter cutoffs, or a swept feedback filter that change with the rooms are untested. The ledger has no source for this.
- **Mid/side treatment of reverb returns.** SLASH_MY's room `width` already scales the side of each return. Neither production filters a return's mid and side separately, for example by high-passing the side harder or keeping the return's mid clear under the vocal. The nearest ledger support is the mono-low-end claim above.
- **A mono-sum check of the opposite-panned doubles.** SLASH_MY's supersaw and vocal doubles add a slightly late, slightly detuned copy at the opposite pan, which can comb-filter in mono. No mono fold of these passages has been rendered or measured.
