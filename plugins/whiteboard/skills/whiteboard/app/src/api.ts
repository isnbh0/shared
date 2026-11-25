// The page's only boundary with the server. Every response is parsed into page types here, so
// the rest of the page works only with parsed values.

import type { Disk, Doc, DocId, Rev } from "./types.ts";

export type { Disk, Doc, DocId, Rev };
export type PutResult =
  | { kind: "ok"; rev: Rev }
  | { kind: "conflict"; current: Disk }
  | { kind: "gone" }
  | { kind: "failed"; message: string; retry: boolean };

export class NotOpenError extends Error {}

class MalformedError extends Error {}

function fail(what: string): never {
  throw new MalformedError(`malformed ${what} from the server`);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function parseDocId(value: unknown): DocId | undefined {
  return typeof value === "string" && /^[0-9a-f]{12}$/.test(value) ? (value as DocId) : undefined;
}

function parseRev(value: unknown): Rev | null {
  if (value === null) return null;
  if (typeof value === "string" && /^[0-9a-f]{16}$/.test(value)) return value as Rev;
  return fail("rev");
}

function parseDoc(value: unknown): Doc {
  if (!isRecord(value)) return fail("document");
  const id = parseDocId(value["id"]);
  const { name, path } = value;
  if (!id || typeof name !== "string" || typeof path !== "string") return fail("document");
  return { id, name, path };
}

function parseDocs(value: unknown): Doc[] {
  if (!isRecord(value) || !Array.isArray(value["docs"])) return fail("document list");
  return value["docs"].map(parseDoc);
}

function parseDisk(value: unknown): Disk {
  if (!isRecord(value)) return fail("disk version");
  const rev = parseRev(value["rev"]);
  if (rev === null) return { rev: null };
  const text = value["text"];
  if (typeof text !== "string") return fail("disk version");
  return { rev, text };
}

async function json(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return fail("response");
  }
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as unknown;
    if (isRecord(body) && typeof body["error"] === "string") return body["error"];
  } catch {
    // Fall through to the status text.
  }
  return `${response.status} ${response.statusText}`.trim();
}

export async function listDocs(): Promise<Doc[]> {
  const response = await fetch("/api/docs");
  if (!response.ok) throw new Error(await errorMessage(response));
  return parseDocs(await json(response));
}

export async function readDoc(id: DocId): Promise<{ doc: Doc; disk: Disk }> {
  const response = await fetch(`/api/docs/${id}`, { cache: "no-store" });
  if (response.status === 404) throw new NotOpenError("this document is not open");
  if (!response.ok) throw new Error(await errorMessage(response));
  const body = await json(response);
  if (!isRecord(body)) return fail("document");
  return { doc: parseDoc(body["doc"]), disk: parseDisk(body["disk"]) };
}

export async function putDoc(id: DocId, text: string, rev: Rev | null): Promise<PutResult> {
  let response: Response;
  try {
    response = await fetch(`/api/docs/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, rev }),
    });
  } catch (error) {
    return { kind: "failed", message: error instanceof Error ? error.message : String(error), retry: true };
  }
  if (response.status === 200) {
    const body = await json(response);
    if (!isRecord(body)) return fail("save result");
    const saved = parseRev(body["rev"]);
    if (saved === null) return fail("save result");
    return { kind: "ok", rev: saved };
  }
  if (response.status === 409) {
    const body = await json(response);
    if (!isRecord(body)) return fail("conflict");
    return { kind: "conflict", current: parseDisk(body["current"]) };
  }
  if (response.status === 404) return { kind: "gone" };
  return { kind: "failed", message: await errorMessage(response), retry: response.status >= 500 };
}

export async function closeDoc(id: DocId): Promise<void> {
  const response = await fetch(`/api/docs/${id}`, { method: "DELETE" });
  if (!response.ok && response.status !== 404) throw new Error(await errorMessage(response));
}

export type ServerEvents = {
  /** The stream (re)connected. The server's initial `docs` event follows. */
  connected(): void;
  docs(docs: Doc[]): void;
  changed(id: DocId, rev: Rev | null): void;
  focus(id: DocId): void;
};

/** Subscribes to the server's event stream. EventSource reconnects on its own. */
export function connectEvents(handlers: ServerEvents): () => void {
  const source = new EventSource("/api/events");
  const parse = (event: MessageEvent<string>): unknown => {
    try {
      return JSON.parse(event.data) as unknown;
    } catch {
      return undefined;
    }
  };
  const report = (error: unknown) => console.error("whiteboard event ignored:", error);
  source.addEventListener("open", () => handlers.connected());
  source.addEventListener("docs", (event) => {
    try {
      handlers.docs(parseDocs(parse(event)));
    } catch (error) {
      report(error);
    }
  });
  source.addEventListener("changed", (event) => {
    try {
      const body = parse(event);
      const id = isRecord(body) ? parseDocId(body["id"]) : undefined;
      if (!isRecord(body) || !id) return fail("changed event");
      handlers.changed(id, parseRev(body["rev"]));
    } catch (error) {
      report(error);
    }
  });
  source.addEventListener("focus", (event) => {
    const body = parse(event);
    const id = isRecord(body) ? parseDocId(body["id"]) : undefined;
    if (id) handlers.focus(id);
    else report(new MalformedError("malformed focus event"));
  });
  return () => source.close();
}
