# Macros Design Philosophy

## Composable, First-Class Skills

Each skill in the macros plugin describes one concern. Skills are not typed as "base" vs "modifier" — they are all equally first-class instructions. When a user invokes multiple skills together (e.g., `/doubt /parallel 3`), the agent reads all of the corresponding skill files and synthesizes what to do.

There is no precedence system, no modifier protocol, no meta-instructions governing how skills combine. The agent figures it out from the content of the skill files themselves.

## Why No Composition Machinery

A formal composition layer (type annotations, precedence rules, interface contracts between skills) creates coupling that gets stale and prevents the agent from making better judgment calls. If two skills genuinely conflict (e.g., `/parallel /seq`), the agent should recognize the tension and ask the user to clarify — not silently apply a precedence rule.

As models improve, any meta-instructions for composition become liability rather than asset. The skill files themselves are the only contract.

## Skill Design Principles

- **Self-contained**: each skill file fully describes its concern without assuming what other skills are present.
- **Composable by accident**: skills that address orthogonal concerns (what to review vs. how to fan out work) naturally don't clash. This is a property of good factoring, not of explicit compatibility annotations.
- **Minimal surface**: a skill describes one thing clearly. Orchestration logic, scope resolution, and domain prompts are separate skills, not modes within a single skill.

## Loading

The only infrastructure needed is a mechanism to get N skill files into the agent's context when N `/slash` tokens appear in an invocation. No interpretation, no routing — just read N files and concatenate.

Claude Code's Skill tool invokes one skill at a time. When a user writes `/delegate /rigor /consensus 2 <task>`, only the first `/command` is reliably detected and invoked — the rest become inert text inside the arguments. To bridge this gap, every macros skill includes a **composition line** immediately after the frontmatter:

```
If other `/commands` appear in the user's message and you have not already called the Skill tool for them in this conversation, invoke each now. Do not re-invoke any skill that has already been loaded.
```

This ensures whichever skill loads first will trigger loading the rest. It adds no composition machinery — just a one-line forwarding directive that gets all N files into context, after which the agent synthesizes from their combined content as intended.
