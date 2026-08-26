import os, re, requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DB_ID = os.environ["NOTION_APISPEC_DB_ID"]
HEADERS = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28"}

# 1) 코드에서 실제 라우트 목록 추출 (Express 기준 예시 — 프레임워크에 맞게 정규식 수정)
code_routes = set()
for root, _, files in os.walk("src/routes"):
    for fn in files:
        if not fn.endswith(".js"):
            continue
        text = open(os.path.join(root, fn), encoding="utf-8").read()
        for m in re.finditer(r'router\.(get|post|put|delete)\(["\']([^"\']+)["\']', text):
            code_routes.add((m.group(1).upper(), m.group(2)))

# 2) Notion API 명세서 DB에서 문서화된 엔드포인트 목록 조회
notion_routes = set()
results = requests.post(
    f"https://api.notion.com/v1/databases/{DB_ID}/query", headers=HEADERS
).json().get("results", [])

for page in results:
    props = page["properties"]
    uri = props["URI"]["rich_text"][0]["plain_text"] if props["URI"]["rich_text"] else None
    method = props["메서드"]["select"]["name"] if props["메서드"]["select"] else None
    if uri and method:
        notion_routes.add((method, uri))

# 3) 차집합 계산 → Notion 코멘트로 알림
missing_in_docs = code_routes - notion_routes
missing_in_code = notion_routes - code_routes

if missing_in_docs or missing_in_code:
    lines = []
    if missing_in_docs:
        lines.append("**코드에는 있지만 명세서에 없음:**\n" + "\n".join(f"- {m} {u}" for m, u in missing_in_docs))
    if missing_in_code:
        lines.append("**명세서에는 있지만 코드에 없음(삭제됐거나 미구현):**\n" + "\n".join(f"- {m} {u}" for m, u in missing_in_code))

    requests.post(
        "https://api.notion.com/v1/comments",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={
            "parent": {"database_id": DB_ID},
            "rich_text": [{"text": {"content": "\n\n".join(lines)}}],
        },
    )
    print("불일치 발견, 코멘트 등록 완료")
else:
    print("일치함")