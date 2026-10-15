// tokens.js — the visual tokens, defined once: palette roles, safe area, grid, type. scene.js and post.js read them;
// so can Node (require('./tokens')).
(function (root) {
  const T = typeof module !== 'undefined' && module.exports ? require('./timeline') : root.T;
  const MARGIN = 120;                // title-safe inset on every side; text and key shapes stay inside it

  const TOKENS = {
    color: {
      ink: '#07080C',                // the ground at the frame's edge
      inkLift: '#141722',            // the ground at its center (a soft radial lift)
      paper: '#F3EFE7',              // primary type and the title
      dim: '#8C8A86',                // secondary type
      faint: '#2C2E38',              // inactive marks: ruler ticks, grid dots
      code: '#53C7E8',               // the code shelf's role color (cool)
      craft: '#FF8A4C',              // the craft shelf's role color (warm)
    },
    safe: { x0: MARGIN, y0: MARGIN, x1: T.W - MARGIN, y1: T.H - MARGIN },
    // A 12-column grid inside the safe area, 24 px gutters: the grid dots, shelf labels and corner text sit on it,
    // and each shelf's first item starts on col(3), the others spaced by measured width. Centered type (title,
    // subtitle, closing line) is centered on the frame instead.
    grid: { cols: 12, gutter: 24 },
    font: {
      display: '"Helvetica Neue", Helvetica, Arial, sans-serif',
      mono: 'Menlo, "SF Mono", monospace',
    },
    // Where a shelf's name sits. 'above': a small tracked label above the line's left end, with an "n of 4"
    // counter under its right end. 'row': the name leads its row on the items' baseline, and there is no counter.
    shelfLabel: 'above',
    // The corner labels: the piece's name top left, section, beat and frame top right.
    hud: true,
    // Every face a frame draws with: window.ready loads each one before frame 0.
    faces: [
      '700 100px "Helvetica Neue"', '500 100px "Helvetica Neue"', '400 100px "Helvetica Neue"',
      '300 100px "Helvetica Neue"', '400 100px Menlo', '700 100px Menlo',
    ],
  };
  // Column edges: col(i) is the left edge of column i (0 … 12; col(12) is the right edge of the safe area).
  const S = TOKENS.safe, G = TOKENS.grid;
  const colW = (S.x1 - S.x0 - G.gutter * (G.cols - 1)) / G.cols;
  TOKENS.col = i => S.x0 + i * (colW + G.gutter) - (i === G.cols ? G.gutter : 0);
  TOKENS.colW = colW;

  if (typeof module !== 'undefined' && module.exports) module.exports = TOKENS;
  else root.TOKENS = TOKENS;
})(this);
