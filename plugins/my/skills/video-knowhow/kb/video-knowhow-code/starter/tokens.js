// tokens.js — the visual tokens, defined once: palette, safe area, type. scene.js reads them; so can Node
// (require('./tokens')), for a checker or a second renderer.
(function (root) {
  const T = typeof module !== 'undefined' && module.exports ? require('./timeline') : root.T;
  const MARGIN = 120;                // px on every side; keep text and key shapes inside the safe area

  const TOKENS = {
    color: {
      bg: '#0B0B10',                 // background
      fg: '#F2EFE8',                 // text and primary shapes
      dim: '#34343F',                // inactive shapes
      accent: '#FF5A36',             // the one accent
    },
    safe: { x0: MARGIN, y0: MARGIN, x1: T.W - MARGIN, y1: T.H - MARGIN },
    font: {
      family: '"Helvetica Neue", Helvetica, Arial, sans-serif',
      weight: 700,
      size: 96,                      // px
    },
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = TOKENS;
  else root.TOKENS = TOKENS;
})(this);
