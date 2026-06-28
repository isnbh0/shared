[← Back to cross-platform overview](README.md)

# Gemini CLI

Gemini CLI has an extension and custom-command system. Treat these repository skills as portable `SKILL.md` resources: package them inside a Gemini extension, or create commands/context that explicitly tell Gemini to read the relevant `SKILL.md`.

## Installation

### As extension resources

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

# Example extension-local layout
mkdir -p .gemini/extensions/shared-skills/skills/interview
cp -R /tmp/shared/plugins/interview/skills/interview/* .gemini/extensions/shared-skills/skills/interview/
```

Add the extension manifest and any command wiring required by Gemini CLI's current extension format.

### As plain project resources

If you do not want to package an extension, keep skills in a project directory and point commands or `GEMINI.md` at them:

```bash
mkdir -p .agents/skills
cp -R /tmp/shared/plugins/interview/skills/interview .agents/skills/
```

## Custom Slash Commands

Gemini CLI supports custom slash commands via TOML files. A command can load a skill explicitly:

```toml
# .gemini/commands/interview.toml
[command]
name = "interview"
description = "Conduct a structured discovery interview"

[command.prompt]
text = """
Read .agents/skills/interview/SKILL.md and follow it.
Topic: $ARGS
"""
```

Place commands in `.gemini/commands/` for the project or `~/.gemini/commands/` globally.

### Example command for spex write

```toml
# .gemini/commands/write.toml
[command]
name = "write"
description = "Write a specification document"

[command.prompt]
text = """
Read .agents/skills/spex-write/SKILL.md and follow it.
Args: $ARGS
"""
```

## Usage

With custom commands:

```text
/interview auth-system
/write auth-refactor
```

Without custom commands, use natural language after making the skill file available as context:

> "Read .agents/skills/interview/SKILL.md and interview me about the auth system design."

## Configuration

Use the shared config convention:

```bash
mkdir -p .agents/skill-configs/interview
vi .agents/skill-configs/interview/config.yaml
```

## Context Files

Gemini CLI loads `GEMINI.md` as project-level always-on context. For passive skills like `phaser`, reference the skill from `GEMINI.md`:

```markdown
## Skills

When writing Phaser 3 code, consult `.agents/skills/phaser/SKILL.md` for patterns and best practices.
```

## Notes

- Gemini CLI extensions can bundle MCP servers, commands, and context alongside project resources.
- Use custom commands for interactive workflows such as `interview` and `spex`.
- Use `GEMINI.md` for always-on project conventions and passive knowledgebases.
