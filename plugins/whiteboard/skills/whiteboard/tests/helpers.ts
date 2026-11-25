// Shared test helpers: temporary directories, free ports, HTTP over TCP or a Unix socket, and an
// event-stream reader, and a `wb` runner.
import { spawn } from "node:child_process";
import { mkdtemp, realpath } from "node:fs/promises";
import { request, type IncomingMessage } from "node:http";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

export async function tempDir(prefix = "wb-test-"): Promise<string> {
  return realpath(await mkdtemp(join(tmpdir(), prefix)));
}

/** A short state directory, so control socket paths stay under the 104-byte limit. */
export async function shortStateDir(): Promise<string> {
  return realpath(await mkdtemp("/tmp/wbs-"));
}

export function freePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      server.close(() => resolve(port));
    });
  });
}

export type Target = { socketPath: string } | { port: number };
export type Reply = { status: number; headers: IncomingMessage["headers"]; text: string; json: any };

export function http(
  target: Target,
  method: string,
  path: string,
  options: { body?: unknown; rawBody?: string; headers?: Record<string, string> } = {},
): Promise<Reply> {
  return new Promise((resolve, reject) => {
    const payload =
      options.rawBody !== undefined
        ? Buffer.from(options.rawBody)
        : options.body !== undefined
          ? Buffer.from(JSON.stringify(options.body))
          : undefined;
    const headers: Record<string, string | number> = { ...options.headers };
    if ("port" in target && !Object.keys(headers).some((h) => h.toLowerCase() === "host")) {
      headers["Host"] = `127.0.0.1:${target.port}`;
    }
    if (payload) {
      headers["Content-Type"] = "application/json";
      headers["Content-Length"] = payload.byteLength;
    }
    const req = request(
      "socketPath" in target
        ? { socketPath: target.socketPath, method, path, headers }
        : { host: "127.0.0.1", port: target.port, method, path, headers },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (c: Buffer) => chunks.push(c));
        res.on("end", () => {
          const text = Buffer.concat(chunks).toString("utf8");
          let json: unknown;
          try {
            json = text ? JSON.parse(text) : undefined;
          } catch {
            json = undefined;
          }
          resolve({ status: res.statusCode ?? 0, headers: res.headers, text, json });
        });
      },
    );
    req.on("error", reject);
    req.end(payload);
  });
}

export type SseEvent = { event: string; data: any };

/** Opens an event stream on the page channel and collects its events. */
export function openEvents(port: number): Promise<{
  events: SseEvent[];
  next: (event: string, predicate?: (data: any) => boolean, timeoutMs?: number) => Promise<SseEvent>;
  close: () => void;
}> {
  return new Promise((resolve, reject) => {
    const events: SseEvent[] = [];
    const waiters: Array<() => void> = [];
    const req = request(
      { host: "127.0.0.1", port, path: "/api/events", headers: { Host: `127.0.0.1:${port}` } },
      (res) => {
        let buffer = "";
        res.setEncoding("utf8");
        res.on("data", (chunk: string) => {
          buffer += chunk;
          let at;
          while ((at = buffer.indexOf("\n\n")) >= 0) {
            const block = buffer.slice(0, at);
            buffer = buffer.slice(at + 2);
            let event = "message";
            let data = "";
            for (const line of block.split("\n")) {
              if (line.startsWith("event: ")) event = line.slice(7);
              else if (line.startsWith("data: ")) data += line.slice(6);
            }
            if (data) events.push({ event, data: JSON.parse(data) });
            for (const w of waiters.splice(0)) w();
          }
        });
        let cursor = 0;
        resolve({
          events,
          close: () => req.destroy(),
          next: (event, predicate = () => true, timeoutMs = 3000) =>
            new Promise((ok, fail) => {
              const timer = setTimeout(() => fail(new Error(`no ${event} event within ${timeoutMs} ms`)), timeoutMs);
              const check = () => {
                while (cursor < events.length) {
                  const e = events[cursor++]!;
                  if (e.event === event && predicate(e.data)) {
                    clearTimeout(timer);
                    ok(e);
                    return;
                  }
                }
                waiters.push(check);
              };
              check();
            }),
        });
      },
    );
    req.on("error", reject);
    req.end();
  });
}

export const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function waitFor<T>(probe: () => T | Promise<T>, timeoutMs = 3000, stepMs = 25): Promise<T> {
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    const value = await probe();
    if (value) return value;
    if (Date.now() > deadline) throw new Error("condition not met in time");
    await sleep(stepMs);
  }
}

const WB = resolve(import.meta.dirname, "..", "wb");

export type Run = { code: number; stdout: string; stderr: string };

/** Runs the `wb` launcher with extra environment, collecting its output. */
export function wb(args: string[], env: Record<string, string>, options: { cwd?: string; input?: string } = {}): Promise<Run> {
  return new Promise((ok, fail) => {
    const child = spawn(WB, args, { cwd: options.cwd, env: { ...process.env, ...env } });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (c: Buffer) => (stdout += c.toString()));
    child.stderr.on("data", (c: Buffer) => (stderr += c.toString()));
    child.on("error", fail);
    child.on("close", (code) => ok({ code: code ?? -1, stdout, stderr }));
    child.stdin.end(options.input ?? "");
  });
}
