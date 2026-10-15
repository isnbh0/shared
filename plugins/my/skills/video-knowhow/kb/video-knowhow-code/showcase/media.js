// media.js — the small media the README shows, made from code into media/: stills and short silent clips cut from
// out/showcase.mp4, and short AAC snippets that teach by contrast, rendered from the score and its variants.
//   node media.js            (after node render.js; `npm run media` runs audio.js, render.js and this)
// Stills are JPEG at 960 px; clips are H.264 at 960 px, CRF 26, no sound; snippets are AAC at 160 kbit/s from
// ffmpeg's native encoder, so a second run writes the same bytes. Slices of the score keep the mix's level. An
// off/on pair is rendered at the full mix's level and trim (renderScore's `fixed`); each half is then matched to
// -16 LUFS and both go through one limiter (-4 dBFS), so the technique is the only difference between them.
'use strict';
const fs = require('fs');
const path = require('path');
const T = require('./timeline');
const { renderScore } = require('./audio');
const { readWav, encodeAac, ff } = require('./delivery');
const { loudness: lufsOf, limit } = require('../samples/master-loudness');

const OUT = path.join(__dirname, 'media'), MP4 = path.join(__dirname, 'out', 'showcase.mp4');
if (!fs.existsSync(MP4)) {
  console.error('media.js: out/showcase.mp4 not found: run node render.js first');
  process.exit(1);
}
fs.mkdirSync(OUT, { recursive: true });
const sec = b => b * T.SPB;
const TAGS = ['-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv'];

// Stills: one frame each, by frame number. JPEG is full range with the BT.601 matrix, so the scale converts to it.
const STILLS = [['01-intro', 4.6], ['02-shelves', 18], ['03-converge', 23.2], ['04-drop', 24.2], ['05-drop-page', 34],
  ['06-resolve', 46]];
for (const [name, b] of STILLS) {
  const f = T.beatToFrame(b);
  const scale = 'scale=960:-2:flags=lanczos:in_range=tv:out_range=pc:in_color_matrix=bt709:out_color_matrix=bt601';
  ff(['-i', MP4, '-vf', `select=eq(n\\,${f}),${scale}`,
    '-frames:v', '1', '-q:v', '3', path.join(OUT, `${name}.jpg`)], `still ${name}`);
}

// Silent clips, in beats.
const CLIPS = [['clip-intro-words', 1.4, 6.4], ['clip-landings', 9.2, 15.2], ['clip-into-the-drop', 20, 28],
  ['clip-resolve', 41, 47]];
for (const [name, b0, b1] of CLIPS) {
  ff(['-i', MP4, '-ss', String(sec(b0)), '-t', String(sec(b1 - b0)), '-an',
    '-vf', 'scale=960:-2:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '26', '-pix_fmt', 'yuv420p',
    ...TAGS,
    '-movflags', '+faststart', path.join(OUT, `${name}.mp4`)], `clip ${name}`);
}

// Snippets. slice() cuts beats b0–b1 with 10 ms half-cosine edges; ab() puts two slices back to back with a
// short rest.
const SR = 48000, EDGE = Math.round(0.01 * SR);
function slice([L, R], b0, b1) {
  const a = Math.round(sec(b0) * SR), n = Math.round(sec(b1 - b0) * SR), l = L.slice(a, a + n), r = R.slice(a, a + n);
  for (let i = 0; i < EDGE; i++) {
    const g = 0.5 - 0.5 * Math.cos(Math.PI * i / EDGE);
    l[i] *= g; r[i] *= g; l[n - 1 - i] *= g; r[n - 1 - i] *= g;
  }
  return [l, r];
}
// Each half gets its own gain, then the pair goes through one limiter at -4 dBFS (the native encoder can overshoot
// by about 2.5 dB): gain, limit, measure each half and correct its gain until both read -16 LUFS.
function ab(x, y, rest = 0.35) {
  const gap = Math.round(rest * SR), nx = x[0].length, at = nx + gap, n = at + y[0].length;
  const half = (L, R, a, b) => lufsOf(L.subarray(a, b), R.subarray(a, b));
  let gx = Math.pow(10, (-16 - lufsOf(x[0], x[1])) / 20), gy = Math.pow(10, (-16 - lufsOf(y[0], y[1])) / 20);
  let L, R;
  for (let pass = 0; pass < 8; pass++) {
    L = new Float32Array(n); R = new Float32Array(n);
    L.set(x[0].map(s => s * gx)); R.set(x[1].map(s => s * gx));
    L.set(y[0].map(s => s * gy), at); R.set(y[1].map(s => s * gy), at);
    limit(L, R, { ceil: Math.pow(10, -4 / 20) });
    const mx = -16 - half(L, R, 0, nx), my = -16 - half(L, R, at, n);
    if (Math.abs(mx) < 0.05 && Math.abs(my) < 0.05) break;
    gx *= Math.pow(10, mx / 20); gy *= Math.pow(10, my / 20);
  }
  return [L, R];
}
const full = renderScore(), fixed = { norm: full.norm, trim: full.trim };
const v = opts => { const r = renderScore({ ...opts, fixed }); return [r.L, r.R]; };
const score = readWav(path.join(__dirname, 'score.wav'));
const SNIPPETS = [
  ['audio-build-into-drop', slice(score, 20, 26)],
  ['audio-drop-mastered', slice(score, 24, 34)],
  ['audio-drums-solo', slice(v({ solo: ['drums'] }), 24, 32)],
  // Bass and chord bed only: with no drums masking it, the kick's ducking is heard as the pump itself.
  ['audio-sidechain-off-on', ab(slice(v({ sidechain: false, solo: ['bass', 'bed'] }), 28, 32),
    slice(v({ solo: ['bass', 'bed'] }), 28, 32))],
  ['audio-sends-off-on', ab(slice(v({ sends: false, solo: ['pluck', 'bed'] }), 44, 48),
    slice(v({ solo: ['pluck', 'bed', 'returns'] }), 44, 48))],
];
SNIPPETS.forEach(([name, [L, R]], k) =>
  encodeAac(L, R, path.join(OUT, `${name}.m4a`), { bitrate: '160k', seed: 100 + k, codec: 'native' }));

let total = 0;
for (const f of fs.readdirSync(OUT).sort()) {
  const s = fs.statSync(path.join(OUT, f)).size;
  total += s;
  console.log(`${f.padEnd(28)} ${(s / 1024).toFixed(0).padStart(5)} KB`);
}
console.log(`media/ total ${(total / 1024 / 1024).toFixed(2)} MB`);
