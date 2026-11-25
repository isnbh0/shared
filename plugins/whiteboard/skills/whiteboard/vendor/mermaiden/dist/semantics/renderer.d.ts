import type { LayoutLoaderDefinition, MermaidConfig } from "mermaid";
import { type TransactionalValidationRequest } from "../mermaid/runtime.js";
import type { SemanticRenderResult } from "./model.js";
export type SemanticRenderRequest = Readonly<{
    id: string;
    source: string;
    container?: Element;
    config?: MermaidConfig;
    signal?: AbortSignal;
}>;
export type SemanticValidationRequest = TransactionalValidationRequest;
export interface SemanticRenderer {
    validate(request: SemanticValidationRequest): Promise<void>;
    renderWithSemantics(request: SemanticRenderRequest): Promise<SemanticRenderResult>;
}
export declare function createSemanticRenderer(options?: Readonly<{
    layoutLoaders?: LayoutLoaderDefinition[];
}>): SemanticRenderer;
export declare function renderWithSemantics(request: SemanticRenderRequest): Promise<SemanticRenderResult>;
