// timeline.js — the one clock that picture (index.html, scene.js, post.js) and sound (audio.js) both read.
// Events are placed in beats; seconds and frames follow from them. What the score actually plays (each kick, each
// hook note, each landing) is exported by audio.js to score-events.json, and the picture reads that file.
// Loads in the page (as window.T) and in Node (require('./timeline')).
(function (root) {
  const BPM = 120;
  const SPB = 60 / BPM;              // seconds per beat (0.5 s)
  const BEATS = 52;                  // the piece's length in beats (26 s)
  const DURATION = BEATS * SPB;      // seconds
  const FPS = 30;                    // 15 frames a beat
  const W = 1920, H = 1080;

  // The four sections, in beats: intro, build, drop, resolve.
  const SECTIONS = [
    { id: 'intro', b0: 0, b1: 8 },
    { id: 'build', b0: 8, b1: 24 },
    { id: 'drop', b0: 24, b1: 40 },
    { id: 'resolve', b0: 40, b1: 52 },
  ];
  const sectionAt = b => SECTIONS.find(s => b < s.b1) || SECTIONS[SECTIONS.length - 1];

  // The silence before the drop: sound is digital zero and the picture pure black between these two beats.
  const GAP = { b0: 23.75, b1: 24 };
  const DROP = 24;

  // The end: over the last four beats both sound and picture fall on one curve, which reaches zero on the last
  // frame (beat 52 - 1/15). audio.js multiplies the master by it; post.js multiplies the picture by it.
  const END = { b0: 48, b1: BEATS - 1 / (FPS * SPB), db: 30, tail: 0.15 };
  function endGain(b) {
    const x = Math.min(1, Math.max(0, (b - END.b0) / (END.b1 - END.b0)));
    let g = Math.pow(10, -END.db * x * x / 20);                       // a release that steepens: 30 dB on x^2
    if (x > 1 - END.tail) g *= 0.5 + 0.5 * Math.cos(Math.PI * (x - (1 - END.tail)) / END.tail);   // zero slope at 0
    return g;
  }

  // Delivery targets (Mastering and delivery): integrated loudness and the true-peak maximum of the encoded file.
  const LUFS = -14, TP_MAX = -1;

  const beatToSec = b => b * SPB;
  const secToBeat = s => s / SPB;
  const frameToSec = (f, fps = FPS) => f / fps;
  const frameToBeat = (f, fps = FPS) => f / fps / SPB;
  const beatToFrame = (b, fps = FPS) => Math.floor(b * SPB * fps + 1e-6);   // the frame that shows beat b
  const frameCount = (fps = FPS) => Math.round(DURATION * fps);

  // mulberry32: the same seed gives the same numbers in the page and in Node.
  function rng(seed) {
    let s = seed >>> 0;
    return () => {
      s = (s + 0x6D2B79F5) >>> 0;
      let t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  // A stateless hash in [0, 1): the same (i, seed) gives the same value in any frame and any order.
  const hash = (i, seed = 0) => { const r = rng((i * 2654435761 + seed * 97 + 1) >>> 0); r(); return r(); };

  const T = {
    BPM, SPB, BEATS, DURATION, FPS, W, H, SECTIONS, sectionAt, GAP, DROP, END, endGain, LUFS, TP_MAX,
    beatToSec, secToBeat, frameToSec, frameToBeat, beatToFrame, frameCount, rng, hash,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = T;
  else root.T = T;
})(this);
