import type { RenderResult } from "mermaid";
export type SemanticDiagnostic = Readonly<{
    severity: "warning" | "error";
    message: string;
    code?: string;
    eventIds?: readonly string[];
}>;
export type FlowchartSemanticNode = Readonly<{
    id: string;
    label: string;
}>;
export type FlowchartSemanticEdge = Readonly<{
    id: string;
    start: string;
    end: string;
    visible: boolean;
}>;
export type FlowchartSemantics = Readonly<{
    kind: "flowchart";
    diagramType: string;
    model: Readonly<{
        nodes: readonly FlowchartSemanticNode[];
        edges: readonly FlowchartSemanticEdge[];
    }>;
    rendered: Readonly<{
        nodes: readonly Readonly<{
            nodeId: string;
            elementId: string;
        }>[];
        edges: readonly Readonly<{
            edgeId: string;
            dataId: string;
        }>[];
    }>;
    diagnostics: readonly SemanticDiagnostic[];
}>;
/** Element-child indices from the SVG root. */
export type SequenceElementRef = readonly number[];
export type SequenceSemanticParticipant = Readonly<{
    id: string;
    label: string;
}>;
export type SequenceSemanticMessage = Readonly<{
    id: string;
    from: string;
    to: string;
    label: string;
    order: number;
}>;
export type SequenceEventKind = "message" | "note" | "activation-start" | "activation-end" | "fragment-open" | "fragment-branch" | "fragment-close" | "rect-open" | "rect-close" | "autonumber" | "central-connection" | "unknown";
export type SequenceSemanticEvent = Readonly<{
    id: string;
    rawId: string;
    kind: SequenceEventKind;
    ordinal: number;
    participants: readonly string[];
    messageId?: string | undefined;
    revealAtMessage: number | null;
    interval?: Readonly<{
        startEventId: string;
        endEventId: string;
        fromMessage: number | null;
        toMessage: number | null;
    }> | undefined;
}>;
export type SequenceRenderedContentRole = "note" | "activation" | "fragment-opening" | "fragment-branch" | "fragment-closing" | "rect-background";
export type SequenceRenderedContent = Readonly<{
    eventId: string;
    role: SequenceRenderedContentRole;
    elements: readonly SequenceElementRef[];
    reveal: Readonly<{
        fromMessage: number | null;
        toMessage: number | null;
    }>;
}>;
export type SequenceDisclosureCapability = Readonly<{
    completeDisclosure: boolean;
    diagnostics: readonly Readonly<{
        code: string;
        eventIds: readonly string[];
    }>[];
}>;
export type SequenceSemantics = Readonly<{
    kind: "sequence";
    diagramType: string;
    model: Readonly<{
        participants: readonly SequenceSemanticParticipant[];
        messages: readonly SequenceSemanticMessage[];
        events?: readonly SequenceSemanticEvent[];
    }>;
    rendered: Readonly<{
        participants: readonly Readonly<{
            participantId: string;
            header: readonly SequenceElementRef[];
            footer: readonly SequenceElementRef[];
            lifeline: readonly SequenceElementRef[];
        }>[];
        messages: readonly Readonly<{
            messageId: string;
            elements: readonly SequenceElementRef[];
        }>[];
        content?: readonly SequenceRenderedContent[];
    }>;
    capabilities?: Readonly<{
        disclosure: SequenceDisclosureCapability;
    }>;
    diagnostics: readonly SemanticDiagnostic[];
}>;
export type UnsupportedDiagramSemantics = Readonly<{
    kind: "unsupported";
    diagramType: string;
    diagnostics: readonly [];
}>;
export type UnavailableDiagramSemantics = Readonly<{
    kind: "unavailable";
    diagramType: string;
    diagnostics: readonly SemanticDiagnostic[];
}>;
export type DiagramSemantics = FlowchartSemantics | SequenceSemantics | UnsupportedDiagramSemantics | UnavailableDiagramSemantics;
export type SemanticRenderResult = RenderResult & Readonly<{
    semantics: DiagramSemantics;
}>;
