[← Back to cross-platform overview](README.md)

# Gemini CLI

Use the skill roots listed in the [compatibility SSOT](README.md). This page only covers repo-specific usage patterns.

## Installation

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p <skill-root>
cp -R /tmp/shared/plugins/interview/skills/interview <skill-root>/
```

For extension-bundled installs, copy the skill directory into the extension's documented skills directory:

```bash
mkdir -p <extension-skill-root>
cp -R /tmp/shared/plugins/interview/skills/interview <extension-skill-root>/
```

## Usage

Use Gemini CLI's documented skill activation flow. These prompt phrasings are typical for this repository's interactive skills:

> "Interview me about the auth system design."

## Optional Commands

If you use Gemini CLI custom commands, keep the command-file schema in Gemini's docs and make the command prompt reference the installed skill:

```text
Read <skill-root>/interview/SKILL.md and follow it.
Topic: $ARGS
```

For `spex-write`:

```text
Read <skill-root>/spex-write/SKILL.md and follow it.
Args: $ARGS
```

With custom commands:

```text
/interview auth-system
/write auth-refactor
```

## Configuration

Use the shared config convention:

```bash
mkdir -p .agents/skill-configs/interview
vi .agents/skill-configs/interview/config.yaml
```

## Context Files

For passive skills like `phaser`, reference the skill from your always-on Gemini CLI context file:

```markdown
## Skills

When writing Phaser 3 code, consult `<skill-root>/phaser/SKILL.md` for patterns and best practices.
```

## Notes

- Use custom commands when you want stable slash-command aliases for interactive workflows such as `interview` and `spex`.
- Use always-on context files for project conventions and passive knowledgebases.
