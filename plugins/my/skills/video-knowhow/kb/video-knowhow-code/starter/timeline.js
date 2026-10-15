// timeline.js — the one clock that picture (index.html, scene.js) and sound (audio.js) both read.
// Place events in beats. Seconds and frames follow from them, so picture and sound cannot drift.
// Loads in the page (as window.T) and in Node (require('./timeline')).
(function (root) {
  const BPM = 120;
  const SPB = 60 / BPM;              // seconds per beat (0.5 s)
  const BEATS_PER_BAR = 4;
  const BEATS = 16;                  // the clip's length in beats (8 s)
  const DURATION = BEATS * SPB;      // seconds
  const FPS = 30;                    // the default frame rate; render.js --fps sets another
  const W = 1920, H = 1080;          // the canvas, in pixels

  // Conversions between beats, seconds and frames. Frame n shows time n / fps; frame 0 is t = 0.
  const beatToSec = b => b * SPB;
  const secToBeat = s => s / SPB;
  const frameToSec = (f, fps = FPS) => f / fps;
  const beatToFrame = (b, fps = FPS) => Math.floor(b * SPB * fps + 1e-6);   // the frame that shows beat b
  const frameCount = (fps = FPS) => Math.round(DURATION * fps);

  // Cues: events that picture and sound share, in beats.
  const CUES = {
    text: 4,                         // the text line lands on the first beat of bar 2
  };

  // A seeded random stream (mulberry32): the same seed gives the same numbers in the page and in Node.
  // Use it for every random choice. Math.random would make each render different.
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

  const T = {
    BPM, SPB, BEATS_PER_BAR, BEATS, DURATION, FPS, W, H, CUES, rng,
    beatToSec, secToBeat, frameToSec, beatToFrame, frameCount,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = T;
  else root.T = T;
})(this);
