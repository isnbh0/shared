[← Back to cross-platform overview](README.md)

# Antigravity

No Antigravity `SKILL.md` install root is recorded in this repository's [compatibility SSOT](README.md). Verify Antigravity's current product docs or UI before installing these skills there.

## Installation

If Antigravity documents an Agent Skills-compatible directory, copy the whole skill directory there:

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p <skill-root>
cp -R /tmp/shared/plugins/interview/skills/interview <skill-root>/
```

Repeat for any other skills you want:

```bash
cp -R /tmp/shared/plugins/spex/skills/write <skill-root>/spex-write
cp -R /tmp/shared/plugins/report-writer/skills/report-writer <skill-root>/
cp -R /tmp/shared/plugins/rigorous-debug/skills/rigorous-debug <skill-root>/
```

## Usage

Use Antigravity's documented skill activation flow, if one exists. After installation, ask for the workflow by skill name or description, for example:

> "Use the interview skill for the auth system."
> "Use the spex-write skill for the payment flow."

## Configuration

Use the shared config convention:

```bash
mkdir -p .agents/skill-configs/interview
vi .agents/skill-configs/interview/config.yaml
```

The `workspace_dir` setting controls where output files are written, relative to the project root unless the skill says otherwise.

## Notes

- Install the whole skill directory, including templates and knowledgebase files.
- Do not publish automation that writes Antigravity skill directories until the target path is verified against current Antigravity docs.
