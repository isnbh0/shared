// seeded-streams.js — deterministic randomness for picture and sound: one seeded generator per concern, per-event
// seeds keyed by where the event sits, and a stateless hash for "random" values that are pure functions of an index.
// When you need it: every frame and every sample must be a pure function of time (parallel workers, resumed chunks,
// byte-identical re-renders), and an edit to one part must not reshuffle the randomness of every other part.
// Source: generalized from the source production's beat clock (seeded stream), score (named
// streams and per-event seeds), and engine (stateless hash and value noise).
// Generalized: the seed numbers are examples; streams() builds a named set. Runs in Node and in the page (window.RNG).
(function (root) {
  // mulberry32: uniform in [0, 1). Small, fast, and a pure function of its seed and the number of draws.
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

  // Separate seeded streams, so editing one part does not reshuffle the others: a layer that draws one more value
  // shifts only its own stream. A part added later takes a stream of its own ("the rest re-roll nothing").
  //   const R = streams({ noise: 101, hum: 202, phase: 303 });  R.noise()
  const streams = seeds => Object.fromEntries(Object.entries(seeds).map(([k, s]) => [k, rng(s)]));

  // A stream per event, seeded by where the event sits (its beat to 1/1000 and its index on that beat), so moving,
  // adding or dropping one event changes no other event's draws. base keeps these clear of the named streams.
  const eventRng = (beat, i = 0, base = 9000) => rng(base + Math.round(beat * 1000) + i);

  // Stateless: the same (i, seed) gives the same value in any order, any worker, any frame. i is spread by a
  // Knuth multiplicative constant; each fresh generator's first draw is thrown away and the second returned.
  const hash = (i, seed = 0) => { const r = rng((i * 2654435761 + seed * 97 + 1) >>> 0); r(); return r(); };
  const smooth = u => u * u * (3 - 2 * u);
  // Smooth value noise in [-1, 1]: hash at the integers, eased between them. For drift, wobble, flicker by time.
  const noise = (x, seed = 0) => {
    const i = Math.floor(x), f = x - i;
    return (hash(i, seed) + (hash(i + 1, seed) - hash(i, seed)) * smooth(f)) * 2 - 1;
  };

  const RNG = { rng, streams, eventRng, hash, noise };
  if (typeof module !== 'undefined' && module.exports) module.exports = RNG;
  else root.RNG = RNG;
})(this);
