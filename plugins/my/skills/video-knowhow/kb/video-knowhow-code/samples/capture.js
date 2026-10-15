// capture.js — open the page in headless Chrome, wait for window.ready, and pull each frame off the canvas as
// PNG (or raw RGBA) bytes, the next frame drawing while the current one is written.
// When you need it: a page draws frames on a canvas and a Node process must turn frame numbers into image bytes,
// the same bytes on every run, without Chrome lingering after the last frame.
// Source: generalized from the source production's renderer (page open, frame grabber, browser
// shutdown, the worker's frame loop).
// Generalized: page path, size, scale, samples and the events file are arguments; frames come off <canvas id="c">
// (the source read its engine's main canvas). Left out: the preview switches and the film's own URL parameters.
// Page contract: window.ready (a Promise that rejects on a missing asset), window.draw(frame, samples), the query
// ?render&scale=<s>[&samples=<n>][&fps=<f>], and window.SCORE_EVENTS, set here before any page script runs. The
// source's page took its frame rate from its own timeline; fps is for a page that reads it (the starter's does).
// Needs: npm install puppeteer-core; Google Chrome (CHROME overrides the path). 'raw' needs Uint8Array#toBase64,
// and Chrome logs a getImageData hint unless the page made #c's context with { willReadFrequently: true }.
// node capture.js page.html out-dir first count [events.json]   writes out-dir/NNNNNN.png
'use strict';
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const CLOSE_S = 10;

// raster 'cpu' keeps 2D canvases on Skia's CPU path: the same bytes every run, about 12 times as long a frame
// (mean 0.4 s -> 4.9 s in the source film). 'gpu' is for previews: GPU raster came out 1-10 codes apart run to run.
// WebGL stays on the GPU either way.
async function openPage({ html, width = 1920, height = 1080, scale = 1, samples = 0, fps = 0, raster = 'cpu', events = null }) {
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: true, pipe: true, protocolTimeout: 600000,
    args: ['--force-device-scale-factor=1', '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
      '--disable-backgrounding-occluded-windows', '--mute-audio', '--allow-file-access-from-files',
      '--disable-gpu-rasterization', ...(raster === 'cpu' ? ['--disable-accelerated-2d-canvas'] : [])],
  });
  const page = await browser.newPage();
  // Page errors reach the terminal. Filter only noise the page makes on purpose (the source skipped
  // ERR_FILE_NOT_FOUND from optional script files it probes for).
  page.on('console', m => {
    if ((m.type() === 'error' || m.type() === 'warn') && !/ERR_FILE_NOT_FOUND/.test(m.text())) console.error(`[page ${m.type()}] ${m.text()}`);
  });
  page.on('pageerror', e => console.error('[page error]', e.message));
  await page.setViewport({ width: Math.round(width * scale), height: Math.round(height * scale) });
  // The score's event times, inlined before the page's scripts run: no fetch, which file:// may refuse.
  if (events && fs.existsSync(events))
    await page.evaluateOnNewDocument(s => { window.SCORE_EVENTS = JSON.parse(s); }, fs.readFileSync(events, 'utf8'));
  const q = `?render&scale=${scale}` + (samples ? `&samples=${samples}` : '') + (fps ? `&fps=${fps}` : '');
  await page.goto('file://' + path.resolve(html) + q);
  await page.evaluate(() => window.ready);   // fonts, events, assets: a rejected ready stops the run here
  return { browser, page };
}

// Frame transfer. 'png': the page encodes, compact over the protocol. 'raw': RGBA bytes, no encode in the page.
function grabber(page, mode = 'png') {
  if (mode === 'raw') return f => page.evaluate(f => {
    window.draw(f);
    const c = document.getElementById('c');
    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
    return new Uint8Array(d.buffer).toBase64();
  }, f).then(s => Buffer.from(s, 'base64'));
  return f => page.evaluate(f => { window.draw(f); return document.getElementById('c').toDataURL('image/png'); }, f)
    .then(u => Buffer.from(u.slice(u.indexOf(',') + 1), 'base64'));
}

// Frames in order into sink(buf, frame) (an ffmpeg stdin, a file). The next frame's draw is requested before the
// current one is written, so the page and the encoder work at the same time.
async function capture(page, frames, sink, mode = 'png') {
  const get = grabber(page, mode);
  let pending = get(frames[0]);
  for (let i = 0; i < frames.length; i++) {
    const buf = await pending;
    if (i + 1 < frames.length) pending = get(frames[i + 1]);
    await sink(buf, frames[i]);
  }
}

// Every Chrome that openPage starts ends here. browser.close() waits for Chrome to answer and then to exit, with no
// limit on the exit; here it gets CLOSE_S s for both. Past that, or if close fails, Chrome's process group is killed.
// Then this process's pipes to Chrome are closed, so nothing of Chrome's keeps node running.
async function closeBrowser(browser) {
  const proc = browser.process(), wait = (p, s) => {
    let t;
    return Promise.race([p, new Promise(r => { t = setTimeout(r, s * 1000, 'timeout'); })]).finally(() => clearTimeout(t));
  };
  const closing = browser.close().then(() => 'closed', e => e);
  const r = await wait(closing, CLOSE_S);
  if (r !== 'closed') {
    console.error(`capture.js: Chrome (pid ${proc.pid}) ${r === 'timeout' ? `had not exited ${CLOSE_S} s after close()` : `failed to close (${(r && r.message) || r})`}; killing its process group`);
    try { process.kill(-proc.pid, 'SIGKILL'); } catch {}   // puppeteer launches Chrome as its own group's leader
    await wait(closing, 5);                                  // puppeteer then removes Chrome's temp profile
  }
  for (const s of proc.stdio) if (s) s.destroy();
}

module.exports = { CHROME, openPage, grabber, capture, closeBrowser };

if (require.main === module) {
  const [html, out, first = '0', count = '1', events] = process.argv.slice(2);
  if (!html || !out) { console.error('node capture.js page.html out-dir first count [events.json]'); process.exit(2); }
  (async () => {
    fs.mkdirSync(out, { recursive: true });
    const { browser, page } = await openPage({ html, events });
    const frames = Array.from({ length: +count }, (_, i) => +first + i);
    await capture(page, frames, (buf, f) => fs.promises.writeFile(path.join(out, `${String(f).padStart(6, '0')}.png`), buf));
    await closeBrowser(browser);
    console.log(`wrote ${frames.length} frames to ${out}`);
  })().catch(e => { console.error(e); process.exit(1); });
}
