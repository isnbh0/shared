import type { SequenceRenderedContentRole, SequenceSemantics } from "mermaiden";
export type SequenceBounds = Readonly<{
    x: number;
    y: number;
    width: number;
    height: number;
}>;
export type SequenceMeasurement = (element: SVGGraphicsElement, svg: SVGSVGElement) => SequenceBounds | undefined;
/** Converts a connected SVG descendant's local coordinates into root user units. */
export declare function sequenceDescendantToRootMatrix(root: SVGSVGElement, element: SVGGraphicsElement): DOMMatrix | undefined;
export type ResolvedSequenceParticipant = Readonly<{
    id: string;
    header: readonly SVGGraphicsElement[];
    footer: readonly SVGGraphicsElement[];
    lifeline: readonly SVGGraphicsElement[];
}>;
export type ResolvedSequenceMessage = Readonly<{
    id: string;
    elements: readonly SVGGraphicsElement[];
}>;
export type ResolvedSequenceContent = Readonly<{
    eventId: string;
    role: SequenceRenderedContentRole;
    elements: readonly SVGGraphicsElement[];
    reveal: Readonly<{
        fromMessage: number | null;
        toMessage: number | null;
    }>;
}>;
export type ResolvedSequenceElements = Readonly<{
    svg: SVGSVGElement;
    participants: ReadonlyMap<string, ResolvedSequenceParticipant>;
    messages: ReadonlyMap<string, ResolvedSequenceMessage>;
    content?: ReadonlyMap<string, ResolvedSequenceContent>;
}>;
/** Resolves portable child paths on an unchanged native Mermaid SVG. */
export declare function resolveSequenceElements(svg: SVGSVGElement, semantics: SequenceSemantics): ResolvedSequenceElements | undefined;
export declare function intersectSequenceBounds(bounds: SequenceBounds, clip: SequenceBounds): SequenceBounds | undefined;
/** Measure before viewport wrapping. Consumers retain this canonical snapshot
 * across pan/zoom; measuring a wrapped tree includes its mutable transform. */
export declare const measureSequenceElement: SequenceMeasurement;
export declare function validBounds(bounds: SequenceBounds, allowZero?: boolean): boolean;
export declare function unionSequenceBounds(bounds: readonly SequenceBounds[]): SequenceBounds | undefined;
export declare function padSequenceBounds(bounds: SequenceBounds, padding: number): SequenceBounds | undefined;
export type SequenceFitLayout = Readonly<{
    scale: number;
    topInset: number;
    bottomInset: number;
    x: number;
    y: number;
}>;
export declare function layoutSequenceFit(viewport: Readonly<{
    width: number;
    height: number;
}>, target: SequenceBounds, topHeight?: number, bottomHeight?: number): SequenceFitLayout | undefined;
