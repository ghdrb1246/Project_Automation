import os, requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
WEBHOOK = os.environ["DISCORD_WEBHOOK"]

def query_flagged(db_id, formula_property, title_property):
    """Formula 속성 값에 ⚠️가 포함된 페이지만 조회 (API는 Formula 필터를 지원함)"""
    results = requests.post(
        f"https://api.notion.com/v1/databases/{db_id}/query",
        headers=HEADERS,
        json={"filter": {"property": formula_property, "formula": {"string": {"contains": "⚠️"}}}},
    ).json().get("results", [])

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

wbs_flagged = query_flagged(os.environ["NOTION_WBS_DB_ID"], "동기화 필요", "업무 항목")
for page_id, name, assignee in wbs_flagged:
    lines.append(f"- [WBS] **{name}** (담당: {assignee}) — 관련 문서가 더 최근에 수정됨")

func_flagged_sync = query_flagged(os.environ["NOTION_FUNCSPEC_DB_ID"], "동기화 필요", "기능")
for page_id, name, _ in func_flagged_sync:
    lines.append(f"- [기능 명세서] **{name}** — API 명세서가 더 최근에 수정됨")

func_flagged_missing = query_flagged(os.environ["NOTION_FUNCSPEC_DB_ID"], "완성도 체크", "기능")
for page_id, name, _ in func_flagged_missing:
    lines.append(f"- [기능 명세서] **{name}** — 필수 항목 누락")

api_flagged_missing = query_flagged(os.environ["NOTION_APISPEC_DB_ID"], "완성도 체크", "API 이름")
for page_id, name, _ in api_flagged_missing:
    lines.append(f"- [API 명세서] **{name}** — 필수 항목 누락")

message = "**불일치 알림**\n" + ("\n".join(lines) if lines else "발견된 불일치 없음 ✅")
requests.post(WEBHOOK, json={"content": message})