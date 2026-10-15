// voices.js — every instrument in the score, each a function that returns its own buffer (mono Float32Array, or
// [L, R] where the voice is stereo by nature). audio.js places the buffers in time. Randomness comes in as a
// seeded stream `rnd`, so the same call gives the same samples.
'use strict';
const { SR, TAU, SVF, Saw, ksBuffer } = require('./dsp');

const mtof = m => 440 * Math.pow(2, (m - 69) / 12);
const len = s => Math.max(1, Math.round(s * SR));
const ease = x => (x <= 0 ? 0 : x >= 1 ? 1 : 0.5 - 0.5 * Math.cos(Math.PI * x));   // half-cosine 0 → 1
// Attack-hold-release gate for a note of `dur` seconds: half-cosine attack a, half-cosine release r after dur.
const gate = (t, dur, a = 0.003, r = 0.02) => ease(t / a) * (t < dur ? 1 : 1 - ease((t - dur) / r));

// Kick: a sine body sweeping 150 → 47 Hz through tanh drive, a short 230 → 185 Hz knock, and a 2 ms click of
// band-limited noise eased in and out (a click that starts at full level is a step: it would splatter).
function kick(rnd, { drive = 1.8, decay = 0.3 } = {}) {
  const n = len(0.55), out = new Float32Array(n), hp = new SVF(), lp = new SVF();
  let ph = 0, ph2 = 0;
  for (let i = 0; i < n; i++) {
    const t = i / SR;
    ph += TAU * (47 + 103 * Math.exp(-t / 0.028)) / SR;
    ph2 += TAU * (185 + 45 * Math.exp(-t / 0.01)) / SR;
    const body = Math.sin(ph) * Math.exp(-t / decay) * ease(t / 0.0015);
    const knock = 0.28 * Math.sin(ph2) * Math.exp(-t / 0.014);
    const cl = t < 0.004 ? (hp.run(lp.run(rnd() * 2 - 1, 7000), 1500), hp.hp) * Math.sin(Math.PI * t / 0.004) * 0.5 : 0;
    out[i] = Math.tanh(drive * (body + knock)) / Math.tanh(drive) + cl;
  }
  for (let i = n - len(0.03); i < n; i++) out[i] *= 1 - ease((i - (n - len(0.03))) / len(0.03));
  return out;
}

// Clap: four noise bursts 0, 11, 21, 30 ms apart through a 1.3 kHz band-pass, the last with a longer tail.
function clap(rnd) {
  const n = len(0.4), out = new Float32Array(n), bp = new SVF(), hp = new SVF();
  const starts = [0, 0.011, 0.021, 0.030];
  for (let i = 0; i < n; i++) {
    const t = i / SR;
    let env = 0;
    for (let k = 0; k < 4; k++) {
      const u = t - starts[k];
      if (u >= 0) env += (k < 3 ? Math.exp(-u / 0.0045) : Math.exp(-u / 0.11)) * ease(u / 0.0006);
    }
    bp.run(rnd() * 2 - 1, 1300, 1.1);
    hp.run(bp.bp * env * 1.6, 400, 0.7);
    out[i] = hp.hp;
  }
  return out;
}

// Snare: a 190 Hz shell (pitch rises with `pitch` for a roll's climb) and a noise wire band centered near 3.6 kHz.
function snare(rnd, { pitch = 190, tail = 0.16 } = {}) {
  const n = len(tail * 3.5), out = new Float32Array(n), bp = new SVF(), hp = new SVF();
  let ph = 0;
  for (let i = 0; i < n; i++) {
    const t = i / SR;
    ph += TAU * pitch * (1 + 0.5 * Math.exp(-t / 0.008)) / SR;
    const shell = Math.sin(ph) * Math.exp(-t / 0.05) * 0.7;
    bp.run(rnd() * 2 - 1, 3600, 0.6);
    hp.run(bp.bp, 1200, 0.7);
    const wire = hp.hp;
    out[i] = (shell + wire * 0.9 * Math.exp(-t / tail)) * ease(t / 0.0008);
  }
  return out;
}

// Hat: six square waves at inharmonic ratios (the TR-808 recipe) plus noise, high-passed at 7.6 kHz.
const HAT_F = [205.3, 304.4, 369.6, 522.7, 540, 800].map(f => f * 1.9);
function hat(rnd, { open = false } = {}) {
  const dec = open ? 0.22 : 0.032, n = len(dec * 5), out = new Float32Array(n), hp = new SVF(), hp2 = new SVF();
  const ph = HAT_F.map(() => rnd());
  for (let i = 0; i < n; i++) {
    const t = i / SR;
    let m = 0;
    for (let k = 0; k < 6; k++) { ph[k] += HAT_F[k] / SR; m += (ph[k] % 1) < 0.5 ? 1 : -1; }
    const x = m / 6 * 0.6 + (rnd() * 2 - 1) * 0.5;
    hp.run(x, 7600, 0.8); hp2.run(hp.hp, 7600, 0.7);
    out[i] = hp2.hp * Math.exp(-t / dec) * ease(t / 0.0005);
  }
  return out;
}

// Bass: two saws 0.4 % apart and a sine at the root, a low-pass at 360 Hz opened by an envelope, then tanh drive.
function bass(f, dur, { env = 1400, drive = 2.2 } = {}) {
  const n = len(dur + 0.03), out = new Float32Array(n), a = new Saw(0), b = new Saw(0.37), lp = new SVF();
  let ph = 0;
  for (let i = 0; i < n; i++) {
    const t = i / SR;
    ph += TAU * f / SR;
    const x = 0.5 * (a.tick(f * 1.004) + b.tick(f * 0.996)) + 0.8 * Math.sin(ph);
    const y = lp.run(x, 360 + env * Math.exp(-t / 0.07), 0.9);
    out[i] = Math.tanh(drive * y) / Math.tanh(drive) * gate(t, dur, 0.004, 0.025);
  }
  return out;
}

// Supersaw: seven saws per note at fixed detune ratios (scaled by `det`), random start phases, the center voice at
// full level and the sides at 0.75 spread left and right; high-passed at 150 Hz, low-passed by an envelope.
const SS_DET = [-0.11002313, -0.06288439, -0.01952356, 0, 0.01991221, 0.06216538, 0.10745242];
function supersaw(notes, dur, rnd,
  { det = 0.12, cut = 2400, cutEnv = 5200, cutDecay = 0.12, a = 0.004, r = 0.06 } = {}) {
  const n = len(dur + r + 0.01), L = new Float32Array(n), R = new Float32Array(n);
  const vs = [];
  for (const m of notes) for (let k = 0; k < 7; k++) {
    const pan = (k - 3) / 3 * 0.8;
    vs.push({
      o: new Saw(rnd()), f: mtof(m) * (1 + SS_DET[k] * det), g: k === 3 ? 1 : 0.75,
      l: Math.cos((pan + 1) * Math.PI / 4), r: Math.sin((pan + 1) * Math.PI / 4),
    });
  }
  const hpL = new SVF(), hpR = new SVF(), lpL = new SVF(), lpR = new SVF(), norm = 1 / Math.sqrt(vs.length);
  for (let i = 0; i < n; i++) {
    const t = i / SR;
    let l = 0, rr = 0;
    for (const v of vs) { const s = v.o.tick(v.f) * v.g; l += s * v.l; rr += s * v.r; }
    const fc = cut + cutEnv * Math.exp(-t / cutDecay), g = gate(t, dur, a, r) * norm;
    hpL.run(lpL.run(l, fc, 0.8), 150, 0.7); hpR.run(lpR.run(rr, fc, 0.8), 150, 0.7);
    L[i] = hpL.hp * g; R[i] = hpR.hp * g;
  }
  return [L, R];
}

// Lead: one monophonic line, rendered whole so the pitch can glide (25 ms, exponential) from note to note, with a
// vibrato (0.12 semitone, 5.6 Hz) that fades in 200 ms after each note starts. Five detuned saws, low-passed.
// notes: [{ t, m, d }] in seconds from the line's start.
function lead(notes, total, rnd) {
  const n = len(total), L = new Float32Array(n), R = new Float32Array(n);
  const det = [-0.012, -0.005, 0, 0.005, 0.012], pans = [-0.7, -0.3, 0, 0.3, 0.7];
  const os = det.map(() => new Saw(rnd())), lpL = new SVF(), lpR = new SVF();
  const glide = 1 - Math.exp(-1 / (0.025 * SR));
  let cur = notes[0].m, k = 0, vph = 0;
  for (let i = 0; i < n; i++) {
    const t = i / SR;
    while (k + 1 < notes.length && t >= notes[k + 1].t) k++;
    const nt = notes[k], u = t - nt.t;
    cur += (nt.m - cur) * glide;
    vph += TAU * 5.6 / SR;
    const vib = 0.12 * Math.sin(vph) * ease((u - 0.2) / 0.15);
    const f = mtof(cur + vib), amp = u >= 0 ? gate(u, nt.d, 0.006, 0.05) : 0;
    let l = 0, r = 0;
    for (let j = 0; j < 5; j++) {
      const s = os[j].tick(f * (1 + det[j]));
      l += s * (1 - pans[j]) * 0.5; r += s * (1 + pans[j]) * 0.5;
    }
    const fc = 2200 + 4200 * Math.exp(-Math.max(0, u) / 0.18);
    L[i] = lpL.run(l, fc, 1.0) * amp * 0.35; R[i] = lpR.run(r, fc, 1.0) * amp * 0.35;
  }
  return [L, R];
}

// Pad: four slightly detuned saws per note, a slow attack and release, low-passed at `cut` with a slow swell.
function pad(notes, dur, rnd, { cut = 1400, a = 0.35, r = 0.8 } = {}) {
  const n = len(dur + r), L = new Float32Array(n), R = new Float32Array(n);
  const vs = [];
  for (const m of notes) for (const [d, p] of [[-0.007, -0.8], [-0.002, -0.3], [0.003, 0.3], [0.008, 0.8]])
    vs.push({ o: new Saw(rnd()), f: mtof(m) * (1 + d), l: (1 - p) * 0.5, r: (1 + p) * 0.5 });
  const lpL = new SVF(), lpR = new SVF(), hpL = new SVF(), hpR = new SVF(), norm = 1 / Math.sqrt(vs.length);
  for (let i = 0; i < n; i++) {
    const t = i / SR;
    let l = 0, rr = 0;
    for (const v of vs) { const s = v.o.tick(v.f); l += s * v.l; rr += s * v.r; }
    const fc = cut * (0.7 + 0.3 * Math.sin(Math.PI * Math.min(1, t / dur))), g = gate(t, dur, a, r) * norm;
    hpL.run(lpL.run(l, fc, 0.7), 140, 0.7); hpR.run(lpR.run(rr, fc, 0.7), 140, 0.7);
    L[i] = hpL.hp * g; R[i] = hpR.hp * g;
  }
  return [L, R];
}

// Pluck: a Karplus-Strong string (dsp.ksBuffer) with a short fade at its end.
function pluck(m, dur, rnd, opts = {}) {
  const out = ksBuffer(mtof(m), dur, rnd, { bright: 0.55, t60: 1.1, damp: 0.32, ...opts });
  const fl = len(0.02);
  for (let i = out.length - fl; i < out.length; i++) out[i] *= 1 - ease((i - (out.length - fl)) / fl);
  return out;
}

// Bell: two-operator FM, the modulator at 3.5x so the partials are inharmonic, its index decaying faster than the tone.
function bell(m, { dur = 1.4, index = 2.2 } = {}) {
  const n = len(dur), out = new Float32Array(n), f = mtof(m);
  for (let i = 0; i < n; i++) {
    const t = i / SR;
    const mod = index * Math.exp(-t / 0.18) * Math.sin(TAU * 3.5 * f * t);
    out[i] = Math.sin(TAU * f * t + mod) * Math.exp(-t / 0.45) * ease(t / 0.002) * (1 - ease((t - dur + 0.05) / 0.05));
  }
  return out;
}

// Riser: noise through a band-pass sweeping 300 → 7300 Hz on p² (slow, then fast) and two saws gliding up an octave,
// louder toward the end, with a 4 ms fade so it stops without a click.
function riser(dur, rnd) {
  const n = len(dur), L = new Float32Array(n), R = new Float32Array(n), bpL = new SVF(), bpR = new SVF();
  const a = new Saw(0.1), b = new Saw(0.6), lp = new SVF(), fade = len(0.004);
  for (let i = 0; i < n; i++) {
    const p = i / n, fc = 300 + 7000 * p * p, g = 0.15 + 0.85 * p * p;
    bpL.run(rnd() * 2 - 1, fc, 1.6); bpR.run(rnd() * 2 - 1, fc, 1.6);
    const f = mtof(57) * Math.pow(2, p * p);
    const s = lp.run(0.5 * (a.tick(f) + b.tick(f * 1.006)), 600 + 4000 * p, 0.8) * 0.25 * p;
    const end = i > n - fade ? 1 - ease((i - (n - fade)) / fade) : 1;
    L[i] = (bpL.bp * 0.9 + s) * g * end; R[i] = (bpR.bp * 0.9 + s) * g * end;
  }
  return [L, R];
}

// Impact: a sub drop (60 → 36 Hz) that starts 4 ms after the downbeat, so the kick's click leads, and a short
// burst of low noise for weight.
function impact(rnd) {
  const n = len(1.6), out = new Float32Array(n), lp = new SVF(), d = len(0.004);
  let ph = 0;
  for (let i = d; i < n; i++) {
    const t = (i - d) / SR;
    ph += TAU * (36 + 24 * Math.exp(-t / 0.25)) / SR;
    const nz = lp.run(rnd() * 2 - 1, 180, 0.7) * Math.exp(-t / 0.08);
    out[i] = (Math.sin(ph) * Math.exp(-t / 0.55) + nz * 0.6) * ease(t / 0.004);
  }
  return out;
}

// Crash: metallic squares and noise, high-passed, with a long decay; each channel has its own noise.
function crash(rnd, { dur = 2.4 } = {}) {
  const n = len(dur), L = new Float32Array(n), R = new Float32Array(n);
  const fs = [HAT_F[0] * 1.3, HAT_F[2] * 1.17, HAT_F[3] * 1.41, HAT_F[5] * 1.09], ph = fs.map(() => rnd());
  const hL = new SVF(), hR = new SVF(), lL = new SVF(), lR = new SVF();
  for (let i = 0; i < n; i++) {
    const t = i / SR;
    let m = 0;
    for (let k = 0; k < 4; k++) { ph[k] += fs[k] / SR; m += (ph[k] % 1) < 0.5 ? 0.25 : -0.25; }
    const env = Math.exp(-t / 0.7) * ease(t / 0.001) * (1 - ease((t - dur + 0.1) / 0.1));
    hL.run(lL.run(m * 0.4 + rnd() * 2 - 1, 11000, 0.6), 4200, 0.7);
    hR.run(lR.run(m * 0.4 + rnd() * 2 - 1, 11000, 0.6), 4200, 0.7);
    L[i] = hL.hp * env; R[i] = hR.hp * env;
  }
  return [L, R];
}

// Room tone: band-limited noise (110 Hz – 1.8 kHz), decorrelated left and right, scaled to `rmsDb` dBFS rms.
function roomTone(dur, rnd, { rmsDb = -52 } = {}) {
  const n = len(dur), L = new Float32Array(n), R = new Float32Array(n);
  const f = [new SVF(), new SVF(), new SVF(), new SVF()];
  let e = 0;
  for (let i = 0; i < n; i++) {
    f[0].run(f[1].run(rnd() * 2 - 1, 1800, 0.6), 110, 0.6); f[2].run(f[3].run(rnd() * 2 - 1, 1800, 0.6), 110, 0.6);
    L[i] = f[0].hp; R[i] = f[2].hp; e += L[i] * L[i] + R[i] * R[i];
  }
  const g = Math.pow(10, rmsDb / 20) / Math.sqrt(e / (2 * n));
  for (let i = 0; i < n; i++) { L[i] *= g; R[i] *= g; }
  return [L, R];
}

// Drone: a root and fifth of soft saws under a low-pass that opens over `dur` (the intro's slow reveal).
// Each note is a detuned pair spread left and right; notes below MIDI 50 stay centered, so the low end is mono.
function drone(notes, dur, rnd, { c0 = 220, c1 = 1600, a = 1.5, r = 1.0 } = {}) {
  const n = len(dur + r), L = new Float32Array(n), R = new Float32Array(n);
  const vs = notes.flatMap(m => [-0.004, 0.004].map((d, j) =>
    ({ o: new Saw(rnd()), f: mtof(m) * (1 + d), l: m < 50 ? 0.5 : j ? 0.35 : 0.65 })));
  const lpL = new SVF(), lpR = new SVF();
  for (let i = 0; i < n; i++) {
    const t = i / SR, p = Math.min(1, t / dur);
    let l = 0, rr = 0;
    for (const v of vs) { const s = v.o.tick(v.f); l += s * v.l; rr += s * (1 - v.l); }
    const fc = c0 * Math.pow(c1 / c0, p * p), g = gate(t, dur, a, r) / Math.sqrt(vs.length);
    L[i] = lpL.run(l, fc, 0.8) * g; R[i] = lpR.run(rr, fc, 0.8) * g;
  }
  return [L, R];
}

module.exports = {
  mtof, ease, kick, clap, snare, hat, bass, supersaw, lead, pad, pluck, bell, riser, impact, crash, roomTone, drone,
  HAT_F,
};
