export type RelationshipNode = Readonly<{
    id: string;
    label: string;
}>;
export type RelationshipEdge = Readonly<{
    id: string;
    start: string;
    end: string;
    visible: boolean;
}>;
export type RelationshipModel = Readonly<{
    nodes: readonly RelationshipNode[];
    edges: readonly RelationshipEdge[];
}>;
