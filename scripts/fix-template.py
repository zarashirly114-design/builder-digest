import base64, os

BASE = os.path.expanduser('~/.hermes/skills/builder-digest')
logo_path = os.path.join(BASE, 'data', 'logo.svg')
with open(logo_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>小红书卡片 · Builder Digest</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; background: #e8e5df; padding: 20px;
    font-family: -apple-system, "PingFang SC", "Noto Sans SC", sans-serif;
  }
  .card {
    width: 1080px; height: 1440px; background: #FFFFFF;
    border-radius: 4px; display: flex; flex-direction: column;
    position: relative; overflow: hidden;
    box-shadow: 0 8px 30px rgba(0,0,0,0.06);
  }
  .card::before {
    content: ""; position: absolute; inset: 0;
    background: radial-gradient(ellipse at 50% 40%, rgba(53, 193, 190, 0.12) 0%, transparent 75%);
    pointer-events: none; z-index: 0;
  }
  .card::after {
    content: ""; position: absolute;
    top: 40px; left: 40px; right: 40px; height: 1px;
    background: rgba(53, 193, 190, 0.22); z-index: 2; pointer-events: none;
  }
  .dot {
    position: absolute; width: 8px; height: 8px;
    background: #35c1be; border-radius: 50%; opacity: 0.5; z-index: 2;
  }
  .dot-1 { top: 34px; left: 34px; }
  .dot-2 { top: 34px; right: 34px; }
  .dot-3 { bottom: 62px; left: 34px; }
  .dot-4 { bottom: 62px; right: 34px; }
  .toolbar {
    display: none; position: fixed; top: 16px; left: 50%;
    transform: translateX(-50%); background: #2C2416; color: #fff;
    padding: 12px 24px; border-radius: 30px; gap: 16px;
    z-index: 9999; font-size: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }
  body.editing .toolbar { display: flex; align-items: center; flex-wrap: wrap; }
  .toolbar button {
    background: #35c1be; border: none; color: #fff;
    padding: 8px 18px; border-radius: 20px; cursor: pointer;
    font-size: 14px; font-weight: 600; white-space: nowrap;
  }
  .toolbar button:hover { opacity: 0.85; }
  .toolbar .btn-download { background: #f59e0b; }
  .color-swatch { display: flex; gap: 8px; align-items: center; }
  .color-swatch span { font-size: 12px; opacity: 0.7; }
  .color-dot {
    width: 22px; height: 22px; border-radius: 50%;
    border: 2px solid rgba(255,255,255,0.5); cursor: pointer;
    transition: transform 0.15s, border-color 0.15s;
  }
  .color-dot:hover { transform: scale(1.2); }
  .color-dot.active { border-color: #fff; transform: scale(1.25); }
  [contenteditable="true"] {
    outline: 2px dashed rgba(53, 193, 190, 0.5);
    outline-offset: 4px; border-radius: 6px; cursor: text;
  }
  [contenteditable="true"]:focus {
    outline: 2px solid #35c1be; background: rgba(53, 193, 190, 0.04);
  }
  .content-area {
    flex: 1; padding: 80px 80px 30px;
    display: flex; flex-direction: column; position: relative; z-index: 1;
  }
  .brand-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
  .brand-left { display: flex; align-items: center; gap: 14px; }
  .logo-img { height: 64px; width: auto; }
  .brand-name { font-size: 36px; font-weight: 700; color: #35c1be; letter-spacing: 2px; }
  .header-badge {
    background: rgba(53, 193, 190, 0.12); border: 1px solid rgba(53, 193, 190, 0.40);
    padding: 8px 20px; border-radius: 20px; font-size: 22px;
    color: #35c1be; letter-spacing: 2px; font-weight: 600;
  }
  .title-zone { margin-bottom: 24px; }
  .title-zone h2 { font-size: 48px; font-weight: 700; color: #1a1a1a; letter-spacing: 1px; line-height: 1.3; }
  .title-underline {
    width: 100%; height: 2px;
    background: linear-gradient(to right, #35c1be 0%, transparent 100%);
    margin-top: 20px;
  }
  .en-block {
    background: #FFFFFF; border: 1.5px solid #35c1be; border-radius: 16px;
    padding: 40px 44px; margin-bottom: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.03);
  }
  .en-label {
    display: inline-block; font-size: 20px; color: #35c1be;
    letter-spacing: 3px; text-transform: uppercase; margin-bottom: 18px;
    border-bottom: 2px solid rgba(53, 193, 190, 0.30); padding-bottom: 6px; font-weight: 600;
  }
  .en-text {
    font-family: "Georgia", "Times New Roman", serif;
    font-size: 30px; line-height: 1.8; color: #2a2a2a; font-style: italic;
  }
  .divider { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
  .divider-line { flex: 1; height: 1px; background: rgba(53, 193, 190, 0.25); }
  .divider-icon { font-size: 20px; color: #35c1be; opacity: 0.7; }
  .zh-block {
    background: rgba(255,255,255,0.6); border: 1.5px solid #35c1be; border-radius: 16px;
    padding: 36px 44px; margin-bottom: auto;
  }
  .zh-label {
    display: inline-block; font-size: 20px; color: #35c1be;
    letter-spacing: 3px; margin-bottom: 18px;
    border-bottom: 2px solid rgba(53, 193, 190, 0.30); padding-bottom: 6px; font-weight: 600;
  }
  .zh-text { font-size: 30px; line-height: 1.8; color: #2a2a2a; }
  .footer-meta {
    display: flex; justify-content: space-between; align-items: flex-end;
    padding: 0 80px 14px; position: relative; z-index: 1;
  }
  .footer-left { display: flex; flex-direction: column; gap: 6px; }
  .author { font-size: 26px; font-weight: 600; color: #1a1a1a; }
  .handle { font-size: 22px; color: #444; }
  .footer-right { text-align: right; max-width: 58%; }
  .source-url {
    font-size: 18px; color: #35c1be; text-decoration: none; opacity: 0.85;
    display: block; word-break: break-all;
  }
  .info-bar {
    display: flex; justify-content: center; align-items: center;
    padding: 16px 80px 12px; font-size: 22px; color: #444;
    letter-spacing: 1px; gap: 24px; position: relative; z-index: 1;
  }
  .info-bar .separator { color: #35c1be; opacity: 0.6; }
  .brand-strip {
    height: 4px; background: #35c1be;
    display: flex; align-items: center; justify-content: center;
    position: relative; z-index: 1;
  }
  .brand-strip-inner {
    background: #35c1be; padding: 8px 24px; border-radius: 0 0 4px 4px;
    display: flex; align-items: center; gap: 8px;
    position: relative; top: -28px;
  }
  .brand-strip-text {
    color: #fff; font-size: 20px; font-weight: 700; letter-spacing: 3px;
  }
</style>
</head>
<body>

<div class="toolbar">
  <span>✏️ 编辑</span>
  <button onclick="toggleEdit()">退出编辑</button>
  <div class="color-swatch">
    <span>强调色</span>
    <div class="color-dot active" style="background:#35c1be" data-color="#35c1be" onclick="setAccent(this)"></div>
    <div class="color-dot" style="background:#f59e0b" data-color="#f59e0b" onclick="setAccent(this)"></div>
    <div class="color-dot" style="background:#8b5cf6" data-color="#8b5cf6" onclick="setAccent(this)"></div>
    <div class="color-dot" style="background:#ef4444" data-color="#ef4444" onclick="setAccent(this)"></div>
  </div>
  <button class="btn-download" onclick="downloadCard()">⬇ 下载</button>
</div>

<div class="card" id="card">
  <div class="dot dot-1"></div><div class="dot dot-2"></div><div class="dot dot-3"></div><div class="dot dot-4"></div>
  <div class="content-area">
    <div class="brand-bar">
      <div class="brand-left">
        <img class="logo-img" src="data:image/svg+xml;base64,''' + b64 + '''" alt="牛雪梨AI">
        <span class="brand-name">牛雪梨AI</span>
      </div>
      <span class="header-badge">Builder Digest</span>
    </div>
    <div class="title-zone">
      <h2 id="cardTitle">AI时代免费服务难以为继，<br>微支付或是出路</h2>
      <div class="title-underline"></div>
    </div>
    <div class="en-block">
      <div class="en-label">● Original</div>
      <p class="en-text" id="enText">"It is honestly impressive that GitHub kept the service up at all, given this kind of growth. I predicted this years ago: Free services will become untenable with the advent of human-level bots. Worth exploring micro-payments."</p>
    </div>
    <div class="divider"><div class="divider-line"></div><span class="divider-icon">✦</span><div class="divider-line"></div></div>
    <div class="zh-block">
      <div class="zh-label">● 中文</div>
      <p class="zh-text" id="zhText">说实话，考虑到这种增长，GitHub 能维持服务运行已经很了不起了。多年前我就预测过：随着人类级别机器人的出现，免费服务将变得不可持续。值得探索微支付方案。</p>
    </div>
  </div>
  <div class="footer-meta">
    <div class="footer-left">
      <span class="author" id="authorName">Amjad Masad</span>
      <span class="handle" id="authorHandle">@amasad · Replit CEO</span>
    </div>
    <div class="footer-right">
      <span class="source-url" id="sourceUrl">📎 x.com/amasad/status/2049242460078100638</span>
    </div>
  </div>
  <div class="info-bar">
    <span>Builder Digest</span><span class="separator">│</span><span>每日AI摘要</span><span class="separator">│</span><span id="cardDate">2026-04-29</span>
  </div>
  <div class="brand-strip"><div class="brand-strip-inner"><span class="brand-strip-text">牛雪梨AI</span></div></div>
</div>

<script>
  const editableIds = ["cardTitle","enText","zhText","authorName","authorHandle","sourceUrl","cardDate"];
  let editing = false;
  let currentAccent = "#35c1be";

  function toggleEdit() {
    editing = !editing;
    document.body.classList.toggle("editing", editing);
    editableIds.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.setAttribute("contenteditable", editing);
    });
    if (!editing && document.activeElement) document.activeElement.blur();
  }

  document.getElementById("card").addEventListener("dblclick", function(e) {
    if (!editing) toggleEdit();
  });
  document.addEventListener("keydown", function(e) {
    if (e.key === "Escape" && editing) toggleEdit();
  });

  function setAccent(dotEl) {
    document.querySelectorAll(".color-dot").forEach(d => d.classList.remove("active"));
    dotEl.classList.add("active");
    currentAccent = dotEl.dataset.color;
    applyAccent();
  }

  function applyAccent() {
    document.querySelectorAll(".brand-name, .header-badge, .en-label, .zh-label, .divider-icon, .source-url").forEach(el => { el.style.color = currentAccent; });
    document.querySelectorAll(".en-block, .zh-block").forEach(el => { el.style.borderColor = currentAccent; });
    document.querySelectorAll(".header-badge").forEach(el => { el.style.background = currentAccent + "1F"; el.style.borderColor = currentAccent + "66"; });
    document.querySelectorAll(".en-label, .zh-label").forEach(el => { el.style.borderBottomColor = currentAccent + "4D"; });
    document.querySelectorAll(".brand-strip, .brand-strip-inner").forEach(el => { el.style.background = currentAccent; });
    document.querySelectorAll(".title-underline").forEach(el => { el.style.background = "linear-gradient(to right, " + currentAccent + " 0%, transparent 100%)"; });
    document.querySelectorAll(".dot").forEach(el => { el.style.background = currentAccent; });
    document.querySelectorAll(".info-bar .separator, .divider-icon").forEach(el => { el.style.color = currentAccent; });
    document.querySelectorAll(".divider-line").forEach(el => { el.style.background = currentAccent + "40"; });
  }

  function downloadCard() {
    if (editing) toggleEdit();
    const card = document.getElementById("card");
    html2canvas(card, {
      scale: 2,
      backgroundColor: "#FFFFFF",
      useCORS: true,
      allowTaint: true
    }).then(canvas => {
      const link = document.createElement("a");
      link.download = "builder-digest-card.png";
      link.href = canvas.toDataURL("image/png");
      link.click();
    }).catch(err => {
      alert("下载失败。可右键 → 检查 → 截图保存。\\n错误：" + err.message);
    });
  }
</script>

</body>
</html>'''

# 写入项目模板 + 桌面预览
for p in [os.path.join(BASE, 'data', 'template.html'),
          os.path.expanduser('~/Desktop/xhs-card-preview.html')]:
    with open(p, 'w', encoding='utf-8') as f:
        f.write(html)
print('Done — 模板已更新（含交互功能）')
