// No lost update through the server: every successful write replaced exactly its base.
// Bounds: writes go through the workspace; external edits run between write groups, because an
// external edit racing the rename is the README's named gap.
import { readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import fc from "fast-check";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { revOf, type Rev } from "../../server/ids.ts";
import { Workspace, type WriteAudit } from "../../server/workspace.ts";
import { tempDir } from "../helpers.ts";

type Op =
  | { kind: "read"; client: number }
  | { kind: "writes"; writes: { client: number; text: string }[] }
  | { kind: "external"; text: string }
  | { kind: "delete" };

const text = fc.stringMatching(/^[ab]{0,3}$/);
const client = fc.integer({ min: 0, max: 2 });
const op: fc.Arbitrary<Op> = fc.oneof(
  { weight: 3, arbitrary: client.map((c) => ({ kind: "read" as const, client: c })) },
  {
    weight: 4,
    arbitrary: fc
      .array(fc.record({ client, text }), { minLength: 1, maxLength: 4 })
      .map((writes) => ({ kind: "writes" as const, writes })),
  },
  { weight: 1, arbitrary: text.map((t) => ({ kind: "external" as const, text: t })) },
  { weight: 1, arbitrary: fc.constant({ kind: "delete" as const }) },
);

let dir: string;

beforeAll(async () => {
  dir = await tempDir("wb-prop-");
});

afterAll(async () => {
  await rm(dir, { recursive: true, force: true });
});

async function diskRev(path: string): Promise<Rev | null> {
  try {
    return revOf(await readFile(path, "utf8"));
  } catch {
    return null;
  }
}

describe("workspace no-lost-update law", () => {
  it("never lets a successful write replace anything but its base", async () => {
    let run = 0;
    await fc.assert(
      fc.asyncProperty(fc.array(op, { minLength: 1, maxLength: 25 }), async (ops) => {
        const path = join(dir, `f${run++}.mmd`);
        const log: WriteAudit[] = [];
        const ws = new Workspace({ audit: (entry) => log.push(entry) });
        const lastRead: (Rev | null)[] = [null, null, null];
        try {
          for (const step of ops) {
            if (step.kind === "read") {
              lastRead[step.client] = (await ws.read(path)).rev;
            } else if (step.kind === "external") {
              await writeFile(path, step.text);
            } else if (step.kind === "delete") {
              await rm(path, { force: true });
            } else {
              const before = await diskRev(path);
              const logStart = log.length;
              const results = await Promise.all(
                step.writes.map((w) => ws.write(path, w.text, lastRead[w.client] ?? null)),
              );
              const committed = log.slice(logStart);
              // Every successful write replaced exactly its base.
              for (const entry of committed) expect(entry.replaced).toBe(entry.base);
              // Successes and audit entries match one to one; refusals committed nothing.
              const successes = results.filter((r) => r.ok);
              expect(committed).toHaveLength(successes.length);
              for (const [i, r] of results.entries()) {
                if (r.ok) expect(r.rev).toBe(revOf(step.writes[i]!.text));
              }
              // The file is the last committed write, or unchanged when every write was refused.
              const expected = committed.length > 0 ? committed[committed.length - 1]!.rev : before;
              expect(await diskRev(path)).toBe(expected);
            }
          }
          // At the end, read matches the file on disk.
          expect((await ws.read(path)).rev).toBe(await diskRev(path));
        } finally {
          ws.dispose();
        }
      }),
      { numRuns: 250 },
    );
  }, 120_000);
});
