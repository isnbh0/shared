---
name: doubt
description: Spawns independent subagent(s) to critique recent work with web research. Use when the user wants a second opinion, says "doubt this", or wants to verify code against docs.
argument-hint: "[count | --seq N | \"freeform question\"]"
---

# Doubt

Independent, research-backed critique via subagents. Each agent reads the code, verifies assumptions against web sources, applies fixes, and reports concerns ranked by severity.

```
/doubt                          # 1 agent, auto-scope
/doubt 2                        # 2 parallel blind agents
/doubt --seq 2                  # 2 serial passes, fixes applied between
/doubt "is this the right API"  # freeform question + research
```

## Modes

- **Single** (default) — one agent critiques and fixes
- **Parallel** (`N`) — N blind agents critique independently (report-only, no edits), findings merged (consensus → unique → conflicts)
- **Sequential** (`--seq N`) — N serial passes; each agent fixes code and commits, next agent reviews the updated code blind

## Relationship to /critique

`/critique` uses a different model (Codex, Gemini) for cross-model reasoning diversity. `/doubt` uses the same model with web research for claim verification. They complement each other.
