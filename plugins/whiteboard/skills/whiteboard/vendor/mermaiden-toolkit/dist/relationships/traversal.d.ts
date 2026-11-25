import type { RelationshipModel } from "./model.js";
export type RelationshipTrace = Readonly<{
    ancestors: ReadonlySet<string>;
    current: ReadonlySet<string>;
    descendants: ReadonlySet<string>;
    both: ReadonlySet<string>;
    edges: ReadonlySet<string>;
}>;
export declare function createRelationshipTraversal(model: RelationshipModel): {
    trace(nodeId: string): RelationshipTrace;
};
