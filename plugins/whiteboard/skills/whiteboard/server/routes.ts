// Two route tables over one Workspace: the page channel (TCP, fixed routes by document ID) and the
// control channel (Unix socket, routes by absolute path). They share body parsing, wire parsing,
// error mapping, and the event stream.
import type { IncomingMessage, ServerResponse } from "node:http";
import { parseDocId, parseRev, type DocId, type Rev } from "./ids.ts";
import { WorkspaceError, type Doc, type Workspace } from "./workspace.ts";

export type Handler = (req: IncomingMessage, res: ServerResponse) => void;
export type Asset = { body: Buffer; type: string };

const MAX_BODY_BYTES = 3 * 1024 * 1024;

class HttpError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function sendJson(res: ServerResponse, status: number, body: unknown): void {
  const text = JSON.stringify(body);
  res.writeHead(status, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
  res.end(text);
}

function sendEmpty(res: ServerResponse, status: number): void {
  res.writeHead(status);
  res.end();
}

async function readJson(req: IncomingMessage): Promise<Record<string, unknown>> {
  const chunks: Buffer[] = [];
  let size = 0;
  for await (const chunk of req as AsyncIterable<Buffer>) {
    size += chunk.byteLength;
    if (size > MAX_BODY_BYTES) throw new HttpError(413, "request body is larger than 3 MB");
    chunks.push(chunk);
  }
  let value: unknown;
  try {
    value = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch {
    throw new HttpError(400, "request body is not valid JSON");
  }
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new HttpError(400, "request body must be a JSON object");
  }
  return value as Record<string, unknown>;
}

function stringField(body: Record<string, unknown>, key: string): string {
  const value = body[key];
  if (typeof value !== "string") throw new HttpError(400, `"${key}" must be a string`);
  return value;
}

function booleanField(body: Record<string, unknown>, key: string): boolean {
  const value = body[key];
  if (typeof value !== "boolean") throw new HttpError(400, `"${key}" must be a boolean`);
  return value;
}

function revField(body: Record<string, unknown>): Rev | null {
  const parsed = parseRev(body["rev"]);
  if (!parsed.ok) throw new HttpError(400, `"rev" is required: 16 hex characters, or null`);
  return parsed.value;
}

/** Runs a route, mapping thrown errors to statuses: refusals 400, unknown docs 404. */
function route(res: ServerResponse, run: () => Promise<void>): void {
  run().catch((error: unknown) => {
    if (res.headersSent) {
      res.destroy();
      return;
    }
    if (error instanceof HttpError) sendJson(res, error.status, { error: error.message });
    else if (error instanceof WorkspaceError) sendJson(res, error.kind === "unknown" ? 404 : 400, { error: error.message });
    else sendJson(res, 500, { error: error instanceof Error ? error.message : String(error) });
  });
}

/** Page event streams. Owns the broadcast of workspace events and `focus`. */
export class Hub {
  readonly #streams = new Set<ServerResponse>();
  readonly #workspace: Workspace;
  readonly #onCount: (count: number) => void;
  readonly #unsubscribe: () => void;

  constructor(workspace: Workspace, options: { onCountChange?: (count: number) => void } = {}) {
    this.#workspace = workspace;
    this.#onCount = options.onCountChange ?? (() => {});
    this.#unsubscribe = workspace.subscribe((event) => {
      if (event.kind === "docs") this.#broadcast("docs", { docs: event.docs });
      else this.#broadcast("changed", { id: event.id, rev: event.rev });
    });
  }

  count(): number {
    return this.#streams.size;
  }

  focus(id: DocId): void {
    this.#broadcast("focus", { id });
  }

  attach(req: IncomingMessage, res: ServerResponse): void {
    res.writeHead(200, {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-store",
      Connection: "keep-alive",
    });
    res.write(": connected\n\n");
    this.#send(res, "docs", { docs: this.#workspace.docs() });
    this.#streams.add(res);
    this.#onCount(this.#streams.size);
    const keepAlive = setInterval(() => res.write(": ping\n\n"), 25_000);
    const detach = () => {
      clearInterval(keepAlive);
      if (this.#streams.delete(res)) this.#onCount(this.#streams.size);
    };
    req.on("close", detach);
    res.on("close", detach);
  }

  close(): void {
    this.#unsubscribe();
    for (const res of this.#streams) res.end();
    this.#streams.clear();
  }

  #send(res: ServerResponse, event: string, data: unknown): void {
    res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
  }

  #broadcast(event: string, data: unknown): void {
    for (const res of this.#streams) this.#send(res, event, data);
  }
}

function docOrThrow(workspace: Workspace, raw: string): Doc {
  const parsed = parseDocId(raw);
  const doc = parsed.ok ? workspace.doc(parsed.value) : undefined;
  if (!doc) throw new WorkspaceError("unknown", "this document is not open");
  return doc;
}

export function pageRoutes(
  workspace: Workspace,
  options: { port: number; assets: Map<string, Asset>; hub: Hub },
): Handler {
  const host = `127.0.0.1:${options.port}`;
  const origin = `http://${host}`;
  return (req, res) => {
    if (req.headers.host !== host || (req.headers.origin !== undefined && req.headers.origin !== origin)) {
      sendJson(res, 403, { error: "forbidden" });
      return;
    }
    const url = new URL(req.url ?? "/", origin);
    const pathname = url.pathname;
    const method = req.method ?? "GET";

    if (pathname === "/api/docs" && method === "GET") {
      sendJson(res, 200, { docs: workspace.docs() });
      return;
    }
    if (pathname === "/api/events" && method === "GET") {
      options.hub.attach(req, res);
      return;
    }
    const match = /^\/api\/docs\/([^/]+)$/.exec(pathname);
    if (match) {
      const raw = match[1] ?? "";
      route(res, async () => {
        const doc = docOrThrow(workspace, raw);
        if (method === "GET") {
          sendJson(res, 200, { doc, disk: await workspace.read(doc.path) });
        } else if (method === "PUT") {
          const body = await readJson(req);
          const text = stringField(body, "text");
          const rev = revField(body);
          const result = await workspace.write(doc.path, text, rev);
          if (result.ok) sendJson(res, 200, { rev: result.rev });
          else sendJson(res, 409, { current: result.current });
        } else if (method === "DELETE") {
          workspace.close(doc.id);
          sendEmpty(res, 204);
        } else {
          throw new HttpError(405, "method not allowed");
        }
      });
      return;
    }
    const asset = method === "GET" ? options.assets.get(pathname === "/" ? "/index.html" : pathname) : undefined;
    if (asset) {
      const headers: Record<string, string> = { "Content-Type": asset.type };
      if (pathname === "/" || pathname === "/index.html") headers["Cache-Control"] = "no-store";
      res.writeHead(200, headers);
      res.end(asset.body);
      return;
    }
    sendJson(res, 404, { error: "not found" });
  };
}

export function controlRoutes(
  workspace: Workspace,
  options: { port: number; hub: Hub; stop: () => void },
): Handler {
  return (req, res) => {
    const pathname = new URL(req.url ?? "/", "http://control").pathname;
    const method = req.method ?? "GET";
    route(res, async () => {
      if (method === "GET" && pathname === "/health") {
        sendJson(res, 200, { pid: process.pid, port: options.port, pages: options.hub.count() });
      } else if (method === "GET" && pathname === "/docs") {
        sendJson(res, 200, { docs: workspace.docs() });
      } else if (method === "POST" && pathname === "/open") {
        const body = await readJson(req);
        const path = stringField(body, "path");
        const create = booleanField(body, "create");
        const focus = booleanField(body, "focus");
        const { doc, opened } = await workspace.open(path, { create });
        if (focus) options.hub.focus(doc.id);
        sendJson(res, 200, { doc, opened, pages: options.hub.count() });
      } else if (method === "POST" && pathname === "/read") {
        const body = await readJson(req);
        sendJson(res, 200, { disk: await workspace.read(stringField(body, "path")) });
      } else if (method === "POST" && pathname === "/write") {
        const body = await readJson(req);
        const path = stringField(body, "path");
        const text = stringField(body, "text");
        const rev = revField(body);
        const result = await workspace.write(path, text, rev);
        if (result.ok) sendJson(res, 200, { rev: result.rev });
        else sendJson(res, 409, { current: result.current });
      } else if (method === "POST" && pathname === "/close") {
        const body = await readJson(req);
        const doc = await workspace.docAt(stringField(body, "path"));
        if (doc) workspace.close(doc.id);
        sendEmpty(res, 204);
      } else if (method === "POST" && pathname === "/stop") {
        res.on("finish", () => options.stop());
        sendEmpty(res, 204);
      } else {
        throw new HttpError(404, "not found");
      }
    });
  };
}
