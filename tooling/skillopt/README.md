# SkillOpt Prompting Guide

[한국어](README.ko.md) | [Setup reference](SETUP.md)

Use this when you want a coding agent to optimize a skill or prompt with the
vendored SkillOpt tooling. The shortest path is to ask the agent to use the
`run-optimize` skill and let it orchestrate the data, config, launch, result
reading, and write-back.

SkillOpt is supervised: it only improves against a graded train/val/test task
set. A good prompt asks the agent to establish that graded set before launching
anything.

## Recommended Prompt

```text
Use the run-optimize skill to optimize <path-to-skill-or-prompt>.

Default to Codex through SkillOpt Guard unless I say otherwise. First inspect the
seed, then help me establish a graded train/val/test task set. Confirm the
success metric is faithful before writing config. Show me the resolved provider,
model, target backend, optimizer backend, output path, and split sizes before
launching. Do not launch until I explicitly approve. After the run, summarize
baseline vs best on the held-out test split and show me the diff before offering
to write best_skill.md back over the seed.
```

If your host does not expose slash commands, use the natural-language form:

```text
Use the "Optimizing Skills with SkillOpt" skill on <path-to-skill-or-prompt>.
```

## What The Agent Should Do

The agent should follow the workflow in
[`plugins/run-optimize/skills/run-optimize/SKILL.md`](../../plugins/run-optimize/skills/run-optimize/SKILL.md):

1. Load or create `run-optimize` config.
2. Identify the seed skill/prompt.
3. Establish graded train/val/test tasks.
4. Confirm the environment/scorer and success metric.
5. Choose chat vs exec target.
6. Choose provider/model.
7. Scaffold the run workspace and write `config.yaml`.
8. Show the resolved plan and wait for approval.
9. Launch SkillOpt and read `summary.json`, `history.json`, and `best_skill.md`.
10. Offer to write `best_skill.md` back to the original seed.

If the agent skips the graded-data conversation, stop it. That is the main
quality gate.

## Provider Prompts

### Codex Default

Use this for the subscription-safe default path.

```text
Use run-optimize on <path>. Use Codex through SkillOpt Guard:
target_backend=codex_exec, optimizer_backend=codex_chat, model=gpt-5.5.
Scrub metered API keys, use the guard, and require my approval before launch.
```

Expected launch shape:

```bash
cd tooling/skillopt
uv sync
unset CODEX_PROFILE OPENAI_API_KEY AZURE_OPENAI_API_KEY ANTHROPIC_API_KEY
uv run skillopt-oauth \
  --config runs/<name>/config.yaml \
  --target_backend codex_exec --optimizer_backend codex_chat \
  --out_root runs/<name>/outputs/run_codex
```

### Claude Subscription

Use this when the target behavior should be measured inside Claude Code.

```text
Use run-optimize on <path>. Use Claude through SkillOpt Guard:
target_backend=claude_code_exec, optimizer_backend=claude_chat. Ask me for the
Claude model slug if the config does not already specify one. Require approval
before launch.
```

Expected launch shape:

```bash
cd tooling/skillopt
uv sync
uv run skillopt-oauth \
  --config runs/<name>/config.yaml \
  --target_backend claude_code_exec --optimizer_backend claude_chat \
  --out_root runs/<name>/outputs/run_claude
```

### pi / GLM

Use this only as a deliberate metered-provider run.

```text
Use run-optimize on <path>. Use pi routed to zai/glm-5.2:
target_backend=pi_exec, optimizer_backend=pi_chat, optimizer=zai/glm-5.2,
target=zai/glm-5.2. Treat this as metered and require PI_ALLOW_METERED=zai plus
my explicit approval before launch.
```

Guarded launch shape:

```bash
cd tooling/skillopt
uv sync
PI_ALLOW_METERED=zai uv run skillopt-oauth \
  --config runs/<name>/config.yaml \
  --target_backend pi_exec --optimizer_backend pi_chat \
  --out_root runs/<name>/outputs/run_glm
```

Direct trainer shape:

```bash
cd tooling/skillopt
uv sync
PI_ALLOW_METERED=zai uv run skillopt-train \
  --config runs/<name>/config.yaml \
  --out_root runs/<name>/outputs/run_glm
```

The guarded form enforces the metered-provider opt-in before spawning `pi`.

## Prompt When You Already Have Graded Data

```text
Use run-optimize on <seed-path>. My graded data is already split at
<data-dir> with train/items.json, val/items.json, and test/items.json. Verify
the schema and counts. Use <provider/backend/model choices>. Show the resolved
plan before launch.
```

For the built-in `searchqa` environment, each item should have `id`,
`question`, `context`, and `answers`. The score is normalized exact match and
token F1 against the gold answers.

## Prompt When You Do Not Have Graded Data Yet

```text
Use run-optimize on <seed-path>, but do not launch yet. First help me design a
small reviewed train/val/test task set. Propose candidate tasks, explain what a
correct answer/output should be, and wait for my review before using them.
```

Synthetic tasks are useful for bootstrapping, but the optimizer will learn the
wrong behavior if the gold answers or success criteria are wrong.

## Guardrails To Put In The Prompt

- Ask before spending subscription quota or metered budget.
- Confirm the success metric before writing config.
- Use an exec target for tool-using coding-agent skills.
- Use a chat target only for pure prompts.
- Keep train, val, and test disjoint.
- Do not overwrite the seed unless held-out test results improved and the user
  approves the diff.

## Reference Docs

- [SkillOpt Guard setup and backend reference](SETUP.md)
- [`run-optimize` skill instructions](../../plugins/run-optimize/skills/run-optimize/SKILL.md)
- [`run-optimize` config example](../../plugins/run-optimize/skills/run-optimize/config.example.yaml)
- [Codex demo](demo/searchqa_codex/)
- [pi/GLM demo](demo/searchqa_pi/)
