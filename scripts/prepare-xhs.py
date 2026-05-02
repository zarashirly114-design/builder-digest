#!/usr/bin/env python3
"""
Builder Digest · prepare-xhs.py
从当天的 CSV 中筛选点赞前6的推文，截图生成 PNG，打包预备发布素材，并发送飞书通知。
新增：生成点赞排行榜图片（榜单.png），复用模板 CSS 和品牌元素，自带每步自检和错误报告。
"""

import csv, os, subprocess, sys, json, requests
from datetime import datetime
from pathlib import Path

# ---------- 配置 ----------
BASE = os.path.expanduser("~/.hermes/skills/builder-digest")
TODAY = datetime.now().strftime("%Y-%m-%d")
CSV_FILE = os.path.join(BASE, "data", "output", TODAY, f"builder-digest-{TODAY}.csv")
IMAGES_DIR = os.path.join(BASE, "data", "images", TODAY)
RELEASE_DIR = os.path.join(BASE, "data", "output", "预备发布", TODAY)
TEMPLATE_FILE = os.path.join(BASE, "data", "template.html")

# 飞书配置
env = {}
with open(os.path.join(BASE, ".env")) as f:
    for line in f:
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.strip().split("=", 1)
            env[k] = v
FEISHU_WEBHOOK = env.get("FEISHU_WEBHOOK", "")
TABLE_LINK = "https://my.feishu.cn/base/P5MRb8PUqa3hPZsvZstcoA5Rn8g?table=tbl4zo3fSZq9rvDw"

error_occurred = False

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# ---------- 1. 读取 CSV ----------
log("1/6 读取 CSV...")
if not os.path.exists(CSV_FILE):
    log(f"❌ CSV 文件不存在：{CSV_FILE}")
    sys.exit(1)

with open(CSV_FILE, encoding="utf-8-sig") as f:
    reader = list(csv.DictReader(f))

required_cols = ["点赞", "卡片链接", "Builder", "中文翻译", "来源", "账号", "转发"]
missing_cols = [c for c in required_cols if c not in reader[0]]
if missing_cols:
    log(f"❌ CSV 缺少必要列：{missing_cols}")
    sys.exit(1)

log(f"✅ CSV 读取成功，共 {len(reader)} 条记录")

# ---------- 2. 排序取前6 ----------
log("2/6 按点赞排序取前6...")
valid_rows = []
for r in reader:
    try:
        likes = int(r.get("点赞", 0))
    except ValueError:
        likes = 0
    valid_rows.append((likes, r))

valid_rows.sort(key=lambda x: x[0], reverse=True)
top10 = [r for _, r in valid_rows[:10]]

if len(top10) < 6:
    log(f"⚠️ 只有 {len(top10)} 条有效记录（预期 10 条）")

log(f"✅ 已取前 {len(top10)} 条，最高点赞：{valid_rows[0][0]}")

# ---------- 3. 截图前6张卡片 ----------
log("3/6 截图生成 PNG...")
os.makedirs(RELEASE_DIR, exist_ok=True)

screenshot_ok = 0
for i, row in enumerate(top10, 1):
    link = row.get("卡片链接", "")
    filename = link.split("/")[-1] if "/" in link else ""
    if not filename:
        log(f"⚠️ 第 {i} 条卡片链接无效，跳过")
        continue

    html_path = os.path.join(IMAGES_DIR, filename)
    if not os.path.exists(html_path):
        log(f"❌ HTML 文件不存在：{html_path}")
        error_occurred = True
        continue

    png_path = os.path.join(RELEASE_DIR, f"{i:02d}-{filename.replace(".html", ".png")}")

    result = subprocess.run([
        "node", "-e", f"""
        const puppeteer = require('puppeteer');
        (async () => {{
            const browser = await puppeteer.launch({{ headless: 'new' }});
            const page = await browser.newPage();
            await page.setViewport({{ width: 1080, height: 1440 }});
            await page.goto('file://{html_path}', {{ waitUntil: 'networkidle0' }});
            await page.screenshot({{ path: '{png_path}', fullPage: true }});
            await browser.close();
        }})();
        """
    ], capture_output=True, text=True)

    if result.returncode != 0:
        log(f"❌ Puppeteer 截图失败：{filename}")
        log(f"   stderr: {result.stderr[:200]}")
        error_occurred = True
        continue

    if os.path.exists(png_path) and os.path.getsize(png_path) > 0:
        log(f"  ✅ {filename} → PNG ({os.path.getsize(png_path)} 字节)")
        screenshot_ok += 1
    else:
        log(f"❌ 截图文件为空或缺失：{png_path}")
        error_occurred = True

        error_occurred = True

# ---------- 5. 生成文案模板 ----------
log("4/5 生成文案模板...")
md_lines = [
    f"# 小红书发布素材 · {TODAY}",
    "",
    "| 排名 | Builder | 中文翻译（初稿） | 点赞 |",
    "|------|---------|-----------------|------|"
]
for i, row in enumerate(top10, 1):
    builder = row.get("Builder", "")
    text_zh = row.get("中文翻译", "")[:80].replace("|", " ").replace("\n", " ")
    likes = row.get("点赞", "")
    md_lines.append(f"| {i} | {builder} | {text_zh}... | {likes} |")

md_path = os.path.join(RELEASE_DIR, "发布文案.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

if os.path.exists(md_path):
    log(f"✅ 文案模板已生成：{md_path}")
else:
    log("❌ 文案模板生成失败")
    error_occurred = True

# ---------- 6. 飞书通知 ----------
log("5/5 发送飞书通知...")
if FEISHU_WEBHOOK:
    ranking_summary = "；".join([f"{i}. {r['Builder']}({r['点赞']}👍)" for i, r in enumerate(top10, 1)])
    message = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "Builder Digest · 今日发布提醒"},
                "template": "wathet"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": f"今日点赞前{len(top10)}已生成\n**🕒 {TODAY}**\n\n{ranking_summary}"}
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "📊 查看飞书表格"},
                            "url": TABLE_LINK,
                            "type": "default"
                        }
                    ]
                }
            ]
        }
    }
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=message, timeout=10)
        if resp.status_code == 200 and resp.json().get("code") == 0:
            log("✅ 飞书通知已发送")
        else:
            log(f"⚠️ 飞书通知失败：{resp.text}")
            error_occurred = True
    except Exception as e:
        log(f"⚠️ 飞书通知异常：{e}")
        error_occurred = True
else:
    log("⚠️ 未配置 FEISHU_WEBHOOK，跳过飞书通知")

# ---------- 最终汇总 ----------
log("")
if error_occurred:
    log("⚠️ 发布素材准备完成，但有部分错误，请检查上述日志。")
else:
    log("✅ 全部步骤完成，发布素材已就绪。")
log(f"   图片数量：{screenshot_ok}/{len(top10)}")
log(f"   素材目录：{RELEASE_DIR}")
