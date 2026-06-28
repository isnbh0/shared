# Developer Guide

## Publishing a New Claude Code Marketplace Plugin

### File structure

Each marketplace plugin lives under `plugins/<name>/` and has this layout. The `.claude-plugin/` directory is Claude Code marketplace metadata; the portable skill content lives under `skills/<skill-name>/`.

```
plugins/<name>/
├── .claude-plugin/
│   └── plugin.json        # Claude Code marketplace metadata
└── skills/
    └── <skill-name>/
        ├── SKILL.md            # The skill itself
        └── config.example.yaml # Config reference (if the skill uses config)
```

A plugin can contain multiple portable Agent Skills (e.g., macros has mapreduce, doubt; spex has write, write-phased, implement). Each skill gets its own directory under `skills/`.

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

When publishing a plugin to the Claude Code marketplace, update all of the following:

- [ ] `plugins/<name>/skills/<skill-name>/SKILL.md` — the skill
- [ ] `plugins/<name>/skills/<skill-name>/config.example.yaml` — if the skill uses config
- [ ] `plugins/<name>/.claude-plugin/plugin.json` — plugin metadata (bump version if updating)
- [ ] `.claude-plugin/marketplace.json` — add entry to `plugins` array
- [ ] `llms.txt` — update these sections (skip any that don't apply):
  - Direct-install and Claude Code marketplace install blocks
  - The "published to the marketplace" note (keep plugin list and skill enumeration current)
  - Available Skills → Published section (add skill entry)
  - File Structure Reference (add plugin/skill to tree)
  - Workspace Configuration table (if file-producing)
  - Notes for LLMs (keep skill enumeration current)
- [ ] `README.md` — update these sections (skip any that don't apply):
  - Direct-install and Claude Code marketplace install blocks
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

- `.agents/skill-configs/<skill>/config.local.yaml` — local/personal, gitignored
- `.agents/skill-configs/<skill>/config.yaml` — project-wide, committed
- Cross-project skills (e.g. `dredge`, which operates over machine-level coding-agent transcript stores regardless of cwd) read **user-scope** config under `~/.agents/skill-configs/<skill>/` instead of project-relative paths, since cwd is incidental and the config is machine-level (an optional per-repo override may live at `.agents/skill-configs/<skill>/`).
- The `.agents/skill-configs/` convention is repository-owned and agent-neutral. Keep provider-specific install roots and activation behavior centralized in `docs/cross-platform/README.md`; do not duplicate them in publishing checklists. Older installs still resolve from the legacy `.claude/skill-configs/<skill>/` (and `~/.claude/skill-configs/<skill>/` for cross-project skills) location as a fallback; spex additionally falls back to its former `.agent-workspace/spex/` path. When config is found only at a legacy path, the skill uses it and offers to move it to the new location.

Always ship a `config.example.yaml` alongside `SKILL.md` documenting all supported fields.
