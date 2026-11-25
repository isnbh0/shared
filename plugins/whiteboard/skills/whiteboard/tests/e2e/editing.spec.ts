import { readdir, readFile, rm, writeFile } from "node:fs/promises";
import type { Page, Route } from "@playwright/test";
import { expect, expectRendered, file, preview, test } from "./fixtures.ts";

const FLOW = "flowchart LR\n  Alpha --> Beta\n";

const editButton = (page: Page) => page.getByRole("button", { name: "Edit", exact: true });
const editorPane = (page: Page) => page.locator("#editor");
const statusLine = (page: Page) => page.locator("#status");
const banner = (page: Page) => page.locator("#conflict");

/** The editor's visible text, with Monaco's non-breaking spaces normalized. */
async function editorText(page: Page): Promise<string> {
  // Monaco reuses line elements, so their DOM order is not their visual order.
  return page.locator("#editor .view-line").evaluateAll((lines) =>
    lines
      .map((line) => ({ top: parseFloat((line as HTMLElement).style.top), text: line.textContent ?? "" }))
      .sort((a, b) => a.top - b.top)
      .map((line) => line.text.replace(/\u00a0/g, " "))
      .join("\n"),
  );
}

async function startEditing(page: Page): Promise<void> {
  await editButton(page).click();
  await expect(editButton(page)).toHaveAttribute("aria-pressed", "true");
  await expect(editorPane(page).locator(".monaco-editor")).toBeVisible();
}

/** Replaces the editor's whole text, as typing would. */
async function typeAll(page: Page, text: string): Promise<void> {
  await editorPane(page).locator(".view-lines").click();
  await page.keyboard.press("ControlOrMeta+a");
  await page.keyboard.insertText(text);
}

/** Holds every PUT until `release` is called. */
async function holdSaves(page: Page) {
  const held: Route[] = [];
  await page.route(/\/api\/docs\/[0-9a-f]{12}$/, (route) => {
    if (route.request().method() === "PUT") held.push(route);
    else void route.continue();
  });
  return {
    async waitHeld() {
      await expect.poll(() => held.length).toBeGreaterThan(0);
    },
    async release() {
      for (const route of held.splice(0)) await route.continue().catch(() => undefined);
      await page.unrouteAll({ behavior: "ignoreErrors" });
    },
  };
}

async function expectNoConflictFiles(dir: string): Promise<void> {
  expect((await readdir(dir)).filter((name) => name.includes(".conflict-"))).toEqual([]);
}

async function opened(page: Page, control: { open(path: string): Promise<unknown> }, path: string, home: string) {
  await control.open(path);
  await page.goto(home);
  await expectRendered(page);
}

test("starts with the editor hidden", async ({ page, control, dir, home }) => {
  await opened(page, control, await file(dir, "flow.mmd", FLOW), home);
  await expect(editButton(page)).toHaveAttribute("aria-pressed", "false");
  await expect(editorPane(page)).toBeHidden();
});

test("saves the exact typed text within 1 s", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await opened(page, control, path, home);
  await startEditing(page);
  const typed = "flowchart LR\n  Alpha --> Typed";
  await typeAll(page, typed);
  await expect.poll(() => readFile(path, "utf8"), { timeout: 1000 }).toBe(typed);
  await expect(statusLine(page)).toHaveText("Saved");
  await expect(preview(page).locator("svg")).toContainText("Typed");
  await expectNoConflictFiles(dir);
});

test("follows an external change while the editor is clean", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await opened(page, control, path, home);
  await startEditing(page);
  await writeFile(path, "flowchart LR\n  Alpha --> Outside\n");
  await expect.poll(() => editorText(page)).toContain("Alpha --> Outside");
  await expect(preview(page).locator("svg")).toContainText("Outside");
  await expect(statusLine(page)).toHaveText("Saved");
});

for (const choice of ["Overwrite file", "Reload from file"] as const) {
  test(`resolves a conflict with "${choice}"`, async ({ page, control, dir, home }) => {
    const path = await file(dir, "flow.mmd", FLOW);
    await opened(page, control, path, home);
    await startEditing(page);
    const saves = await holdSaves(page);
    await typeAll(page, "flowchart LR\n  Alpha --> Mine");
    await saves.waitHeld();
    const theirs = "flowchart LR\n  Alpha --> Theirs\n";
    await writeFile(path, theirs);
    await saves.release();

    await expect(banner(page)).toBeVisible();
    await expect(statusLine(page)).toHaveText("This file changed on disk while you were editing.");
    await expect(page.getByRole("tab", { name: /^flow\.mmd\s*, conflict$/ })).toBeVisible();
    // Typing still works during a conflict.
    await editorPane(page).locator(".view-lines").click();
    await page.keyboard.press("ControlOrMeta+End");
    await page.keyboard.insertText(" --> More");
    await expect.poll(() => editorText(page)).toContain("Alpha --> Mine --> More");
    expect(await readFile(path, "utf8")).toBe(theirs);

    await banner(page).getByRole("button", { name: choice }).click();
    await expect(banner(page)).toBeHidden();
    await expect(statusLine(page)).toHaveText("Saved");
    if (choice === "Overwrite file") {
      await expect.poll(() => readFile(path, "utf8")).toBe("flowchart LR\n  Alpha --> Mine --> More");
    } else {
      await expect.poll(() => editorText(page)).toBe(theirs.trimEnd() + "\n");
      expect(await readFile(path, "utf8")).toBe(theirs);
    }
    await expectNoConflictFiles(dir);
  });
}

test("shows a deleted file as missing, and typing recreates it", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await opened(page, control, path, home);
  await startEditing(page);
  await rm(path);
  await expect(statusLine(page)).toHaveText("Missing on disk");
  await typeAll(page, "flowchart LR\n  Back --> Again");
  await expect.poll(() => readFile(path, "utf8").catch(() => null)).toBe("flowchart LR\n  Back --> Again");
  await expect(statusLine(page)).toHaveText("Saved");
  await expectNoConflictFiles(dir);
});

test("asks before closing a tab with unsaved changes", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await opened(page, control, path, home);
  await startEditing(page);
  const saves = await holdSaves(page);
  await typeAll(page, "flowchart LR\n  Alpha --> Unsaved");
  await saves.waitHeld();
  const close = page.getByRole("button", { name: "Close flow.mmd" });

  let asked = "";
  page.once("dialog", (dialog) => {
    asked = dialog.message();
    void dialog.dismiss();
  });
  await close.click();
  await expect.poll(() => asked).toBe("Discard unsaved changes to flow.mmd?");
  await expect(page.getByRole("tab")).toHaveCount(1);
  expect(await control.docs()).toHaveLength(1);

  page.once("dialog", (dialog) => void dialog.accept());
  await close.click();
  await expect(page.getByRole("tab")).toHaveCount(0);
  await expect.poll(() => control.docs()).toEqual([]);
  await page.unrouteAll({ behavior: "ignoreErrors" });
  expect(await readFile(path, "utf8")).toBe(FLOW);
});

test("keeps the draft when the tab is closed elsewhere, and reopening makes it a conflict", async ({
  page,
  control,
  dir,
  home,
}) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await opened(page, control, path, home);
  await startEditing(page);
  const saves = await holdSaves(page);
  await typeAll(page, "flowchart LR\n  Alpha --> Kept");
  await saves.waitHeld();
  await control.close(path);
  await expect(statusLine(page)).toHaveText(
    "This file was closed elsewhere. Your unsaved text is kept here; copy it before closing the tab.",
  );
  await expect(page.getByRole("tab", { name: /^flow\.mmd\s*, conflict$/ })).toBeVisible();
  expect(await editorText(page)).toContain("Alpha --> Kept");
  await saves.release(); // The held save now answers 404; the tab stays orphaned.
  await expect(statusLine(page)).toHaveText(/closed elsewhere/);

  await control.open(path);
  await expect(banner(page)).toBeVisible();
  await expect(banner(page).getByRole("button", { name: "Reload from file" })).toBeVisible();
  await expect(banner(page).getByRole("button", { name: "Overwrite file" })).toBeVisible();
  await expect(page.getByRole("tab")).toHaveCount(1);
  expect(await editorText(page)).toContain("Alpha --> Kept");
  await expectNoConflictFiles(dir);
});

test("never shows or edits another tab's text while a tab is loading", async ({ page, control, dir, home }) => {
  const first = await file(dir, "first.mmd", "flowchart LR\n  First --> One\n");
  const second = await file(dir, "second.mmd", "flowchart LR\n  Second --> Two\n");
  await control.open(first);
  await control.open(second);
  await page.goto(home);
  await expectRendered(page);
  await startEditing(page);
  await expect.poll(() => editorText(page)).toContain("First --> One");

  const held: Route[] = [];
  await page.route(/\/api\/docs\/[0-9a-f]{12}$/, (route) => {
    if (route.request().method() === "GET") held.push(route);
    else void route.continue();
  });
  await page.getByRole("tab", { name: /^second\.mmd/ }).click();
  await expect.poll(() => held.length).toBeGreaterThan(0);
  await editButton(page).click();
  await expect(editButton(page)).toHaveAttribute("aria-pressed", "true");
  await expect(editorPane(page)).toBeVisible();
  expect(await editorText(page)).not.toContain("First");
  await editorPane(page).click();
  await page.keyboard.insertText("typed while loading");
  await page.waitForTimeout(800);
  expect(await readFile(first, "utf8")).toBe("flowchart LR\n  First --> One\n");

  for (const route of held.splice(0)) await route.continue();
  await page.unrouteAll({ behavior: "ignoreErrors" });
  await expect.poll(() => editorText(page)).toContain("Second --> Two");
  expect(await readFile(second, "utf8")).toBe("flowchart LR\n  Second --> Two\n");
});

test("reads again when the file changes during the first read", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await control.open(path);
  let stale: Promise<void> | undefined;
  let releaseStale!: () => void;
  const gate = new Promise<void>((resolve) => (releaseStale = resolve));
  await page.route(/\/api\/docs\/[0-9a-f]{12}$/, async (route) => {
    if (route.request().method() !== "GET" || stale) return route.continue();
    // Answer the first read with the text from before the change.
    stale = (async () => {
      const response = await route.fetch();
      await gate;
      await route.fulfill({ response });
    })();
    return stale;
  });
  await page.goto(home);
  await expect.poll(() => stale !== undefined).toBe(true);
  await writeFile(path, "flowchart LR\n  Alpha --> Outside\n");
  await page.waitForTimeout(500); // The `changed` event arrives while the first read is held.
  releaseStale();
  await expect(preview(page).locator("svg")).toContainText("Outside");
  await expect(statusLine(page)).toHaveText("Saved");
});

test("keeps the file's CRLF line endings after an external rewrite", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await opened(page, control, path, home);
  await startEditing(page);
  await writeFile(path, "flowchart LR\r\n  Alpha --> Windows\r\n");
  await expect.poll(() => editorText(page)).toContain("Alpha --> Windows");
  await editorPane(page).locator(".view-lines").click();
  await page.keyboard.press("ControlOrMeta+End");
  await page.keyboard.insertText("  Windows --> More");
  await expect
    .poll(() => readFile(path, "utf8"))
    .toBe("flowchart LR\r\n  Alpha --> Windows\r\n  Windows --> More");
});

test("retries a save answered as not open while the file is still open", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await opened(page, control, path, home);
  await startEditing(page);
  let refused = 0;
  await page.route(/\/api\/docs\/[0-9a-f]{12}$/, (route) => {
    if (route.request().method() === "PUT" && refused === 0) {
      refused++;
      return route.fulfill({ status: 404, contentType: "application/json", body: '{"error":"not open"}' });
    }
    return route.continue();
  });
  const typed = "flowchart LR\n  Alpha --> Retried";
  await typeAll(page, typed);
  await expect.poll(() => refused).toBe(1);
  await expect.poll(() => readFile(path, "utf8"), { timeout: 10_000 }).toBe(typed);
  await expect(statusLine(page)).toHaveText("Saved");
});
