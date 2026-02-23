# Shared Dotfiles & Configs

Personal collection of generalizable dotfiles, configurations, and Claude Code skills for reuse across projects.

[한국어](README.ko.md)

## Skills

Located in `.claude/skills/`, these skills enhance Claude Code's capabilities:

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

### spec-workflow

Two-phase specification and implementation workflow that separates planning from execution.

```
/spec-workflow <write|write-phased|implement> [args...] [--workspace <dir>]
```

- **write**: Create a spec, commit it, and stop — no implementation
- **write-phased**: Create a multi-phase spec for complex features
- **implement**: Follow an existing spec, implement, update status, and commit

## Command Aliases

| Alias | Expands to |
|-------|------------|
| `/write-spec` | `/spec-workflow write` |
| `/write-spec-phased` | `/spec-workflow write-phased` |
| `/implement-spec` | `/spec-workflow implement` |

## Workspace Configuration

All file-producing skills (interview, spec-workflow, report-writer) support configurable workspace directories with layered precedence:

1. **Project config** (`.claude/skill-configs/<skill>/config.yaml`)
2. **User config** (`~/.claude/skills/<skill>/config.yaml`)
3. **CLI flag** (`--workspace <dir>`)

Defaults follow the `agent-workspace/<folder>` convention (`specs`, `reports`, `interviews`).

## Installation

```bash
# Clone to your preferred location
git clone <repo-url> ~/shared

# Symlink .claude directory into a project
ln -s ~/shared/.claude /path/to/project/.claude

# Or copy specific skills
cp -r ~/shared/.claude/skills/spec-workflow /path/to/project/.claude/skills/
```

## License

Personal use — adapt and modify as needed for your own projects.
