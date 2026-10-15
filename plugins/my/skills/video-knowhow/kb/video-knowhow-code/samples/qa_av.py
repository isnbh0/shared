# /// script
# requires-python = ">=3.13"
# dependencies = ["numpy", "scipy"]
# ///
"""qa_av.py — two checks on a rendered file: the delivered audio against its loudness spec, and the picture's
hits against the score's event beats.

When you need it: before a file goes out (audio), and after any change to picture timing or the score (sync): a hit
two frames late reads as sloppy, and no single frame looks wrong.

Source: generalized from the source production's QA suite (audio loudness checks, seam and
signal tooling for hit sync).
Generalized: impacts are any key of a score-events.json (beats, or objects with "b"); thresholds are the source's.
Sync finds where each hit starts in the picture's own change signal (onset: the first frame pair at half the
window's peak change) and compares it with the event's beat; it does not cross-correlate audio and picture.
Left out: per-beat tables, spectrogram, band, stereo, hole and click checks, the seam classes around each impact.

uv run qa_av.py audio film.mp4 [--target-lufs -14] [--max-tp -1]
uv run qa_av.py sync film.mp4 --events score-events.json [--key kicks] [--bpm 120] [--offset 0]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from functools import partial

import numpy as np
from scipy.ndimage import gaussian_filter


def sh(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, check=True)


def ebur128(path: str) -> dict:
    err = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", path, "-map", "0:a:0", "-af",
                          "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    summ, num = err[err.rfind("Summary:"):], r"(-?(?:inf|[\d.]+))"

    def get(pat: str) -> float:
        m = re.search(pat, summ, re.S)
        return float(m.group(1)) if m else float("nan")

    return dict(I=get(r"Integrated loudness:.*?I:\s*" + num), LRA=get(r"Loudness range:.*?LRA:\s*" + num),
                TP=get(r"True peak:.*?Peak:\s*" + num))


def audio(a) -> list[str]:
    lo, flags = ebur128(a.file), []
    print(f"integrated {lo['I']:.1f} LUFS, LRA {lo['LRA']:.1f} LU, true peak {lo['TP']:.2f} dBTP "
          f"(spec {a.target_lufs:g} LUFS, <= {a.max_tp:g} dBTP)")
    if np.isfinite(lo["I"]) and abs(lo["I"] - a.target_lufs) > 1.0:
        flags.append(f"integrated {lo['I']:.1f} LUFS vs target {a.target_lufs:g}")
    if np.isfinite(lo["TP"]) and lo["TP"] > a.max_tp:
        flags.append(f"true peak {lo['TP']:.2f} dBTP > {a.max_tp:g}")
    raw = sh(["ffmpeg", "-v", "error", "-i", a.file, "-map", "0:a:0", "-ac", "2", "-f", "f32le", "-"]).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    for name, ch in (("L", x[:, 0]), ("R", x[:, 1])):
        ab = np.abs(ch)
        hot = ab >= 0.999
        over, runs, dc = int(np.sum(ab > 1.0)), int(np.sum(hot[1:] & hot[:-1])), float(ch.mean())
        if over or runs:
            flags.append(f"clipping {name}: {over} samples > 0 dBFS, {runs} consecutive full-scale pairs")
        if abs(dc) > 1e-3:
            flags.append(f"DC offset {name}: {dc:+.5f}")
    return flags


def decode_grey(path: str, width: int = 320) -> tuple[np.ndarray, float]:
    """All frames as (N, h, w) uint8 luma, area-downscaled, and the frame rate."""
    p = json.loads(sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                       "stream=width,height,r_frame_rate", "-of", "json", path]).stdout)["streams"][0]
    n, d = p["r_frame_rate"].split("/")
    height = int(round(width * p["height"] / p["width"] / 2) * 2)
    raw = sh(["ffmpeg", "-v", "error", "-i", path, "-map", "0:v:0", "-fps_mode", "passthrough", "-vf",
              f"scale={width}:{height}:flags=area,format=gray", "-f", "rawvideo", "-"]).stdout
    k = len(raw) // (width * height)
    return np.frombuffer(raw, np.uint8)[: k * width * height].reshape(k, height, width), int(n) / int(d)


def frame_pair_metrics(G: np.ndarray, chunk: int = 240) -> tuple[np.ndarray, np.ndarray]:
    """Pair i = frames i -> i+1: mean |delta luma| (0-255) and 1 - SSIM (Gaussian window, sigma 1.5)."""
    n = len(G)
    mad, dssim = np.zeros(max(n - 1, 0), np.float32), np.zeros(max(n - 1, 0), np.float32)
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    blur = partial(gaussian_filter, sigma=(0, 1.5, 1.5), truncate=3.5)
    for s in range(0, n - 1, chunk):
        e = min(n, s + chunk + 1)
        X = G[s:e].astype(np.float32)
        mad[s:e - 1] = np.abs(X[1:] - X[:-1]).mean(axis=(1, 2))
        mu = blur(X)
        sq = blur(X * X) - mu * mu
        a, b = slice(0, -1), slice(1, None)
        sab = blur(X[a] * X[b]) - mu[a] * mu[b]
        num = (2 * mu[a] * mu[b] + C1) * (2 * sab + C2)
        den = (mu[a] ** 2 + mu[b] ** 2 + C1) * (sq[a] + sq[b] + C2)
        dssim[s:e - 1] = 1.0 - (num / den).mean(axis=(1, 2))
    return mad, dssim


def sync(a) -> list[str]:
    ev = json.load(open(a.events))[a.key]
    hits = sorted(float(x["b"] if isinstance(x, dict) else x) for x in ev)
    G, fps = decode_grey(a.file)
    mad, ds = frame_pair_metrics(G)
    spb, N, flags = 60 / a.bpm, len(mad), []
    win = int(round(1.5 * spb * fps))  # the window each impact's thresholds come from: +-1.5 beats

    def pair_beat(j: int) -> float:  # the beat the second frame of pair j shows
        return a.offset + (j + 1) / fps / spb

    for ib in hits:
        fb = int(round((ib - a.offset) * spb * fps))
        i0, i1 = max(0, fb - win - 1), min(N, fb + win)
        if i1 - i0 < 4:
            continue
        thr_m = max(a.k * float(np.median(mad[i0:i1])), a.min_mad)
        thr_s = max(a.k * float(np.median(ds[i0:i1])), a.min_dssim)

        def score(j: int) -> float:
            return mad[j] / thr_m + ds[j] / thr_s

        # reach: half a beat, or half the gap to the next hit either side, so neighbors don't claim each other
        reach = min([0.5] + [abs(ib - o) / 2 for o in hits if abs(ib - o) > 1e-6])
        js = [j for j in range(i0, i1) if abs(pair_beat(j) - ib) <= reach]
        if not js or score(pk := max(js, key=score)) < 1.0:
            print(f"beat {ib:g}: no visual hit within {reach:g} beat")
            continue
        j = next(j for j in js if score(j) >= 0.5 * score(pk))  # onset: first pair at half the peak
        ms, peak_ms = (pair_beat(j) - ib) * spb * 1000, (pair_beat(pk) - ib) * spb * 1000
        off = min(abs(ms), abs(peak_ms)) > a.sync_ms and ms * peak_ms > 0  # onset and peak off, same side
        print(f"beat {ib:g}: onset {ms:+.0f} ms (frame {j + 1}), peak {peak_ms:+.0f} ms{'  OFF' if off else ''}")
        if off:
            flags.append(f"hit at beat {ib:g} is {'late' if ms > 0 else 'early'}: onset {ms:+.0f} ms, peak {peak_ms:+.0f} ms")
    return flags


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("audio")
    pa.add_argument("file")
    pa.add_argument("--target-lufs", type=float, default=-14.0)
    pa.add_argument("--max-tp", type=float, default=-1.0)
    ps = sub.add_parser("sync")
    ps.add_argument("file")
    ps.add_argument("--events", required=True, help="score-events.json")
    ps.add_argument("--key", default="kicks", help="event list to check (kicks)")
    for name, v, h in (("--bpm", 120.0, "tempo"), ("--offset", 0.0, "the beat at the file's first frame"),
                       ("--sync-ms", 50.0, "flag when onset and peak are both further off"),
                       ("--k", 4.0, "a change counts above k x the window's median"),
                       ("--min-mad", 2.0, "floor for the |delta luma| threshold, 0-255"),
                       ("--min-dssim", 0.03, "floor for the 1-SSIM threshold")):
        ps.add_argument(name, type=float, default=v, help=f"{h} ({v:g})")
    a = ap.parse_args()
    flags = audio(a) if a.cmd == "audio" else sync(a)
    for f in flags:
        print(f"FLAG {f}")
    sys.exit(1 if flags else 0)


if __name__ == "__main__":
    main()
