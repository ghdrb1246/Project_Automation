# 프로젝트 관리 자동화

## 이 프로젝트는 무엇인가

팀 프로젝트를 진행하며 아래 네 가지 문제가 반복적으로 발생했습니다.

1. 일정 관리가 제대로 되지 않아 마지막 날까지 몰림
2. 산출물(문서) 간 불일치가 많아 수정 작업이 반복됨
3. Notion에 데이터를 수동 입력해야 해서 팀원들이 사용하지 않음
4. 담당자 간 소통 부족으로 서로 무슨 작업 중인지 파악이 안 됨

이 프로젝트는 위 문제를 Notion, GitHub Actions, Discord를 연동한 자동화로 해결하기 위한 설계와 구현 기록입니다.

## 어떤 방법으로 해결했는가

### 설계 원칙
- **판단이 필요한 영역(일정 수립)은 자동화하지 않는다** — WBS는 PM이 Notion에 직접 관리
- **Notion을 단일 확인 창구로 삼는다** — 계산·판단 로직은 Notion 자체 기능(Formula, Rollup, Database Automation)으로 최대한 처리
- **AI는 최후 수단으로, 최소로 사용한다** — 토큰 비용 문제로 상시 연동은 배제하고, 규칙 기반으로 못 잡는 애매한 케이스에만 선별적으로 사용

### 3단계(Tier) 구조

실제 Notion 문서 간 연결 관계(`WBS → 기능 명세서 → API 명세서`)를 활용해, 산출물 불일치를 아래 3단계로 감지합니다.

| 단계 | 역할 | 처리 위치 | AI 사용 |
|---|---|---|---|
| Tier 1 | 필수 항목 누락, 문서 간 수정 시점 어긋남 감지 | Notion 자체 기능 (Formula/Rollup/Automation) | 없음 |
| Tier 2 | API 명세서 ↔ 실제 코드 비교, 불일치 시 Discord 알림 | GitHub Actions | 없음 |
| Tier 3 | 문장 의미 수준의 불일치 (규칙으로 못 잡는 것) | Tier 1에서 걸러진 후보만 AI로 재확인 | 최소 사용 |

여기에 Discord 실시간 알림·일일 리포트, PlantUML 다이어그램 자동 렌더링을 더해 커뮤니케이션 문제까지 함께 다룹니다.

## 문서 목록

| 파일명 | 설명 |
|---|---|
| [`automation-plan.md`](./docs/automation-plan.md) | **자동화 기획서.** 왜 이렇게 설계했는지 — 문제 정의, 설계 원칙, 문제→해결책 매핑, 전체 아키텍처 개요, 리스크 |
| [`implementation-guide.md`](./docs/implementation-guide.md) | **자동화 구현 가이드.** 실제 설정 방법 — Notion Formula/Rollup 수식, GitHub Actions 워크플로우, Python 스크립트, Secrets 목록, 디렉토리 구조, 브랜치 전략 |
| [`test-checklist.md`](./docs/test-checklist.md) | **자동화 테스트 체크리스트.** 구현이 실제로 동작하는지 검증하는 순서 — Tier별 개별 테스트 + End-to-End 시나리오 |
| [`wbs-guide.md`](./docs/wbs-guide.md) | **WBS 사용 가이드.** 업무 항목을 어떻게 작성하는지, 업무 영역·상태값의 의미, 자주 헷갈리는 부분 |
| [`qa-guide.md`](./docs/qa-guide.md) | **QA 사용 가이드.** 테스트 실패 시 버그 티켓을 어떻게 작성하는지, 진행 상태 관리 |
| [`test-scenario-guide.md`](./docs/test-scenario-guide.md) | **테스트 시나리오 사용 가이드.** 테스트 케이스를 어떻게 작성하고 빠짐없이 커버하는지 |
| [`service-planning-guide.md`](./docs/service-planning-guide.md) | **서비스 기획 사용 가이드.** 핵심 기능·타겟층·문제 정의·경쟁 분석을 어떻게 작성하는지 |
| [`requirements-guide.md`](./docs/requirements-guide.md) | **요구사항 명세서 사용 가이드.** 도메인·유스케이스 단위로 시스템 요구사항을 정리하는 방법 |

## 문서 간 흐름

기획 → 구현 순서로 보면 이렇게 이어집니다.

```
service-planning-guide.md   (무엇을 만들지 정하기)
        ↓
requirements-guide.md       (도메인·유스케이스 단위로 구체화)
        ↓
wbs-guide.md                (일정·담당자 배정, 기능 명세서와 연결)
        ↓
test-scenario-guide.md ──── qa-guide.md   (테스트 케이스 작성 → 실패 시 버그 티켓)
```

자동화 자체를 다시 세팅하거나 이해하려면 `automation-plan.md` → `implementation-guide.md` → `test-checklist.md` 순으로 읽으세요.

## 시작하기

처음 프로젝트에 합류했다면:
1. `automation-plan.md`를 읽고 전체 그림을 파악하세요
2. `implementation-guide.md`의 "0. 사전 준비 체크리스트"를 따라 Notion Integration·GitHub Secrets를 세팅하세요
3. 문서 작성이 필요할 때마다 해당 `*-guide.md`를 참고하세요

운영 — 스케줄 자동화 켜고 끄기

daily-discord-report.yml, flag-notify.yml은 평일마다 자동으로 도는데, 방학이나 프로젝트 소강기간처럼 잠시 멈추고 싶을 때는 파일을 지우거나 코드를 건드릴 필요 없이 GitHub CLI로 껐다 켤 수 있습니다.

bash
# 끄기
gh workflow disable "Daily Discord Report"
gh workflow disable "Notify Inconsistency Flags"

# 다시 켜기
gh workflow enable "Daily Discord Report"
gh workflow enable "Notify Inconsistency Flags"

# 현재 활성/비활성 상태 확인
gh workflow list
저장소 관리자/쓰기 권한이 있어야 실행할 수 있습니다.
disable 상태에서는 스케줄뿐 아니라 수동 실행(workflow_dispatch)도 함께 막힙니다.
참고로 90일 넘게 저장소에 커밋이 없으면 GitHub가 스케줄 워크플로우를 자동으로 비활성화하기도 하니, 방학이 길어지면 이것도 염두에 두세요.
