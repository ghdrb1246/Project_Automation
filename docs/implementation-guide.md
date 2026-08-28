# 프로젝트 관리 자동화 구현 가이드

기획 배경과 설계 원칙은 `automation-plan.md` 참고. 이 문서는 실제로 무엇을, 어떤 순서로, 어떻게 설정하는지만 다룹니다.

---

## 0. 사전 준비 체크리스트

아래 0-1부터 0-8까지 순서대로 진행하면 이후 Tier 1/2/3을 바로 붙일 수 있는 상태가 됩니다. 한 번만 하면 되는 세팅입니다.

### 0-1. WBS DB에 Task ID 속성 추가

1. WBS 데이터베이스 열기 → 우측 상단 `+` (새 속성)
2. 속성 이름 `Task ID` 입력, 타입 검색창에서 `ID` 선택 (일반 `Text`가 아님에 주의)
3. 방금 만든 속성 클릭 → `Edit property` → `Prefix` 칸에 `WBS` 입력
4. 저장하면 기존 12개 항목에 `WBS-1`~`WBS-12`가 자동으로 채번됨 (읽기 전용, 수동 입력 불필요)

> 이미 `Text` 타입으로 `Task ID`를 만들어두셨다면 그 속성은 삭제하고 위 방식으로 다시 만드세요. 두 속성이 이름만 같고 타입이 다르면 이후 스크립트가 값을 못 찾습니다.

### 0-2. Notion Integration 생성 및 토큰 발급

1. [notion.so/my-integrations](https://www.notion.so/my-integrations) 접속 (Notion에 로그인된 상태여야 함)
2. `+ New integration` 클릭
3. 이름 입력 (예: `project-automation-bot`), 연결할 워크스페이스 선택
4. `Capabilities` 탭에서 최소 `Read content`, `Update content`, `Insert content` 체크 (코멘트 자동 등록까지 쓸 거면 `Comment` 관련 권한도 체크)
5. 저장 후 `Internal Integration Secret` 값을 복사 — 이게 `NOTION_TOKEN` 입니다. **한 번만 보여지므로 바로 안전한 곳에 저장**

### 0-3. 사용할 데이터베이스 ID + 데이터 소스 ID 확보 (3개 DB)

WBS, API 명세서, 기능 명세서 — 각 DB를 **전체 화면(Full page)** 으로 연 상태에서 브라우저 주소창 URL을 확인합니다.

```
https://www.notion.so/워크스페이스이름/1a2b3c4d5e6f...?v=...
                                    └──────┬──────┘
                                     이 32자리 문자열이 DB ID
```
`?v=` 앞에 있는 32자리(하이픈 없는) 문자열을 각각 복사해두세요.
- WBS DB ID → 나중에 `NOTION_WBS_DB_ID`
- API 명세서(APISpec) DB ID → 나중에 `NOTION_APISPEC_DB_ID`
- 기능 명세서(functionalSpecification) DB ID → 나중에 `NOTION_FUNCSPEC_DB_ID`

> **중요 (2025-09-03 이후 Notion API 변경사항)**: Notion이 "데이터베이스"와 "데이터 소스"를 분리했습니다. 데이터베이스는 컨테이너이고, 실제 조회 대상(속성/행)은 그 안의 **데이터 소스**입니다. 최근 만들어진 데이터베이스는 예전 방식(`/v1/databases/{id}/query`)이 막혀 있고, **데이터 소스 ID**로 `/v1/data_sources/{id}/query`를 호출해야 합니다. 아래에서 세 DB의 데이터 소스 ID도 함께 확보하세요.

**데이터 소스 ID 확보 방법**
1. DB를 전체 화면으로 열기 → 우측 상단 `···` → `Manage Data Sources`(데이터 소스 관리)
2. 데이터 소스 옆 `···` → `Copy data source ID`(데이터 소스 ID 복사)
3. 세 DB 각각에 대해 복사:
   - WBS → 나중에 `NOTION_WBS_DS_ID`
   - API 명세서 → 나중에 `NOTION_APISPEC_DS_ID`
   - 기능 명세서 → 나중에 `NOTION_FUNCSPEC_DS_ID`

> DB ID(`NOTION_*_DB_ID`)는 Notion 링크 공유·URL 확인용으로 계속 필요하고, 데이터 소스 ID(`NOTION_*_DS_ID`)는 스크립트가 실제로 데이터를 조회할 때 씁니다. 둘 다 등록해두세요.

### 0-4. Integration을 각 DB에 연결 (연결 안 하면 API가 데이터를 못 봄)

WBS / API 명세서 / 기능 명세서 DB **각각**에서:
1. 오른쪽 상단 `···` 메뉴 클릭
2. `Connections`(연결) → `Add connections`
3. 0-2에서 만든 Integration 검색해서 선택

세 DB 모두 빠짐없이 연결해야 합니다. 하나라도 빠지면 그 DB만 API 조회 시 빈 결과가 나옵니다.

### 0-5. GitHub Secrets 등록

레포 → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`. 아래 목록을 그대로 등록하세요 (뒤에 나오는 워크플로우 파일들이 이 이름을 그대로 참조합니다).

| Secret 이름 | 값 | 어디서 얻나 |
|---|---|---|
| `NOTION_TOKEN` | Integration Secret | 0-2 |
| `NOTION_WBS_DB_ID` | WBS DB ID | 0-3 |
| `NOTION_APISPEC_DB_ID` | API 명세서 DB ID | 0-3 |
| `NOTION_FUNCSPEC_DB_ID` | 기능 명세서 DB ID | 0-3 |
| `NOTION_WBS_DS_ID` | WBS 데이터 소스 ID | 0-3 |
| `NOTION_APISPEC_DS_ID` | API 명세서 데이터 소스 ID | 0-3 |
| `NOTION_FUNCSPEC_DS_ID` | 기능 명세서 데이터 소스 ID | 0-3 |
| `DISCORD_WEBHOOK_URL` | Discord 웹훅 URL | 0-6 |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | 0-7 (Tier 3 쓸 경우에만) |

### 0-6. Discord 웹훅 생성

1. 알림 받을 Discord 채널 → 채널 설정(톱니바퀴) → `연동`(Integrations)
2. `웹후크`(Webhooks) → `새 웹후크 만들기`
3. 이름 지정(예: `프로젝트 봇`), 채널 확인 후 `웹후크 URL 복사`
4. 이 URL을 0-5의 `DISCORD_WEBHOOK_URL`로 등록

실시간 PR/커밋 알림까지 원하면, 같은 `연동` 화면에서 **GitHub 앱 연동**도 별도로 추가하세요 (코드 없이 채널-레포 연결만 하면 됨, 구현가이드 §3-1 참고).

### 0-7. (선택) Tier 3용 Anthropic API 키 발급

AI 최소 검증(구현가이드 §5)까지 쓸 계획이면:
1. [console.anthropic.com](https://console.anthropic.com) 접속 → API Keys 메뉴
2. 새 키 생성 → 0-5의 `ANTHROPIC_API_KEY`로 등록
3. 사용량 알림/한도(Usage limit)를 낮게 설정해두면 예상치 못한 비용 발생을 막을 수 있음

지금 당장 안 쓸 거면 이 단계는 건너뛰고 나중에 Tier 3를 붙일 때 진행해도 됩니다.

### 0-8. Notion 워크스페이스 플랜 확인

Database Automation의 `담당자에게 알림 보내기` 액션은 유료 플랜(팀/비즈니스)에서 제공됩니다. 워크스페이스 설정 → `Settings & members` → `Plans`에서 현재 플랜을 확인하세요. 무료 플랜이면 §1-3의 자동 알림 대신, §3의 Discord 일일 리포트로 대체하시면 됩니다.

### 0-9. 팀 브랜치 전략 공지

```
main    — 배포 기준 브랜치. 직접 push 금지.
develop — 작업 통합 브랜치. 작업 브랜치는 여기서 만들고, PR도 여기로 병합.

작업 브랜치: <타입>/<범위>-<내용>-<TaskID>
  타입: feat / fix / refactor / docs / chore
  범위: fe / be / db / deploy / docs
  TaskID: WBS 항목 번호를 소문자로 붙여 씀 (예: wbs13) — 하이픈 없이 붙여서 한 덩어리로 식별되게 함

예: feat/be-bookmark-wbs13, fix/fe-marker-duplicate-wbs21, docs/docs-guide-update-wbs5
```

> **TaskID는 선택 사항이지만, 붙이면 어떤 WBS 항목과 연결된 작업인지 브랜치명만 보고도 바로 알 수 있어 추천드립니다.** 현재 자동화 스크립트 중 브랜치명에서 Task ID를 파싱해서 쓰는 곳은 없으므로(WBS 자동 동기화는 수동 관리로 확정됨), 붙이든 안 붙이든 자동화에는 영향이 없습니다 — 순수하게 사람이 보기 위한 표기입니다.

> **주의 — 스케줄 자동화 3개는 `main`(Default branch) 기준으로만 실행됩니다.** `flag-notify.yml`, `daily-discord-report.yml`, `ai-semantic-check.yml`은 cron 트리거라서, `develop`에 아무리 최신 상태로 있어도 스케줄 실행 자체는 **Default branch(`main`)에 있는 버전**으로 돕니다. `main`이 배포 시점에만 갱신되는 구조라면, 이 세 워크플로우/스크립트를 고칠 때마다 `develop`에서 검증 후 **별도로 `main`까지 반영(릴리스 PR 등)**해야 실제 스케줄에 적용됩니다. 반면 `api-spec-check.yml`, `render-uml.yml`은 push 트리거라 `develop`이나 작업 브랜치에서 바로바로 정상 동작합니다.

팀 채널에 이 규칙을 공지하고, 가능하면 README나 CONTRIBUTING 문서에도 남겨두세요.

---

## 1. Tier 1 — Notion 자체 기능 (클릭만으로 설정, 코드 불필요)

### 1-1. 필수 항목 누락 체크

**API 명세서(APISpec) DB** → Formula 속성 `완성도 체크` 추가:
```
if(
  or(empty(prop("URI")), empty(prop("메서드")), empty(prop("기능명"))),
  "⚠️ 누락",
  "완료"
)
```

**기능 명세서(functionalSpecification) DB** → Formula 속성 `완성도 체크` 추가:
```
if(
  or(empty(prop("기능 설명")), empty(prop("시작 상태")), empty(prop("종료 상태")), empty(prop("API"))),
  "⚠️ 누락",
  "완료"
)
```

### 1-2. 문서 간 수정 시점 어긋남 체크

**실제 연결 구조**
```
WBS  ──(연결 문서, 새로 만들어야 함)──▶  기능 명세서  ◀──(API ↔ 기능명)──▶  API 명세서
```
`기능 명세서`의 `API` 속성과 `API 명세서`의 `기능명` 속성은 서로 다른 두 개의 관계가 아니라, **Notion Relation 속성 하나를 양쪽 DB에서 보여주는 것**입니다(Relation을 만들면 상대 DB에 자동으로 짝이 되는 속성이 생기고, 이 템플릿은 그 이름을 `기능명`으로 바꿔둔 것). 반면 `WBS → 기능 명세서` 구간은 원래 이 템플릿에 없던 연결이라, 아래에서 새로 만듭니다.

**사전 준비 — `최종 편집 일시` 속성 추가**
API 명세서 DB와 기능 명세서 DB 둘 다 기본적으로 `최종 편집 일시` 속성이 없습니다 (Notion 데이터베이스는 이 속성을 자동으로 넣어주지 않고, 직접 추가해야 합니다). 아래 두 DB에 각각 추가하세요.

- **API 명세서(APISpec) DB**: `+ 새 속성` → 타입 검색 `Last edited time`(최종 편집 일시) 선택 → 이름은 기본값 `최종 편집 일시` 그대로 사용
- **기능 명세서(functionalSpecification) DB**: 동일하게 `+ 새 속성` → `Last edited time` 추가

이 속성이 API 명세서 DB에 없으면 아래 Rollup의 `대상 속성` 목록에 `최종 편집 일시`가 아예 뜨지 않고, 기능 명세서 DB에 없으면 Formula에서 `prop("최종 편집 일시")`가 "유효한 속성이 아닙니다" 오류를 냅니다.

**Rollup 속성 추가**
기능 명세서 DB에 **Rollup 속성** `API 최종수정` 추가:
- Relation: `API`
- 대상 속성: `최종 편집 일시` (API 명세서 DB에 방금 추가한 속성)
- 계산: `가장 최근 날짜`

이어서 **Formula 속성** `동기화 여부` 추가 (여기서 쓰이는 `최종 편집 일시`는 기능 명세서 DB 자신의 속성입니다):
```
if(
  prop("최종 편집 일시") < prop("API 최종수정"),
  "⚠️ API가 더 최근에 수정됨 — 확인 필요",
  "동기화됨"
)
```

**WBS ↔ 기능 명세서 확장**

> **정정**: 실제 export를 확인해보니 WBS의 `관련 항목`은 기능 명세서가 아니라 **WBS DB 내 다른 업무 항목**(자기 자신 DB 내 관계, 예: 관련된 다른 태스크)과 연결되는 속성이었습니다. 기능 명세서와는 애초에 연결되어 있지 않으므로, 아래처럼 **새 Relation 속성을 하나 추가**해서 연결부터 만들어야 합니다.

1. WBS DB에 `+ 새 속성` → 타입 `Relation` 선택 → 연결 대상 DB로 `기능 명세서(functionalSpecification)` 선택, 속성 이름은 `연결 문서`(기존 `관련 항목`과 헷갈리지 않게 새 이름 사용)
2. 각 WBS 업무 항목을 열어서, 해당하는 기능 명세서 페이지를 `연결 문서`에 하나씩 연결 (이 부분은 수동 작업입니다 — 관계 자체를 자동으로 채울 방법은 없음)

연결이 끝나면 Rollup을 두 개 만듭니다. 먼저 WBS DB에 **Rollup 속성** `관련 문서 최종수정` 추가:
- Relation: `연결 문서` (방금 새로 만든 속성)
- 대상 속성: `최종 편집 일시` (기능 명세서 DB의 속성 — 위 사전 준비에서 추가한 것)
- 계산: `가장 최근 날짜`

> **주의 — 타임스탬프 비교만으로는 부족합니다.** API 명세서만 수정하면 기능 명세서의 `동기화 여부`는 재계산되지만, 기능 명세서 페이지 자체의 `최종 편집 일시`는 바뀌지 않습니다(Notion은 관계된 페이지가 변해서 Formula/Rollup 값만 재계산된 것을 "편집"으로 치지 않습니다). 그래서 위 Rollup만으로는 API 명세서 변경이 WBS까지 전파되지 않습니다. 이를 해결하려면 기능 명세서의 **`동기화 여부` 값 자체**도 함께 가져와야 합니다 — Formula 값은 사람이 편집하지 않아도 관계된 데이터가 바뀌면 항상 즉시 재계산되기 때문입니다.

이어서 WBS DB에 **Rollup 속성** `기능명세서 동기화 상태` 추가:
- Relation: `연결 문서`
- 대상 속성: `동기화 여부` (기능 명세서 DB의 Formula 속성)
- 계산: `가장 최근 값 표시`(Show original 계열 — `연결 문서`가 1:1 연결이므로 값이 그대로 나옵니다)

이어서 WBS DB에 **Formula 속성** `동기화 여부` 추가. (기존에 `동기화 필요`로 만들어두셨다면 속성 이름만 `동기화 여부`로 바꾸시면 됩니다 — 기능 명세서 DB와 명칭을 통일하기 위함입니다.) `연결 문서`가 비어있는 태스크도 있을 수 있으므로(예: 미팅·개인 일정처럼 문서와 상관없는 업무 영역), 비어있을 때는 에러 대신 `-`로 표시하도록 처리합니다:
```
if(
  empty(prop("관련 문서 최종수정")),
  "-",
  if(
    or(
      contains(prop("기능명세서 동기화 상태"), "⚠️"),
      prop("최종 편집 일시") < prop("관련 문서 최종수정")
    ),
    "⚠️ 관련 문서가 더 최근에 수정됨 — 확인 필요",
    "동기화됨"
  )
)
```

`기능명세서 동기화 상태`(기능 명세서의 실시간 상태를 그대로 반영) 조건을 추가함으로써, API 명세서만 바뀌어서 기능 명세서의 `최종 편집 일시`는 그대로여도, 기능 명세서의 `동기화 여부`가 `⚠️`로 바뀌는 순간 WBS도 즉시 함께 `⚠️`로 반응합니다.

이렇게 하면 `WBS → 기능 명세서 → API 명세서` 전 구간에서, 뒤쪽(API 명세서)이 수정됐는데 앞쪽(기능 명세서, WBS)이 그대로면 각 단계에서 바로 잡아냅니다.

**`연결 문서`가 비어있는 게 정상인 항목들**
WBS에는 기능 구현 외의 업무 항목(`업무 영역`이 `미팅`, `개인 일정`, `백로그`, `Ops`인 것들)도 섞여 있습니다. 이런 항목은 애초에 대응되는 기능 명세서가 없으므로 `연결 문서`를 채우지 않아도 됩니다 — Formula가 `empty()`로 걸러서 `-`로 표시하고 경고를 띄우지 않습니다. `연결 문서`를 채워야 하는 대상은 실질적으로 `업무 영역`이 `BE`/`FE`인, 즉 기능 구현과 직접 연결된 항목들입니다.

### 1-3. 신규 항목 추가 감지 (Database Automation, 노션 자체 기능)

> **주의**: `동기화 여부`, `완성도 체크`는 Formula 속성입니다. Notion Database Automation은 **Formula/Rollup/생성·수정 일시 같은 자동 계산 속성의 변경을 트리거로 감지할 수 없습니다** (사람이 직접 편집하는 값이 아니라 다른 값에 따라 재계산되는 값이라 "편집됨" 이벤트 자체가 발생하지 않음). 그래서 "(A) 불일치 알림"은 Notion 자동화가 아니라 §2-2의 GitHub Actions 스크립트로 처리합니다. 아래 (B)는 `새 페이지 생성`이 트리거라 Formula와 무관하므로 그대로 Notion 자동화로 만들 수 있습니다.

| 자동화 | 적용 DB | 트리거 | 동작 |
|---|---|---|---|
| 신규 항목 추가 감지 | API 명세서 DB | `새 페이지가 생성될 때` | 관련 담당자(BE)에게 알림 → "새 API가 추가됨, 기능 명세서 반영 확인" |
| 신규 항목 추가 감지 | 기능 명세서 DB | `새 페이지가 생성될 때` | 관련 담당자(FE/QA)에게 알림 → "새 기능 명세가 추가됨, 확인 필요" |

각 DB 우측 상단 ⚡ 아이콘 → 자동화 생성에서 위 표대로 만들면 됩니다. 유료 플랜이 아니라 `알림 보내기` 액션을 쓸 수 없다면, 이 부분도 §2-2 스크립트에 신규 페이지 감지를 포함시켜 대체할 수 있습니다.

**여기까지(1-1, 1-2, 1-3)는 Notion 안에서 클릭만으로 끝납니다. 다만 실제 "담당자에게 알림"까지 자동으로 가려면(불일치 알림), Formula 속성의 트리거 제약 때문에 §2-2의 스크립트가 필요합니다.**

---

## 2. Tier 2 — GitHub Actions (Notion이 못 하는 부분: 코드 읽기 + Formula 트리거)

### 2-1. API 명세서 ↔ 실제 코드 비교

> **수정 이력**: 처음 버전은 결과를 Notion DB에 코멘트로 남기도록 했는데, Notion API의 코멘트 생성은 `page_id`/`block_id`만 지원하고 **`database_id`는 지원하지 않습니다** (400 에러). 또 스크립트가 응답 상태를 확인하지 않아 실패해도 "등록 완료"로 출력되는 문제가 있었습니다. 아래는 이 두 가지를 고친 버전으로, 결과를 Notion 코멘트 대신 **Discord로 통보**합니다 (§2-2, §3과 동일한 방식으로 통일).

`.github/workflows/api-spec-check.yml`
```yaml
name: API Spec Consistency Check
on:
  push:
    paths:
      - "src/routes/**"   # 실제 라우트 정의 경로로 수정
  workflow_dispatch: {}    # 경로 변경 없이도 수동으로 테스트 실행 가능

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 scripts/check_api_spec.py
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_APISPEC_DS_ID: ${{ secrets.NOTION_APISPEC_DS_ID }}
          DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK_URL }}
```

`scripts/check_api_spec.py`
```python
import os, re, requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DS_ID = os.environ["NOTION_APISPEC_DS_ID"]  # 데이터베이스 ID가 아니라 데이터 소스 ID (§0-3 참고)
WEBHOOK = os.environ["DISCORD_WEBHOOK"]
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2025-09-03"}

# 1) 코드에서 실제 라우트 목록 추출 (Express 기준 예시 — 프레임워크에 맞게 정규식 수정)
code_routes = set()
for root, _, files in os.walk("src/routes"):
    for fn in files:
        if not fn.endswith(".js"):
            continue
        text = open(os.path.join(root, fn), encoding="utf-8").read()
        for m in re.finditer(r'router\.(get|post|put|delete)\(["\']([^"\']+)["\']', text):
            code_routes.add((m.group(1).upper(), m.group(2)))

# 2) Notion API 명세서 데이터 소스에서 문서화된 엔드포인트 목록 조회
notion_resp = requests.post(f"https://api.notion.com/v1/data_sources/{DS_ID}/query", headers=HEADERS)
notion_resp.raise_for_status()  # 조회 자체가 실패하면 여기서 바로 에러로 중단시켜서 침묵 실패를 방지

notion_routes = set()
for page in notion_resp.json().get("results", []):
    props = page["properties"]
    uri = props["URI"]["title"][0]["plain_text"] if props["URI"]["title"] else None
    method = props["메서드"]["select"]["name"] if props["메서드"]["select"] else None
    if uri and method:
        notion_routes.add((method, uri))

print("code_routes:", code_routes)
print("notion_routes:", notion_routes)

# 3) 차집합 계산 → Discord로 통보
missing_in_docs = code_routes - notion_routes
missing_in_code = notion_routes - code_routes

if missing_in_docs or missing_in_code:
    lines = ["**API 명세서 ↔ 코드 불일치 발견**"]
    if missing_in_docs:
        lines.append("**코드에는 있지만 명세서에 없음:**\n" + "\n".join(f"- {m} {u}" for m, u in missing_in_docs))
    if missing_in_code:
        lines.append("**명세서에는 있지만 코드에 없음(삭제됐거나 미구현):**\n" + "\n".join(f"- {m} {u}" for m, u in missing_in_code))

    discord_resp = requests.post(WEBHOOK, json={"content": "\n\n".join(lines)})
    discord_resp.raise_for_status()  # Discord 전송 실패도 여기서 바로 드러나게
    print("불일치 발견, Discord 통보 완료")
else:
    print("일치함")
```

### 2-2. 불일치 플래그(Formula) 알림 — §1-3에서 미룬 부분

`동기화 여부`, `완성도 체크`는 Formula라 Notion 자동화가 트리거로 못 쓴다고 했죠. 대신 Notion **API**는 Formula 속성으로 필터링하는 걸 지원하므로, 매일 한 번 조회해서 걸린 항목만 담당자에게 알려주는 스크립트로 대체합니다.

`.github/workflows/flag-notify.yml`
```yaml
name: Notify Inconsistency Flags
on:
  schedule:
    - cron: "30 0 * * 1-5"  # 매일 오전 9시 30분(KST), 평일만
  workflow_dispatch: {}

jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 scripts/notify_flags.py
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_WBS_DS_ID: ${{ secrets.NOTION_WBS_DS_ID }}
          NOTION_APISPEC_DS_ID: ${{ secrets.NOTION_APISPEC_DS_ID }}
          NOTION_FUNCSPEC_DS_ID: ${{ secrets.NOTION_FUNCSPEC_DS_ID }}
          DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK_URL }}
```

`scripts/notify_flags.py`
```python
import os, requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}
WEBHOOK = os.environ["DISCORD_WEBHOOK"]

def query_flagged(ds_id, formula_property, title_property, filter_type="string"):
    """Formula 속성이 걸린 페이지만 조회. filter_type="string"이면 값에 ⚠️가 포함된 것,
    "checkbox"이면 값이 True인 것을 찾는다. ds_id는 데이터베이스 ID가 아니라 데이터 소스 ID."""
    if filter_type == "checkbox":
        formula_filter = {"checkbox": {"equals": True}}
    else:
        formula_filter = {"string": {"contains": "⚠️"}}

    results = requests.post(
        f"https://api.notion.com/v1/data_sources/{ds_id}/query",
        headers=HEADERS,
        json={"filter": {"property": formula_property, "formula": formula_filter}},
    )
    if not results.ok:
        # 400/404 등 에러일 때 Notion이 보내는 실제 사유(예: 존재하지 않는 속성명, 타입 불일치)를 로그에 남김
        print(f"[{formula_property}] Notion API 에러 응답:", results.text)
        # 필터에 쓴 속성명이 실제와 다를 때를 대비해, 필터 없이 1건만 조회해서 진짜 속성명 목록을 같이 출력
        debug = requests.post(f"https://api.notion.com/v1/data_sources/{ds_id}/query", headers=HEADERS, json={"page_size": 1})
        if debug.ok:
            debug_results = debug.json().get("results", [])
            if debug_results:
                print(f"[{ds_id}] 실제 속성명 목록:", list(debug_results[0]["properties"].keys()))
    results.raise_for_status()
    results = results.json().get("results", [])

    flagged = []
    for page in results:
        props = page["properties"]
        title_list = props[title_property]["title"]
        name = title_list[0]["plain_text"] if title_list else "(제목 없음)"
        people = props.get("담당자", {}).get("people", [])
        assignee = people[0]["name"] if people else "미배정"
        flagged.append((page["id"], name, assignee))
    return flagged

lines = []

wbs_flagged = query_flagged(os.environ["NOTION_WBS_DS_ID"], "동기화 여부", "업무 항목")
for page_id, name, assignee in wbs_flagged:
    lines.append(f"- [WBS] **{name}** (담당: {assignee}) — 관련 문서가 더 최근에 수정됨")

func_flagged_sync = query_flagged(os.environ["NOTION_FUNCSPEC_DS_ID"], "동기화 여부", "기능")  # 다시 문자열(⚠️...) Formula로 변경됨
for page_id, name, _ in func_flagged_sync:
    lines.append(f"- [기능 명세서] **{name}** — API 명세서가 더 최근에 수정됨")

func_flagged_missing = query_flagged(os.environ["NOTION_FUNCSPEC_DS_ID"], "완성도 체크", "기능")
for page_id, name, _ in func_flagged_missing:
    lines.append(f"- [기능 명세서] **{name}** — 필수 항목 누락")

api_flagged_missing = query_flagged(os.environ["NOTION_APISPEC_DS_ID"], "완성도 체크", "URI")
for page_id, name, _ in api_flagged_missing:
    lines.append(f"- [API 명세서] **{name}** — 필수 항목 누락")

message = "**불일치 알림**\n" + ("\n".join(lines) if lines else "발견된 불일치 없음 ✅")
requests.post(WEBHOOK, json={"content": message})
```

담당자(WBS 항목의 경우)를 Discord에서 직접 멘션하고 싶다면, 이전에 만든 `member_map.json`과 유사하게 "Notion 담당자 이름 → Discord 사용자 ID" 매핑을 하나 추가하고 `<@디스코드ID>` 형식으로 치환하면 됩니다.

### 2-3. 디렉토리 구조 정리

Tier 2에서 다루는 파일들은 아래 위치에 커밋합니다. 워크플로우 파일은 `.github/workflows/` 아래에 있어야 GitHub Actions가 인식하고, 스크립트는 레포 루트의 `scripts/`에 모아둡니다.

```
저장소 루트/
├── .github/
│   └── workflows/
│       ├── api-spec-check.yml      # 2-1. push 시 자동 실행 (src/routes/** 변경 감지)
│       └── flag-notify.yml         # 2-2. 매일 오전 9시 30분(KST) 자동 실행 + 수동 실행 가능
│
├── scripts/
│   ├── check_api_spec.py           # 2-1이 호출
│   ├── notify_flags.py             # 2-2가 호출
│   └── member_map.json             # (선택) 담당자 매핑 — §1-2 사전준비에서 사용
│
└── src/
    └── routes/                     # check_api_spec.py가 실제 라우트를 읽어오는 대상 경로
        └── ...                     # 실제 프로젝트의 라우트 정의 파일들 (프레임워크에 맞게 위치 조정)
```

> `src/routes/` 경로는 예시입니다. 실제 백엔드 코드의 라우트 정의 위치에 맞춰 `api-spec-check.yml`의 `paths:` 값과 `check_api_spec.py`의 `os.walk("src/routes")` 부분을 함께 수정하세요.

---

## 3. Discord 알림 자동화

### 3-1. 실시간 알림 (설정만으로 가능, 코드 불필요)
Discord 서버 설정 → 연동 → **GitHub 앱 연동** 추가 → 레포 지정. 이러면 push/PR 이벤트가 코드 없이 바로 채널에 올라옵니다.

### 3-2. 일일 현황 리포트 (WBS는 PM이 수동 관리하지만, 리포트 자체는 자동)

`.github/workflows/daily-discord-report.yml`
```yaml
name: Daily Discord Report
on:
  schedule:
    - cron: "0 0 * * 1-5"  # 매일 오전 9시(KST), 평일만
  workflow_dispatch: {}

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 scripts/discord_report.py
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_DS_ID: ${{ secrets.NOTION_WBS_DS_ID }}
          DISCORD_WEBHOOK: ${{ secrets.DISCORD_WEBHOOK_URL }}
```

`scripts/discord_report.py`
```python
import os, requests
from datetime import date, timedelta

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DS_ID = os.environ["NOTION_DS_ID"]  # 데이터베이스 ID가 아니라 데이터 소스 ID (§0-3 참고)
WEBHOOK = os.environ["DISCORD_WEBHOOK"]
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2025-09-03"}

DONE_STATUSES = {"퍼블리싱 완료", "배포 완료", "최종 완료"}
today = date.today().isoformat()
tomorrow = (date.today() + timedelta(days=1)).isoformat()

query = requests.post(
    f"https://api.notion.com/v1/data_sources/{DS_ID}/query",
    headers=HEADERS,
    json={"filter": {"property": "작업일정", "date": {"on_or_before": tomorrow}}},
)
query.raise_for_status()
query = query.json()

lines = []
results = query.get("results", [])
if results:
    # 디버그: 실제 속성명 목록을 한 번만 출력 (숨은 문자·이름 오타 확인용, 원인 파악되면 지워도 됨)
    print("실제 속성명 목록:", list(results[0]["properties"].keys()))

for page in results:
    props = page["properties"]
    status_prop = props.get("업무 항목 현황", {}).get("status")
    status = status_prop["name"] if status_prop else "-"
    if status in DONE_STATUSES:
        continue

    title_list = props.get("업무 항목", {}).get("title", [])
    name = title_list[0]["plain_text"] if title_list else "(제목 없음)"

    date_prop = props.get("작업일정", {}).get("date")
    end = (date_prop["end"] or date_prop["start"]) if date_prop else None
    flag = "지연" if end and end < today else "임박"

    people = props.get("담당자", {}).get("people", [])
    assignee = people[0]["name"] if people else "미배정"

    # 실제 Notion 속성명에 숨은 제어 문자(\x08)가 포함되어 있음 (원본 템플릿에서 그렇게 만들어짐, 눈으로는 안 보임)
    area_prop = props.get("\x08업무 영역", {}).get("select")
    area = area_prop["name"] if area_prop else "-"
    lines.append(f"- [{flag}][{area}] **{name}** (담당: {assignee}, 상태: {status}, 마감: {end})")

message = "**오늘의 WBS 현황**\n" + ("\n".join(lines) if lines else "지연/임박 태스크 없음 ✅")
requests.post(WEBHOOK, json={"content": message})
```

---

## 4. PlantUML 자동 렌더링

### 4-1. 저장 구조
```
docs/
  diagrams/
    architecture.puml
    er-diagram.puml
    sequence-login.puml
```

### 4-2. 워크플로우

`.github/workflows/render-uml.yml`
```yaml
name: Render PlantUML
on:
  push:
    paths:
      - "docs/diagrams/**.puml"
  workflow_dispatch: {}

jobs:
  render:
    runs-on: ubuntu-latest
    permissions:
      contents: write   # git push를 위해 필요. 저장소 Settings > Actions > General에서 Workflow permissions가 "Read only"면 push가 거부되니 함께 확인
    steps:
      - uses: actions/checkout@v4
      - name: Install PlantUML
        run: sudo apt-get update && sudo apt-get install -y plantuml graphviz
      - name: Render diagrams to SVG
        run: plantuml -tsvg docs/diagrams/*.puml
      - name: Commit rendered diagrams
        run: |
          git config user.name "github-actions"
          git config user.email "actions@github.com"
          git add docs/diagrams/*.svg
          git diff --cached --quiet || git commit -m "docs: auto-render UML diagrams"
          git push
```

> 제3자 래퍼 액션이나 Docker 이미지 대신 **Ubuntu 공식 패키지(`plantuml`)를 러너에 직접 설치**하는 방식으로 바꿨습니다. `apt-get`으로 설치하는 표준 패키지라 특정 액션의 유지보수 중단이나 이미지 태그 문제에 영향받지 않고, `docs/diagrams/*.puml`도 러너의 bash가 직접 파일 목록으로 펼쳐서 넘기기 때문에(컨테이너를 거치지 않음) 와일드카드 관련 문제도 없습니다.

### 4-3. Notion에 연결
렌더링된 SVG의 GitHub Raw URL을 Notion 페이지에 `/embed` 블록으로 넣으면, 코드가 바뀌어 다이어그램이 새로 렌더링될 때마다 Notion에서도 자동으로 최신 상태가 보입니다.

---

## 5. Tier 3 — AI 최소 사용 (문장 의미 수준 검증)

규칙 기반으로 못 잡는 "문장이 실제로 모순되는가"만 AI가 담당합니다. 매일 배치로 한 번만 실행합니다.

`.github/workflows/ai-semantic-check.yml`
```yaml
name: AI Semantic Consistency Check (batch)
on:
  schedule:
    - cron: "0 1 * * 1-5"  # Discord 리포트보다 약간 늦게, 평일 1회
  workflow_dispatch: {}

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 scripts/ai_semantic_check.py
        env:
          NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
          NOTION_FUNCSPEC_DS_ID: ${{ secrets.NOTION_FUNCSPEC_DS_ID }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

`scripts/ai_semantic_check.py` (개념 코드)
```python
import os, requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DS_ID = os.environ["NOTION_FUNCSPEC_DS_ID"]  # 데이터베이스 ID가 아니라 데이터 소스 ID (§0-3 참고)
API_KEY = os.environ["ANTHROPIC_API_KEY"]
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2025-09-03"}

# 1) Tier 1에서 "⚠️ 동기화 여부"로 플래그된 항목만 조회 (전체 스캔 아님 — 핵심)
flagged = requests.post(
    f"https://api.notion.com/v1/data_sources/{DS_ID}/query",
    headers=HEADERS,
    json={"filter": {"property": "동기화 여부", "formula": {"string": {"contains": "⚠️"}}}},
)
flagged.raise_for_status()
flagged = flagged.json().get("results", [])

for page in flagged:
    props = page["properties"]
    desc = props["기능 설명"]["rich_text"][0]["plain_text"] if props["기능 설명"]["rich_text"] else ""
    # API 관계에서 이름/Query Params 등 최소 정보만 가져온다고 가정 (관계 페이지 재조회 필요)
    api_summary = "..."  # 관련 API 페이지의 URI/메서드/Query Params만 추출

    # 2) 최소 컨텍스트만 전달 + 저비용 모델
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 200,
            "messages": [{
                "role": "user",
                "content": (
                    f"기능 설명: {desc}\nAPI 요약: {api_summary}\n"
                    "위 두 내용이 서로 모순되는지 '모순' 또는 '일치'로만 답해줘."
                )
            }]
        }
    ).json()

    verdict = resp["content"][0]["text"].strip()
    if "모순" in verdict:
        requests.post(
            "https://api.notion.com/v1/comments",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={
                "parent": {"page_id": page["id"]},
                "rich_text": [{"text": {"content": "⚠️ AI 검토 결과: 기능 설명과 API 내용이 다를 수 있습니다. 확인 부탁드립니다."}}],
            },
        )
```

토큰 절감 포인트: **Tier 1에서 이미 걸러진 소수 항목만**, **전체 문서가 아니라 필드 두 개만**, **저비용 모델(Haiku)로**, **하루 1회 배치**로만 호출합니다.

---

## 6. 전체 설치 순서

| 순서 | 작업 | 담당 |
|---|---|---|
| 1 | Task ID 속성(Unique ID 타입) 추가, Notion Integration 생성/연결, Secrets 등록 | PM |
| 2 | Tier 1 Formula/Rollup/Automation 설정 (신규 항목 감지만 Notion 자동화로) | PM 또는 노션 관리자 |
| 3 | `flag-notify.yml` + 스크립트 커밋 (불일치 알림, Formula 트리거 제약 대응) | 아무나 1명 |
| 4 | Discord GitHub 앱 연동 (실시간 알림) | Discord 관리 권한자 |
| 5 | `daily-discord-report.yml` + 스크립트 커밋 | 아무나 1명 |
| 6 | `api-spec-check.yml` + 스크립트 커밋 (라우트 경로/정규식은 실제 코드에 맞게 수정) | 백엔드 담당 |
| 7 | PlantUML 워크플로우 커밋, 기존 다이어그램을 `.puml`로 이전 | 아키텍처 담당 |
| 8 (선택) | AI 배치 스크립트 추가 | 여유 있을 때 |

1~5번은 하루 안에 끝낼 수 있는 수준입니다. 6~8번은 이후 여유 있을 때 순차적으로 붙이시면 됩니다.
