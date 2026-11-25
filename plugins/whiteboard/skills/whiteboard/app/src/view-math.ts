// Pan and zoom arithmetic for the preview. A transform maps diagram coordinates to pane
// coordinates: pane = diagram * k + (x, y). Pure: no DOM types, so Node-side tests import it.

export type Transform = { x: number; y: number; k: number };
export type Size = { width: number; height: number };

export const MIN_ZOOM = 0.1;
export const MAX_ZOOM = 8;
/** Fit never enlarges a small diagram past this, so a two-node chart does not fill the screen. */
export const MAX_FIT_ZOOM = 2;
export const FIT_PADDING = 16;
/** One zoom button press or keyboard step. */
export const ZOOM_STEP = 1.25;

export function clampZoom(k: number): number {
  if (!Number.isFinite(k)) return 1;
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, k));
}

/** Zooms to `k` (clamped) keeping the pane point (px, py) over the same diagram point. */
export function zoomAt(t: Transform, k: number, px: number, py: number): Transform {
  const next = clampZoom(k);
  const ratio = next / t.k;
  return { k: next, x: px - (px - t.x) * ratio, y: py - (py - t.y) * ratio };
}

/** Centers `content` at zoom `k`. */
export function centered(content: Size, pane: Size, k: number): Transform {
  return { k, x: (pane.width - content.width * k) / 2, y: (pane.height - content.height * k) / 2 };
}

/** The largest zoom that shows all of `content` inside `pane` with padding, centered. */
export function fitTransform(content: Size, pane: Size): Transform {
  if (content.width <= 0 || content.height <= 0) return { x: 0, y: 0, k: 1 };
  const room = { width: Math.max(1, pane.width - 2 * FIT_PADDING), height: Math.max(1, pane.height - 2 * FIT_PADDING) };
  const k = clampZoom(Math.min(room.width / content.width, room.height / content.height, MAX_FIT_ZOOM));
  return centered(content, pane, k);
}

/** 100 % zoom, keeping the diagram point at the pane's center where it is. */
export function actualSize(t: Transform, pane: Size): Transform {
  return zoomAt(t, 1, pane.width / 2, pane.height / 2);
}

/** Wheel delta in pixels, whatever unit the browser reported (0 pixels, 1 lines, 2 pages). */
export function wheelPixels(delta: number, mode: number, pageSize: number): number {
  if (mode === 1) return delta * 16;
  if (mode === 2) return delta * pageSize;
  return delta;
}

/**
 * The zoom factor for a wheel step. Pinch gestures arrive as ctrl+wheel with small deltas, so they
 * get a stronger response than a mouse wheel's large notches.
 */
export function wheelZoomFactor(deltaY: number, pinch: boolean): number {
  const rate = pinch ? 0.01 : 0.002;
  return Math.exp(-Math.max(-100, Math.min(100, deltaY)) * rate);
}

export function zoomPercent(k: number): number {
  return Math.round(k * 100);
}

export type Rect = { x: number; y: number; width: number; height: number };
/** Pane space to keep clear on each side, in pane pixels. */
export type Insets = { top: number; right: number; bottom: number; left: number };

/**
 * Pans as little as possible so `rect` (diagram coordinates) sits inside the pane, clear of
 * `padding` (one value for every side, or per side), at the current zoom. A rect larger than the
 * room is aligned to the room's top-left corner.
 */
export function followRect(t: Transform, rect: Rect, pane: Size, padding: number | Insets = FIT_PADDING): Transform {
  const pad = typeof padding === "number" ? { top: padding, right: padding, bottom: padding, left: padding } : padding;
  const axis = (offset: number, start: number, length: number, min: number, max: number): number => {
    const lo = start * t.k + offset;
    const hi = lo + length * t.k;
    if (hi - lo > max - min || lo < min) return offset + (min - lo);
    if (hi > max) return offset + (max - hi);
    return offset;
  };
  return {
    k: t.k,
    x: axis(t.x, rect.x, rect.width, pad.left, pane.width - pad.right),
    y: axis(t.y, rect.y, rect.height, pad.top, pane.height - pad.bottom),
  };
}
