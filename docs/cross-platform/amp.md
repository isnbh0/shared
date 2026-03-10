[← Back to cross-platform overview](README.md)

# Amp (Sourcegraph)

> **Note:** The agentic tooling ecosystem is evolving rapidly. Paths and mechanisms described here are based on research as of early 2026 and may have changed. Verify against [Amp's current documentation](https://ampcode.com/manual) before use.

Amp supports SKILL.md-compatible skills and can bundle MCP servers alongside them. Skills are activated via semantic triggering.

## Installation

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

# Install a skill into your project
mkdir -p skills/interview
cp /tmp/shared/plugins/interview/skills/interview/* skills/interview/
```

> Check Amp's current documentation for the exact skills directory convention — it may use a project-level directory rather than a dot-prefixed config directory.

## Usage

Describe what you want naturally:

> "Interview me about the database migration"
> "Write a spec for the new API endpoints"

Amp reads the skill's `description` field and activates the matching skill.

## Context Files

Amp uses `AGENT.md` for project-level always-on instructions (similar to `CLAUDE.md` or `AGENTS.md`). For passive skills like `phaser`, reference them from `AGENT.md`:

```markdown
## Skills

When writing Phaser 3 code, consult `skills/phaser/SKILL.md` for patterns and best practices.
```

## Notes

- Amp works as both a CLI and VS Code extension
- Skills can be bundled with MCP servers via `mcp.json` — servers start when Amp launches but tools stay hidden until the skill is activated, reducing context usage
- Amp includes built-in sub-agents (Oracle for code analysis, Librarian for library docs) that complement installed skills
