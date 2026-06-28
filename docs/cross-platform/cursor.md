[← Back to cross-platform overview](README.md)

# Cursor

Use the skill roots listed in the [compatibility SSOT](README.md). This page only covers repo-specific usage patterns.

## Installation

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p <skill-root>
cp -R /tmp/shared/plugins/interview/skills/interview <skill-root>/
```

### As a Cursor plugin

For plugin packaging, follow Cursor's current plugin docs and include the relevant directories from `plugins/<plugin>/skills/<skill>/`.

## Usage

Use Cursor's documented skill activation flow. These prompt phrasings are typical for this repository's interactive skills:

> "Interview me about the auth system"
> "Write a spec for the refactor"

## Rules

For passive skills like `phaser`, reference the installed skill from project rules if you want it always considered:

```text
When writing Phaser 3 code, consult <skill-root>/phaser/SKILL.md for patterns and best practices.
```

## Configuration

Use the shared config convention:

```bash
mkdir -p .agents/skill-configs/interview
vi .agents/skill-configs/interview/config.yaml
```

## Notes

- Install the whole skill directory, including templates and knowledgebase files.
- Use skills for on-demand workflows and project rules for project-wide conventions.
- Cursor plugin packaging is separate from this repository's Claude Code `.claude-plugin/` marketplace metadata.
