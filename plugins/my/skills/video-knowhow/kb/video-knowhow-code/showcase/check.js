// check.js — a flash check of the rendered video (Accessibility and perception: WCAG 2.3.1's general flash).
//   node check.js [file.mp4]          default out/showcase.mp4; `npm run check`
// Decodes each frame at 384×216, converts sRGB to linear light, and takes relative luminance
// (Y = 0.2126 R + 0.7152 G + 0.0722 B) over the whole frame and over each of 4×4 cells. In each series a transition
// runs from one turning point to the next; it counts if Y changes by 0.1 or more and its darker end is below 0.8.
// Two transitions are one flash, and any one second with more than three flashes fails. It also reports the largest
// frame-to-frame change of the whole frame and the largest share of saturated-red pixels (R / (R+G+B) >= 0.8 and
// R >= 64 of 255: near-black encoder noise such as R 1, G 0, B 0 has the ratio but is not visible red).
// A quick proxy for review, not a certified analyzer: it does not measure WCAG's 10-degree field or red flashes.
'use strict';
const path = require('path');
const { spawn } = require('child_process');
const FFMPEG = require('ffmpeg-static');

const SRC = process.argv[2] || path.join(__dirname, 'out', 'showcase.mp4');
const W = 384, H = 216, FRAME = W * H * 3, CELLS = 4;
const LIN = Float64Array.from({ length: 256 }, (_, v) => {
  const c = v / 255;
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
});

const series = Array.from({ length: 1 + CELLS * CELLS }, () => []);   // [0] the whole frame, then the cells
let red = 0, fps = 30, buf = Buffer.alloc(0);

function frame(px) {
  const sum = new Float64Array(CELLS * CELLS);
  let reds = 0;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const i = (y * W + x) * 3, r = px[i], g = px[i + 1], b = px[i + 2];
    const cell = Math.floor(y * CELLS / H) * CELLS + Math.floor(x * CELLS / W);
    sum[cell] += 0.2126 * LIN[r] + 0.7152 * LIN[g] + 0.0722 * LIN[b];
    if (r >= 64 && r / (r + g + b) >= 0.8) reds++;
  }
  const n = (W / CELLS) * (H / CELLS);
  series[0].push(sum.reduce((a, v) => a + v, 0) / (W * H));
  for (let k = 0; k < sum.length; k++) series[k + 1].push(sum[k] / n);
  red = Math.max(red, reds / (W * H));
}

// Transitions between turning points, then the most flashes (transition pairs) in any one second. Held frames
// are skipped when looking for a turn, so a strobe that holds each state for a few frames still counts.
function flashes(s) {
  const ext = [0];
  let dir = 0;
  for (let i = 1; i < s.length; i++) {
    const d = Math.sign(s[i] - s[i - 1]);
    if (d === 0) continue;
    if (dir !== 0 && d !== dir) ext.push(i - 1);
    dir = d;
  }
  ext.push(s.length - 1);
  const tr = [];
  for (let k = 0; k + 1 < ext.length; k++) {
    const a = s[ext[k]], b = s[ext[k + 1]];
    if (Math.abs(b - a) >= 0.1 && Math.min(a, b) < 0.8) tr.push(ext[k + 1]);
  }
  let most = 0;
  for (const i of tr) most = Math.max(most, tr.filter(j => j >= i && j < i + fps).length);
  return { transitions: tr.length, perSecond: most / 2 };
}

const probe = spawn(FFMPEG, ['-hide_banner', '-i', SRC]);
let info = '';
probe.stderr.on('data', d => { info += d; });
probe.on('close', () => {
  const m = info.match(/(\d+(?:\.\d+)?) fps/);
  if (m) fps = Math.round(+m[1]);
  const ff = spawn(FFMPEG, ['-v', 'error', '-i', SRC, '-vf', `scale=${W}:${H}:in_range=tv:in_color_matrix=bt709`,
    '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-']);
  ff.stderr.pipe(process.stderr);
  ff.stdout.on('data', d => {
    buf = Buffer.concat([buf, d]);
    while (buf.length >= FRAME) { frame(buf.subarray(0, FRAME)); buf = buf.subarray(FRAME); }
  });
  ff.on('close', code => {
    if (code !== 0 || !series[0].length) { console.error(`check.js: could not decode ${SRC}`); process.exit(1); }
    const full = flashes(series[0]);
    const cells = series.slice(1).map(flashes), worst = Math.max(...cells.map(c => c.perSecond));
    let jump = 0, at = 0;
    for (let i = 1; i < series[0].length; i++) {
      const d = Math.abs(series[0][i] - series[0][i - 1]);
      if (d > jump) { jump = d; at = i; }
    }
    console.log(`${path.basename(SRC)}: ${series[0].length} frames at ${fps} fps`);
    console.log(`whole frame: ${full.transitions} transitions, at most ${full.perSecond} flashes in any second`);
    console.log(`worst of ${CELLS * CELLS} cells: at most ${worst} flashes in any second`);
    console.log(`largest frame-to-frame change of the whole frame: ${jump.toFixed(3)} (frames ${at - 1} to ${at})`);
    console.log(`saturated red: at most ${(100 * red).toFixed(2)} % of a frame`);
    const pass = full.perSecond <= 3 && worst <= 3;
    console.log(pass ? 'flash check: pass (three flashes or fewer in every second)' : 'flash check: FAIL');
    process.exit(pass ? 0 : 1);
  });
});
