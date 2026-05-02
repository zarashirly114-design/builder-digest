# Builder Digest

> 每日自动从 GitHub 拉取海外 AI Builder 推文，DeepSeek 中英双语翻译，生成小红书风格 HTML 卡片，部署到 GitHub Pages，同步飞书多维表格，并准备小红书发布素材。

## ✨ 核心功能

- **全自动流水线**：从数据源抓取到发布素材生成，一键完成
- **飞书机器人触发**：在飞书群 @机器人 `/run` 即可远程执行全流程
- **每日定时检查**：早9点、下午5点自动检查数据源更新，发现更新即通知
- **品牌化卡片**：牛雪梨AI 品牌色 #35c1be，支持 logo、水印、颜色切换
- **飞书多维表格**：自动同步文本、链接、点赞、转发等数据
- **小红书素材**：自动生成点赞前10的卡片截图、点赞排行榜图片、文案模板

## 📁 项目结构

~/.hermes/skills/builder-digest/
├── scripts/ # 所有脚本（run-all.sh 一键全流程）
├── data/ # 模板、logo、数据源、输出物
└── .env # 环境变量（需自行配置）


## 🚀 快速开始

### 1. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 填入真实的 API Key 和飞书凭证
2. 安装依赖
pip install -r requirements.txt
3. 运行全流程
bash scripts/run-all.sh
或通过飞书机器人远程触发（需配置 Flask + ngrok）。
📊 数据源

zarazhangrui/follow-builders 项目提供的 feed-x.json（每日更新）
🔗 相关链接

GitHub Pages 卡片预览
飞书多维表格
📄 许可证

MIT License
