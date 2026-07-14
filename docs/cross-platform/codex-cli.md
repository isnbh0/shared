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

Use natural language or explicitly mention a skill with Codex's `$` selector:

| Canonical reference | Codex direct-install request |
|---------------------|------------------------------|
| `skill(interview:interview)` | `$interview auth-system` |
| `skill(spex:write)` | `$spex-write auth-refactor` |
| `skill(spex:implement)` | `$spex-implement ./spec.md` |
| `skill(report-writer:report-writer)` | `$report-writer perf-analysis` |
| `skill(rigorous-debug:rigorous-debug)` | `$rigorous-debug` |

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
- Codex plugin installs preserve namespaces, so `skill(macros:doubt)` is selected as `$macros:doubt`; direct installs use the installed directory name, such as `$doubt`.
