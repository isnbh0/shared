// dsp.js — the signal-processing atoms the score is built from. Node only; 48 kHz; every function is deterministic
// (randomness comes in as a seeded stream argument).
//   SVF        state-variable filter (topology-preserving transform), stable under per-sample cutoff changes
//   Saw        band-limited sawtooth (PolyBLEP)
//   ksBuffer   Karplus-Strong plucked string with allpass fine tuning and a pick-position comb
//   freeverb   eight combs and four allpasses per channel, send high-pass, predelay, buffer resets
//   pingpong   tempo-synced ping-pong delay, high-passed in, darkening on each repeat, buffer resets
//   compress   feed-forward stereo-linked compressor with a soft knee
//   lrLow      a fourth-order Linkwitz-Riley low band (two cascaded Butterworth low-passes)
'use strict';

const SR = 48000;
const TAU = Math.PI * 2;
const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);

class SVF {
  constructor() { this.ic1 = 0; this.ic2 = 0; this.fc = -1; this.q = -1; this.lp = 0; this.bp = 0; this.hp = 0; }
  run(x, fc, q = 0.707) {
    if (fc !== this.fc || q !== this.q) {
      this.fc = fc; this.q = q;
      const g = Math.tan(Math.PI * clamp(fc, 10, SR * 0.47) / SR);
      this.k = 1 / q; this.a1 = 1 / (1 + g * (g + this.k)); this.a2 = g * this.a1; this.a3 = g * this.a2;
    }
    const v3 = x - this.ic2;
    const v1 = this.a1 * this.ic1 + this.a2 * v3;
    const v2 = this.ic2 + this.a2 * this.ic1 + this.a3 * v3;
    this.ic1 = 2 * v1 - this.ic1; this.ic2 = 2 * v2 - this.ic2;
    this.lp = v2; this.bp = v1; this.hp = x - this.k * v1 - v2;
    return v2;
  }
}

// PolyBLEP: a two-sample polynomial correction around each wrap, so the step is close to band-limited.
function blep(t, dt) {
  if (t < dt) { t /= dt; return t + t - t * t - 1; }
  if (t > 1 - dt) { t = (t - 1) / dt; return t * t + t + t + 1; }
  return 0;
}
class Saw {
  constructor(phase = 0) { this.ph = phase; }
  tick(f) {
    const dt = Math.min(0.49, f / SR);
    this.ph += dt; if (this.ph >= 1) this.ph -= 1;
    return 2 * this.ph - 1 - blep(this.ph, dt);
  }
}

// Karplus-Strong: a noise burst (low-passed by `bright`, combed at the pick position) circulates in a delay line
// tuned by an allpass for the fraction; the loop gain sets the T60 at every pitch. rnd: a seeded stream.
function ksBuffer(f, dur, rnd, { bright = 0.5, t60 = 1.2, damp = 0.35, pick = 0.17 } = {}) {
  const n = Math.round(dur * SR), out = new Float32Array(n);
  const period = SR / f, L = Math.max(2, Math.floor(period - damp - 0.15));
  const d = period - L - damp, C = (1 - d) / (1 + d);
  const buf = new Float32Array(L), ex = new Float32Array(L);
  const a = 1 - Math.exp(-TAU * (250 + bright * 9000) / SR);
  let y = 0;
  for (let i = 0; i < L; i++) { y += a * (rnd() * 2 - 1 - y); ex[i] = y; }
  const pk = Math.max(1, Math.round(pick * L));
  let mean = 0, mx = 1e-9;
  for (let i = 0; i < L; i++) { buf[i] = ex[i] - 0.85 * ex[(i - pk + L) % L]; mean += buf[i]; }
  mean /= L;
  for (let i = 0; i < L; i++) { buf[i] -= mean; mx = Math.max(mx, Math.abs(buf[i])); }
  for (let i = 0; i < L; i++) buf[i] /= mx;
  const decay = Math.pow(10, -3 / (t60 * f));
  let idx = 0, prev = 0, apx = 0, apy = 0;
  for (let i = 0; i < n; i++) {
    const cur = buf[idx];
    const v = ((1 - damp) * cur + damp * prev) * decay; prev = cur;
    const ap = C * v + apx - C * apy; apx = v; apy = ap;
    buf[idx] = ap; out[i] = cur;
    if (++idx >= L) idx = 0;
  }
  return out;
}

// Freeverb: comb lengths in samples at 44.1 kHz, scaled to 48 kHz and by `size`. The right channel's lines are
// 23 samples longer (decorrelation). resets: sample indices where every line is cleared (the pre-drop gap).
const COMBS = [1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617];
const rt60 = ({ room, size = 1 }) =>
  -3 * size * COMBS.reduce((a, d) => a + d, 0) / COMBS.length / 44100 / Math.log10(room);
function freeverb(inL, inR,
  { room = 0.84, damp = 0.25, gain = 0.015, predelay = 0, size = 1, hpIn = 180, lpOut = 9000, resets = [] } = {}) {
  const n = inL.length, sc = SR / 44100, outL = new Float32Array(n), outR = new Float32Array(n);
  const mk = spread => ({
    combs: COMBS.map(d => ({ buf: new Float32Array(Math.round((d + spread) * sc * size)), i: 0, f: 0 })),
    aps: [556, 441, 341, 225].map(d => ({ buf: new Float32Array(Math.round((d + spread) * sc * size)), i: 0 })),
  });
  const pd = Math.round(predelay * SR), rs = new Set(resets);
  for (const [inp, out, st] of [[inL, outL, mk(0)], [inR, outR, mk(23)]]) {
    const hp = new SVF(), lp = new SVF();
    for (let k = 0; k < n; k++) {
      if (rs.has(k)) { for (const c of st.combs) { c.buf.fill(0); c.f = 0; } for (const a of st.aps) a.buf.fill(0); }
      hp.run(k - pd >= 0 ? inp[k - pd] : 0, hpIn, 0.7);
      const x = hp.hp * gain;
      let s = 0;
      for (const c of st.combs) {
        const y = c.buf[c.i];
        c.f = y * (1 - damp) + c.f * damp;
        c.buf[c.i] = x + c.f * room;
        if (++c.i >= c.buf.length) c.i = 0;
        s += y;
      }
      for (const a of st.aps) {
        const y = a.buf[a.i];
        a.buf[a.i] = s + y * 0.5;
        if (++a.i >= a.buf.length) a.i = 0;
        s = y - s;
      }
      out[k] = lp.run(s, lpOut, 0.6);
    }
  }
  return [outL, outR];
}

// Ping-pong: the mono sum (high-passed at 260 Hz) enters the left line; each line feeds the other through a
// low-pass, so the echoes alternate left, right, left … and darken. time in seconds (a dotted eighth = 0.75 beat).
function pingpong(inL, inR, { time, fb = 0.5, resets = [] }) {
  const n = inL.length, d = Math.round(time * SR), bl = new Float32Array(d), br = new Float32Array(d);
  const outL = new Float32Array(n), outR = new Float32Array(n), hpI = new SVF(), lpA = new SVF(), lpB = new SVF();
  const rs = new Set(resets);
  let i = 0;
  for (let k = 0; k < n; k++) {
    if (rs.has(k)) { bl.fill(0); br.fill(0); }
    hpI.run((inL[k] + inR[k]) * 0.5, 260, 0.7);
    const yl = bl[i], yr = br[i];
    outL[k] = yl; outR[k] = yr;
    bl[i] = hpI.hp + fb * lpA.run(yr, 4200, 0.6);
    br[i] = lpB.run(yl, 4800, 0.6);
    if (++i >= d) i = 0;
  }
  return [outL, outR];
}

// Compressor, in place. thr is linear; returns the largest and the mean gain reduction in dB.
function compress(L, R, { thr, ratio, att, rel, knee = 6, makeup = 1 }) {
  const aA = Math.exp(-1 / (att * SR)), aR = Math.exp(-1 / (rel * SR)), thrDb = 20 * Math.log10(thr);
  let env = 0, grMax = 0, grSum = 0, grN = 0;
  for (let i = 0; i < L.length; i++) {
    const x = Math.max(Math.abs(L[i]), Math.abs(R[i]));
    env = x > env ? aA * env + (1 - aA) * x : aR * env + (1 - aR) * x;
    const over = 20 * Math.log10(env + 1e-9) - thrDb;
    let gr = 0;
    if (over > knee / 2) gr = over * (1 - 1 / ratio);
    else if (over > -knee / 2) gr = (1 - 1 / ratio) * Math.pow(over + knee / 2, 2) / (2 * knee);
    const g = Math.pow(10, -gr / 20) * makeup;
    L[i] *= g; R[i] *= g;
    if (gr > grMax) grMax = gr;
    if (env > 0.01) { grSum += gr; grN++; }
  }
  return { grMax, grAvg: grSum / Math.max(1, grN) };
}

// The low band of a fourth-order Linkwitz-Riley split at fc (two Butterworth low-passes in series). The high band
// is x minus this only approximately, so callers use it where the low band is removed or ducked as a whole.
function lrLow(X, fc) {
  const a = new SVF(), b = new SVF(), out = new Float32Array(X.length);
  for (let i = 0; i < X.length; i++) { a.run(X[i], fc, Math.SQRT1_2); out[i] = b.run(a.lp, fc, Math.SQRT1_2); }
  return out;
}

module.exports = { SR, TAU, clamp, SVF, Saw, ksBuffer, COMBS, rt60, freeverb, pingpong, compress, lrLow };
