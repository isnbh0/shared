// audio.js — writes score.wav from the clock in timeline.js: a click on every beat (higher on each bar's
// first beat), a seeded noise tick on every offbeat, and a soft chord on the text cue.
// The same code writes the same bytes: no Date, no Math.random. Replace the parts with your score.
const fs = require('fs');
const path = require('path');
const T = require('./timeline');

const SR = 48000;                                   // sample rate, Hz
const N = Math.round(T.DURATION * SR);              // samples for the whole clip
const L = new Float32Array(N), R = new Float32Array(N);
const TAU = Math.PI * 2;
const noise = T.rng(2);                             // the score's own seeded stream

// Add a sound into the mix: fn(u) is its signal u seconds after it starts at t. pan runs -1 (left) … 1 (right).
function put(t, dur, fn, gain = 1, pan = 0) {
  const i0 = Math.round(t * SR), i1 = Math.min(N, Math.round((t + dur) * SR));
  const gl = gain * Math.cos((pan + 1) * Math.PI / 4), gr = gain * Math.sin((pan + 1) * Math.PI / 4);
  for (let i = i0; i < i1; i++) {
    const v = fn((i - i0) / SR);
    L[i] += v * gl; R[i] += v * gr;
  }
}

// The click: a short sine blip.
const click = hz => u => Math.sin(TAU * hz * u) * Math.exp(-u * 60);
for (let b = 0; b < T.BEATS; b++) {
  const first = b % T.BEATS_PER_BAR === 0;
  put(T.beatToSec(b), 0.08, click(first ? 1500 : 1000), first ? 0.8 : 0.5);
}

// The offbeat tick: seeded white noise through a one-pole high-pass, alternating left and right.
for (let b = 0.5; b < T.BEATS; b++) {
  let lo = 0;
  put(T.beatToSec(b), 0.04, u => {
    const n = noise() * 2 - 1;
    lo += 0.2 * (n - lo);
    return (n - lo) * Math.exp(-u * 120);
  }, 0.25, Math.floor(b) % 2 ? 0.4 : -0.4);
}

// The cue: a fifth (A4 and E5) that rings for two beats when the text line lands.
put(T.beatToSec(T.CUES.text), T.beatToSec(2), u =>
  (Math.sin(TAU * 440 * u) + 0.7 * Math.sin(TAU * 660 * u)) * Math.min(1, u / 0.01) * Math.exp(-u * 2.5), 0.25);

// Write 16-bit stereo PCM. Samples past ±1 are clipped: keep the peak below 0 dBFS.
let peak = 0;
for (let i = 0; i < N; i++) peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
const pcm = x => Math.round(Math.max(-1, Math.min(1, x)) * 32767);
const buf = Buffer.alloc(44 + N * 4);
buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 4, 4); buf.write('WAVE', 8);
buf.write('fmt ', 12); buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22);
buf.writeUInt32LE(SR, 24); buf.writeUInt32LE(SR * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34);
buf.write('data', 36); buf.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N; i++) {
  buf.writeInt16LE(pcm(L[i]), 44 + i * 4);
  buf.writeInt16LE(pcm(R[i]), 46 + i * 4);
}
const out = path.join(__dirname, 'score.wav');
fs.writeFileSync(out, buf);
console.log(`wrote score.wav  ${T.DURATION} s  ${SR} Hz  peak ${(20 * Math.log10(peak)).toFixed(1)} dBFS` +
  (peak > 1 ? '  (CLIPPED: lower the gains)' : ''));
