---
name: numbered-edges
description: Add explicit steps, phases, or ordering to selected edges of a Mermaid diagram by prefixing edge labels with ordinals under a declared numbering scope. Use when an archetype diagram also needs to communicate sequence.
---

# Numbered edges

Use numbered edges to assign selected interactions to explicit steps or phases, or to show their order within a declared scope.

Prefix an edge label with an ordinal while preserving the edge's underlying meaning. Declare whether each numbering scope represents a total order, shared phases, a lane-local order, or a partial order. Within a scope, equal values mark a shared phase, while unnumbered edges remain outside the declared ordering. The `~~~` relation is layout-only and receives no number.

```mermaid
flowchart LR
    client["Client"] -->|"(1) Submit request"| router["Router"]
    router -->|"(2) Dispatch lane A"| a["Worker A"]
    router -->|"(2) Dispatch lane B"| b["Worker B"]
    a -->|"(3) Return finding"| owner["Owner"]
    b -->|"(3) Return finding"| owner
    owner -.->|consults| policy[("Policy")]
    a ~~~ b
```

Numbered edges compose with the action-flow, artifact-process-flow, and multi-view skills.
