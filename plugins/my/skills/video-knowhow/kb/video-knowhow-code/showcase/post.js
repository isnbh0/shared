// post.js — what happens to a whole frame after its sub-frames are averaged: bloom, vignette, film grain, the
// fade in from black, the gap, and the end curve the sound also follows (T.endGain).
//   bloom     the frame shrunk to 1/8, blurred and added back; it swells on the drop and decays with the
//             reverb's RT60 (from score-events.json), so the light rings as long as the room
//   grain     eight 256 px tiles of seeded noise made once; each frame picks a tile and an offset by hash
//   gap       pure black while the sound is digital zero
(function (root) {
  const { W, H } = T;
  const small = document.createElement('canvas'); small.width = W / 8; small.height = H / 8;
  const sctx = small.getContext('2d');
  const blur = document.createElement('canvas'); blur.width = W / 8; blur.height = H / 8;
  const bctx = blur.getContext('2d');

  const TILE = 256, tiles = [];
  for (let k = 0; k < 8; k++) {
    const c = document.createElement('canvas'); c.width = c.height = TILE;
    const g = c.getContext('2d'), img = g.createImageData(TILE, TILE), r = T.rng(500 + k);
    for (let i = 0; i < TILE * TILE; i++) {
      const v = Math.round(128 + (r() + r() + r() - 1.5) * 90);      // roughly Gaussian around mid-gray
      img.data[4 * i] = img.data[4 * i + 1] = img.data[4 * i + 2] = v; img.data[4 * i + 3] = 255;
    }
    g.putImageData(img, 0, 0);
    tiles.push(c);
  }

  function post(ctx, t, fps = T.FPS) {
    const b = T.secToBeat(t), f = Math.floor(t * fps + 1e-6);   // f: the render's own frame number
    if (b >= T.GAP.b0 && b < T.GAP.b1) { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); return; }

    // Bloom.
    const u = (b - T.DROP) * T.SPB, rt = EV.reverb.rt60;
    const kick = sceneHit(EV.kicks, b, 0.09);
    const lastKick = EV.kicks[EV.kicks.length - 1];
    const amt = 0.16 + (u >= 0 && b < lastKick + 0.5 ? 0.5 * Math.exp(-u / (rt / 6.9)) + 0.1 * kick : 0);
    sctx.drawImage(ctx.canvas, 0, 0, W / 8, H / 8);
    bctx.filter = 'blur(6px)'; bctx.clearRect(0, 0, W / 8, H / 8); bctx.drawImage(small, 0, 0); bctx.filter = 'none';
    ctx.save();
    ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = amt;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(blur, 0, 0, W, H);
    ctx.restore();

    // Vignette.
    const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, W * 0.72);
    v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.55)');
    ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);

    // Grain: one tile per frame, at an offset, as a soft overlay.
    const tile = tiles[Math.floor(T.hash(f, 21) * 8)];
    const ox = Math.floor(T.hash(f, 22) * TILE), oy = Math.floor(T.hash(f, 23) * TILE);
    ctx.save();
    ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = 0.07;
    ctx.translate(-ox, -oy);
    ctx.fillStyle = ctx.createPattern(tile, 'repeat'); ctx.fillRect(0, 0, W + TILE, H + TILE);
    ctx.restore();

    // In from black over the first 1.2 beats; out on the end curve.
    const g = Math.min(1, b / 1.2) * T.endGain(b);
    if (g < 1) { ctx.fillStyle = `rgba(0,0,0,${(1 - g).toFixed(4)})`; ctx.fillRect(0, 0, W, H); }
  }

  root.post = post;
})(this);
