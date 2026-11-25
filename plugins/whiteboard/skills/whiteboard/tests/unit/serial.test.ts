import { describe, expect, it } from "vitest";
import { Serial } from "../../app/src/serial.ts";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

const settle = () => new Promise((r) => setTimeout(r, 0));

describe("Serial", () => {
  it("starts a request only after the previous one settles, and delivers only the latest", async () => {
    const serial = new Serial<string>();
    const first = deferred<string>();
    const second = deferred<string>();
    const started: string[] = [];
    const delivered: string[] = [];
    serial.run(() => (started.push("first"), first.promise), (r) => delivered.push(r), () => {});
    serial.run(() => (started.push("second"), second.promise), (r) => delivered.push(r), () => {});
    await settle();
    expect(started).toEqual(["first"]);
    first.resolve("stale");
    await settle();
    expect(started).toEqual(["first", "second"]);
    expect(delivered).toEqual([]);
    second.resolve("fresh");
    await settle();
    expect(delivered).toEqual(["fresh"]);
  });

  it("continues after a failed request and reports only the latest failure", async () => {
    const serial = new Serial<string>();
    const failures: unknown[] = [];
    const delivered: string[] = [];
    serial.run(() => Promise.reject(new Error("old")), () => {}, (e) => failures.push(e));
    serial.run(() => Promise.resolve("next"), (r) => delivered.push(r), (e) => failures.push(e));
    await settle();
    expect(failures).toEqual([]);
    expect(delivered).toEqual(["next"]);
    serial.run(() => Promise.reject(new Error("latest")), () => {}, (e) => failures.push(e));
    await settle();
    expect(failures).toHaveLength(1);
  });

  it("drops results after drop()", async () => {
    const serial = new Serial<string>();
    const delivered: string[] = [];
    serial.run(() => Promise.resolve("x"), (r) => delivered.push(r), () => {});
    serial.drop();
    await settle();
    expect(delivered).toEqual([]);
  });
});
