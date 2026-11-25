// The per-tab sync table, checked case by case. Expected results are written here from the spec's
// transition table, independent of sync.ts: the only things imported are the API under test.
import { describe, expect, it } from "vitest";
import {
  editorTextOf,
  step,
  viewOf,
  type Effect,
  type Step,
  type SyncEvent,
  type SyncState,
} from "../../app/src/sync.ts";
import type { Disk, Rev } from "../../app/src/types.ts";

const revA = "aaaaaaaaaaaaaaaa" as Rev;
const revB = "bbbbbbbbbbbbbbbb" as Rev;
const revC = "cccccccccccccccc" as Rev;

const diskA: Disk = { rev: revA, text: "alpha" };
const diskB: Disk = { rev: revB, text: "beta" };
const missing: Disk = { rev: null };

const STATE_KINDS = ["unloaded", "synced", "dirty", "saving", "conflict", "orphaned"] as const;
const EVENT_KINDS = [
  "edit",
  "timer",
  "saveOk",
  "saveConflict",
  "saveFailed",
  "remote",
  "reload",
  "overwrite",
  "closed",
  "discard",
] as const;

type StateKind = (typeof STATE_KINDS)[number];
type EventKind = (typeof EVENT_KINDS)[number];

// Representative states: each guard gets a value on both sides.
const STATES: SyncState[] = [
  { kind: "unloaded" },
  { kind: "synced", disk: diskA },
  { kind: "synced", disk: missing },
  { kind: "dirty", base: diskA, draft: "draft", failure: null },
  { kind: "dirty", base: missing, draft: "x", failure: { message: "boom", retry: true, attempt: 2 } },
  { kind: "dirty", base: diskA, draft: "d", failure: { message: "bad", retry: false, attempt: 1 } },
  { kind: "saving", base: diskA, sent: "s", draft: "s", attempt: 0 },
  { kind: "saving", base: diskA, sent: "s", draft: "s2", attempt: 3 },
  { kind: "saving", base: missing, sent: "n", draft: "n", attempt: 5 },
  { kind: "conflict", draft: "c", disk: diskB },
  { kind: "conflict", draft: "alpha", disk: missing },
  { kind: "orphaned", draft: "o" },
];

// Representative events: drafts equal and unequal to diskA's text, and the empty draft (which a
// missing disk does not equal); remotes with the matching rev, a differing rev, and a missing disk.
const EVENTS: SyncEvent[] = [
  { kind: "edit", draft: "alpha" },
  { kind: "edit", draft: "other" },
  { kind: "edit", draft: "" },
  { kind: "timer" },
  { kind: "saveOk", rev: revC },
  { kind: "saveConflict", disk: diskB },
  { kind: "saveConflict", disk: missing },
  { kind: "saveFailed", message: "net", retry: true },
  { kind: "saveFailed", message: "bad", retry: false },
  { kind: "remote", disk: diskA },
  { kind: "remote", disk: { rev: revA, text: "alpha" } },
  { kind: "remote", disk: diskB },
  { kind: "remote", disk: missing },
  { kind: "reload" },
  { kind: "overwrite" },
  { kind: "closed" },
  { kind: "discard" },
];

// ---- The expected-results table: one row per (state kind, event kind), mirroring the spec. ----

/** Spec: "d equals disk" means the disk has text and the draft is exactly that text. */
const draftEqualsDisk = (d: string, disk: Disk): boolean => disk.rev !== null && disk.text === d;

const UNCHANGED = "unchanged" as const;
type Expected = Step | typeof UNCHANGED;
type Row = (s: SyncState, e: SyncEvent) => Expected;

const sched = (ms: number): Effect => ({ kind: "schedule", ms });
const cancel: Effect = { kind: "cancel" };
const fetch: Effect = { kind: "fetch" };
const remove: Effect = { kind: "remove" };
const gone = (...effects: Effect[]): Step => ({ state: null, effects });

// Narrowing helpers so rows can read fields; rows are only ever called with the matching kinds.
function as<K extends SyncState["kind"]>(s: SyncState, k: K): Extract<SyncState, { kind: K }> {
  if (s.kind !== k) throw new Error(`expected ${k}, got ${s.kind}`);
  return s as Extract<SyncState, { kind: K }>;
}
function ev<K extends SyncEvent["kind"]>(e: SyncEvent, k: K): Extract<SyncEvent, { kind: K }> {
  if (e.kind !== k) throw new Error(`expected ${k}, got ${e.kind}`);
  return e as Extract<SyncEvent, { kind: K }>;
}

const fall: Row = () => UNCHANGED;

const TABLE: Record<StateKind, Record<EventKind, Row>> = {
  unloaded: {
    edit: fall,
    timer: fall,
    saveOk: fall,
    saveConflict: fall,
    saveFailed: fall,
    remote: (_s, e) => ({ state: { kind: "synced", disk: ev(e, "remote").disk }, effects: [] }),
    reload: fall,
    overwrite: fall,
    closed: () => gone(remove),
    discard: () => gone(remove),
  },
  synced: {
    edit: (s, e) => {
      const { disk } = as(s, "synced");
      const { draft } = ev(e, "edit");
      if (draftEqualsDisk(draft, disk)) return UNCHANGED;
      return { state: { kind: "dirty", base: disk, draft, failure: null }, effects: [sched(400)] };
    },
    timer: fall,
    saveOk: fall,
    saveConflict: fall,
    saveFailed: fall,
    remote: (s, e) => {
      const r = ev(e, "remote").disk;
      if (r.rev === as(s, "synced").disk.rev) return UNCHANGED;
      return { state: { kind: "synced", disk: r }, effects: [] };
    },
    reload: fall,
    overwrite: fall,
    closed: () => gone(remove),
    discard: () => gone(remove),
  },
  dirty: {
    edit: (s, e) => {
      const { base } = as(s, "dirty");
      const { draft } = ev(e, "edit");
      if (draftEqualsDisk(draft, base)) return { state: { kind: "synced", disk: base }, effects: [cancel] };
      return { state: { kind: "dirty", base, draft, failure: null }, effects: [sched(400)] };
    },
    timer: (s) => {
      const d = as(s, "dirty");
      return {
        state: { kind: "saving", base: d.base, sent: d.draft, draft: d.draft, attempt: d.failure ? d.failure.attempt : 0 },
        effects: [{ kind: "put", text: d.draft, rev: d.base.rev }],
      };
    },
    saveOk: fall,
    saveConflict: fall,
    saveFailed: fall,
    remote: (s, e) => {
      const d = as(s, "dirty");
      const r = ev(e, "remote").disk;
      if (r.rev === d.base.rev) return UNCHANGED;
      return { state: { kind: "conflict", draft: d.draft, disk: r }, effects: [cancel] };
    },
    reload: fall,
    overwrite: fall,
    closed: (s) => ({ state: { kind: "orphaned", draft: as(s, "dirty").draft }, effects: [cancel] }),
    discard: () => gone(cancel, remove),
  },
  saving: {
    edit: (s, e) => ({ state: { ...as(s, "saving"), draft: ev(e, "edit").draft }, effects: [] }),
    timer: fall,
    saveOk: (s, e) => {
      const sv = as(s, "saving");
      const base: Disk = { rev: ev(e, "saveOk").rev, text: sv.sent };
      if (sv.draft === sv.sent) return { state: { kind: "synced", disk: base }, effects: [fetch] };
      return { state: { kind: "dirty", base, draft: sv.draft, failure: null }, effects: [fetch, sched(400)] };
    },
    saveConflict: (s, e) => ({
      state: { kind: "conflict", draft: as(s, "saving").draft, disk: ev(e, "saveConflict").disk },
      effects: [fetch],
    }),
    saveFailed: (s, e) => {
      const sv = as(s, "saving");
      const f = ev(e, "saveFailed");
      return {
        state: {
          kind: "dirty",
          base: sv.base,
          draft: sv.draft,
          failure: { message: f.message, retry: f.retry, attempt: sv.attempt + 1 },
        },
        effects: f.retry ? [fetch, sched(Math.min(2000 * Math.pow(2, sv.attempt), 30000))] : [fetch],
      };
    },
    remote: fall,
    reload: fall,
    overwrite: fall,
    closed: (s) => ({ state: { kind: "orphaned", draft: as(s, "saving").draft }, effects: [] }),
    discard: () => gone(remove),
  },
  conflict: {
    edit: (s, e) => ({ state: { kind: "conflict", draft: ev(e, "edit").draft, disk: as(s, "conflict").disk }, effects: [] }),
    timer: fall,
    saveOk: fall,
    saveConflict: fall,
    saveFailed: fall,
    remote: (s, e) => ({ state: { kind: "conflict", draft: as(s, "conflict").draft, disk: ev(e, "remote").disk }, effects: [] }),
    reload: (s) => ({ state: { kind: "synced", disk: as(s, "conflict").disk }, effects: [] }),
    overwrite: (s) => {
      const c = as(s, "conflict");
      return {
        state: { kind: "saving", base: c.disk, sent: c.draft, draft: c.draft, attempt: 0 },
        effects: [{ kind: "put", text: c.draft, rev: c.disk.rev }],
      };
    },
    closed: (s) => ({ state: { kind: "orphaned", draft: as(s, "conflict").draft }, effects: [] }),
    discard: () => gone(remove),
  },
  orphaned: {
    edit: (_s, e) => ({ state: { kind: "orphaned", draft: ev(e, "edit").draft }, effects: [] }),
    timer: fall,
    saveOk: fall,
    saveConflict: fall,
    saveFailed: fall,
    remote: (s, e) => ({ state: { kind: "conflict", draft: as(s, "orphaned").draft, disk: ev(e, "remote").disk }, effects: [] }),
    reload: fall,
    overwrite: fall,
    closed: fall,
    discard: () => gone(remove),
  },
};

const label = (x: SyncState | SyncEvent): string => JSON.stringify(x);

describe("sync step: exhaustive table", () => {
  it("represents all 6 state kinds and all 10 event kinds", () => {
    expect(new Set(STATES.map((s) => s.kind))).toEqual(new Set(STATE_KINDS));
    expect(new Set(EVENTS.map((e) => e.kind))).toEqual(new Set(EVENT_KINDS));
    for (const k of STATE_KINDS) expect(Object.keys(TABLE[k]).sort()).toEqual([...EVENT_KINDS].sort());
  });

  const cases = STATES.flatMap((s) => EVENTS.map((e) => [s, e] as const));
  it.each(cases.map(([s, e]) => [label(s), label(e), s, e] as const))("%s + %s", (_ls, _le, s, e) => {
    const input = structuredClone(s);
    const expected = TABLE[s.kind][e.kind](s, e);
    const got = step(s, e);
    if (expected === UNCHANGED) {
      expect(got.state).toEqual(input);
      expect(got.effects).toEqual([]);
    } else {
      expect(got).toEqual(expected);
    }
    // step is pure: the input is not mutated.
    expect(s).toEqual(input);
  });

  it("emits put only on dirty + timer and conflict + overwrite", () => {
    for (const [s, e] of cases) {
      const hasPut = step(s, e).effects.some((x) => x.kind === "put");
      const allowed = (s.kind === "dirty" && e.kind === "timer") || (s.kind === "conflict" && e.kind === "overwrite");
      expect(hasPut, `${label(s)} + ${label(e)}`).toBe(allowed);
    }
  });

  it("pairs a null state with a remove effect and nothing else", () => {
    for (const [s, e] of cases) {
      const got = step(s, e);
      expect(got.state === null, `${label(s)} + ${label(e)}`).toBe(got.effects.some((x) => x.kind === "remove"));
    }
  });
});

describe("sync step: guards with literal expectations", () => {
  it("synced + edit equal to the disk text is unchanged", () => {
    expect(step({ kind: "synced", disk: diskA }, { kind: "edit", draft: "alpha" })).toEqual({
      state: { kind: "synced", disk: diskA },
      effects: [],
    });
  });

  it("synced(missing) + edit of the empty string becomes dirty: a missing disk equals no draft", () => {
    expect(step({ kind: "synced", disk: missing }, { kind: "edit", draft: "" })).toEqual({
      state: { kind: "dirty", base: { rev: null }, draft: "", failure: null },
      effects: [{ kind: "schedule", ms: 400 }],
    });
  });

  it("synced + remote with the same rev is unchanged, with a differing rev or missing disk replaces", () => {
    const s: SyncState = { kind: "synced", disk: diskA };
    expect(step(s, { kind: "remote", disk: { rev: revA, text: "alpha" } })).toEqual({ state: s, effects: [] });
    expect(step(s, { kind: "remote", disk: diskB })).toEqual({ state: { kind: "synced", disk: diskB }, effects: [] });
    expect(step(s, { kind: "remote", disk: missing })).toEqual({ state: { kind: "synced", disk: { rev: null } }, effects: [] });
  });

  it("dirty + edit back to the base text returns to synced and cancels; another edit clears failure", () => {
    const s: SyncState = { kind: "dirty", base: diskA, draft: "x", failure: { message: "m", retry: true, attempt: 1 } };
    expect(step(s, { kind: "edit", draft: "alpha" })).toEqual({
      state: { kind: "synced", disk: diskA },
      effects: [{ kind: "cancel" }],
    });
    expect(step(s, { kind: "edit", draft: "y" })).toEqual({
      state: { kind: "dirty", base: diskA, draft: "y", failure: null },
      effects: [{ kind: "schedule", ms: 400 }],
    });
  });

  it("dirty + timer carries the failure attempt and puts against base.rev (null for a missing base)", () => {
    expect(
      step({ kind: "dirty", base: missing, draft: "x", failure: { message: "m", retry: true, attempt: 2 } }, { kind: "timer" }),
    ).toEqual({
      state: { kind: "saving", base: { rev: null }, sent: "x", draft: "x", attempt: 2 },
      effects: [{ kind: "put", text: "x", rev: null }],
    });
    expect(step({ kind: "dirty", base: diskA, draft: "x", failure: null }, { kind: "timer" })).toEqual({
      state: { kind: "saving", base: diskA, sent: "x", draft: "x", attempt: 0 },
      effects: [{ kind: "put", text: "x", rev: revA }],
    });
  });

  it("dirty + remote: same rev unchanged; differing rev or missing disk goes to conflict and cancels", () => {
    const s: SyncState = { kind: "dirty", base: diskA, draft: "x", failure: null };
    expect(step(s, { kind: "remote", disk: { rev: revA, text: "alpha" } })).toEqual({ state: s, effects: [] });
    expect(step(s, { kind: "remote", disk: diskB })).toEqual({
      state: { kind: "conflict", draft: "x", disk: diskB },
      effects: [{ kind: "cancel" }],
    });
    expect(step(s, { kind: "remote", disk: missing })).toEqual({
      state: { kind: "conflict", draft: "x", disk: { rev: null } },
      effects: [{ kind: "cancel" }],
    });
  });

  it("saving + saveOk: draft === sent goes synced with fetch; otherwise dirty with fetch then schedule", () => {
    expect(step({ kind: "saving", base: diskA, sent: "s", draft: "s", attempt: 2 }, { kind: "saveOk", rev: revC })).toEqual({
      state: { kind: "synced", disk: { rev: revC, text: "s" } },
      effects: [{ kind: "fetch" }],
    });
    expect(step({ kind: "saving", base: diskA, sent: "s", draft: "t", attempt: 2 }, { kind: "saveOk", rev: revC })).toEqual({
      state: { kind: "dirty", base: { rev: revC, text: "s" }, draft: "t", failure: null },
      effects: [{ kind: "fetch" }, { kind: "schedule", ms: 400 }],
    });
  });

  it.each([0, 1, 2, 3, 4, 5, 10])("saving(attempt %i) + saveFailed backs off min(2000 * 2^attempt, 30000)", (attempt) => {
    const s: SyncState = { kind: "saving", base: diskA, sent: "s", draft: "t", attempt };
    const delay = Math.min(2000 * 2 ** attempt, 30000);
    expect(step(s, { kind: "saveFailed", message: "net", retry: true })).toEqual({
      state: { kind: "dirty", base: diskA, draft: "t", failure: { message: "net", retry: true, attempt: attempt + 1 } },
      effects: [{ kind: "fetch" }, { kind: "schedule", ms: delay }],
    });
    expect(step(s, { kind: "saveFailed", message: "bad", retry: false })).toEqual({
      state: { kind: "dirty", base: diskA, draft: "t", failure: { message: "bad", retry: false, attempt: attempt + 1 } },
      effects: [{ kind: "fetch" }],
    });
  });

  it("backoff literal values", () => {
    const at = (attempt: number) =>
      step({ kind: "saving", base: diskA, sent: "s", draft: "s", attempt }, { kind: "saveFailed", message: "m", retry: true })
        .effects.filter((e) => e.kind === "schedule");
    expect(at(0)).toEqual([{ kind: "schedule", ms: 2000 }]);
    expect(at(1)).toEqual([{ kind: "schedule", ms: 4000 }]);
    expect(at(3)).toEqual([{ kind: "schedule", ms: 16000 }]);
    expect(at(4)).toEqual([{ kind: "schedule", ms: 30000 }]);
  });

  it("conflict + overwrite puts against the conflicting disk's rev; reload adopts that disk", () => {
    const c: SyncState = { kind: "conflict", draft: "mine", disk: diskB };
    expect(step(c, { kind: "overwrite" })).toEqual({
      state: { kind: "saving", base: diskB, sent: "mine", draft: "mine", attempt: 0 },
      effects: [{ kind: "put", text: "mine", rev: revB }],
    });
    expect(step(c, { kind: "reload" })).toEqual({ state: { kind: "synced", disk: diskB }, effects: [] });
    expect(step({ kind: "conflict", draft: "mine", disk: missing }, { kind: "overwrite" })).toEqual({
      state: { kind: "saving", base: { rev: null }, sent: "mine", draft: "mine", attempt: 0 },
      effects: [{ kind: "put", text: "mine", rev: null }],
    });
  });

  it("removal steps: dirty + discard cancels then removes; others just remove", () => {
    expect(step({ kind: "dirty", base: diskA, draft: "x", failure: null }, { kind: "discard" })).toEqual({
      state: null,
      effects: [{ kind: "cancel" }, { kind: "remove" }],
    });
    expect(step({ kind: "orphaned", draft: "o" }, { kind: "discard" })).toEqual({ state: null, effects: [{ kind: "remove" }] });
    expect(step({ kind: "unloaded" }, { kind: "closed" })).toEqual({ state: null, effects: [{ kind: "remove" }] });
  });
});

describe("sync views", () => {
  const cases: [SyncState, ReturnType<typeof viewOf>, string | null][] = [
    [{ kind: "unloaded" }, null, null],
    [{ kind: "synced", disk: diskA }, { kind: "text", text: "alpha" }, "alpha"],
    [{ kind: "synced", disk: missing }, { kind: "missing" }, ""],
    [{ kind: "synced", disk: { rev: revB, text: "" } }, { kind: "text", text: "" }, ""],
    [{ kind: "dirty", base: diskA, draft: "d", failure: null }, { kind: "text", text: "d" }, "d"],
    [{ kind: "saving", base: diskA, sent: "s", draft: "s2", attempt: 0 }, { kind: "text", text: "s2" }, "s2"],
    [{ kind: "conflict", draft: "c", disk: diskB }, { kind: "text", text: "c" }, "c"],
    [{ kind: "conflict", draft: "c", disk: missing }, { kind: "text", text: "c" }, "c"],
    [{ kind: "orphaned", draft: "o" }, { kind: "text", text: "o" }, "o"],
  ];

  it("covers every state kind", () => {
    expect(new Set(cases.map(([s]) => s.kind))).toEqual(new Set(STATE_KINDS));
  });

  it.each(cases.map(([s, v, t]) => [label(s), s, v, t] as const))("%s", (_l, s, view, text) => {
    expect(viewOf(s)).toEqual(view);
    expect(editorTextOf(s)).toBe(text);
  });
});
