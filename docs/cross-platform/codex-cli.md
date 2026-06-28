[← Back to cross-platform overview](README.md)

# Codex CLI

Use the skill root listed in the [compatibility SSOT](README.md). This page only covers repo-specific usage patterns.

## Installation

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p <skill-root>
cp -R /tmp/shared/plugins/interview/skills/interview <skill-root>/
cp -R /tmp/shared/plugins/spex/skills/write <skill-root>/spex-write
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

- Use `AGENTS.md` for always-on project instructions; keep task-specific workflows in skills.
- The `phaser` skill can be installed as a passive knowledgebase for Phaser work.
- Claude Code plugin namespace syntax such as `/spex:write` does not apply directly. Install the sub-skill you want and refer to it by its installed name or description.
