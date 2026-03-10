[← Back to cross-platform overview](README.md)

# Cursor

> **Note:** The agentic tooling ecosystem is evolving rapidly. Paths and mechanisms described here are based on research as of early 2026 and may have changed. Verify against [Cursor's current documentation](https://cursor.com/docs) before use.

Cursor's plugin marketplace (launched with Cursor 2.5) supports skills as part of its plugin system. Skills can also be installed manually.

## Installation

### Manual (project-level)

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p .cursor/skills/interview
cp /tmp/shared/plugins/interview/skills/interview/* .cursor/skills/interview/
```

### As a Cursor plugin

Cursor plugins use a `plugin.json` manifest that can bundle skills, rules, MCP servers, and hooks. To package these skills as a Cursor plugin, create a `plugin.json` following the [Cursor plugins documentation](https://cursor.com/docs/plugins).

## Usage

Cursor's agent discovers installed skills and activates them when relevant. Describe what you want:

> "Interview me about the auth system"
> "Write a spec for the refactor"

## Rules

Cursor uses `.cursorrules` for project-level always-on instructions (similar to `CLAUDE.md`). For passive skills like `phaser`, reference them:

```
When writing Phaser 3 code, consult .cursor/skills/phaser/SKILL.md for patterns and best practices.
```

## Notes

- The [Cursor Marketplace](https://cursor.com/marketplace) is the official registry for sharing plugins
- Cursor plugins can bundle MCP servers alongside skills
- Cursor supports both on-demand skills and always-on rules — use skills for interactive workflows and rules for conventions
