// Locations and markers shared by the server and the CLI. Imports only Node built-ins, so the CLI
// can load it before dependencies are installed.
import { tmpdir } from "node:os";
import { join } from "node:path";

/** Response header set while the page is being built, so starting clients can recognize us. */
export const STARTING_HEADER = "x-whiteboard-starting";
export const DEFAULT_PORT = 5179;

export function defaultStateDir(): string {
  return process.env["WHITEBOARD_STATE_DIR"] || join(process.env["TMPDIR"] || tmpdir() || "/tmp", "my-whiteboard");
}

export function portFromEnv(): number {
  const raw = process.env["WHITEBOARD_PORT"];
  const port = raw ? Number(raw) : DEFAULT_PORT;
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error(`invalid WHITEBOARD_PORT: ${raw}`);
  return port;
}

export function portDir(stateDir: string, port: number): string {
  return join(stateDir, String(port));
}

export function socketPath(stateDir: string, port: number): string {
  return join(portDir(stateDir, port), "control.sock");
}
