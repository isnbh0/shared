# Before→after 데모: pi에서 zai/glm-5.2로 프롬프트 최적화

[English](README.md)

**타깃**(`pi_exec`)과 **옵티마이저**(`pi_chat`)가 모두 `pi` CLI를 통해 **`zai/glm-5.2`**로 실행되는 SkillOpt 예시입니다. 일부러 나쁜 seed prompt에서 시작해 `pi_chat` 옵티마이저가 어떻게 고쳐 쓰는지 추적합니다. ([`searchqa_codex`](../searchqa_codex/README.ko.md)의 pi 대응 예시입니다.)

target leg는 agentic합니다. `pi_exec`가 하나의 skill을 로드하고 GLM-5.2를 tools on 상태로 실행하며, task마다 rollout 하나를 수행합니다. optimizer leg는 같은 모델에 대한 single-shot `pi_chat` completion입니다. provider/model은 `zai/glm-5.2` deployment slug에서 오며, runtime guard가 모든 응답이 실제로 `zai`/`glm-5.2`에서 제공되었는지 확인합니다.

## 결과

Held-out **test** set:

| | exact-match | token-F1 |
| --- | --- | --- |
| **before** (bad seed) | **0.00** | 0.11 |
| **after** (optimized) | **1.00** | 1.00 |

`+1.00` exact-match가 step 2에서 accepted 되었고, **198s / 16 pi calls / 54,259 tokens**로 모두 `zai/glm-5.2`에서 실행되었습니다. (`trace/summary.json`.)

## 옵티마이저가 한 일

작업([SearchQA](../../vendor/skillopt/skillopt/envs/searchqa))은 `<answer>…</answer>` 안의 텍스트를 SQuAD exact-match / F1로 채점합니다. seed(`trace/skill_v0000_BEFORE.md`)는 **의도적으로 틀린** 지시입니다. 짧은 gold span과 exact-match가 불가능하도록 answer tag 안에 완성된 설명문을 강제하므로 baseline EM은 0입니다.

`pi_chat` 옵티마이저(GLM-5.2)는 실패한 rollout에서 원인을 진단하고 지시를 **반대로 뒤집었습니다**(`trace/best_skill_AFTER.md`).

> **before:** "always write a complete, polished explanation rather than a short
> label … put your full explanation INSIDE `<answer>` … at least 15 words … Never
> put a bare word."
>
> **after:** "put ONLY the concise final answer inside `<answer>` … as brief as
> possible — typically a single word, number, or short phrase … Do not write full
> sentences, restate the question, or add explanatory context."

`trace/history.json`: step 1 `reject`(candidate edit가 gate 통과 실패), step 2 `accept_new_best`(selection 0→1.0), step 3 `skip_no_patches`(이미 최적).

## 재현

```bash
cd tooling/skillopt
uv sync
PI_ALLOW_METERED=zai uv run skillopt-train \
  --config demo/searchqa_pi/config.yaml \
  --out_root demo/searchqa_pi/outputs/run_pi_pi
```

`glm-5.2`를 제공하는 `zai` provider entry가 설정된 `pi` CLI(여기서는 v0.79.10)가 필요합니다. pi가 제공할 수 있는 다른 `provider/model` slug를 쓰려면 `config.yaml`의 `model.optimizer` / `model.target`을 바꾸세요. `--api-key`는 넘기지 마세요. pi는 자체 provider config에서 auth를 해결합니다.

`skillopt-train`은 직접 trainer entry point(`scripts.train:main` console script)이며 `skillopt-oauth` wrapper가 아닙니다. `PI_ALLOW_METERED=zai`는 `zai`를 allowed-metered provider set에 넣습니다. `config.yaml`의 `pi_allowed_metered_providers: [zai]`도 같은 policy를 기록합니다. 이 provider를 해당 run에서 의도적으로 허용할 때만 사용하세요. `PI_ALLOW_METERED=zai`와 함께 `skillopt-oauth`에서도 실행할 수 있습니다. 원본 run dir(`outputs/`)은 gitignore 대상이며, 정리된 `trace/`만 커밋되어 있습니다.

## zai/glm-5.2 라우팅 확인

- `trace/config.resolved.json`: `optimizer_backend: pi_chat`, `target_backend: pi_exec`, `optimizer_model` / `target_model` 모두 `zai/glm-5.2`.
- 모든 `pi` `message_end` event가 `provider: "zai"`와 `model: "glm-5.2"`를 echo했습니다. `actual == intended` runtime guard(`_guard_provider`)가 spawn마다 이를 확인했고 한 번도 trip되지 않았습니다. 불일치하면 non-retryable `PiBillingError`로 run이 중단됩니다.
- `trace/routing_proof.txt`: config backend, persisted `pi` JSON stream에서 수집한 provider/model(모두 `zai`/`glm-5.2`), guard status.
- `trace/summary.json` `token_summary`: 사용량은 `rollout`(`pi_exec` target)과 `analyst`(`pi_chat` optimizer) stage에만 귀속됩니다.

## 파일

```text
config.yaml              # run config (pi_chat optimizer + pi_exec target, zai/glm-5.2, tiny loop)
seed_skill_bad.md        # 일부러 나쁜 seed prompt
data/{train,val,test}/   # context 안에만 answer가 있는 작은 fictional-fact QA split
trace/                   # 커밋된 before→after artifacts:
  skill_v0000_BEFORE.md  #   seed
  best_skill_AFTER.md    #   optimized skill
  history.json           #   step별 accept/reject/score
  summary.json           #   baseline vs best, held-out test
  config.resolved.json   #   resolved config (pi_chat/pi_exec, zai/glm-5.2)
  routing_proof.txt      #   provider/model served + guard status
```
