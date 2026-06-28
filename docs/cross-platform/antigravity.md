[← Back to cross-platform overview](README.md)

# Antigravity

Antigravity supports Agent Skills through the shared `.agents/skills/` convention. Skills are activated by semantic matching against the skill description and available context.

## Installation

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

# Install a skill into your project
mkdir -p .agents/skills
cp -R /tmp/shared/plugins/interview/skills/interview .agents/skills/
```

Repeat for any other skills you want:

```bash
mkdir -p .agents/skills
cp -R /tmp/shared/plugins/spex/skills/write .agents/skills/spex-write
cp -R /tmp/shared/plugins/report-writer/skills/report-writer .agents/skills/
cp -R /tmp/shared/plugins/rigorous-debug/skills/rigorous-debug .agents/skills/
```

## Usage

Describe what you want naturally. Antigravity matches your request against installed skill descriptions:

| What to say | Skill activated |
|-------------|----------------|
| "Interview me about the auth system" | interview |
| "Write a spec for the payment flow" | spex-write |
| "Debug this using the rigorous method" | rigorous-debug |
| "Write a technical report on the outage" | report-writer |

## Configuration

Use the shared config convention:

```bash
mkdir -p .agents/skill-configs/interview
vi .agents/skill-configs/interview/config.yaml
```

The `workspace_dir` setting controls where output files are written, relative to the project root unless the skill says otherwise.

## Notes

- Install the whole skill directory, including templates and knowledgebase files.
- Passive skills like `phaser` activate automatically when you work on relevant code.
- Antigravity can also consume skills provided by plugins; package layout may differ from direct `.agents/skills` installs.
