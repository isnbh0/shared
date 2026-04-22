# Developer Guide

## Publishing a New Plugin

### File structure

Each plugin lives under `plugins/<name>/` and has this layout:

```
plugins/<name>/
├── .claude-plugin/
│   └── plugin.json        # Plugin metadata
└── skills/
    └── <skill-name>/
        ├── SKILL.md            # The skill itself
        └── config.example.yaml # Config reference (if the skill uses config)
```

A plugin can contain multiple skills (e.g., macros has mapreduce, doubt; spex has write, write-phased, implement). Each skill gets its own directory under `skills/`.

`plugin.json` format:

```json
{
  "name": "<name>",
  "description": "<one-line description>",
  "version": "1.0.0",
  "author": { "name": "isnbh0" }
}
```

### Publishing checklist

When publishing a plugin to the marketplace, update all of the following:

- [ ] `plugins/<name>/skills/<skill-name>/SKILL.md` — the skill
- [ ] `plugins/<name>/skills/<skill-name>/config.example.yaml` — if the skill uses config
- [ ] `plugins/<name>/.claude-plugin/plugin.json` — plugin metadata (bump version if updating)
- [ ] `.claude-plugin/marketplace.json` — add entry to `plugins` array
- [ ] `llms.txt` — update these sections (skip any that don't apply):
  - Install command block
  - The "published to the marketplace" note (keep plugin list and skill enumeration current)
  - Available Skills → Published section (add skill entry)
  - File Structure Reference (add plugin/skill to tree)
  - Workspace Configuration table (if file-producing)
  - Notes for LLMs (keep skill enumeration current)
- [ ] `README.md` — update these sections (skip any that don't apply):
  - Install command block
  - Published skills section (add entry)
  - Workspace Configuration note (if file-producing)
- [ ] `README.ko.md` — same sections as README.md

### Versioning

Bump `version` in `plugin.json` using semver. Decide based on what changed **for the end user**:

- **patch** (1.0.x) — internal restructure, bug fixes, doc updates. No user-facing change.
- **minor** (1.x.0) — new skill added, new feature. Existing invocations still work.
- **major** (x.0.0) — removed/renamed skills, changed invocation surface, breaking config changes.

### Config pattern

Skills that produce files use a layered config pattern. The skill prompts for setup on first use if no config is found. Config files:

- `.claude/skill-configs/<skill>/config.local.yaml` — local/personal, gitignored
- `.claude/skill-configs/<skill>/config.yaml` — project-wide, committed

Always ship a `config.example.yaml` alongside `SKILL.md` documenting all supported fields.
