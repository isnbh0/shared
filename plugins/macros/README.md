# Macros: Parallel Subagent Orchestration

Macros are portable, composable skills for coordinating agent workflows. Each runtime skill is self-contained under `skills/<name>/SKILL.md`; this file is human reference documentation.

Host-specific activation syntax is documented separately. This plugin identifies bundled skills by qualified names such as `macros:mapreduce`.

## Skills

- `macros:mapreduce` — split work into independent parallel chunks, then consolidate the results.
- `macros:chunked` — process an ordered partition sequentially, allowing later chunks to use earlier outputs.
- `macros:packet` — package work for completion outside the current agent loop, then validate the returned artifacts and resume.
- `macros:doubt` — launch an independent, web-researched critique of recent work or a supplied question.
- `macros:consensus` — run blind agents on the same job concurrently, then merge consensus, unique findings, and conflicts.
- `macros:seq` — run blind passes serially, committing each pass before the next.
- `macros:rigor` — prioritize correctness, thorough investigation, and web-grounded verification while active.
- `macros:orchestrate` — delegate execution by default and keep the primary agent focused on direction and synthesis.
- `macros:askme` — ask the user at ambiguities and decision points instead of assuming.
- `macros:delegate` — prefer subagents when they save context or enable concurrency.
- `macros:dry-run` — describe the intended actions for the current request without performing side effects.
- `macros:dredge` — search prior coding-agent transcripts for relevant context.
- `macros:timeless` — avoid time estimates and describe complexity, scope, risk, and ordering instead.
- `macros:timestamp` — prefix new paths with one timestamp per logical job bucket.
- `macros:tmi` — flag artifact content that only makes sense with conversational backstory.
- `macros:new` — scaffold a standalone custom macro skill.

## Configuration

`macros:mapreduce`, `macros:chunked`, and `macros:packet` resolve configuration in this order:

1. An explicit workspace override for the current run
2. `.agents/skill-configs/macros/config.local.yaml`
3. `.agents/skill-configs/macros/config.yaml`
4. Legacy fallback for older installs: `.claude/skill-configs/macros/config.local.yaml`, then `.claude/skill-configs/macros/config.yaml`

When configuration is found only at a legacy path, the skill uses it and offers to move it to the current location. There are no built-in defaults; see `config.example.yaml`.

```yaml
workspace_dir: .agent-workspace/macros
```

## Workspace Structure

```text
${WORKSPACE_DIR}/
└── {timestamp}-{task-name}/
    ├── _context.md
    ├── chunk-1-{name}.md
    ├── chunk-2-{name}.md
    └── consolidated-report.md
```
