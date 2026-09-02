---
name: artifact-process-flow
description: Author a Mermaid artifact-process flow showing how processes consume or consult durable information and what they produce. Use when durable artifacts and the work that transforms them are the diagram's primary subject.
---

# Artifact-process flow

Use an artifact-process flow to show how processes consume or consult durable information and what they produce.

Artifact nodes represent durable information, whereas process nodes represent work that transforms information. Solid paths alternate between artifact and process nodes. A dotted edge means that a process consults an artifact without transforming it along the main path.

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
