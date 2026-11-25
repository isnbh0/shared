// View-only links to the hosted Mermaiden demo. The demo reads a document from the URL hash as
// `pako:` + base64url(zlib(JSON)) and opens it view-only when the query has `view=1`
// (mermaiden/apps/demo/src/adapters/browser/pakoCodec.ts and ports/documentCodec.ts). The JSON
// keys follow the demo's `documentSemanticKey` order so the same diagram always gives the same link.

export const MERMAIDEN_DEMO = "https://isnbh0.github.io/mermaiden/";
/** The demo refuses sources longer than this many UTF-16 code units. */
export const MAX_SOURCE_CODE_UNITS = 50_000;
/** The demo refuses document URLs longer than this. */
export const MAX_URL_LENGTH = 64 * 1024;

export type ShareAspects = {
  grid: boolean;
  relationshipHighlight: boolean;
  sequencePlayback: boolean;
  sequencePinnedRows: boolean;
};

export type ShareResult = { ok: true; url: string } | { ok: false; message: string };

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
  }
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}

async function zlib(text: string): Promise<Uint8Array> {
  const stream = new Blob([text]).stream().pipeThrough(new CompressionStream("deflate"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

/** Builds a view-only link to the hosted demo, or says why the diagram can't be shared. */
export async function mermaidenViewLink(source: string, aspects: ShareAspects): Promise<ShareResult> {
  if (source.length > MAX_SOURCE_CODE_UNITS) {
    return { ok: false, message: `Too long to share: Mermaiden accepts up to ${MAX_SOURCE_CODE_UNITS} characters.` };
  }
  if (/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/.test(source)) {
    return { ok: false, message: "Can't share: the source has an invalid character." };
  }
  const json = JSON.stringify({
    schemaVersion: 1,
    source,
    aspects: {
      rough: false,
      grid: aspects.grid,
      relationshipHighlight: aspects.relationshipHighlight,
      sequencePlayback: aspects.sequencePlayback,
      sequencePinnedRows: aspects.sequencePinnedRows,
    },
  });
  const url = new URL(MERMAIDEN_DEMO);
  url.searchParams.set("view", "1");
  url.hash = `pako:${base64Url(await zlib(json))}`;
  if (url.href.length > MAX_URL_LENGTH) {
    return { ok: false, message: "Too large to share: the Mermaiden link would be too long." };
  }
  return { ok: true, url: url.href };
}
