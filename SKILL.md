# Builder Digest · SKILL.md 修改预览

> 以下是基于我们实际跑通的全流程重写的 SKILL.md，删除了所有幻灯片相关内容，补充了实际的脚本和功能描述。

---

```markdown
---
name: builder-digest
description: "每日自动从 GitHub 拉取海外 AI Builder 推文，DeepSeek 中英双语翻译，生成小红书风格 HTML 卡片部署到 GitHub Pages，同步飞书多维表格，并准备小红书发布素材。"
version: 0.4.0
---

# Builder Digest

每日海外 AI Builder 信息摘要，全流程自动化：从数据拉取到卡片生成、飞书同步、发布素材准备。

## 触发方式

```bash
# 一键全流程（9步）
bash ~/.hermes/skills/builder-digest/scripts/run-all.sh

# 或通过飞书群 @机器人 发送 /run 远程触发
# 前提：Flask 服务 + ngrok 内网穿透已启动
数据流
GitHub (raw.githubusercontent.com)
  ↓ download.sh
data/feed-x.json
  ↓ extract.py
data/tweets/YYYY-MM-DD/*.json
  ↓ translate.py (+ DeepSeek API)
text_zh 写回 JSON，标题自动清洗（去链接、去 emoji、截断）
  ↓ gen-card.py
data/images/YYYY-MM-DD/*.html（小红书风格卡片）
  → 推送 GitHub Pages → 永久在线链接
  ↓ sync-to-feishu.py
飞书多维表格（文本字段 + 在线预览链接）
  ↓ export-to-excel.py
CSV 数据表（含“发布文案”列）
  ↓ gen-ranking.py
榜单.png（点赞前10排行榜图片）
  ↓ prepare-xhs.py
发布素材：10 张卡片截图 + 文案模板 + 飞书通知
# 核心脚本
脚本	功能
download.sh	从 GitHub 下载最新 feed JSON
extract.py	提取推文数据（三源兼容：X/Blog/Podcast）
translate.py	DeepSeek 翻译 + 自动清洗（去链接/emoji，标题截断）
gen-card.py	生成牛雪梨AI 品牌 HTML 卡片
sync-to-feishu.py	同步飞书多维表格（文本+卡片链接）
export-to-excel.py	导出 CSV 数据表
gen-ranking.py	生成点赞排行榜图片
prepare-xhs.py	准备小红书发布素材（截图+文案+通知）
check-update.sh	检查远程数据更新 + 飞书通知
feishu-bot-server.py	飞书机器人 HTTP 回调服务（接收 /run 指令）
run-all.sh	一键执行完整流程
#环境变量

在 ~/.hermes/skills/builder-digest/.env 中配置：

text
DEEPSEEK_API_KEY=sk-xxx
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_TABLE_ID=tblxxx
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
#项目文件结构

text
~/.hermes/skills/builder-digest/
├── SKILL.md
├── .env
├── scripts/
│   ├── run-all.sh
│   ├── download.sh
│   ├── extract.py
│   ├── translate.py
│   ├── gen-card.py
│   ├── sync-to-feishu.py
│   ├── export-to-excel.py
│   ├── gen-ranking.py
│   ├── prepare-xhs.py
│   ├── check-update.sh
│   └── feishu-bot-server.py
├── data/
│   ├── template.html
│   ├── ranking-template.html
│   ├── logo.svg
│   ├── feed-x.json
│   ├── tweets/
│   ├── images/
│   └── output/
│       └── YYYY-MM-DD/
│           ├── *.html
│           ├── *.csv
│           └── 预备发布/
└── logs/
#品牌规范

品牌名：牛雪梨AI
品牌色：#35c1be
风格：知性简约，白色背景 + 品牌色点缀
Logo：data/logo.svg，内嵌 base64 于 HTML 模板
卡片交互：双击编辑文字、颜色切换（4色）、一键下载 PNG
#定时任务

早 9:00 / 下午 17:00 自动检查 GitHub 数据源更新
有更新时飞书群收到通知，@机器人 /run 触发生成
#依赖

Python 3
DeepSeek API
Puppeteer（用于卡片截图）
Flask + ngrok（用于飞书机器人回调）
