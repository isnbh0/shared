# Mermaiden Toolkit

Mermaiden Toolkit adds optional, accessible relationship exploration to Mermaiden flowcharts. Focusing or pointing at a node reveals the current node, related upstream and downstream nodes, cycles that relate in both directions, and visible connecting edges.

It also provides independently attachable sequence walkthrough and frozen participant rows. The walkthrough reveals a cumulative message prefix with mapped notes and structures and reports separate current-step, revealed-prefix, and overview bounds. Frozen rows render noninteractive participant copies in a host-owned overlay while retaining the native rows as the accessible source.

[Try the hosted demo](https://isnbh0.github.io/mermaiden/)

The toolkit is experimental and may evolve. It is not yet published to npm, accepts `mermaiden@^0.1.0` as a peer, and has no direct Mermaid dependency. It consumes the engine's public semantic contract.

## Highlight flowchart relationships

Render a flowchart with semantics, mount Mermaid's native result, and then attach the optional presentation:

```ts
import { renderWithSemantics } from "mermaiden";
import {
  attachRelationshipHighlight,
  stripRelationshipHighlight,
  type RelationshipHighlightHandle,
} from "mermaiden-toolkit";
import "mermaiden-toolkit/relationships.css";

const host = document.querySelector<HTMLElement>("#diagram");
if (!host) throw new Error("Missing diagram host");

const result = await renderWithSemantics({
  id: "checkout-flow",
  source: "flowchart LR\nCart-->Payment-->Receipt",
});

host.innerHTML = result.svg;
result.bindFunctions?.(host);

const displaySvg = host.querySelector<SVGSVGElement>("svg");
if (!displaySvg) throw new Error("Missing rendered SVG");

let relationshipHighlight: RelationshipHighlightHandle | undefined;
if (result.semantics.kind === "flowchart") {
  relationshipHighlight = attachRelationshipHighlight(displaySvg, result.semantics);
}

function teardownDiagram() {
  relationshipHighlight?.dispose();
  relationshipHighlight = undefined;
}

function serializeDiagram() {
  const exportSvg = displaySvg.cloneNode(true) as SVGSVGElement;
  stripRelationshipHighlight(exportSvg);
  return exportSvg.outerHTML;
}
```

Keep the returned handle with the presentation and call the named teardown when that presentation retires. For export, clone the displayed SVG before removing transient toolkit state from the copy.

## Behavior and ownership

Relationship highlighting responds to pointer input and keyboard focus. It provides accessible names and interaction geometry for participating nodes. Exact keyboard bindings are intentionally not documented as stable while the package is experimental.

Logical topology and rendered linkage remain separate. Only uniquely mapped nodes and edges participate; missing or ambiguous mappings are omitted rather than guessed. Attachment does not mutate the semantic result or Mermaid-owned presentation attributes.

Importing the JavaScript or stylesheet does not attach behavior automatically. The host owns CSS cascade placement, presentation lifetime, cancellation, viewport policy, publication order, and export policy.

An offline, self-contained direct-file artifact must incorporate both the explicitly imported Toolkit JavaScript and stylesheet through the host's build.

`dispose()` removes listeners, toolkit-owned layers, and active host state. `stripRelationshipHighlight()` is safe to repeat and cleans toolkit-owned layers and state from a serialization copy.

## Sequence walkthrough and frozen headers

Resolve portable sequence references before changing or wrapping the native SVG. The same resolved handles can then be passed to either attachment on that tree:

```ts
import { renderWithSemantics } from "mermaiden";
import {
  attachSequencePinnedRows,
  attachSequencePlayback,
  resolveSequenceElements,
  stripSequencePinnedRows,
  stripSequencePlayback,
} from "mermaiden-toolkit";
import "mermaiden-toolkit/sequence.css";

const result = await renderWithSemantics({ id: "calls", source: "sequenceDiagram\nA->>B: hello" });
host.innerHTML = result.svg;
const svg = host.querySelector("svg");
if (!svg || result.semantics.kind !== "sequence") throw new Error("Expected a sequence diagram");
const resolved = resolveSequenceElements(svg, result.semantics);

const playback = attachSequencePlayback(svg, result.semantics, {
  resolved,
  onFitRequest: ({ bounds }) => viewport.fit(bounds),
});
const pinned = attachSequencePinnedRows(svg, result.semantics, {
  resolved,
  overlay: pinnedOverlay,
  viewport,
});
const stopSync = playback?.subscribe((state) => pinned?.setVisibleParticipantIds(state.revealedParticipantIds));

function teardown() {
  stopSync?.();
  playback?.dispose();
  pinned?.dispose();
}

function serialize() {
  const copy = svg.cloneNode(true) as SVGSVGElement;
  stripSequencePlayback(copy);
  stripSequencePinnedRows(copy);
  return copy.outerHTML;
}
```

Message indices range from zero through `messageCount - 1`. `setOverview(true)` enters the full native overview while remembering the current message, and `setOverview(false)` restores it; the legacy terminal `setIndex(messageCount)` aliases overview. Previous and next do nothing in overview. Message-less diagrams are overview-only.

The toolkit derives visibility, focus suppression, participant selection, interval clipping, and fit geometry from one cumulative projection. `onFitRequest` exposes `currentStepBounds`, `cumulativeBounds`, and `fullBounds`; hosts own camera policy. Complete Phase 2 event semantics reveal notes, activations, and fragments at their source-order message interval. Legacy semantics without content mappings remain usable by direct toolkit callers as basic message-only walkthroughs, while hosts that promise complete disclosure should gate on `capabilities.disclosure.completeDisclosure`. Hidden future notes do not enter fit bounds, but Mermaid's native lane positions remain unchanged if those notes widened layout during rendering.

The viewport adapter supplies a synchronous diagram-to-viewport matrix, viewport size, and change subscription. Hosts can keep follow mode at a readable painted scale while allowing distant revealed context to remain offscreen, and can offer a separate cumulative-prefix fit. A current label wider than the viewport stays readable, starts at the reading edge, and remains reachable by panning. Frozen headers occupy only a capped top band; the native diagram remains pannable and zoomable, and freezing is suppressed when full-scale headers would consume too much of the viewport. Call `refresh()` after native geometry changes; ordinary pan and zoom updates use cached measurements. Either attachment can be used and disposed independently. Importing `sequence.css` provides the transient visibility and history treatment. Disposal and `stripSequencePlayback()` restore canonical attributes, focus, clips, and marker references.

## Use the temporary browser CDN

The `latest` browser channel is experimental, mutable, and unversioned. It exposes Toolkit JavaScript and CSS separately:

```text
https://isnbh0.github.io/mermaiden/cdn/latest/mermaiden-toolkit.js
https://isnbh0.github.io/mermaiden/cdn/latest/relationships.css
```

Load the stylesheet explicitly, obtain semantics from the separate engine artifact, and attach Toolkit behavior explicitly:

```html
<link rel="stylesheet" href="https://isnbh0.github.io/mermaiden/cdn/latest/relationships.css">
<div id="diagram"></div>
<script type="module">
  import { renderWithSemantics } from "https://isnbh0.github.io/mermaiden/cdn/latest/mermaiden.js";
  import {
    attachRelationshipHighlight,
    stripRelationshipHighlight,
  } from "https://isnbh0.github.io/mermaiden/cdn/latest/mermaiden-toolkit.js";

  const host = document.querySelector("#diagram");
  if (!host) throw new Error("Missing diagram host");
  const result = await renderWithSemantics({
    id: "checkout-flow",
    source: "flowchart LR\nCart-->Payment-->Receipt",
    config: { startOnLoad: false },
  });
  host.innerHTML = result.svg;
  result.bindFunctions?.(host);
  await new Promise((resolve) => requestAnimationFrame(resolve));
  const svg = host.querySelector("svg");
  if (!svg) throw new Error("Missing rendered SVG");
  const highlight = result.semantics.kind === "flowchart"
    ? attachRelationshipHighlight(svg, result.semantics)
    : undefined;

  function serializeDiagram() {
    const copy = svg.cloneNode(true);
    stripRelationshipHighlight(copy);
    return copy.outerHTML;
  }

  window.addEventListener("pagehide", () => highlight?.dispose(), { once: true });
</script>
```

Toolkit does not import the engine or attach itself automatically. The host still owns stylesheet cascade placement, disposal, and clone-before-strip export. Both JavaScript files are self-contained, but all CDN resources require network access, including from `file://` HTML. When forcing revalidation, put one shared consumer-selected query token on the engine, Toolkit, and stylesheet URLs.

## API

| Export | Purpose |
| --- | --- |
| `attachRelationshipHighlight` | Attach interaction to the unambiguous rendered subset of flowchart semantics and return disposable ownership when geometry is available. |
| `stripRelationshipHighlight` | Remove toolkit-owned layers and active state from an SVG, safely and repeatedly. |
| `RELATIONSHIP_HIGHLIGHT_LAYER_SELECTOR` | Select toolkit-owned visual and interaction layers for specialized serializers or tests. |
| `RelationshipHighlightHandle` | Describe the returned `dispose()` ownership. |
| `RelationshipHighlightOptions` | Configure canonical geometry, transformed node surfaces, cancellation, and optional listener instrumentation. |

`RelationshipHighlightOptions` supports the following advanced inputs. The common path shown above needs none of them.

| Option | Common/default behavior |
| --- | --- |
| `canonicalSvg` | Defaults to `displaySvg`; provide the original rendered SVG when the displayed diagram uses transformed geometry. |
| `nodeSurfaces` | By default, mapped canonical node elements provide geometry; transformed displays can map logical node IDs to alternate display surfaces. |
| `signal` | No cancellation signal by default; provide one to cancel attachment that is no longer needed. |
| `onListenerCountChange` | No instrumentation by default; this optional callback reports listener-count changes for specialized diagnostics or tests. |

## Customize the presentation

Import `mermaiden-toolkit/relationships.css` explicitly. It supports these custom properties:

| Property | Default |
| --- | --- |
| `--relation-current` | `#007ca6` |
| `--relation-ancestor` | `#4357a6` |
| `--relation-descendant` | `#577a16` |
| `--relation-both` | `#8a3fb0` |
| `--focus` | `#a13d61` |

The stylesheet is deliberately unlayered so the importing host chooses cascade ownership.

## Develop in this repository

After running `pnpm install --frozen-lockfile` at the [repository root](https://github.com/isnbh0/mermaiden), run these commands from `packages/mermaiden-toolkit/`. Component commands build the engine first when required.

| Command | Purpose |
| --- | --- |
| `pnpm run typecheck` | Check the toolkit's TypeScript contracts. |
| `pnpm run build` | Build JavaScript, CSS, and declarations. |
| `pnpm test` | Build and run the toolkit test suite. |
| `pnpm run test:related <source-or-test-path>` | Build and run tests related to one toolkit path. |

## Related documentation

- [Hosted demo](https://isnbh0.github.io/mermaiden/)
- [Mermaiden engine](https://github.com/isnbh0/mermaiden/tree/main/packages/mermaiden#readme)
- [Repository overview](https://github.com/isnbh0/mermaiden#readme)
