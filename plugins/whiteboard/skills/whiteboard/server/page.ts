// Builds the page with Vite into a directory and loads the output into an asset table.
import { readdir, readFile } from "node:fs/promises";
import { extname, join, relative, resolve, sep } from "node:path";
import { build, type Rolldown } from "vite";
import type { Asset } from "./routes.ts";

export const SKILL_DIR = resolve(import.meta.dirname, "..");

const TYPES: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".map": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".wasm": "application/wasm",
};

async function listFiles(dir: string): Promise<string[]> {
  const entries = await readdir(dir, { withFileTypes: true, recursive: true });
  return entries.filter((e) => e.isFile()).map((e) => join(e.parentPath, e.name));
}

export async function buildPage(outDir: string): Promise<{ assets: Map<string, Asset>; moduleIds: string[] }> {
  const result = await build({
    configFile: false,
    root: join(SKILL_DIR, "app"),
    base: "/",
    logLevel: "warn",
    resolve: { dedupe: ["mermaid"] },
    worker: { format: "es" },
    // A local, loopback-only page: bundle size is not a concern.
    build: { outDir, emptyOutDir: true, chunkSizeWarningLimit: 20_000 },
  });
  const outputs = (Array.isArray(result) ? result : [result]) as Rolldown.RolldownOutput[];
  const moduleIds: string[] = [];
  for (const output of outputs) {
    for (const item of output.output ?? []) {
      if (item.type === "chunk") moduleIds.push(...item.moduleIds);
    }
  }
  const assets = new Map<string, Asset>();
  for (const file of await listFiles(outDir)) {
    const urlPath = "/" + relative(outDir, file).split(sep).join("/");
    assets.set(urlPath, {
      body: await readFile(file),
      type: TYPES[extname(file).toLowerCase()] ?? "application/octet-stream",
    });
  }
  return { assets, moduleIds };
}
