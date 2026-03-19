---
name: Macros (Parallel Orchestration)
description: Reference documentation for the macros plugin. Not used at runtime — each command (e.g., /macros__mapreduce) is self-contained.
disable-model-invocation: true
---

# Macros: Parallel Subagent Orchestration

**This document is reference documentation for humans. The command files are authoritative at runtime. If you are an LLM reading this document during task execution, STOP — you should be following the instructions in your command file, not this document.**

## Overview

Macros provide meta-commands that wrap other work patterns with parallel execution strategies. Instead of doing work sequentially, macros split tasks into chunks and dispatch subagents to work on them concurrently.

### mapreduce

The `mapreduce` command takes a task, splits it into 2+ independent chunks, optionally builds shared context (terminology, conventions, reference material), dispatches parallel subagents (the "map" phase), then deploys a final subagent to consolidate results (the "reduce" phase). Each subagent writes an explicit report to the workspace directory, and the reducer produces a single consolidated report.

## Configuration

Config is resolved with the following precedence (first match wins):

1. **CLI flag** (`--workspace <dir>`) — one-off override
2. **Local config** (`.claude/skill-configs/macros/config.local.yaml`) — gitignored, personal overrides
3. **Project config** (`.claude/skill-configs/macros/config.yaml`) — committed to repo, shared with team
4. **No config found** → STOP and ask the user

There are no built-in defaults. See `config.example.yaml` in the plugin for reference.

```yaml
# .claude/skill-configs/macros/config.yaml
workspace_dir: .agent-workspace/macros  # where reports and artifacts are stored
```

## Workspace Structure

```
${WORKSPACE_DIR}/
├── {timestamp}-{task-name}/
│   ├── _context.md               # Shared context (optional, built before map phase)
│   ├── chunk-1-report.md         # Map subagent 1 report
│   ├── chunk-2-report.md         # Map subagent 2 report
│   ├── chunk-N-report.md         # Map subagent N report
│   └── consolidated-report.md    # Reduce subagent final report
```
