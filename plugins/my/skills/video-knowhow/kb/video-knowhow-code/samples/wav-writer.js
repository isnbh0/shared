// wav-writer.js — write float stereo samples as a 48 kHz 24-bit PCM WAV with TPDF dither from its own seeded stream.
// When you need it: a score synthesized in code leaves the float domain once, for the file every later step reads,
// and that cut to 24 bits should add a steady noise floor rather than distortion that follows the signal, with the
// same bytes on every run.
// Source: generalized from the source production's score (WAV writer and dither) and its beat
// clock's seeded stream.
// Generalized: sample rate and seed are arguments; it returns the buffer and the peak rather than logging.
// Left out: nothing of the writer; the source's second file (an opener's room tone) used its own seed the same way.
'use strict';
const fs = require('fs');

// mulberry32 (the same generator as seeded-streams.js): uniform in [0, 1), a pure function of the seed.
function rng(seed) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6D2B79F5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Every sample takes TPDF dither of 2 LSB peak to peak before it is rounded (Lipshitz, Wannamaker and Vanderkooy,
// JAES 1992): two uniform draws, so the rounding error is a steady noise (about -144.5 dBFS rms at 24 bits) that does
// not follow the signal; no noise shaping. Two draws per channel per frame whatever the sample holds, so sample i's
// dither depends only on i and the seed. A sample that is exactly zero has no rounding error and stays digital zero
// (silence stays silent). The dithered value is clamped to 24 bits, so nothing wraps at full scale.
function wavBuffer(L, R, { sr = 48000, seed = 1 } = {}) {
  const n = L.length, bps = 3, block = 2 * bps, buf = Buffer.alloc(44 + n * block);
  buf.write('RIFF', 0); buf.writeUInt32LE(36 + n * block, 4); buf.write('WAVE', 8);
  buf.write('fmt ', 12); buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22);
  buf.writeUInt32LE(sr, 24); buf.writeUInt32LE(sr * block, 28); buf.writeUInt16LE(block, 32); buf.writeUInt16LE(24, 34);
  buf.write('data', 36); buf.writeUInt32LE(n * block, 40);
  const FS = 8388607, rD = rng(seed), tpdf = () => rD() + rD() - 1;
  const word = (x, d) => (x === 0 ? 0 : Math.max(-FS - 1, Math.min(FS, Math.round(x * FS + d))));
  let o = 44, peak = 0;
  for (let i = 0; i < n; i++) {
    peak = Math.max(peak, Math.abs(L[i]), Math.abs(R[i]));
    const dL = tpdf(), dR = tpdf();
    buf.writeIntLE(word(L[i], dL), o, 3); o += 3;
    buf.writeIntLE(word(R[i], dR), o, 3); o += 3;
  }
  return { buf, peak };
}

// One seed per file, so editing one file's length re-rolls nothing in another.
function writeWav(file, L, R, opts) {
  const { buf, peak } = wavBuffer(L, R, opts);
  fs.writeFileSync(file, buf);
  return peak;
}

module.exports = { rng, wavBuffer, writeWav };
