[← Back to cross-platform overview](README.md)

# Antigravity

> **Note:** The agentic tooling ecosystem is evolving rapidly. Paths and mechanisms described here are based on research as of early 2026 and may have changed. Verify against [Antigravity's current documentation](https://antigravity.google/docs/home) before use.

Google's agent-first IDE supports SKILL.md natively. Skills are activated via semantic triggering — the agent reads skill descriptions and activates the matching skill when your request fits.

## Installation

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

# Install a skill into your project
mkdir -p .antigravity/skills/interview
cp /tmp/shared/plugins/interview/skills/interview/* .antigravity/skills/interview/
```

Repeat for any other skills you want:

```bash
for skill in spex report-writer rigorous-debug; do
  mkdir -p .antigravity/skills/$skill
  cp /tmp/shared/plugins/$skill/skills/$skill/* .antigravity/skills/$skill/
done
```

## Usage

Describe what you want naturally. Antigravity matches your request against installed skill descriptions:

| What to say | Skill activated |
|-------------|----------------|
| "Interview me about the auth system" | interview |
| "Write a spec for the payment flow" | spex |
| "Debug this — use the rigorous method" | rigorous-debug |
| "Write a technical report on the outage" | report-writer |

## Configuration

Edit `config.yaml` in the skill's install directory:

```bash
vi .antigravity/skills/interview/config.yaml
```

The `workspace_dir` setting controls where output files are written, relative to the project root.

## Notes

- Antigravity adopted the SKILL.md standard early — skills work without modification
- The [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) repo aggregates community skills
- Passive skills like `phaser` activate automatically when you work on relevant code
- Antigravity's Manager view can orchestrate multiple agents, each with access to installed skills
