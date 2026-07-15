[← Back to cross-platform overview](README.md)

# Antigravity

Use the skill roots listed in the [compatibility SSOT](README.md). This page only covers repo-specific usage patterns.

## Installation

Copy the whole skill directory into the selected root:

```bash
git clone https://github.com/isnbh0/shared.git /tmp/shared

mkdir -p <skill-root>
cp -R /tmp/shared/plugins/interview/skills/interview <skill-root>/
```

Repeat for any other skills you want:

```bash
cp -R /tmp/shared/plugins/spex/skills/write <skill-root>/
cp -R /tmp/shared/plugins/report-writer/skills/report-writer <skill-root>/
cp -R /tmp/shared/plugins/rigorous-debug/skills/rigorous-debug <skill-root>/
```

## Usage

After installation, ask for the workflow by skill name or description, for example:

> "Use the interview skill for the auth system."
> "Use the write skill for the payment flow."

## Configuration

Use the shared config convention:

```bash
mkdir -p .agents/skill-configs/interview
vi .agents/skill-configs/interview/config.yaml
```

The `workspace_dir` setting controls where output files are written, relative to the project root unless the skill says otherwise.

## Notes

- Install the whole skill directory, including templates and knowledgebase files.
