import type { SequenceSemantics } from "mermaiden";
import { type ResolvedSequenceElements, type SequenceBounds } from "./geometry.js";
export type SequenceProjection = Readonly<{
    index: number;
    messageCount: number;
    kind: "message" | "overview";
    currentMessageId?: string;
    visibleMessageIds: ReadonlySet<string>;
    pastMessageIds: ReadonlySet<string>;
    visibleEventIds: ReadonlySet<string>;
    revealedParticipantIds: ReadonlySet<string>;
    frontier?: number;
    cumulativeBounds: SequenceBounds;
    currentStepBounds: SequenceBounds;
    fullBounds: SequenceBounds;
}>;
export type SequenceGeometrySnapshot = ReadonlyMap<SVGGraphicsElement, SequenceBounds>;
/** Pure narrative projection shared by disclosure, accessibility and camera inputs. */
export declare function deriveSequenceProjection(semantics: SequenceSemantics, resolved: ResolvedSequenceElements, geometry: SequenceGeometrySnapshot, index: number, overview?: boolean): SequenceProjection | undefined;
