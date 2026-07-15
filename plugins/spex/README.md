# Spex

Spex separates specification writing from implementation:

- `write` creates and commits a single specification, then stops.
- `write-phased` creates and commits a phased specification, then stops.
- `implement` implements an existing specification and records progress.

Each skill is self-contained and authoritative at runtime. Configure the workspace in `.agents/skill-configs/spex/config.yaml` or `config.local.yaml`; legacy `.agent-workspace/spex/` and `.claude/skill-configs/spex/` paths remain supported by the skills.

```yaml
workspace_dir: .agent-workspace/specs
```
