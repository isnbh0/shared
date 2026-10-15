// scene.js — the picture. scene(ctx, t) draws the whole 1920×1080 frame at time t, in seconds.
// The rules: draw from t alone (render.js asks for frames in any order), fill every pixel, take timing from T,
// look from TOKENS and randomness from T.rng. Replace this placeholder with your film.
(function (root) {
  const { W, H } = T;
  const C = TOKENS.color, S = TOKENS.safe, F = TOKENS.font;
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const outCubic = u => 1 - Math.pow(1 - clamp(u), 3);

  // Seeded once, when the page loads: the same dots in every run and every frame, above and below the text.
  const rand = T.rng(1);
  const DOTS = Array.from({ length: 24 }, () => ({
    x: S.x0 + rand() * (S.x1 - S.x0),
    y: rand() < 0.5 ? S.y0 + 60 + rand() * 220 : S.y1 - 120 - rand() * 220,
    r: 4 + rand() * 6,
  }));

  function scene(ctx, t) {
    const b = T.secToBeat(t);                  // beats since the start
    const beat = Math.floor(b), u = b - beat;  // the current beat, and how far through it (0 … 1)
    const inBar = beat % T.BEATS_PER_BAR;      // 0 on each bar's first beat
    const hit = Math.exp(-u * 5);              // 1 on the beat, fading before the next

    ctx.fillStyle = C.bg;
    ctx.fillRect(0, 0, W, H);

    // Dots: one lights on each beat.
    DOTS.forEach((d, i) => {
      const lit = i === beat % DOTS.length;
      ctx.fillStyle = lit ? C.fg : C.dim;
      ctx.beginPath(); ctx.arc(d.x, d.y, lit ? d.r * (1 + hit) : d.r, 0, Math.PI * 2); ctx.fill();
    });

    // A circle that swells on every beat, more on each bar's first beat.
    const swell = (inBar === 0 ? 70 : 35) * hit;
    ctx.fillStyle = C.accent;
    ctx.beginPath(); ctx.arc(S.x1 - 260, H / 2, 150 + swell, 0, Math.PI * 2); ctx.fill();

    // Four squares count the beats of the bar.
    for (let i = 0; i < T.BEATS_PER_BAR; i++) {
      ctx.fillStyle = i === inBar ? C.fg : C.dim;
      ctx.fillRect(S.x0 + i * 72, S.y1 - 48, 48, 48);
    }

    // A thin line along the top shows the way through the clip.
    ctx.fillStyle = C.dim;
    ctx.fillRect(S.x0, S.y0, S.x1 - S.x0, 4);
    ctx.fillStyle = C.fg;
    ctx.fillRect(S.x0, S.y0, (S.x1 - S.x0) * clamp(t / T.DURATION), 4);

    // The text line lands on its cue: it rises into place and fades in over half a beat.
    const p = outCubic((b - T.CUES.text) / 0.5);
    if (p > 0) {
      ctx.globalAlpha = p;
      ctx.fillStyle = C.fg;
      ctx.font = `${F.weight} ${F.size}px ${F.family}`;
      ctx.textBaseline = 'middle';
      ctx.fillText('Edit scene.js', S.x0, H / 2 + 40 * (1 - p));
      ctx.globalAlpha = 1;
    }
  }

  root.scene = scene;
})(this);
