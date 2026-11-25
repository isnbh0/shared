import { existsSync } from "node:fs";
import { readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { freePort, openEvents, shortStateDir, sleep, tempDir, wb } from "../helpers.ts";

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const VALID = "flowchart LR\n  Alpha --> Beta\n";
const INVALID = "flowchart LR\n  A -->\n";

async function expectPng(path: string): Promise<void> {
  const bytes = await readFile(path);
  expect(bytes.subarray(0, 8).equals(PNG_SIGNATURE)).toBe(true);
  expect(bytes.byteLength).toBeGreaterThan(1024);
}

describe("wb shot", () => {
  let dir: string;
  let stateDir: string;
  let port: number;
  let env: Record<string, string>;
  const ls = async () => (await wb(["ls"], env)).stdout;

  beforeAll(async () => {
    dir = await tempDir("wb-shot-");
    stateDir = await shortStateDir();
    port = await freePort();
    env = { WHITEBOARD_PORT: String(port), WHITEBOARD_STATE_DIR: stateDir };
    await writeFile(join(dir, "valid.mmd"), VALID);
    await writeFile(join(dir, "invalid.mmd"), INVALID);
  });

  afterAll(async () => {
    await wb(["stop"], env);
    await rm(dir, { recursive: true, force: true });
    await rm(stateDir, { recursive: true, force: true });
  });

  it("writes a PNG under STATE/shots/ and leaves an unopened file closed", async () => {
    const run = await wb(["shot", join(dir, "valid.mmd")], env);
    expect(run.code, run.stderr).toBe(0);
    const path = run.stdout.trim();
    expect(path.startsWith(join(stateDir, "shots") + "/")).toBe(true);
    expect(path).toMatch(/\/\d{8}-\d{6}(-\d+)?\.png$/);
    await expectPng(path);
    expect(await ls()).toBe("");
  }, 180_000);

  it("writes to the given output path", async () => {
    const out = join(dir, "out", "shot.png");
    const run = await wb(["shot", join(dir, "valid.mmd"), out], env);
    expect(run.code, run.stderr).toBe(0);
    expect(run.stdout.trim()).toBe(out);
    await expectPng(out);
  }, 60_000);

  it("exits 1 with the render error, and still writes the PNG", async () => {
    const out = join(dir, "invalid.png");
    const run = await wb(["shot", join(dir, "invalid.mmd"), out], env);
    expect(run.code).toBe(1);
    expect(run.stderr).toMatch(/^render error: Parse error/m);
    await expectPng(out);
    expect(await ls()).toBe("");
  }, 60_000);

  it("exits 1 for a missing file and creates nothing", async () => {
    const missing = join(dir, "missing.mmd");
    const out = join(dir, "missing.png");
    const run = await wb(["shot", missing, out], env);
    expect(run.code).toBe(1);
    expect(existsSync(missing)).toBe(false);
    expect(existsSync(out)).toBe(false);
  }, 60_000);

  it("leaves an already open file open", async () => {
    const path = join(dir, "valid.mmd");
    expect((await wb(["open", path], env)).code).toBe(0);
    const before = await ls();
    expect(before).toContain("valid.mmd");
    const run = await wb(["shot", path, join(dir, "open.png")], env);
    expect(run.code, run.stderr).toBe(0);
    expect(await ls()).toBe(before);
    await wb(["close", path], env);
  }, 60_000);

  it("sends no focus event to a connected page", async () => {
    const stream = await openEvents(port);
    try {
      await stream.next("docs");
      const run = await wb(["shot", join(dir, "valid.mmd"), join(dir, "focus.png")], env);
      expect(run.code, run.stderr).toBe(0);
      await sleep(200);
      expect(stream.events.filter((e) => e.event === "focus")).toEqual([]);
      // The shot's own open and close did reach the stream, so the check above is meaningful.
      expect(stream.events.filter((e) => e.event === "docs").length).toBeGreaterThanOrEqual(3);
    } finally {
      stream.close();
    }
  }, 60_000);
});
