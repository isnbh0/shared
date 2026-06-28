[← Back to cross-platform overview](README.md)

# Cursor

Cursor supports skills through its own skills directory and plugin ecosystem. Install these repository skills as complete `SKILL.md` directories.

## Installation

### Manual project-level install

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p .cursor/skills
cp -R /tmp/shared/plugins/interview/skills/interview .cursor/skills/
```

### User-level install

```bash
mkdir -p ~/.cursor/skills
cp -R /tmp/shared/plugins/interview/skills/interview ~/.cursor/skills/
```

### As a Cursor plugin

Cursor plugins can bundle skills, rules, MCP servers, and hooks. To package these skills as a Cursor plugin, create the plugin manifest expected by Cursor and include the relevant directories from `plugins/<plugin>/skills/<skill>/`.

## Usage

Cursor discovers installed skills and activates them when relevant. Describe what you want:

> "Interview me about the auth system"
> "Write a spec for the refactor"

## Rules

Cursor uses project rules for always-on instructions. For passive skills like `phaser`, reference the installed skill from your project rules if you want it always considered:

```text
When writing Phaser 3 code, consult .cursor/skills/phaser/SKILL.md for patterns and best practices.
```

## Configuration

Use the shared config convention:

```bash
mkdir -p .agents/skill-configs/interview
vi .agents/skill-configs/interview/config.yaml
```

## Notes

- Install the whole skill directory, including templates and knowledgebase files.
- Use skills for on-demand workflows and Cursor rules for project-wide conventions.
- Cursor plugin packaging is separate from this repository's Claude Code `.claude-plugin/` marketplace metadata.
