# 공유 Dotfiles & Agent Skills

프로젝트 간 재사용할 수 있는 dotfile, 설정, 휴대 가능한 `SKILL.md` 에이전트 스킬 모음입니다.

[English](README.md)

## 설치

재사용 가능한 원본은 `plugins/<plugin>/skills/<skill>/` 아래의 각 스킬 디렉터리입니다. `SKILL.md`와 필요한 보조 파일을 포함한 디렉터리 전체가 하나의 휴대 가능한 스킬입니다.

### 옵션 A: 스킬 복사 / 심볼릭 링크

`SKILL.md` 스킬을 직접 읽는 에이전트에서 사용합니다. 대상 에이전트의 현재 스킬 루트는 해당 도구의 공식 문서 또는 [docs/cross-platform/README.md](docs/cross-platform/README.md)의 호환성 SSOT에서 확인하세요.

```bash
# 원하는 위치에 클론
git clone <repo-url> ~/shared

# SKILL.md 파일만이 아니라 스킬 디렉터리 전체를 복사
mkdir -p <skill-root>
cp -R ~/shared/plugins/interview/skills/interview <skill-root>/
```

자동 업데이트를 원하면 복사 대신 스킬 디렉터리를 심볼릭 링크하세요.

### 옵션 B: Claude Code 마켓플레이스

일부 스킬은 Claude Code 마켓플레이스 플러그인으로도 패키징되어 있습니다. 먼저 마켓플레이스를 등록합니다:

```bash
/plugin marketplace add isnbh0/shared
```

그런 다음 개별 스킬을 설치합니다:

```bash
/plugin install interview@isnbh0
/plugin install spex@isnbh0
/plugin install critique@isnbh0
/plugin install macros@isnbh0
/plugin install study@isnbh0
/plugin install gimme@isnbh0
/plugin install promptopt@isnbh0
/plugin install zoomdoc@isnbh0
```

## 스킬

아래 스킬 참조는 저장소 표기법을 사용합니다. 번들 스킬은 `skill(plugin:name)`, 독립 스킬은 `skill(name)`으로 씁니다. 이는 식별자이지 실제 명령이 아닙니다. 플러그인 설치에서는 Claude Code가 `/plugin:name`, Codex가 `$plugin:name`으로 활성화하며, 다른 호스트는 각 도구가 문서화한 방식을 사용합니다. 직접 설치한 스킬은 보통 플러그인 네임스페이스 없이 설치 디렉터리 이름으로 노출됩니다.

### 게시됨 (마켓플레이스)

Claude Code에서 `/plugin install <name>@isnbh0`으로 설치 가능:

#### critique

CLI 도구(Codex, Gemini)를 통한 외부 AI 코드 리뷰 도구입니다.

```
skill(critique:codex) [file-path] [focus]
skill(critique:gemini) [file-path] [focus]
```

- 명세, 코드, 최근 변경사항에 대한 독립적인 세컨드 오피니언 제공
- **Codex 백엔드:** 설정된 Codex CLI 리뷰 실행
- **Gemini 백엔드:** 설정된 Gemini CLI 리뷰 실행

#### interview

대화형 인터뷰를 통한 구조화된 요구사항 발굴 도구입니다.

**Claude Code에서 설치 없이 바로 사용:**

```bash
claude --plugin-url https://github.com/isnbh0/shared/releases/download/interview-latest/interview.zip
```

마음에 드신다면, 위의 마켓플레이스 명령어로 설치하세요.

```
skill(interview:interview) <topic> [--ref <path>]
```

- 가이드 방식의 Q&A를 통해 요구사항, 제약조건, 설계 결정을 도출
- 기존 산출물을 기반으로 논의를 진행할 수 있는 참조 파일 지원
- 타임스탬프가 포함된 종합 문서를 워크스페이스에 생성

#### study

URL 또는 로컬 파일을 기반으로 한 소크라테스식 학습 세션 도구입니다.

```
skill(study:study) <uri>
```

- 사용자의 친숙도에 맞게 세션 방식 조정 (전체 학습, 가이드 학습, 갭 체크)
- 세션 노트를 마크다운 파일로 저장하며 이어서 진행 가능
- 세션 저장 디렉터리 및 페르소나/동작 커스터마이징을 위한 자유형 `instructions` 설정 지원

#### spex

기획과 구현을 분리하는 2단계 명세 및 구현 워크플로우입니다.

독립적인 3개의 스킬:

- `skill(spex:write)` — 명세를 작성하고 커밋한 뒤 중단 — 구현하지 않음
- `skill(spex:write-phased)` — 복잡한 기능을 위한 다단계 명세 작성
- `skill(spex:implement)` — 기존 명세를 따라 구현하고 상태를 업데이트한 뒤 커밋

#### macros

서브에이전트 오케스트레이션 워크플로우 및 세션 모드: map-reduce, 순서 있는 분할 실행, 리서치 기반 코드 비평, 합의 리뷰, 순차 패스, 리고 모드.

```
skill(macros:mapreduce) <task>
skill(macros:chunked) <task>
skill(macros:doubt) ["freeform question"]
skill(macros:consensus) <count>
skill(macros:seq) <count>
skill(macros:rigor)
skill(macros:orchestrate)
skill(macros:askme)
skill(macros:delegate)
skill(macros:tmi)
skill(macros:dry-run)
skill(macros:timeless)
skill(macros:dredge) ["freeform query"]
skill(macros:timestamp)
skill(macros:new)
```

- **mapreduce** — 작업을 독립적인 청크로 분할, 병렬 서브에이전트 배포, 결과 통합
- **chunked** — 작업을 전체를 덮는 순서 있는 부분들로 분할 실행; 각 반복은 이전 반복의 산출물을 읽을 수 있음
- **doubt** — 블라인드 서브에이전트가 코드를 읽고, 웹 소스를 통해 가정을 검증하며, 수정을 적용하고 심각도 순으로 문제를 보고
- **consensus** — N개의 블라인드 에이전트가 동일 작업을 병렬로 수행한 후, 합의/고유 발견/충돌로 결과를 병합 (동시성 안전을 위해 수정 없음)
- **seq** — N회 직렬 블라인드 패스를 수행하며 라운드 간 커밋; 클린 워크트리 필요
- **rigor** — 세션에 리고 모드 활성화: 정확성, 철저한 조사, 웹 기반 검증을 최소주의보다 우선시
- **orchestrate** — 세션에 오케스트레이터 모드 활성화: 실행을 기본적으로 서브에이전트에 위임하고 높은 수준에서 작업하며, 자신의 컨텍스트는 방향 설정과 종합에 사용; 사소한 작업은 인라인으로 처리하는 예외 장치 포함
- **askme** — 단축 명령: 가정하지 말고 모호한 점이나 결정 사항을 사용자에게 질문
- **delegate** — 단축 명령: 컨텍스트 공간 절약과 독립 하위 작업 병렬화를 위해 서브에이전트 우선 사용
- **tmi** — 작성 당시 맥락 없이는 이해하기 어려운 불필요한 내용을 식별; 기본적으로 리포트, 명시적 지시 시 직접 수정
- **dry-run** — 일회성 안전장치: 다음 요청을 실행하지 않고 무엇을 할지 설명한 뒤 확인을 기다림
- **timeless** — 단축 명령: 시간 추정(시·일, 달력 날짜, 시간에 매핑되는 크기 버킷) 금지; 복잡도, 구체적 범위, 리스크, 선후 관계로 설명
- **dredge** — 이전 코딩 에이전트(Claude Code, Codex, ...) 대화 기록에서 문맥을 검색; 기본은 현재 프로젝트, 쿼리의 자연어 힌트(예: "모든 프로젝트에서", "craken 저장소에서", "어제")에 따라 범위·시간 창을 자동 확장. `agentsview` CLI가 설치되어 있으면 선택적 AgentsView 백엔드를 사용(사용자 스코프 `~/.agents/skill-configs/dredge/`에서 설정); 없으면 Claude Code 기록 대상 grep으로 폴백
- **timestamp** — 단축 명령: 새로 만드는 파일/폴더 이름 앞에 `date` CLI로 생성한 `yymmdd-HHMMSS` 타임스탬프를 접두어로 붙임; 하나의 논리적 작업 묶음 당 타임스탬프 한 개; 해당 턴에만 적용
- **new** — 커스텀 매크로 스캐폴딩: 일급 매크로처럼 동작하는 사용자 스코프 또는 프로젝트 스코프 스킬을 생성(composition line을 포함해 `skill(macros:doubt)`, `skill(macros:seq)` 등과 조합 가능); 사용자 스코프 매크로는 기본적으로 `my-` 이름 접두어 사용

#### gimme

사용자 호출 전용 역방향 위임 — 에이전트에게 요청하면 사용자가 처리할 수 있는 파일시스템 번들을 만들어 돌려줍니다.

```
skill(gimme:gimme)
```

- 타임스탬프 번들을 생성: `checklist.md`, `notes.md` (붙여넣기 슬롯이 미리 라벨링된 템플릿), 파일 산출물용 빈 `dropbox/` 디렉터리
- 각 체크리스트 항목은 action / why-you / drop-path 형태로, 결과물이 에이전트가 별도 안내 없이 바로 픽업할 수 있는 위치에 떨어지도록 명시
- 선택 설정 `launch_command` (예: `cursor {path}`, `code {path}`, `open {path}`)로 번들을 에디터에서 즉시 오픈
- 모델이 자발적으로 호출하지 않음 — `skill(gimme:gimme)`를 명시적으로 활성화할 때만 실행

#### promptopt

애플리케이션 프롬프트, 프롬프트 빌더, 에이전트 지시문, 라우팅 프롬프트, LLM 워크플로우를 위한 산출물 기반 프롬프트 최적화 워크플로우입니다.

```
skill(promptopt:promptopt)
```

- 최적화 전에 사용자가 소유한 목표 동작, 출력 계약, train/val 케이스, 수용 기준을 수집
- 소스 파일을 직접 수정하지 않고 자체 실행 워크스페이스에 최적화 산출물을 기록
- baseline 출력, candidate ledger, optimizer state, decision record를 유지

#### zoomdoc

일반적인 시맨틱 구조를 보존하는 접근 가능한 단일 파일 semantic-zoom HTML 문서를 작성합니다.

**Claude Code에서 설치 없이 바로 사용:**

```bash
claude --plugin-url https://github.com/isnbh0/shared/releases/download/zoomdoc-latest/zoomdoc.zip
```

```
skill(zoomdoc:zoomdoc)
```

- 고정된 글 문서 온톨로지 대신 문서별 순서형 상세도 레벨과 선택적 편집 프로필 사용
- 중첩 섹션, 그림, 정의 목록, 표, 코드, 미디어, 각주 등 임의의 시맨틱 HTML 지원
- 네이티브 라디오·디스클로저 컨트롤과 명시적 `hidden` 상태를 사용하며, JavaScript 없이도 최상세 레벨로 온전히 읽힘
- 접근 가능한 렌더러와 검증기를 포함하고, 소스 전사 모드에서는 선택적으로 엄격한 커버리지 검사 수행

### 기타 (복사 / 심볼릭 링크)

저장소에 포함되어 있지만 마켓플레이스에는 게시되지 않은 스킬입니다. 심볼릭 링크 또는 복사로 설치:

```bash
cp -R ~/shared/plugins/<plugin>/skills/<skill> <skill-root>/
```

아래에서도 같은 표준 참조 표기법을 사용합니다. 직접 설치한 스킬은 보통 설치 디렉터리 이름으로 활성화합니다.

#### phaser

Phaser 3 게임 개발을 위한 검증된 패턴과 모범 사례 모음입니다.

패시브 지식 베이스 — Phaser 코드 작성 시 자동으로 참조됩니다.

- 멀티 씬 흐름, 오브젝트 풀링, 물리 엔진 패턴
- 성능 최적화 및 자주 발생하는 실수 방지
- 게임 프로젝트를 위한 아키텍처 가이드

#### report-writer

표준화된 섹션 구조를 갖춘 기술 분석 및 디버깅 리포트 생성 도구입니다.

```
skill(report-writer:report-writer) [topic]
```

- 타임스탬프 기반 리포트 생성 (디버깅, 분석, 구현)
- 표준 섹션: 요약, 주요 발견사항, 근본 원인 분석, 권장사항
- 코드 참조가 포함된 근거 기반 문서화

#### rigorous-debug

과학적 방법론에 기반한 체계적 디버깅 프로토콜입니다.

```
skill(rigorous-debug:rigorous-debug)
```

- 최초 사용 전 프로젝트별 일회성 초기화 필요
- 가설 → 실험 → 결론의 순환 구조 적용
- 구조화된 근거 수집으로 가정 기반 디버깅 방지

#### skill-writer

효과적인 `SKILL.md` 에이전트 스킬 작성을 위한 도구입니다.

```
skill(skill-writer:skill-writer)
```

- 패턴 식별부터 완성된 SKILL.md까지 단계별 워크플로우
- 프론트매터, 명령어 구조, 모범 사례 안내
- 재사용 가능한 패턴을 공유 가능한 스킬로 추출

## 워크스페이스 설정

파일을 생성하는 스킬(interview, spex, report-writer, macros, study, gimme, promptopt)은 계층적 우선순위를 가진 워크스페이스 디렉터리 설정을 지원합니다 (먼저 발견된 항목 우선):

1. **명시적 오버라이드** — 이번 실행에 사용할 워크스페이스 디렉터리를 요청
2. **로컬 설정** (`.agents/skill-configs/<skill>/config.local.yaml`) — gitignore 대상, 개인 오버라이드
3. **프로젝트 설정** (`.agents/skill-configs/<skill>/config.yaml`) — 커밋 대상, 팀 공유
4. **레거시 폴백** (`.claude/skill-configs/<skill>/`) — 오래된 설정 경로를 배포한 스킬에만 해당

대부분의 파일 생성 스킬에는 기본값이 없습니다. 각 스킬은 첫 사용 시 설정을 안내합니다. 출력은 `.agent-workspace/<folder>` 규칙을 따릅니다 (`specs`, `reports`, `interviews`, `macros`, `study`, `gimme`, `promptopt`).

새 설정은 `.agents/skill-configs/`를 사용하세요. `.claude/skill-configs/` 경로는 이전에 해당 경로를 사용했던 스킬의 마이그레이션 지원용으로만 유지되며, 새 스킬은 이 폴백을 추가할 필요가 없습니다. 2027-01-31 이후 레거시 폴백 제거를 검토합니다.

## 다른 에이전트 도구

이 스킬들은 Agent Skills `SKILL.md` 형식을 사용합니다. 제공자별 설치 루트와 활성화 메모는 [크로스 플랫폼 가이드](docs/cross-platform/README.md)에만 유지하고, 다른 문서에는 복사하지 마세요.

## 라이선스

개인 사용 — 필요에 따라 자유롭게 수정하여 사용하세요.
