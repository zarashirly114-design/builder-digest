# Builder Digest 项目要点（持久备忘）

## 数据流（2026-04-30 更新确认）
- **输入**：`data/tweets/YYYY-MM-DD/*.json` — JSON 格式，包含 text/text_zh/author_name/author_handle/url/title_zh
- **同时存在** `data/images/YYYY-MM-DD/*.html` 是渲染用的卡片文件，**gen-slides.py 从 JSON 读，不是从 HTML 卡片读**
- **输出**：`data/output/YYYY-MM-DD/slides/slides-YYYY-MM-DD.html`（自包含 HTML 幻灯片）

## gen-slides.py 关键规范
1. 数据源：`data/tweets/YYYY-MM-DD/*.json`，不要改读 HTML
2. 链接显示：完整 `https://x.com/...` URL，不用 `link-label`/原文链接 等纯文字
3. handle 格式：`@{handle} · X/Twitter`，直接从 JSON 取
4. Logo base64：从 `data/logo.svg` 读取（存在且完整）
5. CSS/JS：从 `data/slides-css.txt` / `data/slides-js.txt` 读取
6. 输出目录：`data/output/TODAY/slides/slides-TODAY.html`（含 slides 子文件夹）
7. 文件预检：脚本启动时检查 tweets/CSS/JS/logo 是否存在，不存在则报错退出
8. 路径：统一用 `pathlib.Path`

## 品牌规范
- 牛雪梨AI | 品牌色 #35c1be | 字体 Bodoni Moda + DM Sans
- 链接显示完整 URL（PDF 可读性），不用"查看原文"这类纯文字

## 标题处理逻辑（2026-04-30 更新）
- `clean_str()`: 去除 t.co 链接和 emoji（综合 Unicode 正则）
- `clean_title()`: 优先 title_zh → text_zh → text 兜底，截取前100字符
- `fallback_title()`: 当 clean_title 无内容时，从 text/text_zh 取前40字符
- **两轮扫描**: 第一轮收集有效卡片/统计总数，第二轮生成带正确编号的 slide
- **跳过机制**: clean_title() 返回 None 的文件跳过（如 sama-02/03，纯媒体推文无文本）
- **打印统计**: 显示 "共 N 张内容卡片 + 封面 + 结尾（跳过 M 张无内容卡片）"
