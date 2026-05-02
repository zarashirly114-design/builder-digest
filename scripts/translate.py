#!/usr/bin/env python3
"""
Builder Digest · translate.py
批量翻译：读取当天 tweets JSON，调用 DeepSeek API 逐条翻译 title 和 text，
结果写入 JSON（text_zh / title_zh）并生成 Markdown。
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# --- 配置 ---
BASE_DIR = os.path.expanduser("~/.hermes/skills/builder-digest")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")
TODAY = datetime.now().strftime("%Y-%m-%d")
TWEETS_DIR = os.path.join(DATA_DIR, "tweets", TODAY)
CARDS_DIR = os.path.join(DATA_DIR, "cards", TODAY)
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
MAX_RETRIES = 3

os.makedirs(CARDS_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"translate-{TODAY}.log")
success_count = 0
fail_count = 0


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_tweets():
    """加载当天所有推文 JSON，按文件名排序"""
    files = sorted(Path(TWEETS_DIR).glob("*.json"))
    tweets = []
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            tweets.append({"file": str(f), "data": json.load(fh)})
    return tweets


def translate_single(d):
    """翻译单条推文的 title 和 text"""
    title = d.get("title", "")
    text = d.get("text", "")

    system = """你是一个专业的英中翻译助手。请将以下 TITLE 和 TEXT 完整翻译成中文。

输出格式：
TITLE_ZH: 中文标题
TEXT_ZH: 中文正文（翻译全部段落，保留原文换行）

要求：
1. 完整翻译全部内容，严禁省略任何段落
2. 忠实原文，不添加不删减
3. 中文自然流畅
4. 保留 @handle、链接、技术术语原文"""

    user = f"TITLE: {title}\nTEXT: {text}"

    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.3,
        "max_tokens": 4096
    }).encode("utf-8")

    import urllib.request
    import urllib.error

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(API_URL, data=payload)
            req.add_header("Content-Type", "application/json")
            req.add_header("Authorization", f"Bearer {API_KEY}")
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
                raw = result["choices"][0]["message"]["content"]

                title_zh = ""
                text_zh_lines = []
                in_text = False
                for line in raw.strip().split("\n"):
                    if line.startswith("TITLE_ZH:"):
                        title_zh = line.replace("TITLE_ZH:", "").strip()
                        in_text = False
                    elif line.startswith("TEXT_ZH:"):
                        text_zh_lines.append(line.replace("TEXT_ZH:", "").strip())
                        in_text = True
                    elif in_text:
                        text_zh_lines.append(line.strip())

                return title_zh, "\n".join(text_zh_lines)
        except Exception as e:
            log(f"API 调用失败（第 {attempt}/{MAX_RETRIES} 次）：{e}")
            if attempt < MAX_RETRIES:
                time.sleep(3)
    return None, None


def clean_title(text):
    """标题清理：去链接、去emoji、保留空格、智能截断≤15字"""
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'[😀-🙏🌀-🗿🚀-🛿🤀-🧿🩰-🫿]', '', text)
    text = re.sub(r'[ \t]+', ' ', text).strip()
    if len(text) <= 15:
        return text
    for i in range(14, -1, -1):
        if text[i] in '。！？，、；：）""\'\'.,!?;:)-':
            return text[:i+1].strip()
    return text[:15].strip()

def clean_zh(text):
    """中文清理：只去emoji"""
    return re.sub(r'[😀-🙏🌀-🗿🚀-🛿🤀-🧿🩰-🫿]', '', text)


def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_markdown(tweet):
    """生成中英双语 Markdown 卡片内容"""
    d = tweet["data"]
    lines = [
        f"> {d['text']}",
        "",
        f"{d.get('text_zh', '')}",
        "",
        f"—— {d['author_name']} (@{d['author_handle']}) · {d['platform']}",
        f"📎 原文链接：{d['url']}",
    ]
    return "\n".join(lines)


# --- 主流程 ---
if not API_KEY:
    log("❌ 未设置 DEEPSEEK_API_KEY 环境变量，请先在 .env 中配置")
    sys.exit(1)

log("translate.py 开始执行")

tweets = load_tweets()
if not tweets:
    log("⚠️  当天无推文，退出")
    sys.exit(0)

log(f"共加载 {len(tweets)} 条推文，逐条翻译中...")

for tweet in tweets:
    title_zh, text_zh = translate_single(tweet["data"])
    if text_zh is None:
        log(f"❌ {Path(tweet['file']).name} 翻译失败")
        fail_count += 1
        continue

    tweet["data"]["title_zh"] = clean_title(title_zh)
    tweet["data"]["text_zh"] = clean_zh(text_zh)

    save_json(tweet["file"], tweet["data"])

    handle = tweet["data"]["author_handle"].replace("@", "").replace("/", "_")
    seq = Path(tweet["file"]).stem.split("-")[-1]
    md_filename = f"{handle}-{seq}.md"
    md_path = os.path.join(CARDS_DIR, md_filename)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(generate_markdown(tweet))

    log(f"✅ {Path(tweet['file']).name} → {md_filename}")
    success_count += 1

log("")
log(f"翻译完成：{success_count} 成功，{fail_count} 失败")
log(f"Markdown 输出：{CARDS_DIR}")
