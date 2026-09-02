---
name: multi-view
description: Author a Mermaid multi-view diagram that shows what remains stable across two or more views of one shared graph and what each view selects, emphasizes, or changes. Use for whole-plus-focused views, before and after states, scenarios, modes, phases, or perspectives.
---

# Multi-view

Use multi-view to show what remains stable across two or more views and how each view selects, emphasizes, or changes parts of the shared graph.

Begin with one shared semantic graph that is the union of every element any view will show. Every view renders that same graph with the same nodes, edges, boundaries, and layout; views differ only in styling. Each view names its lens and uses emphasis, de-emphasis, hiding, or status styling to communicate what that lens highlights or changes. An element outside a view's lens stays in the graph, styled hidden or grayed.

Forms include:

- a whole diagram followed by focused or partial views;
- before and after states;
- iterations, scenarios, operating modes, phases, or perspectives.

A focused view keeps the rest of the graph in gray for orientation. A partial view styles out-of-lens elements hidden. Before-and-after views render the same graph in both states: elements that will be added appear in the before view hidden or grayed, elements that will be removed appear in the after view grayed as obsolete, and unchanged elements keep identical styling. Show an ownership change by placing the element in both boundaries in every view, styling the losing copy obsolete and the gaining copy new.

With ELK or Dagre, connect an invisible root to each view with layout-only `~~~` links to guide view order without asserting semantic relationships between views.

```mermaid
---
config:
  layout: elk
---
flowchart TB
    subgraph whole["WHOLE"]
        direction TB
        whole_root["Client"] --> w_api["API"]
        w_api --> w_store[("Store")]
        w_api --> w_worker["Worker"]
    end
    subgraph online["VIEW · online request"]
        direction TB
        online_root["Client"] --> o_api["API"]
        o_api --> o_store[("Store")]
        o_api --> o_worker["Worker"]
    end
    subgraph batch["VIEW · batch"]
        direction TB
        batch_root["Client"] --> b_api["API"]
        b_api --> b_store[("Store")]
        b_api --> b_worker["Worker"]
    end
    classDef focus fill:#fff1e8,stroke:#c2410c,color:#7c2d12,stroke-width:2px
    classDef context fill:#f1f5f9,stroke:#cbd5e1,color:#94a3b8
    classDef hidden fill:transparent,stroke:transparent,color:transparent
    class online_root,o_api,o_store focus
    class b_api,b_worker,b_store focus
    class o_worker context
    class batch_root hidden
    linkStyle 6 stroke:transparent
    order_anchor[" "]
    order_anchor ~~~ whole
    order_anchor ~~~ online
    order_anchor ~~~ batch
    style order_anchor opacity:0,fill:transparent,stroke:transparent
```

Multi-view can repeat either an artifact-process flow or an action flow, authored with the artifact-process-flow or action-flow skill. Add the numbered-edges skill when a view also needs explicit interaction order.
