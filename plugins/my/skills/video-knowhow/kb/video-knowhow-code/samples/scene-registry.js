// scene-registry.js — scenes as registered pure functions of time over beat segments: which scenes are live at a
// beat, how two hand off across a boundary (fade and slide, self-handled overlap, or a hard cut), and a draw that
// survives a broken scene. Plus the loader that lets scene files be missing.
// When you need it: several people or agents write scenes in separate files against one timeline, and a seam
// between two scenes must be decided by the timeline and the scenes' declared hand-off, not by each scene.
// Source: generalized from the source production's engine (scene dispatch, segment cuts, hand-off
// rules, placeholder) and page (script loader).
// Generalized: segments, hard cuts and the overlap are arguments; env carries only timing (b, t, u, len,
// transition) plus whatever base you pass. Left out: the film's section scenes and bookend fallbacks, its camera and
// world hooks (fn.camera, fn.world), the page pull-back, and the env's text and lockup helpers.
// Scene contract: SCENES[id] = function (ctx, u, env) { ... }, u = beats since the segment starts, called while
// u is in [-ov, len + ov] inside save/restore. No Math.random, Date or accumulated state; seeded randomness only.
// SCENES[id].handoff = 'fade' (default) | 'self' | 'overlap' | 'cut'; .seamIn / .seamOut = true: only this
// scene is drawn at that boundary (it draws the seam itself).
(function (root) {
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const win = (x, x0, x1) => clamp((x - x0) / (x1 - x0));
  const smooth = u => u * u * (3 - 2 * u), inCubic = u => u * u * u, outCubic = u => 1 - Math.pow(1 - u, 3);

  // segs [{ id, b0, b1 }] in beats; hard: boundaries that are deliberate cuts; beats: the film's length.
  function createScenes({ segs, hard = [], beats, ov = 0.25, slide = 140, scenes = root.SCENES || (root.SCENES = {}) }) {
    const HARD = new Set(hard), fnOf = seg => scenes[seg.id];
    const handoffOf = seg => (fnOf(seg) && fnOf(seg).handoff) || 'fade';
    // A boundary is a single-segment cut when it is a deliberate hard moment, when either side asks for 'cut', or
    // when the incoming scene sets seamIn / the outgoing one seamOut.
    const cutAt = X => HARD.has(X) || segs.some(s => fnOf(s) && (
      (s.b0 === X && (fnOf(s).seamIn === true || fnOf(s).handoff === 'cut')) ||
      (s.b1 === X && (fnOf(s).seamOut === true || fnOf(s).handoff === 'cut'))));
    // Live segments at beat b: each reaches ov past its boundaries unless the boundary is a cut.
    const activeSegs = b => segs.filter(s => b >= (cutAt(s.b0) ? s.b0 : s.b0 - ov) && b < (cutAt(s.b1) ? s.b1 : s.b1 + ov));
    // Where a segment is in its hand-off: phase 'in' or 'out' and p 0 -> 1 across the 2·ov overlap; else null.
    function transitionOf(seg, b) {
      if (b < seg.b0 + ov && !cutAt(seg.b0) && seg.b0 > 0) return { phase: 'in', p: win(b, seg.b0 - ov, seg.b0 + ov) };
      if (b > seg.b1 - ov && !cutAt(seg.b1) && seg.b1 < beats) return { phase: 'out', p: win(b, seg.b1 - ov, seg.b1 + ov) };
      return { phase: null, p: 0 };
    }
    const envOf = (seg, b, t, base) => Object.assign({}, base, { id: seg.id, b, t, u: b - seg.b0, len: seg.b1 - seg.b0,
      transition: transitionOf(seg, b) });
    // A missing scene draws its id, so the cut is still reviewable; a throwing scene logs once and the frame goes on.
    const placeholder = (ctx, u, env) => {
      ctx.fillStyle = '#888'; ctx.font = '500 48px Menlo, monospace'; ctx.textAlign = 'center';
      ctx.fillText(env.id, (env.W || 1920) / 2, (env.H || 1080) / 2);
    };
    const errors = new Set();
    function drawSeg(ctx, seg, env) {
      ctx.save();
      try { (fnOf(seg) || placeholder)(ctx, env.u, env); } catch (e) {
        if (!errors.has(seg.id)) { errors.add(seg.id); console.error(`scene ${seg.id}:`, e); }
      }
      ctx.restore();
    }
    // One scene: straight onto ctx. Two in a hand-off: each into its own layer (layers: two 2D contexts the size of
    // ctx's canvas), composited in one pass. 'fade': the outgoing fades and slides left, the incoming fades in from
    // the right; 'self' and 'overlap': both at full opacity, the scenes read env.transition.
    function draw(ctx, b, t, { base = {}, layers = null, scale = 1 } = {}) {
      const act = activeSegs(b);
      if (act.length < 2 || !layers) { for (const seg of act) drawSeg(ctx, seg, envOf(seg, b, t, base)); return act; }
      for (const [k, seg] of act.entries()) {
        const lx = layers[k % 2], lc = lx.canvas;
        lx.setTransform(1, 0, 0, 1, 0, 0); lx.clearRect(0, 0, lc.width, lc.height); lx.setTransform(scale, 0, 0, scale, 0, 0);
        drawSeg(lx, seg, envOf(seg, b, t, base));
        const tr = transitionOf(seg, b), mode = handoffOf(seg);
        let a = 1, dx = 0;
        if (mode === 'fade' && tr.phase === 'out') { a = 1 - smooth(tr.p); dx = -inCubic(tr.p) * slide; }
        if (mode === 'fade' && tr.phase === 'in') { a = smooth(tr.p); dx = (1 - outCubic(tr.p)) * slide; }
        if (a <= 0.001) continue;
        ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = a;
        ctx.drawImage(lc, Math.round(dx * scale), 0);
        ctx.restore();
      }
      return act;
    }
    return { scenes, cutAt, activeSegs, transitionOf, draw };
  }

  // Scene files, one per scene; a missing file is skipped (its segments get the placeholder). The page's ready waits
  // for them: window.ready = loadScenes(files).then(() => engineReady).
  const loadScenes = files => Promise.all(files.map(src => new Promise(res => {
    const el = document.createElement('script');
    el.src = src; el.onload = () => res(true); el.onerror = () => { el.remove(); res(false); };
    document.body.appendChild(el);
  })));

  const SCENE_REGISTRY = { createScenes, loadScenes };
  if (typeof module !== 'undefined' && module.exports) module.exports = SCENE_REGISTRY;
  else root.SCENE_REGISTRY = SCENE_REGISTRY;
})(this);
