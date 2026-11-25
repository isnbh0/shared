import { type Mermaid } from "mermaid";
import { createSemanticRenderer, renderWithSemantics as renderWithDefaultSemantics, type SemanticRenderRequest } from "./semantics/renderer.js";
import type { SemanticRenderResult } from "./semantics/model.js";
export { sequenceContractFixtures } from "./semantics/sequenceContractFixtures.js";
export type { SequenceContractFixture } from "./semantics/sequenceContractFixtures.js";
export interface Mermaiden extends Mermaid {
    renderWithSemantics(request: SemanticRenderRequest): Promise<SemanticRenderResult>;
}
declare const mermaiden: Mermaiden;
export default mermaiden;
export * from "mermaid";
export { MermaidTransactionFailure, type MermaidTransactionStage } from "./mermaid/runtime.js";
export { createSemanticRenderer, renderWithDefaultSemantics as renderWithSemantics };
export type { SemanticRenderRequest, SemanticRenderer, SemanticValidationRequest, } from "./semantics/renderer.js";
export type { DiagramSemantics, FlowchartSemanticEdge, FlowchartSemanticNode, FlowchartSemantics, SemanticDiagnostic, SemanticRenderResult, SequenceElementRef, SequenceDisclosureCapability, SequenceEventKind, SequenceRenderedContent, SequenceRenderedContentRole, SequenceSemanticEvent, SequenceSemanticMessage, SequenceSemanticParticipant, SequenceSemantics, UnavailableDiagramSemantics, UnsupportedDiagramSemantics, } from "./semantics/model.js";
