// One request at a time, and only the latest request's result is delivered. A tab's saves go
// through one Serial, so a save left in flight by an orphaned tab can neither overlap a later save
// nor have its response taken for the later save's.

export class Serial<T> {
  #tail: Promise<unknown> = Promise.resolve();
  #latest = 0;

  run(request: () => Promise<T>, deliver: (result: T) => void, fail: (error: unknown) => void): void {
    const token = ++this.#latest;
    const go = () =>
      request().then(
        (result) => {
          if (token === this.#latest) deliver(result);
        },
        (error: unknown) => {
          if (token === this.#latest) fail(error);
        },
      );
    this.#tail = this.#tail.then(go, go);
  }

  /** Drops the results of every request made so far. */
  drop(): void {
    this.#latest++;
  }
}
