import os, requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}
WEBHOOK = os.environ["DISCORD_WEBHOOK"]

def query_flagged(ds_id, formula_property, title_property):
    """Formula 속성 값에 ⚠️가 포함된 페이지만 조회 (API는 Formula 필터를 지원함). ds_id는 데이터베이스 ID가 아니라 데이터 소스 ID."""
    results = requests.post(
        f"https://api.notion.com/v1/data_sources/{ds_id}/query",
        headers=HEADERS,
        json={"filter": {"property": formula_property, "formula": {"string": {"contains": "⚠️"}}}},
    )
    if not results.ok:
        # 400/404 등 에러일 때 Notion이 보내는 실제 사유(예: 존재하지 않는 속성명)를 로그에 남김
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

func_flagged_sync = query_flagged(os.environ["NOTION_FUNCSPEC_DS_ID"], "동기화 여부", "기능")
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