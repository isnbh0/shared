// beat-clock.js — one beat timeline for picture and score: beats to frames and back, beat ranges as whole frames,
// a 16th-step groove grid, and the score's events as played, recorded by the synth and read by the picture.
// When you need it: picture and sound are both generated, and every hit the picture lands on must come from the
// score's own record of what it played, not from a hand-copied table that drifts after the next score edit.
// Source: generalized from the source production's beat clock (frame spans), score (event record
// and events file write), and engine (hit agreement checks).
// Generalized: tempo and frame rate are arguments to clock(); event names are free. Left out: the film's sections,
// slots and step patterns. Runs in Node (the synth, QA) and in the page (window.BEAT).
(function (root) {
  // ---- the clock. 120 BPM at 60 fps is 30 frames a beat.
  function clock({ bpm = 120, fps = 60 } = {}) {
    const SPB = 60 / bpm, fpb = fps * SPB;
    return {
      bpm, fps, SPB, fpb,
      beatOf: frame => frame / fpb,                   // the beat a frame shows (its shutter opens here)
      timeOf: beat => beat * SPB,
      // A beat range a-b as whole frames, the one rule for every range tool: snap outward. f0 is the frame showing
      // beat a, f1 the frame after the one showing b (end exclusive), so frames f0 ... f1-1 cover every beat asked
      // for, each once. A beat on a whole frame (to 1e-6 frame) is that frame. b0, b1: f0 and f1 back as beats.
      frameSpan(a, b) {
        const f0 = Math.floor(a * fpb + 1e-6), f1 = Math.ceil(b * fpb - 1e-6);
        return { f0, f1, b0: f0 / fpb, b1: f1 / fpb };
      },
    };
  }

  // ---- the groove grid: steps are 16th positions in a 4/4 bar (four = [0, 4, 8, 12]; tresillo = [0, 6, 12]).
  // The most recent hit at or before beat x: { i, step, at, since, next, bar, n } (n counts hits from beat 0).
  function hits(x, steps) {
    const sx = x * 4, bar = Math.floor(sx / 16), inBar = sx - bar * 16;
    let i = -1;
    for (let k = 0; k < steps.length; k++) if (steps[k] <= inBar + 1e-9) i = k;
    let hb = bar;
    if (i < 0) { hb = bar - 1; i = steps.length - 1; }
    const at = (hb * 16 + steps[i]) / 4;
    const nx = i + 1 < steps.length ? (hb * 16 + steps[i + 1]) / 4 : ((hb + 1) * 16 + steps[0]) / 4;
    return { i, step: steps[i], at, since: x - at, next: nx - x, bar: hb, n: hb * steps.length + i };
  }

  // ---- score side: record each event where it is actually played (after swing, fills and replacements), in beats
  // rounded to 1e-4, and write one key per line so a diff of the events file reads as a diff of the score.
  const r4 = x => Math.round(x * 1e4) / 1e4;
  function recorder(note = 'Beats from 0. Written by the score; read by the picture instead of copying tables.') {
    const ev = {};
    return {
      add(key, b, extra) { (ev[key] ||= []).push(extra ? { b: r4(b), ...extra } : r4(b)); },
      json() {
        const out = { note };
        for (const [k, v] of Object.entries(ev)) out[k] = [...v].sort((p, q) => (p.b ?? p) - (q.b ?? q));
        return '{\n' + Object.entries(out).map(([k, v]) => '  ' + JSON.stringify(k) + ': ' + JSON.stringify(v)).join(',\n') + '\n}\n';
      },
    };
  }

  // ---- picture side. An event list as sorted beats: numbers are beats; { b } is a beat, { t } seconds.
  const beatsOf = (a, SPB = 0.5) => (Array.isArray(a) ? a : [])
    .map(x => (typeof x === 'number' ? x : x && (x.b != null ? x.b : x.t != null ? x.t / SPB : NaN)))
    .filter(Number.isFinite).sort((p, q) => p - q);
  // A stand-in table (used until the score exists) must be the score once it does: a disagreement beyond tol beats
  // stops the page instead of drawing to the wrong hits.
  function agree(score, table, what, tol = 0.1) {
    const near = (b, a) => a.some(x => Math.abs(x - b) < tol);
    const onlyScore = score.filter(b => !near(b, table)), onlyTable = table.filter(b => !near(b, score));
    if (onlyScore.length || onlyTable.length)
      throw new Error(`${what}: only the score has ${onlyScore.join(', ') || 'none'}; only the table has ${onlyTable.join(', ') || 'none'}`);
  }
  // window.SCORE_EVENTS (inlined by the renderer) or a fetched events file, checked against the stand-in.
  function useEvents(ev, fallback = {}, SPB = 0.5) {
    if (!ev) return { source: 'stand-in', ...fallback };
    const out = { source: 'score' };
    for (const [k, v] of Object.entries(ev)) {
      if (!Array.isArray(v)) { out[k] = v; continue; }
      out[k] = beatsOf(v, SPB);
      if (fallback[k]) agree(out[k], fallback[k], k);
    }
    return out;
  }
  // The most recent event at or before beat x (binary search over sorted beats), or null.
  function lastHit(list, x) {
    let lo = 0, hi = list.length - 1, r = -1;
    while (lo <= hi) { const m = (lo + hi) >> 1; if (list[m] <= x + 1e-9) { r = m; lo = m + 1; } else hi = m - 1; }
    return r < 0 ? null : list[r];
  }

  const BEAT = { clock, hits, r4, recorder, beatsOf, agree, useEvents, lastHit };
  if (typeof module !== 'undefined' && module.exports) module.exports = BEAT;
  else root.BEAT = BEAT;
})(this);
