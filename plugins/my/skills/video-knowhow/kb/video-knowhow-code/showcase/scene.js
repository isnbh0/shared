// scene.js — the picture. scene(ctx, t, fps) draws one sub-frame at time t (seconds); post.js finishes each frame.
// Timing comes from T (the clock, its sections and the gap) and EV (score-events.json: the beats the score actually
// plays); no event beat is typed here. Look comes from TOKENS, randomness from T.hash. Nothing reads the previous
// frame, so frames can be drawn in any order.
//   intro   "video made with code" one word on each of the hook's first four notes
//   build   two shelves draw in on the first kicks; their items drop onto them on the score's landing notes; the
//           shelves converge under the riser into one line, and the snare roll writes ticks onto it; the gap cuts
//           to black
//   drop    the title on that line, the line pulsing with the kick and lit by each stab; the subtitle on two stabs;
//           three kinds of page on the next chord's stabs
//   resolve the title steps back; "read the pages" on a pluck note, "run the code" on the next chord; the end
//           curve takes it to black
(function (root) {
  const { W, H } = T;
  const C = TOKENS.color, S = TOKENS.safe, F = TOKENS.font, col = TOKENS.col;
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, u) => a + (b - a) * u;
  const outCubic = u => 1 - Math.pow(1 - clamp(u), 3);
  const inOutCubic = u => (u = clamp(u), u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
  const smooth = u => u * u * (3 - 2 * u);
  const vnoise = (x, seed) => {
    const i = Math.floor(x), f = x - i;
    return lerp(T.hash(i, seed), T.hash(i + 1, seed), smooth(f)) * 2 - 1;
  };
  // The last event at or before beat b (a list of beats, or of { b } objects, sorted).
  const lastEvent = (list, b) => {
    let r = null;
    for (const x of list) { if ((typeof x === 'number' ? x : x.b) <= b) r = x; else break; }
    return r;
  };
  const lastAt = (list, b) => {
    const e = lastEvent(list, b);
    return e === null ? -Infinity : typeof e === 'number' ? e : e.b;
  };
  // 1 at an event, decaying with time constant tau seconds.
  const hitDecay = (list, b, tau) => {
    const e = lastAt(list, b);
    return e === -Infinity ? 0 : Math.exp(-(b - e) * T.SPB / tau);
  };
  const section = id => T.SECTIONS.find(s => s.id === id);

  const TITLE = 'video-knowhow';
  const CLOSING = [['read the pages', C.paper], ['run the code', C.code]];
  // The craft shelf climbs from a single control to the whole piece, as the craft shelf's pages do.
  const SHELVES = {
    code: { label: 'code', color: C.code, y: 440, items: ['render', 'score', 'sync', 'master'] },
    craft: { label: 'craft', color: C.craft, y: 720, items: ['motion', 'scene', 'sequence', 'direction'] },
  };
  const L = {};            // layout measured once the fonts are loaded (layout(), called by window.ready)
  const E = {};            // event beats, read from EV in layout()
  const RULER = { x0: S.x0, x1: S.x1, y: S.y1 - 34 };
  const bx = b => lerp(RULER.x0, RULER.x1, b / T.BEATS);
  const LABEL_FONT = `400 16px ${F.mono}`;

  function layout(ctx) {
    ctx.save();
    ctx.font = `700 200px ${F.display}`; ctx.letterSpacing = '-6px';
    L.titleW = ctx.measureText(TITLE).width;
    ctx.font = `500 60px ${F.display}`; ctx.letterSpacing = '-1px';
    L.closeW = CLOSING.map(([s]) => ctx.measureText(s).width);
    ctx.font = LABEL_FONT; ctx.letterSpacing = '1.5px';
    L.labelW = T.SECTIONS.map(s => ctx.measureText(s.id).width);
    // Each shelf's items: from col(3) to the safe area's right edge (12 px held back for the glyphs' overhang),
    // spaced by their measured widths with equal gaps between them.
    ctx.font = `500 64px ${F.display}`; ctx.letterSpacing = '-1px';
    L.itemX = {};
    for (const [key, sh] of Object.entries(SHELVES)) {
      const iw = sh.items.map(w => ctx.measureText(w).width);
      const igap = (col(12) - 12 - col(3) - iw.reduce((a, w) => a + w, 0)) / (iw.length - 1);
      L.itemX[key] = iw.map((w, i) => col(3) + iw.slice(0, i).reduce((a, v) => a + v + igap, 0));
    }
    ctx.restore();
    L.lineY = 580;                                     // the merged line under the title
    L.lineX0 = W / 2 - L.titleW / 2; L.lineX1 = W / 2 + L.titleW / 2;

    // Every picture event, from the score's events or the clock's sections.
    const resolve = section('resolve').b0;
    const dropChords = EV.chords.filter(c => c.b0 >= T.DROP && c.b0 < resolve);
    const stabsOf = c => EV.stabs.filter(s => s >= c.b0 && s < c.b1);
    const resolvePluck = EV.hook.filter(h => h.b >= resolve && h.src === 'pluck');
    Object.assign(E, {
      build: section('build').b0,
      resolve,
      riser: EV.riser,
      lastLand: EV.lands[EV.lands.length - 1].b,
      subtitle: [stabsOf(dropChords[0]).slice(-1)[0], stabsOf(dropChords[1])[0]],   // the drop's 3rd and 4th stabs
      kinds: stabsOf(dropChords[2]),                                                // the third chord's three stabs
      closing: [resolvePluck[2].b, EV.chords.filter(c => c.b0 >= resolve)[1].b0],  // a pluck note, the next chord
      dropStabs: EV.stabs.filter(s => s >= T.DROP && s < resolve),
      buildKicks: EV.kicks.filter(k => k < T.GAP.b0),
      buildClaps: EV.claps.filter(k => k < T.GAP.b0),
      snares: EV.snares,
    });
  }

  function text(ctx, s, x, y, { font, color = C.paper, align = 'left', track = 0, alpha = 1 }) {
    if (alpha <= 0) return;
    ctx.globalAlpha = alpha; ctx.font = font; ctx.fillStyle = color; ctx.textAlign = align;
    ctx.letterSpacing = `${track}px`; ctx.fillText(s, x, y);
    ctx.globalAlpha = 1; ctx.letterSpacing = '0px';
  }

  function background(ctx, b) {
    const g = ctx.createRadialGradient(W / 2, H * 0.46, 80, W / 2, H * 0.5, W * 0.62);
    g.addColorStop(0, C.inkLift); g.addColorStop(1, C.ink);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // A dot grid on the 12 columns, faint: the page's paper. In the build it lights on each kick, more on each
    // clap, and on each hit of the snare roll by the hit's strength, so the build's peak shows in the paper too.
    const dots = () => {
      for (let i = 0; i <= 12; i++) {
        for (let y = S.y0 + 96; y <= S.y1 - 96; y += 96) ctx.fillRect(col(i) - 1.5, y - 1.5, 3, 3);
      }
    };
    ctx.fillStyle = C.faint; ctx.globalAlpha = 0.55; dots();
    if (b >= E.build && b < T.GAP.b0) {
      const sn = lastEvent(E.snares, b);
      const snare = sn ? sn.v * Math.exp(-(b - sn.b) * T.SPB / 0.1) : 0;
      const pulse = 0.35 * hitDecay(E.buildKicks, b, 0.12) + 0.5 * hitDecay(E.buildClaps, b, 0.18) + 0.45 * snare;
      ctx.fillStyle = C.dim; ctx.globalAlpha = Math.min(0.9, pulse); dots();
    }
    ctx.globalAlpha = 1;
    // Through the drop, each kick sends a ring out from the title's line, lighting the dots it passes.
    const lastKick = EV.kicks[EV.kicks.length - 1];
    if (b >= T.DROP && b < lastKick + 0.5) {
      const k = lastAt(EV.kicks, b), u = (b - k) * T.SPB, R = 2600 * u, fade = Math.exp(-u / 0.3);
      ctx.fillStyle = C.paper;
      for (let i = 0; i <= 12; i++) for (let y = S.y0 + 96; y <= S.y1 - 96; y += 96) {
        const d = Math.hypot(col(i) - W / 2, y - L.lineY), a = 0.6 * fade * Math.exp(-Math.pow((d - R) / 110, 2));
        if (a < 0.01) continue;
        ctx.globalAlpha = a; ctx.fillRect(col(i) - 2.5, y - 2.5, 5, 5);
      }
      ctx.globalAlpha = 1;
    }
  }

  // The score strip along the bottom: every beat of the piece, the kicks under the line, the hook's notes above it
  // by pitch, the landings in their shelf's color. What is still to come stays faint; what has played is lit.
  function ruler(ctx, b) {
    const reveal = outCubic((b - 0.5) / 2);
    if (reveal <= 0) return;
    const { x0, x1, y } = RULER, xe = lerp(x0, x1, reveal);
    ctx.save();
    ctx.beginPath(); ctx.rect(0, 0, xe, H); ctx.clip();
    ctx.fillStyle = C.faint; ctx.fillRect(x0, y, x1 - x0, 2);
    for (let k = 0; k <= T.BEATS; k++) {
      const bar = k % 4 === 0;
      ctx.fillStyle = k <= b ? C.dim : C.faint;
      ctx.fillRect(bx(k) - 1, y - (bar ? 12 : 6), 2, bar ? 12 : 6);
    }
    T.SECTIONS.forEach(s => text(ctx, s.id, bx(s.b0) + 6, y - 22,
      { font: LABEL_FONT, color: b >= s.b0 ? C.dim : C.faint, track: 1.5 }));
    const lit = (e, tau) => (e <= b ? 0.55 + 0.45 * Math.exp(-(b - e) * T.SPB / tau) : 0.22);
    for (const k of EV.kicks) {
      ctx.globalAlpha = lit(k, 0.15); ctx.fillStyle = C.paper; ctx.fillRect(bx(k) - 3, y + 6, 6, 6);
    }
    for (const h of EV.hook) {
      ctx.globalAlpha = lit(h.b, 0.2); ctx.fillStyle = C.paper;
      ctx.beginPath(); ctx.arc(bx(h.b), y - 30 - (h.m - 66) * 2.6, 2.6, 0, Math.PI * 2); ctx.fill();
    }
    for (const l of EV.lands) {
      ctx.globalAlpha = lit(l.b, 0.3); ctx.fillStyle = SHELVES[l.shelf].color;
      ctx.beginPath(); ctx.arc(bx(l.b), y + 22, 4, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
    // The playhead. It passes under a section label: no stroke across the label's band.
    const px = bx(Math.min(b, T.BEATS));
    const onLabel = T.SECTIONS.some((s, i) => px > bx(s.b0) + 2 && px < bx(s.b0) + 10 + L.labelW[i]);
    ctx.fillStyle = C.paper;
    if (onLabel) { ctx.fillRect(px - 1, y - 74, 2, 34); ctx.fillRect(px - 1, y - 16, 2, 46); }
    else ctx.fillRect(px - 1, y - 74, 2, 104);
    ctx.restore();
  }

  // The corner labels. The frame counter shows through intro and build; under the title only the section and beat
  // stay, dimmed, so nothing ticks beside the title.
  function hud(ctx, b, t, fps) {
    if (!TOKENS.hud) return;
    const a = outCubic((b - 0.5) / 2) * 0.9 * (b >= T.DROP ? 0.55 : 1);
    const f = Math.floor(t * fps + 1e-6);
    const right = `${T.sectionAt(b).id}   beat ${String(Math.floor(b)).padStart(2, '0')}`
      + (b < T.DROP ? `   frame ${String(f).padStart(3, '0')}` : '');
    text(ctx, 'video-knowhow   showcase', S.x0, S.y0 + 16,
      { font: `400 18px ${F.mono}`, color: C.dim, track: 1, alpha: a });
    text(ctx, right, S.x1, S.y0 + 16, { font: `400 18px ${F.mono}`, color: C.dim, align: 'right', track: 1, alpha: a });
  }

  // Intro: four words, each rising on one of the hook's first four notes; they leave as the build begins.
  function intro(ctx, b) {
    if (b > E.build + 0.2) return;
    const words = ['video', 'made', 'with', 'code'], notes = EV.hook.slice(0, 4).map(h => h.b);
    ctx.font = `500 120px ${F.display}`; ctx.letterSpacing = '-2px';
    const sp = 34, ws = words.map(w => ctx.measureText(w).width), total = ws.reduce((a, w) => a + w, 0) + sp * 3;
    ctx.letterSpacing = '0px';
    const out = inOutCubic((b - (E.build - 0.75)) / 0.75);
    let x = W / 2 - total / 2;
    words.forEach((w, i) => {
      const p = outCubic((b - notes[i] + 0.12) / 0.5);   // starts just before its note, settles a quarter second after
      const y = 520 + 34 * (1 - p) - 60 * out;
      text(ctx, w, x, y,
        { font: `500 120px ${F.display}`, color: i === 3 ? C.code : C.paper, track: -2, alpha: p * (1 - out) });
      x += ws[i] + sp;
    });
  }

  // Build: two shelves; items land on the score's landing notes; the shelves converge on the line the title will
  // stand on, and the snare roll marks it.
  function build(ctx, b) {
    if (b < E.build || b >= T.GAP.b0) return;
    const r0 = E.riser.b0, r1 = E.riser.b1;
    const conv = Math.pow(clamp((b - r0) / (r1 - r0)), 2);              // the riser's curve: slow, then fast
    const push = 1 + 0.04 * inOutCubic((b - r0) / (r1 - r0));
    const fade0 = E.lastLand + 2, fade1 = T.GAP.b0 - 2.25;              // the full set holds a second, then goes
    const itemFade = 1 - inOutCubic((b - fade0) / (fade1 - fade0));
    // The snare roll: each hit a tick on the line, taller and brighter as the roll climbs; the line glows with it.
    let roll = 0;
    for (const sn of EV.snares) {
      const u = (b - sn.b) * T.SPB;
      if (u >= 0 && u < 0.5) roll += (0.3 + 0.7 * sn.v) * Math.exp(-u / 0.08);
    }
    roll = Math.min(1, roll);
    ctx.save();
    ctx.translate(W / 2, L.lineY); ctx.scale(push, push); ctx.translate(-W / 2, -L.lineY);
    Object.entries(SHELVES).forEach(([key, sh], si) => {
      const draw = outCubic((b - E.buildKicks[si]) / 1.2);              // shoots out on the build's first two kicks
      if (draw <= 0) return;
      const y = lerp(sh.y, L.lineY, conv);
      const x0 = si === 0 ? lerp(col(0), L.lineX0, conv) : lerp(col(0), W / 2, conv);
      const x1f = si === 0 ? lerp(col(12), W / 2, conv) : lerp(col(12), L.lineX1, conv);
      const x1 = lerp(x0, x1f, draw);
      const lands = EV.lands.filter(l => l.shelf === key);
      const itemX = i => L.itemX[key][i];
      // The shelf dips where an item lands, a damped spring at that x.
      const dip = x => {
        let d = 0;
        for (const l of lands) {
          const u = (b - l.b) * T.SPB;
          if (u < 0 || u > 1.2) continue;
          d += 9 * Math.exp(-u / 0.14) * Math.cos(u * 2 * Math.PI * 3.2)
            * Math.exp(-Math.pow((x - itemX(l.i)) / 150, 2));
        }
        return d * (1 - conv);
      };
      const path = () => {
        ctx.beginPath();
        for (let k = 0; k <= 96; k++) {
          const x = lerp(x0, x1, k / 96);
          if (k) ctx.lineTo(x, y + dip(x)); else ctx.moveTo(x, y + dip(x));
        }
      };
      ctx.strokeStyle = sh.color; ctx.lineCap = 'butt';
      if (roll > 0.01) {                                              // the roll's glow around the line
        ctx.globalAlpha = 0.5 * roll; ctx.lineWidth = lerp(3, 6, conv) + 10 * roll; path(); ctx.stroke();
        ctx.globalAlpha = 1;
      }
      ctx.lineWidth = lerp(3, 6, conv); path(); ctx.stroke();
      EV.snares.forEach((sn, k) => {
        if (k % 2 !== si) return;
        const u = (b - sn.b) * T.SPB;
        if (u < 0 || u > 0.4) return;
        const a = Math.exp(-u / 0.1) * (0.35 + 0.65 * sn.v), h = 10 + 30 * sn.v;
        const x = lerp(x0, x1, 0.08 + 0.84 * T.hash(k, 31));
        ctx.globalAlpha = a; ctx.fillStyle = sh.color; ctx.fillRect(x - 1.5, y - h / 2, 3, h); ctx.globalAlpha = 1;
      });
      if (TOKENS.shelfLabel === 'row') {
        text(ctx, sh.label, col(0), y + dip(col(0)) - 20,
          { font: `700 64px ${F.display}`, color: sh.color, track: -1, alpha: draw * itemFade });
      } else {
        text(ctx, sh.label, col(0), sh.y - 22,
          { font: `700 22px ${F.mono}`, color: sh.color, track: 5, alpha: draw * itemFade });
        text(ctx, `${lands.filter(l => l.b <= b).length} of 4`, col(12), sh.y + 38,
          { font: `400 20px ${F.mono}`, color: C.dim, align: 'right', track: 2, alpha: draw * itemFade });
      }
      lands.forEach(l => {
        const fall = clamp((b - (l.b - 0.45)) / 0.45);        // a quarter second of falling, landing on the note
        if (fall <= 0) return;
        const x = itemX(l.i), lift = 120 * Math.pow(1 - fall, 2);
        const u = Math.max(0, (b - l.b) * T.SPB);
        const settle = fall < 1 ? 0 : -7 * Math.exp(-u / 0.09) * Math.abs(Math.sin(u * Math.PI * 6));
        text(ctx, sh.items[l.i], x, y + dip(x) - 20 - lift + settle,
          { font: `500 64px ${F.display}`, color: C.paper, track: -1, alpha: clamp(fall * 2) * itemFade });
      });
    });
    ctx.restore();
  }

  // Drop and resolve: the title on the merged line.
  function title(ctx, b) {
    if (b < T.DROP) return;
    const u = (b - T.DROP) * T.SPB;
    const kick = hitDecay(EV.kicks, b, 0.09);
    const back = inOutCubic((b - E.resolve) / 2.2);                    // resolve: the title steps back and up
    const shake = 5 * Math.exp(-u / 0.12);
    const sx = shake * vnoise(u * 38, 11), sy = shake * vnoise(u * 38, 12);
    const enter = outCubic(u / 0.35);
    const drift = 1 + 0.015 * clamp((b - T.DROP) / (E.resolve - T.DROP));   // a slow push-in across the drop
    const scale = lerp(lerp(1.03, 1, enter) * drift * (1 + 0.006 * kick * (1 - back)), 0.6, back);
    const cy = lerp(L.lineY, 420, back);
    ctx.save();
    ctx.translate(W / 2 + sx, cy + sy); ctx.scale(scale, scale);
    text(ctx, TITLE, 0, -52, { font: `700 200px ${F.display}`, color: C.paper, align: 'center', track: -6 });
    const half = L.titleW / 2, th = 6 + 6 * kick * (1 - back);
    ctx.fillStyle = C.code; ctx.fillRect(-half, -th / 2, half, th);
    ctx.fillStyle = C.craft; ctx.fillRect(0, -th / 2, half, th);
    // Each stab sends a light outward from the seam along both halves of the underline.
    const s = lastAt(E.dropStabs, b), su = (b - s) * T.SPB;
    if (su >= 0 && su < 0.4) {
      const p = outCubic(su / 0.4), x = half * p, a = 0.75 * (1 - p);
      ctx.globalAlpha = a; ctx.fillStyle = C.paper;
      ctx.fillRect(x - 60, -th / 2, 120, th); ctx.fillRect(-x - 60, -th / 2, 120, th);
      ctx.globalAlpha = 1;
    }
    ctx.restore();

    // The subtitle on the drop's third and fourth stabs: what the package is, bright; what it is for, dim. Then
    // three kinds of page on the next chord's stabs, a level below.
    const fadeOut = 1 - inOutCubic((b - E.resolve) / 1);
    [['a code shelf and a craft shelf', C.paper], ['for making video with code', C.dim]].forEach(([s, color], i) => {
      const p = outCubic((b - E.subtitle[i]) / 0.9);
      text(ctx, s, W / 2, 682 + i * 56 + 18 * (1 - p),
        { font: `400 44px ${F.display}`, color, align: 'center', track: -0.5, alpha: p * fadeOut });
    });
    const kinds = ['technique pages', 'case records', 'runnable code'];   // set apart by space alone
    ctx.font = `400 26px ${F.mono}`; ctx.letterSpacing = '2px';
    const kw = kinds.map(k => ctx.measureText(k).width), gap = 96, tw = kw.reduce((a, w) => a + w, 0) + gap * 2;
    ctx.letterSpacing = '0px';
    let x = W / 2 - tw / 2;
    kinds.forEach((k, i) => {
      const p = outCubic((b - E.kinds[i]) / 0.3);
      if (p > 0) {
        ctx.save(); ctx.beginPath(); ctx.rect(x - 4, 750, (kw[i] + 8) * p, 50); ctx.clip();
        text(ctx, k, x, 786, { font: `400 26px ${F.mono}`, color: C.dim, track: 2, alpha: fadeOut });
        ctx.restore();
      }
      x += kw[i] + gap;
    });

    // Resolve: the closing line, its halves placed from their measured widths, one on a pluck note, one on the
    // next chord.
    const cgap = 48, cw = L.closeW[0] + cgap + L.closeW[1];
    let cx = W / 2 - cw / 2;
    CLOSING.forEach(([s, color], i) => {
      const p = outCubic((b - E.closing[i]) / 1.0);
      text(ctx, s, cx, 640 + 14 * (1 - p), { font: `500 60px ${F.display}`, color, track: -1, alpha: p });
      cx += L.closeW[i] + cgap;
    });
  }

  function scene(ctx, t, fps = T.FPS) {
    const b = T.secToBeat(t);
    background(ctx, b);
    ruler(ctx, b);
    hud(ctx, b, t, fps);
    intro(ctx, b);
    build(ctx, b);
    title(ctx, b);
  }

  root.scene = scene;
  root.sceneLayout = layout;
  root.sceneHit = hitDecay;
})(this);
