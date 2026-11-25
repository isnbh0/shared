import type { FlowchartSemantics } from "mermaiden";
export declare const RELATIONSHIP_HIGHLIGHT_LAYER_SELECTOR = ".mermaiden-relationship-visual,.mermaiden-relationship-interaction";
/**
 * Removes every element relationship highlighting added. Safe on an untouched SVG.
 *
 * Pass the rendered `<svg>` element itself, not the container holding it: the
 * `relationships-active` marker lives on the SVG's parent, so a container
 * argument would strip the layers but leave the marker behind and clear the
 * class off the container's own parent instead.
 */
export declare function stripRelationshipHighlight(root: Element): void;
export type RelationshipHighlightOptions = Readonly<{
    /** Display-space elements to measure instead of the canonical node groups, keyed by node id. */
    nodeSurfaces?: ReadonlyMap<string, SVGGraphicsElement>;
    /** Tree holding the original rendered node ids and edge paths. Defaults to displaySvg. */
    canonicalSvg?: SVGSVGElement;
    /** Attach aborts if this is already aborted, and again after layers are built. */
    signal?: AbortSignal;
    onListenerCountChange?(delta: 1 | -1): void;
}>;
export interface RelationshipHighlightHandle {
    dispose(): void;
}
/**
 * Attaches relationship interaction for the unambiguous rendered subset of a
 * flowchart semantic artifact.
 */
export declare function attachRelationshipHighlight(displaySvg: SVGSVGElement, semantics: FlowchartSemantics, options?: RelationshipHighlightOptions): RelationshipHighlightHandle | undefined;
