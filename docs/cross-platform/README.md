# Using These Skills Across Agentic Tools

These skills use the Agent Skills **SKILL.md** format: a directory containing a `SKILL.md` file with YAML frontmatter plus any supporting files. The skill content is portable; installation paths, command syntax, and marketplace packaging are host-specific.

## Compatibility SSOT

This table is the only place in this repository that should list third-party install roots. Other docs should link here or use `<skill-root>`. Verify the target tool's current docs before turning these rows into automation.

| Tool | Skill Root / Status | Notes |
|------|---------------------|-------|
| [Codex CLI](codex-cli.md) | `.agents/skills/<name>/` | Agent Skills support |
| [Gemini CLI](gemini-cli.md) | `.agents/skills/<name>/`, `.gemini/skills/<name>/`, or extension-local `skills/<name>/` | Agent Skills support |
| [Amp](amp.md) | `.agents/skills/<name>/`; user roots include `~/.config/agents/skills/`, `~/.agents/skills/`, and `~/.config/amp/skills/` | Agent Skills support |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code/skills) | `.claude/skills/<name>/` or marketplace plugin | Marketplace packages use `.claude-plugin/` metadata |
| [Cursor](cursor.md) | `.cursor/skills/<name>/`; Cursor docs also mention `.agents/skills/<name>/` | Agent Skills support |
| [Antigravity](antigravity.md) | Not confirmed here | Verify current Antigravity docs or UI before installing |

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

mkdir -p <skill-root>
cp -R /tmp/shared/plugins/interview/skills/interview <skill-root>/
```

Resolve `<skill-root>` from the compatibility table or the target host's current docs. Do not copy only `SKILL.md` when the skill has templates, examples, or knowledgebase files.

### Invocation

Claude Code marketplace installs expose slash-style invocations such as `/interview` or `/spex:write`. Other tools may use semantic triggering, explicit skill mentions, command files, or UI activation:

> "Interview me about a career change"

The portable part is the skill name, frontmatter description, and `SKILL.md` instructions; the activation mechanism belongs to the host.

### Configuration Paths

Skills read layered configuration from an agent-neutral location:

| Config Path | Scope |
|-------------|-------|
| `.agents/skill-configs/<skill>/config.local.yaml` | Project-local personal config, gitignored |
| `.agents/skill-configs/<skill>/config.yaml` | Project-level config, committed to the repo |
| `~/.agents/skill-configs/<skill>/config.local.yaml` | User-local config for cross-project skills, such as `dredge` |
| `~/.agents/skill-configs/<skill>/config.yaml` | User-level config for cross-project skills, such as `dredge` |

Most file-producing project skills read project-local config. Cross-project skills that operate independently of the current repository may read user-scope config. Legacy `.claude/skill-configs/` and `~/.claude/skill-configs/` fallbacks are migration support for skills that previously shipped with those paths; newly published skills do not need to add legacy fallbacks. Review legacy fallback removal after 2027-01-31.

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

> **Maintenance note:** Keep provider-specific install roots in the compatibility table above. Use `<skill-root>` everywhere else unless a provider-specific page is explicitly documenting an exception.

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
| promptopt | Interactive | Artifact-backed prompt optimization against user-owned cases |
| phaser | Passive | Phaser 3 game development knowledgebase (18 files) |
