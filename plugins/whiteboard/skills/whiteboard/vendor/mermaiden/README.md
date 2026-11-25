# Mermaiden

Mermaiden renders Mermaid diagrams and can return portable diagram semantics alongside Mermaid's native result.

[Try the hosted demo](https://isnbh0.github.io/mermaiden/)

Mermaiden is not yet published to npm. It requires exactly Mermaid `12.0.0` as a peer so the host and engine share one Mermaid instance. Rendering requires a browser-compatible DOM. Browser-backed Node workflows fit that requirement; arbitrary DOM shims are not supported as production environments.

## Render with semantics

`renderWithSemantics` returns Mermaid's native result plus a family-discriminated semantic result:

```ts
import { renderWithSemantics } from "mermaiden";

const result = await renderWithSemantics({
  id: "checkout-flow",
  source: "flowchart LR\nCart-->Payment",
});

if (result.semantics.kind === "flowchart") {
  const { model, rendered } = result.semantics;
  const firstNode = model.nodes[0];
  const elementId = rendered.nodes.find(({ nodeId }) => nodeId === firstNode?.id)?.elementId;
  // `firstNode` is portable logical content; `elementId` belongs to this SVG artifact.
}
```

Sequence diagrams expose declaration-ordered participants and a dense, zero-based
list of drawable message occurrences. Repeated labels and endpoints remain
separate messages:

```ts
const result = await renderWithSemantics({
  id: "sign-in-sequence",
  source: "sequenceDiagram\nUser->>Server: Sign in",
});

if (result.semantics.kind === "sequence") {
  const first = result.semantics.model.messages[0];
  // { id: "0", from: "User", to: "Server", label: "Sign in", order: 0 }

  const disclosure = result.semantics.capabilities?.disclosure;
  // `completeDisclosure` is true only when every narrative event has a verified
  // rendered mapping for this exact SVG artifact.
}
```

Sequence semantics also expose source-ordered `events` and portable rendered
`content` references for notes, activations, and control structures. Each event
has a stable occurrence ID and a `revealAtMessage` cursor. Paired structures
carry an interval. Content entries identify their role and message interval so
consumers can reveal a cumulative prefix without inspecting Mermaid internals.
Leading or between-message content belongs to the following message; trailing
content belongs to the final message. Structure closes belong to the final
message inside their interval. A note-only diagram has no invented message.

`capabilities.disclosure.completeDisclosure` is independent of native rendering.
It is false, with stable diagnostic codes, when the pinned renderer cannot be
mapped safely (currently participant boxes, participant creation/destruction,
`par_over`, ambiguous activations, or unknown narrative shapes). Existing
message-only semantic values remain valid inputs for consumers; absence of the
capability means comprehensive disclosure was not established.

`semantics.model` contains portable logical nodes and directed edges. `semantics.rendered` optionally links those logical records to elements in this exact SVG artifact when the correspondence is unambiguous.

| `kind` | Meaning |
| --- | --- |
| `flowchart` | Logical flowchart topology is available; rendered mappings include only unambiguous SVG correspondence. |
| `sequence` | Logical participants and ordered messages are available; rendered mappings contain complete, verified element bundles. |
| `unsupported` | Mermaid rendered successfully, but this diagram family has no semantic adapter. |
| `unavailable` | Mermaid rendered successfully, but semantic extraction could not complete; diagnostics explain the loss. |

Semantic extraction does not rewrite Mermaid's SVG or replace its `bindFunctions` reference. Logical records remain available when a rendered mapping is missing, and `unsupported` or `unavailable` semantics never discard a valid native render.

Sequence rendered references are arrays of element-child indices starting at
the returned SVG root. They contain no DOM nodes or browser geometry and survive
a JSON round trip. Resolve them against the exact returned native SVG, or an
unchanged deep clone, before accessibility normalization, viewport wrapping, or
other descendant changes. A reference is invalid after native descendants are
reparented, replaced, inserted, removed, or reordered. Moving already-resolved
element handles is safe. Missing or ambiguous correspondence is omitted with a
diagnostic while the portable logical participant or message remains available.

## Use it through Mermaid's API

The default export is a low-migration substitute for Mermaid's ordinary API:

```ts
import mermaid from "mermaiden";

mermaid.initialize({ startOnLoad: false });

const host = document.querySelector("#diagram");
if (!host) throw new Error("Missing diagram host");

const result = await mermaid.render("checkout-flow", "flowchart LR\nCart-->Payment");
host.innerHTML = result.svg;
result.bindFunctions?.(host);
```

Ordinary `render` and `run` retain Mermaid's result and behavior. Mermaiden does not attach presentation behavior or CSS.

## Configure rendering

Configured hosts can validate input and provide configuration for each request. Mermaid 12 includes ELK, so selecting it needs no separate loader registration:

```ts
import { createSemanticRenderer } from "mermaiden";

const source = "flowchart LR\nCart-->Payment";
const controller = new AbortController();
const renderer = createSemanticRenderer();

await renderer.validate({
  source,
  config: { startOnLoad: false },
  signal: controller.signal,
});

const result = await renderer.renderWithSemantics({
  id: "checkout-flow",
  source,
  config: { startOnLoad: false, theme: "neutral" },
  signal: controller.signal,
});
```

Mermaid registers its built-in layouts, including ELK. Hosts can still pass custom `layoutLoaders` to `createSemanticRenderer`; Mermaiden registers those once for that renderer. The optional `signal` cancels work that is no longer needed.

## Compatibility

Mermaiden serializes operations that render or inspect Mermaid's shared singleton state, and later operations can continue after an earlier operation fails. Direct calls through plain Mermaid and raw forwarded stateful APIs such as `initialize`, `parse`, and `mermaidAPI` are outside that protection.

Use one Mermaiden module instance per process or application bundle. An unconfigured render inherits the shared Mermaid configuration. Importing `mermaiden` replaces Mermaid's browser `load` listener with Mermaiden's serialized listener; importing it after the load event has fired cannot replay that event.

The only supported package import is `mermaiden`. HTML source that uses this package import requires a package-aware build and preserves the exact Mermaid peer relationship described above. For offline direct-file delivery, the host must produce a generated artifact containing its selected runtime dependency graph.

As a separate delivery contract, the repository temporarily publishes a browser artifact that bundles the supported Mermaid peer:

```html
<script type="module">
  import mermaiden from "https://isnbh0.github.io/mermaiden/cdn/latest/mermaiden.js";

  mermaiden.initialize({ startOnLoad: false });
  const host = document.querySelector("#diagram");
  if (!host) throw new Error("Missing diagram host");
  const source = `---
config:
  layout: elk
---
flowchart LR
Cart-->Payment`;
  const result = await mermaiden.render("checkout-flow", source);
  host.innerHTML = result.svg;
  result.bindFunctions?.(host);
</script>
```

This ESM-only `latest` URL is experimental, mutable, and unversioned. It requires network access when used from HTTP(S) or `file://` HTML. It is self-contained and fetches no runtime chunks. It already owns the bundled Mermaid 12.0.0 singleton, so do not load Mermaid separately. The URL supplies runtime ESM only; declarations and npm-style subpath resolution remain package concerns. Use a consumer-selected query token when forcing revalidation.

The browser artifact includes Mermaid's built-in ELK implementation. CDN and package consumers can select ELK through source frontmatter at `config.layout` without installing or registering a separate layout package.

Presentation and build ownership remain with the host application.

## Develop in this repository

After running `pnpm install --frozen-lockfile` at the [repository root](https://github.com/isnbh0/mermaiden), run these commands from `packages/mermaiden/`:

| Command | Purpose |
| --- | --- |
| `pnpm run typecheck` | Check the engine's TypeScript contracts. |
| `pnpm run build` | Build JavaScript and declarations. |
| `pnpm test` | Build and run the engine test suite. |
| `pnpm run test:related <source-or-test-path>` | Build and run tests related to one engine path. |

See the [repository overview](https://github.com/isnbh0/mermaiden#readme) for repository-wide development.
