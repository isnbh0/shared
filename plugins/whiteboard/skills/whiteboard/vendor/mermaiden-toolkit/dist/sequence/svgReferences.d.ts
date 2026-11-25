export declare function referencedSvgIds(root: Element): ReadonlySet<string>;
export declare function cloneSvgTree<T extends Element>(root: T, replacements: ReadonlyMap<string, string>): T;
export declare function collectReferencedDefinitions(svg: SVGSVGElement, sources: readonly Element[]): readonly Element[];
