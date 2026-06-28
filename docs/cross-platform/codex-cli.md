[← Back to cross-platform overview](README.md)

# Codex CLI

Codex supports Agent Skills natively. Install project skills under `.agents/skills/` or user-level skills under `~/.agents/skills/`. Codex can activate relevant skills automatically and can also be directed to use a specific skill by name.

## Installation

### Project-level

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

# Install a single skill
mkdir -p .agents/skills
cp -R /tmp/shared/plugins/interview/skills/interview .agents/skills/

# Install a spex sub-skill
cp -R /tmp/shared/plugins/spex/skills/write .agents/skills/spex-write
```

### User-level

```bash
mkdir -p ~/.agents/skills
cp -R /tmp/shared/plugins/interview/skills/interview ~/.agents/skills/
```

## Usage

Use natural language or explicitly mention the skill:

| Claude Code invocation | Codex request |
|------------------------|---------------|
| `/interview auth-system` | "Interview me about the auth system" |
| `/spex:write auth-refactor` | "Use the spex-write skill to write a spec for the auth refactor" |
| `/spex:implement ./spec.md` | "Use the spex-implement skill to implement ./spec.md" |
| `/report-writer perf-analysis` | "Write a report on the performance analysis" |
| `/rigorous-debug` | "Debug this using the rigorous debugging protocol" |

## Configuration

Use the agent-neutral config directory, not the skill install directory:

```bash
# Project shared config
mkdir -p .agents/skill-configs/interview
vi .agents/skill-configs/interview/config.yaml

# Personal machine-wide config
mkdir -p ~/.agents/skill-configs/dredge
vi ~/.agents/skill-configs/dredge/config.yaml
```

The `workspace_dir` setting works as-is; relative paths are resolved from the project root unless a skill says otherwise.

## Notes

- Codex also supports `AGENTS.md` for always-on project instructions; that is separate from skills.
- The `phaser` skill works as a passive knowledgebase when installed, because Codex can infer relevance from the request and code context.
- Claude Code plugin namespace syntax such as `/spex:write` does not apply directly. Install the sub-skill you want and refer to it by its installed name or description.
