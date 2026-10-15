// master-loudness.js — in-process mastering for a score synthesized in Node: BS.1770-4 integrated loudness, a
// lookahead true-peak limiter, and the trim search that lands the limited mix on the loudness target.
// When you need it: the score is rendered sample by sample in code and should leave the synth already at the
// delivery loudness under its own ceiling, so the AAC stage only trims about 0 dB (loudness-gate.js).
// Source: generalized from the source production's score (loudness measure, mastering limiter
// and its true-peak estimate, trim search).
// Generalized: sample arrays, ceiling and target are arguments; render(trim) is any function that mixes at a trim.
// Outside the mix, the limiter's window counts the edge's gain (the source counts unity: its mix starts and ends
// quiet, and a mix that starts at full scale was only clamped in its first 3 ms, over the ceiling between samples).
// Left out: the soft clip at 4x before the limiter, the per-hit clip-room steps, the end fade and gap muting.
// The K-weighting coefficients are BS.1770-4's for 48 kHz only.
'use strict';

const SR = 48000;
const CEIL = Math.pow(10, -2 / 20);                 // the limiter's ceiling: -2 dBFS true peak

// BS.1770-4: K-weighting (high shelf, then high-pass), 400 ms blocks every 100 ms, absolute gate -70 LUFS, relative
// gate 10 LU under the mean of what passed it. L and R are Float32Arrays at 48 kHz.
function loudness(L, R) {
  const N = L.length, blk = Math.round(0.4 * SR), hop = Math.round(0.1 * SR), P = new Float64Array(N + 1);
  const f = [[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]];
  for (let i = 0; i < N; i++) {
    let e = 0;
    for (let c = 0; c < 2; c++) {
      const s = f[c], x = (c ? R : L)[i];
      const y = 1.53512485958697 * x - 2.69169618940638 * s[0] + 1.19839281085285 * s[1] + 1.69065929318241 * s[2] - 0.73248077421585 * s[3];
      s[1] = s[0]; s[0] = x; s[3] = s[2]; s[2] = y;
      const h = y - 2 * s[4] + s[5] + 1.99004745483398 * s[6] - 0.99007225036621 * s[7];
      s[5] = s[4]; s[4] = y; s[7] = s[6]; s[6] = h;
      e += h * h;
    }
    P[i + 1] = P[i] + e;                              // prefix sums: each block's energy in O(1)
  }
  const lk = m => -0.691 + 10 * Math.log10(m), z = [];
  for (let s = 0; s + blk <= N; s += hop) z.push((P[s + blk] - P[s]) / blk);
  const mean = a => a.reduce((s, m) => s + m, 0) / a.length;
  const g1 = z.filter(m => lk(m) > -70), thr = lk(mean(g1)) - 10;
  return lk(mean(g1.filter(m => lk(m) > thr)));
}

// True-peak estimate: 4x oversampling with Hann-windowed sinc taps (32), only where a sample is near the ceiling.
const H = 16, TPT = [1, 2, 3].map(p => {
  const t = [];
  for (let k = -H + 1; k <= H; k++) { const x = k - p / 4; t.push(Math.sin(Math.PI * x) / (Math.PI * x) * (0.5 + 0.5 * Math.cos(Math.PI * x / H))); }
  return t;
});
function truePeakAt(X, i, ceil) {
  let pk = Math.abs(X[i]);
  if (pk < 0.5 * ceil || i < H || i >= X.length - H) return pk;
  for (const t of TPT) { let v = 0; for (let k = 0; k < 2 * H; k++) v += X[i - H + 1 + k] * t[k]; pk = Math.max(pk, Math.abs(v)); }
  return pk;
}

// The limiter, in place: the gain each sample needs, a sliding-window minimum over +-W (so the gain is down before
// the peak arrives), box-averaged over the same window (smooth, and still under every peak's need), then a release
// that recovers smoothly. Returns the deepest gain reduction in dB.
function limit(L, R, { ceil = CEIL, lookS = 0.003, relS = 0.08 } = {}) {
  const N = L.length, W = Math.round(lookS * SR), need = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    const pk = Math.max(truePeakAt(L, i, ceil), truePeakAt(R, i, ceil));
    need[i] = pk > ceil ? ceil / pk : 1;
  }
  const hold = new Float32Array(N), dq = new Int32Array(N);   // sliding-window minimum (monotone deque)
  let h = 0, t = 0;
  for (let i = 0; i < N + W; i++) {
    if (i < N) { while (t > h && need[dq[t - 1]] >= need[i]) t--; dq[t++] = i; }
    const c = i - W;
    if (c >= 0) { while (dq[h] < c - W) h++; hold[c] = need[dq[h]]; }
  }
  const rel = 1 - Math.exp(-1 / (relS * SR));
  // The window [-W-1, W-1] before the first step. Outside the mix counts as the edge's gain, so a mix that starts or
  // ends hot is limited there too, not only clamped.
  const h0 = hold[0], h1 = hold[N - 1];
  let acc = (W + 1) * h0, g = 1, gr = 0;
  for (let i = 0; i < W; i++) acc += i < N ? hold[i] : h1;
  for (let i = 0; i < N; i++) {
    acc += (i + W < N ? hold[i + W] : h1) - (i - W - 1 >= 0 ? hold[i - W - 1] : h0);
    const avg = acc / (2 * W + 1);
    g = avg < g ? avg : g + (avg - g) * rel;
    const gg = Math.min(g, avg);
    L[i] = Math.max(-ceil, Math.min(ceil, L[i] * gg)); R[i] = Math.max(-ceil, Math.min(ceil, R[i] * gg));
    gr = Math.max(gr, -20 * Math.log10(gg));
  }
  return gr;
}

// The trim that lands the limited mix on the target: the limiter takes a little loudness, so mix, limit, measure and
// correct, up to four passes, stopping within 0.03 LU. render(trim) -> [L, R] (fresh arrays: limit works in place).
// A mix too peaky for the ceiling stops short, so read I: the limiter takes most of each raise (a sparse kick track
// aimed at -14 LUFS under -2 dBFS stops near -15). The source soft-clips before the limiter, leaving it less to do.
function findTrim(render, { lufs = -14, ceil = CEIL } = {}) {
  let trim = 1, L, R, I = 0, passes = 0;
  for (let p = 0; ; p++) {
    [L, R] = render(trim);
    limit(L, R, { ceil });
    I = loudness(L, R); passes++;
    if (Math.abs(I - lufs) < 0.03 || p === 3) return { trim, I, passes, L, R };
    trim *= Math.pow(10, (lufs - I) / 20);
  }
}

module.exports = { SR, CEIL, loudness, truePeakAt, limit, findTrim };
