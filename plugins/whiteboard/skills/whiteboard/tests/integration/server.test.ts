import { existsSync } from "node:fs";
import { rm } from "node:fs/promises";
import { join } from "node:path";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { startServer } from "../../server/main.ts";
import { buildPage, SKILL_DIR } from "../../server/page.ts";
import { socketPath as socketPathOf } from "../../server/state.ts";
import { freePort, http, openEvents, shortStateDir, sleep, waitFor } from "../helpers.ts";

describe("server", () => {
  let stateDir: string;
  let port: number;
  let server: Awaited<ReturnType<typeof startServer>>;
  let exits = 0;

  beforeAll(async () => {
    stateDir = await shortStateDir();
    port = await freePort();
    server = await startServer({ port, stateDir, idleMs: 60_000, onExit: () => exits++ });
  }, 120_000);

  afterAll(async () => {
    await server.close();
    await rm(stateDir, { recursive: true, force: true });
  });

  it("answers health on the socket and serves the built page on the port", async () => {
    const health = await http({ socketPath: socketPathOf(stateDir, port) }, "GET", "/health");
    expect(health.status).toBe(200);
    expect(health.json).toMatchObject({ port, pid: process.pid, pages: 0 });
    const index = await http({ port }, "GET", "/");
    expect(index.status).toBe(200);
    expect(index.text).toMatch(/<!doctype html>/i);
    expect(index.text).toMatch(/<script type="module"[^>]*src="\/assets\//);
  });

  it("refuses a second server on the same port and keeps the first working", async () => {
    const otherState = await shortStateDir();
    try {
      await expect(startServer({ port, stateDir: otherState, idleMs: 60_000, onExit: () => {} })).rejects.toMatchObject({
        code: "EADDRINUSE",
      });
      expect(existsSync(join(otherState, String(port)))).toBe(false);
      const health = await http({ socketPath: socketPathOf(stateDir, port) }, "GET", "/health");
      expect(health.json.port).toBe(port);
    } finally {
      await rm(otherState, { recursive: true, force: true });
    }
  });

  it("does not exit while running with a long idle limit", () => {
    expect(exits).toBe(0);
  });
});

describe("page build", () => {
  it("bundles one mermaid for the app and the vendored Mermaiden", async () => {
    const out = await shortStateDir();
    try {
      const { moduleIds, assets } = await buildPage(join(out, "page"));
      expect(assets.has("/index.html")).toBe(true);
      expect(moduleIds.length).toBeGreaterThan(0);
      // The vendored Mermaiden takes mermaid as a peer dependency, so every mermaid module must
      // come from one package root inside the skill.
      const roots = new Set(
        moduleIds.filter((id) => /\/mermaid\/dist\//.test(id)).map((id) => id.replace(/\/mermaid\/dist\/.*/, "")),
      );
      expect(roots.size).toBe(1);
      expect([...roots][0]!.startsWith(join(SKILL_DIR, "node_modules"))).toBe(true);
    } finally {
      await rm(out, { recursive: true, force: true });
    }
  }, 120_000);
});

describe("server lifetime", () => {
  it("exits after the idle period, but not while a page stream is open", async () => {
    const stateDir = await shortStateDir();
    const port = await freePort();
    let exited = 0;
    const server = await startServer({ port, stateDir, idleMs: 200, onExit: () => exited++ });
    try {
      const stream = await openEvents(port);
      await stream.next("docs");
      await sleep(600);
      expect(exited).toBe(0);
      stream.close();
      const closedAt = Date.now();
      await waitFor(() => exited === 1, 3000, 10);
      expect(Date.now() - closedAt).toBeGreaterThanOrEqual(150);
      expect(existsSync(socketPathOf(stateDir, port))).toBe(false);
    } finally {
      await server.close();
      await rm(stateDir, { recursive: true, force: true });
    }
  }, 120_000);

  it("exits after idleMs with no streams and no requests", async () => {
    const stateDir = await shortStateDir();
    const port = await freePort();
    let exitedAt = 0;
    const startedAt = Date.now();
    const server = await startServer({ port, stateDir, idleMs: 200, onExit: () => (exitedAt = Date.now()) });
    const readyAt = Date.now();
    try {
      await waitFor(() => exitedAt > 0, 3000, 10);
      expect(exitedAt - readyAt).toBeGreaterThanOrEqual(190);
      expect(exitedAt).toBeGreaterThan(startedAt);
    } finally {
      await server.close();
      await rm(stateDir, { recursive: true, force: true });
    }
  }, 120_000);

  it("closes and removes its socket on POST /stop", async () => {
    const stateDir = await shortStateDir();
    const port = await freePort();
    let exited = 0;
    const server = await startServer({ port, stateDir, idleMs: 60_000, onExit: () => exited++ });
    const socketPath = socketPathOf(stateDir, port);
    try {
      expect(existsSync(socketPath)).toBe(true);
      expect((await http({ socketPath }, "POST", "/stop")).status).toBe(204);
      await waitFor(() => exited === 1);
      expect(existsSync(socketPath)).toBe(false);
      await expect(http({ port }, "GET", "/")).rejects.toThrow();
    } finally {
      await server.close();
      await rm(stateDir, { recursive: true, force: true });
    }
  }, 120_000);
});
