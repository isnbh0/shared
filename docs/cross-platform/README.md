# Using These Skills Across Agentic Tools

These skills use the Agent Skills **SKILL.md** format: a directory containing a `SKILL.md` file with YAML frontmatter plus any supporting files. The skill content is portable; installation paths, command syntax, and marketplace packaging are host-specific.

## Compatibility SSOT

This table is the only place in this repository that should list third-party install roots. Other docs should link here or use `<skill-root>`. Verify the target tool's current docs before turning these rows into automation.

| Tool | Project roots | User roots | Other packaging |
|------|---------------|------------|-----------------|
| [Codex CLI](codex-cli.md) | `.agents/skills/<name>/` | `~/.agents/skills/<name>/` | — |
| [Gemini CLI](gemini-cli.md) | `.agents/skills/<name>/`, `.gemini/skills/<name>/` | `~/.agents/skills/<name>/`, `~/.gemini/skills/<name>/` | Extension-local `skills/<name>/` |
| [Amp](amp.md) | `.agents/skills/<name>/` | `~/.config/agents/skills/<name>/`, `~/.agents/skills/<name>/`, `~/.config/amp/skills/<name>/` | — |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code/skills) | `.claude/skills/<name>/` | See current Claude Code documentation | Marketplace plugins use `.claude-plugin/` metadata |
| [Cursor](cursor.md) | `.cursor/skills/<name>/`, `.agents/skills/<name>/` | See current Cursor documentation | Cursor plugins use their own packaging |
| [Antigravity](antigravity.md) | `.agents/skills/<name>/` | `~/.gemini/config/skills/<name>/` | — |

## What Works Everywhere

- **SKILL.md content** - Instructions, methodology, templates, and supporting files are portable.
- **YAML frontmatter** - `name` and `description` are the key fields agents use for discovery.
- **Workspace output** - The `.agent-workspace/` convention is a filesystem convention, not tied to one agent.

## Skill Names and Host Selectors

Shared documentation uses plain skill names. Developer-facing inventories may use `plugin:name` to disambiguate a bundled skill, but that identifier is not a command.

| Installation | Claude Code | Codex | Other hosts |
|--------------|-------------|-------|-------------|
| Plugin | `/plugin:name` | `$plugin:name` | Use the host's documented selector |
| Direct skill | `/name` | `$name` | Use the host's documented selector or mention the skill by name |

Keep provider sigils in host-specific guidance like this table. In portable skill instructions, say “the doubt skill”; never teach a host-specific invocation.

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

Activation belongs to the host. Shared documentation names the skill; host-specific documentation may show the corresponding selector. Hosts may also support semantic triggering, command files, or UI activation:

> "Interview me about a career change"

The portable part is the skill name, frontmatter description, and `SKILL.md` instructions; the activation mechanism belongs to the host.

### Configuration Paths

Skills read layered configuration using this repository's provider-neutral convention. These paths are not defined by the Agent Skills standard:

| Config Path | Scope |
|-------------|-------|
| `.agents/skill-configs/<skill>/config.local.yaml` | Project-local personal config, gitignored |
| `.agents/skill-configs/<skill>/config.yaml` | Project-level config, committed to the repo |
| `~/.agents/skill-configs/<skill>/config.local.yaml` | User-local config for cross-project skills, such as `dredge` |
| `~/.agents/skill-configs/<skill>/config.yaml` | User-level config for cross-project skills, such as `dredge` |

Most file-producing project skills read project-local config. Cross-project skills that operate independently of the current repository may read user-scope config. Legacy `.claude/skill-configs/` and `~/.claude/skill-configs/` fallbacks are migration support for skills that previously shipped with those paths; newly published skills do not need to add legacy fallbacks. Review legacy fallback removal after 2027-01-31.

### Spex Sub-Skills

The spex plugin includes the `write`, `write-phased`, and `implement` skills. Install the specific skill directory or ask by description:

> "Write a spec for the auth system"
> "Implement the spec at .agent-workspace/specs/260310-auth-system/SPEC.md"

## Tool Guides

- [Codex CLI](codex-cli.md)
- [Gemini CLI](gemini-cli.md)
- [Antigravity](antigravity.md)
- [Amp](amp.md)
- [Cursor](cursor.md)

> **Maintenance note:** Keep provider-specific install roots in the compatibility table above. Use `<skill-root>` everywhere else unless a provider-specific page is explicitly documenting an exception. The repository's skill inventory lives in the root README and `llms.txt`, not here.
