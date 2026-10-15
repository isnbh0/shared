// delivery-encode.js — join the lossless chunks into one H.264 High 4:2:0 delivery file, BT.709-tagged, with extra
// bits in fades to and from black and keyframes on whole-frame swaps, then mux it with the mastered AAC.
// When you need it: frames exist as lossless 4:4:4 chunks (chunk-render.js) and the file goes to a player or a
// platform that re-encodes it, so it needs a clean high-bitrate master whose color tags say what the pixels are.
// Source: generalized from the source production's renderer (delivery encode: x264 zones, mux,
// full pipeline, the chunk encode in its worker).
// Generalized: zones and forced keyframes are frame ranges and frame numbers passed in (the source derived them
// from its beat timeline); lead shifts both when frames are put in front (the source's warning card).
// Left out: splicing a separately encoded opener by stream copy (it needs the same SPS/PPS: the source checks
// them in paramSets); the delivered-audio gate after the mux (loudness-gate.js gate).
// node delivery-encode.js list.txt out.mp4 [audio.m4a] [seconds]
'use strict';
const { spawnSync } = require('child_process');

const FFMPEG = process.env.FFMPEG || 'ffmpeg';
const TAGS = ['-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv'];
// The same four tags on the frames themselves: ffmpeg 9.0.2 leaves primaries and transfer unset on filtered frames
// when only the output options name them (ffmpeg 6.0, which the source encoded with, sets all four from them).
const SET709 = 'setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv';

// The intermediate every chunk is encoded with: RGB -> BT.709 limited range once, lossless (qp 0), 4:4:4, so the
// only lossy step left is the delivery encode. About 5 GB a minute at 1080p60.
const INTERMEDIATE = ['-vf', 'scale=out_color_matrix=bt709:out_range=tv,' + SET709, '-c:v', 'libx264', '-preset', 'veryfast',
  '-qp', '0', '-pix_fmt', 'yuv444p', ...TAGS];

// x264 args for the delivery file.
//   zones [{ f0, f1, set }]: inclusive frame ranges with their own x264 settings. The source gives fades from and to
//     black 'b=1.5,deblock=1' and 'b=2,deblock=1': dark gradients band first, so they get more bits and deblocking.
//   keys [frame]: an I-frame on each, for whole-frame swaps (a hard cut to a new page) that would otherwise be coded
//     as a P-frame off the old picture. It changes frame types only, not the SPS/PPS.
//   crf 18, tune film, aq-mode 3 (bits toward dark flat areas), capped at 45 Mbit/s, High@4.2 for player support.
function x264Delivery({ first = 0, n = Infinity, lead = 0, zones = [], keys = [], crf = 18 } = {}) {
  const z = zones.map(({ f0, f1, set }) => [Math.max(first, f0), Math.min(first + n - 1, f1), set])
    .filter(([a, e]) => e >= a).map(([a, e, s]) => `${a - first + lead},${e - first + lead},${s}`);
  const k = keys.filter(f => f >= first && f < first + n).map(f => f - first + lead);
  return ['-c:v', 'libx264', '-preset', 'slow', '-crf', String(crf), '-tune', 'film',
    '-x264-params', ['aq-mode=3', ...(z.length ? ['zones=' + z.join('/')] : [])].join(':'),
    ...(k.length ? ['-force_key_frames', 'expr:' + k.map(f => `eq(n,${f})`).join('+')] : []),
    '-maxrate', '45M', '-bufsize', '45M', '-profile:v', 'high', '-level:v', '4.2', '-pix_fmt', 'yuv420p'];
}

// Zones from fade spans given in seconds: [{ s: [a, b], set }] -> frame ranges at fps.
const zonesFromSeconds = (spans, fps) => spans.map(({ s, set }) => ({ f0: Math.round(s[0] * fps), f1: Math.round(s[1] * fps) - 1, set }));

function ff(args, label) {
  const r = spawnSync(FFMPEG, ['-hide_banner', '-y', ...args], { encoding: 'utf8', maxBuffer: 1 << 26 });
  if (r.status !== 0) { console.error(r.stderr.slice(-3000)); throw new Error(`${label} failed`); }
  return r.stderr;
}

// Concat list (file '<chunk>' lines) -> delivery encode, muxed with the AAC by stream copy. The audio is mastered
// before this (loudness-gate.js master): re-encoding it here would move its peaks. -t trims to the film's length;
// +faststart puts the index first so a browser plays it before it has all of it.
function deliver({ list, out, audio = null, dur = null, x264 = x264Delivery() }) {
  ff(['-f', 'concat', '-safe', '0', '-i', list, ...(audio ? ['-i', audio] : []),
    '-map', '0:v:0', ...(audio ? ['-map', '1:a:0', '-c:a', 'copy'] : []),
    '-vf', 'format=yuv420p,' + SET709, ...x264, ...TAGS, ...(dur ? ['-t', String(dur)] : []), '-movflags', '+faststart', out], 'delivery encode');
}

// What a player will read: codec, profile, pixel format and the four color tags of the first video stream.
function probe(file) {
  const r = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries',
    'stream=codec_name,profile,pix_fmt,color_space,color_primaries,color_transfer,color_range', '-of', 'json', file], { encoding: 'utf8' });
  return JSON.parse(r.stdout).streams[0];
}

module.exports = { INTERMEDIATE, TAGS, x264Delivery, zonesFromSeconds, deliver, probe };

if (require.main === module) {
  const [list, out, audio, dur] = process.argv.slice(2);
  if (!list || !out) { console.error('node delivery-encode.js list.txt out.mp4 [audio.m4a] [seconds]'); process.exit(2); }
  try {
    deliver({ list, out, audio: audio || null, dur: dur ? +dur : null });
    console.log(JSON.stringify(probe(out)));
  } catch (e) { console.error(e.message); process.exit(1); }
}
