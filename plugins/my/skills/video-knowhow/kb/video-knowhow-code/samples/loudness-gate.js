// loudness-gate.js — master a WAV to AAC at an integrated-loudness target under a true-peak ceiling, measured on the
// encoded stream and corrected over up to three passes; then gate the delivered file against the spec.
// When you need it: the delivered file must meet a loudness spec (for example -14 LUFS integrated, <= -1 dBTP) and
// the AAC encoder's own peak overshoot must not take it over the ceiling.
// Source: generalized from the source production's renderer (AAC stage, loudness measure,
// master-audio path, and the mux's delivery check).
// Generalized: target, ceiling and files are arguments; the pass correction is the pure function nextPass.
// Left out: joining an opener's room tone in front of the score; the 16-bit cut for AudioToolbox (aac_at takes s16
// only and ffmpeg's own conversion rounds without dither: the source cuts to 16 bits with TPDF dither first, the way
// wav-writer.js cuts to 24).
// node loudness-gate.js in.wav out.m4a [lufs] [tpMax]
'use strict';
const { spawnSync } = require('child_process');

const FFMPEG = process.env.FFMPEG || 'ffmpeg';
// AudioToolbox AAC (macOS) overshoots about 0.1 dB; ffmpeg's native AAC 1.1-1.7 dB and erratically, so it may need
// the limiter and the extra passes. `over` sets the limiter that far under the aim.
const AAC = spawnSync(FFMPEG, ['-hide_banner', '-encoders'], { encoding: 'utf8' }).stdout.includes(' aac_at ')
  ? { args: ['-c:a', 'aac_at', '-aac_at_mode', 'cbr', '-b:a', '320k'], over: 0.3 } : { args: ['-c:a', 'aac', '-b:a', '320k'], over: 1.2 };

function ff(args, label) {
  const r = spawnSync(FFMPEG, ['-hide_banner', '-y', ...args], { encoding: 'utf8', maxBuffer: 1 << 26 });
  if (r.status !== 0) { console.error(r.stderr.slice(-3000)); throw new Error(`${label} failed`); }
  return r.stderr;
}
// ebur128 on the first audio stream, decoded: integrated loudness and true peak from the summary block.
function loudness(file) {
  const err = ff(['-nostats', '-i', file, '-map', '0:a:0', '-af', 'ebur128=peak=true', '-f', 'null', '-'], 'loudness');
  const sum = err.slice(err.lastIndexOf('Summary:'));
  const I = /I:\s+(-?[\d.]+) LUFS/.exec(sum), P = /Peak:\s+(-?[\d.]+|-inf) dBFS/.exec(sum);
  if (!I || !P) throw new Error(`no loudness summary for ${file}`);
  return { I: +I[1], TP: P[1] === '-inf' ? -Infinity : +P[1] };
}

// A lookahead limiter at 4x oversampling: sample peaks at 192 kHz track true peaks. Used only when needed.
const limiter = ceilDb => `aresample=192000,alimiter=limit=${Math.pow(10, ceilDb / 20).toFixed(5)}:attack=2:release=80:level=0:latency=1,aresample=48000`;

// The first pass: gain to the target; the limiter ceiling under the aim by the encoder's overshoot.
const firstPass = (src, { lufs, tpAim, over }) => ({ gain: lufs - src.I, ceil: tpAim - over });
// The limiter goes in only when the gained source's true peak would cross the ceiling.
const needsLimiter = (src, p) => src.TP + p.gain > p.ceil;
// After measuring the encoded pass m: done when its peak is under the aim and its loudness within 0.05 LU; else
// correct the gain by the loudness error and lower the ceiling by the peak's overshoot of the aim.
function nextPass(p, m, { lufs, tpAim }) {
  if (m.TP <= tpAim && Math.abs(m.I - lufs) < 0.05) return { ...p, done: true };
  return { gain: p.gain + (lufs - m.I), ceil: p.ceil - Math.max(0, m.TP - tpAim), done: false };
}

function master(input, out, { lufs = -14, tpMax = -1 } = {}) {
  const tpAim = tpMax - 0.2, src = loudness(input);
  let p = firstPass(src, { lufs, tpAim, over: AAC.over }), m;
  for (let pass = 1; pass <= 3; pass++) {
    const lim = needsLimiter(src, p) ? limiter(p.ceil) : '';
    const af = [`volume=${p.gain.toFixed(2)}dB`, lim].filter(Boolean).join(',');
    ff(['-i', input, '-af', af, ...AAC.args, '-ar', '48000', '-ac', '2', out], 'audio master');
    m = loudness(out);
    console.log(`pass ${pass} (${AAC.args[1]}): source ${src.I} LUFS ${src.TP} dBTP, gain ${p.gain.toFixed(2)} dB, `
      + `${lim ? `limiter at ${p.ceil.toFixed(2)} dBTP` : 'no limiter'} -> ${m.I} LUFS ${m.TP} dBTP`);
    p = nextPass(p, m, { lufs, tpAim });
    if (p.done) break;
  }
  return m;
}

// Measure what was delivered (the muxed file, not the master) and stop the run when it is out of spec.
function gate(file, { lufs = -14, tpMax = -1, tol = 0.5 } = {}) {
  const m = loudness(file);
  console.log(`delivered audio: ${m.I} LUFS, ${m.TP} dBTP (spec ${lufs} LUFS, <= ${tpMax} dBTP)`);
  if (m.TP > tpMax || Math.abs(m.I - lufs) > tol) throw new Error(`${file} audio is out of spec`);
  return m;
}

module.exports = { AAC, loudness, limiter, firstPass, needsLimiter, nextPass, master, gate };

if (require.main === module) {
  const [input, out, lufs = '-14', tpMax = '-1'] = process.argv.slice(2);
  if (!input || !out) { console.error('node loudness-gate.js in.wav out.m4a [lufs] [tpMax]'); process.exit(2); }
  try { master(input, out, { lufs: +lufs, tpMax: +tpMax }); gate(out, { lufs: +lufs, tpMax: +tpMax }); }
  catch (e) { console.error(e.message); process.exit(1); }
}
