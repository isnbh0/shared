# Shared Dotfiles & Agent Skills

Personal collection of reusable dotfiles, configurations, and portable `SKILL.md` agent skills for coding agents.

[한국어](README.ko.md)

## Installation

The reusable source of truth is each skill directory under `plugins/<plugin>/skills/<skill>/`. A skill is portable when the full directory contains a `SKILL.md` file and any supporting resources.

### Option A: Copy / Symlink Skills

Use this for any agent that reads `SKILL.md` skills directly. Resolve the target agent's current skill root from its own docs or from the compatibility SSOT in [docs/cross-platform/README.md](docs/cross-platform/README.md).

```bash
# Clone to your preferred location
git clone <repo-url> ~/shared

# Copy the whole skill directory, not only SKILL.md
mkdir -p <skill-root>
cp -R ~/shared/plugins/interview/skills/interview <skill-root>/
```

For automatic updates, symlink the skill directory instead of copying it.

### Option B: Claude Code Marketplace

The repository also packages selected skills as Claude Code marketplace plugins. First, register the marketplace:

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
/plugin install gimme@isnbh0
/plugin install promptopt@isnbh0
/plugin install zoomdoc@isnbh0
```

## Skills

Skills are listed by plain name below. Activation syntax depends on the host and installation method; see the [cross-platform guide](docs/cross-platform/README.md).

### Published (marketplace)

Installable in Claude Code via `/plugin install <name>@isnbh0`:

#### critique

External AI critique via CLI tools (Codex, Gemini).

| Skill | Optional inputs |
|-------|-----------------|
| codex | file path, focus |
| gemini | file path, focus |

- Gets an independent second opinion on specs, code, or recent changes
- **Codex backend:** Runs a configured Codex CLI review
- **Gemini backend:** Runs a configured Gemini CLI review

#### interview

Structured requirements discovery through conversational interviews.

**Try it without installing in Claude Code:**

```bash
claude --plugin-url https://github.com/isnbh0/shared/releases/download/interview-latest/interview.zip
```

Like it? Install with the marketplace commands above.

**Inputs:** topic; optional reference path

- Extracts requirements, constraints, and design decisions through guided Q&A
- Supports reference files to anchor discussion around existing artifacts
- Produces timestamped synthesis documents in the workspace

#### study

Document-grounded Socratic study sessions on any URL or local file.

**Input:** URL or local document path

- Calibrates to user familiarity (full study, guided study, or gap check)
- Persists session notes to markdown files with resumption across sittings
- Configurable sessions directory and optional freeform `instructions` for persona/behavior customization

#### spex

Two-phase specification and implementation workflow that separates planning from execution.

Three self-contained skills:

- **write** — Create a spec, commit it, and stop — no implementation
- **write-phased** — Create a multi-phase spec for complex features
- **implement** — Follow an existing spec, implement, update status, and commit

#### macros

Subagent orchestration workflows and behavior modifiers: map-reduce, chunked sequencing, durable filesystem packets, progressive mental-model calibration, interpretive leeway, research-backed critique, consensus review, sequential passes, and rigor mode.

- **mapreduce** — Splits tasks into independent chunks, dispatches parallel subagents, consolidates results
- **chunked** — Runs a task as an ordered partition where each iteration may read prior iterations' outputs
- **packet** — Packages work for completion outside the current agent loop, stops at a durable filesystem boundary, then validates the returned artifacts and resumes
- **calibrate** — Aligns a mental model or state through adaptive passes from broad structure to consequential finer distinctions; composes with packet for file-based exchanges
- **leeway** — Grants interpretive latitude where the user intends it, avoiding needless rigidity and literalism without making it a new protocol
- **doubt** — Spawns a blind subagent that reads code, verifies assumptions against web sources, applies fixes, and reports concerns ranked by severity
- **consensus** — Runs N blind agents on the same job in parallel, merges findings into consensus/unique/conflicts (no edits for concurrent safety)
- **seq** — Runs N serial blind passes with commits between rounds; requires clean worktree
- **rigor** — While active, prioritizes correctness, thorough investigation, and web-grounded verification over minimalism
- **orchestrate** — While active, delegates execution to subagents by default and operates at the high level, conserving context for direction and synthesis; an escape hatch keeps trivial work inline
- **askme** — Shorthand: stop and ask the user to clarify ambiguities or make decisions instead of assuming
- **delegate** — Shorthand: prefer subagents to save context space and parallelize independent subtasks
- **tmi** — Flags content that only makes sense if you were in the room when it was written; reports by default, edits if explicitly instructed
- **dry-run** — One-shot failsafe: describes what it would do for the activating request instead of doing it, then waits for confirmation
- **timeless** — Shorthand: avoid time estimates (hours, calendar, size-to-time buckets); describe complexity, scope, risk, and ordering instead
- **dredge** — Searches prior coding-agent chat transcripts (Claude Code, Codex, ...) for context; defaults to the current project, widens scope and time window from natural-language hints in the query (e.g. "across all projects", "in the craken repo", "yesterday"). Uses an optional AgentsView backend when the `agentsview` CLI is installed (configured at user scope under `~/.agents/skill-configs/dredge/`); falls back to grep over Claude Code transcripts otherwise
- **timestamp** — Shorthand: prefix newly created files/folders with a `yymmdd-HHMMSS` stamp from the `date` CLI; one timestamp per logical job bucket; one turn only
- **new** — Scaffold a custom macro: writes a user- or project-scope skill that behaves as a first-class macro and composes with other active skills; user-scope macros default to a `my-` name prefix

#### gimme

User-invoked inversion of delegation — hand the agent a request and get back a filesystem bundle you can act on.

- Writes a timestamped bundle with `checklist.md`, `notes.md` (template with pre-labeled paste slots), and an empty `dropbox/` directory for file artifacts
- Each checklist item has action / why-it's-on-you / drop-path so results land somewhere the agent can pick up without further direction
- Secrets never enter the bundle — API keys and tokens get a store command for your OS secret store, so the bundle names only the reference
- Optional `launch_command` config (e.g. `cursor {path}`, `code {path}`, `open {path}`) opens the bundle in your editor immediately
- Never self-invoked — only runs when you explicitly activate the gimme skill

#### promptopt

Artifact-backed prompt optimization workflow for application prompts, prompt builders, agent instructions, routing prompts, and LLM workflows.

- Collects user-owned target behavior, output contract, train/val cases, and acceptance criteria before optimizing
- Writes all optimization artifacts to its own run workspace instead of editing source files
- Maintains baseline outputs, candidate ledger, optimizer state, and a decision record

#### zoomdoc

Authors accessible, self-contained semantic-zoom HTML documents while preserving ordinary semantic structure.

**Try it without installing in Claude Code:**

```bash
claude --plugin-url https://github.com/isnbh0/shared/releases/download/zoomdoc-latest/zoomdoc.zip
```

- Uses document-defined ordered detail levels and optional editorial profiles instead of a fixed article ontology
- Supports arbitrary semantic HTML, including nested sections, figures, definition lists, tables, code, media, and footnotes
- Uses native radio and disclosure controls, explicit `hidden` state, and a complete finest-level JavaScript-disabled fallback
- Ships an accessible renderer and validator with optional strict coverage for source transcriptions

### Other (copy / symlink)

Available in the repo but not published to the marketplace. Install via symlink or copy:

```bash
cp -R ~/shared/plugins/<plugin>/skills/<skill> <skill-root>/
```

Direct installs use the skill's frontmatter `name`, which matches its source directory in this repository.

#### phaser

Battle-tested patterns and best practices for Phaser 3 game development.

Passive knowledgebase intended for semantic activation during Phaser work.

- Multi-scene flow, object pooling, and physics patterns
- Performance optimization and common pitfall avoidance
- Architecture guidance for game projects

#### report-writer

Structured technical analysis and debugging reports with standardized sections.

**Optional input:** topic

- Generates timestamped reports (debugging, analysis, implementation)
- Standardized sections: Executive Summary, Key Findings, Root Cause Analysis, Recommendations
- Evidence-based documentation with code references

#### rigorous-debug

Evidence-based debugging protocol using the scientific method.

- Requires one-time project-specific initialization before first use
- Enforces hypothesis → experiment → conclusion cycles
- Prevents assumption-driven debugging with structured evidence gathering

#### skill-writer

Tools for creating effective `SKILL.md` agent skills.

- Step-by-step workflow from pattern identification to polished SKILL.md
- Covers frontmatter, instruction structure, and best practices
- Helps extract reusable patterns into shareable skills

## Workspace Configuration

File-producing skills (interview, spex, report-writer, macros, study, gimme, promptopt) support configurable workspace directories with layered precedence (first match wins):

1. **Explicit override** — ask to use a specific workspace directory for this run
2. **Local config** (`.agents/skill-configs/<skill>/config.local.yaml`) — gitignored, personal overrides
3. **Project config** (`.agents/skill-configs/<skill>/config.yaml`) — committed to repo, shared with team
4. **Legacy fallback** (`.claude/skill-configs/<skill>/`) — only for skills that shipped older config paths

There are no built-in defaults for most file-producing skills. Each skill prompts for setup on first use. Output follows the `.agent-workspace/<folder>` convention (`specs`, `reports`, `interviews`, `macros`, `study`, `gimme`, `promptopt`).

Use `.agents/skill-configs/` for new configuration. This is a provider-neutral convention defined by this repository, not an Agent Skills ecosystem standard. The `.claude/skill-configs/` path is retained only as migration support for skills that previously used it; new skills do not need to add that fallback. Review legacy fallback removal after 2027-01-31.

## Other Agentic Tools

These skills use the Agent Skills `SKILL.md` format. Provider-specific install roots and activation notes live in the [cross-platform guide](docs/cross-platform/README.md); avoid copying those details into other docs.

## License

Personal use — adapt and modify as needed for your own projects.
