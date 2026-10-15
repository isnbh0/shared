// render.js — captures index.html frame by frame in headless Chrome, encodes the frames with ffmpeg, encodes
// score.wav to AAC at the delivery loudness and muxes the two (run `node audio.js` first; `npm run render` does both).
//   node render.js                        the whole piece → out/showcase.mp4, its audio gated at -14 LUFS, <= -1 dBTP
//   node render.js --frames 0-90          frames 0 … 89 only (end exclusive), with the matching slice of sound
//   node render.js --fps 60 --out a.mp4   another frame rate, another output path
//   node render.js --samples 16           motion-blur sub-frames per frame (default 16; 1 turns the blur off)
//   node render.js --crf 18 --abr 320k    the H.264 quality (CRF, lower is better) and the AAC bit rate
//   node render.js --master               an upload master: CRF 14, x264 preset slow, AAC 320 kbit/s, the same
//                                         loudness → out/showcase-master.mp4 (unless --out is given)
// Chrome comes from the CHROME_PATH environment variable.
const puppeteer = require('puppeteer-core');
const ffmpeg = require('ffmpeg-static');
const { spawn } = require('child_process');
const { pathToFileURL } = require('url');
const fs = require('fs');
const path = require('path');
const T = require('./timeline');
const { readWav, encodeAac, gate, ff } = require('./delivery');

const die = m => { console.error('render.js: ' + m); process.exit(1); };
const argv = process.argv.slice(2);
if (argv.includes('--help') || argv.includes('-h')) {
  const head = fs.readFileSync(__filename, 'utf8').split('\n');
  console.log(head.slice(0, head.findIndex(l => !l.startsWith('//'))).map(l => l.replace(/^\/\/ ?/, '')).join('\n'));
  process.exit(0);
}
for (let i = 0; i < argv.length; i += 2) {
  if (argv[i] === '--master') { i--; continue; }
  if (!['--frames', '--fps', '--out', '--samples', '--crf', '--abr'].includes(argv[i]) || argv[i + 1] === undefined)
    die(`unknown or incomplete option ${argv[i]} (options: --frames a-b, --fps n, --out file.mp4, --samples n, `
      + '--crf n, --abr rate, --master; --help)');
}
const opt = (k, d) => (argv.includes(k) ? argv[argv.indexOf(k) + 1] : d);

const FPS = Number(opt('--fps', T.FPS));
if (!(FPS > 0)) die('--fps must be a positive number');
const MASTER = argv.includes('--master');
const CRF = Number(opt('--crf', MASTER ? 14 : 18)), PRESET = MASTER ? 'slow' : 'medium', ABR = opt('--abr', '320k');
if (!(CRF >= 0 && CRF <= 51)) die('--crf must be a number from 0 to 51');
if (!/^\d+k$/.test(ABR)) die('--abr must look like 256k');
const SAMPLES = Number(opt('--samples', 16));
if (!(SAMPLES >= 1 && Number.isInteger(SAMPLES))) die('--samples must be a whole number >= 1');
const TOTAL = T.frameCount(FPS);
const m = /^(\d+)-(\d+)$/.exec(opt('--frames', `0-${TOTAL}`));
if (!m || +m[1] >= +m[2] || +m[2] > TOTAL) {
  die(`--frames must be a-b with 0 <= a < b <= ${TOTAL} (the piece at ${FPS} fps)`);
}
const F0 = +m[1], F1 = +m[2], N = F1 - F0, WHOLE = F0 === 0 && F1 === TOTAL;
const OUT = path.resolve(opt('--out', path.join(__dirname, 'out', MASTER ? 'showcase-master.mp4' : 'showcase.mp4')));
const SCORE = path.join(__dirname, 'score.wav'), EVENTS = path.join(__dirname, 'score-events.json');

// Check the inputs before any frame is drawn.
const CHROME = process.env.CHROME_PATH;
if (!CHROME) die('CHROME_PATH is not set. Point it at a Chrome or Chromium executable, for example\n'
  + '  export CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"   # macOS\n'
  + '  export CHROME_PATH="$(command -v google-chrome || command -v chromium)"              # Linux');
if (!fs.existsSync(CHROME)) die(`CHROME_PATH is ${CHROME}, which does not exist`);
for (const f of [SCORE, EVENTS]) {
  if (!fs.existsSync(f)) die(`${path.basename(f)} not found: run node audio.js first (npm run render runs both)`);
}

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: true,
    // CPU raster for 2D canvas: a frame comes out as the same bytes in every run. GPU raster is faster but can
    // differ by a few code values from run to run.
    args: ['--force-device-scale-factor=1', '--disable-gpu-rasterization', '--disable-accelerated-2d-canvas',
      '--mute-audio'],
  });
  const page = await browser.newPage();
  page.on('pageerror', e => console.error('[page error]', e.message));
  await page.setViewport({ width: T.W, height: T.H });
  // The score's events, handed to the page before its scripts run.
  await page.evaluateOnNewDocument(ev => { window.SCORE_EVENTS = ev; }, JSON.parse(fs.readFileSync(EVENTS, 'utf8')));
  await page.goto(pathToFileURL(path.join(__dirname, 'index.html')).href + `?render&fps=${FPS}`);
  await page.evaluate(() => window.ready);

  // The page contract: draw frame f into canvas#c, then read the canvas back as PNG.
  const grab = f => page.evaluate((f, s) => {
    window.draw(f, s);
    return document.getElementById('c').toDataURL('image/png');
  }, f, SAMPLES)
    .then(u => Buffer.from(u.slice(u.indexOf(',') + 1), 'base64'));

  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  const base = OUT.replace(/\.mp4$/, ''), VIDEO = base + '.video.mp4', AUDIO = base + '.m4a';
  const ffv = spawn(ffmpeg, ['-hide_banner', '-loglevel', 'error', '-y',
    '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    // RGB to BT.709 video range, tagged as such, so players show the canvas colors (tags on the frames too:
    // ffmpeg 7-9 leave primaries and transfer unset on filtered frames otherwise).
    '-vf', 'scale=out_color_matrix=bt709:out_range=tv,'
      + 'setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv,format=yuv420p',
    '-c:v', 'libx264', '-preset', PRESET, '-crf', String(CRF), '-tune', 'film',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-an', VIDEO], { stdio: ['pipe', 'ignore', 'inherit'] });
  const closed = new Promise(r => ffv.on('close', r));
  ffv.on('close', code => { if (code !== 0) die(`ffmpeg exited ${code}`); });
  ffv.stdin.on('error', () => {});

  console.log(`rendering frames ${F0}-${F1 - 1} (${N} frames, ${(N / FPS).toFixed(2)} s at ${FPS} fps, `
    + `${SAMPLES} sub-frames, CRF ${CRF}, AAC ${ABR}) → ${path.relative(process.cwd(), OUT)}`);
  const t0 = Date.now();
  for (let f = F0; f < F1; f++) {
    const png = await grab(f);
    if (!ffv.stdin.write(png)) await new Promise(r => ffv.stdin.once('drain', r));
    if ((f - F0 + 1) % (Math.round(FPS) * 2) === 0 || f === F1 - 1)
      console.log(`  frame ${f - F0 + 1}/${N}  ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  }
  ffv.stdin.end();
  await closed;
  await browser.close();

  // Sound: the frames' own slice of score.wav, cut to 16 bits with dither and encoded. The whole piece is measured
  // on the encoded file and corrected to the delivery targets; a slice keeps the score's own level.
  const [L, R] = readWav(SCORE), a = Math.round(F0 / FPS * 48000), b = Math.round(F1 / FPS * 48000);
  const mm = encodeAac(L.subarray(a, b), R.subarray(a, b), AUDIO,
    { target: WHOLE ? { lufs: T.LUFS, tpMax: T.TP_MAX } : null, bitrate: ABR, log: console.log });
  ff(['-i', VIDEO, '-i', AUDIO, '-map', '0:v:0', '-map', '1:a:0', '-c', 'copy', '-t', String(N / FPS),
    '-movflags', '+faststart', OUT], 'mux');
  fs.unlinkSync(VIDEO); fs.unlinkSync(AUDIO);
  if (WHOLE) gate(OUT, { lufs: T.LUFS, tpMax: T.TP_MAX });
  console.log(`done → ${OUT}${mm ? '' : ' (a slice: loudness not gated)'}`);
})().catch(e => die(e.stack || e.message));
