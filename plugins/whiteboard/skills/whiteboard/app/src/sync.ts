// Per-tab sync state. Every tab's state is a value of SyncState, changed only by `step`, and what
// the tab shows is derived from the state by the view functions below. Pure: no DOM or Vite types.
import type { Disk, Rev } from "./types.ts";

export type Failure = { message: string; retry: boolean; attempt: number };

export type SyncState =
  | { kind: "unloaded" }
  | { kind: "synced"; disk: Disk }
  | { kind: "dirty"; base: Disk; draft: string; failure: Failure | null }
  | { kind: "saving"; base: Disk; sent: string; draft: string; attempt: number }
  | { kind: "conflict"; draft: string; disk: Disk }
  | { kind: "orphaned"; draft: string };

export type SyncEvent =
  | { kind: "edit"; draft: string }
  | { kind: "timer" }
  | { kind: "saveOk"; rev: Rev }
  | { kind: "saveConflict"; disk: Disk }
  | { kind: "saveFailed"; message: string; retry: boolean }
  | { kind: "remote"; disk: Disk }
  | { kind: "reload" }
  | { kind: "overwrite" }
  | { kind: "closed" }
  | { kind: "discard" };

export type Effect =
  | { kind: "schedule"; ms: number }
  | { kind: "cancel" }
  | { kind: "put"; text: string; rev: Rev | null }
  | { kind: "fetch" }
  | { kind: "remove" };

/** `state: null` means the tab is gone; the `remove` effect accompanies it. */
export type Step = { state: SyncState | null; effects: Effect[] };

export const SAVE_DELAY_MS = 400;

export function retryDelay(attempt: number): number {
  return Math.min(2000 * 2 ** attempt, 30_000);
}

/** "d equals disk": the disk has text and the draft is exactly that text. */
export function equalsDisk(draft: string, disk: Disk): boolean {
  return disk.rev !== null && draft === disk.text;
}

const schedule = (ms: number): Effect => ({ kind: "schedule", ms });
const CANCEL: Effect = { kind: "cancel" };
const FETCH: Effect = { kind: "fetch" };
const REMOVE: Effect = { kind: "remove" };
const removed = (...before: Effect[]): Step => ({ state: null, effects: [...before, REMOVE] });

function assertNever(value: never): never {
  throw new Error(`unhandled case: ${JSON.stringify(value)}`);
}

export function step(state: SyncState, event: SyncEvent): Step {
  const unchanged: Step = { state, effects: [] };
  switch (state.kind) {
    case "unloaded":
      switch (event.kind) {
        case "remote":
          return { state: { kind: "synced", disk: event.disk }, effects: [] };
        case "closed":
        case "discard":
          return removed();
        case "edit":
        case "timer":
        case "saveOk":
        case "saveConflict":
        case "saveFailed":
        case "reload":
        case "overwrite":
          return unchanged;
        default:
          return assertNever(event);
      }
    case "synced":
      switch (event.kind) {
        case "edit":
          if (equalsDisk(event.draft, state.disk)) return unchanged;
          return {
            state: { kind: "dirty", base: state.disk, draft: event.draft, failure: null },
            effects: [schedule(SAVE_DELAY_MS)],
          };
        case "remote":
          if (event.disk.rev === state.disk.rev) return unchanged;
          return { state: { kind: "synced", disk: event.disk }, effects: [] };
        case "closed":
        case "discard":
          return removed();
        case "timer":
        case "saveOk":
        case "saveConflict":
        case "saveFailed":
        case "reload":
        case "overwrite":
          return unchanged;
        default:
          return assertNever(event);
      }
    case "dirty":
      switch (event.kind) {
        case "edit":
          if (equalsDisk(event.draft, state.base)) {
            return { state: { kind: "synced", disk: state.base }, effects: [CANCEL] };
          }
          return {
            state: { kind: "dirty", base: state.base, draft: event.draft, failure: null },
            effects: [schedule(SAVE_DELAY_MS)],
          };
        case "timer":
          return {
            state: {
              kind: "saving",
              base: state.base,
              sent: state.draft,
              draft: state.draft,
              attempt: state.failure?.attempt ?? 0,
            },
            effects: [{ kind: "put", text: state.draft, rev: state.base.rev }],
          };
        case "remote":
          if (event.disk.rev === state.base.rev) return unchanged;
          return { state: { kind: "conflict", draft: state.draft, disk: event.disk }, effects: [CANCEL] };
        case "closed":
          return { state: { kind: "orphaned", draft: state.draft }, effects: [CANCEL] };
        case "discard":
          return removed(CANCEL);
        case "saveOk":
        case "saveConflict":
        case "saveFailed":
        case "reload":
        case "overwrite":
          return unchanged;
        default:
          return assertNever(event);
      }
    case "saving":
      switch (event.kind) {
        case "edit":
          return { state: { ...state, draft: event.draft }, effects: [] };
        case "saveOk": {
          const base: Disk = { rev: event.rev, text: state.sent };
          if (state.draft === state.sent) return { state: { kind: "synced", disk: base }, effects: [FETCH] };
          return {
            state: { kind: "dirty", base, draft: state.draft, failure: null },
            effects: [FETCH, schedule(SAVE_DELAY_MS)],
          };
        }
        case "saveConflict":
          // A `remote` that arrived while saving was dropped, so read again.
          return { state: { kind: "conflict", draft: state.draft, disk: event.disk }, effects: [FETCH] };
        case "saveFailed":
          return {
            state: {
              kind: "dirty",
              base: state.base,
              draft: state.draft,
              failure: { message: event.message, retry: event.retry, attempt: state.attempt + 1 },
            },
            // A `remote` that arrived while saving was dropped, so read again.
            effects: event.retry ? [FETCH, schedule(retryDelay(state.attempt))] : [FETCH],
          };
        case "closed":
          return { state: { kind: "orphaned", draft: state.draft }, effects: [] };
        case "discard":
          return removed();
        case "timer":
        case "remote":
        case "reload":
        case "overwrite":
          return unchanged;
        default:
          return assertNever(event);
      }
    case "conflict":
      switch (event.kind) {
        case "edit":
          return { state: { ...state, draft: event.draft }, effects: [] };
        case "remote":
          return { state: { ...state, disk: event.disk }, effects: [] };
        case "reload":
          return { state: { kind: "synced", disk: state.disk }, effects: [] };
        case "overwrite":
          return {
            state: { kind: "saving", base: state.disk, sent: state.draft, draft: state.draft, attempt: 0 },
            effects: [{ kind: "put", text: state.draft, rev: state.disk.rev }],
          };
        case "closed":
          return { state: { kind: "orphaned", draft: state.draft }, effects: [] };
        case "discard":
          return removed();
        case "timer":
        case "saveOk":
        case "saveConflict":
        case "saveFailed":
          return unchanged;
        default:
          return assertNever(event);
      }
    case "orphaned":
      switch (event.kind) {
        case "edit":
          return { state: { kind: "orphaned", draft: event.draft }, effects: [] };
        case "remote":
          return { state: { kind: "conflict", draft: state.draft, disk: event.disk }, effects: [] };
        case "discard":
          return removed();
        case "timer":
        case "saveOk":
        case "saveConflict":
        case "saveFailed":
        case "reload":
        case "overwrite":
        case "closed":
          return unchanged;
        default:
          return assertNever(event);
      }
    default:
      return assertNever(state);
  }
}

// ---- Views: what a tab shows, computed from its state. ----

export type View = { kind: "text"; text: string } | { kind: "missing" };

/** What the preview renders; null for `unloaded` (the wiring reads the tab first). */
export function viewOf(state: SyncState): View | null {
  switch (state.kind) {
    case "unloaded":
      return null;
    case "synced":
      return state.disk.rev === null ? { kind: "missing" } : { kind: "text", text: state.disk.text };
    case "dirty":
    case "saving":
    case "conflict":
    case "orphaned":
      return { kind: "text", text: state.draft };
    default:
      return assertNever(state);
  }
}

/** What the editor holds; null for `unloaded`. */
export function editorTextOf(state: SyncState): string | null {
  switch (state.kind) {
    case "unloaded":
      return null;
    case "synced":
      return state.disk.rev === null ? "" : state.disk.text;
    case "dirty":
    case "saving":
    case "conflict":
    case "orphaned":
      return state.draft;
    default:
      return assertNever(state);
  }
}

export function statusOf(state: SyncState): string {
  switch (state.kind) {
    case "unloaded":
      return "Loading…";
    case "synced":
      return state.disk.rev === null ? "Missing on disk" : "Saved";
    case "dirty":
      if (!state.failure) return "Unsaved changes";
      return state.failure.retry ? "Save failed, retrying" : `Save failed: ${state.failure.message}`;
    case "saving":
      return "Saving…";
    case "conflict":
      return "This file changed on disk while you were editing.";
    case "orphaned":
      return "This file was closed elsewhere. Your unsaved text is kept here; copy it before closing the tab.";
    default:
      return assertNever(state);
  }
}

export function markOf(state: SyncState): { symbol: string; label: string } | undefined {
  switch (state.kind) {
    case "dirty":
    case "saving":
      return { symbol: "•", label: "unsaved" };
    case "conflict":
    case "orphaned":
      return { symbol: "!", label: "conflict" };
    case "unloaded":
    case "synced":
      return undefined;
    default:
      return assertNever(state);
  }
}

/** Whether closing the tab or unloading the page would lose text that is not on disk. */
export function hasUnsaved(state: SyncState): boolean {
  return state.kind === "dirty" || state.kind === "saving" || state.kind === "conflict" || state.kind === "orphaned";
}
