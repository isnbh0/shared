[← Back to cross-platform overview](README.md)

# Amp (Sourcegraph)

Amp supports Agent Skills and can activate them by semantic matching. Project skills can live under `.agents/skills/`; user-level skills can live in shared Agent Skills locations documented by Amp.

## Installation

### Project-level

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p .agents/skills
cp -R /tmp/shared/plugins/interview/skills/interview .agents/skills/
```

### User-level

```bash
mkdir -p ~/.agents/skills
cp -R /tmp/shared/plugins/interview/skills/interview ~/.agents/skills/
```

## Usage

Describe what you want naturally:

> "Interview me about the database migration"
> "Write a spec for the new API endpoints"

Amp reads the skill's metadata and activates matching instructions.

## Context Files

Amp supports project-level instruction files such as `AGENTS.md`. For passive skills like `phaser`, reference them from project instructions if you want them always considered:

```markdown
## Skills

When writing Phaser 3 code, consult `.agents/skills/phaser/SKILL.md` for patterns and best practices.
```

## Configuration

Use the shared config convention:

```bash
mkdir -p .agents/skill-configs/interview
vi .agents/skill-configs/interview/config.yaml
```

## Notes

- Install the whole skill directory, including templates and knowledgebase files.
- Amp can also use MCP servers alongside skills; keep this repository's filesystem skills independent from any host-specific MCP packaging.
