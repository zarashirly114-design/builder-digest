import json, os, requests

BASE = os.path.expanduser("~/.hermes/skills/builder-digest")
with open(os.path.join(BASE, ".env")) as f:
    for line in f:
        if "FEISHU_APP_SECRET" in line:
            secret = line.strip().split("=", 1)[1]
            break

APP_ID = "cli_a9685f6be8f8dbcd"
BASE_ID = "P5MRb8PUqa3hPZsvZstcoA5Rn8g"
TABLE_ID = "tbl4zo3fSZq9rvDw"

resp = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": APP_ID, "app_secret": secret},
).json()
TOKEN = resp["tenant_access_token"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# 获取所有记录
records = []
page_token = None
while True:
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records?page_size=100"
    if page_token:
        url += f"&page_token={page_token}"
    r = requests.get(url, headers=HEADERS).json()
    items = r.get("data", {}).get("items", [])
    records.extend(items)
    if not r.get("data", {}).get("has_more"):
        break
    page_token = r["data"]["page_token"]

# 筛选 2026-05-01 的记录
to_delete = [
    r["record_id"]
    for r in records
    if r.get("fields", {}).get("日期") == "2026-05-01"
]

print(f"将删除 {len(to_delete)} 条 5月1日的记录")

deleted = 0
for rid in to_delete:
    del_url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records/{rid}"
    r = requests.delete(del_url, headers=HEADERS).json()
    if r.get("code") == 0:
        deleted += 1
    else:
        print(f"  删除失败 {rid}: {r}")

print(f"清理完成：成功删除 {deleted} 条")
