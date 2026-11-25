import type { FeatureInspection } from "../mermaid/runtime.js";
import type { DiagramSemanticAdapter } from "./flowchart.js";
import type { SequenceSemantics, UnavailableDiagramSemantics } from "./model.js";
export declare function inspectSequence(input: FeatureInspection): SequenceSemantics | UnavailableDiagramSemantics;
export declare const sequenceSemanticAdapter: DiagramSemanticAdapter<SequenceSemantics | UnavailableDiagramSemantics>;
