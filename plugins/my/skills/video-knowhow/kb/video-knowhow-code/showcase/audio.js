// audio.js — synthesizes the score from timeline.js and writes score.wav (48 kHz, 24-bit, TPDF dither) and
// score-events.json (every kick, hook note, landing and accent the picture follows, in beats).
//   node audio.js                       score.wav + score-events.json
// Other scripts call renderScore(opts) for variants: { sends: false } (no reverb or delay), { sidechain: false },
// { solo: ['drums'] } (only the named buses; add 'returns' to hear their reverb and delay too);
// fixed: { norm, trim } reuses the full mix's gains so variants compare.
// The same code writes the same bytes: no Date, no Math.random; every voice draws from its own seeded stream.
'use strict';
const fs = require('fs');
const path = require('path');
const T = require('./timeline');
const { SR, SVF, freeverb, pingpong, compress, lrLow, rt60 } = require('./dsp');
const V = require('./voices');
const { loudness, limit, findTrim } = require('../samples/master-loudness');
const { writeWav } = require('../samples/wav-writer');
const { eventRng } = require('../samples/seeded-streams');

const N = Math.round(T.DURATION * SR);
const S = b => b * T.SPB;                                    // beat → seconds
const I = b => Math.round(b * T.SPB * SR);                   // beat → sample index
const GAP0 = I(T.GAP.b0), GAP1 = I(T.GAP.b1), FADE = Math.round(0.005 * SR);
const RV = { room: 0.86, damp: 0.3, size: 1.1, predelay: 0.018 };
const DELAY = 0.75 * T.SPB;                                  // a dotted eighth
// The sections and the drop come from timeline.js; every other beat below is an offset from one of them.
const SEC = Object.fromEntries(T.SECTIONS.map(s => [s.id, s]));
const BUILD = SEC.build.b0, DROP = T.DROP, RESOLVE = SEC.resolve.b0, END = T.BEATS;
const GAP = T.GAP.b0;                                        // the build runs up to the gap
const RISER = { b0: GAP - 5.75, b1: GAP };                   // the riser's span; exported for the picture

// The harmony, in beats. Bass roots, pad voicings and the hook's six pitches per chord (3-3-2-3-3-2 sixteenths).
const STEPS = [0, 3, 6, 8, 11, 14].map(s => s / 4);
const CH = {
  Am: { root: 33, pad: [57, 60, 64, 69], hook: [76, 72, 69, 76, 74, 72] },
  F: { root: 29, pad: [53, 57, 60, 65], hook: [77, 72, 69, 77, 76, 72] },
  C: { root: 36, pad: [55, 60, 64, 67], hook: [79, 76, 72, 79, 77, 76] },
  G: { root: 31, pad: [55, 59, 62, 67], hook: [79, 74, 71, 79, 81, 83] },
  Fmaj7: { root: 29, pad: [53, 57, 60, 64] },
  G6: { root: 31, pad: [52, 55, 59, 62] },
  Amadd9: { root: 33, pad: [57, 60, 64, 71] },                 // A C E B: an added ninth, no seventh
};
const PROG = ['Am', 'F', 'C', 'G'];

// A stereo bus. add() places a buffer (mono, or [L, R]) at a beat with a gain and a constant-power pan, and feeds
// the reverb and delay sends. Anything that starts before the gap is cut there with a 5 ms half-cosine fade, so the
// gap is digital zero and nothing from the build rings into the drop.
class Bus {
  constructor(name) { this.name = name; this.L = new Float32Array(N); this.R = new Float32Array(N); }
  add(src, b, { g = 1, pan = 0, rv = 0, dl = 0 } = {}, sends) {
    const st = Array.isArray(src) ? src : [src, src];
    const i0 = I(b), stop = i0 < GAP0 ? GAP0 : N, n = Math.min(st[0].length, stop - i0);
    if (i0 >= GAP0 && i0 < GAP1) return;                          // nothing starts inside the gap
    const gl = g * Math.cos((pan + 1) * Math.PI / 4) * Math.SQRT2;
    const gr = g * Math.sin((pan + 1) * Math.PI / 4) * Math.SQRT2;
    for (let k = 0; k < n; k++) {
      const i = i0 + k;
      if (i < 0) continue;
      const f = stop - i < FADE ? V.ease((stop - i) / FADE) : 1;
      const l = st[0][k] * gl * f, r = st[1][k] * gr * f;
      this.L[i] += l; this.R[i] += r;
      if (sends && rv) { sends.rv.L[i] += l * rv; sends.rv.R[i] += r * rv; }
      if (sends && dl) { sends.dl.L[i] += l * dl; sends.dl.R[i] += r * dl; }
    }
  }
}

// The kick's sidechain: 4 ms down, exponential release; a bus is multiplied by 1 - depth * env.
function duckEnv(kicks, rel) {
  const env = new Float32Array(N), a = 0.004 * SR, w = Math.round(6 * rel * SR);
  for (const b of kicks) {
    const i0 = I(b);
    for (let k = 0; k < w && i0 + k < N; k++) {
      const v = k < a ? k / a : Math.exp(-(k - a) / (rel * SR));
      if (v > env[i0 + k]) env[i0 + k] = v;
    }
  }
  return env;
}
const duck = (bus, env, depth) => {
  for (let i = 0; i < N; i++) { const g = 1 - depth * env[i]; bus.L[i] *= g; bus.R[i] *= g; }
};

// A per-sample gain curve from beat breakpoints [[b, dB], …], eased between them.
function curve(points) {
  const out = new Float32Array(N);
  for (let i = 0, k = 0; i < N; i++) {
    const b = i / SR / T.SPB;
    while (k + 1 < points.length && b >= points[k + 1][0]) k++;
    const [b0, d0] = points[k], [b1, d1] = points[Math.min(k + 1, points.length - 1)];
    const x = b1 > b0 ? Math.min(1, Math.max(0, (b - b0) / (b1 - b0))) : 0;
    out[i] = Math.pow(10, (d0 + (d1 - d0) * V.ease(x)) / 20);
  }
  return out;
}

// Swung sixteenths: the second of each pair lands at 54 % of the pair (an MPC-style swing).
const swing16 = j => Math.floor(j / 2) * 0.5 + (j % 2 ? 0.54 * 0.5 : 0);

function renderScore({ sends = true, sidechain = true, solo = null, fixed = null } = {}) {
  const B = Object.fromEntries(['drums', 'bass', 'bed', 'lead', 'pluck', 'fx'].map(k => [k, new Bus(k)]));
  const SND = { rv: new Bus('rv'), dl: new Bus('dl') };
  const ev = {
    kicks: [], claps: [], snares: [], hats: [], hook: [], lands: [], stabs: [], crashes: [], bass: [], chords: [],
  };
  const keep = k => !solo || solo.includes(k);
  // Only buses that are heard feed the returns, so a solo's reverb and delay carry that solo alone.
  const put = (bus, src, b, o) => B[bus].add(src, b, o, sends && keep(bus) ? SND : null);

  // ---- intro (beats 0–8): a drone whose low-pass opens, and the pluck hook entering at beat 2, dark and wet.
  put('fx', V.drone([45, 52, 57], S(BUILD), eventRng(0, 1)), 0, { g: 0.55, rv: 0.3 });
  const pluckAt = (b, m, o = {}, src = 'pluck') => {
    const bright = b < BUILD ? 0.18 + 0.03 * b : Math.min(0.62, 0.42 + 0.02 * (b - BUILD));
    put('pluck', V.pluck(m, 1.6, eventRng(b, 2), { bright }), b,
      { g: o.g ?? 0.7, pan: o.pan ?? 0, rv: o.rv ?? 0.45, dl: o.dl ?? 0.28 });
    ev.hook.push({ b, m, src });
  };
  STEPS.forEach((s, k) => pluckAt(BUILD - 6 + s, CH.Am.hook[k], { rv: 0.7, dl: 0.35 }));
  STEPS.slice(0, 3).forEach((s, k) => pluckAt(BUILD - 2 + s, CH.Am.hook[k], { rv: 0.7, dl: 0.35 }));

  // ---- build (beats 8–23.75): chords, kick from beat 8 behind an opening low-pass, bass from 12, hats from 12,
  // claps on 17 and 19, landings 10–17, riser 18–23.75, snare roll 20–23.625, the drums high-passed in the last
  // bar, the bass running on to the gap so the build peaks into it.
  for (let c = 0; c < 4; c++) {
    const b0 = BUILD + 4 * c, ch = CH[PROG[c]];
    ev.chords.push({ b0, b1: b0 + 4, name: PROG[c] });
    put('bed', V.pad(ch.pad, S(4), eventRng(b0, 3), { cut: 700 + 260 * c }), b0, { g: 0.32, rv: 0.4 });
    STEPS.forEach((s, k) => pluckAt(b0 + s, ch.hook[k], { pan: k % 2 ? 0.25 : -0.25 }));
  }
  for (let b = BUILD; b < GAP; b++) { put('drums', V.kick(eventRng(b, 4)), b, { g: 0.9 }); ev.kicks.push(b); }
  for (let b = BUILD + 4.5; b < GAP; b += 1) {
    const ch = CH[PROG[Math.floor((b - BUILD) / 4)]];
    put('bass', V.bass(V.mtof(ch.root + 12), S(0.4), { env: 900 + 120 * Math.max(0, b - (BUILD + 12)) }), b,
      { g: 0.4 });
    ev.bass.push(b);
  }
  for (let b = BUILD + 4; b < GAP - 0.25; b++) for (let j = 0; j < 4; j++) {
    if (b < BUILD + 8 && j !== 2) continue;
    const r = eventRng(b, 10 + j), hb = b + swing16(j) + (r() - 0.5) * 0.005 / T.SPB;
    if (hb >= GAP) continue;
    const vel = j === 2 ? 1 : j === 0 ? 0.62 : 0.45 + 0.1 * r();
    put('drums', V.hat(r), hb, { g: 0.85 * vel, pan: 0.22 });
    ev.hats.push(+hb.toFixed(4));
  }
  for (let b = BUILD + 9; b < BUILD + 12; b += 2) {
    put('drums', V.clap(eventRng(b, 5)), b, { g: 0.85, rv: 0.3 }); ev.claps.push(b);
  }
  // The snare roll: eighths, then sixteenths, then thirty-seconds, up to the gap.
  const roll = [], R0 = GAP - 3.75, R1 = GAP - 0.125;
  for (let b = R0; b < GAP - 1.75; b += 0.5) roll.push(b);
  for (let b = GAP - 1.75; b < GAP - 0.75; b += 0.25) roll.push(b);
  for (let b = GAP - 0.75; b < GAP - 0.124; b += 0.125) roll.push(b);
  for (const b of roll) {
    const p = (b - R0) / (R1 - R0);
    put('drums', V.snare(eventRng(b, 6), { pitch: 190 + 210 * p, tail: 0.12 - 0.06 * p }), b,
      { g: 0.42 * Math.pow(10, (-11.5 + 14 * p * p) / 20), rv: 0.25, pan: (p - 0.5) * 0.2 });
    ev.snares.push({ b, v: +p.toFixed(3) });
  }
  const LAND = [[2, 'code', 88], [3, 'craft', 81], [4, 'code', 89], [5, 'craft', 81],
    [6, 'code', 84], [7, 'craft', 79], [8, 'code', 91], [9, 'craft', 79]];       // beats into the build
  LAND.forEach(([o, shelf, m], k) => {
    const b = BUILD + o;
    put('pluck', V.bell(m), b, { g: 0.2, pan: shelf === 'code' ? -0.35 : 0.35, rv: 0.55, dl: 0.3 });
    ev.lands.push({ b, shelf, i: k >> 1 });
  });
  put('fx', V.riser(S(RISER.b1 - RISER.b0), eventRng(RISER.b0, 7)), RISER.b0, { g: 0.32, rv: 0.2 });

  // ---- drop (beats 24–40): impact and crash, four-on-the-floor, claps, swung hats, 3-3-2 bass, supersaw stabs on
  // each chord's first three hits, the hook as a gliding supersaw lead, a pad under all of it.
  put('fx', V.impact(eventRng(DROP, 8)), DROP, { g: 0.55 });
  for (const b of [DROP, DROP + 8, RESOLVE]) {
    put('fx', V.crash(eventRng(b, 9)), b, { g: b === RESOLVE ? 0.16 : 0.2, rv: 0.2 }); ev.crashes.push(b);
  }
  for (let b = DROP; b <= RESOLVE; b++) { put('drums', V.kick(eventRng(b, 4)), b, { g: 0.8 }); ev.kicks.push(b); }
  for (let b = DROP + 1; b < RESOLVE; b += 2) {
    put('drums', V.clap(eventRng(b, 5)), b, { g: 1.0, rv: 0.3 }); ev.claps.push(b);
  }
  for (let b = DROP; b < RESOLVE; b++) for (let j = 0; j < 4; j++) {
    const r = eventRng(b, 10 + j), hb = b + swing16(j) + (r() - 0.5) * 0.005 / T.SPB;
    const open = b >= DROP + 8 && j === 2, vel = j === 2 ? 1 : j === 0 ? 0.6 : 0.42 + 0.12 * r();
    put('drums', V.hat(r, { open }), hb, { g: (open ? 0.55 : 0.9) * vel, pan: 0.22 });
    ev.hats.push(+hb.toFixed(4));
  }
  const leadNotes = [];
  for (let c = 0; c < 4; c++) {
    const b0 = DROP + 4 * c, ch = CH[PROG[c]];
    ev.chords.push({ b0, b1: b0 + 4, name: PROG[c] });
    put('bed', V.pad(ch.pad, S(4), eventRng(b0, 3), { cut: 1700 }), b0, { g: 0.17, rv: 0.35 });
    for (let h = 0; h < 2; h++) [0, 0.75, 1.5].forEach((o, k) => {
      const b = b0 + 2 * h + o, m = ch.root + 12 + (k === 2 ? 12 : 0);
      put('bass', V.bass(V.mtof(m), S(k === 2 ? 0.4 : 0.6)), b, { g: 0.36 });
      ev.bass.push(b);
    });
    [0, 0.75, 1.5].forEach(o => {
      put('bed', V.supersaw(ch.pad.map(m => m + 12), S(0.3), eventRng(b0 + o, 11)), b0 + o,
        { g: 0.55, rv: 0.3, dl: 0.14 });
      ev.stabs.push(b0 + o);
    });
    STEPS.forEach((s, k) => {
      const next = k + 1 < STEPS.length ? STEPS[k + 1] : 4;
      leadNotes.push({ t: S(b0 - DROP + s), m: ch.hook[k], d: S((next - s) * 0.85) });
      ev.hook.push({ b: b0 + s, m: ch.hook[k], src: 'lead' });
    });
  }
  put('lead', V.lead(leadNotes, S(RESOLVE - DROP + 0.5), eventRng(DROP, 12)), DROP,
    { g: 0.95, rv: 0.25, dl: 0.3 });

  // ---- resolve (beats 40–52): drums out after the beat-40 hit; a pad on Fmaj7, G6, Am(add9); the pluck slowed to
  // quarter notes with heavy ping-pong throws; quiet legato bass roots, the last held into the end curve, which
  // takes it all to zero.
  [[0, 4, 'Fmaj7'], [4, 2, 'G6'], [6, 4, 'Amadd9']].forEach(([o, d, name], k, all) => {
    const b0 = RESOLVE + o;
    ev.chords.push({ b0, b1: b0 + d, name });
    put('bed', V.pad(CH[name].pad, S(d), eventRng(b0, 3), { cut: 1300, r: 1.2 }), b0, { g: 0.27, rv: 0.5 });
    const last = k === all.length - 1, len = last ? S(END - b0) : S(d) + 0.1;    // overlaps the next note
    put('bass', V.bass(V.mtof(CH[name].root + 12), len, { env: 300, drive: 1.2 }), b0, { g: 0.15 });
  });
  [76, 72, 69, 72, 74, 71, 72, 76, 81]
    .forEach((m, k) => pluckAt(RESOLVE + k, m, { pan: k % 2 ? 0.3 : -0.3, rv: 0.55, dl: 0.6 }));

  // ---- drum processing: an opening low-pass (beats 8–16), a closing high-pass (20–23.75), glue compression,
  // and a parallel crushed copy blended in through the drop.
  const D = B.drums, lpL = new SVF(), lpR = new SVF(), hpL = new SVF(), hpR = new SVF();
  for (let i = 0; i < N; i++) {
    const b = i / SR / T.SPB;
    const lp = b < BUILD + 8 ? 250 * Math.pow(18000 / 250, Math.pow(Math.max(0, (b - BUILD) / 8), 2)) : 0;
    const hp = b >= R0 && b < DROP ? 30 * Math.pow(220 / 30, Math.pow((b - R0) / (GAP - R0), 2)) : 0;
    if (lp) { D.L[i] = lpL.run(D.L[i], lp, 0.9); D.R[i] = lpR.run(D.R[i], lp, 0.9); }
    if (hp) { hpL.run(D.L[i], hp, 0.8); hpR.run(D.R[i], hp, 0.8); D.L[i] = hpL.hp; D.R[i] = hpR.hp; }
  }
  const crushL = Float32Array.from(D.L), crushR = Float32Array.from(D.R);
  compress(D.L, D.R, { thr: 0.35, ratio: 3, att: 0.008, rel: 0.12 });
  compress(crushL, crushR, { thr: 0.06, ratio: 8, att: 0.001, rel: 0.08, makeup: 3 });
  const blend = curve([[0, -60], [DROP - 0.1, -60], [DROP, -9], [RESOLVE, -9], [RESOLVE + 0.5, -60]]);
  for (let i = 0; i < N; i++) { D.L[i] += crushL[i] * blend[i] * 0.5; D.R[i] += crushR[i] * blend[i] * 0.5; }

  // ---- sidechain from the kicks: bass deepest, then pad and stabs, then the lead.
  if (sidechain) {
    const short = duckEnv(ev.kicks, 0.1), long = duckEnv(ev.kicks, 0.16);
    duck(B.bass, short, 0.75); duck(B.bed, long, 0.5); duck(B.lead, long, 0.3);
  }

  // ---- returns: one reverb, one ping-pong delay; both cleared at the gap, so the drop starts from a dry room.
  // From the resolve the returns come up 7 dB, so with the drums gone the pluck's throws are heard as echoes.
  const ret = { L: new Float32Array(N), R: new Float32Array(N) };
  if (sends) {
    const resets = [GAP0, GAP1];
    const [rl, rr] = freeverb(SND.rv.L, SND.rv.R, { ...RV, resets });
    const [dl, dr] = pingpong(SND.dl.L, SND.dl.R, { time: DELAY, fb: 0.45, resets });
    const lift = curve([[0, 0], [RESOLVE - 0.5, 0], [RESOLVE + 0.5, 7], [END, 7]]);
    for (let i = 0; i < N; i++) {
      ret.L[i] = (rl[i] * 1.7 + dl[i] * 0.6) * lift[i]; ret.R[i] = (rr[i] * 1.7 + dr[i] * 0.6) * lift[i];
    }
    if (sidechain) duck(ret, duckEnv(ev.kicks, 0.16), 0.35);
  }

  // ---- master: sum, mono below 120 Hz, a level set (the drop to -15 LUFS) before the bus compressor, the section
  // arc, the gap and the end curve, then trim and limit to -14 LUFS under -2 dBFS (master-loudness.js).
  const L = new Float32Array(N), R = new Float32Array(N);
  for (const k of Object.keys(B)) if (keep(k)) for (let i = 0; i < N; i++) { L[i] += B[k].L[i]; R[i] += B[k].R[i]; }
  if (keep('returns') || !solo) for (let i = 0; i < N; i++) { L[i] += ret.L[i]; R[i] += ret.R[i]; }
  const side = new Float32Array(N);
  for (let i = 0; i < N; i++) side[i] = (L[i] - R[i]) / 2;
  const sideLow = lrLow(side, 120);
  for (let i = 0; i < N; i++) { L[i] -= sideLow[i]; R[i] += sideLow[i]; }
  const airL = new SVF(), airR = new SVF();                    // a gentle shelf: about +3 dB above 6 kHz
  for (let i = 0; i < N; i++) {
    airL.run(L[i], 6000, 0.6); airR.run(R[i], 6000, 0.6);
    L[i] += 0.4 * airL.hp; R[i] += 0.4 * airR.hp;
  }
  const dropL = L.subarray(I(DROP), I(RESOLVE)), dropR = R.subarray(I(DROP), I(RESOLVE));
  const norm = fixed ? fixed.norm : Math.pow(10, (-15 - loudness(dropL, dropR)) / 20);
  for (let i = 0; i < N; i++) { L[i] *= norm; R[i] *= norm; }
  const comp = compress(L, R, { thr: Math.pow(10, -14 / 20), ratio: 1.6, att: 0.03, rel: 0.25 });
  const arc = curve([[0, -3], [BUILD, -3], [BUILD + 0.01, -3.5], [R0, -2.5], [GAP, 0], [DROP, 0], [RESOLVE, 0],
    [RESOLVE + 1, -0.5], [END, -0.5]]);
  for (let i = 0; i < N; i++) {
    const b = i / SR / T.SPB;
    let g = arc[i] * T.endGain(b);
    if (i >= GAP0 - FADE && i < GAP0) g *= V.ease((GAP0 - i) / FADE);
    if (i >= GAP0 && i < GAP1) g = 0;
    L[i] *= g; R[i] *= g;
  }
  const mix = trim => [L.map(x => x * trim), R.map(x => x * trim)];
  let out;
  if (fixed) {
    const [a, b] = mix(fixed.trim); limit(a, b);
    out = { trim: fixed.trim, L: a, R: b, I: loudness(a, b), passes: 0 };
  }
  else out = findTrim(mix, { lufs: T.LUFS });

  // The opening's room tone (-52 dBFS rms), under the drone and gone by the build; added after the limiter.
  if (!solo) {
    const [tl, tr] = V.roomTone(S(9), eventRng(0, 13));
    for (let i = 0; i < tl.length; i++) {
      const g = V.ease(i / (0.02 * SR)) * (1 - V.ease((i - I(6)) / I(3)));
      out.L[i] += tl[i] * g; out.R[i] += tr[i] * g;
    }
  }
  ev.gap = T.GAP; ev.drop = T.DROP; ev.riser = RISER; ev.impact = DROP;
  ev.reverb = { rt60: +rt60(RV).toFixed(3) };
  for (const k of ['kicks', 'claps', 'hats', 'stabs', 'bass']) ev[k].sort((a, b) => a - b);
  ev.hook.sort((a, b) => a.b - b.b);
  return { L: out.L, R: out.R, norm, trim: out.trim, I: out.I, passes: out.passes, comp, events: ev };
}

module.exports = { renderScore, N, I };

if (require.main === module) {
  const r = renderScore();
  const peak = writeWav(path.join(__dirname, 'score.wav'), r.L, r.R, { seed: 7 });
  fs.writeFileSync(path.join(__dirname, 'score-events.json'), JSON.stringify(r.events));
  console.log(`score.wav: ${T.DURATION} s, ${r.I.toFixed(2)} LUFS after ${r.passes} trim passes, sample peak `
    + `${(20 * Math.log10(peak)).toFixed(2)} dBFS, bus compressor max ${r.comp.grMax.toFixed(1)} dB; `
    + 'score-events.json written');
}
