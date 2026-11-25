import { expect, expectRendered, file, preview, test } from "./fixtures.ts";

const FLOW = "flowchart LR\n  Alpha --> Beta\n";
const SECOND = "flowchart TD\n  Gamma --> Delta\n";

test("shows a tab per open file and addresses the first on load", async ({ page, control, dir, home }) => {
  const a = await control.open(await file(dir, "first.mmd", FLOW));
  await control.open(await file(dir, "second.mmd", SECOND));
  await page.goto(home);
  const tabs = page.getByRole("tab");
  await expect(tabs).toHaveCount(2);
  await expect(tabs.nth(0)).toHaveText("first.mmd");
  await expect(tabs.nth(1)).toHaveText("second.mmd");
  await expect(page).toHaveURL(`${home}#/${a.id}/first.mmd`);
  await expect(tabs.nth(0)).toHaveAttribute("title", a.path);
  await expectRendered(page);
});

test("clicking a tab addresses it and renders its diagram", async ({ page, control, dir, home }) => {
  await control.open(await file(dir, "first.mmd", FLOW));
  const b = await control.open(await file(dir, "second.mmd", SECOND));
  await page.goto(home);
  await page.getByRole("tab", { name: "second.mmd" }).click();
  await expect(page).toHaveURL(`${home}#/${b.id}/second.mmd`);
  await expectRendered(page);
  await expect(preview(page).locator("svg")).toContainText("Gamma");
});

test("arrow keys move the selection", async ({ page, control, dir, home }) => {
  await control.open(await file(dir, "first.mmd", FLOW));
  await control.open(await file(dir, "second.mmd", SECOND));
  await page.goto(home);
  const first = page.getByRole("tab", { name: "first.mmd" });
  const second = page.getByRole("tab", { name: "second.mmd" });
  await expect(first).toHaveAttribute("aria-selected", "true");
  await first.focus();
  await page.keyboard.press("ArrowRight");
  await expect(second).toHaveAttribute("aria-selected", "true");
  await expect(first).toHaveAttribute("aria-selected", "false");
  await expect(second).toBeFocused();
  await page.keyboard.press("ArrowLeft");
  await expect(first).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("End");
  await expect(second).toHaveAttribute("aria-selected", "true");
  await page.keyboard.press("Home");
  await expect(first).toHaveAttribute("aria-selected", "true");
});

test("a focusing open activates the file in an open page", async ({ page, control, dir, home }) => {
  const firstPath = await file(dir, "first.mmd", FLOW);
  await control.open(firstPath);
  const b = await control.open(await file(dir, "second.mmd", SECOND));
  await page.goto(`${home}#/${b.id}/second.mmd`);
  await expect(page.getByRole("tab", { name: "second.mmd" })).toHaveAttribute("aria-selected", "true");
  await control.open(firstPath, { focus: true });
  await expect(page.getByRole("tab", { name: "first.mmd" })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("tab", { name: "first.mmd" })).toBeFocused();
  await expect(preview(page).locator("svg")).toContainText("Alpha");
});

test("closing a tab removes it and activates its neighbour", async ({ page, control, dir, home }) => {
  await control.open(await file(dir, "first.mmd", FLOW));
  await control.open(await file(dir, "second.mmd", SECOND));
  await control.open(await file(dir, "third.mmd", FLOW));
  await page.goto(home);
  await page.getByRole("button", { name: "Close first.mmd" }).click();
  await expect(page.getByRole("tab")).toHaveCount(2);
  await expect(page.getByRole("tab", { name: "second.mmd" })).toHaveAttribute("aria-selected", "true");
  await page.getByRole("tab", { name: "third.mmd" }).click();
  await page.getByRole("button", { name: "Close third.mmd" }).click();
  await expect(page.getByRole("tab")).toHaveCount(1);
  await expect(page.getByRole("tab", { name: "second.mmd" })).toHaveAttribute("aria-selected", "true");
});

test("a stale address says the file isn't open", async ({ page, control, dir, home }) => {
  await control.open(await file(dir, "first.mmd", FLOW));
  await page.goto(`${home}#/000000000000/x.mmd`);
  await expect(page.getByText("This file isn't open")).toBeVisible();
  await expect(page.getByRole("tab", { selected: true })).toHaveCount(0);
});

test("with no files open the panel says so", async ({ page, control, home }) => {
  expect(await control.docs()).toEqual([]);
  await page.goto(home);
  await expect(page.getByText("No files open")).toBeVisible();
});
