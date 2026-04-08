# Shared Dotfiles & Configs

Personal collection of generalizable dotfiles, configurations, and Claude Code skills for reuse across projects.

[한국어](README.ko.md)

## Installation

### Option A: Plugin (recommended)

First, register the marketplace:

```bash
/plugin marketplace add isnbh0/shared
```

Then install individual skills:

```bash
/plugin install interview@isnbh0
/plugin install spex@isnbh0
/plugin install critique@isnbh0
/plugin install macros@isnbh0
/plugin install study@isnbh0
```

### Option B: Symlink / Copy

```bash
# Clone to your preferred location
git clone <repo-url> ~/shared

# Symlink .claude directory into a project
ln -s ~/shared/.claude /path/to/project/.claude

# Or copy specific skills
cp -r ~/shared/plugins/spex/skills/spex /path/to/project/.claude/skills/
```

## Skills

### Published (marketplace)

Installable via `/plugin install <name>@isnbh0`:

#### critique

External AI critique via CLI tools (Codex, Gemini).

```
/critique:codex [file-path] [focus]
/critique:gemini [file-path] [focus]
```

- Gets an independent second opinion on specs, code, or recent changes
- **Codex backend:** Runs in a read-only sandbox, supports reasoning effort levels (default, high, xhigh)
- **Gemini backend:** Sandboxed with write and network restrictions

#### interview

Structured requirements discovery through conversational interviews.

```
/interview <topic> [--ref <path>] [--workspace <dir>]
```

- Extracts requirements, constraints, and design decisions through guided Q&A
- Supports reference files to anchor discussion around existing artifacts
- Produces timestamped synthesis documents in the workspace

#### study

Document-grounded Socratic study sessions on any URL or local file.

```
/study <uri>
```

- Calibrates to user familiarity (full study, guided study, or gap check)
- Persists session notes to markdown files with resumption across sittings
- Configurable sessions directory and optional freeform `instructions` for persona/behavior customization

#### spex

Two-phase specification and implementation workflow that separates planning from execution.

Three self-contained skills:

- `/spex:write` — Create a spec, commit it, and stop — no implementation
- `/spex:write-phased` — Create a multi-phase spec for complex features
- `/spex:implement` — Follow an existing spec, implement, update status, and commit

#### macros

Subagent orchestration workflows and session modes: map-reduce, research-backed critique, consensus review, sequential passes, and rigor mode.

```
/macros:mapreduce <task> [--workspace <dir>]
/macros:doubt ["freeform question"]
/macros:consensus <count>
/macros:seq <count>
/macros:rigor
/macros:askme
/macros:delegate
/macros:tmi
```

- **mapreduce** — Splits tasks into independent chunks, dispatches parallel subagents, consolidates results
- **doubt** — Spawns a blind subagent that reads code, verifies assumptions against web sources, applies fixes, and reports concerns ranked by severity
- **consensus** — Runs N blind agents on the same job in parallel, merges findings into consensus/unique/conflicts (no edits for concurrent safety)
- **seq** — Runs N serial blind passes with commits between rounds; requires clean worktree
- **rigor** — Activates Rigor Mode for the session: prioritizes correctness, thorough investigation, and web-grounded verification over minimalism
- **askme** — Shorthand: stop and ask the user to clarify ambiguities or make decisions instead of assuming
- **delegate** — Shorthand: prefer subagents to save context space and parallelize independent subtasks
- **tmi** — Flags content that only makes sense if you were in the room when it was written; reports by default, edits if explicitly instructed

### Other (copy / symlink)

Available in the repo but not published to the marketplace. Install via symlink or copy:

```bash
cp -r ~/shared/plugins/<name>/skills/<skill> /path/to/project/.claude/skills/
```

#### phaser

Battle-tested patterns and best practices for Phaser 3 game development.

Passive knowledgebase — automatically consulted when writing Phaser code.

- Multi-scene flow, object pooling, and physics patterns
- Performance optimization and common pitfall avoidance
- Architecture guidance for game projects

#### report-writer

Structured technical analysis and debugging reports with standardized sections.

```
/report-writer [topic] [--workspace <dir>]
```

- Generates timestamped reports (debugging, analysis, implementation)
- Standardized sections: Executive Summary, Key Findings, Root Cause Analysis, Recommendations
- Evidence-based documentation with code references

#### rigorous-debug

Evidence-based debugging protocol using the scientific method.

```
/rigorous-debug
```

- Requires one-time project-specific initialization before first use
- Enforces hypothesis → experiment → conclusion cycles
- Prevents assumption-driven debugging with structured evidence gathering

#### skill-writer

Tools for creating effective Claude Code skills.

```
/skill-writer
```

- Step-by-step workflow from pattern identification to polished SKILL.md
- Covers frontmatter, instruction structure, and best practices
- Helps extract reusable patterns into shareable skills

## Workspace Configuration

File-producing skills (interview, spex, report-writer, macros, study) support configurable workspace directories with layered precedence (first match wins):

1. **CLI flag** (`--workspace <dir>`) — one-off override
2. **Local config** (`.claude/skill-configs/<skill>/config.local.yaml`) — gitignored, personal overrides
3. **Project config** (`.claude/skill-configs/<skill>/config.yaml`) — committed to repo, shared with team

There are no built-in defaults. Each skill prompts for setup on first use. Output follows the `.agent-workspace/<folder>` convention (`specs`, `reports`, `interviews`, `macros`).

## Other Agentic Tools

These skills use the SKILL.md format, which is supported across multiple AI coding tools. See the [cross-platform guide](docs/cross-platform/README.md) for installation instructions for:

- [Codex CLI](docs/cross-platform/codex-cli.md) (OpenAI)
- [Gemini CLI](docs/cross-platform/gemini-cli.md) (Google)
- [Antigravity](docs/cross-platform/antigravity.md) (Google)
- [Amp](docs/cross-platform/amp.md) (Sourcegraph)
- [Cursor](docs/cross-platform/cursor.md)

## License

Personal use — adapt and modify as needed for your own projects.
