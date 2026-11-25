// The only module that constructs DocId and Rev values.
import { createHash } from "node:crypto";

export type DocId = string & { readonly __brand: "DocId" };
export type Rev = string & { readonly __brand: "Rev" };

export type Parsed<T> = { ok: true; value: T } | { ok: false; error: string };

function sha256Hex(input: string): string {
  return createHash("sha256").update(input, "utf8").digest("hex");
}

export function docIdOf(realPath: string): DocId {
  return sha256Hex(realPath).slice(0, 12) as DocId;
}

export function revOf(text: string): Rev {
  return sha256Hex(text).slice(0, 16) as Rev;
}

export function parseDocId(s: unknown): Parsed<DocId> {
  return typeof s === "string" && /^[0-9a-f]{12}$/.test(s)
    ? { ok: true, value: s as DocId }
    : { ok: false, error: "malformed document id" };
}

/** Parses a wire revision: 16 lowercase hex characters, or null meaning "missing". */
export function parseRev(s: unknown): Parsed<Rev | null> {
  if (s === null) return { ok: true, value: null };
  return typeof s === "string" && /^[0-9a-f]{16}$/.test(s)
    ? { ok: true, value: s as Rev }
    : { ok: false, error: "malformed rev" };
}
