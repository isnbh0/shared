import type { SequenceSemantics } from "mermaiden";
import { type ResolvedSequenceElements, type SequenceBounds, type SequenceMeasurement } from "./geometry.js";
import { type SequenceProjection } from "./projection.js";
export type SequencePlaybackState = SequenceProjection;
export type SequenceFitRequest = Readonly<{
    kind: "message" | "overview";
    bounds: SequenceBounds;
    cumulativeBounds: SequenceBounds;
    currentStepBounds: SequenceBounds;
    fullBounds: SequenceBounds;
}>;
export type SequencePlaybackOptions = Readonly<{
    resolved?: ResolvedSequenceElements;
    measure?: SequenceMeasurement;
    padding?: number;
    signal?: AbortSignal;
    onFitRequest?(request: SequenceFitRequest): void;
    onUnavailable?(reason: string): void;
}>;
export interface SequencePlaybackHandle {
    getState(): SequencePlaybackState;
    setIndex(index: number): void;
    setOverview(overview: boolean): void;
    next(): void;
    previous(): void;
    subscribe(listener: (state: SequencePlaybackState) => void): () => void;
    dispose(): void;
}
/** @deprecated Prefer deriveSequenceProjection with resolved canonical geometry. */
export declare function deriveSequencePlaybackState(semantics: SequenceSemantics, index: number): Pick<SequencePlaybackState, "index" | "messageCount" | "kind" | "revealedParticipantIds">;
/** Removes playback state from a live SVG or serialization clone. */
export declare function stripSequencePlayback(svg: SVGSVGElement): void;
export declare function attachSequencePlayback(svg: SVGSVGElement, semantics: SequenceSemantics, options?: SequencePlaybackOptions): SequencePlaybackHandle | undefined;
