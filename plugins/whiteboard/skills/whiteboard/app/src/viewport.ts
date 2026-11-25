// Pan and zoom for the preview pane: wheel, pinch, drag, keys, and the toolbar's commands. The
// stage element carries a CSS transform; the pane clips it.
//
// A view is either following "fit" (refit on every render and resize, so live edits stay in view)
// or "manual" after the person zooms or pans (kept across renders, so edits do not reset it).
import {
  actualSize,
  fitTransform,
  followRect,
  wheelPixels,
  wheelZoomFactor,
  zoomAt,
  ZOOM_STEP,
  type Insets,
  type Rect,
  type Size,
  type Transform,
} from "./view-math.ts";

export type ViewState = { mode: "fit" | "manual"; t: Transform };

const DRAG_THRESHOLD_PX = 3;
const KEY_PAN_PX = 60;

export class Viewport {
  readonly #pane: HTMLElement;
  readonly #stage: HTMLElement;
  readonly #onChange: (state: ViewState) => void;
  #content: Size | undefined;
  #state: ViewState = { mode: "fit", t: { x: 0, y: 0, k: 1 } };
  #pending: ViewState | undefined;
  #drag: { id: number; x: number; y: number; moved: boolean; start: Transform } | undefined;
  #suppressClick = false;
  /** When true the wheel pans and ctrl/⌘+wheel (or a pinch) zooms; otherwise the wheel zooms. */
  scrollPans = false;
  /** Sees the pane's keys first; returning true claims the key (e.g. arrows during playback). */
  keyHandler: ((event: KeyboardEvent) => boolean) | undefined;

  constructor(pane: HTMLElement, stage: HTMLElement, onChange: (state: ViewState) => void) {
    this.#pane = pane;
    this.#stage = stage;
    this.#onChange = onChange;
    pane.addEventListener("wheel", (event) => this.#wheel(event), { passive: false });
    pane.addEventListener("pointerdown", (event) => this.#pointerDown(event));
    pane.addEventListener("pointermove", (event) => this.#pointerMove(event));
    pane.addEventListener("pointerup", (event) => this.#pointerUp(event));
    pane.addEventListener("pointercancel", (event) => this.#pointerUp(event));
    pane.addEventListener("click", (event) => this.#click(event), true);
    pane.addEventListener("keydown", (event) => this.#key(event));
    new ResizeObserver(() => {
      // Fit refits; a manual view keeps its transform but still reports, for pane-sized overlays.
      if (this.#state.mode === "fit" && this.#content) this.fit();
      else this.#apply();
    }).observe(pane);
  }

  get state(): ViewState {
    return { mode: this.#state.mode, t: { ...this.#state.t } };
  }

  /** The view the next `setContent` applies instead of the current one, e.g. a tab's saved view. */
  restoreNext(state: ViewState | undefined): void {
    this.#pending = state;
    if (!state) this.#state = { mode: "fit", t: this.#state.t };
  }

  /** Called with the diagram's size after each render. */
  setContent(size: Size): void {
    this.#content = size;
    const pending = this.#pending;
    this.#pending = undefined;
    if (pending?.mode === "manual") this.#set({ mode: "manual", t: pending.t });
    else if (pending || this.#state.mode === "fit") this.fit();
    else this.#apply();
  }

  clearContent(): void {
    this.#content = undefined;
  }

  fit(): void {
    if (!this.#content) return;
    this.#set({ mode: "fit", t: fitTransform(this.#content, this.#paneSize()) });
  }

  zoomIn(): void {
    this.#zoomCenter(this.#state.t.k * ZOOM_STEP);
  }

  zoomOut(): void {
    this.#zoomCenter(this.#state.t.k / ZOOM_STEP);
  }

  /** 100 %, keeping the diagram point at the pane's center in place. */
  actualSize(): void {
    this.#set({ mode: "manual", t: actualSize(this.#state.t, this.#paneSize()) });
  }

  /** Pans as little as possible to show `rect` (diagram coordinates), keeping the zoom. */
  follow(rect: Rect, padding?: number | Insets): void {
    if (!this.#content) return;
    this.#set({ mode: "manual", t: followRect(this.#state.t, rect, this.#paneSize(), padding) });
  }

  panBy(dx: number, dy: number): void {
    const { t } = this.#state;
    this.#set({ mode: "manual", t: { ...t, x: t.x + dx, y: t.y + dy } });
  }

  #zoomCenter(k: number): void {
    const pane = this.#paneSize();
    this.#set({ mode: "manual", t: zoomAt(this.#state.t, k, pane.width / 2, pane.height / 2) });
  }

  #paneSize(): Size {
    return { width: this.#pane.clientWidth, height: this.#pane.clientHeight };
  }

  #set(state: ViewState): void {
    this.#state = state;
    this.#apply();
  }

  #apply(): void {
    const { x, y, k } = this.#state.t;
    this.#stage.style.transform = `translate(${x}px, ${y}px) scale(${k})`;
    // For backgrounds that move with the view, such as the grid.
    this.#pane.style.setProperty("--view-x", `${x}px`);
    this.#pane.style.setProperty("--view-y", `${y}px`);
    this.#pane.style.setProperty("--view-k", String(k));
    this.#onChange(this.state);
  }

  #wheel(event: WheelEvent): void {
    if (!this.#content) return;
    event.preventDefault();
    const page = this.#pane.clientHeight;
    const dx = wheelPixels(event.deltaX, event.deltaMode, page);
    const dy = wheelPixels(event.deltaY, event.deltaMode, page);
    const zoomGesture = event.ctrlKey || event.metaKey;
    if (this.scrollPans && !zoomGesture) {
      this.panBy(event.shiftKey && dx === 0 ? -dy : -dx, event.shiftKey && dx === 0 ? 0 : -dy);
      return;
    }
    const rect = this.#pane.getBoundingClientRect();
    const k = this.#state.t.k * wheelZoomFactor(dy, event.ctrlKey);
    this.#set({ mode: "manual", t: zoomAt(this.#state.t, k, event.clientX - rect.left, event.clientY - rect.top) });
  }

  #pointerDown(event: PointerEvent): void {
    if (event.button !== 0 || !this.#content || this.#drag) return;
    if ((event.target as Element).closest?.("[data-wb-error]")) return;
    this.#drag = { id: event.pointerId, x: event.clientX, y: event.clientY, moved: false, start: this.#state.t };
  }

  #pointerMove(event: PointerEvent): void {
    const drag = this.#drag;
    if (!drag || drag.id !== event.pointerId) return;
    const dx = event.clientX - drag.x;
    const dy = event.clientY - drag.y;
    if (!drag.moved) {
      if (Math.hypot(dx, dy) < DRAG_THRESHOLD_PX) return;
      drag.moved = true;
      this.#pane.setPointerCapture(event.pointerId);
      this.#pane.classList.add("panning");
    }
    this.#set({ mode: "manual", t: { ...drag.start, x: drag.start.x + dx, y: drag.start.y + dy } });
  }

  #pointerUp(event: PointerEvent): void {
    const drag = this.#drag;
    if (!drag || drag.id !== event.pointerId) return;
    if (drag.moved) {
      this.#pane.releasePointerCapture(event.pointerId);
      this.#pane.classList.remove("panning");
      // Swallow the click that ends a drag, so a drag over a linked node does not follow it.
      this.#suppressClick = true;
      setTimeout(() => (this.#suppressClick = false), 0);
    }
    this.#drag = undefined;
  }

  #click(event: MouseEvent): void {
    if (!this.#suppressClick) return;
    event.preventDefault();
    event.stopPropagation();
    this.#suppressClick = false;
  }

  #key(event: KeyboardEvent): void {
    if (event.target !== this.#pane || event.altKey || event.ctrlKey || event.metaKey || !this.#content) return;
    if (this.keyHandler?.(event)) {
      event.preventDefault();
      return;
    }
    const actions: Record<string, () => void> = {
      "+": () => this.zoomIn(),
      "=": () => this.zoomIn(),
      "-": () => this.zoomOut(),
      "0": () => this.actualSize(),
      "!": () => this.fit(), // Shift+1 on US layouts
      ArrowLeft: () => this.panBy(KEY_PAN_PX, 0),
      ArrowRight: () => this.panBy(-KEY_PAN_PX, 0),
      ArrowUp: () => this.panBy(0, KEY_PAN_PX),
      ArrowDown: () => this.panBy(0, -KEY_PAN_PX),
    };
    const action = actions[event.key] ?? (event.shiftKey && event.code === "Digit1" ? actions["!"] : undefined);
    if (!action) return;
    event.preventDefault();
    action();
  }
}
