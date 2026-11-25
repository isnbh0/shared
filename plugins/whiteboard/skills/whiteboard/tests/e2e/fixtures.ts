// Shared fixtures: the server's port, a control-channel helper, and a fresh files directory.
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { test as base, expect, type Page } from "@playwright/test";
import { http } from "../helpers.ts";

export type Control = {
  open(path: string, options?: { focus?: boolean; create?: boolean }): Promise<{ id: string; name: string; path: string }>;
  write(path: string, text: string, rev: string | null): Promise<{ status: number; json: any }>;
  close(path: string): Promise<void>;
  docs(): Promise<{ id: string; name: string; path: string }[]>;
};

function control(socketPath: string): Control {
  const call = (method: string, path: string, body?: unknown) => http({ socketPath }, method, path, { body });
  return {
    async open(path, options = {}) {
      const reply = await call("POST", "/open", { path, create: options.create ?? true, focus: options.focus ?? false });
      if (reply.status !== 200) throw new Error(`open failed: ${reply.text}`);
      return reply.json.doc;
    },
    async write(path, text, rev) {
      const reply = await call("POST", "/write", { path, text, rev });
      return { status: reply.status, json: reply.json };
    },
    async close(path) {
      await call("POST", "/close", { path });
    },
    async docs() {
      return (await call("GET", "/docs")).json.docs;
    },
  };
}

let dirCount = 0;

export const test = base.extend<{ port: number; control: Control; dir: string; home: string }>({
  port: async ({}, use) => use(Number(process.env["WB_E2E_PORT"])),
  home: async ({ port }, use) => use(`http://127.0.0.1:${port}/`),
  control: async ({}, use) => {
    const ctl = control(process.env["WB_E2E_SOCKET"]!);
    for (const doc of await ctl.docs()) await ctl.close(doc.path);
    await use(ctl);
    for (const doc of await ctl.docs()) await ctl.close(doc.path);
  },
  dir: async ({}, use, testInfo) => {
    const dir = join(process.env["WB_E2E_FILES"]!, `t${testInfo.workerIndex}-${dirCount++}`);
    await mkdir(dir, { recursive: true });
    await use(dir);
  },
});

export { expect };

export async function file(dir: string, name: string, text: string): Promise<string> {
  const path = join(dir, name);
  await writeFile(path, text);
  return path;
}

export function preview(page: Page) {
  return page.locator("#preview");
}

export async function expectRendered(page: Page) {
  await expect(preview(page)).toHaveAttribute("data-wb-state", "rendered");
  await expect(preview(page).locator("svg").first()).toBeVisible();
}
