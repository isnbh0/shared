[← Back to cross-platform overview](README.md)

# Codex CLI

Use the skill root listed in the [compatibility SSOT](README.md). This page only covers repo-specific usage patterns.

## Installation

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p <skill-root>
cp -R /tmp/shared/plugins/interview/skills/interview <skill-root>/
cp -R /tmp/shared/plugins/spex/skills/write <skill-root>/
```

## Usage

Use natural language or explicitly mention a skill with Codex's `$` selector:

| Skill | Codex direct-install request |
|-------|------------------------------|
| interview | `$interview auth-system` |
| spex write | `$write auth-refactor` |
| spex implement | `$implement ./spec.md` |
| report-writer | `$report-writer perf-analysis` |
| rigorous-debug | `$rigorous-debug` |

## Configuration

Use this repository's provider-neutral config convention, not the skill install directory:

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
- Codex plugin installs preserve namespaces, so the bundled doubt skill is selected as `$macros:doubt`; direct installs use the installed directory name, such as `$doubt`.
