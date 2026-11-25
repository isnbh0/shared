// One tab against a model file, driven through `step` with the wiring simulated here.
// Bounds: one tab, one model server. A put's compare-and-swap runs when the server receives it, and
// its response is delivered separately (late, at once, or replaced by a failure). Reads are answered
// when delivered. The doc can be closed elsewhere and reopened. Saves go through the wiring's Serial
// (app/src/serial.ts): a put waits for the previous one to settle, and only the latest put's
// response is fed back. Server-side serialization is covered by workspace.property.test.ts.
import { createHash } from "node:crypto";
import fc from "fast-check";
import { describe, expect, it } from "vitest";
import { editorTextOf, step, type SyncEvent, type SyncState } from "../../app/src/sync.ts";
import type { Disk, Rev } from "../../app/src/types.ts";

const revOf = (text: string): Rev => createHash("sha256").update(text).digest("hex").slice(0, 16) as Rev;

type Op =
  | { kind: "edit"; text: string }
  | { kind: "timer" }
  | { kind: "receivePut" }
  | { kind: "deliverPut"; mode: "ok" | "failRetry" | "failNoRetry" }
  | { kind: "deliverFetch" }
  | { kind: "external"; text: string }
  | { kind: "delete" }
  | { kind: "reload" }
  | { kind: "overwrite" }
  | { kind: "closed" }
  | { kind: "reopen" }
  | { kind: "discard" };

const text = fc.stringMatching(/^[ab]{0,3}$/);
const op: fc.Arbitrary<Op> = fc.oneof(
  { weight: 5, arbitrary: text.map((t) => ({ kind: "edit" as const, text: t })) },
  { weight: 4, arbitrary: fc.constant({ kind: "timer" as const }) },
  { weight: 3, arbitrary: fc.constant({ kind: "receivePut" as const }) },
  {
    weight: 4,
    arbitrary: fc
      .constantFrom("ok" as const, "ok" as const, "failRetry" as const, "failNoRetry" as const)
      .map((mode) => ({ kind: "deliverPut" as const, mode })),
  },
  { weight: 4, arbitrary: fc.constant({ kind: "deliverFetch" as const }) },
  { weight: 2, arbitrary: text.map((t) => ({ kind: "external" as const, text: t })) },
  { weight: 1, arbitrary: fc.constant({ kind: "delete" as const }) },
  { weight: 1, arbitrary: fc.constant({ kind: "reload" as const }) },
  { weight: 1, arbitrary: fc.constant({ kind: "overwrite" as const }) },
  { weight: 1, arbitrary: fc.constant({ kind: "closed" as const }) },
  { weight: 1, arbitrary: fc.constant({ kind: "reopen" as const }) },
  { weight: 1, arbitrary: fc.constant({ kind: "discard" as const }) },
);
const initial: fc.Arbitrary<Disk> = fc.option(text, { nil: undefined }).map((t) =>
  t === undefined ? { rev: null } : { rev: revOf(t), text: t },
);

type PutResult = { kind: "ok"; rev: Rev } | { kind: "conflict"; disk: Disk } | { kind: "gone" };
/** `stale`: a later put superseded it, so the Serial drops its response. */
type Put = { text: string; rev: Rev | null; result?: PutResult; stale: boolean };

class Harness {
  file: Disk;
  open = true; // the doc is in the open set
  state: SyncState = { kind: "unloaded" };
  timer = false;
  puts: Put[] = [];
  fetches = 0;
  /** The person's latest typed text not yet known to be safe; null when nothing is at stake. */
  typed: string | null = null;
  trace: string[] = [];

  constructor(file: Disk) {
    this.file = file;
    this.fetches = 1; // activating the unloaded tab reads it
  }

  private feed(event: SyncEvent): void {
    const result = step(this.state, event);
    for (const effect of result.effects) {
      switch (effect.kind) {
        case "schedule":
          this.timer = true;
          break;
        case "cancel":
          this.timer = false;
          break;
        case "put":
          // The Serial queues the put behind any earlier one and drops the earlier one's response.
          for (const earlier of this.puts) earlier.stale = true;
          this.puts.push({ text: effect.text, rev: effect.rev, stale: false });
          break;
        case "fetch":
          this.fetches++;
          break;
        case "remove":
          break;
      }
    }
    if (result.state === null) {
      expect(result.effects.some((e) => e.kind === "remove")).toBe(true);
      this.restart();
    } else {
      this.state = result.state;
    }
  }

  /** The tab was removed; the person opens a fresh one. In-flight requests of the old tab are dropped. */
  private restart(): void {
    this.state = { kind: "unloaded" };
    this.timer = false;
    this.puts = [];
    this.fetches = 1;
    this.typed = null;
    this.open = true;
  }

  /** A `changed` event from the server: tabs that aren't unloaded fetch. */
  private changed(): void {
    if (this.open && this.state.kind !== "unloaded") this.fetches++;
  }

  private receive(put: Put): void {
    if (put.result) return;
    if (!this.open) {
      put.result = { kind: "gone" };
    } else if (put.rev === this.file.rev) {
      this.file = { rev: revOf(put.text), text: put.text };
      put.result = { kind: "ok", rev: this.file.rev };
      this.changed();
    } else {
      put.result = { kind: "conflict", disk: this.file };
    }
  }

  apply(o: Op): void {
    this.trace.push(`${JSON.stringify(o)}  [state ${JSON.stringify(this.state)} file ${JSON.stringify(this.file)}]`);
    let resetTyped = false;
    switch (o.kind) {
      case "edit":
        // The editor exists only for loaded tabs.
        if (this.state.kind === "unloaded") return;
        this.typed = o.text;
        this.feed({ kind: "edit", draft: o.text });
        break;
      case "timer":
        if (!this.timer) return;
        this.timer = false;
        this.feed({ kind: "timer" });
        break;
      case "receivePut": {
        // Only the head of the Serial's queue has been sent.
        const put = this.puts[0];
        if (put) this.receive(put);
        break;
      }
      case "deliverPut": {
        const put = this.puts.shift();
        if (!put) return;
        if (put.stale) {
          if (o.mode === "ok") this.receive(put);
        } else if (o.mode === "ok") {
          this.receive(put);
          const r = put.result!;
          if (r.kind === "ok") this.feed({ kind: "saveOk", rev: r.rev });
          else if (r.kind === "conflict") this.feed({ kind: "saveConflict", disk: r.disk });
          // gone (404): nothing; the docs event already fed `closed`.
        } else if (put.result) {
          // Applied (or refused) by the server, but the response was lost: a network error.
          this.feed({ kind: "saveFailed", message: "network", retry: true });
        } else {
          // Never reached the server.
          this.feed({ kind: "saveFailed", message: o.mode, retry: o.mode === "failRetry" });
        }
        break;
      }
      case "deliverFetch":
        if (this.fetches === 0) return;
        this.fetches--;
        if (this.open) this.feed({ kind: "remote", disk: this.file });
        break;
      case "external":
        this.file = { rev: revOf(o.text), text: o.text };
        this.changed();
        break;
      case "delete":
        this.file = { rev: null };
        this.changed();
        break;
      case "reload":
        resetTyped = this.state.kind === "conflict";
        this.feed({ kind: "reload" });
        break;
      case "overwrite":
        this.feed({ kind: "overwrite" });
        break;
      case "closed":
        if (!this.open) return;
        this.open = false;
        this.feed({ kind: "closed" });
        break;
      case "reopen":
        // The doc reappears in the open set; the wiring fetches an orphaned tab.
        if (this.open) return;
        this.open = true;
        if (this.state.kind === "orphaned") this.fetches++;
        break;
      case "discard":
        // The person closes the tab and accepts the loss; restart() resets everything.
        this.feed({ kind: "discard" });
        break;
    }
    if (resetTyped) this.typed = null;
    this.check();
  }

  private check(): void {
    const why = () => this.trace.join("\n");
    const editor = editorTextOf(this.state);
    const fileText = this.file.rev === null ? null : this.file.text;
    // Invariant 1: the latest typed text is the current draft or the model file's text.
    if (this.typed !== null) {
      expect(
        editor === this.typed || fileText === this.typed,
        `typed ${JSON.stringify(this.typed)} lost: editor ${JSON.stringify(editor)}, file ${JSON.stringify(fileText)}\n${why()}`,
      ).toBe(true);
    }
    // Invariant 2: settled + synced means the editor shows the model file.
    if (this.state.kind === "synced" && this.puts.length === 0 && this.fetches === 0) {
      expect(editor, `settled synced tab is stale\n${why()}`).toBe(fileText ?? "");
    }
    // Invariant 3: at most one put whose response the tab awaits, and only the head is ever sent.
    expect(this.puts.filter((p) => !p.stale).length, `two puts in flight\n${why()}`).toBeLessThanOrEqual(1);
    expect(this.puts.slice(1).every((p) => p.result === undefined)).toBe(true);
    // Once the tab shows the typed text as saved, the text is no longer at stake.
    if (this.state.kind === "synced" && editor === this.typed) this.typed = null;
  }
}

describe("sync model: one tab against a model file", () => {
  it("keeps typed text, settles to the file, and never has two puts in flight", () => {
    fc.assert(
      fc.property(initial, fc.array(op, { minLength: 1, maxLength: 60 }), (file, ops) => {
        const h = new Harness(file);
        for (const o of ops) h.apply(o);
        // Drain: deliver everything, fire timers, until quiet; invariants are checked at each step.
        for (let i = 0; i < 50 && (h.puts.length > 0 || h.fetches > 0 || h.timer); i++) {
          if (h.puts.length > 0) h.apply({ kind: "deliverPut", mode: "ok" });
          else if (h.fetches > 0) h.apply({ kind: "deliverFetch" });
          else h.apply({ kind: "timer" });
        }
      }),
      { numRuns: 5000 },
    );
  });

  // Fixed sequences for the two holes this model found in the original table. The random search
  // reaches the first only rarely, so it is pinned here.
  it("re-reads after a failed save, so a read dropped while saving cannot leave a stale synced tab", () => {
    const h = new Harness({ rev: revOf("aba"), text: "aba" });
    const ops: Op[] = [
      { kind: "deliverFetch" },
      { kind: "edit", text: "" },
      { kind: "timer" },
      { kind: "external", text: "" },
      { kind: "deliverFetch" }, // arrives while saving: dropped by the table
      { kind: "deliverPut", mode: "failNoRetry" },
      { kind: "edit", text: "aba" }, // back to the old base
      { kind: "deliverFetch" },
    ];
    for (const o of ops) h.apply(o);
    expect(h.state).toEqual({ kind: "synced", disk: { rev: revOf(""), text: "" } });
  });

  it("keeps one save in flight when an orphaned tab with a pending save is reopened and overwritten", () => {
    const h = new Harness({ rev: revOf("a"), text: "a" });
    const ops: Op[] = [
      { kind: "deliverFetch" },
      { kind: "edit", text: "b" },
      { kind: "timer" }, // put 1 in flight
      { kind: "closed" },
      { kind: "reopen" },
      { kind: "deliverFetch" }, // orphaned + remote → conflict
      { kind: "overwrite" }, // put 2 queues behind put 1
      { kind: "deliverPut", mode: "ok" }, // put 1's response: dropped
      { kind: "deliverPut", mode: "ok" }, // put 2 was refused: put 1 already changed the file
    ];
    for (const o of ops) h.apply(o);
    expect(h.state.kind).toBe("conflict");
  });
});
