// preview.js — serves this folder on http://localhost:8000 (PORT sets another) for the live preview: open the
// address in a browser and click the page for sound. Byte ranges are served, so the browser can seek score.wav.
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = Number(process.env.PORT || 8000);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.wav': 'audio/wav', '.png': 'image/png', '.json': 'application/json' };

http.createServer((req, res) => {
  const rel = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const file = path.join(__dirname, rel === '/' ? 'index.html' : rel);
  if (!file.startsWith(__dirname + path.sep)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); return res.end('not found'); }
    const head = { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Accept-Ranges': 'bytes', 'Cache-Control': 'no-store' };
    const r = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || '');
    if (!r) { res.writeHead(200, { ...head, 'Content-Length': data.length }); return res.end(data); }
    const a = r[1] ? +r[1] : Math.max(0, data.length - +r[2]), b = r[1] && r[2] ? Math.min(+r[2], data.length - 1) : data.length - 1;
    res.writeHead(206, { ...head, 'Content-Range': `bytes ${a}-${b}/${data.length}`, 'Content-Length': b - a + 1 });
    res.end(data.subarray(a, b + 1));
  });
}).listen(PORT, '127.0.0.1', () => console.log(`preview: http://localhost:${PORT}/   (Ctrl-C stops it)`));
