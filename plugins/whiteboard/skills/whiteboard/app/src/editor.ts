// Monaco, loaded on the first Edit toggle. One plain-text model per tab. Programmatic replaces
// keep undo working and do not emit edits. A model holds one line-ending style, matched to the
// text it is given; a file with mixed line endings takes its dominant style on the first edit.
import type * as Monaco from "monaco-editor/editor/editor.api";
import EditorWorker from "monaco-editor/editor/editor.worker?worker";
import type { DocId } from "./types.ts";

type MonacoApi = typeof Monaco;

let loading: Promise<MonacoApi> | undefined;

function loadMonaco(): Promise<MonacoApi> {
  loading ??= (async () => {
    (self as unknown as { MonacoEnvironment: Monaco.Environment }).MonacoEnvironment = {
      getWorker: () => new EditorWorker(),
    };
    return import("monaco-editor/editor/editor.api");
  })();
  return loading;
}

/** The line ending `text` mostly uses: CRLF only when it outnumbers LF; null with no line breaks. */
function dominantEol(text: string): "\n" | "\r\n" | null {
  const crlf = text.split("\r\n").length - 1;
  const lf = text.split("\n").length - 1 - crlf;
  if (crlf === 0 && lf === 0) return null;
  return crlf > lf ? "\r\n" : "\n";
}

export class EditorPane {
  readonly #host: HTMLElement;
  readonly #onEdit: (id: DocId, text: string) => void;
  readonly #models = new Map<DocId, Monaco.editor.ITextModel>();
  #monaco: MonacoApi | undefined;
  #editor: Monaco.editor.IStandaloneCodeEditor | undefined;
  #shown: DocId | undefined;
  #replacing = false;

  constructor(host: HTMLElement, onEdit: (id: DocId, text: string) => void) {
    this.#host = host;
    this.#onEdit = onEdit;
  }

  get loaded(): boolean {
    return this.#editor !== undefined;
  }

  async load(): Promise<void> {
    if (this.#editor) return;
    const monaco = await loadMonaco();
    if (this.#editor) return;
    this.#monaco = monaco;
    this.#editor = monaco.editor.create(this.#host, {
      model: null,
      automaticLayout: true,
      minimap: { enabled: false },
      wordWrap: "on",
      fontSize: 13,
      scrollBeyondLastLine: false,
      ariaLabel: "Diagram source",
    });
  }

  hasModel(id: DocId): boolean {
    return this.#models.has(id);
  }

  /** Shows the tab's model in the editor, creating it from `text` the first time. */
  show(id: DocId, text: string): void {
    if (!this.#monaco || !this.#editor) return;
    let model = this.#models.get(id);
    if (!model) {
      model = this.#monaco.editor.createModel(text, "plaintext");
      const created = model;
      created.onDidChangeContent(() => {
        if (!this.#replacing) this.#onEdit(id, created.getValue());
      });
      this.#models.set(id, model);
    }
    if (this.#shown !== id) {
      this.#editor.setModel(model);
      this.#shown = id;
    }
  }

  /** Shows no model, so a tab whose text has not loaded never displays or edits another tab's. */
  detach(): void {
    if (this.#shown === undefined) return;
    this.#editor?.setModel(null);
    this.#shown = undefined;
  }

  focus(): void {
    this.#editor?.focus();
  }

  /** Replaces a tab's text programmatically, as one undoable edit that emits no `edit`. */
  replace(id: DocId, text: string): void {
    const model = this.#models.get(id);
    if (!model || !this.#monaco) return;
    const eol = dominantEol(text);
    if (eol !== null && model.getEOL() !== eol) {
      const crlf = eol === "\r\n";
      this.#replacing = true;
      try {
        model.pushEOL(crlf ? this.#monaco.editor.EndOfLineSequence.CRLF : this.#monaco.editor.EndOfLineSequence.LF);
      } finally {
        this.#replacing = false;
      }
    }
    if (model.getValue() === text.replace(/\r\n|\r|\n/g, model.getEOL())) return;
    const editor = this.#editor;
    const ownsModel = editor?.getModel() === model;
    const position = ownsModel ? editor!.getPosition() : null;
    this.#replacing = true;
    try {
      model.pushStackElement();
      model.pushEditOperations([], [{ range: model.getFullModelRange(), text }], () => null);
      model.pushStackElement();
    } finally {
      this.#replacing = false;
    }
    if (ownsModel && position) {
      const line = Math.min(position.lineNumber, model.getLineCount());
      const column = Math.min(position.column, model.getLineMaxColumn(line));
      editor!.setPosition({ lineNumber: line, column });
    }
  }

  dispose(id: DocId): void {
    const model = this.#models.get(id);
    if (!model) return;
    if (this.#shown === id) {
      this.#editor?.setModel(null);
      this.#shown = undefined;
    }
    model.dispose();
    this.#models.delete(id);
  }
}
