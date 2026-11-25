// wb: the agent CLI for the whiteboard. Talks only to STATE/<port>/control.sock and starts the
// server on demand. Imports only Node built-ins until a command needs a dependency.
import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, openSync, readFileSync } from "node:fs";
import { request } from "node:http";
import { dirname, join, resolve } from "node:path";
import { defaultStateDir, portDir, portFromEnv, socketPath, STARTING_HEADER } from "../server/state.ts";

const SKILL_DIR = resolve(import.meta.dirname, "..");
const USAGE = `usage:
  wb open <path>                   add a tab (creating the file if missing) and switch pages to it
  wb ls                            list open files
  wb read <path>                   print the file; its rev goes to stderr
  wb write <path> --rev <rev|none> replace the file with stdin if it is still at <rev>
  wb close <path>                  remove a tab
  wb shot <path> [out.png]         screenshot the rendered file without changing anyone's page
  wb stop                          stop the server`;

type Disk = { rev: string; text: string } | { rev: null };
type Doc = { id: string; name: string; path: string };
type Reply = { status: number; body: any };

class CliError extends Error {
  readonly code: number;
  constructor(message: string, code = 1) {
    super(message);
    this.code = code;
  }
}

const port = portFromEnv();
const stateDir = defaultStateDir();
const sock = socketPath(stateDir, port);

function call(method: string, path: string, body?: unknown, timeoutMs = 30_000): Promise<Reply> {
  return new Promise((resolvePromise, reject) => {
    const payload = body === undefined ? undefined : Buffer.from(JSON.stringify(body), "utf8");
    const req = request(
      {
        socketPath: sock,
        method,
        path,
        headers: payload ? { "Content-Type": "application/json", "Content-Length": payload.byteLength } : {},
        timeout: timeoutMs,
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (c: Buffer) => chunks.push(c));
        res.on("end", () => {
          const text = Buffer.concat(chunks).toString("utf8");
          let parsed: unknown = undefined;
          if (text) {
            try {
              parsed = JSON.parse(text);
            } catch {
              parsed = { error: text };
            }
          }
          resolvePromise({ status: res.statusCode ?? 0, body: parsed });
        });
        res.on("error", reject);
      },
    );
    req.on("timeout", () => req.destroy(new Error("control request timed out")));
    req.on("error", reject);
    req.end(payload);
  });
}

async function healthy(): Promise<boolean> {
  try {
    const reply = await call("GET", "/health", undefined, 2_000);
    return reply.status === 200 && reply.body?.port === port;
  } catch {
    return false;
  }
}

/** True when a whiteboard server holds the TCP port and is still building its page. */
function portHeldByStartingServer(): Promise<boolean> {
  return new Promise((resolvePromise) => {
    const req = request(
      { host: "127.0.0.1", port, path: "/", headers: { Host: `127.0.0.1:${port}` }, timeout: 2_000 },
      (res) => {
        res.resume();
        resolvePromise(res.statusCode === 503 && res.headers[STARTING_HEADER] === "1");
      },
    );
    req.on("timeout", () => req.destroy());
    req.on("error", () => resolvePromise(false));
    req.end();
  });
}

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

function ensureDependencies(): void {
  if (!existsSync(join(SKILL_DIR, "node_modules", ".modules.yaml"))) {
    process.stderr.write("installing whiteboard dependencies…\n");
    const result = spawnSync("pnpm", ["install", "--frozen-lockfile"], {
      cwd: SKILL_DIR,
      stdio: ["ignore", process.stderr, process.stderr],
    });
    if (result.error || result.status !== 0) {
      throw new CliError(`pnpm install failed in ${SKILL_DIR}${result.error ? `: ${result.error.message}` : ""}`);
    }
  }
}

function logTail(logPath: string, lines = 20): string {
  try {
    return readFileSync(logPath, "utf8").trimEnd().split("\n").slice(-lines).join("\n");
  } catch {
    return "(no server log)";
  }
}

async function ensureServer(): Promise<void> {
  if (await healthy()) return;
  ensureDependencies();
  const dir = portDir(stateDir, port);
  mkdirSync(dir, { recursive: true });
  const logPath = join(dir, "server.log");
  process.stderr.write("starting whiteboard server…\n");
  const log = openSync(logPath, "a");
  const child = spawn(process.execPath, [join(SKILL_DIR, "server", "main.ts")], {
    cwd: SKILL_DIR,
    detached: true,
    stdio: ["ignore", log, log],
    env: process.env,
  });
  let exitedAt: number | undefined;
  child.on("exit", () => (exitedAt = Date.now()));
  child.unref();

  const deadline = Date.now() + 120_000;
  for (;;) {
    if (await healthy()) return;
    const now = Date.now();
    if (now > deadline) break;
    // The spawned server exited. Another start may have won the port and still be building.
    if (exitedAt !== undefined && now - exitedAt > 3_000 && !(await portHeldByStartingServer())) break;
    await delay(200);
  }
  throw new CliError(`the whiteboard server did not start. Last lines of ${logPath}:\n${logTail(logPath)}`);
}

function absolute(arg: string | undefined): string {
  if (!arg) throw new CliError(USAGE, 2);
  return resolve(process.cwd(), arg);
}

function fail(reply: Reply): never {
  throw new CliError(reply.body?.error ?? `unexpected response ${reply.status}`);
}

function readStdin(): Promise<string> {
  return new Promise((resolvePromise, reject) => {
    const chunks: Buffer[] = [];
    process.stdin.on("data", (c: Buffer) => chunks.push(c));
    process.stdin.on("end", () => resolvePromise(Buffer.concat(chunks).toString("utf8")));
    process.stdin.on("error", reject);
  });
}

function tabAddress(doc: Doc): string {
  return `http://127.0.0.1:${port}/#/${doc.id}/${encodeURIComponent(doc.name)}`;
}

async function main(argv: string[]): Promise<void> {
  const [command, ...rest] = argv;
  if (!command || command === "-h" || command === "--help" || command === "help") {
    process.stdout.write(USAGE + "\n");
    if (!command) process.exitCode = 2;
    return;
  }

  if (command === "stop") {
    if (!(await healthy())) {
      process.stdout.write("not running\n");
      return;
    }
    await call("POST", "/stop").catch(() => undefined);
    const deadline = Date.now() + 10_000;
    while (Date.now() < deadline) {
      if (!(await healthy())) return;
      await delay(100);
    }
    throw new CliError("the server did not stop within 10 s");
  }

  const known = ["open", "ls", "read", "write", "close", "shot"];
  if (!known.includes(command)) throw new CliError(USAGE, 2);

  // Validate arguments before starting anything.
  let path: string | undefined;
  let rev: string | null | undefined;
  let out: string | undefined;
  if (command !== "ls") {
    const positional = rest.filter((a, i) => !a.startsWith("--") && rest[i - 1] !== "--rev");
    path = absolute(positional[0]);
    if (command === "shot" && positional[1]) out = absolute(positional[1]);
    if (command === "write") {
      const at = rest.indexOf("--rev");
      const value = at >= 0 ? rest[at + 1] : undefined;
      if (!value) throw new CliError(`wb write requires --rev <rev> or --rev none\n${USAGE}`, 2);
      rev = value === "none" ? null : value;
    }
  }

  await ensureServer();

  switch (command) {
    case "open": {
      const reply = await call("POST", "/open", { path, create: true, focus: true });
      if (reply.status !== 200) fail(reply);
      const { doc, pages } = reply.body as { doc: Doc; pages: number };
      process.stdout.write(tabAddress(doc) + "\n");
      if (pages === 0) process.stdout.write("No page is connected; the user can open the address above.\n");
      return;
    }
    case "ls": {
      const reply = await call("GET", "/docs");
      if (reply.status !== 200) fail(reply);
      for (const doc of (reply.body as { docs: Doc[] }).docs) {
        process.stdout.write(`${doc.id}  ${doc.name}  ${doc.path}\n`);
      }
      return;
    }
    case "read": {
      const reply = await call("POST", "/read", { path });
      if (reply.status !== 200) fail(reply);
      const disk = (reply.body as { disk: Disk }).disk;
      if (disk.rev === null) throw new CliError(`no such file: ${path}`);
      process.stdout.write(disk.text);
      process.stderr.write(`rev ${disk.rev}\n`);
      return;
    }
    case "write": {
      const text = await readStdin();
      const reply = await call("POST", "/write", { path, text, rev });
      if (reply.status === 200) {
        process.stderr.write(`rev ${reply.body.rev}\n`);
        return;
      }
      if (reply.status === 409) {
        const current = (reply.body as { current: Disk }).current;
        throw new CliError(
          `current rev ${current.rev ?? "none"}\n` +
            "the file changed since that rev; read it again and apply your change on top",
        );
      }
      fail(reply);
    }
    case "close": {
      const reply = await call("POST", "/close", { path });
      if (reply.status !== 204) fail(reply);
      return;
    }
    case "shot":
      return shot(path!, out);
  }
}

const SHOT_TIMEOUT_MS = 30_000;

function timestamp(date = new Date()): string {
  const two = (n: number) => String(n).padStart(2, "0");
  return (
    `${date.getFullYear()}${two(date.getMonth() + 1)}${two(date.getDate())}-` +
    `${two(date.getHours())}${two(date.getMinutes())}${two(date.getSeconds())}`
  );
}

function defaultShotPath(): string {
  const base = join(stateDir, "shots", timestamp());
  let candidate = `${base}.png`;
  for (let n = 2; existsSync(candidate); n++) candidate = `${base}-${n}.png`;
  return candidate;
}

type Browser = import("playwright").Browser;

async function launchChromium(): Promise<Browser> {
  const { chromium } = await import("playwright");
  try {
    return await chromium.launch({ headless: true });
  } catch (error) {
    if (!(error instanceof Error) || !/Executable doesn't exist/i.test(error.message)) throw error;
    process.stderr.write("installing the headless browser for screenshots…\n");
    const cli = join(SKILL_DIR, "node_modules", "playwright", "cli.js");
    const result = spawnSync(process.execPath, [cli, "install", "chromium-headless-shell"], {
      cwd: SKILL_DIR,
      stdio: ["ignore", process.stderr, process.stderr],
    });
    if (result.error || result.status !== 0) throw new CliError("playwright could not install chromium-headless-shell");
    return chromium.launch({ headless: true });
  }
}

/** Screenshots the rendered file. Neither creates files nor switches anyone's page. */
async function shot(path: string, out: string | undefined): Promise<void> {
  const reply = await call("POST", "/open", { path, create: false, focus: false });
  if (reply.status !== 200) fail(reply);
  const { doc, opened } = reply.body as { doc: Doc; opened: boolean };
  const target = out ?? defaultShotPath();
  let browser: Browser | undefined;
  try {
    browser = await launchChromium();
    const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
    await page.goto(tabAddress(doc));
    const preview = page.locator("#preview");
    try {
      await page.waitForSelector('#preview[data-wb-state="rendered"], #preview[data-wb-state="error"]', {
        state: "attached",
        timeout: SHOT_TIMEOUT_MS,
      });
    } catch {
      throw new CliError("the page did not render within 30 s");
    }
    const state = await preview.getAttribute("data-wb-state");
    mkdirSync(dirname(target), { recursive: true });
    await page.screenshot({ path: target });
    process.stdout.write(target + "\n");
    if (state === "error") {
      const message = (await page.locator("#preview [data-wb-error]").textContent())?.trim() ?? "";
      throw new CliError(`render error: ${message || "unknown error"}`);
    }
  } finally {
    await browser?.close().catch(() => undefined);
    if (opened) await call("POST", "/close", { path }).catch(() => undefined);
  }
}

main(process.argv.slice(2)).catch((error: unknown) => {
  const code = error instanceof CliError ? error.code : 1;
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = code;
});
