# SkillOpt Guard 설정

[프롬프트 가이드](README.ko.md) | [English setup](SETUP.md)

[Microsoft SkillOpt](https://github.com/microsoft/SkillOpt)를 로컬 에이전트
CLI로 실행할 때 라우팅, 자격 증명 사전 확인, 비밀값 제거를 명시적으로 처리하는
런처입니다.

이 디렉터리는 두 부분으로 구성됩니다.

- `SkillOpt Guard`: `skillopt-oauth` 명령으로 제공되는
  `skillopt-train` 실행 가드
- `vendor/skillopt`: `codex_chat`, `pi_chat`, `pi_exec` 백엔드 배선을 추가한
  고정 버전 SkillOpt 포크

가드는 SkillOpt의 타깃 롤아웃과 옵티마이저 재작성 단계가 의도한 로컬 CLI 경로를
사용하도록 합니다. 지원 provider는 `claude`, `codex`, `pi`입니다.

## 가드 동작

`skillopt-oauth`는 `skillopt-train`을 실행하기 전에 다음을 수행합니다.

1. **자격 증명 사전 확인.** 선택된 provider가 의도한 로컬 인증으로 실행 가능한지
   확인합니다. `claude`는 `CLAUDE_CODE_OAUTH_TOKEN`, macOS Keychain의
   `Claude Code-credentials`, `~/.claude/.credentials.json`을 확인합니다.
   `codex`는 `~/.codex/auth.json`의 `auth_mode == "chatgpt"`를 확인합니다.
   `pi`는 설정된 provider 항목과 metered provider opt-in 규칙을 확인합니다.
2. **비밀값 제거.** child 환경에서 모든 `*_API_KEY`, `*_AUTH_TOKEN`을 제거합니다.
   `CLAUDE_CODE_OAUTH_TOKEN`은 Claude Code OAuth 토큰이므로 보존합니다.
3. **두 역할 라우팅.** 타깃 backend를 설정하고, 명시하지 않았다면 옵티마이저
   backend를 주입합니다.

기본 라우팅:

| Provider | Target backend | Optimizer backend |
| --- | --- | --- |
| `claude` | `claude_code_exec` | `claude_chat` |
| `codex` | `codex_exec` | `codex_chat` |
| `pi` | `pi_exec` | `pi_chat` |

## 빠른 시작

```bash
cd tooling/skillopt
uv sync
uv run pytest
```

가드로 SkillOpt 작업 실행:

```bash
uv run skillopt-oauth \
  --backend codex_exec \
  --config demo/searchqa_codex/config.yaml \
  --out_root demo/searchqa_codex/outputs/run_codex_codex
```

provider는 `--backend`, `--target_backend`, `--optimizer_backend`에서 추론됩니다.
필요하면 `SKILLOPT_OAUTH_TARGET=claude|codex|pi`로 고정할 수 있습니다.

실행 없이 라우팅만 확인하려면 dry run을 사용합니다.

```bash
SKILLOPT_OAUTH_DRY_RUN=1 uv run skillopt-oauth \
  --backend codex_exec \
  --config demo/searchqa_codex/config.yaml
```

## Vendored SkillOpt 포크

`vendor/skillopt`는 upstream SkillOpt `v0.1.0`에 고정되어 있습니다. 로컬 변경은
backend와 config 배선 추가에 한정됩니다.

- `codex_chat`: `codex exec`를 호출하는 CLI 기반 옵티마이저
- `pi_chat`: `pi -p --mode json --no-tools` 기반 옵티마이저 및 chat target
- `pi_exec`: tools를 켠 `pi -p --mode json` 기반 agentic rollout target

SkillOpt의 학습 루프, 데이터셋, 평가 흐름, 체크포인트 처리는 vendored package가
담당합니다. pin과 로컬 변경 목록은
[`vendor/skillopt/PINNED_UPSTREAM.md`](vendor/skillopt/PINNED_UPSTREAM.md)를
참고하세요.

## Codex 및 Claude 실행

upstream SkillOpt는 `codex_exec`, `claude_code_exec` 타깃 backend를 제공하지만,
옵티마이저는 설정하지 않으면 `openai_chat`으로 기본 설정됩니다. 가드는
`codex_chat` 또는 `claude_chat`을 주입하여 옵티마이저 단계도 같은 로컬 CLI 경로를
사용하게 합니다.

명시적으로 backend를 지정할 수 있습니다.

```bash
uv run skillopt-oauth \
  --config demo/searchqa_codex/config.yaml \
  --target_backend codex_exec \
  --optimizer_backend codex_chat \
  --out_root demo/searchqa_codex/outputs/run_codex_codex
```

[`demo/searchqa_codex/`](demo/searchqa_codex/)에는 `codex_exec`와 `codex_chat`으로
수행한 SearchQA before/after 예제가 들어 있습니다.

## pi backend

`pi` backend는 SkillOpt의 각 역할을 `provider/model` deployment slug로 라우팅합니다.
예: `zai/glm-5.2`, `openai-codex/gpt-5.5`, `github-copilot/gpt-5.5`.

- `pi_chat`: optimizer call 및 chat target
- `pi_exec`: agentic target rollout
- provider가 없는 model 이름은 `PI_PROVIDER`를 사용하며 기본값은 `openai-codex`
- runtime guard가 stream의 `provider`, `model`이 pin과 일치하는지 확인

예시 config:

```yaml
model:
  optimizer_backend: pi_chat
  target_backend: pi_exec
  optimizer: zai/glm-5.2
  target: zai/glm-5.2
  pi_allowed_metered_providers: [zai]
```

직접 trainer 실행:

```bash
PI_ALLOW_METERED=zai uv run skillopt-train \
  --config demo/searchqa_pi/config.yaml \
  --out_root demo/searchqa_pi/outputs/run_pi_pi
```

가드 실행:

```bash
PI_ALLOW_METERED=zai uv run skillopt-oauth \
  --backend pi_exec \
  --config demo/searchqa_pi/config.yaml \
  --out_root demo/searchqa_pi/outputs/run_pi_pi
```

### Metered Provider Opt-In

`openai-codex`, `github-copilot`은 subscription provider로 취급합니다. `zai`,
`anthropic`은 metered provider로 취급하며 `skillopt-oauth`에서 실행하려면 명시적
opt-in이 필요합니다.

둘 중 하나로 opt-in합니다.

- `PI_ALLOW_METERED=zai,anthropic`
- leaf config 파일의 `model.pi_allowed_metered_providers: [zai, anthropic]`

둘 다 있으면 `PI_ALLOW_METERED`가 우선합니다. 가드의 preflight는 leaf
`--config` 파일에서만 `model.pi_allowed_metered_providers`를 읽으며 `_base_`
상속은 해석하지 않습니다.

## 기록

가드는 기본적으로 각 실행마다 secret-safe JSONL 기록을 남깁니다.

- 기본 경로: `.agent-workspace/skillopt-oauth/runs.jsonl`
- 경로 변경: `SKILLOPT_OAUTH_LOG_DIR=/path/to/dir`
- 파일 기록 끄기: `SKILLOPT_OAUTH_LOG=0`

기록에는 event type, `run_id`, 제거된 env 이름, redacted argv, provider, backend
라우팅, output root가 포함됩니다. 자격 증명 값은 기록하지 않습니다.

`SKILLOPT_OAUTH_SUPERVISE=1`을 설정하면 가드가 child를 기다리고 exit code와
duration이 포함된 `completed` 기록을 추가합니다.

## 환경 변수

| Var | Effect |
| --- | --- |
| `SKILLOPT_OAUTH_TARGET` | provider 라우팅 고정: `claude`, `codex`, `pi` |
| `SKILLOPT_OAUTH_OPTIMIZER` | 주입할 optimizer backend. `off`, `none`, empty는 주입 비활성화 |
| `SKILLOPT_OAUTH_DRY_RUN=1` | exec 없이 preflight, scrub, launch 출력 |
| `SKILLOPT_OAUTH_SUPERVISE=1` | child를 기다리고 completion 기록 |
| `SKILLOPT_OAUTH_LOG_DIR` | 기록 디렉터리 |
| `SKILLOPT_OAUTH_LOG=0` | 기록 파일 쓰기 비활성화 |
| `SKILLOPT_OAUTH_LOG_LEVEL` | stderr 로그 레벨 |
| `SKILLOPT_OAUTH_INJECT_OUT_ROOT=1` | `--out_root`가 없을 때 기록 디렉터리 아래에 자동 주입 |
| `SKILLOPT_OAUTH_RUN_ID` | correlation을 위해 child에 export |
| `PI_ALLOW_METERED` | 이 실행에서 허용할 metered `pi` provider 목록 |

## 데모

- [`demo/searchqa_codex/`](demo/searchqa_codex/): `codex_exec` target과
  `codex_chat` optimizer
- [`demo/searchqa_pi/`](demo/searchqa_pi/): `zai/glm-5.2`로 라우팅되는
  `pi_exec` target과 `pi_chat` optimizer

두 데모는 선별된 trace artifact를 `trace/` 아래에 보관합니다. raw `outputs/`
디렉터리는 gitignore 처리되어 있습니다.
