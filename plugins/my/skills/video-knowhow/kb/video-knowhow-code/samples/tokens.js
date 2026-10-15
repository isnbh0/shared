// tokens.js — the design values every part reads from one place (palette, margins, the margins a punch-in leaves,
// type stacks), Node-safe so the score, the docs, lint and QA require the same numbers the page draws with; and the
// page's readiness chain, which does not resolve until every face the frames use is loaded and measured.
// When you need it: a value appears in more than one file (a color in the picture and in a QA plot, a margin in the
// page and in the docs), or the first rendered frames come out in a fallback font.
// Source: generalized from the source production's engine (shared-values block, punch box, fonts,
// faces, readiness chain).
// Generalized: accent keys name hues (the source keyed them by section); ready() takes the canvas, the hooks and
// an init step (the source's was its WebGL2 post pass, which throws when WebGL2 is missing: no silent fallback).
// Left out: the film's other shared values (opener card, cuts, groove patterns), its Korean face and the score
// events fetch the source ran between the face loads and document.fonts.ready (here it is a hook).
(function (root) {
  const W = 1920, H = 1080;
  const PALETTE = {
    ink: '#07070D', paper: '#F3F0EA',
    accents: { orange: '#FF5A36', cyan: '#2EE6D6', yellow: '#FFD23F', violet: '#9B7BFF' },
  };
  const SAFE = { x0: 120, y0: 120, x1: W - 120, y1: H - 120 };   // the margins
  // punchBox(z): the margins as a punch-in leaves them. On a hit the camera scales the frame about its center by up
  // to z, so SAFE drawn in toward the center by z, to whole pixels, is where readable type must sit to stay inside
  // SAFE on screen through the punch. punchBox(1) is SAFE.
  const punchBox = (z = 1) => {
    const cx = W / 2, cy = H / 2;
    return { x0: Math.ceil(cx - (cx - SAFE.x0) / z), y0: Math.ceil(cy - (cy - SAFE.y0) / z),
      x1: Math.floor(cx + (SAFE.x1 - cx) / z), y1: Math.floor(cy + (SAFE.y1 - cy) / z) };
  };
  const FONTS = {
    DISPLAY: '"SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif',
    COND: '"SF Pro", "Helvetica Neue", Helvetica, sans-serif',     // pair with ctx.fontStretch = 'condensed'
    MONO: '"SF Mono", Menlo, monospace',
  };
  // Every weight and family a frame draws with, as CSS font shorthands: each must be loaded before frame 0.
  const FACES = [
    `900 100px ${FONTS.DISPLAY}`, `700 100px ${FONTS.DISPLAY}`, `500 100px ${FONTS.DISPLAY}`,
    `900 100px ${FONTS.COND}`, `500 100px ${FONTS.MONO}`, `700 100px ${FONTS.MONO}`,
  ];

  // The page's readiness: load each face (one that fails to load does not block the others), wait for
  // document.fonts, warm each face with one measureText on the canvas, run the hooks together (events fetch, asset
  // decoding, particle sampling: functions returning promises), then init (a GPU post pass), which may throw.
  // window.ready = TOKENS.ready(ctx, { hooks: [loadEvents, sampleParticles], init: () => FINISH.init() });
  function ready(ctx, { hooks = [], init = null, sample = 'Abc 123' } = {}) {
    return Promise.all(FACES.map(f => document.fonts.load(f).catch(() => null)))
      .then(() => document.fonts.ready)
      .then(() => { for (const f of FACES) { ctx.font = f; ctx.measureText(sample); } })
      .then(() => Promise.all(hooks.map(fn => fn())))
      .then(() => init && init())
      .then(() => true);
  }

  const TOKENS = { W, H, PALETTE, SAFE, punchBox, FONTS, FACES, ready };
  if (typeof window === 'undefined' && typeof module !== 'undefined' && module.exports) module.exports = TOKENS;
  else root.TOKENS = TOKENS;
})(this);
