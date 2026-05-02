import csv, os, base64, subprocess
from datetime import datetime
from pathlib import Path

BASE = os.path.expanduser("~/.hermes/skills/builder-digest")
TODAY = datetime.now().strftime("%Y-%m-%d")
CSV_FILE = os.path.join(BASE, "data", "output", TODAY, f"builder-digest-{TODAY}.csv")
TEMPLATE = os.path.join(BASE, "data", "ranking-template.html")
LOGO_SVG = os.path.join(BASE, "data", "logo.svg")
OUTPUT_DIR = os.path.join(BASE, "data", "output", "预备发布", TODAY)
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(CSV_FILE, encoding="utf-8-sig") as f:
    reader = list(csv.DictReader(f))
ranking = sorted(reader, key=lambda x: (-int(x.get("点赞",0)), -int(x.get("转发",0))))[:10]

with open(TEMPLATE, encoding="utf-8") as f:
    tpl = f.read()
with open(LOGO_SVG, "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode()

cn_date = f"{datetime.now().year}年{datetime.now().month}月{datetime.now().day}日"

rows = ""
for i, row in enumerate(ranking, 1):
    zh = row.get("中文翻译", "")
    title = (zh[:50] + "...") if len(zh) > 50 else zh
    likes = row.get("点赞", "0")
    retweets = row.get("转发", "0")
    likes_display = f"{likes} 👍" if i <= 3 else likes
    rows += f"""    <div class="rank-row">
      <span class="rank-num">{i}</span>
      <span class="rank-source">{row.get("来源", "")}</span>
      <span class="rank-builder">{row.get("Builder", "")}</span>
      <span class="rank-title">{title}</span>
      <span class="rank-likes">{likes_display}</span>
      <span class="rank-retweets">{retweets}{" 👍" if i <= 3 else ""}</span>
    </div>
"""

html = tpl.replace("{{LOGO_BASE64}}", f"data:image/svg+xml;base64,{logo_b64}")
html = html.replace("{{DATE_CN}}", cn_date)
html = html.replace("{{ROWS}}", rows)

tmp = os.path.join(OUTPUT_DIR, "榜单-tmp.html")
png_path = os.path.join(OUTPUT_DIR, "榜单.png")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(html)

subprocess.run([
    "node", "-e", f"""
    const puppeteer = require('puppeteer');
    const fs = require('fs');
    (async () => {{
        const browser = await puppeteer.launch({{ headless: 'new' }});
        const page = await browser.newPage();
        await page.setViewport({{ width: 1080, height: 1440 }});
        await page.goto('file://{tmp}', {{ waitUntil: 'networkidle0' }});
        await page.screenshot({{ path: '{png_path}', fullPage: true }});
        await browser.close();
        fs.unlinkSync('{tmp}');
        console.log('done');
    }})();
    """
])
print(f"✅ 榜单图片已生成：{png_path}")
