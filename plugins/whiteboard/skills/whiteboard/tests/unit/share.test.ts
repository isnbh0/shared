import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { inflateSync } from "node:zlib";
import fc from "fast-check";
import { describe, expect, it } from "vitest";
import { MAX_SOURCE_CODE_UNITS, MERMAIDEN_DEMO, mermaidenViewLink, type ShareAspects } from "../../app/src/share.ts";

const aspects: ShareAspects = { grid: true, relationshipHighlight: false, sequencePlayback: true, sequencePinnedRows: false };

/** Decodes a link with no shared code, the way the demo does: `pako:` + base64url(zlib(JSON)). */
function decode(href: string) {
  const url = new URL(href);
  const hash = url.hash.slice(1);
  if (!hash.startsWith("pako:")) throw new Error(`not a pako link: ${hash.slice(0, 16)}`);
  const json = inflateSync(Buffer.from(hash.slice("pako:".length), "base64url")).toString("utf8");
  return { url, document: JSON.parse(json) };
}

// With a Mermaiden checkout at hand, the demo's own codec decodes too, so a format change there
// fails here. `MERMAIDEN_DIR` names the checkout.
const codecPath = join(process.env["MERMAIDEN_DIR"] ?? join(homedir(), "local/src/mermaiden"), "apps/demo/src/adapters/browser/pakoCodec.ts");
const demo = existsSync(codecPath) ? new (await import(pathToFileURL(codecPath).href)).PakoDocumentCodec() : null;

const source = "flowchart LR\n  A[Café ☕] --> B{ok?}\n  B -->|yes| C";
const document = { schemaVersion: 1, source, aspects: { rough: false, ...aspects } };
const anySource = fc.string({ unit: "grapheme", maxLength: 300 });

async function link(text: string): Promise<string> {
  const result = await mermaidenViewLink(text, aspects);
  if (!result.ok) throw new Error(result.message);
  return result.url;
}

describe("mermaidenViewLink", () => {
  it("builds a view-only demo link that decodes to the same document", async () => {
    const { url, document: decoded } = decode(await link(source));
    expect(`${url.origin}${url.pathname}`).toBe(MERMAIDEN_DEMO);
    expect(url.searchParams.get("view")).toBe("1");
    expect(decoded).toEqual(document);
  });

  it("round-trips any valid source", async () => {
    await fc.assert(
      fc.asyncProperty(anySource, async (text) => {
        expect(decode(await link(text)).document).toMatchObject({ source: text });
      }),
      { numRuns: 100 },
    );
  });

  it("refuses sources the demo would refuse", async () => {
    expect(await mermaidenViewLink("x".repeat(MAX_SOURCE_CODE_UNITS + 1), aspects)).toMatchObject({ ok: false });
    expect(await mermaidenViewLink("a\uD800b", aspects)).toMatchObject({ ok: false });
  });
});

describe.skipIf(!demo)("the Mermaiden demo's own codec", () => {
  it("decodes the link to the same document", async () => {
    expect(demo!.decode(new URL(await link(source)).hash.slice(1))).toEqual({ ok: true, document });
  });

  it("round-trips any valid source", async () => {
    await fc.assert(
      fc.asyncProperty(anySource, async (text) => {
        expect(demo!.decode(new URL(await link(text)).hash.slice(1))).toMatchObject({ ok: true, document: { source: text } });
      }),
      { numRuns: 100 },
    );
  });
});
