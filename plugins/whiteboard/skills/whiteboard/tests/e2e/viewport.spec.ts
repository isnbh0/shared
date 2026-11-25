import { writeFile } from "node:fs/promises";
import type { Page } from "@playwright/test";
import { expect, expectRendered, file, preview, test } from "./fixtures.ts";

const FLOW = "flowchart LR\n  Alpha --> Beta\n  Beta --> Gamma\n";
const WIDE = `flowchart LR\n${Array.from({ length: 14 }, (_, i) => `  N${i} --> N${i + 1}`).join("\n")}\n`;

const button = (page: Page, name: string | RegExp) => page.getByRole("button", { name, exact: typeof name === "string" });
const zoomLabel = (page: Page) => page.locator("#zoom-reset");
const svg = (page: Page) => preview(page).locator("svg").first();

async function percent(page: Page): Promise<number> {
  return Number((await zoomLabel(page).textContent())!.replace("%", ""));
}

async function boxes(page: Page) {
  const pane = (await preview(page).boundingBox())!;
  const diagram = (await svg(page).boundingBox())!;
  return { pane, diagram };
}

function inside(inner: { x: number; y: number; width: number; height: number }, outer: typeof inner) {
  return (
    inner.x >= outer.x - 0.5 &&
    inner.y >= outer.y - 0.5 &&
    inner.x + inner.width <= outer.x + outer.width + 0.5 &&
    inner.y + inner.height <= outer.y + outer.height + 0.5
  );
}

async function opened(page: Page, control: { open(path: string): Promise<unknown> }, path: string, home: string) {
  await control.open(path);
  await page.goto(home);
  await expectRendered(page);
}

test("fits the diagram in the pane, including a wide one", async ({ page, control, dir, home }) => {
  await opened(page, control, await file(dir, "wide.mmd", WIDE), home);
  const { pane, diagram } = await boxes(page);
  expect(inside(diagram, pane)).toBe(true);
  expect(await percent(page)).toBeLessThan(100);
});

test("zooms with the buttons and returns to 100 % and to fit", async ({ page, control, dir, home }) => {
  await opened(page, control, await file(dir, "flow.mmd", FLOW), home);
  const fitted = await percent(page);
  await button(page, "Zoom in").click();
  await expect.poll(() => percent(page)).toBe(Math.round(fitted * 1.25));
  await button(page, "Zoom out").click();
  await button(page, "Zoom out").click();
  await expect.poll(() => percent(page)).toBeLessThan(fitted);

  await zoomLabel(page).click();
  await expect(zoomLabel(page)).toHaveText("100%");
  const viewBoxWidth = await svg(page).evaluate((el) => (el as SVGSVGElement).viewBox.baseVal.width);
  expect((await svg(page).boundingBox())!.width).toBeCloseTo(viewBoxWidth, 0);

  await button(page, "Fit").click();
  await expect.poll(() => percent(page)).toBe(fitted);
});

test("zooms with the wheel around the cursor by default", async ({ page, control, dir, home }) => {
  await opened(page, control, await file(dir, "flow.mmd", FLOW), home);
  const before = await percent(page);
  const { diagram } = await boxes(page);
  const point = { x: diagram.x + diagram.width * 0.25, y: diagram.y + diagram.height / 2 };
  await page.mouse.move(point.x, point.y);
  await page.mouse.wheel(0, -200);
  await expect.poll(() => percent(page)).toBeGreaterThan(before);
  // The diagram point under the cursor stays put: a quarter of the way across.
  const after = (await svg(page).boundingBox())!;
  expect((point.x - after.x) / after.width).toBeCloseTo(0.25, 2);
});

test("pans with the wheel when Scroll to pan is on, remembered across reloads", async ({ page, control, dir, home }) => {
  await opened(page, control, await file(dir, "flow.mmd", FLOW), home);
  const toggle = button(page, "Scroll to pan");
  await expect(toggle).toHaveAttribute("aria-pressed", "false");
  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-pressed", "true");

  const before = await percent(page);
  const start = (await svg(page).boundingBox())!;
  const pane = (await preview(page).boundingBox())!;
  await page.mouse.move(pane.x + pane.width / 2, pane.y + pane.height / 2);
  await page.mouse.wheel(0, 120);
  await expect.poll(async () => (await svg(page).boundingBox())!.y).toBeCloseTo(start.y - 120, 0);
  expect(await percent(page)).toBe(before);

  // Ctrl+wheel still zooms.
  await page.keyboard.down("Control");
  await page.mouse.wheel(0, -50);
  await page.keyboard.up("Control");
  await expect.poll(() => percent(page)).toBeGreaterThan(before);

  await page.reload();
  await expectRendered(page);
  await expect(button(page, "Scroll to pan")).toHaveAttribute("aria-pressed", "true");
});

test("pans by dragging", async ({ page, control, dir, home }) => {
  await opened(page, control, await file(dir, "flow.mmd", FLOW), home);
  const start = (await svg(page).boundingBox())!;
  const pane = (await preview(page).boundingBox())!;
  await page.mouse.move(pane.x + 20, pane.y + 20);
  await page.mouse.down();
  await page.mouse.move(pane.x + 80, pane.y + 60, { steps: 5 });
  await page.mouse.up();
  const end = (await svg(page).boundingBox())!;
  expect(end.x - start.x).toBeCloseTo(60, 0);
  expect(end.y - start.y).toBeCloseTo(40, 0);
});

test("responds to keys when the preview has focus", async ({ page, control, dir, home }) => {
  await opened(page, control, await file(dir, "flow.mmd", FLOW), home);
  const fitted = await percent(page);
  await preview(page).focus();
  await page.keyboard.press("0");
  await expect(zoomLabel(page)).toHaveText("100%");
  await page.keyboard.press("+");
  await expect(zoomLabel(page)).toHaveText("125%");
  await page.keyboard.press("Shift+Digit1");
  await expect.poll(() => percent(page)).toBe(fitted);
});

test("keeps a zoomed view through live edits, and refits while following fit", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await opened(page, control, path, home);

  await writeFile(path, WIDE);
  await expect(svg(page)).toContainText("N14");
  await expectRendered(page);
  expect(inside((await svg(page).boundingBox())!, (await preview(page).boundingBox())!)).toBe(true);

  await zoomLabel(page).click();
  await button(page, "Zoom in").click();
  await expect(zoomLabel(page)).toHaveText("125%");
  const before = (await svg(page).boundingBox())!;
  await writeFile(path, WIDE.replace("N0 -->", "Start -->"));
  await expect(svg(page)).toContainText("Start");
  await expect(zoomLabel(page)).toHaveText("125%");
  const after = (await svg(page).boundingBox())!;
  expect(after.x).toBeCloseTo(before.x, 0);
  expect(after.y).toBeCloseTo(before.y, 0);
});

test("restores each tab's view when switching back", async ({ page, control, dir, home }) => {
  await control.open(await file(dir, "one.mmd", FLOW));
  await control.open(await file(dir, "two.mmd", WIDE));
  await page.goto(home);
  await expectRendered(page);
  await page.getByRole("tab", { name: /^one\.mmd/ }).click();
  await expect(svg(page)).toContainText("Alpha");
  await zoomLabel(page).click();
  await button(page, "Zoom in").click();
  await expect(zoomLabel(page)).toHaveText("125%");

  await page.getByRole("tab", { name: /^two\.mmd/ }).click();
  await expect(svg(page)).toContainText("N14");
  await expect.poll(() => percent(page)).toBeLessThan(100);

  await page.getByRole("tab", { name: /^one\.mmd/ }).click();
  await expect(svg(page)).toContainText("Alpha");
  await expect(zoomLabel(page)).toHaveText("125%");
});

test("highlights related nodes on hover, with a toggle shown for flowcharts only", async ({ page, control, dir, home }) => {
  const path = await file(dir, "flow.mmd", FLOW);
  await opened(page, control, path, home);
  const toggle = button(page, "Highlight related");
  await expect(toggle).toHaveAttribute("aria-pressed", "true");
  const current = preview(page).locator(".relationship-node--current");

  await preview(page).locator('[data-relationship-node]').first().hover();
  await expect(current).toHaveCount(1);

  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-pressed", "false");
  await expect(preview(page).locator("[data-relationship-node]")).toHaveCount(0);
  await page.mouse.move(0, 0);
  const node = preview(page).locator("g.node").first();
  await node.hover();
  await expect(current).toHaveCount(0);

  await toggle.click();
  await preview(page).locator('[data-relationship-node]').first().hover();
  await expect(current).toHaveCount(1);

  await writeFile(path, "sequenceDiagram\n  A->>B: hi\n");
  await expect(svg(page)).toContainText("hi");
  await expect(toggle).toBeHidden();
});

test("shows a grid that moves and scales with the view, remembered across reloads", async ({ page, control, dir, home }) => {
  await opened(page, control, await file(dir, "flow.mmd", FLOW), home);
  const toggle = button(page, "Grid");
  const image = () => preview(page).evaluate((el) => getComputedStyle(el).backgroundImage);
  const size = () => preview(page).evaluate((el) => getComputedStyle(el).backgroundSize);
  await expect(toggle).toHaveAttribute("aria-pressed", "false");
  expect(await image()).toBe("none");

  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-pressed", "true");
  expect(await image()).toContain("radial-gradient");
  await zoomLabel(page).click();
  await expect.poll(size).toBe("20px 20px");
  await button(page, "Zoom in").click();
  await expect.poll(size).toBe("25px 25px");

  await page.reload();
  await expectRendered(page);
  await expect(button(page, "Grid")).toHaveAttribute("aria-pressed", "true");
});

const SEQUENCE = "sequenceDiagram\n  Alice->>Bob: first\n  Bob->>Carol: second\n  Carol->>Alice: third\n";

test("steps through a sequence diagram's messages with buttons and keys", async ({ page, control, dir, home }) => {
  const path = await file(dir, "seq.mmd", SEQUENCE);
  await opened(page, control, path, home);
  const toggle = button(page, "Step through messages");
  const bar = page.getByRole("group", { name: "Message playback" });
  const hidden = preview(page).locator('[data-mermaiden-sequence-state="hidden"]');
  await expect(toggle).toBeVisible();
  await expect(bar).toBeHidden();

  await toggle.click();
  await expect(bar).toBeVisible();
  await expect(bar).toContainText("1 of 3 first");
  await expect(hidden.first()).toBeAttached();
  const previous = button(page, "Previous message");
  const next = button(page, "Next message");
  await expect(previous).toBeDisabled();

  await next.click();
  await expect(bar).toContainText("2 of 3 second");
  // Previous disables itself at the first message; focus moves to Next rather than being lost.
  await previous.click();
  await expect(bar).toContainText("1 of 3 first");
  await expect(next).toBeFocused();

  await preview(page).focus();
  await page.keyboard.press("End");
  await expect(bar).toContainText("All 3 messages");
  await expect(hidden).toHaveCount(0);
  await expect(next).toBeDisabled();
  await page.keyboard.press("Home");
  await expect(bar).toContainText("1 of 3 first");
  await page.keyboard.press("ArrowRight");
  await expect(bar).toContainText("2 of 3 second");

  // A live edit keeps the position.
  await writeFile(path, SEQUENCE.replace("second", "second, edited"));
  await expect(bar).toContainText("2 of 3 second, edited");

  // Hidden for other diagrams; off removes the bar and shows every message.
  await writeFile(path, FLOW);
  await expect(svg(page)).toContainText("Alpha");
  await expect(toggle).toBeHidden();
  await expect(bar).toBeHidden();
  await writeFile(path, SEQUENCE);
  await expect(bar).toContainText("2 of 3 second");
  await toggle.click();
  await expect(bar).toBeHidden();
  await expect(hidden).toHaveCount(0);
});

test("follows the current message when the diagram is zoomed in", async ({ page, control, dir, home }) => {
  const long = `sequenceDiagram\n${Array.from({ length: 30 }, (_, i) => `  A->>B: m${i}`).join("\n")}\n`;
  await opened(page, control, await file(dir, "long.mmd", long), home);
  await button(page, "Step through messages").click();
  await zoomLabel(page).click();
  await preview(page).focus();
  await page.keyboard.press("Home");
  const pane = (await preview(page).boundingBox())!;
  for (const i of [0, 29]) {
    if (i === 29) for (let n = 0; n < 29; n++) await page.keyboard.press("ArrowRight");
    await expect(page.getByRole("group", { name: "Message playback" })).toContainText(`${i + 1} of 30`);
    const label = preview(page).locator("text", { hasText: new RegExp(`^m${i}$`) }).first();
    await expect.poll(async () => inside((await label.boundingBox())!, pane)).toBe(true);
  }
});

test("freezes participant rows at the pane's edges while panning a sequence diagram", async ({ page, control, dir, home }) => {
  const long = `sequenceDiagram\n  participant A as Alpha\n  participant B as Beta\n${Array.from({ length: 30 }, (_, i) => `  A->>B: m${i}`).join("\n")}\n`;
  await opened(page, control, await file(dir, "long.mmd", long), home);
  const toggle = button(page, "Freeze participants");
  const topRows = preview(page).locator('.preview-overlay [data-participant-row="top"]');
  await expect(toggle).toHaveAttribute("aria-pressed", "true");

  // Pan down past the native headers; the frozen copies stay at the pane's top.
  await zoomLabel(page).click();
  await preview(page).focus();
  for (let n = 0; n < 8; n++) await page.keyboard.press("ArrowDown");
  const pane = (await preview(page).boundingBox())!;
  // The native header row (the diagram's top) is scrolled out of the pane.
  await expect.poll(async () => (await svg(page).boundingBox())!.y).toBeLessThan(pane.y - 100);
  await expect(topRows).toHaveCount(2);
  await expect(topRows.filter({ hasText: "Alpha" })).toHaveCount(1);
  const frozen = (await topRows.filter({ hasText: "Alpha" }).boundingBox())!;
  expect(frozen.y).toBeGreaterThanOrEqual(pane.y);
  expect(frozen.y).toBeLessThan(pane.y + 80);

  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-pressed", "false");
  await expect(preview(page).locator(".preview-overlay")).toHaveCount(0);
  await expect(preview(page).locator(".mermaiden-sequence-frozen-underlay")).toHaveCount(0);
  await page.reload();
  await expectRendered(page);
  await expect(button(page, "Freeze participants")).toHaveAttribute("aria-pressed", "false");
  await expect(preview(page).locator(".preview-overlay")).toHaveCount(0);
});

test("freezes only the participants playback has revealed, and hides the toggle for other diagrams", async ({ page, control, dir, home }) => {
  const path = await file(dir, "seq.mmd", SEQUENCE);
  await opened(page, control, path, home);
  const topRows = preview(page).locator('.preview-overlay [data-participant-row="top"]');
  await expect(topRows).toHaveCount(3);
  await button(page, "Step through messages").click();
  await expect(topRows).toHaveCount(2);
  await button(page, "Next message").click();
  await expect(topRows).toHaveCount(3);

  await writeFile(path, FLOW);
  await expect(svg(page)).toContainText("Alpha");
  await expect(button(page, "Freeze participants")).toBeHidden();
  await expect(preview(page).locator(".preview-overlay")).toHaveCount(0);
});
