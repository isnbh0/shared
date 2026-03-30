# 공유 Dotfiles & 설정

프로젝트 간 재사용을 위한 범용 dotfile, 설정, Claude Code 스킬 모음입니다.

[English](README.md)

## 설치

### 옵션 A: 플러그인 (권장)

먼저 마켓플레이스를 등록합니다:

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
```

### 옵션 B: 심볼릭 링크 / 복사

```bash
# 원하는 위치에 클론
git clone <repo-url> ~/shared

# 프로젝트에 .claude 디렉터리 심볼릭 링크
ln -s ~/shared/.claude /path/to/project/.claude

# 또는 특정 스킬만 복사
cp -r ~/shared/plugins/spex/skills/spex /path/to/project/.claude/skills/
```

## 스킬

### 게시됨 (마켓플레이스)

`/plugin install <name>@isnbh0`으로 설치 가능:

#### critique

CLI 도구(Codex, Gemini)를 통한 외부 AI 코드 리뷰 도구입니다.

```
/critique:codex [file-path] [focus]
/critique:gemini [file-path] [focus]
```

- 명세, 코드, 최근 변경사항에 대한 독립적인 세컨드 오피니언 제공
- **Codex 백엔드:** 읽기 전용 샌드박스, 추론 노력 수준 지원 (기본, high, xhigh)
- **Gemini 백엔드:** 쓰기 및 네트워크 제한이 적용된 샌드박스

#### interview

대화형 인터뷰를 통한 구조화된 요구사항 발굴 도구입니다.

```
/interview <topic> [--ref <path>] [--workspace <dir>]
```

- 가이드 방식의 Q&A를 통해 요구사항, 제약조건, 설계 결정을 도출
- 기존 산출물을 기반으로 논의를 진행할 수 있는 참조 파일 지원
- 타임스탬프가 포함된 종합 문서를 워크스페이스에 생성

#### study

URL 또는 로컬 파일을 기반으로 한 소크라테스식 학습 세션 도구입니다.

```
/study <uri>
```

- 사용자의 친숙도에 맞게 세션 방식 조정 (전체 학습, 가이드 학습, 갭 체크)
- 세션 노트를 마크다운 파일로 저장하며 이어서 진행 가능
- 세션 저장 디렉터리 및 페르소나/동작 커스터마이징을 위한 자유형 `instructions` 설정 지원

#### spex

기획과 구현을 분리하는 2단계 명세 및 구현 워크플로우입니다.

독립적인 3개의 스킬:

- `/spex:write` — 명세를 작성하고 커밋한 뒤 중단 — 구현하지 않음
- `/spex:write-phased` — 복잡한 기능을 위한 다단계 명세 작성
- `/spex:implement` — 기존 명세를 따라 구현하고 상태를 업데이트한 뒤 커밋

#### macros

서브에이전트 오케스트레이션 워크플로우: map-reduce 및 리서치 기반 코드 비평.

```
/macros:mapreduce <task> [--workspace <dir>]
/macros:doubt [count | --seq N | "freeform question"]
```

- **mapreduce** — 작업을 독립적인 청크로 분할, 병렬 서브에이전트 배포, 결과 통합
- **doubt** — 블라인드 서브에이전트가 코드를 읽고, 웹 소스를 통해 가정을 검증하며, 수정을 적용. 병렬 모드로 독립적 커버리지 확보; 순차 모드에서는 패스 간 자동 수정 적용 및 커밋

### 기타 (복사 / 심볼릭 링크)

저장소에 포함되어 있지만 마켓플레이스에는 게시되지 않은 스킬입니다. 심볼릭 링크 또는 복사로 설치:

```bash
cp -r ~/shared/plugins/<name>/skills/<skill> /path/to/project/.claude/skills/
```

#### phaser

Phaser 3 게임 개발을 위한 검증된 패턴과 모범 사례 모음입니다.

패시브 지식 베이스 — Phaser 코드 작성 시 자동으로 참조됩니다.

- 멀티 씬 흐름, 오브젝트 풀링, 물리 엔진 패턴
- 성능 최적화 및 자주 발생하는 실수 방지
- 게임 프로젝트를 위한 아키텍처 가이드

#### report-writer

표준화된 섹션 구조를 갖춘 기술 분석 및 디버깅 리포트 생성 도구입니다.

```
/report-writer [topic] [--workspace <dir>]
```

- 타임스탬프 기반 리포트 생성 (디버깅, 분석, 구현)
- 표준 섹션: 요약, 주요 발견사항, 근본 원인 분석, 권장사항
- 코드 참조가 포함된 근거 기반 문서화

#### rigorous-debug

과학적 방법론에 기반한 체계적 디버깅 프로토콜입니다.

```
/rigorous-debug
```

- 최초 사용 전 프로젝트별 일회성 초기화 필요
- 가설 → 실험 → 결론의 순환 구조 적용
- 구조화된 근거 수집으로 가정 기반 디버깅 방지

#### skill-writer

효과적인 Claude Code 스킬 작성을 위한 도구입니다.

```
/skill-writer
```

- 패턴 식별부터 완성된 SKILL.md까지 단계별 워크플로우
- 프론트매터, 명령어 구조, 모범 사례 안내
- 재사용 가능한 패턴을 공유 가능한 스킬로 추출

## 워크스페이스 설정

파일을 생성하는 스킬(interview, spex, report-writer, macros, study)은 계층적 우선순위를 가진 워크스페이스 디렉터리 설정을 지원합니다 (먼저 발견된 항목 우선):

1. **CLI 플래그** (`--workspace <dir>`) — 일회성 오버라이드
2. **로컬 설정** (`.claude/skill-configs/<skill>/config.local.yaml`) — gitignore 대상, 개인 오버라이드
3. **프로젝트 설정** (`.claude/skill-configs/<skill>/config.yaml`) — 커밋 대상, 팀 공유

기본값은 없습니다. 각 스킬은 첫 사용 시 설정을 안내합니다. 출력은 `.agent-workspace/<folder>` 규칙을 따릅니다 (`specs`, `reports`, `interviews`, `macros`).

## 다른 에이전트 도구

이 스킬들은 여러 AI 코딩 도구에서 지원되는 SKILL.md 형식을 사용합니다. 설치 방법은 [크로스 플랫폼 가이드](docs/cross-platform/README.md)를 참조하세요:

- [Codex CLI](docs/cross-platform/codex-cli.md) (OpenAI)
- [Gemini CLI](docs/cross-platform/gemini-cli.md) (Google)
- [Antigravity](docs/cross-platform/antigravity.md) (Google)
- [Amp](docs/cross-platform/amp.md) (Sourcegraph)
- [Cursor](docs/cross-platform/cursor.md)

## 라이선스

개인 사용 — 필요에 따라 자유롭게 수정하여 사용하세요.
