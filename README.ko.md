# 공유 Dotfiles & 설정

프로젝트 간 재사용을 위한 범용 dotfile, 설정, Claude Code 스킬 모음입니다.

[English](README.md)

## 스킬

`.claude/skills/`에 위치하며, Claude Code의 기능을 확장합니다:

### interview

대화형 인터뷰를 통한 구조화된 요구사항 발굴 도구입니다.

```
/interview <topic> [--ref <path>] [--workspace <dir>]
```

- 가이드 방식의 Q&A를 통해 요구사항, 제약조건, 설계 결정을 도출
- 기존 산출물을 기반으로 논의를 진행할 수 있는 참조 파일 지원
- 타임스탬프가 포함된 종합 문서를 워크스페이스에 생성

### phaser

Phaser 3 게임 개발을 위한 검증된 패턴과 모범 사례 모음입니다.

패시브 지식 베이스 — Phaser 코드 작성 시 자동으로 참조됩니다.

- 멀티 씬 흐름, 오브젝트 풀링, 물리 엔진 패턴
- 성능 최적화 및 자주 발생하는 실수 방지
- 게임 프로젝트를 위한 아키텍처 가이드

### report-writer

표준화된 섹션 구조를 갖춘 기술 분석 및 디버깅 리포트 생성 도구입니다.

```
/report-writer [topic] [--workspace <dir>]
```

- 타임스탬프 기반 리포트 생성 (디버깅, 분석, 구현)
- 표준 섹션: 요약, 주요 발견사항, 근본 원인 분석, 권장사항
- 코드 참조가 포함된 근거 기반 문서화

### rigorous-debug

과학적 방법론에 기반한 체계적 디버깅 프로토콜입니다.

```
/rigorous-debug
```

- 최초 사용 전 프로젝트별 일회성 초기화 필요
- 가설 → 실험 → 결론의 순환 구조 적용
- 구조화된 근거 수집으로 가정 기반 디버깅 방지

### skill-writer

효과적인 Claude Code 스킬 작성을 위한 도구입니다.

```
/skill-writer
```

- 패턴 식별부터 완성된 SKILL.md까지 단계별 워크플로우
- 프론트매터, 명령어 구조, 모범 사례 안내
- 재사용 가능한 패턴을 공유 가능한 스킬로 추출

### spec-workflow

기획과 구현을 분리하는 2단계 명세 및 구현 워크플로우입니다.

```
/spec-workflow <write|write-phased|implement> [args...] [--workspace <dir>]
```

- **write**: 명세를 작성하고 커밋한 뒤 중단 — 구현하지 않음
- **write-phased**: 복잡한 기능을 위한 다단계 명세 작성
- **implement**: 기존 명세를 따라 구현하고 상태를 업데이트한 뒤 커밋

## 커맨드 별칭

| 별칭 | 확장 |
|------|------|
| `/write-spec` | `/spec-workflow write` |
| `/write-spec-phased` | `/spec-workflow write-phased` |
| `/implement-spec` | `/spec-workflow implement` |

## 워크스페이스 설정

파일을 생성하는 스킬(interview, spec-workflow, report-writer)은 계층적 우선순위를 가진 워크스페이스 디렉터리 설정을 지원합니다:

1. **프로젝트 설정** (`.claude/skill-configs/<skill>/config.yaml`)
2. **사용자 설정** (`~/.claude/skills/<skill>/config.yaml`)
3. **CLI 플래그** (`--workspace <dir>`)

기본값은 `agent-workspace/<folder>` 규칙을 따릅니다 (`specs`, `reports`, `interviews`).

## 설치

```bash
# 원하는 위치에 클론
git clone <repo-url> ~/shared

# 프로젝트에 .claude 디렉터리 심볼릭 링크
ln -s ~/shared/.claude /path/to/project/.claude

# 또는 특정 스킬만 복사
cp -r ~/shared/.claude/skills/spec-workflow /path/to/project/.claude/skills/
```

## 라이선스

개인 사용 — 필요에 따라 자유롭게 수정하여 사용하세요.
