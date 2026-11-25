export type SequenceContractFixture = Readonly<{
    id: string;
    source: string;
    expectedKinds: readonly string[];
    completeDisclosure: boolean;
    diagnosticCodes: readonly string[];
}>;
/** Shared pinned-renderer corpus for engine and browser contract checks. */
export declare const sequenceContractFixtures: readonly SequenceContractFixture[];
