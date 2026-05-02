import json, os, requests

BASE = os.path.expanduser("~/.hermes/skills/builder-digest")
ENV_FILE = os.path.join(BASE, ".env")

def load_env():
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

env = load_env()
APP_ID = env["FEISHU_APP_ID"]
APP_SECRET = env["FEISHU_APP_SECRET"]
TABLE_ID = env["FEISHU_TABLE_ID"]
BASE_ID = "P5MRb8PUqa3hPZsvZstcoA5Rn8g"

# 获取 token
resp = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": APP_ID, "app_secret": APP_SECRET}).json()
TOKEN = resp["tenant_access_token"]

HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def get_all_records():
    """获取表格中所有记录"""
    records = []
    page_token = None
    while True:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records?page_size=100"
        if page_token:
            url += f"&page_token={page_token}"
        r = requests.get(url, headers=HEADERS).json()
        if r.get("code") != 0:
            print("获取记录失败:", r)
            break
        items = r.get("data", {}).get("items", [])
        records.extend(items)
        if not r.get("data", {}).get("has_more"):
            break
        page_token = r["data"]["page_token"]
    return records

def delete_record(record_id):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records/{record_id}"
    r = requests.delete(url, headers=HEADERS).json()
    return r.get("code") == 0

print("正在获取所有记录...")
records = get_all_records()
print(f"共 {len(records)} 条记录")

# 筛选 2026-05-01 日期中链接不含日期的重复记录
to_delete = []
for r in records:
    fields = r.get("fields", {})
    date = fields.get("日期", "")
    link_obj = fields.get("在线预览", {})
    link = link_obj.get("link", "") if isinstance(link_obj, dict) else ""
    record_id = r.get("record_id", "")
    
    # 日期为 2026-05-01 但链接不含 2026-05-01 的是旧格式重复数据
    if date == "2026-05-01" and "2026-05-01" not in link:
        to_delete.append(record_id)

print(f"发现 {len(to_delete)} 条重复记录，开始删除...")
deleted = 0
for rid in to_delete:
    if delete_record(rid):
        deleted += 1
        print(f"  已删除 {rid}")
    else:
        print(f"  删除失败 {rid}")

print(f"清理完成：成功删除 {deleted}/{len(to_delete)} 条重复记录")
