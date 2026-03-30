# Using These Skills with Other Agentic Tools

These skills use the **SKILL.md** format — markdown files with YAML frontmatter — which has become the cross-platform standard for AI coding agent instructions. While the plugin marketplace and slash commands are Claude Code-specific, the skills themselves work across multiple tools.

## Compatibility

| Tool | Install Location | Invocation | Config Paths | Notes |
|------|-----------------|------------|-------------|-------|
| [Claude Code](https://claude.com/claude-code) | `.claude/skills/<name>/` | `/skill-name` (slash command) | `.claude/skill-configs/` | Native support via plugin marketplace |
| [Codex CLI](codex-cli.md) | `.codex/skills/<name>/` | Semantic triggering | Adapt config paths | Full SKILL.md support |
| [Gemini CLI](gemini-cli.md) | `.gemini/skills/<name>/` | Semantic triggering or `.toml` commands | Adapt config paths | Extensions ecosystem |
| [Antigravity](antigravity.md) | `.antigravity/skills/<name>/` | Semantic triggering | Adapt config paths | Native SKILL.md support |
| [Amp](amp.md) | Project-level skills directory | Semantic triggering | Adapt config paths | SKILL.md compatible |
| [Cursor](cursor.md) | `.cursor/skills/<name>/` | Semantic triggering | Adapt config paths | Plugin marketplace |

## What Works Everywhere

- **SKILL.md content** — The instructions, methodology, and templates are tool-agnostic
- **YAML frontmatter** — `name` and `description` fields are the cross-platform standard
- **Template files** — All supporting files (SCRATCHPAD.template.md, etc.) work as-is
- **Workspace output** — The `.agent-workspace/` convention works in any tool

## What Needs Adaptation

### Invocation

Claude Code uses explicit slash commands (`/interview`, `/spex`). Other tools use **semantic triggering** — the agent reads the skill's `description` field and activates it when your request matches. Instead of typing `/interview career-change`, you'd say:

> "Interview me about a career change"

The agent matches this to the skill's description and follows its instructions.

### Configuration Paths

Skills reference Claude Code-specific config paths for layered configuration:

| Claude Code Path | Generic Equivalent |
|-----------------|-------------------|
| `.claude/skill-configs/<skill>/config.yaml` | Project-level config in the skill's install directory |
| `~/.claude/skills/<skill>/config.yaml` | User-level config in the tool's global skills directory |

Most tools don't have a layered config system. The simplest approach: edit `config.yaml` directly in the skill's install directory.

### Spex Sub-Skills

The spex plugin includes three sub-skills (`/spex:write`, `/spex:write-phased`, `/spex:implement`). In Claude Code, these are invoked via plugin namespace. In other tools, invoke by description:

> "Write a spec for the auth system"
> "Implement the spec at .agent-workspace/specs/260310-auth-system/SPEC.md"

## General Installation

For any tool that supports SKILL.md:

```bash
# Clone the repository
git clone https://github.com/isnbh0/shared.git /tmp/shared

# Copy a skill into your project
mkdir -p <project>/.<tool>/skills/<skill-name>
cp /tmp/shared/plugins/<skill-name>/skills/<skill-name>/* <project>/.<tool>/skills/<skill-name>/
```

Replace `<tool>` with your tool's config directory name (`codex`, `gemini`, `antigravity`, etc.).

See the tool-specific guides for exact paths and any additional steps.

> **Note:** The agentic tooling ecosystem is evolving rapidly. Directory paths and installation mechanisms described in these guides are based on research as of early 2026 and may have changed. Verify against each tool's current documentation before use.

## Available Skills

| Skill | Type | Description |
|-------|------|-------------|
| interview | Interactive | Structured discovery interviews for any topic |
| spex | Interactive | Two-phase specification → implementation workflow |
| report-writer | Interactive | Timestamped technical analysis reports |
| rigorous-debug | Interactive | Scientific hypothesis-driven debugging |
| skill-writer | Interactive | Guidance for creating SKILL.md files |
| critique | Interactive | External AI critique via Codex or Gemini CLI |
| macros | Interactive | Subagent orchestration: map-reduce and research-backed critique |
| phaser | Passive | Phaser 3 game development knowledgebase (18 files) |
