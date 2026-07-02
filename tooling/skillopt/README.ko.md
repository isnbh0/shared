# SkillOpt 프롬프트 가이드

[English](README.md) | [설정 레퍼런스](SETUP.ko.md)

vendored SkillOpt 도구로 스킬이나 프롬프트를 최적화하고 싶을 때 코딩 에이전트에
이렇게 요청하세요. 가장 짧은 경로는 에이전트에게 `run-optimize` 스킬을 사용하게
하고, 데이터 준비, config 작성, 실행, 결과 해석, write-back을 오케스트레이션하게
하는 것입니다.

SkillOpt는 supervised optimizer입니다. train/val/test로 나뉜 graded task set에
대해서만 개선됩니다. 좋은 프롬프트는 실행 전에 이 graded set을 먼저 확정하게
합니다.

## 권장 프롬프트

```text
<skill-or-prompt-경로>를 run-optimize 스킬로 최적화해 주세요.

제가 다르게 말하지 않으면 SkillOpt Guard를 통한 Codex를 기본값으로 사용하세요.
먼저 seed를 읽고, graded train/val/test task set을 만드는 것을 도와주세요. config를
쓰기 전에 success metric이 실제 성공을 잘 측정하는지 확인해 주세요. 실행 전에
resolved provider, model, target backend, optimizer backend, output path, split size를
보여주고, 제가 명시적으로 승인하기 전에는 launch하지 마세요. 실행 후에는 held-out
test split에서 baseline과 best를 비교해 요약하고, best_skill.md를 seed에 덮어쓰기
전에 diff를 보여주세요.
```

<details>
<summary>Original English</summary>

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

</details>

slash command가 없는 host에서는 자연어로 요청합니다.

```text
"Optimizing Skills with SkillOpt" 스킬을 <skill-or-prompt-경로>에 사용해 주세요.
```

<details>
<summary>Original English</summary>

```text
Use the "Optimizing Skills with SkillOpt" skill on <path-to-skill-or-prompt>.
```

</details>

## 에이전트가 해야 할 일

에이전트는
[`plugins/run-optimize/skills/run-optimize/SKILL.md`](../../plugins/run-optimize/skills/run-optimize/SKILL.md)의
워크플로우를 따라야 합니다.

1. `run-optimize` config를 읽거나 만듭니다.
2. seed skill/prompt를 확인합니다.
3. train/val/test graded task를 확정합니다.
4. environment/scorer와 success metric을 확인합니다.
5. chat target과 exec target 중 하나를 고릅니다.
6. provider/model을 고릅니다.
7. run workspace를 만들고 `config.yaml`을 씁니다.
8. resolved plan을 보여주고 승인을 기다립니다.
9. SkillOpt를 실행하고 `summary.json`, `history.json`, `best_skill.md`를 읽습니다.
10. `best_skill.md`를 원래 seed에 반영할지 제안합니다.

에이전트가 graded-data 확인을 건너뛰면 멈추세요. 이것이 핵심 품질 게이트입니다.

## Provider별 프롬프트

### Codex 기본값

subscription-safe 기본 경로입니다.

```text
<경로>에 run-optimize를 사용해 주세요. SkillOpt Guard를 통해 Codex를 사용하세요:
target_backend=codex_exec, optimizer_backend=codex_chat, model=gpt-5.5.
metered API key를 scrub하고 guard를 사용하세요. launch 전에는 제 승인을 받으세요.
```

<details>
<summary>Original English</summary>

```text
Use run-optimize on <path>. Use Codex through SkillOpt Guard:
target_backend=codex_exec, optimizer_backend=codex_chat, model=gpt-5.5.
Scrub metered API keys, use the guard, and require my approval before launch.
```

</details>

예상 실행 형태:

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

Claude Code 안에서의 동작을 측정해야 할 때 사용합니다.

```text
<경로>에 run-optimize를 사용해 주세요. SkillOpt Guard를 통해 Claude를 사용하세요:
target_backend=claude_code_exec, optimizer_backend=claude_chat. config에 Claude
model slug가 없다면 저에게 물어보세요. launch 전에는 승인을 받으세요.
```

<details>
<summary>Original English</summary>

```text
Use run-optimize on <path>. Use Claude through SkillOpt Guard:
target_backend=claude_code_exec, optimizer_backend=claude_chat. Ask me for the
Claude model slug if the config does not already specify one. Require approval
before launch.
```

</details>

### pi / GLM

명시적인 metered-provider 실행으로만 사용하세요.

```text
<경로>에 run-optimize를 사용해 주세요. zai/glm-5.2로 라우팅되는 pi를 사용하세요:
target_backend=pi_exec, optimizer_backend=pi_chat, optimizer=zai/glm-5.2,
target=zai/glm-5.2. 이것은 metered 실행으로 취급하고, launch 전에는
PI_ALLOW_METERED=zai와 제 명시적 승인을 요구하세요.
```

<details>
<summary>Original English</summary>

```text
Use run-optimize on <path>. Use pi routed to zai/glm-5.2:
target_backend=pi_exec, optimizer_backend=pi_chat, optimizer=zai/glm-5.2,
target=zai/glm-5.2. Treat this as metered and require PI_ALLOW_METERED=zai plus
my explicit approval before launch.
```

</details>

guarded 실행 형태:

```bash
cd tooling/skillopt
uv sync
PI_ALLOW_METERED=zai uv run skillopt-oauth \
  --config runs/<name>/config.yaml \
  --target_backend pi_exec --optimizer_backend pi_chat \
  --out_root runs/<name>/outputs/run_glm
```

guarded 형태는 `pi`를 spawn하기 전에 metered-provider opt-in을 확인합니다.

## 이미 graded data가 있을 때

```text
<seed-경로>에 run-optimize를 사용해 주세요. graded data는 이미 <data-dir> 아래에
train/items.json, val/items.json, test/items.json으로 나뉘어 있습니다. schema와
count를 확인하세요. <provider/backend/model 선택값>을 사용하세요. launch 전에
resolved plan을 보여주세요.
```

<details>
<summary>Original English</summary>

```text
Use run-optimize on <seed-path>. My graded data is already split at
<data-dir> with train/items.json, val/items.json, and test/items.json. Verify
the schema and counts. Use <provider/backend/model choices>. Show the resolved
plan before launch.
```

</details>

내장 `searchqa` environment는 `id`, `question`, `context`, `answers` 필드를
기대합니다. 점수는 gold answer에 대한 normalized exact match와 token F1입니다.

## graded data가 아직 없을 때

```text
<seed-경로>에 run-optimize를 사용하되, 아직 launch하지 마세요. 먼저 제가 검토할 수
있는 작은 train/val/test task set을 설계하도록 도와주세요. candidate task를
제안하고, 올바른 answer/output이 무엇이어야 하는지 설명한 뒤, 사용하기 전에 제
검토를 기다리세요.
```

<details>
<summary>Original English</summary>

```text
Use run-optimize on <seed-path>, but do not launch yet. First help me design a
small reviewed train/val/test task set. Propose candidate tasks, explain what a
correct answer/output should be, and wait for my review before using them.
```

</details>

합성 task는 시작점으로는 유용하지만, gold answer나 success criterion이 틀리면
optimizer가 잘못된 행동을 학습합니다.

## 프롬프트에 넣을 가드레일

- subscription quota나 metered budget을 쓰기 전에 질문하게 하세요.
- config 작성 전에 success metric을 확인하게 하세요.
- tool을 쓰는 coding-agent skill은 exec target을 쓰게 하세요.
- 순수 prompt에만 chat target을 쓰게 하세요.
- train, val, test는 서로 겹치지 않게 하세요.
- held-out test 결과가 개선되고 사용자가 diff를 승인하기 전에는 seed를 덮어쓰지
  않게 하세요.

## 레퍼런스

- [SkillOpt Guard 설정 및 backend 레퍼런스](SETUP.ko.md)
- [`run-optimize` 스킬 지침](../../plugins/run-optimize/skills/run-optimize/SKILL.md)
- [`run-optimize` config 예시](../../plugins/run-optimize/skills/run-optimize/config.example.yaml)
- [Codex demo](demo/searchqa_codex/README.ko.md)
- [pi/GLM demo](demo/searchqa_pi/README.ko.md)
