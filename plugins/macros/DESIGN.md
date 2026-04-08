# Macros Design Philosophy

## Composable, First-Class Skills

Each skill in the macros plugin describes one concern. Skills are not typed as "base" vs "modifier" — they are all equally first-class instructions. When a user invokes multiple skills together (e.g., `/doubt /parallel 3`), the agent reads all of the corresponding skill files and synthesizes what to do.

### Design Principles

- **Self-contained**: each skill file fully describes its concern without assuming what other skills are present.
- **Composable by accident**: skills that address orthogonal concerns (what to review vs. how to fan out work) naturally don't clash. This is a property of good factoring, not of explicit compatibility annotations.
- **Minimal surface**: a skill describes one thing clearly. Orchestration logic, scope resolution, and domain prompts are separate skills, not modes within a single skill.

## Loading

The only infrastructure needed is a mechanism to get N skill files into the agent's context when N `/slash` tokens appear in an invocation. No interpretation, no routing — just read N files and concatenate.

Every macros skill includes a **composition line** immediately after the frontmatter:

```
If other `/commands` appear in the user's message and you have not already called the Skill tool for them in this conversation, invoke each now. Do not re-invoke any skill that has already been loaded.
```
