import { inflateSync } from "node:zlib";
import { expect, expectRendered, file, test } from "./fixtures.ts";

const FLOW = "flowchart LR\n  Alpha --> Beta\n";

test("copies a view-only Mermaiden link to the active diagram", async ({ page, context, control, dir, home }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"], { origin: home });
  await control.open(await file(dir, "flow.mmd", FLOW));
  await page.goto(home);
  await expectRendered(page);
  await page.getByRole("button", { name: "Copy Mermaiden link" }).click();
  await expect(page.locator("#share-note")).toHaveText("View link copied");

  const url = new URL(await page.evaluate(() => navigator.clipboard.readText()));
  expect(`${url.origin}${url.pathname}`).toBe("https://isnbh0.github.io/mermaiden/");
  expect(url.searchParams.get("view")).toBe("1");
  expect(url.hash).toMatch(/^#pako:[A-Za-z0-9_-]+$/);
  const json = inflateSync(Buffer.from(url.hash.slice("#pako:".length), "base64url")).toString("utf8");
  expect(JSON.parse(json)).toMatchObject({ schemaVersion: 1, source: FLOW });
});
