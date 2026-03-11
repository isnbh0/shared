[← Back to cross-platform overview](README.md)

# Gemini CLI

> **Note:** The agentic tooling ecosystem is evolving rapidly. Paths and mechanisms described here are based on research as of early 2026 and may have changed. Verify against [Gemini CLI's current documentation](https://geminicli.com/docs/) before use.

Google's Gemini CLI has an extensions ecosystem that supports prompts, custom commands, and MCP servers. Skills can be installed as extensions or loaded as context files.

## Installation

### As project-level skills

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p .gemini/skills/interview
cp /tmp/shared/plugins/interview/skills/interview/* .gemini/skills/interview/
```

### As a Gemini CLI extension

Package skills as a Gemini extension for installation via `gemini extensions install`. See the [Gemini CLI extensions docs](https://geminicli.com/docs/extensions/) for the extension directory structure.

## Custom Slash Commands

Gemini CLI supports custom slash commands via `.toml` files. To create a command for a skill, add a `.toml` file to `.gemini/commands/`:

```toml
# .gemini/commands/interview.toml
[command]
name = "interview"
description = "Conduct a structured discovery interview"

[command.prompt]
text = """
Read the skill instructions at .gemini/skills/interview/SKILL.md and follow them.
Topic: $ARGS
"""
```

Place in `.gemini/commands/` (project-level) or `~/.gemini/commands/` (global).

### Example commands for other skills

```toml
# .gemini/commands/write-spec.toml
[command]
name = "write-spec"
description = "Write a specification document"

[command.prompt]
text = """
Read the skill instructions at .gemini/skills/spex/SKILL.md and follow them.
Mode: write
Args: $ARGS
"""
```

## Usage

With custom commands:

```
/interview auth-system
/write-spec auth-refactor
```

Without custom commands, use natural language:

> "Interview me about the auth system design"

## Configuration

Edit `config.yaml` directly in the skill's install directory:

```bash
vi .gemini/skills/interview/config.yaml
```

## Context Files

Gemini CLI loads `GEMINI.md` as always-on context. For passive skills like `phaser`, you can reference the skill from `GEMINI.md`:

```markdown
## Skills

When writing Phaser 3 code, consult `.gemini/skills/phaser/SKILL.md` for patterns and best practices.
```

## Notes

- Gemini CLI extensions can bundle MCP servers, themes, and hooks alongside skills
- The Extensions Gallery at [geminicli.com/extensions](https://geminicli.com/extensions/browse/) is the central registry for sharing extensions
- `GEMINI.md` serves the same role as Claude Code's `CLAUDE.md` — project-level always-on instructions
