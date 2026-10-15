# Audio synthesis

Procedural sound builds a waveform in code, alongside or in place of recorded files. Work in **events**: at a set time, something happens and makes a sound, and that sound has a source, a timbre, an amplitude shape, and a place in the mix. A generated sound can mark an impact, make a process feel continuous, or tell one kind of change apart from another. Check its job in the complete video, because a sound that works on its own may mask narration or clash with the cues around it.

## Signal path

```text
source → timbre processing → amplitude envelope → mix bus → output
```

The path is a model to think with; a real graph does not have to follow it as a fixed chain. In the Web Audio API, nodes form a graph, so a signal can branch, modulate other parameters, and merge with other signals. The [W3C Web Audio specification](https://www.w3.org/TR/webaudio/) defines a `BaseAudioContext` as a connected graph of audio nodes routed to a destination.

| Component | What it controls | Typical code source |
| --- | --- | --- |
| Source | Initial waveform or recording | Oscillator, audio buffer, custom worklet |
| Timbre | Spectral character | Wave shape, filter, modulation, sample selection |
| Envelope | How the sound begins, develops, and ends | Scheduled gain or frequency automation |
| Space | Apparent position and width | Channel routing or panning |
| Mix | Relationship to speech, music, and other cues | Bus gain, compression, limiting, measurement |

[MDN's advanced Web Audio tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Advanced_techniques) shows oscillators, custom periodic waves, modulation, noise buffers, filters, samples, envelopes, and scheduling in one example. These are building blocks, and a cue does not need every stage.

## Sources: tone, noise, and samples

An oscillator produces a periodic waveform. A sine wave gives a simple pitch. Square, sawtooth, triangle, and custom periodic waves each have different harmonic content. Changing the frequency over time makes a pitch sweep, and a low-frequency oscillator can modulate another signal's amplitude or one of its parameters. The [Web Audio synthesis tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Advanced_techniques) shows each of these.

To make noise, fill an audio buffer with random samples. A filter can then narrow that broad spectrum into a hiss, burst, rumble, or other texture. Use a seeded random generator when the same source code must produce the same noise waveform on every render; unseeded randomness can change the sound from one export to the next. This point about reproducibility is inferred from how the [MDN example](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Advanced_techniques) builds its random buffer.

Pitch, loudness, and timbre are separate controls. Oscillator **frequency** mainly changes the pitch you hear. A **gain** stage changes the signal's amplitude. The waveform and filtering change the balance of frequencies that gives a tone its character. A low-pass filter cuts higher frequencies, a high-pass filter cuts lower ones, and a band-pass filter favors one region. What a filter's `Q` or resonance means depends on the filter type, so tune it by its documented response and by ear, and do not treat one number as right everywhere. [MDN's `BiquadFilterNode` reference](https://developer.mozilla.org/en-US/docs/Web/API/BiquadFilterNode/BiquadFilterNode) defines these filter modes.

Digital audio has a sampling limit. Frequencies above half the sample rate cannot be represented directly and can fold down into lower frequencies as aliasing. The [Web Audio specification](https://www.w3.org/TR/webaudio/) discusses this for oscillators, and [MDN's audio basics](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Basic_concepts_behind_Web_Audio_API) explains the Nyquist relationship. It matters when you synthesize bright waveforms or strong modulation at high pitches. A renderer's built-in oscillator may handle anti-aliasing differently from a sample buffer you fill by hand, so listen to the actual output.

A recorded sample can be the right source when the sound of a recognizable physical event matters. `AudioBufferSourceNode` plays audio held in memory and supports scheduled starts, offsets, and playback-rate changes. A source node can be started only once, so each repeat needs a new source node. The [AudioBufferSourceNode](https://developer.mozilla.org/en-US/docs/Web/API/AudioBufferSourceNode) page and [its `start()` method](https://developer.mozilla.org/en-US/docs/Web/API/AudioBufferSourceNode/start) document these limits. Changing the playback rate changes the pitch unless you add a separate pitch-correction method.

When the built-in nodes cannot do the signal processing you need, an `AudioWorkletNode` can run a custom processor on the audio rendering thread. It adds implementation work, and it is useful for generation or processing that existing nodes cannot express clearly. [MDN documents the worklet model](https://developer.mozilla.org/en-US/docs/Web/API/AudioWorkletNode).

## Envelope: the event's shape in time

A waveform that jumps from silence to full amplitude, or stops on a nonzero sample, can produce a discontinuity that sounds like a click. A short gain ramp or envelope controls the onset and the release. A longer attack can feel softer, and a short attack brings out the transient. Decay and release decide whether the sound ends sharply or leaves a tail. The right values depend on the sound; set them by listening.

The Web Audio `AudioParam` interface schedules values and curves on the context's audio clock: instant changes, linear ramps, exponential ramps, and approaches to a target. The [specification's automation section](https://www.w3.org/TR/webaudio/) describes `setTargetAtTime()` as useful for the decay and release parts of an ADSR envelope, and [MDN's `AudioParam` reference](https://developer.mozilla.org/en-US/docs/Web/API/AudioParam) summarizes the API. Automation works on timbre as well as amplitude: a filter cutoff or an oscillator frequency can change during a cue.

Shape envelopes at two scales. A cue's own envelope can make an impact or a swell. A bus for the scene can fade several cues together or make room for narration. If every event has the same envelope and level, listeners can lose track of which actions matter more.

## Scheduling and rendering

For live playback in a browser, JavaScript timers are a control mechanism; the precise clock is the audio clock. Schedule events shortly ahead using `AudioContext.currentTime`. [MDN's sequencer example](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API/Advanced_techniques) shows a look-ahead queue with the visual drawing kept separate. A scheduled source's `start(when)` takes its time in that same audio-context clock ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/AudioScheduledSourceNode/start)).

For a fixed video, `OfflineAudioContext` can render the graph into an `AudioBuffer` with a set channel count, sample length, and sample rate. The [W3C definition](https://www.w3.org/TR/webaudio/) says it renders as fast as it can instead of to audio hardware, which suits making an audio file to go with a frame-based video export. If effect tails should stay audible, the requested length must include them. To reproduce a render, keep the cue times, sample rate, and random seeds fixed. [Audiovisual synchronization](Audiovisual%20synchronization.md) covers mapping these cues to video frames.

## Mix by role, then measure

Several signals that are each safe on their own can add up to a peak that clips. Bus gain leaves headroom. A compressor can reduce loud peaks, but too much compression can flatten the differences you wanted between events. The [Web Audio compressor reference](https://developer.mozilla.org/en-US/docs/Web/API/DynamicsCompressorNode) describes peak reduction and its use on a combined signal.

Loudness and peak are separate measurements. [ITU-R BS.1770](https://www.itu.int/rec/R-REC-BS.1770-5-202311-I) specifies algorithms for programme loudness and true-peak level. [EBU R 128](https://tech.ebu.ch/publications/r128) recommends a target of −23 LUFS for broadcast programmes and tracks loudness range and maximum true peak. That target is for broadcast; check what each distribution channel expects before you reuse it. FFmpeg's [official `loudnorm` documentation](https://ffmpeg.org/ffmpeg-filters.html) describes integrated loudness, loudness range, true-peak targets, and two-pass file normalization.

Measurement can catch clipping or large jumps in level. It cannot tell you whether a cue has the character you wanted, whether it pulls attention from a line, or whether the encoded video feels balanced. Listen to the full mix, quiet and busy passages both, at the level people will likely play it. Keep speech and any audio that carries information understandable. [Accessibility and perception](Accessibility%20and%20perception.md) covers captions and equivalent access to audio content.
