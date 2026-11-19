---
name: artifact-process-flow
description: Author a Mermaid artifact-process flow showing how processes consume or consult durable information and what they produce. Use when durable artifacts and the work that transforms them are the diagram's primary subject.
---

# Artifact-process flow

Use an artifact-process flow to show how processes consume or consult durable information and what they produce.

Artifact nodes represent durable information, whereas process nodes represent work that transforms information. Solid paths alternate between artifact and process nodes. A dotted edge means that a process consults an artifact without transforming it along the main path.

An artifact with solid arrows both in from and out to the same process reads as a two-way document. Prefer one writer per artifact, so the path runs process → artifact → next process; an artifact fed by independent processes may have several writers. Use a portal (a hexagon labelled `returns to X`) only to close a real loop back to an earlier artifact, rather than drawing the back-edge.

```mermaid
flowchart TD
    request[("Request")]
    prepare[["Prepare result"]]:::process
    result[("Result")]
    policy[("Policy")]
    request --> prepare --> result
    policy -.-> prepare
    classDef process fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000
```

Repeat the same flow under different lenses with the multi-view skill, or add explicit order to selected interactions with the numbered-edges skill. Choose the action-flow skill when the diagram concerns who acts on whom rather than information transformed by work.
