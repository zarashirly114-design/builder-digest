import json, os, csv
from datetime import datetime
from pathlib import Path

BASE = os.path.expanduser("~/.hermes/skills/builder-digest")
TODAY = datetime.now().strftime("%Y-%m-%d")
TWEETS_DIR = os.path.join(BASE, "data", "tweets", TODAY)
OUTPUT_DIR = os.path.join(BASE, "data", "output", TODAY)
GITHUB_USER = "zarashirly114-design"
REPO = "builder-digest"

os.makedirs(OUTPUT_DIR, exist_ok=True)

csv_path = os.path.join(OUTPUT_DIR, f"builder-digest-{TODAY}.csv")

rows = []
files = sorted(Path(TWEETS_DIR).glob("*.json"))

for f in files:
    with open(f) as fh:
        d = json.load(fh)
    name = f.stem
    github_url = f"https://{GITHUB_USER}.github.io/{REPO}/{TODAY}/{name}.html"
    rows.append([
        TODAY,
        d.get("platform", "X/Twitter"),
        d.get("author_name", ""),
        "@" + d.get("author_handle", ""),
        d.get("text", ""),
        d.get("text_zh", ""),
        d.get("url", "").replace("https://x.com/", "x.com/"),
        d.get("likes", 0),
        d.get("retweets", 0),
        github_url,
        d.get("text_zh", "")
    ])

with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["日期", "来源", "Builder", "账号", "英文原文", "中文翻译", "原文链接", "点赞", "转发", "卡片链接", "发布文案"])
    w.writerows(rows)

print(f"✅ CSV 已生成: {csv_path}")
print(f"共 {len(rows)} 条记录")
