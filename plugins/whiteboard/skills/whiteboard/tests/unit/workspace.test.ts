import { chmod, mkdir, readFile, rename, rm, stat, symlink, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { docIdOf, revOf, type Rev } from "../../server/ids.ts";
import { STARTER, Workspace, type WorkspaceEvent } from "../../server/workspace.ts";
import { sleep, tempDir } from "../helpers.ts";

let dir: string;
let ws: Workspace;

beforeEach(async () => {
  dir = await tempDir();
  ws = new Workspace();
});

afterEach(async () => {
  ws.dispose();
  await rm(dir, { recursive: true, force: true });
});

function collect(): WorkspaceEvent[] {
  const events: WorkspaceEvent[] = [];
  ws.subscribe((e) => events.push(e));
  return events;
}

async function changedWithin(events: WorkspaceEvent[], ms = 2000) {
  const deadline = Date.now() + ms;
  while (Date.now() < deadline) {
    const found = events.filter((e) => e.kind === "changed");
    if (found.length > 0) return found;
    await sleep(20);
  }
  return [];
}

describe("resolve", () => {
  it("rejects a relative path", async () => {
    await expect(ws.resolve("rel/file.mmd")).rejects.toThrow(/absolute/);
  });

  it("gives two spellings of one file the same real path and id", async () => {
    await mkdir(join(dir, "real"));
    await writeFile(join(dir, "real", "a.mmd"), "flowchart LR\n");
    await symlink(join(dir, "real"), join(dir, "link"));
    const direct = await ws.resolve(join(dir, "real", "a.mmd"));
    const viaLink = await ws.resolve(join(dir, "link", "a.mmd"));
    const dotted = await ws.resolve(`${dir}/real/./../real/a.mmd`);
    expect(viaLink).toBe(direct);
    expect(dotted).toBe(direct);
    expect(docIdOf(viaLink)).toBe(docIdOf(direct));
  });
});

describe("read", () => {
  it("returns rev null for a missing file", async () => {
    expect(await ws.read(join(dir, "nope.mmd"))).toEqual({ rev: null });
  });

  it("refuses a directory, a file over 2 MB, and invalid UTF-8 with distinct messages", async () => {
    await mkdir(join(dir, "d"));
    await writeFile(join(dir, "big.mmd"), Buffer.alloc(2 * 1024 * 1024 + 1, 0x61));
    await writeFile(join(dir, "bad.mmd"), Buffer.from([0x66, 0xff, 0xfe]));
    await expect(ws.read(join(dir, "d"))).rejects.toThrow(/not a regular file/);
    await expect(ws.read(join(dir, "big.mmd"))).rejects.toThrow(/larger than 2 MB/);
    await expect(ws.read(join(dir, "bad.mmd"))).rejects.toThrow(/not valid UTF-8/);
  });
});

describe("open", () => {
  it("refuses a missing file without create", async () => {
    await expect(ws.open(join(dir, "missing.mmd"), { create: false })).rejects.toThrow(/no such file/);
  });

  it("creates the directory and starter diagram with create, and reports opened once", async () => {
    const path = join(dir, "new", "sub", "flow.mmd");
    const first = await ws.open(path, { create: true });
    expect(first.opened).toBe(true);
    expect(first.doc.name).toBe("flow.mmd");
    expect(await readFile(path, "utf8")).toBe(STARTER);
    const second = await ws.open(path, { create: true });
    expect(second.opened).toBe(false);
    expect(second.doc).toEqual(first.doc);
    expect(ws.docs()).toHaveLength(1);
  });
});

describe("write", () => {
  it("succeeds with the current rev, writes the text exactly, and keeps the file mode", async () => {
    const path = join(dir, "a.mmd");
    await writeFile(path, "flowchart LR\n  A\n");
    await chmod(path, 0o640);
    const disk = await ws.read(path);
    if (disk.rev === null) throw new Error("expected file");
    const text = "flowchart TD\n  X --> Y";
    const result = await ws.write(path, text, disk.rev);
    expect(result).toEqual({ ok: true, rev: revOf(text) });
    expect(await readFile(path, "utf8")).toBe(text);
    expect((await stat(path)).mode & 0o777).toBe(0o640);
  });

  it("refuses a stale rev and leaves the file unchanged", async () => {
    const path = join(dir, "a.mmd");
    await writeFile(path, "one");
    const stale = revOf("zero");
    const result = await ws.write(path, "two", stale);
    expect(result).toEqual({ ok: false, current: { rev: revOf("one"), text: "one" } });
    expect(await readFile(path, "utf8")).toBe("one");
  });

  it("creates a missing file with base null, and refuses when the file exists", async () => {
    const path = join(dir, "deep", "c.mmd");
    expect(await ws.write(path, "made", null)).toEqual({ ok: true, rev: revOf("made") });
    expect(await readFile(path, "utf8")).toBe("made");
    const again = await ws.write(path, "other", null);
    expect(again.ok).toBe(false);
    expect(await readFile(path, "utf8")).toBe("made");
  });
});

describe("watching", () => {
  async function opened() {
    const path = join(dir, "w.mmd");
    await writeFile(path, "start");
    const { doc } = await ws.open(path, { create: false });
    await sleep(150); // Let the directory watcher settle.
    return { path, doc };
  }

  it("reports an external writeFile once", async () => {
    const { path, doc } = await opened();
    const events = collect();
    await writeFile(path, "external");
    const changed = await changedWithin(events);
    await sleep(200);
    expect(events.filter((e) => e.kind === "changed")).toEqual([{ kind: "changed", id: doc.id, rev: revOf("external") }]);
    expect(changed).toHaveLength(1);
  });

  it("reports an external rename-replace once", async () => {
    const { path, doc } = await opened();
    const events = collect();
    await writeFile(join(dir, ".tmp-replace"), "replaced");
    await rename(join(dir, ".tmp-replace"), path);
    await changedWithin(events);
    await sleep(200);
    expect(events.filter((e) => e.kind === "changed")).toEqual([{ kind: "changed", id: doc.id, rev: revOf("replaced") }]);
  });

  it("reports a deletion and a recreation once each", async () => {
    const { path, doc } = await opened();
    const events = collect();
    await rm(path);
    await changedWithin(events);
    await sleep(200);
    expect(events.filter((e) => e.kind === "changed")).toEqual([{ kind: "changed", id: doc.id, rev: null }]);
    events.length = 0;
    await writeFile(path, "back");
    await changedWithin(events);
    await sleep(200);
    expect(events.filter((e) => e.kind === "changed")).toEqual([{ kind: "changed", id: doc.id, rev: revOf("back") }]);
  });

  it("reports nothing when identical content is rewritten", async () => {
    const { path } = await opened();
    const events = collect();
    await writeFile(path, "start");
    await sleep(600);
    expect(events.filter((e) => e.kind === "changed")).toEqual([]);
  });

  it("reports writes made through the workspace", async () => {
    const { path, doc } = await opened();
    const events = collect();
    await ws.write(path, "via ws", revOf("start") as Rev);
    await changedWithin(events);
    expect(events.filter((e) => e.kind === "changed")).toEqual([{ kind: "changed", id: doc.id, rev: revOf("via ws") }]);
  });
});

describe("close", () => {
  it("removes the doc and closes the directory watcher with the last doc in it", async () => {
    await writeFile(join(dir, "a.mmd"), "a");
    await writeFile(join(dir, "b.mmd"), "b");
    await mkdir(join(dir, "other"));
    await writeFile(join(dir, "other", "c.mmd"), "c");
    const a = await ws.open(join(dir, "a.mmd"), { create: false });
    const b = await ws.open(join(dir, "b.mmd"), { create: false });
    const c = await ws.open(join(dir, "other", "c.mmd"), { create: false });
    expect(ws.watcherCount()).toBe(2);
    const events = collect();
    ws.close(a.doc.id);
    expect(ws.doc(a.doc.id)).toBeUndefined();
    expect(ws.watcherCount()).toBe(2);
    expect(events).toEqual([{ kind: "docs", docs: [b.doc, c.doc] }]);
    ws.close(b.doc.id);
    expect(ws.watcherCount()).toBe(1);
    ws.close(c.doc.id);
    expect(ws.watcherCount()).toBe(0);
    expect(ws.docs()).toEqual([]);
  });
});
