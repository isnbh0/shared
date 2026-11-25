// The whiteboard server. Binding the TCP port first is the single-instance lock: the holder of
// port P owns STATE/P/, including its control socket and built page.
import { mkdir, rm } from "node:fs/promises";
import { createServer, type Server } from "node:http";
import { join } from "node:path";
import { buildPage } from "./page.ts";
import { controlRoutes, Hub, pageRoutes, type Handler } from "./routes.ts";
import { defaultStateDir, portDir as portDirOf, portFromEnv, socketPath as socketPathOf, STARTING_HEADER } from "./state.ts";
import { Workspace } from "./workspace.ts";

function listen(server: Server, target: { port: number; host: string } | { path: string }): Promise<void> {
  return new Promise((resolve, reject) => {
    const onError = (error: Error) => reject(error);
    server.once("error", onError);
    const done = () => {
      server.off("error", onError);
      resolve();
    };
    if ("path" in target) server.listen(target.path, done);
    else server.listen(target.port, target.host, done);
  });
}

function closeServer(server: Server): Promise<void> {
  return new Promise((resolve) => {
    server.close(() => resolve());
    server.closeAllConnections();
  });
}

export async function startServer(options: {
  port: number;
  stateDir: string;
  idleMs: number;
  onExit: (code: number) => void;
}): Promise<{ close: () => Promise<void>; port: number }> {
  const { port, stateDir, idleMs } = options;

  // 1. Bind the port, with no fallback, before touching anything in STATE.
  let handler: Handler = (_req, res) => {
    res.writeHead(503, { "Content-Type": "text/plain; charset=utf-8", [STARTING_HEADER]: "1" });
    res.end("whiteboard is starting\n");
  };
  let idleTimer: NodeJS.Timeout | undefined;
  let hub: Hub | undefined;
  let closing: Promise<void> | undefined;
  const activity = () => {
    clearTimeout(idleTimer);
    idleTimer = undefined;
    if (!closing && (hub?.count() ?? 0) === 0) {
      idleTimer = setTimeout(() => {
        void close().then(() => options.onExit(0));
      }, idleMs);
      idleTimer.unref?.();
    }
  };
  const pageServer = createServer((req, res) => {
    activity();
    handler(req, res);
  });
  await listen(pageServer, { port, host: "127.0.0.1" });

  const portDir = portDirOf(stateDir, port);
  const socketPath = socketPathOf(stateDir, port);
  const workspace = new Workspace();
  hub = new Hub(workspace, { onCountChange: () => activity() });
  let controlServer: Server | undefined;

  const close = (): Promise<void> => {
    closing ??= (async () => {
      clearTimeout(idleTimer);
      hub?.close();
      await Promise.all([closeServer(pageServer), controlServer ? closeServer(controlServer) : undefined]);
      workspace.dispose();
      await rm(socketPath, { force: true });
    })();
    return closing;
  };

  try {
    // 2. Build the page into STATE/P/page/ and switch to the page routes.
    await mkdir(portDir, { recursive: true });
    const { assets } = await buildPage(join(portDir, "page"));
    handler = pageRoutes(workspace, { port, assets, hub });

    // 3. Replace any leftover socket and serve the control channel on it.
    await rm(socketPath, { force: true });
    const controlHandler = controlRoutes(workspace, {
      port,
      hub,
      stop: () => void close().then(() => options.onExit(0)),
    });
    const control = createServer((req, res) => {
      activity();
      controlHandler(req, res);
    });
    controlServer = control;
    await listen(control, { path: socketPath });
  } catch (error) {
    await close();
    throw error;
  }
  activity();
  return { close, port };
}

if (import.meta.main) {
  const port = portFromEnv();
  const minutes = Number(process.env["WHITEBOARD_IDLE_MINUTES"] || 30);
  try {
    await startServer({
      port,
      stateDir: defaultStateDir(),
      idleMs: minutes * 60_000,
      onExit: (code) => process.exit(code),
    });
    console.log(`${new Date().toISOString()} whiteboard server ${process.pid} on 127.0.0.1:${port}`);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "EADDRINUSE") {
      console.error(`port ${port} is in use; set WHITEBOARD_PORT`);
    } else {
      console.error(error);
    }
    process.exit(1);
  }
}
