# Music under voice-over

A music bed under narration has to leave the words clear. [Mastering and delivery](Mastering%20and%20delivery.md) covers full-mix loudness and true peak, and [Accessibility and perception](Accessibility%20and%20perception.md#audio-content-and-alternatives) covers captions and transcripts. External claims come from the [audio source ledger](../sources/Audio%20sources.md).

Neither code-built soundtrack in the package has speech. SLASH_MY (snapshot `fd543f2a`) has one voice, a synthesized sung word, "my" ([Sound sources and voices](Sound%20sources%20and%20voices.md)), and the AX DAY reconstruction (snapshot `e5ae340d`) has no voice. The targets below therefore come from broadcast research and guidance. Each section names the SLASH_MY code that would carry over to narration, and using that code under narration is an untested idea. The [Soundtrack code case](../cases/Soundtrack%20code.md#carry-over-code-in-slash_my) shows where that code is.

The sources use different units: LU (a difference in BS.1770 integrated loudness), a "PPM point" (a peak-meter step), and WCAG's decibels (RMS in its example, sound pressure in its test). They do not convert into one another exactly.

## How far below the voice the music sits

The level difference (LD) is the voice's integrated loudness minus the music's, in LU.

**Source status: supported:** Torcoli et al. ([JAES 2019](https://doi.org/10.17743/jaes.2019.0052)) "recommend an LD of at least 10 LU for Commentary over Music (CoM) and 15 LU for Commentary over Ambience (CoA). Higher LDs should be used for location dialog." The upper limits that still sound good are 15 LU for music and 20 LU for ambience, and listeners accepted about ±3 LU around their preference. In 12 TV documentaries, commentary over music mostly sat 10–15 LU above the bed. Non-experts wanted the music about 4 LU lower than experts did. The 22 listeners had normal hearing and median ages near 25, and they heard 9-second clips without picture.

**Source status: partly (secondary):** German public broadcasters (ARD/ZDF) ask for speech at least 7 LU above the background. Their 16–23 LU range applies to one voice over another, such as a translation over the original speech. It is not a range for music under narration.

**Source status: supported:** the BBC's advice is to trim from the mixer's own balance. "Take the music down. A mix which sounds fine in the dub may still cause problems for some viewers" ([BBC, *Hearing Impaired Audiences*, 2011](http://downloads.bbc.co.uk/guidelines/editorialguidelines/pdfs/hearing-impaired.pdf)). It asks for one PPM step, which the BBC Academy puts at 4 dB.

**Interpretation:** a code-built video holds voice and music as separate stems, so you can measure the LD. Start between 10 and 15 LU for narration over music. Lean toward 15 LU for a general audience, since non-experts wanted quieter music than the experts who mix it. Go higher under location dialogue.

**Checked (SLASH_MY):** the code sets no value for this. SLASH_MY's BS.1770-4 meter ([`loudness`](../cases/Soundtrack%20code.md#carry-over-code-in-slash_my)) runs only on the master.

When it fails, inspect:

- Words hard to follow in a mix that sounded right: take the music down about 4 dB and listen again.
- A measured LD that disagrees with the ear: check that both stems were measured over the same span, with the same meter, as integrated loudness.
- Music that seems to vanish: an LD past about 15 LU.
- A translated voice over the original speech: that is voice over voice, which has its own target.

## Ducking under speech

Ducking lowers the music only while the voice speaks, so the bed can sit fuller between lines. Either a sidechain compressor follows the voice's level, or a scheduled envelope uses known speech times.

**Source status: supported:** voice ducking "is usually accomplished by feeding a compressor's side‑chain (its control circuit) from the voice track while routing the music though the compressor" ([Sound On Sound, VoxDucker review](https://www.soundonsound.com/reviews/soundevice-digital-voxducker)). Broadcast ducking adds two timings to attack and release. A shift starts the duck before speech begins, and a hold "prevents pumping in short speech gaps" (Torcoli et al. 2019). Torcoli's test used 500 ms for attack, release, and shift, with a 1,500 ms hold. A faster audio-description setting (200 ms each, no hold) did not change the level difference listeners preferred. No handbook or broadcaster defines best-practice ducking.

**Source status: partly (one example):** one DAW tutorial gives this setup: with a sidechain compressor, use the highest ratio and set the threshold so that the quietest real speech triggers it. Make the release "long enough that the music doesn't pop back up during breaths in the dialogue, but short enough that the music rises reasonably quickly after a patch of dialogue" ([Sound On Sound](https://www.soundonsound.com/techniques/live-side-chain-compression)).

No source gives a ducking depth. **Interpretation:** Set the depth so that the music under speech sits at the target LD.

**Checked (SLASH_MY):** SLASH_MY's [kick-keyed ducking](Dynamics%20and%20spectral%20carving.md#kick-keyed-ducking) ([`addDuck`](../cases/Soundtrack%20code.md#carry-over-code-in-slash_my)) is built for a beat. Each dip starts on the kick with a 4 ms attack, has no hold, and releases exponentially, so the bed recovers before the next kick. Speech needs the reverse: a lead, a hold across pauses, and a slower release. SLASH_MY's scheduled carve key ([`keyCurve`](../cases/Soundtrack%20code.md#carry-over-code-in-slash_my); see [dynamic band carves](Dynamics%20and%20spectral%20carving.md#dynamic-band-carves)) already has that shape. Its attack starts before the event, so full depth arrives on the event, and overlapping keys combine by taking the minimum instead of stacking deeper.

**Interpretation:** Duck when narration comes in lines with gaps between them and the music should keep its energy in those gaps. Under continuous narration, a static bed at the target LD is simpler and cannot pump. A detector cannot react before the first syllable, so a shift needs look-ahead or a schedule.

When it fails, inspect:

- Music swelling in short pauses (pumping): the hold is too short.
- A first syllable buried: no shift, or too slow an attack.
- Music popping up on breaths: the release is too short. Music slow to return after a phrase: the release is too long.
- Quiet words that do not duck: the threshold is above the quietest real speech.
- Reverb tails still loud under the words: the returns are not ducked, or the sends are tapped before the duck.
- The voice dipping on the beat: it follows the music's duck curve. SLASH_MY's sung word does this on purpose ([`VOX_DUCK`](../cases/Soundtrack%20code.md#carry-over-code-in-slash_my)), and a narrator should not.

## Spectral room for the voice

A carve lowers only the band where the voice carries its meaning, and only while the voice speaks.

**Source status: partly:** intelligibility is concentrated in the mid frequencies, but the band depends on the speech material and the method. The ANSI S3.5 importance function for nonsense syllables puts most of it between about 1 and 6 kHz. A narrowband study puts it at 400–2500 Hz, with consonant peaks near 600 and 1700 Hz and a band near 7 kHz ([Apoux & Healy, JASA 2012](https://doi.org/10.1121/1.4730905)). Across the sources, the region runs from about 0.4 to 6 kHz.

**Source status: supported (product review):** multiband and spectral duckers lower only the bands the voice occupies. "This preserves more of the backing music in areas that don't overlap with vocal frequencies" (VoxDucker review). The ledger's dynamic-EQ row (partly) agrees and finds no source for fixed bands.

**Source status: practice:** a fixed carve such as 1–4 kHz. A live-sound tip for vocals in a band says "try cutting 4kHz in guitars and other instruments" ([QSC](https://support.qsc.com/en_US/sound-advice/sound-advice-%7C-eq-tips-for-vocals)).

**Source status: supported:** the BBC warns that "low-pitched sounds like traffic, fans and air conditioning or rumbling background effects and music are more likely to cover up the sounds of speech" for listeners with hearing loss. A presence-band carve alone does nothing about that.

**Checked (SLASH_MY):** SLASH_MY carves its bed for its sung word ([dynamic band carves](Dynamics%20and%20spectral%20carving.md#dynamic-band-carves); code in the [case](../cases/Soundtrack%20code.md#carry-over-code-in-slash_my)):

- `MY_POCKET`: under the drop's word, the bed loses 4 dB in a bell at 1.1 kHz for the word's length.
- `LOCK_POCKET`: under the later sung words, the bed loses 10 dB in a broad bell at 2.24 kHz, which the code describes as covering 1–5 kHz.
- `PAD_DIP`: the vocal and the lead, band-passed at 2.2 kHz, key a cut of up to 4 dB there on the pads (5 ms attack, 150 ms release), like a sidechained dynamic EQ.

**Reported:** with `MY_POCKET`, the voice over the rest of the mix at 500–2500 Hz went from −0.5 to +1.4 dB in the word's first 0.3 beat (`70c9dfe5`). Deepening `LOCK_POCKET` from 6 to 10 dB moved the vocal against the rest at 1–5 kHz from −7.2 to −5.6 dB (`d7aeae3d`). These bands suit one sung syllable over a synth bed. They are not speech bands.

**Interpretation:** Carve when the music must stay present under the words and a full-band duck would be audible. A carve does not replace the level difference.

When it fails, inspect:

- Words still unclear after a presence carve: the bed's low end, or too small an LD.
- A bed that sounds hollow under every line: the carve is too deep or too wide.
- A carve that changes nothing: the voice's energy sits elsewhere. Check its spectrum before choosing the center.
- A carve heard switching on and off between words: the keys do not bridge the pauses.

## Loudness anchored to dialogue

Some delivery specs measure program loudness on the voice instead of the whole mix, and the music is then set relative to the voice.

**Source status: supported:** ATSC A/85 measures long-form loudness on the "anchor element", the element the rest of the mix is balanced around. "Dialog forms the Anchor Element in the majority of television programs." Automatic dialogue detection is acceptable, and if the anchor cannot be isolated, the full mix is measured. Short-form content under about 2–3 minutes, such as ads and promos, is measured on the full mix ([A/85:2013](https://www.atsc.org/wp-content/uploads/2025/06/A85-2013-with-Corrigendum-No-1.pdf)).

**Source status: supported:** Netflix requires −27 LKFS ±2 LU, dialog-gated (BS.1770-1), with true peaks no higher than −2 dBTP. Mixes with less than 15% dialogue fall back to −24 LKFS ±2 LU on the full program. Netflix recommends a dialogue loudness range of 10 LU or less ([spec v1.5](https://partnerhelp.netflixstudios.com/hc/en-us/articles/360001794307-Netflix-Sound-Mix-Specifications-Best-Practices-v1-5)).

**Source status: supported (vendor):** Dolby's speech gating "measures loudness only on the segments of a program that contain dialogue", and "Content creators typically set dialogue at a fixed level and mix other content around it" ([Dolby](https://professional.dolby.com/support/dolbys-speech-gating-reference-code/)).

**Source status: partly:** AES TD1008 puts streaming playback at −18 LUFS for speech and mixed content and about −16 LUFS for music ([Production Advice](https://productionadvice.co.uk/td1008/)). It has no dialog gating, and it is playback guidance, not a mixing target. Its 2–3 dB figure compares speech programs with music programs.

**Checked (SLASH_MY):** SLASH_MY trims its full mix toward −14 LUFS with its own BS.1770-4 meter, then measures the encoded and muxed files with ffmpeg and stops on an out-of-spec file ([Mastering and delivery](Mastering%20and%20delivery.md)). Nothing measures a voice alone.

**Interpretation:** a dialog-gated target matters for long-form narration delivered to a spec that names one. A product video under 2–3 minutes, or one bound for a platform that normalizes the full mix, is measured on the full mix; the ledger's Spotify and YouTube rows give no dialog-gated figure. In those cases the LD inside the mix is what protects the voice.

When it fails, inspect:

- Narration that jumps in level between sections while the full-mix figure holds: music-heavy passages move the full-mix meter. Measure the narration.
- A dialog-gated figure out of spec: check which meter and BS.1770 revision the spec names. A home-built gate gives a preview, and the compliance figure comes from the meter the spec names.
- Too little dialogue to gate: below Netflix's 15%, the full-program target applies.

## Music chosen for speech

The cheapest place to make room for the voice is the score.

**Source status: supported:** the BBC advises: "Avoid the use of music with vocals in combination with the spoken word." "Music that is specially written to be heard at a low level under speech should be mixed so that the melody is not too prominent." It also warns against music that is too dynamic and asks whether the music can drop out under the words.

**Interpretation:** a code-built score is written against a timeline, so it can be written against the narration too. SLASH_MY builds score and picture from shared event lists ([sound and picture on one beat grid](Audiovisual%20synchronization.md#sound-and-picture-on-one-beat-grid)). A list of spoken lines could thin the melody, flatten the dynamics, or drop parts under each line.

When it fails, inspect:

- Two voices competing: a sung vocal or vocal sample under the narration. SLASH_MY's sung "my" would be one.
- Swells, hits, or a prominent melody landing on words: check the score's dynamics against the line times.

## Older and hearing-impaired listeners

A bed that suits a young listener with normal hearing can bury the words for others.

**Source status: supported:** "It is well known that background sounds reduce the ability to comprehend speech and that this effect is greater for those who have some form of hearing loss" ([Armstrong, BBC R&D WHP 324](https://downloads.bbci.co.uk/rd/pubs/whp/whp-pdf-files/WHP324.pdf)). Age-related loss starts at high frequencies and moves down into the speech bands. To match normal-hearing word recognition, listeners with hearing loss need about 4–6 dB more speech-to-noise ratio for mild-to-moderate loss, 7–9 dB for moderate-to-severe, and up to 18 dB for severe-to-profound (Killion, via Armstrong). In diaries from 506 viewers aged 65 and over, 11% cited background music as a problem.

**Source status: supported:** in the BBC Vision trial, eight programs were remixed with music and effects 4 dB louder and 4 dB quieter, and 452 people took an online test. Louder backgrounds made every program harder to follow. Quieter ones gave mixed results: the trailer and the most complex soundtracks came out worse.

**Source status: partly (secondary):** in the study behind the ARD/ZDF guideline, listeners over 50 preferred at least 7 LU, and those under 50 showed no clear preference. Torcoli notes that serving the study's listeners who wanted quieter music would move the values toward what hearing-impaired listeners need.

**Source status: supported:** WCAG 2.2 SC 1.4.7 asks that background sounds be absent, able to be switched off, or at least 20 dB below the speech, with occasional sounds of one or two seconds exempt ([W3C](https://www.w3.org/WAI/WCAG22/Understanding/low-or-no-background-audio.html)). It is Level AAA and covers prerecorded audio-only content that is mainly speech, so a narrated video falls outside it.

**Interpretation:** when the narration carries the information and the audience includes older viewers, aim near 15 LU and keep the bed's low end down under speech. An audio-only cut of the narration would fall inside SC 1.4.7, where the bar is 20 dB. A quieter bed does not fix everything: where music carries the story, as in the trial's trailer, trimming it may cost more. Captions and transcripts serve the viewers that no mix will reach ([Accessibility and perception](Accessibility%20and%20perception.md#audio-content-and-alternatives)).

When it fails, inspect:

- Complaints from older viewers at 10 LU: move toward 15 LU.
- A carve that helps young listeners but not older ones: low-frequency masking.
- A bed turned down until the scene goes flat: trim less and carve more.

## Untested ideas

- **Spoken lines driving the score.** Line times, from the script or from a detector on the voice stem, could key ducks and carves through `keyCurve`, with Torcoli's shift and hold.
- **LD checked in the build.** SLASH_MY's BS.1770-4 meter could measure voice and music stems over the speech segments, report the LD per line, and stop the build outside a range, as its mux gate does for loudness. It would not replace a delivery spec's meter.
- **Detected versus scheduled band ducking.** SLASH_MY has a scheduled pocket (`MY_POCKET`) and a level-keyed dip (`PAD_DIP`). Which sounds better under real narration, and at what depth, is untested.
- **A listening check with older viewers and the picture.** Torcoli's listeners were young, had normal hearing, and heard no picture. Checking a chosen LD with older viewers, on the finished video, would test whether the broadcast figures transfer to short product videos.
