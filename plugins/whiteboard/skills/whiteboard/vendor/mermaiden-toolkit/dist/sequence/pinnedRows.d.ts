import type { SequenceSemantics } from "mermaiden";
import { type ResolvedSequenceElements, type SequenceMeasurement } from "./geometry.js";
export type SequenceViewportMatrix = Readonly<{
    a: number;
    b: number;
    c: number;
    d: number;
    e: number;
    f: number;
}>;
export interface SequenceViewportAdapter {
    getMatrix(): SequenceViewportMatrix;
    getSize(): Readonly<{
        width: number;
        height: number;
    }>;
    subscribe(listener: () => void): () => void;
}
export type SequencePinnedRowsOptions = Readonly<{
    overlay: SVGSVGElement;
    viewport: SequenceViewportAdapter;
    visibleParticipantIds?: ReadonlySet<string>;
    resolved?: ResolvedSequenceElements;
    measure?: SequenceMeasurement;
    computedStyle?: (element: Element) => CSSStyleDeclaration;
    parentTransform?: (element: SVGGraphicsElement) => string | undefined;
    rowPadding?: number;
    bottomOffset?: number;
    signal?: AbortSignal;
    onUnavailable?(reason: string): void;
    onAvailabilityChange?(reason: string | undefined): void;
}>;
export interface SequencePinnedRowsHandle {
    setVisibleParticipantIds(ids: ReadonlySet<string>): void;
    setBottomOffset(px: number): void;
    update(): void;
    refresh(): void;
    getInsets(): Readonly<{
        top: number;
        bottom: number;
    }>;
    dispose(): void;
}
/** Removes only toolkit-owned pinned-row presentation from a live SVG or clone. */
export declare function stripSequencePinnedRows(svg: SVGSVGElement): void;
export declare function attachSequencePinnedRows(svg: SVGSVGElement, semantics: SequenceSemantics, options: SequencePinnedRowsOptions): SequencePinnedRowsHandle | undefined;
