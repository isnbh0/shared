// Starts one whiteboard server per run (building the page once) and exposes it through env.
import { rm } from "node:fs/promises";
import { startServer } from "../../server/main.ts";
import { socketPath } from "../../server/state.ts";
import { freePort, shortStateDir, tempDir } from "../helpers.ts";

export default async function globalSetup(): Promise<() => Promise<void>> {
  const stateDir = await shortStateDir();
  const filesDir = await tempDir("wb-e2e-");
  const port = await freePort();
  const server = await startServer({ port, stateDir, idleMs: 30 * 60_000, onExit: () => {} });
  process.env["WB_E2E_PORT"] = String(port);
  process.env["WB_E2E_SOCKET"] = socketPath(stateDir, port);
  process.env["WB_E2E_FILES"] = filesDir;
  return async () => {
    await server.close();
    await rm(stateDir, { recursive: true, force: true });
    await rm(filesDir, { recursive: true, force: true });
  };
}
