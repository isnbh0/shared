import { readFile, rm, writeFile } from "node:fs/promises";
import { createServer, type Server } from "node:http";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { revOf } from "../../server/ids.ts";
import { controlRoutes, Hub, pageRoutes, type Asset } from "../../server/routes.ts";
import { Workspace } from "../../server/workspace.ts";
import { http, openEvents, shortStateDir, tempDir, waitFor } from "../helpers.ts";

let dir: string;
let sockDir: string;
let ws: Workspace;
let hub: Hub;
let page: Server;
let control: Server;
let port: number;
let socketPath: string;

beforeEach(async () => {
  dir = await tempDir();
  sockDir = await shortStateDir();
  socketPath = join(sockDir, "c.sock");
  ws = new Workspace();
  hub = new Hub(ws);
  const assets = new Map<string, Asset>([
    ["/index.html", { body: Buffer.from("<!doctype html><p>page</p>"), type: "text/html; charset=utf-8" }],
    ["/x.js", { body: Buffer.from("export {}"), type: "text/javascript; charset=utf-8" }],
  ]);
  page = createServer();
  await new Promise<void>((r) => page.listen(0, "127.0.0.1", r));
  const address = page.address();
  port = typeof address === "object" && address ? address.port : 0;
  page.on("request", pageRoutes(ws, { port, assets, hub }));
  control = createServer(controlRoutes(ws, { port, hub, stop: () => {} }));
  await new Promise<void>((r) => control.listen(socketPath, r));
});

afterEach(async () => {
  hub.close();
  ws.dispose();
  page.closeAllConnections();
  await Promise.all([new Promise((r) => page.close(r)), new Promise((r) => control.close(r))]);
  await rm(dir, { recursive: true, force: true });
  await rm(sockDir, { recursive: true, force: true });
});

const ctl = (method: string, path: string, body?: unknown) => http({ socketPath }, method, path, { body });
const pg = (method: string, path: string, options: Parameters<typeof http>[3] = {}) =>
  http({ port }, method, path, options);

async function openFile(name: string, text = "flowchart LR\n  A --> B\n") {
  const path = join(dir, name);
  await writeFile(path, text);
  const reply = await ctl("POST", "/open", { path, create: false, focus: false });
  expect(reply.status).toBe(200);
  return { path, id: reply.json.doc.id as string };
}

describe("page channel", () => {
  it("refuses a wrong Host or a foreign Origin, for API routes and assets alike", async () => {
    for (const path of ["/api/docs", "/x.js", "/"]) {
      expect((await pg("GET", path, { headers: { Host: `localhost:${port}` } })).status).toBe(403);
      expect((await pg("GET", path, { headers: { Origin: "http://evil.test" } })).status).toBe(403);
    }
    expect((await pg("GET", "/api/docs", { headers: { Origin: `http://127.0.0.1:${port}` } })).status).toBe(200);
  });

  it("serves only the asset table and fixed routes", async () => {
    const asset = await pg("GET", "/x.js");
    expect(asset.status).toBe(200);
    expect(asset.text).toBe("export {}");
    const index = await pg("GET", "/");
    expect(index.status).toBe(200);
    expect(index.headers["cache-control"]).toBe("no-store");
    for (const path of ["/@fs/etc/hosts", "/../package.json", "/api/open", "/package.json"]) {
      expect((await pg("GET", path)).status, path).toBe(404);
    }
  });

  it("answers 404 for an unopened or malformed id", async () => {
    expect((await pg("GET", "/api/docs/0123456789ab")).status).toBe(404);
    expect((await pg("GET", "/api/docs/not-an-id")).status).toBe(404);
  });

  it("returns a document and its disk version", async () => {
    const { id, path } = await openFile("a.mmd", "flowchart LR\n");
    const reply = await pg("GET", `/api/docs/${id}`);
    expect(reply.status).toBe(200);
    expect(reply.json).toEqual({
      doc: { id, name: "a.mmd", path },
      disk: { rev: revOf("flowchart LR\n"), text: "flowchart LR\n" },
    });
  });

  it("refuses a PUT without a rev or with a malformed one, leaving the file alone", async () => {
    const { id, path } = await openFile("a.mmd", "orig");
    expect((await pg("PUT", `/api/docs/${id}`, { body: { text: "new" } })).status).toBe(400);
    expect((await pg("PUT", `/api/docs/${id}`, { body: { text: "new", rev: "xyz" } })).status).toBe(400);
    expect((await pg("PUT", `/api/docs/${id}`, { rawBody: "{not json" })).status).toBe(400);
    expect(await readFile(path, "utf8")).toBe("orig");
  });

  it("compares and swaps on PUT", async () => {
    const { id, path } = await openFile("a.mmd", "orig");
    const ok = await pg("PUT", `/api/docs/${id}`, { body: { text: "next", rev: revOf("orig") } });
    expect(ok.status).toBe(200);
    expect(ok.json).toEqual({ rev: revOf("next") });
    const stale = await pg("PUT", `/api/docs/${id}`, { body: { text: "again", rev: revOf("orig") } });
    expect(stale.status).toBe(409);
    expect(stale.json).toEqual({ current: { rev: revOf("next"), text: "next" } });
    expect(await readFile(path, "utf8")).toBe("next");
  });

  it("closes a document on DELETE", async () => {
    const { id } = await openFile("a.mmd");
    expect((await pg("DELETE", `/api/docs/${id}`)).status).toBe(204);
    expect((await pg("GET", "/api/docs")).json).toEqual({ docs: [] });
  });

  it("streams docs on connect, focus after a focusing open, and changed after an external edit", async () => {
    const { path, id } = await openFile("a.mmd");
    const stream = await openEvents(port);
    try {
      const first = await stream.next("docs");
      expect(first.data.docs.map((d: { id: string }) => d.id)).toEqual([id]);
      await ctl("POST", "/open", { path, create: false, focus: true });
      expect((await stream.next("focus")).data).toEqual({ id });
      await new Promise((r) => setTimeout(r, 150));
      await writeFile(path, "changed text");
      expect((await stream.next("changed")).data).toEqual({ id, rev: revOf("changed text") });
    } finally {
      stream.close();
    }
  });
});

describe("control channel", () => {
  it("refuses a relative path", async () => {
    for (const route of ["/open", "/read", "/close"]) {
      const reply = await ctl("POST", route, { path: "rel/a.mmd", create: true, focus: false });
      expect(reply.status, route).toBe(400);
    }
    expect((await ctl("POST", "/write", { path: "rel/a.mmd", text: "x", rev: null })).status).toBe(400);
  });

  it("reads and writes a file that is not open, leaving the open set empty", async () => {
    const path = join(dir, "free.mmd");
    await writeFile(path, "one");
    expect((await ctl("POST", "/read", { path })).json).toEqual({ disk: { rev: revOf("one"), text: "one" } });
    const write = await ctl("POST", "/write", { path, text: "two", rev: revOf("one") });
    expect(write.status).toBe(200);
    expect(write.json).toEqual({ rev: revOf("two") });
    expect(await readFile(path, "utf8")).toBe("two");
    expect((await ctl("GET", "/docs")).json).toEqual({ docs: [] });
  });

  it("answers 204 when closing a file that is not open", async () => {
    expect((await ctl("POST", "/close", { path: join(dir, "never.mmd") })).status).toBe(204);
  });

  it("refuses a write without a rev", async () => {
    expect((await ctl("POST", "/write", { path: join(dir, "x.mmd"), text: "x" })).status).toBe(400);
  });

  it("counts open page event streams", async () => {
    expect((await ctl("GET", "/health")).json).toMatchObject({ port, pages: 0 });
    const a = await openEvents(port);
    const b = await openEvents(port);
    await a.next("docs");
    await b.next("docs");
    expect((await ctl("GET", "/health")).json.pages).toBe(2);
    a.close();
    await waitFor(async () => (await ctl("GET", "/health")).json.pages === 1);
    b.close();
    await waitFor(async () => (await ctl("GET", "/health")).json.pages === 0);
  });
});
