// Sequence-diagram features on one rendered SVG: playback (one message at a time) and frozen
// participants (header and footer rows pinned to the pane's top and bottom while panning). Both
// come from mermaiden-toolkit; this module wires them to the preview's pane and to each other.
//
// Coordinates: the toolkit measures in the SVG's user units (viewBox coordinates). The preview
// sizes the SVG so one user unit is one CSS pixel on the stage, offset by the viewBox origin.
import type { SequenceSemantics } from "mermaiden";
import {
  attachSequencePinnedRows,
  attachSequencePlayback,
  sequenceDescendantToRootMatrix,
  type SequencePinnedRowsHandle,
  type SequencePlaybackHandle,
  type SequencePlaybackState,
} from "mermaiden-toolkit";

import type { Insets, Rect, Transform } from "./view-math.ts";

/** `index` counts from 0; `overview` shows every message at once (after the last). */
export type PlaybackPosition = { index: number; count: number; overview: boolean; label: string };
export type PlaybackStep = "previous" | "next" | "first" | "overview";

export type SequenceViewOptions = {
  playback: boolean;
  freeze: boolean;
  /** The playback position to resume at, clamped to the diagram's messages. */
  index: number;
  /** The pane the frozen rows are drawn over, and its current transform. */
  pane: HTMLElement;
  transform(): Transform;
  /** Calls `listener` whenever the transform or the pane's size changes; returns an unsubscribe. */
  subscribe(listener: () => void): () => void;
  position(position: PlaybackPosition | null): void;
  /** Why frozen participants are hidden right now (e.g. too large at this zoom), or null. */
  freezeNote(reason: string | null): void;
};

/** Room kept below the diagram for the playback bar floating over the preview's bottom. */
export const PLAYBACK_BAR_SPACE = 56;
const FOLLOW_MARGIN = 16;
const COPIED_STYLES = [
  "fill",
  "stroke",
  "stroke-width",
  "stroke-linecap",
  "font-family",
  "font-size",
  "font-weight",
  "font-style",
  "line-height",
  "text-anchor",
  "dominant-baseline",
  "color",
  "text-align",
  "white-space",
  "opacity",
  "fill-opacity",
  "stroke-opacity",
];

export class SequenceView {
  readonly #svg: SVGSVGElement;
  readonly #semantics: SequenceSemantics;
  readonly #options: SequenceViewOptions;
  readonly #overlay: SVGSVGElement | undefined;
  readonly #pinned: SequencePinnedRowsHandle | undefined;
  readonly #playback: SequencePlaybackHandle | undefined;
  readonly #cleanup: (() => void)[] = [];

  constructor(svg: SVGSVGElement, semantics: SequenceSemantics, options: SequenceViewOptions) {
    this.#svg = svg;
    this.#semantics = semantics;
    this.#options = options;

    if (options.freeze) {
      // The frozen rows are copies drawn in an overlay outside the diagram's SVG, so they need the
      // diagram's styles and nesting transforms copied before playback or freezing change them.
      const styles = snapshotStyles(svg);
      const overlay = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      overlay.classList.add("preview-overlay");
      overlay.setAttribute("aria-hidden", "true");
      options.pane.append(overlay);
      this.#overlay = overlay;
      this.#pinned = attachSequencePinnedRows(svg, semantics, {
        overlay,
        viewport: {
          getMatrix: () => this.#matrix(),
          getSize: () => ({ width: options.pane.clientWidth, height: options.pane.clientHeight }),
          subscribe: (listener) => options.subscribe(listener),
        },
        computedStyle: (element) => styles.get(element) ?? getComputedStyle(element),
        parentTransform: (element) => parentTransform(svg, element),
        onAvailabilityChange: (reason) => options.freezeNote(reason ?? null),
        onUnavailable: (reason) => console.warn(`Frozen participants unavailable: ${reason}`),
      });
      // The toolkit puts lifeline extensions just before the SVG, inside the transformed stage;
      // they are drawn in pane coordinates, so they belong in the pane. They go after the stage so
      // the diagram stays the pane's first SVG; the stylesheet layers them under it.
      const underlay = svg.previousElementSibling;
      if (underlay?.matches(".mermaiden-sequence-frozen-underlay")) overlay.before(underlay);
      if (!this.#pinned) {
        overlay.remove();
        this.#overlay = undefined;
      }
    }

    if (options.playback) {
      this.#playback = attachSequencePlayback(svg, semantics, {
        onUnavailable: (reason) => console.warn(`Playback unavailable: ${reason}`),
      });
    }
    const playback = this.#playback;
    if (playback) {
      playback.setIndex(Math.min(options.index, playback.getState().messageCount));
      const report = (state: SequencePlaybackState) => {
        this.#pinned?.setVisibleParticipantIds(state.revealedParticipantIds);
        options.position(position(state, semantics));
      };
      this.#cleanup.push(playback.subscribe(report));
      this.#pinned?.setBottomOffset(PLAYBACK_BAR_SPACE);
      report(playback.getState());
    }
  }

  get playing(): boolean {
    return this.#playback !== undefined;
  }

  get index(): number {
    return this.#playback?.getState().index ?? 0;
  }

  step(step: PlaybackStep): void {
    const playback = this.#playback;
    if (!playback) return;
    if (step === "previous") playback.previous();
    else if (step === "next") playback.next();
    else playback.setIndex(step === "first" ? 0 : playback.getState().messageCount);
  }

  /** What the view should show: the current message (stage coordinates), or the whole diagram. */
  focus(): Rect | "overview" | undefined {
    const state = this.#playback?.getState();
    if (!state) return undefined;
    if (state.kind === "overview") return "overview";
    const box = this.#svg.viewBox.baseVal;
    const b = state.currentStepBounds;
    return { x: b.x - (box?.x ?? 0), y: b.y - (box?.y ?? 0), width: b.width, height: b.height };
  }

  /** Pane space the frozen rows and the playback bar cover, which followed messages avoid. */
  insets(): Insets {
    const frozen = this.#pinned?.getInsets() ?? { top: 0, bottom: 0 };
    const bar = this.#playback ? PLAYBACK_BAR_SPACE : 0;
    return {
      top: frozen.top + FOLLOW_MARGIN,
      bottom: frozen.bottom + bar + FOLLOW_MARGIN,
      left: FOLLOW_MARGIN,
      right: FOLLOW_MARGIN,
    };
  }

  dispose(): void {
    for (const cleanup of this.#cleanup.splice(0)) cleanup();
    this.#playback?.dispose();
    this.#pinned?.dispose();
    this.#overlay?.remove();
    if (this.#playback) this.#options.position(null);
    if (this.#pinned) this.#options.freezeNote(null);
  }

  /** SVG user units to pane pixels. */
  #matrix() {
    const { x, y, k } = this.#options.transform();
    const box = this.#svg.viewBox.baseVal;
    return { a: k, b: 0, c: 0, d: k, e: x - (box?.x ?? 0) * k, f: y - (box?.y ?? 0) * k };
  }
}

function position(state: SequencePlaybackState, semantics: SequenceSemantics): PlaybackPosition {
  const message = semantics.model.messages.find((m) => m.id === state.currentMessageId);
  return {
    index: state.index,
    count: state.messageCount,
    overview: state.kind === "overview",
    label: state.kind === "overview" ? "" : (message?.label ?? ""),
  };
}

function snapshotStyles(svg: SVGSVGElement): Map<Element, CSSStyleDeclaration> {
  const styles = new Map<Element, CSSStyleDeclaration>();
  for (const element of [svg, ...svg.querySelectorAll("*")]) {
    const computed = getComputedStyle(element);
    const snapshot = document.createElement("span").style;
    for (const property of COPIED_STYLES) snapshot.setProperty(property, computed.getPropertyValue(property));
    styles.set(element, snapshot);
  }
  return styles;
}

function parentTransform(svg: SVGSVGElement, element: SVGGraphicsElement): string | undefined {
  const parent = element.parentNode;
  if (!(parent instanceof SVGGraphicsElement) || parent === svg) return undefined;
  const m = sequenceDescendantToRootMatrix(svg, parent);
  return m ? `matrix(${m.a} ${m.b} ${m.c} ${m.d} ${m.e} ${m.f})` : undefined;
}
