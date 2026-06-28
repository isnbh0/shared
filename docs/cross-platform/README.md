# Using These Skills Across Agentic Tools

These skills use the Agent Skills **SKILL.md** format: a directory containing a `SKILL.md` file with YAML frontmatter plus any supporting files. The skill content is portable; installation paths, command syntax, and marketplace packaging are host-specific.

## Compatibility

| Tool | Install Location | Invocation | Config Paths | Notes |
|------|------------------|------------|--------------|-------|
| [Codex CLI](codex-cli.md) | `.agents/skills/<name>/` | Semantic triggering or explicit skill mention | `.agents/skill-configs/` | Native Agent Skills support |
| [Amp](amp.md) | `.agents/skills/<name>/` | Semantic triggering | `.agents/skill-configs/` | Also reads user-level Agent Skills locations |
| [Antigravity](antigravity.md) | `.agents/skills/<name>/` | Semantic triggering | `.agents/skill-configs/` | Native Agent Skills support |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code/skills) | `.claude/skills/<name>/` or marketplace plugin | Slash command / skill invocation | `.agents/skill-configs/` | Marketplace packages use `.claude-plugin/` metadata |
| [Cursor](cursor.md) | `.cursor/skills/<name>/` | Semantic triggering or explicit skill mention | `.agents/skill-configs/` | Cursor-specific skills directory |
| [Gemini CLI](gemini-cli.md) | `skills/<name>/` inside an extension, or explicit command/context wiring | Custom command or natural language with context | `.agents/skill-configs/` | Extension system can package skills |

## What Works Everywhere

- **SKILL.md content** - Instructions, methodology, templates, and supporting files are portable.
- **YAML frontmatter** - `name` and `description` are the key fields agents use for discovery.
- **Workspace output** - The `.agent-workspace/` convention is a filesystem convention, not tied to one agent.
- **Configuration** - `.agents/skill-configs/` keeps project/user config independent from any one host.

## What Needs Adaptation

### Installation Path

Install the whole skill directory:

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p <project>/.agents/skills
cp -R /tmp/shared/plugins/interview/skills/interview <project>/.agents/skills/
```

If your host does not read `.agents/skills`, use that host's skills directory from the compatibility table. Do not copy only `SKILL.md` when the skill has templates, examples, or knowledgebase files.

### Invocation

Claude Code marketplace installs expose slash-style invocations such as `/interview` or `/spex:write`. Other tools usually use semantic triggering:

> "Interview me about a career change"

The agent matches this to the skill's `description` and follows its instructions. Some hosts also support explicit skill mentions or custom commands.

### Configuration Paths

Skills read layered configuration from an agent-neutral location:

| Config Path | Scope |
|-------------|-------|
| `.agents/skill-configs/<skill>/config.local.yaml` | Project-local personal config, gitignored |
| `.agents/skill-configs/<skill>/config.yaml` | Project-level config, committed to the repo |
| `~/.agents/skill-configs/<skill>/config.local.yaml` | User-local config for cross-project skills, such as `dredge` |
| `~/.agents/skill-configs/<skill>/config.yaml` | User-level config for cross-project skills, such as `dredge` |

Most file-producing project skills read project-local config. Cross-project skills that operate independently of the current repository may read user-scope config. Older installs are still resolved from the legacy `.claude/skill-configs/` and `~/.claude/skill-configs/` paths as fallbacks.

### Spex Sub-Skills

The spex plugin includes `write`, `write-phased`, and `implement` skills. In Claude Code marketplace installs these are invoked as `/spex:write`, `/spex:write-phased`, and `/spex:implement`. In other tools, install the specific skill directory or ask by description:

> "Write a spec for the auth system"
> "Implement the spec at .agent-workspace/specs/260310-auth-system/SPEC.md"

## Tool Guides

- [Codex CLI](codex-cli.md)
- [Gemini CLI](gemini-cli.md)
- [Antigravity](antigravity.md)
- [Amp](amp.md)
- [Cursor](cursor.md)

> **Note:** The agentic tooling ecosystem changes quickly. Paths and mechanisms in these guides were checked against public docs on 2026-06-28, but you should verify against each tool's current documentation before publishing automation around them.

## Available Skills

| Skill | Type | Description |
|-------|------|-------------|
| interview | Interactive | Structured discovery interviews for any topic |
| spex | Interactive | Two-phase specification -> implementation workflow |
| report-writer | Interactive | Timestamped technical analysis reports |
| rigorous-debug | Interactive | Scientific hypothesis-driven debugging |
| skill-writer | Interactive | Guidance for creating SKILL.md files |
| critique | Interactive | External AI critique via Codex or Gemini CLI |
| macros | Interactive | Subagent orchestration: map-reduce and research-backed critique |
| phaser | Passive | Phaser 3 game development knowledgebase (18 files) |
