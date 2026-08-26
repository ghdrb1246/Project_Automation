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

    area_prop = props.get("업무 영역", {}).get("select")
    area = area_prop["name"] if area_prop else "-"
    lines.append(f"- [{flag}][{area}] **{name}** (담당: {assignee}, 상태: {status}, 마감: {end})")

message = "**오늘의 WBS 현황**\n" + ("\n".join(lines) if lines else "지연/임박 태스크 없음 ✅")
requests.post(WEBHOOK, json={"content": message})