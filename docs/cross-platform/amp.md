[← Back to cross-platform overview](README.md)

# Amp (Sourcegraph)

Use the skill roots listed in the [compatibility SSOT](README.md). This page only covers repo-specific usage patterns.

## Installation

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p <skill-root>
cp -R /tmp/shared/plugins/interview/skills/interview <skill-root>/
```

## Usage

Use Amp's documented skill activation flow. These prompt phrasings are typical for this repository's interactive skills:

> "Interview me about the database migration"
> "Write a spec for the new API endpoints"

## Context Files

For passive skills like `phaser`, reference them from project instructions if you want them always considered:

```markdown
## Skills

When writing Phaser 3 code, consult `<skill-root>/phaser/SKILL.md` for patterns and best practices.
```

## Configuration

Use the shared config convention:

```bash
mkdir -p .agents/skill-configs/interview
vi .agents/skill-configs/interview/config.yaml
```

## Notes

- Install the whole skill directory, including templates and knowledgebase files.
- Keep this repository's filesystem skills independent from any host-specific MCP packaging.
