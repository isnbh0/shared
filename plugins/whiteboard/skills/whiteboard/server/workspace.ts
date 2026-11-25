// The only code that reads, writes, creates, or watches files, and the only code that derives
// document IDs. Routes are thin tables onto this module.
import { randomBytes } from "node:crypto";
import { watch, type FSWatcher } from "node:fs";
import { chmod, mkdir, readFile, realpath, rename, rm, stat, writeFile } from "node:fs/promises";
import { basename, dirname, isAbsolute, join } from "node:path";
import { docIdOf, revOf, type DocId, type Rev } from "./ids.ts";

export type RealPath = string & { readonly __brand: "RealPath" };
export type Disk = { rev: Rev; text: string } | { rev: null };
export type Doc = { id: DocId; name: string; path: RealPath };
export type WriteResult = { ok: true; rev: Rev } | { ok: false; current: Disk };
export type WorkspaceEvent =
  | { kind: "docs"; docs: Doc[] }
  | { kind: "changed"; id: DocId; rev: Rev | null };

/** `refused`: the request cannot be honored (400). `unknown`: no such open document (404). */
export class WorkspaceError extends Error {
  readonly kind: "refused" | "unknown";
  constructor(kind: "refused" | "unknown", message: string) {
    super(message);
    this.kind = kind;
  }
}

/** Written inside the serialized section, immediately before a write's rename. Test hook. */
export type WriteAudit = { path: RealPath; base: Rev | null; replaced: Rev | null; rev: Rev };

export const MAX_FILE_BYTES = 2 * 1024 * 1024;
export const STARTER = "flowchart LR\n  A[Start] --> B[Next]\n";
const WATCH_DEBOUNCE_MS = 40;

const utf8 = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true });

function isCode(error: unknown, ...codes: string[]): boolean {
  return error instanceof Error && codes.includes((error as NodeJS.ErrnoException).code ?? "");
}

async function readReal(real: RealPath): Promise<Disk> {
  let info;
  try {
    info = await stat(real);
  } catch (error) {
    if (isCode(error, "ENOENT", "ENOTDIR")) return { rev: null };
    throw error;
  }
  if (!info.isFile()) throw new WorkspaceError("refused", `not a regular file: ${real}`);
  if (info.size > MAX_FILE_BYTES) throw new WorkspaceError("refused", `file is larger than 2 MB: ${real}`);
  let bytes;
  try {
    bytes = await readFile(real);
  } catch (error) {
    if (isCode(error, "ENOENT", "ENOTDIR")) return { rev: null };
    throw error;
  }
  if (bytes.byteLength > MAX_FILE_BYTES) throw new WorkspaceError("refused", `file is larger than 2 MB: ${real}`);
  let text;
  try {
    text = utf8.decode(bytes);
  } catch {
    throw new WorkspaceError("refused", `file is not valid UTF-8: ${real}`);
  }
  return { rev: revOf(text), text };
}

/**
 * Real path of `path`: the realpath of an existing file, otherwise the realpath of the nearest
 * existing ancestor plus the missing segments. `missingDepth` counts those missing segments.
 */
async function realish(path: string): Promise<{ real: RealPath; missingDepth: number }> {
  if (!isAbsolute(path)) throw new WorkspaceError("refused", `path must be absolute: ${path}`);
  const missing: string[] = [];
  let current = path;
  for (;;) {
    try {
      const found = await realpath(current);
      return { real: join(found, ...missing.reverse()) as RealPath, missingDepth: missing.length };
    } catch (error) {
      if (!isCode(error, "ENOENT", "ENOTDIR")) throw error;
      const parent = dirname(current);
      if (parent === current) throw error;
      missing.push(basename(current));
      current = parent;
    }
  }
}

type DirWatch = { watcher: FSWatcher; ids: Set<DocId> };

export class Workspace {
  readonly #docs = new Map<DocId, Doc>();
  readonly #lastRev = new Map<DocId, Rev | null>();
  readonly #dirs = new Map<string, DirWatch>();
  readonly #timers = new Map<DocId, NodeJS.Timeout>();
  readonly #locks = new Map<string, Promise<unknown>>();
  readonly #listeners = new Set<(event: WorkspaceEvent) => void>();
  readonly #audit: ((entry: WriteAudit) => void) | undefined;
  #disposed = false;

  constructor(options: { audit?: (entry: WriteAudit) => void } = {}) {
    this.#audit = options.audit;
  }

  /** Rejects relative paths and paths whose parent directory does not exist. */
  async resolve(path: string): Promise<RealPath> {
    const { real, missingDepth } = await realish(path);
    if (missingDepth > 1) throw new WorkspaceError("refused", `directory does not exist: ${dirname(path)}`);
    return real;
  }

  async read(path: string): Promise<Disk> {
    const { real } = await realish(path);
    return readReal(real);
  }

  async write(path: string, text: string, base: Rev | null): Promise<WriteResult> {
    const { real } = await realish(path);
    return this.#serialize(real, async () => {
      const current = await readReal(real);
      if (current.rev !== base) return { ok: false, current };
      const dir = dirname(real);
      let mode: number | undefined;
      if (current.rev === null) await mkdir(dir, { recursive: true });
      else mode = (await stat(real)).mode & 0o7777;
      const tmp = join(dir, `.${basename(real)}.wb-${randomBytes(6).toString("hex")}.tmp`);
      try {
        await writeFile(tmp, text, { encoding: "utf8", flag: "wx" });
        if (mode !== undefined) await chmod(tmp, mode);
        const rev = revOf(text);
        if (this.#audit) this.#audit({ path: real, base, replaced: (await readReal(real)).rev, rev });
        await rename(tmp, real);
        return { ok: true, rev };
      } catch (error) {
        await rm(tmp, { force: true });
        throw error;
      }
    });
  }

  async open(path: string, options: { create: boolean }): Promise<{ doc: Doc; opened: boolean; created: boolean }> {
    let disk = await this.read(path);
    let created = false;
    if (disk.rev === null) {
      if (!options.create) throw new WorkspaceError("refused", `no such file: ${path}`);
      await this.write(path, STARTER, null);
      disk = await this.read(path);
      if (disk.rev === null) throw new WorkspaceError("refused", `could not create: ${path}`);
      created = true;
    }
    const real = await this.resolve(path);
    const id = docIdOf(real);
    const existing = this.#docs.get(id);
    if (existing) return { doc: existing, opened: false, created };
    const doc: Doc = { id, name: basename(real), path: real };
    this.#docs.set(id, doc);
    this.#lastRev.set(id, disk.rev);
    this.#watch(doc);
    this.#emit({ kind: "docs", docs: this.docs() });
    return { doc, opened: true, created };
  }

  docs(): Doc[] {
    return [...this.#docs.values()];
  }

  doc(id: DocId): Doc | undefined {
    return this.#docs.get(id);
  }

  /** The open document at `path`, if any. */
  async docAt(path: string): Promise<Doc | undefined> {
    const { real } = await realish(path);
    return this.#docs.get(docIdOf(real));
  }

  close(id: DocId): void {
    const doc = this.#docs.get(id);
    if (!doc) return;
    this.#docs.delete(id);
    this.#lastRev.delete(id);
    clearTimeout(this.#timers.get(id));
    this.#timers.delete(id);
    const dir = dirname(doc.path);
    const entry = this.#dirs.get(dir);
    if (entry) {
      entry.ids.delete(id);
      if (entry.ids.size === 0) {
        entry.watcher.close();
        this.#dirs.delete(dir);
      }
    }
    this.#emit({ kind: "docs", docs: this.docs() });
  }

  subscribe(listener: (event: WorkspaceEvent) => void): () => void {
    this.#listeners.add(listener);
    return () => this.#listeners.delete(listener);
  }

  /** Number of directory watchers, for tests. */
  watcherCount(): number {
    return this.#dirs.size;
  }

  dispose(): void {
    this.#disposed = true;
    for (const { watcher } of this.#dirs.values()) watcher.close();
    this.#dirs.clear();
    for (const timer of this.#timers.values()) clearTimeout(timer);
    this.#timers.clear();
    this.#listeners.clear();
  }

  #emit(event: WorkspaceEvent): void {
    for (const listener of this.#listeners) listener(event);
  }

  #serialize<T>(key: string, task: () => Promise<T>): Promise<T> {
    const previous = this.#locks.get(key) ?? Promise.resolve();
    const run = previous.then(task, task);
    const settled = run.catch(() => undefined);
    this.#locks.set(key, settled);
    void settled.then(() => {
      if (this.#locks.get(key) === settled) this.#locks.delete(key);
    });
    return run;
  }

  #watch(doc: Doc): void {
    const dir = dirname(doc.path);
    const existing = this.#dirs.get(dir);
    if (existing) {
      existing.ids.add(doc.id);
      return;
    }
    const watcher = watch(dir, { persistent: false }, (_event, filename) => {
      const entry = this.#dirs.get(dir);
      if (!entry) return;
      for (const id of entry.ids) {
        const target = this.#docs.get(id);
        if (target && (filename === null || filename === target.name)) this.#schedule(id);
      }
    });
    watcher.on("error", () => {
      // The directory went away. Documents stay open; their next read reports them missing.
      const entry = this.#dirs.get(dir);
      if (entry?.watcher === watcher) {
        for (const id of entry.ids) this.#schedule(id);
      }
    });
    this.#dirs.set(dir, { watcher, ids: new Set([doc.id]) });
  }

  #schedule(id: DocId): void {
    clearTimeout(this.#timers.get(id));
    this.#timers.set(
      id,
      setTimeout(() => {
        this.#timers.delete(id);
        void this.#check(id);
      }, WATCH_DEBOUNCE_MS),
    );
  }

  async #check(id: DocId): Promise<void> {
    const doc = this.#docs.get(id);
    if (!doc || this.#disposed) return;
    let rev: Rev | null;
    try {
      rev = (await readReal(doc.path)).rev;
    } catch {
      return; // Mid-replace or refused; the next event retries.
    }
    if (!this.#docs.has(id) || this.#lastRev.get(id) === rev) return;
    this.#lastRev.set(id, rev);
    this.#emit({ kind: "changed", id, rev });
  }
}
