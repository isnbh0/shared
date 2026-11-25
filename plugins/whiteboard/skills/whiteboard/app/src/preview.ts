// Renders one view (text or "missing") into the preview host and maintains the readiness
// contract: data-wb-state is rendering, rendered (one frame after the SVG is inserted), or error,
// with [data-wb-error] holding the message. The host is a pan-and-zoom pane (see viewport.ts);
// flowcharts can highlight a hovered node's relationships, and sequence diagrams can be stepped
// through one message at a time (the view following the current message) and can keep their
// participants frozen at the pane's edges (see sequence-view.ts).
import mermaiden, { renderWithSemantics } from "mermaiden";
import { attachRelationshipHighlight, type RelationshipHighlightHandle } from "mermaiden-toolkit";

import { SequenceView, type PlaybackPosition, type PlaybackStep } from "./sequence-view.ts";

import type { View } from "./sync.ts";
import { Viewport, type ViewState } from "./viewport.ts";

export type { PlaybackPosition, PlaybackStep, View, ViewState };

export type PreviewHooks = {
  /** The pan and zoom changed. */
  view(state: ViewState): void;
  /** The rendered diagram's kind, or null when nothing is rendered. */
  kind(kind: string | null): void;
  /** Where playback is, or null when it is not running. */
  playback(position: PlaybackPosition | null): void;
  /** Why frozen participants are hidden right now (e.g. too large at this zoom), or null. */
  freezeNote(reason: string | null): void;
};

export function sameView(a: View | undefined, b: View | undefined): boolean {
  if (!a || !b) return a === b;
  if (a.kind === "missing" || b.kind === "missing") return a.kind === b.kind;
  return a.text === b.text;
}

/**
 * The most specific message in an error's cause chain. Mermaiden wraps Mermaid's parse error
 * ("Parse error on line 2: …") in a generic "transaction failed" error.
 */
export function renderErrorMessage(error: unknown): string {
  let message = "";
  let current: unknown = error;
  for (let depth = 0; current !== undefined && current !== null && depth < 8; depth++) {
    if (current instanceof Error) {
      if (current.message) message = current.message;
      current = current.cause;
    } else {
      if (typeof current === "string" && current) message = current;
      else if (typeof current === "object" && typeof (current as { message?: unknown }).message === "string") {
        message = (current as { message: string }).message || message;
      }
      break;
    }
  }
  return message;
}

let initialized = false;

export class Preview {
  readonly #host: HTMLElement;
  readonly #canvas: HTMLElement;
  readonly #error: HTMLElement;
  readonly #hooks: PreviewHooks;
  readonly viewport: Viewport;
  #seq = 0;
  #highlight: RelationshipHighlightHandle | undefined;
  #highlightOn = true;
  #semantics: Awaited<ReturnType<typeof renderWithSemantics>>["semantics"] | undefined;
  #shown: View | undefined;
  #playbackOn = false;
  #freezeOn = true;
  #sequence: SequenceView | undefined;
  /** Kept across re-renders of the same document, so a live edit does not restart playback. */
  #playbackIndex = 0;
  readonly #viewListeners = new Set<() => void>();

  constructor(host: HTMLElement, hooks: PreviewHooks) {
    if (!initialized) {
      // Without suppressErrorRendering, Mermaid leaves an error SVG in <body> for every failed render.
      mermaiden.initialize({ startOnLoad: false, suppressErrorRendering: true });
      initialized = true;
    }
    this.#host = host;
    this.#hooks = hooks;
    this.#canvas = document.createElement("div");
    this.#canvas.className = "preview-canvas";
    this.#error = document.createElement("p");
    this.#error.className = "preview-error";
    this.#error.setAttribute("data-wb-error", "");
    this.#error.setAttribute("role", "status");
    host.replaceChildren(this.#error, this.#canvas);
    host.tabIndex = 0;
    this.viewport = new Viewport(host, this.#canvas, (state) => {
      hooks.view(state);
      for (const listener of this.#viewListeners) listener();
    });
    this.viewport.keyHandler = (event) => {
      const steps: Record<string, PlaybackStep> = {
        ArrowLeft: "previous",
        ArrowRight: "next",
        Home: "first",
        End: "overview",
      };
      const step = steps[event.key];
      if (!this.#sequence?.playing || !step || event.shiftKey) return false;
      this.step(step);
      return true;
    };
  }

  /** The view most recently requested. */
  get shown(): View | undefined {
    return this.#shown;
  }

  /** Turns relationship highlighting on hover on or off; it applies to flowcharts only. */
  setHighlight(on: boolean): void {
    this.#highlightOn = on;
    this.#attachHighlight();
  }

  /** Turns sequence playback on (from the first message) or off; it applies to sequence diagrams. */
  setPlayback(on: boolean): void {
    this.#playbackOn = on;
    this.#playbackIndex = 0;
    this.#attachSequence();
    if (this.#sequence?.playing) {
      this.viewport.fit();
      this.#follow();
    }
  }

  /** Turns frozen participant rows on or off; it applies to sequence diagrams. */
  setFreeze(on: boolean): void {
    this.#freezeOn = on;
    this.#attachSequence();
  }

  step(step: PlaybackStep): void {
    if (!this.#sequence?.playing) return;
    this.#sequence.step(step);
    this.#follow();
  }

  /**
   * Empties the preview and drops the readiness state (no document to show). The next render
   * shows `view` if given, otherwise it fits the diagram.
   */
  clear(view?: ViewState): void {
    this.#seq++;
    this.viewport.restoreNext(view);
    this.#playbackIndex = 0;
    this.#shown = undefined;
    this.#dropSvg();
    this.#error.textContent = "";
    this.#host.classList.remove("stale");
    this.#host.removeAttribute("data-wb-state");
  }

  async render(view: View): Promise<void> {
    const seq = ++this.#seq;
    this.#shown = view;
    if (view.kind === "missing") {
      this.#dropSvg();
      this.#fail("This file is missing on disk.");
      return;
    }
    if (view.text.trim() === "") {
      this.#fail("This file is empty.");
      return;
    }
    this.#host.setAttribute("data-wb-state", "rendering");
    try {
      const result = await renderWithSemantics({ id: `wb-render-${seq}`, source: view.text });
      if (seq !== this.#seq) return;
      this.#dropSvg();
      this.#canvas.innerHTML = result.svg;
      result.bindFunctions?.(this.#canvas);
      const svg = this.#canvas.querySelector("svg");
      if (svg) {
        this.#semantics = result.semantics;
        this.viewport.setContent(sizeSvg(svg));
        this.#attachHighlight();
        this.#attachSequence();
      }
      this.#hooks.kind(result.semantics.kind);
      this.#error.textContent = "";
      this.#host.classList.remove("stale");
      requestAnimationFrame(() => {
        if (seq === this.#seq) this.#host.setAttribute("data-wb-state", "rendered");
      });
    } catch (error) {
      // Mermaid's temporary render containers, in case a failure path left one behind.
      for (const leftover of [`wb-render-${seq}`, `dwb-render-${seq}`, `iwb-render-${seq}`]) {
        document.getElementById(leftover)?.remove();
      }
      if (seq !== this.#seq) return;
      this.#fail(renderErrorMessage(error));
    }
  }

  #fail(message: string): void {
    this.#error.textContent = message || "The diagram could not be rendered.";
    this.#host.classList.toggle("stale", this.#canvas.querySelector("svg") !== null);
    this.#host.setAttribute("data-wb-state", "error");
  }

  #dropSvg(): void {
    this.#detachSequence();
    this.#highlight?.dispose();
    this.#highlight = undefined;
    this.#semantics = undefined;
    this.#canvas.replaceChildren();
    this.viewport.clearContent();
    this.#hooks.kind(null);
  }

  #attachHighlight(): void {
    this.#highlight?.dispose();
    this.#highlight = undefined;
    const svg = this.#canvas.querySelector("svg");
    if (this.#highlightOn && svg && this.#semantics?.kind === "flowchart") {
      this.#highlight = attachRelationshipHighlight(svg, this.#semantics);
    }
  }

  #attachSequence(): void {
    this.#detachSequence();
    const svg = this.#canvas.querySelector("svg");
    const semantics = this.#semantics;
    if (!svg || semantics?.kind !== "sequence" || !(this.#playbackOn || this.#freezeOn)) return;
    this.#sequence = new SequenceView(svg, semantics, {
      playback: this.#playbackOn,
      freeze: this.#freezeOn,
      index: this.#playbackIndex,
      pane: this.#host,
      transform: () => this.viewport.state.t,
      subscribe: (listener) => {
        this.#viewListeners.add(listener);
        return () => this.#viewListeners.delete(listener);
      },
      position: (position) => {
        if (position) this.#playbackIndex = position.index;
        this.#hooks.playback(position);
      },
      freezeNote: (reason) => this.#hooks.freezeNote(reason),
    });
  }

  #detachSequence(): void {
    this.#sequence?.dispose();
    this.#sequence = undefined;
  }

  /** Keeps the current message in view, clear of frozen rows and the playback bar; the overview fits. */
  #follow(): void {
    const focus = this.#sequence?.focus();
    if (focus === "overview") this.viewport.fit();
    else if (focus) this.viewport.follow(focus, this.#sequence!.insets());
  }
}

/** Gives the SVG its natural pixel size, so the viewport's zoom is relative to 100 %. */
function sizeSvg(svg: SVGSVGElement): { width: number; height: number } {
  const box = svg.viewBox.baseVal;
  let width = box?.width ?? 0;
  let height = box?.height ?? 0;
  if (!(width > 0 && height > 0)) {
    const rect = svg.getBoundingClientRect();
    width = rect.width || 1;
    height = rect.height || 1;
  }
  svg.style.width = `${width}px`;
  svg.style.height = `${height}px`;
  svg.style.maxWidth = "none";
  return { width, height };
}
