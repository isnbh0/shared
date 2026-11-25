// Tab addresses: `#/<id>/<name>`. The name segment is display-only.
import { parseDocId, type Doc, type DocId } from "./api.ts";

export type Route = { kind: "doc"; id: DocId } | { kind: "none" };

export function parseRoute(hash: string): Route {
  const match = /^#\/([^/]*)(?:\/.*)?$/.exec(hash);
  const id = match ? parseDocId(match[1]) : undefined;
  return id ? { kind: "doc", id } : { kind: "none" };
}

export function formatHash(doc: Doc): string {
  return `#/${doc.id}/${encodeURIComponent(doc.name)}`;
}

/** Points the address at `doc` (or at no tab) without adding back history. */
export function replaceRoute(doc: Doc | undefined): void {
  const target = doc ? formatHash(doc) : "";
  if (location.hash === target) return;
  history.replaceState(null, "", `${location.pathname}${location.search}${target}`);
}
