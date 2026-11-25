// The whiteboard page: tabs for the open set, a live preview, and an editor per tab. Every tab's
// state is a SyncState changed only by `step`; what the page shows is derived from it.
import "mermaiden-toolkit/relationships.css";
import "mermaiden-toolkit/sequence.css";
import "./styles.css";
import {
  closeDoc,
  connectEvents,
  NotOpenError,
  putDoc,
  readDoc,
  type Doc,
  type DocId,
  type PutResult,
} from "./api.ts";
import { EditorPane } from "./editor.ts";
import { Preview, sameView, type ViewState } from "./preview.ts";
import { Serial } from "./serial.ts";
import { mermaidenViewLink, type ShareResult } from "./share.ts";
import { parseRoute, replaceRoute } from "./route.ts";
import {
  editorTextOf,
  hasUnsaved,
  markOf,
  statusOf,
  step,
  viewOf,
  type Effect,
  type SyncEvent,
  type SyncState,
} from "./sync.ts";
import { chooseActive, TabBar, type Active } from "./tabs.ts";
import { zoomPercent } from "./view-math.ts";

const panel = document.getElementById("panel")!;
const message = document.getElementById("message")!;
const workspaceEl = document.getElementById("workspace")!;
const editButton = document.getElementById("edit")!;
const zoomResetButton = document.getElementById("zoom-reset")!;
const scrollPanButton = document.getElementById("scroll-pan")!;
const highlightButton = document.getElementById("highlight")!;
const gridButton = document.getElementById("grid")!;
const playbackButton = document.getElementById("playback")!;
const freezeButton = document.getElementById("freeze")!;
const FREEZE_TITLE = freezeButton.title;
const playbackBar = document.getElementById("playback-bar")!;
const playbackPrevious = document.getElementById("playback-previous") as HTMLButtonElement;
const playbackNext = document.getElementById("playback-next") as HTMLButtonElement;
const playbackPosition = document.getElementById("playback-position")!;
const playbackLabel = document.getElementById("playback-label")!;
const shareButton = document.getElementById("share")!;
const shareNote = document.getElementById("share-note")!;
const previewEl = document.getElementById("preview")!;
const statusEl = document.getElementById("status")!;
const conflictEl = document.getElementById("conflict")!;
const editorEl = document.getElementById("editor")!;
const preview = new Preview(previewEl, {
  view: (state) => {
    const percent = zoomPercent(state.t.k);
    zoomResetButton.textContent = `${percent}%`;
    zoomResetButton.setAttribute("aria-label", `Zoom is ${percent} percent; activate for 100 percent`);
  },
  kind: (kind) => {
    highlightButton.hidden = kind !== null && kind !== "flowchart";
    playbackButton.hidden = kind !== "sequence";
    freezeButton.hidden = kind !== "sequence";
  },
  freezeNote: (reason) => {
    freezeButton.title = reason ? `${FREEZE_TITLE}. ${reason}` : FREEZE_TITLE;
  },
  playback: (position) => {
    playbackBar.hidden = position === null;
    if (!position) return;
    playbackPosition.textContent = position.overview
      ? `All ${position.count} messages`
      : `${position.index + 1} of ${position.count}`;
    playbackLabel.textContent = position.label;
    playbackPrevious.disabled = position.index === 0;
    playbackNext.disabled = position.overview;
    // A button that disables itself under focus would drop focus to the page; hand it across.
    if (document.activeElement === playbackPrevious && playbackPrevious.disabled) playbackNext.focus();
    if (document.activeElement === playbackNext && playbackNext.disabled) playbackPrevious.focus();
  },
});
const editor = new EditorPane(editorEl, (id, text) => dispatch(id, { kind: "edit", draft: text }));

type Tab = {
  doc: Doc;
  state: SyncState;
  timer: ReturnType<typeof setTimeout> | undefined;
  /** Only the latest read's result is delivered, so reads cannot arrive out of order. */
  fetchSeq: number;
  /** Saves run one at a time and only the latest save's response is fed back. */
  saves: Serial<PutResult>;
  editing: boolean;
};

/** Tabs in display order: the server's open set plus orphaned tabs kept for their drafts. */
let order: DocId[] = [];
const tabs = new Map<DocId, Tab>();
/** Each tab's pan and zoom, saved when the person switches away from it. */
const views = new Map<DocId, ViewState>();
/** Ids the page asked the server to close, ignored in `docs` until the server confirms. */
const pendingClose = new Set<DocId>();
let active: Active = { kind: "empty" };
let loaded = false;

const tabBar = new TabBar(document.getElementById("tabs")!, panel.id, {
  select: (id) => activate(id),
  close: (id) => requestClose(id),
});

function shownDocs(): Doc[] {
  return order.map((id) => tabs.get(id)!.doc);
}

function activeTab(): Tab | undefined {
  return active.kind === "doc" ? tabs.get(active.doc.id) : undefined;
}

// ---- Sync: dispatch an event, run its effects, and derive what the tab shows. ----

function dispatch(id: DocId, event: SyncEvent): void {
  const tab = tabs.get(id);
  if (!tab) return;
  const next = step(tab.state, event);
  if (next.state) tab.state = next.state;
  for (const effect of next.effects) run(tab, effect);
  if (next.state) refresh(tab);
}

function run(tab: Tab, effect: Effect): void {
  const id = tab.doc.id;
  switch (effect.kind) {
    case "schedule":
      clearTimeout(tab.timer);
      tab.timer = setTimeout(() => {
        tab.timer = undefined;
        dispatch(id, { kind: "timer" });
      }, effect.ms);
      return;
    case "cancel":
      clearTimeout(tab.timer);
      tab.timer = undefined;
      return;
    case "put": {
      const { text, rev } = effect;
      tab.saves.run(
        () => putDoc(id, text, rev),
        (result) => {
          switch (result.kind) {
            case "ok":
              return dispatch(id, { kind: "saveOk", rev: result.rev });
            case "conflict":
              return dispatch(id, { kind: "saveConflict", disk: result.current });
            case "gone":
              // Retry: if the file really closed, the `docs` event that follows feeds `closed`;
              // if it was reopened first, the retry saves it.
              return dispatch(id, { kind: "saveFailed", message: "not open", retry: true });
            case "failed":
              return dispatch(id, { kind: "saveFailed", message: result.message, retry: result.retry });
          }
        },
        (error: unknown) =>
          dispatch(id, {
            kind: "saveFailed",
            message: error instanceof Error ? error.message : String(error),
            retry: false,
          }),
      );
      return;
    }
    case "fetch":
      fetchTab(tab);
      return;
    case "remove":
      removeTab(id);
      return;
  }
}

const FETCH_RETRY_MAX_MS = 5000;

/** Whether the tab's text has been asked for, so later changes must be read too. */
function fetched(tab: Tab): boolean {
  return tab.state.kind !== "unloaded" || tab.fetchSeq > 0;
}

/** Reads the tab; a failed latest read is retried with backoff until a newer read replaces it. */
function fetchTab(tab: Tab, attempt = 0): void {
  const seq = ++tab.fetchSeq;
  const id = tab.doc.id;
  const current = () => tabs.get(id) === tab && tab.fetchSeq === seq;
  readDoc(id).then(
    ({ disk }) => {
      if (current()) dispatch(id, { kind: "remote", disk });
    },
    (error: unknown) => {
      if (error instanceof NotOpenError) return;
      console.error(error);
      setTimeout(() => {
        if (current()) fetchTab(tab, attempt + 1);
      }, Math.min(250 * 2 ** attempt, FETCH_RETRY_MAX_MS));
    },
  );
}

/** Brings the editor, preview, status, banner, and tab marks in line with the tab's state. */
function refresh(tab: Tab): void {
  const text = editorTextOf(tab.state);
  if (text !== null) {
    if (editor.hasModel(tab.doc.id)) editor.replace(tab.doc.id, text);
    else if (tab.editing && activeTab() === tab && editor.loaded) editor.show(tab.doc.id, text);
  }
  if (activeTab() === tab) {
    const view = viewOf(tab.state);
    if (view && !sameView(view, preview.shown)) void preview.render(view);
    statusEl.textContent = statusOf(tab.state);
    conflictEl.hidden = tab.state.kind !== "conflict";
  }
  renderTabs();
}

function renderTabs(): void {
  const activeId = active.kind === "doc" ? active.doc.id : undefined;
  tabBar.render(shownDocs(), activeId, (id) => {
    const tab = tabs.get(id);
    return tab ? markOf(tab.state) : undefined;
  });
}

function removeTab(id: DocId): void {
  const tab = tabs.get(id);
  if (!tab) return;
  clearTimeout(tab.timer);
  tab.saves.drop();
  const previous = shownDocs();
  tabs.delete(id);
  order = order.filter((other) => other !== id);
  editor.dispose(id);
  views.delete(id);
  if (active.kind === "doc" && active.doc.id === id) show(chooseActive(shownDocs(), { kind: "doc", id }, previous), previous);
  else renderTabs();
}

// ---- Closing: the person's choice, guarded when a draft would be lost. ----

function requestClose(id: DocId): void {
  const tab = tabs.get(id);
  if (!tab) return;
  if (!hasUnsaved(tab.state)) {
    void closeDoc(id).catch((error: unknown) => console.error(error));
    return;
  }
  if (!confirm(`Discard unsaved changes to ${tab.doc.name}?`)) return;
  const orphaned = tab.state.kind === "orphaned";
  if (!orphaned) {
    pendingClose.add(id);
    // Kept until a `docs` event without the id arrives, so an older `docs` cannot restore the tab.
    void closeDoc(id).catch((error: unknown) => {
      console.error(error);
      pendingClose.delete(id);
    });
  }
  dispatch(id, { kind: "discard" });
}

window.addEventListener("beforeunload", (event) => {
  if ([...tabs.values()].some((tab) => hasUnsaved(tab.state))) {
    event.preventDefault();
    event.returnValue = "";
  }
});

// ---- Active tab and panel. ----

function show(next: Active, previousDocs: Doc[] = shownDocs()): void {
  const before = active;
  const switching = before.kind !== "doc" || next.kind !== "doc" || before.doc.id !== next.doc.id;
  if (switching && before.kind === "doc" && tabs.has(before.doc.id) && preview.shown) {
    views.set(before.doc.id, preview.viewport.state);
  }
  active = next;
  renderTabs();
  const tab = activeTab();
  if (next.kind === "doc" && tab) {
    replaceRoute(next.doc);
    panel.setAttribute("aria-labelledby", TabBar.tabId(next.doc.id));
    message.hidden = true;
    workspaceEl.hidden = false;
    if (switching) {
      preview.clear(views.get(next.doc.id));
      showEditor(tab);
      if (tab.state.kind === "unloaded") fetchTab(tab);
    }
    refresh(tab);
  } else {
    panel.removeAttribute("aria-labelledby");
    workspaceEl.hidden = true;
    message.hidden = false;
    preview.clear();
    if (next.kind === "empty") {
      if (previousDocs.length > 0) replaceRoute(undefined);
      message.textContent = "No files open. Run `wb open <path>` to add one.";
    } else {
      message.textContent = "This file isn't open. Run `wb open <path>` to show it.";
    }
  }
}

/** Shows or hides the editor pane for the active tab, loading Monaco on first use. */
function showEditor(tab: Tab): void {
  editButton.setAttribute("aria-pressed", String(tab.editing));
  editorEl.hidden = !tab.editing;
  if (!tab.editing) return;
  // Until this tab's text loads, show no model; `refresh` attaches it when the read arrives.
  if (editorTextOf(tab.state) === null) editor.detach();
  void editor.load().then(() => {
    if (activeTab() !== tab || !tab.editing) return;
    const text = editorTextOf(tab.state);
    if (text !== null) editor.show(tab.doc.id, text);
    else editor.detach();
  });
}

function activate(id: DocId): void {
  const tab = tabs.get(id);
  if (tab) show({ kind: "doc", doc: tab.doc });
}

function onDocs(next: Doc[], reconnected: boolean): void {
  const previous = loaded ? shownDocs() : [];
  loaded = true;
  const incoming = next.filter((doc) => !pendingClose.has(doc.id));
  const ids = new Set(incoming.map((doc) => doc.id));
  for (const id of pendingClose) if (!next.some((doc) => doc.id === id)) pendingClose.delete(id);

  for (const doc of incoming) {
    const tab = tabs.get(doc.id);
    if (!tab) {
      tabs.set(doc.id, {
        doc,
        state: { kind: "unloaded" },
        timer: undefined,
        fetchSeq: 0,
        saves: new Serial<PutResult>(),
        editing: false,
      });
      order.push(doc.id);
    } else {
      tab.doc = doc;
      if (tab.state.kind === "orphaned" || (reconnected && fetched(tab))) fetchTab(tab);
    }
  }
  for (const id of [...order]) {
    if (!ids.has(id)) dispatch(id, { kind: "closed" });
  }

  const route = active.kind === "doc" ? { kind: "doc" as const, id: active.doc.id } : parseRoute(location.hash);
  show(chooseActive(shownDocs(), route, previous), previous);
}

let reconnected = false;
connectEvents({
  connected: () => {
    reconnected = loaded;
  },
  docs: (next) => {
    onDocs(next, reconnected);
    reconnected = false;
  },
  changed: (id) => {
    const tab = tabs.get(id);
    if (tab && fetched(tab)) fetchTab(tab);
  },
  focus: (id) => {
    activate(id);
    tabBar.focusTab(id);
  },
});

window.addEventListener("hashchange", () => {
  if (!loaded) return;
  const route = parseRoute(location.hash);
  if (route.kind === "doc" && tabs.has(route.id)) activate(route.id);
  else show(chooseActive(shownDocs(), route, []));
});

editButton.addEventListener("click", () => {
  const tab = activeTab();
  if (!tab) return;
  tab.editing = !tab.editing;
  showEditor(tab);
  if (tab.editing) void editor.load().then(() => activeTab() === tab && editor.focus());
});

// ---- View controls. Toggles persist in this browser. ----

function preference(key: string, fallback: boolean): boolean {
  const stored = localStorage.getItem(`wb.${key}`);
  return stored === null ? fallback : stored === "true";
}

function bindToggle(button: HTMLElement, key: string, fallback: boolean, apply: (on: boolean) => void): void {
  const set = (on: boolean) => {
    button.setAttribute("aria-pressed", String(on));
    apply(on);
  };
  set(preference(key, fallback));
  button.addEventListener("click", () => {
    const on = button.getAttribute("aria-pressed") !== "true";
    localStorage.setItem(`wb.${key}`, String(on));
    set(on);
  });
}

bindToggle(scrollPanButton, "scrollPan", false, (on) => (preview.viewport.scrollPans = on));
bindToggle(highlightButton, "highlight", true, (on) => preview.setHighlight(on));
bindToggle(gridButton, "grid", false, (on) => previewEl.classList.toggle("grid", on));
bindToggle(freezeButton, "freeze", true, (on) => preview.setFreeze(on));
bindToggle(playbackButton, "playback", false, (on) => preview.setPlayback(on));
playbackPrevious.addEventListener("click", () => preview.step("previous"));
playbackNext.addEventListener("click", () => preview.step("next"));
document.getElementById("skip")!.addEventListener("click", (event) => {
  // The hash holds the route, so move focus without following the link.
  event.preventDefault();
  previewEl.focus();
});
document.getElementById("fit")!.addEventListener("click", () => preview.viewport.fit());
document.getElementById("zoom-in")!.addEventListener("click", () => preview.viewport.zoomIn());
document.getElementById("zoom-out")!.addEventListener("click", () => preview.viewport.zoomOut());
zoomResetButton.addEventListener("click", () => preview.viewport.actualSize());

document.getElementById("reload")!.addEventListener("click", () => {
  const tab = activeTab();
  if (tab) dispatch(tab.doc.id, { kind: "reload" });
});

document.getElementById("overwrite")!.addEventListener("click", () => {
  const tab = activeTab();
  if (tab) dispatch(tab.doc.id, { kind: "overwrite" });
});

// ---- Sharing: a view-only link to the active tab's current text on the hosted Mermaiden demo. ----

let shareNoteTimer: ReturnType<typeof setTimeout> | undefined;

function noteShare(text: string, error: boolean): void {
  clearTimeout(shareNoteTimer);
  shareNote.textContent = text;
  shareNote.classList.toggle("error", error);
  shareNoteTimer = setTimeout(() => (shareNote.textContent = ""), error ? 6000 : 2500);
}

function pressed(button: HTMLElement): boolean {
  return button.getAttribute("aria-pressed") === "true";
}

shareButton.addEventListener("click", () => {
  const tab = activeTab();
  const text = tab ? editorTextOf(tab.state) : null;
  if (text === null) return noteShare("Nothing to share yet.", true);
  const link = mermaidenViewLink(text, {
    grid: pressed(gridButton),
    relationshipHighlight: pressed(highlightButton),
    sequencePlayback: pressed(playbackButton),
    sequencePinnedRows: pressed(freezeButton),
  });
  const failed = (result: ShareResult): result is { ok: false; message: string } => !result.ok;
  // Safari allows a clipboard write only inside the click, so hand it the pending text.
  const blob = link.then((result) => {
    if (failed(result)) throw new Error(result.message);
    return new Blob([result.url], { type: "text/plain" });
  });
  const write =
    typeof ClipboardItem !== "undefined"
      ? navigator.clipboard.write([new ClipboardItem({ "text/plain": blob })])
      : blob.then((b) => b.text()).then((url) => navigator.clipboard.writeText(url));
  write.then(
    () => noteShare("View link copied", false),
    async (error: unknown) => {
      const result = await link;
      noteShare(failed(result) ? result.message : `Couldn't copy the link: ${error instanceof Error ? error.message : String(error)}`, true);
    },
  );
});
