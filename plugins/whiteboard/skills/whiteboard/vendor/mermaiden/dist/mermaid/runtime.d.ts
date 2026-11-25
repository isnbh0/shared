import { type LayoutLoaderDefinition, type MermaidConfig, type RenderResult } from "mermaid";
export type FeatureInspection = Readonly<{
    diagramType: string;
    /**
     * Mermaid's parsed diagram database, valid only for the duration of the
     * synchronous `inspect` call. Copy out everything needed before returning:
     * once the transaction releases, the next render may mutate the singleton
     * diagram databases and the shared `commonDb` this object views.
     */
    database: unknown;
    svg: string;
}>;
export type MermaidTransactionStage = "setup" | "initialization" | "parse" | "render";
export declare class MermaidTransactionFailure extends Error {
    readonly stage: MermaidTransactionStage;
    readonly cause: unknown;
    constructor(stage: MermaidTransactionStage, cause: unknown);
}
export type InspectionOutcome<T> = Readonly<{
    status: "not-applicable";
}> | Readonly<{
    status: "available";
    value: T;
}> | Readonly<{
    status: "failed";
    reason: unknown;
}>;
type SynchronousInspectionValue<T> = T extends PromiseLike<unknown> ? never : T;
export interface MermaidInspector<T> {
    appliesTo(diagramType: string): boolean;
    inspect(input: FeatureInspection): SynchronousInspectionValue<T>;
}
export type TransactionalValidationRequest = Readonly<{
    source: string;
    config: MermaidConfig;
    signal?: AbortSignal;
}>;
export type TransactionalRenderRequest<T> = Readonly<{
    id: string;
    source: string;
    container?: Element;
    config?: MermaidConfig;
    signal?: AbortSignal;
    inspector?: MermaidInspector<T>;
}>;
export type TransactionalRenderResult<T> = Readonly<{
    result: RenderResult;
    inspection?: InspectionOutcome<T>;
}>;
export interface TransactionalMermaidRuntime {
    validate(request: TransactionalValidationRequest): Promise<void>;
    render<T = never>(request: TransactionalRenderRequest<T>): Promise<TransactionalRenderResult<T>>;
}
/** @internal The caller must already own the shared Mermaid transaction. */
export declare function inspectRendered<T>(source: string, diagramType: string, svg: string, inspector: MermaidInspector<T>, signal?: AbortSignal): Promise<InspectionOutcome<T>>;
export declare function createTransactionalMermaidRuntime(options?: Readonly<{
    layoutLoaders?: LayoutLoaderDefinition[];
}>): TransactionalMermaidRuntime;
export declare const transactionalMermaid: TransactionalMermaidRuntime;
export {};
