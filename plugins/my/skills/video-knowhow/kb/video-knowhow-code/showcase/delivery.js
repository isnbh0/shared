// delivery.js — the sound's way into AAC, shared by render.js and media.js.
//   readWav(file)                 a 24-bit PCM WAV (score.wav) back to float [L, R]
//   wav16(file, L, R, opts)       float → 16-bit WAV with gain baked in and TPDF dither from a seeded stream.
//                                 AudioToolbox AAC (aac_at) takes 16-bit input only, and ffmpeg's own conversion
//                                 rounds without dither, so the word-length cut happens here, dithered, once.
//   encodeAac(L, R, out, opts)    wav16 → AAC; with `target`, measure the encoded file (ebur128) and correct the
//                                 gain, up to three passes, until it is within 0.1 LU and under the true-peak aim.
//                                 codec: 'native' uses ffmpeg's own AAC encoder, which gives the same bytes on
//                                 every run (AudioToolbox's output can vary between runs); media.js uses it.
// ffmpeg is ffmpeg-static's; loudness measurement and the delivery gate come from samples/loudness-gate.js.
'use strict';
const fs = require('fs');
const path = require('path');
process.env.FFMPEG = process.env.FFMPEG || require('ffmpeg-static');
const { spawnSync } = require('child_process');
const { AAC, loudness, gate } = require('../samples/loudness-gate');
const { rng } = require('../samples/wav-writer');

function readWav(file) {
  const buf = fs.readFileSync(file);
  let o = 12, fmt = null, data = null;
  while (o + 8 <= buf.length) {
    const id = buf.toString('ascii', o, o + 4), size = buf.readUInt32LE(o + 4);
    if (id === 'fmt ') {
      fmt = { ch: buf.readUInt16LE(o + 10), sr: buf.readUInt32LE(o + 12), bits: buf.readUInt16LE(o + 22) };
    }
    if (id === 'data') data = { at: o + 8, size };
    o += 8 + size + (size & 1);
  }
  if (!fmt || !data || fmt.ch !== 2 || fmt.bits !== 24) throw new Error(`${file}: expected 24-bit stereo PCM`);
  const n = data.size / 6, L = new Float32Array(n), R = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    L[i] = buf.readIntLE(data.at + 6 * i, 3) / 8388608;
    R[i] = buf.readIntLE(data.at + 6 * i + 3, 3) / 8388608;
  }
  return [L, R];
}

// TPDF dither of 2 LSB peak to peak; exact zeros stay zero (the gap stays digital silence).
function wav16(file, L, R, { gainDb = 0, seed = 16 } = {}) {
  const n = L.length, buf = Buffer.alloc(44 + n * 4), g = Math.pow(10, gainDb / 20), r = rng(seed);
  buf.write('RIFF', 0); buf.writeUInt32LE(36 + n * 4, 4); buf.write('WAVE', 8);
  buf.write('fmt ', 12); buf.writeUInt32LE(16, 16); buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22);
  buf.writeUInt32LE(48000, 24); buf.writeUInt32LE(48000 * 4, 28); buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34);
  buf.write('data', 36); buf.writeUInt32LE(n * 4, 40);
  const word = (x, d) => (x === 0 ? 0 : Math.max(-32768, Math.min(32767, Math.round(x * g * 32767 + d))));
  for (let i = 0, o = 44; i < n; i++, o += 4) {
    const dL = r() + r() - 1, dR = r() + r() - 1;
    buf.writeInt16LE(word(L[i], dL), o); buf.writeInt16LE(word(R[i], dR), o + 2);
  }
  fs.writeFileSync(file, buf);
}

function ff(args, label) {
  const r = spawnSync(process.env.FFMPEG, ['-hide_banner', '-loglevel', 'error', '-y', ...args], { encoding: 'utf8' });
  if (r.status !== 0) throw new Error(`${label}: ${r.stderr.slice(-2000)}`);
}

function encodeAac(L, R, out, { target = null, bitrate = '320k', seed = 16, codec = 'default', log = () => {} } = {}) {
  const tmp = out.replace(/\.[^.]+$/, '') + '.16bit.wav';
  const args = codec === 'native' ? ['-c:a', 'aac', '-b:a', bitrate] : AAC.args.map(a => (a === '320k' ? bitrate : a));
  let gainDb = 0, m = null;
  for (let pass = 1; pass <= (target ? 3 : 1); pass++) {
    wav16(tmp, L, R, { gainDb, seed });
    ff(['-i', tmp, ...args, '-ar', '48000', out], 'aac encode');
    if (!target) break;
    m = loudness(out);
    log(`  audio pass ${pass} (${args[1]}): gain ${gainDb.toFixed(2)} dB → ${m.I} LUFS, ${m.TP} dBTP`);
    const aim = target.tpMax - 0.2;
    if (Math.abs(m.I - target.lufs) < 0.1 && m.TP <= aim) break;
    gainDb += Math.min(target.lufs - m.I, aim - m.TP);   // never raise the peak past the aim
  }
  fs.unlinkSync(tmp);
  return m;
}

module.exports = { readWav, wav16, encodeAac, loudness, gate, ff, AAC };
