import { rm, writeFile } from "node:fs/promises";
import { RELATIONSHIP_HIGHLIGHT_LAYER_SELECTOR } from "mermaiden-toolkit";
import { expect, expectRendered, file, preview, test } from "./fixtures.ts";

const FLOW = "flowchart LR\n  Alpha --> Beta\n";

test("follows an external edit within 2 s", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await control.open(path);
  await page.goto(home);
  await expectRendered(page);
  await writeFile(path, "flowchart LR\n  Alpha --> Beta --> Charlie\n");
  await expect(preview(page).locator("svg")).toContainText("Charlie", { timeout: 2000 });
});

test("shows a render error, keeps the previous SVG, and recovers", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await control.open(path);
  await page.goto(home);
  await expectRendered(page);
  await writeFile(path, "flowchart LR\n  A -->\n");
  await expect(preview(page)).toHaveAttribute("data-wb-state", "error");
  // The parse error itself, not Mermaiden's wrapper message.
  await expect(page.locator("[data-wb-error]")).toContainText("Parse error");
  await expect(preview(page).locator("svg")).toContainText("Alpha");
  // A failed render leaves nothing behind outside the preview.
  await expect(page.locator("body > :not(header, main, script, .sprite, .skip-link, .mermaidTooltip)")).toHaveCount(0);
  await writeFile(path, "flowchart LR\n  Alpha --> Fixed\n");
  await expect(preview(page)).toHaveAttribute("data-wb-state", "rendered");
  await expect(preview(page).locator("svg")).toContainText("Fixed");
  await expect(page.locator("[data-wb-error]")).toBeEmpty();
});

test("says when the file is missing, and renders it again when recreated", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await control.open(path);
  await page.goto(home);
  await expectRendered(page);
  await rm(path);
  await expect(page.locator("[data-wb-error]")).toHaveText("This file is missing on disk.");
  await expect(preview(page)).toHaveAttribute("data-wb-state", "error");
  await expect(preview(page).locator("svg")).toHaveCount(0);
  await writeFile(path, "flowchart LR\n  Back --> Again\n");
  await expectRendered(page);
  await expect(preview(page).locator("svg")).toContainText("Back");
});

test("reports an empty file", async ({ page, control, dir, home }) => {
  await control.open(await file(dir, "empty.mmd", ""));
  await page.goto(home);
  await expect(page.locator("[data-wb-error]")).toHaveText("This file is empty.");
  await expect(preview(page)).toHaveAttribute("data-wb-state", "error");
});

test("hovering a flowchart node adds the relationship highlight", async ({ page, control, dir, home }) => {
  await control.open(await file(dir, "flow.mmd", FLOW));
  await page.goto(home);
  await expectRendered(page);
  await expect(preview(page).locator(RELATIONSHIP_HIGHLIGHT_LAYER_SELECTOR)).toHaveCount(2);
  await expect(preview(page).locator(".relationship-node-overlay")).toHaveCount(0);
  // The toolkit's hit target sits over the node and receives the pointer.
  await preview(page).getByRole("button", { name: "Alpha: show related nodes" }).hover();
  await expect(preview(page).locator(".relationship-node-overlay").first()).toBeAttached();
});

test("renders the latest of two quick writes", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await control.open(path);
  await page.goto(home);
  await expectRendered(page);
  await writeFile(path, "flowchart LR\n  First --> Write\n");
  await writeFile(path, "flowchart LR\n  Second --> Write\n");
  await expect(preview(page).locator("svg")).toContainText("Second");
  await page.waitForTimeout(500);
  await expect(preview(page).locator("svg")).toContainText("Second");
  await expect(preview(page)).toHaveAttribute("data-wb-state", "rendered");
});
