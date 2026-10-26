[← Back to cross-platform overview](README.md)

# Pi

Use the skill root listed in the [compatibility SSOT](README.md). This page only covers repo-specific usage patterns.

## Installation

Pi discovers the skill roots listed in the [compatibility SSOT](README.md) natively, so the copy and symlink options from the overview work as-is:

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p ~/.pi/agent/skills
cp -R /tmp/shared/plugins/interview/skills/interview ~/.pi/agent/skills/
```

The repository is also a Pi package. The `pi` manifest in `package.json` declares the plugin skills Pi should load (`macros`, `my`, `spex`, and `merbook`):

```bash
pi install git:github.com/isnbh0/shared
```

Personal installs are written to `~/.pi/agent/settings.json`. Pi keeps its own clone under `~/.pi/agent/git/`; reconcile it with `pi update --extensions` after pushing to the repository. To load different plugins, edit the `pi.skills` manifest in `package.json` or narrow the package's `skills` in Pi settings.

## Usage

Force-load a skill with Pi's explicit selector, optionally followed by a request:

| Skill | Pi request |
|-------|------------|
| interview | `/skill:interview auth-system` |
| askme (macros) | `/skill:askme` |
| doubt (macros) | `/skill:doubt` |
| grounding (my) | `/skill:grounding` |

Skills without `disable-model-invocation: true` in their frontmatter are also advertised to the model and may load automatically when the task matches the description. Run `/reload` after changing skills during an active session.

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

## Notes

- Pi honors `disable-model-invocation: true`: the skill is hidden from automatic selection but stays available as `/skill:name`.
- The `macros:<name>` references inside skills resolve through the project `.mm/` install convention described in `~/.agents/macros/_INSTALL.md`; this is independent of how Pi loads the skill itself.
- Name collisions across installed skills keep the first discovered skill; the canonical `my` plugin skill names (for example `grounding`) are distinct from the `my-*` compatibility aliases.
