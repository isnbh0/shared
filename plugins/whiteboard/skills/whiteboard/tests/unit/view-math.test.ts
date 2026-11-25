import fc from "fast-check";
import { describe, expect, it } from "vitest";
import {
  actualSize,
  clampZoom,
  fitTransform,
  followRect,
  FIT_PADDING,
  MAX_FIT_ZOOM,
  MAX_ZOOM,
  MIN_ZOOM,
  wheelPixels,
  wheelZoomFactor,
  zoomAt,
  type Transform,
} from "../../app/src/view-math.ts";

/** The diagram point under the pane point (px, py). */
const under = (t: Transform, px: number, py: number) => ({ x: (px - t.x) / t.k, y: (py - t.y) / t.k });

describe("view math", () => {
  it("keeps the point under the cursor fixed while zooming", () => {
    fc.assert(
      fc.property(
        fc.record({ x: fc.double({ min: -1e4, max: 1e4, noNaN: true }), y: fc.double({ min: -1e4, max: 1e4, noNaN: true }), k: fc.double({ min: MIN_ZOOM, max: MAX_ZOOM, noNaN: true }) }),
        fc.double({ min: 0.01, max: 20, noNaN: true }),
        fc.double({ min: 0, max: 2000, noNaN: true }),
        fc.double({ min: 0, max: 2000, noNaN: true }),
        (t, k, px, py) => {
          const next = zoomAt(t, k, px, py);
          expect(next.k).toBe(clampZoom(k));
          const before = under(t, px, py);
          const after = under(next, px, py);
          expect(after.x).toBeCloseTo(before.x, 6);
          expect(after.y).toBeCloseTo(before.y, 6);
        },
      ),
    );
  });

  it("clamps zoom, treating a non-finite zoom as 100 %", () => {
    expect(clampZoom(100)).toBe(MAX_ZOOM);
    expect(clampZoom(0)).toBe(MIN_ZOOM);
    expect(clampZoom(Number.NaN)).toBe(1);
  });

  it("fits content inside the padded pane, centered, never above the fit cap", () => {
    fc.assert(
      fc.property(
        fc.double({ min: 10, max: 5000, noNaN: true }),
        fc.double({ min: 10, max: 5000, noNaN: true }),
        fc.double({ min: 200, max: 3000, noNaN: true }),
        fc.double({ min: 200, max: 3000, noNaN: true }),
        (width, height, pw, ph) => {
          const t = fitTransform({ width, height }, { width: pw, height: ph });
          expect(t.k).toBeLessThanOrEqual(MAX_FIT_ZOOM);
          if (t.k > MIN_ZOOM) {
            expect(width * t.k).toBeLessThanOrEqual(pw - 2 * FIT_PADDING + 1e-6);
            expect(height * t.k).toBeLessThanOrEqual(ph - 2 * FIT_PADDING + 1e-6);
          }
          expect(t.x + (width * t.k) / 2).toBeCloseTo(pw / 2, 6);
          expect(t.y + (height * t.k) / 2).toBeCloseTo(ph / 2, 6);
        },
      ),
    );
    expect(fitTransform({ width: 100, height: 50 }, { width: 2000, height: 2000 }).k).toBe(MAX_FIT_ZOOM);
    expect(fitTransform({ width: 0, height: 0 }, { width: 500, height: 500 })).toEqual({ x: 0, y: 0, k: 1 });
  });

  it("goes to 100 % around the pane's center", () => {
    const t = actualSize({ x: -50, y: 20, k: 2.5 }, { width: 800, height: 600 });
    expect(t.k).toBe(1);
    expect(under(t, 400, 300).x).toBeCloseTo(under({ x: -50, y: 20, k: 2.5 }, 400, 300).x, 9);
  });

  it("converts wheel units and zooms in on a negative delta", () => {
    expect(wheelPixels(3, 1, 600)).toBe(48);
    expect(wheelPixels(1, 2, 600)).toBe(600);
    expect(wheelPixels(7, 0, 600)).toBe(7);
    expect(wheelZoomFactor(-100, false)).toBeGreaterThan(1);
    expect(wheelZoomFactor(100, false)).toBeLessThan(1);
    expect(wheelZoomFactor(-10, true)).toBeGreaterThan(wheelZoomFactor(-10, false));
    expect(wheelZoomFactor(-1e6, false)).toBe(wheelZoomFactor(-100, false));
  });

  it("pans minimally to bring a rect into view, keeping the zoom", () => {
    const num = (min: number, max: number) => fc.double({ min, max, noNaN: true });
    fc.assert(
      fc.property(
        fc.record({ x: num(-2000, 2000), y: num(-2000, 2000), k: num(MIN_ZOOM, MAX_ZOOM) }),
        fc.record({ x: num(-500, 500), y: num(-500, 500), width: num(0, 400), height: num(0, 400) }),
        fc.record({ width: num(100, 2000), height: num(100, 2000) }),
        (t, rect, pane) => {
          const next = followRect(t, rect, pane);
          expect(next.k).toBe(t.k);
          const left = rect.x * t.k + next.x;
          const top = rect.y * t.k + next.y;
          const room = { width: pane.width - 2 * FIT_PADDING, height: pane.height - 2 * FIT_PADDING };
          // Fits: inside the padded room. Too big: aligned to its start.
          if (rect.width * t.k <= room.width) {
            expect(left).toBeGreaterThanOrEqual(FIT_PADDING - 1e-6);
            expect(left + rect.width * t.k).toBeLessThanOrEqual(pane.width - FIT_PADDING + 1e-6);
          } else expect(left).toBeCloseTo(FIT_PADDING, 6);
          if (rect.height * t.k <= room.height) {
            expect(top).toBeGreaterThanOrEqual(FIT_PADDING - 1e-6);
            expect(top + rect.height * t.k).toBeLessThanOrEqual(pane.height - FIT_PADDING + 1e-6);
          } else expect(top).toBeCloseTo(FIT_PADDING, 6);
          // Already in view: nothing moves.
          const again = followRect(next, rect, pane);
          expect(again.x).toBeCloseTo(next.x, 6);
          expect(again.y).toBeCloseTo(next.y, 6);
        },
      ),
    );
  });

  it("keeps a followed rect clear of per-side insets", () => {
    const pane = { width: 400, height: 300 };
    const insets = { top: 80, right: 10, bottom: 60, left: 10 };
    // Below the bottom inset: pans up just enough.
    expect(followRect({ x: 0, y: 0, k: 1 }, { x: 50, y: 250, width: 20, height: 20 }, pane, insets).y).toBe(-30);
    // Under the top inset: pans down just enough.
    expect(followRect({ x: 0, y: 0, k: 1 }, { x: 50, y: 40, width: 20, height: 20 }, pane, insets).y).toBe(40);
  });
});
