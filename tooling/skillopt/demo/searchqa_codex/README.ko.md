# Before→after 데모: codex 구독에서 프롬프트 최적화

[English](README.md)

**타깃**(`codex_exec`)과 **옵티마이저**(`codex_chat`)가 모두 **codex / ChatGPT OAuth 구독**에서 실행되는 SkillOpt 예시입니다. metered API 호출이 발생할 수 없도록 구성되어 있으며, 일부러 나쁜 seed prompt에서 시작해 `codex_chat` 옵티마이저가 어떻게 고쳐 쓰는지 추적합니다.

옵티마이저 쪽 실행은 vendored `codex_chat` backend(`../../vendor/skillopt`)와 wrapper의 `--optimizer_backend` 주입 덕분에 가능합니다. 기본 upstream SkillOpt는 옵티마이저를 metered chat API로 제한합니다.

## 결과

Held-out **test** set, exact-match(`hard`):

| | exact-match | token-F1 |
| --- | --- | --- |
| **before** (bad seed) | **0.00** | 0.18 |
| **after** (optimized) | **1.00** | 1.00 |

`+1.00` exact-match가 step 1에서 accepted 되었고, **88s / 16 codex calls / 54k tokens**로 모두 구독 경로에서 실행되었습니다. (`trace/summary.json`.)

## 옵티마이저가 한 일

작업([SearchQA](../../vendor/skillopt/skillopt/envs/searchqa))은 `<answer>…</answer>` 안의 텍스트를 SQuAD exact-match / F1로 채점합니다. seed(`trace/skill_v0000_BEFORE.md`)는 **의도적으로 틀린** 지시입니다. 짧은 gold span과 exact-match가 불가능하도록 answer tag 안에 완성된 설명문을 강제하므로 baseline EM은 0입니다.

`codex_chat` 옵티마이저는 실패한 rollout에서 원인을 진단하고 지시를 **반대로 뒤집었습니다**(`trace/best_skill_AFTER.md`).

> **before:** "always write a complete, polished explanation rather than a short
> label … put your full explanation INSIDE `<answer>` … at least 15 words … Never
> put a bare word."
>
> **after:** "return only the shortest exact answer span … Do not add explanation,
> restate the question, or include surrounding context … A bare word, number, name,
> or short phrase is correct when that is the minimal answer."

`trace/history.json`: step 1 `accept_new_best`(selection 0→1.0), steps 2–3 `skip_no_patches`(이미 최적).

## 재현

```bash
cd tooling/skillopt
uv sync
unset CODEX_PROFILE OPENAI_API_KEY AZURE_OPENAI_API_KEY ANTHROPIC_API_KEY
export SKILLOPT_OAUTH_LOG_DIR=demo/searchqa_codex/outputs/_oauth_log
uv run skillopt-oauth \
  --config demo/searchqa_codex/config.yaml \
  --target_backend codex_exec --optimizer_backend codex_chat \
  --out_root demo/searchqa_codex/outputs/run_codex_codex
```

codex ChatGPT 구독(`~/.codex/auth.json`, `auth_mode: "chatgpt"`)이 필요합니다. 모델은 `gpt-5.5`(codex/upstream default)입니다. 다른 구독 모델 slug를 쓰려면 `config.yaml`의 `model.optimizer` / `model.target`을 바꾸세요.

여기서는 감사 기록에 명시되도록 `--optimizer_backend codex_chat`을 직접 넘깁니다. 생략하면 wrapper가 codex → `codex_chat`으로 **주입**합니다. 원본 run dir(`outputs/`)은 gitignore 대상이며, 정리된 `trace/`만 커밋되어 있습니다.

## 구독 경로 유지 확인

- `trace/oauth_runs.jsonl`(`handoff`): `provider: codex`, `preflight.verdict: oauth`, `OPTIMIZER_BACKEND: codex_chat`.
- `trace/config.resolved.json`: `optimizer_backend: codex_chat`, `target_backend: codex_exec`.
- `trace/summary.json` `token_summary`: 사용량은 `rollout`(target)과 `analyst`(optimizer) stage에만 귀속됩니다. azure/openai stage는 없습니다.
- outputs에서 secret-leak grep을 돌려도 아무것도 나오지 않습니다. env scrub은 모든 `*_API_KEY` / `*_AUTH_TOKEN`을 제거하므로 metered backend로 잘못 라우팅되면 과금 대신 fail closed 됩니다.

## 파일

```text
config.yaml              # run config (codex/codex, gpt-5.5, tiny loop)
seed_skill_bad.md        # 일부러 나쁜 seed prompt
data/{train,val,test}/   # context 안에만 answer가 있는 작은 fictional-fact QA split
trace/                   # 커밋된 before→after artifacts:
  skill_v0000_BEFORE.md  #   seed
  best_skill_AFTER.md    #   optimized skill
  history.json           #   step별 accept/reject/score
  summary.json           #   baseline vs best, held-out test
  config.resolved.json   #   routing proof
  oauth_runs.jsonl       #   guard audit record
```
