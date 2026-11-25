// The tab bar (ARIA tabs pattern) and the rule that picks the active tab.
import type { Doc, DocId } from "./api.ts";
import type { Route } from "./route.ts";

export type Active = { kind: "doc"; doc: Doc } | { kind: "not-open" } | { kind: "empty" };

/**
 * The active tab as one function of (open set, route, previous open set). When the routed doc
 * just closed, its right neighbour in the previous order becomes active, or the last tab.
 */
export function chooseActive(docs: Doc[], route: Route, previous: Doc[]): Active {
  if (route.kind === "doc") {
    const found = docs.find((d) => d.id === route.id);
    if (found) return { kind: "doc", doc: found };
    const at = previous.findIndex((d) => d.id === route.id);
    if (at < 0) return { kind: "not-open" };
    if (docs.length === 0) return { kind: "empty" };
    const open = new Set(docs.map((d) => d.id));
    const right = previous.slice(at + 1).find((d) => open.has(d.id));
    const next = right ? docs.find((d) => d.id === right.id)! : docs[docs.length - 1]!;
    return { kind: "doc", doc: next };
  }
  return docs.length > 0 ? { kind: "doc", doc: docs[0]! } : { kind: "empty" };
}

export type TabMark = { symbol: string; label: string } | undefined;

export type TabHandlers = {
  select(id: DocId): void;
  close(id: DocId): void;
};

export class TabBar {
  readonly #list: HTMLElement;
  readonly #panelId: string;
  readonly #handlers: TabHandlers;
  #docs: Doc[] = [];

  constructor(list: HTMLElement, panelId: string, handlers: TabHandlers) {
    this.#list = list;
    this.#panelId = panelId;
    this.#handlers = handlers;
    list.setAttribute("role", "tablist");
    list.setAttribute("aria-label", "Open files");
    list.addEventListener("keydown", (event) => this.#onKey(event));
  }

  static tabId(id: DocId): string {
    return `tab-${id}`;
  }

  render(docs: Doc[], activeId: DocId | undefined, marks: (id: DocId) => TabMark = () => undefined): void {
    this.#docs = docs;
    const focused = document.activeElement instanceof HTMLElement ? document.activeElement.id : "";
    this.#list.replaceChildren(
      ...docs.map((doc, index) => {
        const selected = doc.id === activeId;
        const wrapper = document.createElement("div");
        wrapper.className = "tab";
        wrapper.setAttribute("role", "presentation");

        const tab = document.createElement("button");
        tab.type = "button";
        tab.id = TabBar.tabId(doc.id);
        tab.setAttribute("role", "tab");
        tab.setAttribute("aria-selected", String(selected));
        tab.setAttribute("aria-controls", this.#panelId);
        tab.tabIndex = selected || (activeId === undefined && index === 0) ? 0 : -1;
        tab.title = doc.path;
        tab.dataset["id"] = doc.id;
        const name = document.createElement("span");
        name.className = "tab-name";
        name.textContent = doc.name;
        tab.append(name);
        const mark = marks(doc.id);
        if (mark) {
          const markEl = document.createElement("span");
          markEl.className = "tab-mark";
          markEl.setAttribute("aria-hidden", "true");
          markEl.textContent = mark.symbol;
          const markText = document.createElement("span");
          markText.className = "visually-hidden";
          markText.textContent = `, ${mark.label}`;
          tab.append(markEl, markText);
        }
        const description = document.createElement("span");
        description.id = `${tab.id}-path`;
        description.className = "visually-hidden";
        description.textContent = doc.path;
        tab.setAttribute("aria-describedby", description.id);
        tab.addEventListener("click", () => this.#handlers.select(doc.id));

        const close = document.createElement("button");
        close.type = "button";
        close.className = "tab-close";
        close.tabIndex = -1;
        close.setAttribute("aria-label", `Close ${doc.name}`);
        close.title = `Close ${doc.name}`;
        close.append(icon("i-close"));
        close.addEventListener("click", (event) => {
          event.stopPropagation();
          this.#handlers.close(doc.id);
        });

        wrapper.append(tab, description, close);
        return wrapper;
      }),
    );
    if (focused) document.getElementById(focused)?.focus();
  }

  focusTab(id: DocId): void {
    document.getElementById(TabBar.tabId(id))?.focus();
  }

  #onKey(event: KeyboardEvent): void {
    const target = event.target;
    if (!(target instanceof HTMLElement) || target.getAttribute("role") !== "tab") return;
    const index = this.#docs.findIndex((d) => d.id === target.dataset["id"]);
    if (index < 0 || this.#docs.length === 0) return;
    let next: number;
    switch (event.key) {
      case "ArrowRight":
        next = (index + 1) % this.#docs.length;
        break;
      case "ArrowLeft":
        next = (index - 1 + this.#docs.length) % this.#docs.length;
        break;
      case "Home":
        next = 0;
        break;
      case "End":
        next = this.#docs.length - 1;
        break;
      case "Delete": {
        event.preventDefault();
        this.#handlers.close(this.#docs[index]!.id);
        return;
      }
      default:
        return;
    }
    event.preventDefault();
    const doc = this.#docs[next]!;
    this.#handlers.select(doc.id);
    this.focusTab(doc.id);
  }
}

/** A sprite icon from the page (see index.html), hidden from assistive technology. */
function icon(id: string): SVGSVGElement {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("class", "icon-svg");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS(ns, "use");
  use.setAttribute("href", `#${id}`);
  svg.append(use);
  return svg;
}
