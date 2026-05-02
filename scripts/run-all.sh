#!/bin/bash
# ==========================================
# Builder Digest · run-all.sh
# 一键执行：下载 → 提取 → 翻译 → 生成卡片 → 推送 GitHub Pages → 同步飞书 → 导出 CSV → 生成榜单 → 发布素材
# ==========================================

set -e

BASE="$HOME/.hermes/skills/builder-digest"
ENV_FILE="$BASE/.env"
TODAY=$(date +%Y-%m-%d)

export $(cat "$ENV_FILE" | xargs)

# 飞书通知函数
notify_progress() {
    local step="$1"
    local status="$2"
    local detail="$3"
    if [ -n "$FEISHU_WEBHOOK" ]; then
        python3 << PYEOF
import requests, json, os
data = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": "Builder Digest · 进度"},
            "template": "wathet"
        },
        "elements": [
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"**步骤：{os.environ.get('STEP')}**\n状态：{os.environ.get('STATUS')}\n{os.environ.get('DETAIL')}"}
            }
        ]
    }
}
requests.post(os.environ.get('FEISHU_WEBHOOK'), json=data, timeout=10)
PYEOF
    fi
}

echo "=========================================="
echo "  Builder Digest · 全流程一键执行"
echo "  日期：$TODAY"
echo "=========================================="
echo ""

# 1. 下载
echo "【1/9】下载 JSON..."
bash "$BASE/scripts/download.sh" && export STEP="1/9 下载 JSON" STATUS="✅ 完成" DETAIL="成功下载3个JSON文件" notify_progress || { export STEP="1/9 下载 JSON" STATUS="❌ 失败" DETAIL="请检查网络及数据源" notify_progress; exit 1; }
echo ""

# 2. 提取
echo "【2/9】提取推文..."
python3 "$BASE/scripts/extract.py" && export STEP="2/9 提取推文" STATUS="✅ 完成" DETAIL="推文数据已提取" notify_progress || { export STEP="2/9 提取推文" STATUS="❌ 失败" DETAIL="请检查数据源格式" notify_progress; exit 1; }
echo ""

# 3. 翻译
echo "【3/9】翻译..."
python3 "$BASE/scripts/translate.py" && export STEP="3/9 翻译" STATUS="✅ 完成" DETAIL="翻译及清洗已完成" notify_progress || { export STEP="3/9 翻译" STATUS="❌ 失败" DETAIL="请检查DeepSeek API余额及Token" notify_progress; exit 1; }
echo ""

# 4. 生成 HTML 卡片
echo "【4/9】生成 HTML 卡片..."
python3 "$BASE/scripts/gen-card.py" && export STEP="4/9 生成卡片" STATUS="✅ 完成" DETAIL="卡片文件已生成" notify_progress || { export STEP="4/9 生成卡片" STATUS="❌ 失败" DETAIL="请检查模板及JSON数据" notify_progress; exit 1; }
echo ""

# 5. 推送 GitHub Pages
echo "【5/9】推送 HTML 到 GitHub Pages..."
IMAGES_DIR="$BASE/data/images/$TODAY"
OUTPUT_DIR="$BASE/data/output/$TODAY"
mkdir -p "$OUTPUT_DIR"
cp "$IMAGES_DIR"/*.html "$OUTPUT_DIR/" 2>/dev/null
cd "$BASE/data/output"
if [ -d ".git" ]; then
    git add "$TODAY"/*.html 2>/dev/null
    git commit -m "Daily cards $TODAY" 2>/dev/null || echo "(没有新文件需要提交)"
    git push 2>/dev/null && export STEP="5/9 推送 Pages" STATUS="✅ 完成" DETAIL="卡片已部署至GitHub Pages" notify_progress || { export STEP="5/9 推送 Pages" STATUS="⚠️ 失败" DETAIL="请检查GitHub权限及网络" notify_progress; }
else
    export STEP="5/9 推送 Pages" STATUS="⚠️ 跳过" DETAIL="未找到Git仓库" notify_progress
fi
cd "$BASE"
echo ""

# 6. 同步飞书
echo "【6/9】同步飞书多维表格..."
python3 "$BASE/scripts/sync-to-feishu.py" && export STEP="6/9 同步飞书" STATUS="✅ 完成" DETAIL="数据已写入多维表格" notify_progress || { export STEP="6/9 同步飞书" STATUS="❌ 失败" DETAIL="请检查飞书应用权限" notify_progress; exit 1; }
echo ""

# 7. 导出 CSV
echo "【7/9】导出 CSV..."
python3 "$BASE/scripts/export-to-excel.py" && export STEP="7/9 导出 CSV" STATUS="✅ 完成" DETAIL="表格文件已生成" notify_progress || { export STEP="7/9 导出 CSV" STATUS="❌ 失败" DETAIL="请检查数据完整性" notify_progress; exit 1; }
echo ""

# 8. 生成榜单图片
echo "【8/9】生成榜单图片..."
python3 "$BASE/scripts/gen-ranking.py" && export STEP="8/9 生成榜单" STATUS="✅ 完成" DETAIL="榜单图片已生成" notify_progress || { export STEP="8/9 生成榜单" STATUS="❌ 失败" DETAIL="请检查Puppeteer及模板" notify_progress; exit 1; }
echo ""

# 9. 准备发布素材 + 飞书通知
echo "【9/9】准备发布素材 + 飞书通知..."
python3 "$BASE/scripts/prepare-xhs.py" && export STEP="9/9 发布素材" STATUS="✅ 完成" DETAIL="素材已就绪，请前往发布" notify_progress || { export STEP="9/9 发布素材" STATUS="❌ 失败" DETAIL="请检查Puppeteer及模板" notify_progress; exit 1; }
echo ""

echo "=========================================="
echo "  ✅ 全流程完成！"
echo "  飞书表格：已同步 $TODAY 数据"
echo "  发布素材：$BASE/data/output/预备发布/$TODAY/"
echo "=========================================="
