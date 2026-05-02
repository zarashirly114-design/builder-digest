import json, os, sys, time, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

BASE = os.path.expanduser("~/.hermes/skills/builder-digest")
TEMPLATE = os.path.join(BASE, "data", "template.html")
TWEETS_DIR = os.path.join(BASE, "data", "tweets")
IMAGES_DIR = os.path.join(BASE, "data", "images")
OUTPUT_DIR = os.path.join(BASE, "data", "output")
LOG_DIR = os.path.join(BASE, "logs")
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/chat/completions"
MAX_RETRIES = 3

TODAY = datetime.now().strftime("%Y-%m-%d")
TWEETS_TODAY = os.path.join(TWEETS_DIR, TODAY)
IMAGES_TODAY = os.path.join(IMAGES_DIR, TODAY)
OUTPUT_TODAY = os.path.join(OUTPUT_DIR, TODAY)

for d in [IMAGES_TODAY, OUTPUT_TODAY, LOG_DIR]:
    os.makedirs(d, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"gen-card-{TODAY}.log")
success = 0
fail = 0

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def call_deepseek(system, user, max_tokens=512):
    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0.5,
        "max_tokens": max_tokens
    }).encode("utf-8")
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(API_URL, data=payload)
            req.add_header("Content-Type", "application/json")
            req.add_header("Authorization", f"Bearer {API_KEY}")
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode())["choices"][0]["message"]["content"].strip()
        except Exception as e:
            log(f"API 调用失败 (attempt {attempt}/{MAX_RETRIES}): {e}")
            time.sleep(3)
    return None

def generate_title(text):
    system = "你是专业编辑。用不超过15字的中文口语概括以下推文的核心观点。要求：1.用有温度的口语，像发微博一样自然，不要机器腔、不要书面语；2.禁止使用学术词（分析、研究、探讨、可行性、浅谈、思考）；3.必须具体到最核心观点，不能泛泛而谈；4.说人话，要有活人感觉；5.直接输出标题，不加引号、不加句号、不解释。"
    return call_deepseek(system, text, max_tokens=32)

def translate_text(text):
    system = "你是专业英中翻译。翻译以下推文为中文，忠实原文、自然流畅、保留@handle和链接。直接输出译文，不加解释。"
    return call_deepseek(system, text, max_tokens=4096)

# --- 主流程 ---
if not API_KEY:
    log("❌ 未设置 DEEPSEEK_API_KEY")
    sys.exit(1)

with open(TEMPLATE, "r", encoding="utf-8") as f:
    tpl = f.read()

files = sorted(Path(TWEETS_TODAY).glob("*.json"))
if not files:
    log("⚠️ 当天无推文")
    sys.exit(0)

log(f"共 {len(files)} 条推文，开始生成卡片...")

for f in files:
    with open(f, "r", encoding="utf-8") as fh:
        d = json.load(fh)

    name = f.stem

    # ====== 检查点 1：翻译完整性 ======
    text_zh = d.get("text_zh", "").strip()
    if not text_zh:
        log(f"⚠️ {name} 中文翻译缺失，正在补翻译...")
        translated = translate_text(d["text"])
        if translated:
            d["text_zh"] = translated
            d["title_zh"] = translated[:30]
            with open(f, "w", encoding="utf-8") as fw:
                json.dump(d, fw, ensure_ascii=False, indent=2)
            log(f"✅ {name} 翻译已补全")
        else:
            log(f"❌ {name} 补翻译失败，跳过")
            fail += 1
            continue

    # 生成标题
    title = generate_title(d["text"])
    if not title:
        title = d.get("title_zh", d["text"][:30])
        log(f"⚠️ {name} 标题生成失败，使用备选")

    # 替换占位符
    html = tpl
    html = html.replace("{{TITLE}}", title or "")
    html = html.replace("{{EN_TEXT}}", d.get("text", "").replace('"', '\\"'))
    html = html.replace("{{ZH_TEXT}}", d.get("text_zh", ""))
    html = html.replace("{{AUTHOR}}", d.get("author_name", ""))
    html = html.replace("{{HANDLE}}", "@" + d.get("author_handle", "") + " · " + d.get("platform", ""))
    html = html.replace("{{URL}}", d.get("url", "").replace("https://x.com/", "x.com/"))
    html = html.replace("{{DATE}}", TODAY)

    # 检查点 2：占位符完整性
    remaining = [p for p in ["{{TITLE}}","{{EN_TEXT}}","{{ZH_TEXT}}","{{AUTHOR}}","{{HANDLE}}","{{URL}}","{{DATE}}"] if p in html]
    if remaining:
        log(f"❌ {name} 存在未替换的占位符：{remaining}")
        fail += 1
        continue

    # 写入 images 和 output
    for p in [os.path.join(IMAGES_TODAY, name + ".html"),
              os.path.join(OUTPUT_TODAY, name + ".html")]:
        with open(p, "w", encoding="utf-8") as fw:
            fw.write(html)

    log(f"✅ {name}.html")
    success += 1

log(f"\n完成：{success} 成功，{fail} 失败")
