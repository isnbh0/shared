[← Back to cross-platform overview](README.md)

# Codex CLI

> **Note:** The agentic tooling ecosystem is evolving rapidly. Paths and mechanisms described here are based on research as of early 2026 and may have changed. Verify against [Codex CLI's current documentation](https://github.com/openai/codex) before use.

OpenAI's Codex CLI supports SKILL.md natively. Skills install to `.codex/skills/` and are activated via semantic triggering — Codex reads the skill's description and activates it when your request matches.

## Installation

### Project-level (recommended)

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

# Install a single skill
mkdir -p .codex/skills/interview
cp /tmp/shared/plugins/interview/skills/interview/* .codex/skills/interview/

# Install another
mkdir -p .codex/skills/spex
cp /tmp/shared/plugins/spex/skills/spex/* .codex/skills/spex/
```

### User-level

```bash
mkdir -p ~/.codex/skills/interview
cp /tmp/shared/plugins/interview/skills/interview/* ~/.codex/skills/interview/
```

## Usage

Codex uses semantic triggering. Describe what you want naturally:

| Instead of (Claude Code) | Say this |
|--------------------------|----------|
| `/interview auth-system` | "Interview me about the auth system" |
| `/spex write auth-refactor` | "Write a spec for the auth refactor" |
| `/spex implement ./spec.md` | "Implement the spec at ./spec.md" |
| `/report-writer perf-analysis` | "Write a report on the performance analysis" |
| `/rigorous-debug` | "Debug this using the rigorous debugging protocol" |

## Configuration

Edit `config.yaml` directly in the skill's install directory:

```bash
# Project-level
vi .codex/skills/interview/config.yaml

# User-level
vi ~/.codex/skills/interview/config.yaml
```

The `workspace_dir` setting works as-is — it specifies where output files are created relative to the project root.

## Notes

- Codex also supports `AGENTS.md` for always-on project instructions — this is separate from skills
- The `phaser` skill (passive knowledgebase) works well with Codex since semantic triggering naturally activates it when you're writing Phaser code
- Command aliases (`/write-spec`, etc.) don't apply — use natural language instead
