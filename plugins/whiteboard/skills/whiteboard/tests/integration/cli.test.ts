import { existsSync } from "node:fs";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { delimiter, join } from "node:path";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { STARTER } from "../../server/workspace.ts";
import { socketPath as socketPathOf } from "../../server/state.ts";
import { freePort, shortStateDir, tempDir, wb } from "../helpers.ts";

const revFrom = (stderr: string) => /^rev ([0-9a-f]{16})$/m.exec(stderr)?.[1];

describe("wb", () => {
  let cwd: string;
  let env: Record<string, string>;
  let stateDir: string;
  let port: number;

  beforeAll(async () => {
    cwd = await tempDir("wb-cli-");
    stateDir = await shortStateDir();
    port = await freePort();
    env = { WHITEBOARD_PORT: String(port), WHITEBOARD_STATE_DIR: stateDir };
  });

  afterAll(async () => {
    await wb(["stop"], env);
    await rm(cwd, { recursive: true, force: true });
    await rm(stateDir, { recursive: true, force: true });
  });

  it("opens a relative path, creating it with the starter diagram and starting the server", async () => {
    const run = await wb(["open", "rel/new.mmd"], env, { cwd });
    expect(run.code, run.stderr).toBe(0);
    expect(await readFile(join(cwd, "rel", "new.mmd"), "utf8")).toBe(STARTER);
    expect(run.stderr).toMatch(/starting whiteboard server/);
    expect(run.stdout).toMatch(new RegExp(`^http://127\\.0\\.0\\.1:${port}/#/[0-9a-f]{12}/new\\.mmd$`, "m"));
    expect(run.stdout).toMatch(/No page is connected/);
    expect(run.stderr).toMatch(/^created .*\/rel\/new\.mmd$/m);
  }, 130_000);

  it("reads without opening, and writes with compare-and-swap", async () => {
    const path = join(cwd, "plain.mmd");
    await writeFile(path, "flowchart LR\n  A\n");
    const read = await wb(["read", path], env);
    expect(read.code).toBe(0);
    expect(read.stdout).toBe("flowchart LR\n  A\n");
    const rev = revFrom(read.stderr);
    expect(rev).toMatch(/^[0-9a-f]{16}$/);
    expect((await wb(["ls"], env)).stdout).not.toMatch(/plain\.mmd/);

    const write = await wb(["write", path, "--rev", rev!], env, { input: "flowchart LR\n  B" });
    expect(write.code, write.stderr).toBe(0);
    const newRev = revFrom(write.stderr);
    expect(await readFile(path, "utf8")).toBe("flowchart LR\n  B");

    const stale = await wb(["write", path, "--rev", rev!], env, { input: "lost" });
    expect(stale.code).toBe(1);
    expect(stale.stderr).toContain(`current rev ${newRev}`);
    expect(stale.stderr).toMatch(/read it again/);
    expect(await readFile(path, "utf8")).toBe("flowchart LR\n  B");
  }, 60_000);

  it("creates with --rev none, refuses it for an existing file, and requires --rev", async () => {
    const path = join(cwd, "fresh", "made.mmd");
    const create = await wb(["write", path, "--rev", "none"], env, { input: "flowchart TD\n" });
    expect(create.code, create.stderr).toBe(0);
    expect(await readFile(path, "utf8")).toBe("flowchart TD\n");
    const again = await wb(["write", path, "--rev", "none"], env, { input: "x" });
    expect(again.code).toBe(1);
    expect((await wb(["write", path], env, { input: "x" })).code).toBe(2);
  }, 60_000);

  it("reports a missing file on read", async () => {
    const run = await wb(["read", join(cwd, "absent.mmd")], env);
    expect(run.code).toBe(1);
    expect(run.stderr).toMatch(/no such file/);
  });

  it("lists, closes, and stops", async () => {
    await mkdir(join(cwd, "list"), { recursive: true });
    await wb(["open", join(cwd, "list", "one.mmd")], env);
    const ls = await wb(["ls"], env);
    expect(ls.stdout).toMatch(/^[0-9a-f]{12} {2}one\.mmd {2}\/.*\/list\/one\.mmd$/m);
    expect(ls.stdout).toMatch(/no page is connected\n$/);
    expect((await wb(["close", join(cwd, "list", "one.mmd")], env)).code).toBe(0);
    const after = await wb(["ls"], env);
    expect(after.stdout).not.toMatch(/one\.mmd/);
    expect(after.stdout).toMatch(/no page is connected\n$/);
    const stop = await wb(["stop"], env);
    expect(stop.code).toBe(0);
    expect(stop.stdout).toBe("stopped\n");
    expect(existsSync(socketPathOf(stateDir, port))).toBe(false);
    expect((await wb(["stop"], env)).stdout).toMatch(/not running/);
  }, 60_000);
});

describe("wb requirements", () => {
  it("refuses a Node older than 24 by name, before anything starts", async () => {
    const bin = await tempDir("wb-old-node-");
    // A `node` that reports 22.16.0 to the launcher and otherwise is the real one.
    await writeFile(
      join(bin, "node"),
      `#!/bin/sh\nif [ "$1" = "-p" ]; then echo 22.16.0; else exec "${process.execPath}" "$@"; fi\n`,
      { mode: 0o755 },
    );
    try {
      const run = await wb(["ls"], {
        WHITEBOARD_PORT: "1",
        WHITEBOARD_STATE_DIR: "/nonexistent",
        PATH: `${bin}${delimiter}${process.env["PATH"] ?? ""}`,
      });
      expect(run.code).toBe(1);
      expect(run.stderr).toMatch(/Node 22\.16\.0 is too old/);
    } finally {
      await rm(bin, { recursive: true, force: true });
    }
  }, 30_000);
});

describe("wb starting", () => {
  it("lets two simultaneous commands share one new server", async () => {
    const stateDir = await shortStateDir();
    const port = await freePort();
    const env = { WHITEBOARD_PORT: String(port), WHITEBOARD_STATE_DIR: stateDir };
    try {
      const [a, b] = await Promise.all([wb(["ls"], env), wb(["ls"], env)]);
      expect(a.code, a.stderr).toBe(0);
      expect(b.code, b.stderr).toBe(0);
      expect(a.stdout).toBe("nothing is open\nno page is connected\n");
      const log = await readFile(join(stateDir, String(port), "server.log"), "utf8");
      expect(log.match(/whiteboard server \d+ on/g)).toHaveLength(1);
    } finally {
      await wb(["stop"], env);
      await rm(stateDir, { recursive: true, force: true });
    }
  }, 130_000);

  it("fails within 10 s when another program holds the port", async () => {
    const stateDir = await shortStateDir();
    const blocker = createServer((_req, res) => res.end("someone else"));
    await new Promise<void>((r) => blocker.listen(0, "127.0.0.1", r));
    const address = blocker.address();
    const port = typeof address === "object" && address ? address.port : 0;
    try {
      const started = Date.now();
      const run = await wb(["ls"], { WHITEBOARD_PORT: String(port), WHITEBOARD_STATE_DIR: stateDir });
      expect(run.code).toBe(1);
      expect(Date.now() - started).toBeLessThan(10_000);
      expect(run.stderr).toContain(`port ${port} is in use`);
    } finally {
      await new Promise((r) => blocker.close(r));
      await rm(stateDir, { recursive: true, force: true });
    }
  }, 30_000);
});
