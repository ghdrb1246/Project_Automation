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
    uri = props["URI"]["rich_text"][0]["plain_text"] if props["URI"]["rich_text"] else None
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