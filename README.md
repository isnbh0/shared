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
/plugin install report-writer@isnbh0
/plugin install rigorous-debug@isnbh0
/plugin install skill-writer@isnbh0
/plugin install phaser@isnbh0
/plugin install critique@isnbh0
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

Seven independent skills, each available as a Claude Code plugin:

### critique

External AI critique via CLI tools (Codex, Gemini).

```
/critique:codex [file-path] [focus]
/critique:gemini [file-path] [focus]
```

- Gets an independent second opinion on specs, code, or recent changes
- **Codex backend:** Runs in a read-only sandbox, supports reasoning effort levels (default, high, xhigh)
- **Gemini backend:** Sandboxed with write and network restrictions

### interview

Structured requirements discovery through conversational interviews.

```
/interview <topic> [--ref <path>] [--workspace <dir>]
```

- Extracts requirements, constraints, and design decisions through guided Q&A
- Supports reference files to anchor discussion around existing artifacts
- Produces timestamped synthesis documents in the workspace

### phaser

Battle-tested patterns and best practices for Phaser 3 game development.

Passive knowledgebase — automatically consulted when writing Phaser code.

- Multi-scene flow, object pooling, and physics patterns
- Performance optimization and common pitfall avoidance
- Architecture guidance for game projects

### report-writer

Structured technical analysis and debugging reports with standardized sections.

```
/report-writer [topic] [--workspace <dir>]
```

- Generates timestamped reports (debugging, analysis, implementation)
- Standardized sections: Executive Summary, Key Findings, Root Cause Analysis, Recommendations
- Evidence-based documentation with code references

### rigorous-debug

Evidence-based debugging protocol using the scientific method.

```
/rigorous-debug
```

- Requires one-time project-specific initialization before first use
- Enforces hypothesis → experiment → conclusion cycles
- Prevents assumption-driven debugging with structured evidence gathering

### skill-writer

Tools for creating effective Claude Code skills.

```
/skill-writer
```

- Step-by-step workflow from pattern identification to polished SKILL.md
- Covers frontmatter, instruction structure, and best practices
- Helps extract reusable patterns into shareable skills

### spex

Two-phase specification and implementation workflow that separates planning from execution.

Three self-contained commands:

- `/spex__write-spec` — Create a spec, commit it, and stop — no implementation
- `/spex__write-spec-phased` — Create a multi-phase spec for complex features
- `/spex__implement-spec` — Follow an existing spec, implement, update status, and commit

## Workspace Configuration

All file-producing skills (interview, spex, report-writer) support configurable workspace directories with layered precedence:

1. **Project config** (`.claude/skill-configs/<skill>/config.yaml`)
2. **User config** (`~/.claude/skills/<skill>/config.yaml`)
3. **CLI flag** (`--workspace <dir>`)

Defaults follow the `.agent-workspace/<folder>` convention (`specs`, `reports`, `interviews`).

## Other Agentic Tools

These skills use the SKILL.md format, which is supported across multiple AI coding tools. See the [cross-platform guide](docs/cross-platform/README.md) for installation instructions for:

- [Codex CLI](docs/cross-platform/codex-cli.md) (OpenAI)
- [Gemini CLI](docs/cross-platform/gemini-cli.md) (Google)
- [Antigravity](docs/cross-platform/antigravity.md) (Google)
- [Amp](docs/cross-platform/amp.md) (Sourcegraph)
- [Cursor](docs/cross-platform/cursor.md)

## License

Personal use — adapt and modify as needed for your own projects.
