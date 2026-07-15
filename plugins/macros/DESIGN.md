# Macros Design Philosophy

## Composable, First-Class Skills

Each skill in the macros plugin describes one concern. Skills are not typed as "base" vs "modifier" — they are all equally first-class instructions. When multiple skills are active together (for example, `macros:doubt` and `macros:consensus`), the agent reads all of the corresponding skill files and synthesizes what to do.

Bundled skills are identified by their qualified names, such as `macros:doubt`; standalone skills use their unqualified names. Host-specific activation syntax belongs in `docs/cross-platform/`.

### Design Principles

- **Self-contained**: each skill file fully describes its concern without assuming what other skills are present.
- **Composable by accident**: skills that address orthogonal concerns (what to review vs. how to fan out work) naturally don't clash. This is a property of good factoring, not of explicit compatibility annotations.
- **Minimal surface**: a skill describes one thing clearly. Orchestration logic, scope resolution, and domain prompts are separate skills, not modes within a single skill.

## Loading

The only infrastructure needed is the host's normal skill-loading mechanism. No interpretation or routing is required beyond making every explicitly activated skill available to the agent.

Every macros skill includes a **composition line** immediately after the frontmatter:

```
Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.
```
