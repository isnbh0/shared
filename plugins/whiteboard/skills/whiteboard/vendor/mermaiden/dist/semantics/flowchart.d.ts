import type { FeatureInspection } from "../mermaid/runtime.js";
import type { DiagramSemantics, FlowchartSemantics, UnavailableDiagramSemantics } from "./model.js";
export interface DiagramSemanticAdapter<T extends DiagramSemantics> {
    appliesTo(diagramType: string): boolean;
    inspect(input: FeatureInspection): T;
}
/**
 * Copies one supported Mermaid flowchart database into the public semantic
 * contract. This is the only function that reads `getData()` or computes
 * rendered correspondence.
 */
export declare function inspectFlowchart(input: FeatureInspection): FlowchartSemantics | UnavailableDiagramSemantics;
export declare function normalizeFlowchartType(type: string): "flowchart" | undefined;
export declare const flowchartSemanticAdapter: DiagramSemanticAdapter<FlowchartSemantics | UnavailableDiagramSemantics>;
