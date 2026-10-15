// render.js — captures index.html frame by frame in headless Chrome, encodes the frames with ffmpeg and muxes
// in score.wav (run `node audio.js` first; `npm run render` does both).
//   node render.js                        the whole clip → out/clip.mp4
//   node render.js --frames 0-90          frames 0 … 89 only (end exclusive), with the matching slice of sound
//   node render.js --fps 60 --out a.mp4   another frame rate, another output path
// Chrome comes from the CHROME_PATH environment variable.
const puppeteer = require('puppeteer-core');
const ffmpeg = require('ffmpeg-static');
const { spawn } = require('child_process');
const { pathToFileURL } = require('url');
const fs = require('fs');
const path = require('path');
const T = require('./timeline');

const die = m => { console.error('render.js: ' + m); process.exit(1); };
const argv = process.argv.slice(2);
if (argv.includes('--help') || argv.includes('-h')) {
  const head = fs.readFileSync(__filename, 'utf8').split('\n');
  console.log(head.slice(0, head.findIndex(l => !l.startsWith('//'))).map(l => l.replace(/^\/\/ ?/, '')).join('\n'));
  process.exit(0);
}
for (let i = 0; i < argv.length; i += 2) {
  if (!['--frames', '--fps', '--out'].includes(argv[i]) || argv[i + 1] === undefined)
    die(`unknown or incomplete option ${argv[i]} (options: --frames a-b, --fps n, --out file.mp4; --help)`);
}
const opt = (k, d) => (argv.includes(k) ? argv[argv.indexOf(k) + 1] : d);

const FPS = Number(opt('--fps', T.FPS));
if (!(FPS > 0)) die('--fps must be a positive number');
const TOTAL = T.frameCount(FPS);
const m = /^(\d+)-(\d+)$/.exec(opt('--frames', `0-${TOTAL}`));
if (!m || +m[1] >= +m[2] || +m[2] > TOTAL) die(`--frames must be a-b with 0 <= a < b <= ${TOTAL} (the clip at ${FPS} fps)`);
const F0 = +m[1], F1 = +m[2], N = F1 - F0;
const OUT = path.resolve(opt('--out', path.join(__dirname, 'out', 'clip.mp4')));
const SCORE = path.join(__dirname, 'score.wav');

// Check the inputs before any frame is drawn.
const CHROME = process.env.CHROME_PATH;
if (!CHROME) die('CHROME_PATH is not set. Point it at a Chrome or Chromium executable, for example\n'
  + '  export CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"   # macOS\n'
  + '  export CHROME_PATH="$(command -v google-chrome || command -v chromium)"              # Linux');
if (!fs.existsSync(CHROME)) die(`CHROME_PATH is ${CHROME}, which does not exist`);
if (!fs.existsSync(SCORE)) die('score.wav not found: run node audio.js first (npm run render runs both)');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: true,
    // CPU raster for 2D canvas: a frame comes out as the same bytes in every run. GPU raster is faster but can
    // differ by a few code values from run to run.
    args: ['--force-device-scale-factor=1', '--disable-gpu-rasterization', '--disable-accelerated-2d-canvas', '--mute-audio'],
  });
  const page = await browser.newPage();
  page.on('pageerror', e => console.error('[page error]', e.message));
  await page.setViewport({ width: T.W, height: T.H });
  await page.goto(pathToFileURL(path.join(__dirname, 'index.html')).href + `?render&fps=${FPS}`);
  await page.evaluate(() => window.ready);

  // The page contract: draw frame f into canvas#c, then read the canvas back as PNG.
  const grab = f => page.evaluate(f => { window.draw(f); return document.getElementById('c').toDataURL('image/png'); }, f)
    .then(u => Buffer.from(u.slice(u.indexOf(',') + 1), 'base64'));

  // Picture from the pipe; sound from score.wav, cut to the frames' own time span so both start together.
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  const s0 = T.frameToSec(F0, FPS), dur = N / FPS;
  const ff = spawn(ffmpeg, ['-hide_banner', '-loglevel', 'error', '-y',
    '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-ss', String(s0), '-t', String(dur), '-i', SCORE,
    '-map', '0:v:0', '-map', '1:a:0',
    // RGB to BT.709 video range, tagged as such, so players show the canvas colors. setparams carries the four
    // tags on the frames themselves: ffmpeg 6 writes them onto the file from the -color* output options alone,
    // while ffmpeg 7-9 leave primaries and transfer unset unless the frames carry them (checked 6.0/9.0.2).
    '-vf', 'scale=out_color_matrix=bt709:out_range=tv,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv,format=yuv420p',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
    '-t', String(dur), '-movflags', '+faststart', OUT], { stdio: ['pipe', 'ignore', 'inherit'] });
  const closed = new Promise(r => ff.on('close', r));
  ff.on('close', code => { if (code !== 0) die(`ffmpeg exited ${code}`); });
  ff.stdin.on('error', () => {});                  // ffmpeg died: its exit code is reported above

  console.log(`rendering frames ${F0}-${F1 - 1} (${N} frames, ${dur.toFixed(2)} s at ${FPS} fps) → ${path.relative(process.cwd(), OUT)}`);
  const t0 = Date.now();
  for (let f = F0; f < F1; f++) {
    const png = await grab(f);
    if (!ff.stdin.write(png)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - F0 + 1) % Math.round(FPS) === 0 || f === F1 - 1)
      console.log(`  frame ${f - F0 + 1}/${N}  ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  }
  ff.stdin.end();
  await closed;
  await browser.close();
  console.log(`done → ${OUT}`);
})().catch(e => die(e.stack || e.message));
