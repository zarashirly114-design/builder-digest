import json, os, sys, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

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
APP_ID = env.get("FEISHU_APP_ID", "")
APP_SECRET = env.get("FEISHU_APP_SECRET", "")
TABLE_ID = env.get("FEISHU_TABLE_ID", "")
BASE_ID = "P5MRb8PUqa3hPZsvZstcoA5Rn8g"
GITHUB_USER = "zarashirly114-design"
REPO = "builder-digest"

def get_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = json.dumps({"app_id": APP_ID, "app_secret": APP_SECRET}).encode()
    req = urllib.request.Request(url, data=payload)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["tenant_access_token"]

TOKEN = get_token()
print("✅ Token 已获取")

TODAY = datetime.now().strftime("%Y-%m-%d")
tweet_dir = os.path.join(BASE, "data", "tweets", TODAY)
files = sorted(Path(tweet_dir).glob("*.json"))

success = 0
for f in files:
    with open(f) as fh:
        d = json.load(fh)
    name = f.stem
    github_url = f"https://{GITHUB_USER}.github.io/{REPO}/{TODAY}/{name}.html"

    fields = {
        "日期": TODAY,
        "来源": d.get("platform", "X/Twitter"),
        "Builder": d.get("author_name", ""),
        "账号": "@" + d.get("author_handle", ""),
        "英文原文": d.get("text", ""),
        "中文翻译": d.get("text_zh", ""),
        "原文链接": {"link": d.get("url", ""), "text": d.get("url", "").replace("https://x.com/", "x.com/")},
        "点赞": d.get("likes", 0),
        "转发": d.get("retweets", 0),
        "在线预览": {"link": github_url, "text": github_url}
    }

    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BASE_ID}/tables/{TABLE_ID}/records"
    payload = json.dumps({"fields": fields}).encode()
    req = urllib.request.Request(url, data=payload)
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {TOKEN}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if result.get("code") == 0:
                success += 1
            else:
                print(f"❌ {name}: {result}")
    except urllib.error.HTTPError as e:
        print(f"❌ {name} HTTP {e.code}: {e.read().decode()}")

print(f"\n✅ 同步完成：{success}/{len(files)} 条")
