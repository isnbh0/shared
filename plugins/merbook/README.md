# Merbook: Semantic Mermaid Patterns

Merbook is a set of portable skills for authoring Mermaid flowcharts whose arrows carry one consistent meaning. Each skill is self-contained under `skills/<name>/SKILL.md`; this file is human reference documentation.

Start with the question the diagram must answer, choose an archetype, then add a pattern only when it expresses an additional relationship the diagram needs to show. Host-specific activation syntax is documented separately. This plugin identifies bundled skills by qualified names such as `merbook:action-flow`.

## Archetypes

- `merbook:action-flow` — who or what acts on whom; every arrow is a one-way action initiated by its source toward its target.
- `merbook:artifact-process-flow` — how processes consume or consult durable information and what they produce.

## Patterns

- `merbook:multi-view` — what remains stable across two or more views and what each view shows differently.
- `merbook:numbered-edges` — how selected interactions are assigned to steps or phases, or ordered within a scope.

## Composition

Patterns compose with either archetype. Composition never changes the archetype's arrow semantics: an action flow with numbered edges still points every arrow from initiator to target, and a multi-view of an artifact-process flow still alternates artifact and process nodes on solid paths.
