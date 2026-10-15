// chunk-render.js — render a frame list on parallel Chrome workers in 30-frame lossless chunks, cached under a key of
// the source and the job, so a crashed or killed render resumes from its finished chunks.
// When you need it: a render runs long enough that a crash, a kill or a reboot must not cost the finished part, and
// one Chrome is too slow. A frame must be a pure function of its number (seeded randomness, no state carried from
// frame to frame): then which worker draws a chunk, and after which chunk, changes no pixel.
// Source: generalized from the source production's renderer (chunked parallel workers) and its
// render cache (source, environment, and job keys, holder, lock).
// Generalized: the source files are every page file in the page's folder plus this renderer; the Chrome version comes
// from `--version` (the source read macOS Info.plist). Left out: cache listing and pruning (the source's guarded
// removeTree never follows links), the free-disk preflight (2x the unfinished chunks' bytes), older-key cleanup.
// Needs: capture.js beside it (and its puppeteer-core); ffmpeg on PATH (FFMPEG overrides).
// node chunk-render.js page.html first count [workers] [fps]   prints the concat list for delivery-encode.js
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');
const { fork, spawn, spawnSync } = require('child_process');
const { CHROME, openPage, grabber, closeBrowser } = require('./capture.js');

const CHUNK = 30;                                   // frames per chunk, by position in the job's frame list
const ROOT = process.env.RENDER_CACHE || path.join(os.tmpdir(), 'render-cache');
const FFMPEG = process.env.FFMPEG || 'ffmpeg';
const SET709 = 'setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv';

// ---- the key: <source>-<job>, two 12-hex hashes. The same source and job give the same key in any checkout.
const hash = (...parts) => { const h = crypto.createHash('sha256'); for (const p of parts) h.update(p).update('\0'); return h.digest('hex').slice(0, 12); };
// What decides a pixel: the page and every file it loads, the renderer, then the machine (Chrome, ffmpeg, the OS and
// so its fonts). Over-including costs a re-render; leaving an input out reuses chunks the source no longer makes.
function sourceHash(dir) {
  const files = fs.readdirSync(dir).filter(f => /\.(html|js|json|css)$/.test(f)).sort();
  const parts = files.flatMap(f => [f, fs.readFileSync(path.join(dir, f))]);
  for (const f of [__filename, require.resolve('./capture.js')]) parts.push(path.basename(f), fs.readFileSync(f));
  const ver = (cmd, args) => (spawnSync(cmd, args, { encoding: 'utf8' }).stdout || `${path.basename(cmd)} unknown`).split('\n')[0].trim();
  return hash(...parts, `${ver(CHROME, ['--version'])}; ${ver(FFMPEG, ['-version'])}; ${os.platform()} ${os.release()}`);
}
const RASTER = j => (j.preview ? 'gpu' : 'cpu');   // in the key: chunks of the two rasters never mix
const jobHash = j => hash(JSON.stringify([j.frames.join(','), j.scale, j.fps, j.samples, j.grab, !!j.preview, CHUNK, RASTER(j)]));

// ---- the lock: <key>/lock holds { pid }; the key is in use while that pid is alive and is node. A dead run's lock is
// taken over, so a crash never needs a manual unlock.
function holder(dir) {
  let pid = 0;
  try { pid = +JSON.parse(fs.readFileSync(path.join(dir, 'lock'), 'utf8')).pid || 0; } catch { return 0; }
  if (pid === process.pid) return pid;
  try { process.kill(pid, 0); } catch (e) { if (e.code !== 'EPERM') return 0; }
  return /node/.test(spawnSync('ps', ['-p', String(pid), '-o', 'comm='], { encoding: 'utf8' }).stdout || '') ? pid : 0;
}
function lock(dir) {                                // 0 once this process holds it, else the live pid that does
  const f = path.join(dir, 'lock');
  for (;;) {
    try { fs.writeFileSync(f, JSON.stringify({ pid: process.pid, since: new Date().toISOString() }), { flag: 'wx' }); return 0; }
    catch (e) { if (e.code !== 'EEXIST') throw e; }
    const pid = holder(dir);
    if (pid) return pid === process.pid ? 0 : pid;
    try { fs.unlinkSync(f); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  }
}

// ---- worker (child process): one Chrome; asks the parent for chunks until none are left; encodes each to
// <chunk>.<pid>.part and renames it only when ffmpeg has finished, so a killed run leaves no partial chunk.
async function worker(cfg) {
  let cur = null;
  process.on('exit', () => { if (cur) { cur.ff.kill('SIGKILL'); fs.rmSync(cur.tmp, { force: true }); } });
  process.on('disconnect', () => process.exit(1));  // parent gone (failed, killed): stop; puppeteer kills Chrome
  process.on('error', () => process.exit(1));       // IPC to a parent that is already gone
  const { browser, page } = await openPage(cfg);
  const w = Math.round(cfg.width * cfg.scale), h = Math.round(cfg.height * cfg.scale);
  const input = cfg.grab === 'raw' ? ['-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${w}x${h}`, '-framerate', String(cfg.fps), '-i', '-']
    : ['-f', 'image2pipe', '-framerate', String(cfg.fps), '-c:v', 'png', '-i', '-'];
  // Lossless 4:4:4 (qp 0, about 450-630 Mbit/s at 1080p60); previews crf 18. RGB -> BT.709 limited range, once, here,
  // with all four tags set on the frames: ffmpeg 9.0.2 leaves primaries and transfer unset when only the -color_*
  // output options name them (ffmpeg 6.0, which the source encoded with, sets all four from the options).
  const enc = ['-c:v', 'libx264', '-preset', 'veryfast', ...(cfg.preview ? ['-crf', '18'] : ['-qp', '0']), '-pix_fmt', 'yuv444p'];
  const get = grabber(page, cfg.grab);
  const next = () => new Promise(r => { process.once('message', r); process.send({ ready: 1 }); });
  for (let job; (job = await next()).frames;) {
    const { frames, out } = job, tmp = `${out}.${process.pid}.part`;
    const ff = spawn(FFMPEG, ['-hide_banner', '-loglevel', 'error', '-y', ...input, '-vf', 'scale=out_color_matrix=bt709:out_range=tv,' + SET709,
      ...enc, '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-f', 'mp4', tmp],
    { stdio: ['pipe', 'ignore', 'inherit'] });
    cur = { ff, tmp };
    let pending = get(frames[0]);
    for (let i = 0; i < frames.length; i++) {
      const buf = await pending;
      if (i + 1 < frames.length) pending = get(frames[i + 1]);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      process.send({ done: 1 });
    }
    ff.stdin.end();
    const code = await new Promise(r => ff.on('close', r));
    if (code !== 0) throw new Error(`ffmpeg exited ${code} on ${path.basename(out)}`);
    fs.renameSync(tmp, out);
    cur = null;
  }
  await closeBrowser(browser);
}

// ---- parent: the job's chunks under its key; finished ones skipped, the rest handed out in frame order from one
// queue, so a slow stretch costs its own chunk, not one worker's whole share.
async function renderChunks(job, workers = 8) {
  const key = `${sourceHash(path.dirname(path.resolve(job.html)))}-${jobHash(job)}`, dir = path.join(ROOT, key);
  fs.mkdirSync(dir, { recursive: true });
  const pid = lock(dir);
  if (pid) throw new Error(`${dir} is in use by pid ${pid}: the same render is running elsewhere`);
  for (const f of fs.readdirSync(dir)) if (f.endsWith('.part')) fs.rmSync(path.join(dir, f), { force: true });  // a dead run's
  const meta = path.join(dir, 'meta.json');
  if (!fs.existsSync(meta)) fs.writeFileSync(meta, JSON.stringify({ ...job, frames: job.frames.length, chunk: CHUNK, raster: RASTER(job),
    created: new Date().toISOString() }, null, 1) + '\n');
  const parts = [];
  for (let k = 0; k * CHUNK < job.frames.length; k++)
    parts.push({ frames: job.frames.slice(k * CHUNK, (k + 1) * CHUNK), out: path.join(dir, `${String(k).padStart(4, '0')}.mp4`) });
  const todo = parts.filter(p => !fs.existsSync(p.out)), total = todo.reduce((s, p) => s + p.frames.length, 0);
  if (todo.length < parts.length) console.log(`resuming: ${parts.length - todo.length}/${parts.length} chunks done (${dir})`);
  const { frames, ...rest } = job, cfg = JSON.stringify({ ...rest, raster: RASTER(job) }), t0 = Date.now();
  let next = 0, done = 0, last = 0;
  try {
    await Promise.all([...Array(Math.min(workers, todo.length))].map(() => new Promise((res, rej) => {
      const ch = fork(__filename, ['--worker', cfg], { stdio: ['ignore', 'inherit', 'inherit', 'ipc'] });
      ch.on('message', m => {
        if (m.ready) return ch.send(next < todo.length ? todo[next++] : {});
        done += m.done || 0;
        if (Date.now() - last < 3000 && done < total) return;
        last = Date.now();
        const el = (last - t0) / 1000, rate = done / el;
        console.log(`  ${done}/${total} frames  ${rate.toFixed(1)} fps  ETA ${((total - done) / Math.max(rate, 1e-6)).toFixed(0)} s`);
      });
      ch.on('exit', c => (c === 0 ? res() : rej(new Error(`worker exited ${c}`))));
    })));
  } catch (e) {                                     // the other workers see the disconnect when this process exits
    const kept = parts.filter(p => fs.existsSync(p.out)).length;
    throw new Error(`${e.message}; kept ${kept}/${parts.length} chunks in ${dir}: run again to resume`);
  }
  const missing = parts.filter(p => !fs.existsSync(p.out)).length;
  if (missing) throw new Error(`${missing} chunks missing in ${dir} after the render`);
  const list = path.join(dir, 'list.txt');
  fs.writeFileSync(list, parts.map(p => `file '${p.out}'`).join('\n') + '\n');
  // drop() once the delivery file is written: the chunks are worth keeping only until then
  const drop = (keep = false) => (keep ? fs.unlinkSync(path.join(dir, 'lock')) : fs.rmSync(dir, { recursive: true, force: true }));
  return { list, dir, drop };
}

module.exports = { CHUNK, ROOT, sourceHash, jobHash, lock, holder, renderChunks };

if (require.main === module) {
  const argv = process.argv.slice(2);
  // A worker exits by itself once its Chrome is closed: the IPC channel would otherwise keep it alive.
  if (argv[0] === '--worker') worker(JSON.parse(argv[1])).then(() => process.exit(0), e => { console.error(e); process.exit(1); });
  else {
    const [html, first = '0', count, workers = '4', fps = '60'] = argv;
    if (!html || !count) { console.error('node chunk-render.js page.html first count [workers] [fps]'); process.exit(2); }
    const job = { html: path.resolve(html), width: 1920, height: 1080, scale: 1, fps: +fps, samples: 0, grab: 'png', preview: false,
      events: path.join(path.dirname(path.resolve(html)), 'score-events.json'), frames: Array.from({ length: +count }, (_, i) => +first + i) };
    renderChunks(job, +workers).then(r => console.log(r.list), e => { console.error(e.message); process.exit(1); });
  }
}
